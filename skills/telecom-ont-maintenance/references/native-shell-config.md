# 主系统Shell和原生配置

这份记录把进Telnet、看主系统、装SSH和改原生配置接起来。先核对型号和固件，再用对应步骤；文中的地址、账号和进程号占位符由Agent按现场填写。

| 光猫 | 固件 | 主系统架构 | 实际记录 |
|---|---|---|---|
| 中兴 ZXHN G7615V2 | `V3.0.0P1T2` | AArch64，小端 | webFac v3临时Telnet、主系统UID 0、SAF应用SSH、原生日志配置和运行状态调整 |
| ZNXT ZN-XG120 | `ZV2.01.X01` | MIPS32r2，小端 | 后台开启临时Telnet、管理员Shell、SAF应用SSH、共享日志文件读取 |

## 一、先连上主系统Telnet

### 中兴ZXHN G7615V2

1. 用超密走8080端口的`/login.cgi`，保存登录会话。网页登录和后面的webFac会话分别处理。
2. 读取`/webFac`的`SendSq.gch?rand=0`响应。这台返回`re_rand=`，按v3流程处理，不套空响应或`newrand=`那两版。
3. 按[webFac v3协议说明](https://github.com/qiudz/zte-f7015tv3-telnet-solidify/blob/main/docs/webfac-v3-protocol.md)完成临时维护交互：`RequestFactoryMode.gch`、`SendSq.gch?rand=0`、`SendInfo.gch?info=22|...`、`CheckLoginAuth.gch?version50&user=...&pass=...`，最后是`FactoryMode.gch?mode=2&user=notused`。实际请求体使用该协议的AES-192-ECB封装。
4. 证明载荷里的客户端MAC要对应光猫实际看到的连接来源。直连时读取出接口；经过现有管理路由时，读取光猫主机表中管理侧地址对应的MAC。上游脚本默认本机网卡直连，不能隔着路由还照抄电脑的MAC；这次是按光猫读回的管理侧记录匹配的，没有改网卡MAC。
5. 从响应中读取本次临时Telnet账号和密码，保存在当前登录流程里，再连23端口。这台使用CRLF换行。

协议里的`RequestFactoryMode.gch`可能主动断开HTTP连接，这是该阶段的返回行为。后续用挑战响应和认证结果判断进度，不把这次断开直接当成登录失败。

### ZNXT ZN-XG120

1. 向8080端口`/login.cgi`提交`username`和`psd`，根据返回的`auth_result`保存`ecntToken` Cookie，再读取`/cgi-bin/content.asp`。
2. 从已登录的`/cgi-bin/telnet.asp`表单开启Telnet。样本字段为`telnet_flag=1`、`telnetenable_flag=Yes`、`enabletelnet=on`；`EBOOVALUE`按页面脚本计算。样本是按字段顺序拼接键和值，再取CRC32的十六进制。
3. 用现有命令行账号登录，需要时执行`su`并提交对应的管理员密码。这台使用LF换行，CRLF会多提交一个空行。
4. 用`id`读取当前身份，确认UID 0后继续。

两台都使用用户提供的超密和对应登录账号，密码及临时会话值不写进公开命令示例。

## 二、分清主系统和应用环境

先看当前Shell实际在哪，再决定在哪执行命令：

```sh
id
uname -m
readlink /proc/1/exe
readlink /proc/self/ns/pid
readlink /proc/self/ns/mnt
cat /proc/mounts
```

本次临时Telnet到达主系统，SSH则装在SAF应用环境里。两边都能显示UID 0，但看到的进程、挂载和可用命令不一样，应用root不等于已进入主系统。

从主系统找到正在运行的`appmgr`，读回它的PID和`/proc/<PID>/root`。中兴可用已补充的BusyBox，ZNXT用主系统现有BusyBox。下面三个变量先换成实际值，进程号每次重新读取：

```sh
BB='<BUSYBOX_PATH>'
APP_PID='<APP_MANAGER_PID>'
APP_ROOT="/proc/$APP_PID/root"
"$BB" ps -o pid,comm
"$BB" nsenter -t "$APP_PID" -m -u -i -n -p -r"$APP_ROOT" -w"$APP_ROOT" -- /bin/sh
```

进入后再核对`id`、PID 1、根目录和可写层。样本的应用环境使用`procd`、`rc.common`和已有的应用存储；在这个正在运行的环境里安装SSH，不直接改挂载层背后的文件。

## 三、网页参数和本机配置分开处理

### 继续走网页

中兴的网页配置包含`_SESSION_TOKEN`，配置参数经AES-CBC封装后放入`IF_ENCODEPARAM`，对应的AES密钥再按网页给出的RSA公钥封装到`IF_ENCODE`。让Agent读取当前页面JavaScript，照实际的参数顺序、编码、密钥和IV来源提交，不复用别的会话值。

这和前面webFac使用的AES-192-ECB是两条不同流程，不要混用加密方式。HTTP 200或页面返回`SUCC`之后，仍然重新读取目标配置；这次日志网页曾返回成功，但目标字段没有改变。

### 从本机处理配置

已经进了主系统，就先查固件自带命令。这次中兴的日志配置是大小写敏感的`Log`表第0行，接收地址和端口由Agent按NAS实际配置填写：

```sh
sendcmd 1 DB p Log
sendcmd 1 DB set Log 0 ServiceIp '<LOG_RECEIVER_IPV4>'
sendcmd 1 DB set Log 0 ServicePort '<LOG_RECEIVER_PORT>'
sendcmd 1 DB set Log 0 ServiceEnable 1
sendcmd 1 DB save
sendcmd 1 DB p Log
```

修改前先读表并保留要比较的字段，修改后再读回。这个保存入口会保存原生用户配置，不是单独导出一份日志文件。样本的配置容器虽然以`.xml`命名，实际是二进制，不能当普通XML覆盖。

本机调用不用再经过网页的RSA+AES参数封装，但前提仍是已经登录并到达对应的本机环境。SAF有独立的进程和IPC环境，不能因为应用SSH也是root，就直接假定它能访问主系统配置数据库。

## 四、用native-ABI helper启用当前日志发送

这里的native-ABI helper，就是按固件内部接口的结构和调用约定，启用已有的日志发送程序。**这一段只核对过ZXHN G7615V2、V3.0.0P1T2的日志接口**，ZNXT以及其他型号、固件不直接套用。

这次保存`Log`配置后，当前发送程序仍是关闭的。固件的`cspd`通过`logSetSaveService`调用日志接口，启动时的`logStart`也会读取配置并走这个接口。对应参数如下：

| 项目 | 已核对值 |
|---|---|
| 调用 | `klogctl(0x469, request, 0x24)` |
| 操作码 / 载荷长度 | `0x404` / `0x1c` |
| 请求结构长度 | `0x24`字节 |
| 开关偏移 | `8`，本次设为`1` |
| 端口 / IPv4地址偏移 | `10` / `12`，网络字节序 |
| 型号字段偏移 | `16`，长度20字节，值为`ZXHN_G7615V2` |

下面是对应的C源码。Agent先把`LOG_RECEIVER`和`LOG_PORT`填成与保存配置相同的值，存成`native-log-apply.c`，再编译：

```c
/* Runtime apply for ZXHN G7615V2 V3.0.0P1T2; persistence is handled separately. */
#include <arpa/inet.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/klog.h>
#include <sys/utsname.h>
#include <unistd.h>

#define LOG_RECEIVER "<LOG_RECEIVER_IPV4>"
#define LOG_PORT 520

struct native_log_server {
    uint32_t operation;
    uint32_t payload_size;
    uint8_t enabled;
    uint8_t reserved;
    uint16_t port;
    uint32_t address;
    char model[20];
};

_Static_assert(sizeof(struct native_log_server) == 0x24, "Unexpected native log ABI");
_Static_assert(offsetof(struct native_log_server, port) == 10, "Unexpected port offset");
_Static_assert(offsetof(struct native_log_server, address) == 12, "Unexpected address offset");
_Static_assert(offsetof(struct native_log_server, model) == 16, "Unexpected model offset");
_Static_assert(LOG_PORT > 0 && LOG_PORT <= 65535, "Invalid receiver port");

int main(int argc, char **argv)
{
    struct utsname host;
    if (argc != 2 || strcmp(argv[1], "--apply-logging") != 0) {
        fputs("Usage: native-log-apply --apply-logging\n", stderr);
        return 2;
    }
    if (geteuid() != 0 || uname(&host) != 0 || strcmp(host.machine, "aarch64") != 0) {
        fputs("Expected the documented G7615V2 runtime\n", stderr);
        return 2;
    }
    struct native_log_server request = {0};
    request.operation = 0x404;
    request.payload_size = 0x1c;
    request.enabled = 1;
    request.port = htons(LOG_PORT);
    if (inet_pton(AF_INET, LOG_RECEIVER, &request.address) != 1)
        return 2;
    memcpy(request.model, "ZXHN_G7615V2", sizeof("ZXHN_G7615V2"));
    if (klogctl(0x469, (char *)&request, sizeof(request)) < 0) {
        perror("Native log runtime apply");
        return 1;
    }
    puts("Native log runtime apply completed");
    return 0;
}
```

这次实际使用的是静态链接的**32位ARM EABI**程序，在AArch64内核的兼容环境运行；不是看到`uname -m`是`aarch64`，就把这份请求直接换成64位程序。调用约定也要与样本对上。使用Zig 0.13.0的编译命令为：

```sh
zig cc -target arm-linux-musleabi -Os -static native-log-apply.c -o native-log-apply
```

核对生成文件的ELF类别、架构和SHA256，传到光猫内存目录，再按文档对应的运行环境调用。样本曾通过应用SSH调用这个原生日志接口；这不代表应用环境能够直接操作主系统配置数据库。

```sh
chmod 700 /tmp/native-log-apply
/tmp/native-log-apply --apply-logging
```

执行后，用与固件匹配的`sendcmd log KLogServer info`读取当前开关，再去NAS核对真实设备日志是否新增。样本从`enable=0`变为`enable=1`，随后收到带型号标记的真实日志。退出码只说明这次调用的返回结果，不代替状态和接收端检查。

helper只调整当前日志发送状态，不负责保存`Log`配置，不读写日志历史，也不安装自启动任务。原生启动时重新应用配置的路径已经确认，整机重启恢复还没验证。

## 五、装好SSH再核对连接环境

给实际架构准备Dropbear静态程序，进入已有SAF应用环境后，放到单独目录，沿用该环境的`rc.common`启动方式。样本使用的文件是：

| 应用内路径 | 作用 |
|---|---|
| `/opt/ontssh/dropbearmulti` | Dropbear程序和主机密钥生成工具 |
| `/opt/ontssh/hostkey` | 这台光猫生成的主机密钥 |
| `/root/.ssh/authorized_keys` | 用户提供的登录公钥 |
| `/etc/init.d/ontssh` | SSH服务入口 |
| `/etc/rc.d/S96ontssh` | 应用环境原生启动项 |

先看已有的SSH服务和公钥文件，有的话沿用当前入口；下面是新增独立`ontssh`服务时的模板。把`ONT_ADDR`换成当前应用环境能监听的管理地址，再存成`/etc/init.d/ontssh`：

```sh
#!/bin/sh /etc/rc.common
START=96
STOP=05
ONT_ADDR='<ONT_MANAGEMENT_IPV4>'

start() {
    if [ -r /var/run/ontssh.pid ]; then
        read -r pid < /var/run/ontssh.pid
        case "$pid" in ''|*[!0-9]*) return 1 ;; esac
        if kill -0 "$pid" 2>/dev/null; then
            [ "$(readlink "/proc/$pid/exe")" = /opt/ontssh/dropbearmulti ]
            return $?
        fi
    fi
    [ -s /opt/ontssh/hostkey ] && [ -s /root/.ssh/authorized_keys ] || return 1
    /opt/ontssh/dropbearmulti dropbear \
        -p "$ONT_ADDR:22" -r /opt/ontssh/hostkey -P /var/run/ontssh.pid \
        -s -g -j -k -I 600 -K 30
}

boot() {
    (
        attempt=0
        while [ "$attempt" -lt 30 ]; do
            start && exit 0
            attempt=$((attempt + 1))
            sleep 2
        done
        logger -t ontssh "SSH startup failed"
    ) </dev/null >/dev/null 2>&1 &
}

stop() {
    [ -r /var/run/ontssh.pid ] || return 0
    read -r pid < /var/run/ontssh.pid
    case "$pid" in ''|*[!0-9]*) return 1 ;; esac
    kill -0 "$pid" 2>/dev/null || return 0
    [ "$(readlink "/proc/$pid/exe")" = /opt/ontssh/dropbearmulti ] || return 1
    kill "$pid"
}
```

程序目录和程序设为700，`.ssh`目录设为700，公钥文件和主机密钥设为600。用`dropbearmulti dropbearkey -t ed25519 -f /opt/ontssh/hostkey`在光猫生成主机密钥，已有密钥就保留，不重新生成。文件和公钥准备好后，检查脚本语法，再启用服务：

```sh
sh -n /etc/init.d/ontssh
chmod 700 /etc/init.d/ontssh
/etc/init.d/ontssh enable
/etc/init.d/ontssh enabled
/etc/init.d/ontssh start
```

用用户公钥登录，读回主机公钥指纹，在电脑上核对后连接。连上再看`id`、PID 1和挂载，确认这是SAF应用环境。启动命令和启动项分别检查，能连一次SSH不等于已经验证重启恢复。

完成后关掉本次临时Telnet：中兴样本需要同时处理`telnetd`和`utelnetd`，等待会话结束；ZNXT把对应网页开关恢复为关闭。读回监听状态，再确认SSH仍可连接。
