# 来源、适用范围与第三方说明

## 本教程的案例来源

教程按两台已授权设备的维护过程重新编写：上海电信的中兴 ZXHN G7615V2，以及浙江电信的 ZNXT ZN-XG120。

公开材料不包含实际用户凭据、设备唯一标识、站点名称、私人网络规划、原始配置或会话附件。省份和通用型号保留用于说明适用范围。

## 中兴临时认证协议

公开校时工具的中兴路径只实现 `webFac v3 / re_rand` 的临时认证，不包括固化、刷机、分区导出或恢复流程。

主要参考：

- [qiudz/zte-f7015tv3-telnet-solidify](https://github.com/qiudz/zte-f7015tv3-telnet-solidify)
- [该项目的 webFac v3 协议说明](https://github.com/qiudz/zte-f7015tv3-telnet-solidify/blob/main/docs/webfac-v3-protocol.md)

以上项目采用 MIT 许可证。我们保留其相关许可说明。这个项目的名字含有“固化”，不意味着本教程建议执行固化脚本。

下面这个项目仅作为旧协议和工具适用范围的比较来源：

- [Septrum101/zteOnu](https://github.com/Septrum101/zteOnu)

它当前声明 AGPL-3.0。本公开工具不包含其 v1/v2 实现或密钥池，不应把该项目整体复制后改标为 MIT。

## iKuai CLI

示例 CLI 来源：

- [ikuaidev/ikuai-cli](https://github.com/ikuaidev/ikuai-cli)

当前项目声明 MIT。教程中的命令只是对应版本的使用示意，不保证今后的 CLI、API 和设备固件保持不变。

尤其注意：CLI 帮助、后端参数和设备实际行为可能不完全一致，所有写操作仍须预览、核对并回读。

## Dropbear、Zig 与应用启动框架

[原生应用 SSH 章节](docs/12-native-app-ssh.md) 记录了从上游构建 Dropbear 2026.94 的方法：

- [Dropbear 上游仓库](https://github.com/mkj/dropbear)
- [对应版本的多功能二进制构建说明](https://github.com/mkj/dropbear/blob/DROPBEAR_2026.94/MULTI.md)
- [对应版本的完整 LICENSE](https://github.com/mkj/dropbear/blob/DROPBEAR_2026.94/LICENSE)
- [Zig 0.13.0 发布与下载页](https://ziglang.org/download/0.13.0/)

Dropbear 包含不同来源、不同许可的组件，不能用本仓库的 MIT 标记替代其完整许可。本仓库只提供自己编写的构建说明和启动模板，**没有打包 Dropbear 源码、二进制、Zig 编译器或它们的依赖**；读者自行再分发产物时须核对并保留上游及实际包含组件的全部许可。

`tools/ont-ssh.init` 使用目标系统已有的 `/etc/rc.common` 接口，不包含或替换 OpenWrt 的启动框架。该模板只适用于已核实的 SAF 应用环境，不代表运营商或设备厂商对第三方服务提供支持。

## MIT 上游许可正文

以下是上述 v3 参考项目的 MIT 许可文本：

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

## 使用边界

- 只维护本人或已明确授权的设备。
- 必须先取得当前有效超密。
- 不提供猜密、弱口令表或绕过设备所有者授权的流程。
- 本教程不是运营商官方配置规范。
- 厂商、运营商和产品名称属于相应权利人。
- 文档和代码按现状提供，不能替代对当前设备的检查。
