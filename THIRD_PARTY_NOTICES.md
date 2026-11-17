# 参考项目和许可

## 参考来源

- 中兴临时维护认证：[qiudz/zte-f7015tv3-telnet-solidify](https://github.com/qiudz/zte-f7015tv3-telnet-solidify) 及其 [webFac v3 协议说明](https://github.com/qiudz/zte-f7015tv3-telnet-solidify/blob/main/docs/webfac-v3-protocol.md)。
- 爱快 CLI 和配套 Skill：[ikuaidev/ikuai-cli](https://github.com/ikuaidev/ikuai-cli)。
- SSH：[Dropbear](https://github.com/mkj/dropbear) 和 [对应版本的许可](https://github.com/mkj/dropbear/blob/DROPBEAR_2026.94/LICENSE)，这次用的是 2026.94。
- BusyBox：当前使用[官方BusyBox 1.38.0源码](https://busybox.net/downloads/busybox-1.38.0.tar.bz2)，加入OpenWrt的[netmsg补丁](https://github.com/openwrt/openwrt/blob/openwrt-24.10/package/utils/busybox/patches/210-add_netmsg_util.patch)和[lock补丁](https://github.com/openwrt/openwrt/blob/openwrt-24.10/package/utils/busybox/patches/220-add_lock_util.patch)，分别构建两种架构的静态程序。
- 静态排障工具：[tcpdump](https://github.com/the-tcpdump-group/tcpdump)、[libpcap](https://github.com/the-tcpdump-group/libpcap)、[iperf3](https://github.com/esnet/iperf)、[ethtool](https://www.kernel.org/pub/software/network/ethtool/)和[strace](https://github.com/strace/strace)。
- 后补工具：[OpenWrt 24.10.4官方软件源](https://downloads.openwrt.org/releases/24.10.4/packages/)及[packages构建配方](https://github.com/openwrt/packages/tree/openwrt-24.10)，选定工具和依赖库单独放置，不使用厂商opkg直接安装。
- 早期BusyBox构建参考：[plusls/busybox-static](https://github.com/plusls/busybox-static)。
- 界面拓展案例：[HS8546V5光猫补全Shell、切华为原厂界面](https://www.right.com.cn/forum/thread-4060870-1-1.html)，是外部机型案例，不是本次两台设备的刷机记录。

## 许可

仓库里的文字使用 [MIT 许可证](LICENSE)，参考项目和下载的程序按各自的许可使用。

<details>
<summary>中兴 v3 参考项目的 MIT 许可正文</summary>

```text
MIT License

Copyright (c) 2026 Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

</details>
