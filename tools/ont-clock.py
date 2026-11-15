#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Opt-in ONT clock maintenance for the two documented Linux/OpenWrt profiles.

Default: read NTP and HTTP time only. Writes require --apply AND a private
configuration with allow_time_change=true. See docs/05-time-sync.md first.

webFac v3 protocol facts and constants: qiudz/zte-f7015tv3-telnet-solidify,
Copyright (c) 2026 Contributors, MIT; full notice: THIRD_PARTY_NOTICES.md.
No v1/v2 implementation, firmware writes, solidification or WAN edits.
"""

import argparse
import binascii
import calendar
import json
import os
import re
import shutil
import socket
import stat
import struct
import subprocess
import sys
import time


HOST = None
NTP = None
BASE = None
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36"
PROFILES = {"zte-g7615v2-webfac-v3": "ZXHN G7615V2", "znxt-xg120": "ZN-XG120"}
# Shared protocol constants, not a customer's key or password.
V3_POOL = bytes.fromhex(
    "9c3375d11c424537184891731745794443d7d573335476d2c5f12c4f7aba61d95c69"
    "df8cd21cde3b352d2fe1de4c77f51a65d1fe18438ea742080478d5e4f334a4d3f2364"
    "76d869d42651342dc429948dc679f9edc46375f849f6f76ce794f49"
)
assert len(V3_POOL) == 96


def fail(message):
    raise RuntimeError(message)


def private_ipv4(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}", value):
        fail("地址必须是现场核实过的私有 IPv4，不接受域名、URL 或命令")
    a, b, c, d = (int(v) for v in value.split("."))
    if value != ".".join(str(v) for v in (a, b, c, d)):
        fail("管理地址不接受前导零，避免不同网络工具解释不一致")
    if max(a, b, c, d) > 255 or not (a == 10 or (a == 172 and 16 <= b <= 31) or (a == 192 and b == 168)):
        fail("此参考工具只接受私有 IPv4 管理地址")
    return value


def secret(config, key):
    value = config.get(key)
    if not isinstance(value, str) or not value or value.startswith(("REPLACE_", "REDACTED", "<")):
        fail("私密配置还有未填写的凭据；不显示其内容")
    if any(v in value for v in ("\r", "\n", "\x00")):
        fail("凭据含不支持的控制字符，未发送")
    return value


def pct(value):
    return "".join(chr(v) if v in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~" else "%%%02X" % v for v in str(value).encode())


def form(pairs):
    return "&".join(pct(k) + "=" + pct(v) for k, v in pairs).encode()


assert form([("zone", "GMT+08:00")]) == b"zone=GMT%2B08%3A00"


def ntp_time():
    request = bytearray(48)
    request[0] = 0x23
    request[40:] = os.urandom(8)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(4)
        sock.sendto(request, (NTP, 123))
        response, peer = sock.recvfrom(512)
    if len(response) < 48 or peer != (NTP, 123) or response[24:32] != request[40:]:
        fail("时间源回应不属于本次请求")
    if response[0] >> 6 == 3 or response[0] & 7 != 4 or not 1 <= response[1] <= 15:
        fail("时间源未同步或回应类型无效")
    seconds, fraction = struct.unpack("!II", response[40:48])
    # Choose the NTP era nearest the independently synchronized control router.
    era = round((time.time() + 2208988800 - seconds) / 4294967296)
    value = seconds - 2208988800 + era * 4294967296 + fraction / 4294967296
    if not 1577836800 < value < 4102444800 or abs(value - time.time()) > 300:
        fail("时间源与管理设备时钟不一致，请先核对管理设备")
    return value


def http_clock():
    result = subprocess.run(["curl", "--noproxy", "*", "-sS", "--max-time", "8", "-I", "http://" + HOST + "/"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        fail("无法读取已确认光猫的 HTTP 时钟")
    match = re.search(rb"^Date:\s*(.*?)\r?$", result.stdout, re.M | re.I)
    if not match:
        fail("此设备未提供可用的 HTTP Date，不能套用本参考工具")
    try:
        parsed = time.strptime(match.group(1).decode().strip(), "%a, %d %b %Y %H:%M:%S GMT")
    except ValueError:
        fail("HTTP Date 格式不受支持")
    return calendar.timegm(parsed)


def service_state():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        try:
            sock.connect((HOST, 23))
            return "open"
        except ConnectionRefusedError:
            return "closed"
        except OSError:
            return "unknown"


class Web:
    def __init__(self, state):
        self.state = state
        self.jar = state + "/cookies"
        self.token = ""
        self.temp_requested = False
        if os.path.exists(state + "/web-token.json"):
            self.token = json.load(open(state + "/web-token.json"))["token"]

    def request(self, path, body=None, referer="/cgi-bin/content.asp", extra_cookie="", allow_empty=False):
        agent = "curl/8.8.0-DEV" if path.startswith("/webFac") else UA
        args = ["curl", "--noproxy", "*", "-sS", "--max-time", "15", "-A", agent,
                "-b", self.jar, "-c", self.jar, "-e", BASE + referer, "-w", "\n%{http_code}"]
        cookies = (["ecntToken=" + self.token] if self.token else []) + ([extra_cookie] if extra_cookie else [])
        if cookies:
            args += ["-b", "; ".join(cookies)]
        if body is not None:
            args += ["--data-binary", "@-", "-H", "Origin: " + BASE]
            if path.startswith("/webFac"):
                args += ["-H", "Content-Type: text/plain"]
        result = subprocess.run(args + [BASE + path], input=body, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode and not (allow_empty and result.returncode in (52, 56)):
            fail("本地 HTTP 通信失败，未输出请求或凭据")
        data, _, status = result.stdout.rpartition(b"\n")
        return int(status or b"0"), data

    def znxt_login(self, config, fresh=False):
        if not fresh:
            status, data = self.request("/cgi-bin/content.asp")
            if status == 200 and re.search(rb'ModelName\s*=\s*"ZN-XG120"', data):
                return
        status, data = self.request("/login.cgi", form([("username", secret(config, "username")), ("psd", secret(config, "password"))]), "/login.cgi")
        match = re.search(rb"var\s+auth_result\s*=\s*(\{.*?\})", data, re.S)
        if not match:
            fail("未读到当前固件的认证状态")
        result = json.loads(match.group(1))
        if result.get("Privilege") not in ("1", "2") or result.get("Active") != "1":
            fail("认证未完成，可能被占用、锁定或拒绝；不进行重试猜密")
        self.token = result["ecntToken"]
        with open(self.state + "/web-token.json", "w") as stream:
            json.dump({"token": self.token}, stream)
        status, data = self.request("/cgi-bin/content.asp", referer="/login.cgi")
        if status != 200 or not re.search(rb'ModelName\s*=\s*"ZN-XG120"', data):
            fail("当前内容框架或机型核对失败")

    def telnet_flag(self):
        status, data = self.request("/cgi-bin/telnet.asp")
        match = re.search(rb'name="telnetenable_flag"\s+value="([^"]*)"', data)
        if status != 200 or not match:
            fail("未读到受支持的临时访问开关")
        return match.group(1).decode()

    def telnet_switch(self, enabled):
        pairs = [("telnet_flag", "1"), ("telnetenable_flag", "Yes" if enabled else "No")]
        if enabled:
            pairs.append(("enabletelnet", "on"))
        checksum = format(binascii.crc32("".join(k + v for k, v in pairs).encode()) & 0xFFFFFFFF, "x")
        status, data = self.request("/cgi-bin/telnet.asp", form(pairs), "/cgi-bin/telnet.asp", "EBOOVALUE=" + checksum)
        match = re.search(rb'name="telnetenable_flag"\s+value="([^"]*)"', data)
        if status != 200 or not match or match.group(1) != (b"Yes" if enabled else b"No"):
            fail("临时访问开关没有得到确认")


def zte_access(web, config):
    status, _ = web.request("/login.cgi", form([("username", secret(config, "username")), ("psd", secret(config, "password"))]), "/login.cgi")
    if status != 302:
        fail("中兴 Web 会话没有建立")
    web.request("/start.ghtml")
    web.request("/template.gch", referer="/start.ghtml")
    status, data = web.request("/getpage.gch?pid=1002&nextpage=status_dev_info_t.gch", referer="/template.gch")
    model = re.findall(rb"Transfer_meaning\('ModelName','([^']*)'\)", data)
    models = [re.sub(rb"\\x([a-fA-F0-9]{2})", lambda v: bytes([int(v.group(1), 16)]), v).decode("ascii") for v in model]
    if status != 200 or config["expected_model"] not in models:
        fail("中兴机型核对未通过，未申请临时访问")
    status, data = web.request("/getpage.gch?pid=1002&nextpage=net_family_named_t.gch", referer="/template.gch")
    values = {}
    for key, value in re.findall(rb"Transfer_meaning\('(IPAddress\d*|MACAddress\d*)','([^']*)'\)", data):
        values[key.decode()] = re.sub(r"\\x([a-fA-F0-9]{2})", lambda v: chr(int(v.group(1), 16)), value.decode("ascii"))
    mac = next((values.get("MACAddress" + k[9:]) for k, v in values.items() if k.startswith("IPAddress") and v == NTP), None)
    if status != 200 or not mac or not re.fullmatch(r"(?:[a-fA-F0-9]{2}:){5}[a-fA-F0-9]{2}", mac):
        fail("没有核实到光猫侧管理地址对应的二层记录；不猜 MAC")
    status, _ = web.request("/webFac", b"SendSq.gch")
    if status not in (200, 400):
        fail("当前固件不支持此临时入口")
    web.request("/webFac", b"RequestFactoryMode.gch", allow_empty=True)
    status, reply = web.request("/webFac", b"SendSq.gch?rand=0\r\n")
    challenge = re.match(rb"re_rand=(\d+)&\d+&", reply)
    if status != 200 or not challenge or len(reply) != challenge.end() + 6:
        fail("只支持已核对的 webFac v3，当前协议不匹配")
    device_mac = reply[-6:]
    client_mac = bytes.fromhex(mac.replace(":", ""))
    index = int(challenge.group(1)) % 60
    key = bytes(v ^ 0xA5 for v in V3_POOL[index:index + 24])

    def crypt(data, decrypt=False):
        if decrypt:
            data += bytes((-len(data)) % 16)
        else:
            data += bytes(16 - len(data) % 16)
        args = ["openssl", "enc", "-aes-192-ecb", "-K", key.hex(), "-nopad"] + (["-d"] if decrypt else [])
        result = subprocess.run(args, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            fail("临时认证的加密步骤失败")
        return result.stdout.rstrip(bytes([0])) if decrypt else result.stdout

    headers = {0: None, 1: None, 0x1687: None}
    mac_words = {v: None for v in device_mac + client_mac}
    missing = len(headers) + len(mac_words)
    alphabet = b"lmaoztebcdfghijknpqrsuvwxy"
    for a in alphabet:
        if not missing:
            break
        for b in alphabet:
            if not missing:
                break
            for c in alphabet:
                if not missing:
                    break
                for d in alphabet:
                    word = a | b << 8 | c << 16 | d << 24
                    value = pow(word, 0x1687, 0x7561)
                    if value in headers and headers[value] is None:
                        headers[value] = word
                        missing -= 1
                    value = word % 0x1687 & 255
                    if value in mac_words and mac_words[value] is None:
                        mac_words[value] = word
                        missing -= 1
                    if not missing:
                        break
    if missing:
        fail("无法构造本次临时认证")
    words = [headers[v] for v in (0, 1, 0, 0x1687)] + [mac_words[v] for v in device_mac + client_mac + client_mac]
    assert [pow(v, 0x1687, 0x7561) for v in words[:4]] == [0, 1, 0, 0x1687]
    assert bytes(v % 0x1687 & 255 for v in words[4:]) == device_mac + client_mac + client_mac
    status, _ = web.request("/webFacEntry", crypt(b"SendInfo.gch?info=22|" + b"".join(struct.pack("<I", v) for v in words)))
    if status != 200:
        fail("当前路径的客户端认证未通过；不修改 MAC 或连接配置")
    auth = "CheckLoginAuth.gch?version50&user=%s&pass=%s" % (secret(config, "username"), secret(config, "password"))
    status, response = web.request("/webFacEntry", crypt(auth.encode()))
    if status != 200 or b"FactoryMode.gch" not in crypt(response, True):
        fail("已提供的超密未完成临时认证，不继续尝试其他密码")
    web.temp_requested = True
    status, response = web.request("/webFacEntry", crypt(b"FactoryMode.gch?mode=2&user=notused"))
    if status != 200:
        fail("临时命令入口未获准")
    text = crypt(response, True)
    match = re.search(rb"user=([^&\s\x00]+)&pass=([^&\s\x00]+)", text)
    if not match:
        fail("未取得可用临时会话；需要核实入口是否关闭")
    return match.group(1).decode(), match.group(2).decode()


class Telnet:
    def __init__(self, username, password, admin=None):
        self.newline = b"\n" if admin else b"\r\n"
        self.pending = b""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.settimeout(5)
            self.sock.connect((HOST, 23))
            self.sock.settimeout(.3)
            self.until(rb"[Ll]ogin:\s*$")
            self.send(username)
            self.until(rb"[Pp]assword:\s*$")
            self.send(password)
            self.until(rb"(?:^|[\r\n])[^\r\n]{0,80}[#$>]\s*$")
            if admin:
                self.send("su")
                self.until(rb"[Pp]assword:\s*$")
                self.send(admin)
                self.until(rb"(?:^|[\r\n])[^\r\n]{0,80}#\s*$")
        except BaseException:
            self.sock.close()
            raise

    def send(self, value):
        self.sock.sendall(value.encode() + self.newline)

    def until(self, pattern, seconds=8):
        deadline = time.monotonic() + seconds
        text = bytearray()
        while time.monotonic() < deadline:
            try:
                data = self.sock.recv(8192)
                if not data:
                    break
            except socket.timeout:
                continue
            data = self.pending + data
            self.pending = b""
            i = 0
            while i < len(data):
                if data[i] == 255:
                    if i + 2 >= len(data):
                        self.pending = data[i:]
                        break
                    op, option = data[i + 1:i + 3]
                    if op == 253:
                        self.sock.sendall(bytes([255, 252, option]))
                    elif op == 251:
                        self.sock.sendall(bytes([255, 253 if option in (1, 3) else 254, option]))
                    i += 3
                else:
                    text.append(data[i])
                    i += 1
            if re.search(pattern, text, re.M):
                return text.decode("utf-8", "replace")
            if re.search(rb"Error!|Login incorrect|login again after", text, re.I):
                fail("本地命令认证未通过；不输出终端内容、不猜密")
        fail("本地命令提示符未完成；先核对协议、换行和权限")

    def command(self, value):
        self.send(value + "; echo __ONT_CLOCK_DONE__:$?")
        result = self.until(rb"^__ONT_CLOCK_DONE__:\d+\r?$", 12)
        status = re.search(r"^__ONT_CLOCK_DONE__:(\d+)\r?$", result, re.M)
        if not status or status.group(1) != "0":
            fail("光猫时间命令未成功")
        return result

    def stop_own_zte_access(self):
        self.send("killall telnetd utelnetd 2>/dev/null")
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                if not self.sock.recv(1024):
                    break
            except socket.timeout:
                continue

    def close(self):
        self.sock.close()


def main():
    global HOST, NTP, BASE
    parser = argparse.ArgumentParser(description="默认只读光猫与本地 NTP 时钟，写入只支持已核对的 Linux / OpenWrt 样本")
    parser.add_argument("config", help="本机私密 JSON 配置，凭据不放进命令")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-config", action="store_true", help="离线检查结构、占位符和依赖，不发网络请求")
    mode.add_argument("--apply", action="store_true", help="必要时修正时间，还要求配置显式允许")
    parser.add_argument("--force", action="store_true", help="仅配合 --apply，明确要求执行修复路径")
    args = parser.parse_args()
    apply, force = args.apply, args.force
    if force and not apply:
        fail("--force 必须和明确写入授权 --apply 一起使用")
    if os.name == "posix" and stat.S_IMODE(os.stat(args.config).st_mode) & 0o077:
        fail("配置文件权限必须限制为 600；未读取其内容")
    try:
        with open(args.config, encoding="utf-8-sig") as stream:
            config = json.load(stream)
    except (ValueError, UnicodeError):
        fail("私密配置不是有效 JSON；不回显文件内容")
    if not isinstance(config, dict):
        fail("私密配置必须是 JSON 对象，不回显文件内容")
    HOST = private_ipv4(config.get("host"))
    NTP = private_ipv4(config.get("ntp_server"))
    if HOST == NTP:
        fail("光猫管理地址和本地时间源不能混为同一目标")
    BASE = "http://%s:8080" % HOST
    if config.get("profile") not in PROFILES or config.get("expected_model") != PROFILES[config["profile"]]:
        fail("配置机型不属于本工具已限定的两个样本")
    if not isinstance(config.get("allow_time_change"), bool):
        fail("allow_time_change 必须明确填写 true 或 false")
    if args.check_config:
        keys = ["username", "password"]
        if config["profile"] == "znxt-xg120":
            keys += ["telnet_username", "telnet_password", "admin_password"]
        unready = sum(not isinstance(config.get(key), str) or not config[key] or config[key].startswith(("REPLACE_", "REDACTED", "<")) for key in keys)
        print("离线检查：结构有效；未就绪凭据字段=%d；允许写时间=%s" % (unready, "是" if config["allow_time_change"] else "否"))
        print("本机依赖：curl=%s；OpenSSL=%s" % ("存在" if shutil.which("curl") else "缺少", "存在" if shutil.which("openssl") else "缺少"))
        print("没有网络请求，没有验证型号、路由、密码或兼容性。Windows 配置权限需另行用 ACL 限制。")
        return
    if apply:
        if not sys.platform.startswith("linux"):
            fail("实际写时间只支持 Linux / OpenWrt，没有发送网络请求")
        if config["allow_time_change"] is not True:
            fail("配置尚未授权时间修正；没有发送网络请求")
        import fcntl

        os.umask(0o077)
    reference = ntp_time()
    current = http_clock()
    delta = current - reference
    if not apply:
        print("只读检查：光猫时间=%s UTC；与本地时间源相差 %.2f 秒；没有登录或修改" % (time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(current)), delta))
        return
    if abs(delta) <= 5 and not force:
        print("检查正常：误差 %.2f 秒，无需登录或修改" % delta)
        return
    secret(config, "username")
    secret(config, "password")
    znxt = config["profile"] == "znxt-xg120"
    if znxt:
        for key in ("telnet_username", "telnet_password", "admin_password"):
            secret(config, key)
    state = "/tmp/telecom-ont-clock-" + HOST.replace(".", "-")
    os.makedirs(state, mode=0o700, exist_ok=True)
    if stat.S_IMODE(os.stat(state).st_mode) & 0o077 or os.stat(state).st_uid != os.geteuid():
        fail("会话目录权限或所有者不符合要求")
    lock = open(state + "/run.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("已有校时任务执行，本轮跳过")
        return
    if service_state() != "closed":
        fail("目标命令端口已开或状态不明；不接管、不关闭现有入口")
    web = Web(state)
    telnet = None
    opened = False
    cleanup_ok = True
    try:
        if znxt:
            web.znxt_login(config)
            if web.telnet_flag() != "No":
                fail("设备原本已启用命令入口，不擅自接管")
            opened = True
            web.telnet_switch(True)
            username, password, admin = config["telnet_username"], config["telnet_password"], config["admin_password"]
        else:
            username, password = zte_access(web, config)
            admin = None
            opened = True
        telnet = Telnet(username, password, admin)
        wanted = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ntp_time() + 1))
        telnet.command("date -u -s '" + wanted + "'")
        epoch = re.search(r"^(\d{10})\r?$", telnet.command("date +%s"), re.M)
        if not epoch or abs(int(epoch.group(1)) - ntp_time()) > 5:
            fail("命令行系统时间回读未通过")
    finally:
        if telnet:
            try:
                if not znxt:
                    telnet.stop_own_zte_access()
            except Exception:
                cleanup_ok = False
            finally:
                telnet.close()
        if opened and znxt:
            try:
                try:
                    web.telnet_switch(False)
                except RuntimeError:
                    # A large clock step can expire the old Web session.
                    web.znxt_login(config, fresh=True)
                    web.telnet_switch(False)
                if web.telnet_flag() != "No":
                    cleanup_ok = False
            except Exception:
                cleanup_ok = False
        if web.temp_requested and telnet is None:
            cleanup_ok = False
        if (opened or web.temp_requested) and service_state() != "closed":
            cleanup_ok = False
        if not cleanup_ok:
            print("警告：临时入口清理未确认。不要设置定时任务，请用已授权管理通道核实；不要重置设备。", file=sys.stderr)
    if not cleanup_ok:
        fail("校时流程尚未全部完成，不能忽略临时访问状态")
    delta = http_clock() - ntp_time()
    if abs(delta) > 5:
        fail("HTTP 实际系统时间回读未通过")
    print("修正并验证完成：真实系统时间误差 %.2f 秒；本次临时端口已拒绝连接" % delta)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never echo third-party responses, config values or terminal buffers.
        error = sys.exc_info()[1]
        message = str(error) if isinstance(error, RuntimeError) else "执行失败；为保护凭据，不输出底层数据，请核对权限、依赖和对应章节"
        print("未完成：" + message, file=sys.stderr)
        sys.exit(1)
