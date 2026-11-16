# 来源与第三方说明

本教程依据两台已授权光猫的历史维护结果编写：上海电信的中兴 ZXHN G7615V2，以及浙江电信的 ZNXT ZN-XG120。具体固件和验证范围见 [README](README.md)。

本仓库提供方法说明、提示词和一份总 Skill，不提供安装脚本、打包的下载工具或设备程序，不包含真实密码、配置、会话和私人网络规划。

## 参考来源

- 中兴临时维护认证：[qiudz/zte-f7015tv3-telnet-solidify](https://github.com/qiudz/zte-f7015tv3-telnet-solidify) 及其 [webFac v3 协议说明](https://github.com/qiudz/zte-f7015tv3-telnet-solidify/blob/main/docs/webfac-v3-protocol.md)。这里只参考临时认证方法，不推荐执行固化或刷机操作。
- 爱快 CLI 和配套 Skill：[ikuaidev/ikuai-cli](https://github.com/ikuaidev/ikuai-cli)。使用前核对当前项目说明和自己的路由器版本。
- SSH 服务：[Dropbear 上游项目](https://github.com/mkj/dropbear) 及其 [完整许可](https://github.com/mkj/dropbear/blob/DROPBEAR_2026.94/LICENSE)。样本安装的是从上游构建的 Dropbear 2026.94。
- BusyBox 构建来源：[plusls/busybox-static](https://github.com/plusls/busybox-static)。中兴样本使用的程序实际版本是 BusyBox 1.37.0；构建项目的 Release 标签不等于程序版本。

## 许可

本仓库自己编写的文字按 [MIT 许可证](LICENSE) 提供。引用的项目和读者另行下载的程序仍适用各自的许可，不能用本仓库的 MIT 许可证替代。

没有复制或分发第三方源码、二进制和密钥。以后如果要打包第三方程序，须先核对并保留对应许可。

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

运营商、厂商和产品名称属于对应权利人。本教程不是运营商或设备厂商的官方操作指南，也不代表它们支持安装第三方服务。
