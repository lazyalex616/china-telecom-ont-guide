# 11：下载、安装、离线阅读和校验

[返回首页](../README.md)

## 先选包，不需要把所有附件都下载

| 文件 | 适合谁 | 包内内容 |
|---|---|---|
| `telecom-ont-toolkit-v1.1.0.zip` | 第一次使用，想保留完整材料 | 离线手册、四张技术图、全部章节、Skill、模板、安装器、校时源码及 SSH 启动模板 |
| `telecom-ont-agent-kit-v1.1.0.zip` | 只想给 Agent 安装能力 | 独立 Skill、含 SSH 在内的四份参考、三份记录表、一份启动提示词、安装器、入门和许可 |
| `telecom-ont-maintenance.skill` | 平台支持 Skill 文件导入 | 同一 Skill 的 ZIP 格式包，保留目录结构 |
| `telecom-ont-handbook-v1.1.0.html` | 只阅读或打印 | 单文件图文手册，所有插图和样式内嵌，没有外部字体、脚本或跟踪 |
| `SHA256SUMS.txt` | 核对下载是否完整 | 前面四个下载文件的 SHA256 |

GitHub 自动提供的 Source code 是源码快照，不含构建出来的单文件手册。一般用户优先选上表附件，而不是先克隆仓库再自己打包。

## Skill 能直接帮你做什么

它告诉支持 Skills 的 Agent：

- 先确认目标、授权和装维提供的有效超密；
- 怎样复现两个样本的登录会话；
- 怎样按菜单和现有对象做只读盘点；
- 怎样区分删除管理 WAN、语音依赖和真正上网连接；
- 怎样为 QoS、UPnP、防火墙和校时划定最小改动；
- 怎样按证据排查断网，而不是先怪光纤；
- 怎样回读、记录、脱敏和交付。
- 怎样解释和审阅明确授权后的原生应用 SSH，区分应用权限、主机身份、内网入口及重启验证。

它**不是独立运行的程序，也不替 Agent 提供浏览器、SSH、设备权限或密码**。不同 Agent 对 Skills 的识别方法不同，安装目录必须以你实际使用的平台为准。

## 安装器到底会做什么

在解压后的包根目录运行：

```sh
python tools/install-skill.py
```

默认只列计划。需要复制才运行：

```sh
python tools/install-skill.py --apply
```

安装范围只有：

```text
~/.agents/skills/telecom-ont-maintenance/
  SKILL.md
  LICENSE.txt
  references/
  assets/
```

如果你的 Agent 使用其他目录，先核实，再通过 `--target` 指定**父目录**。不要把最终的 `telecom-ont-maintenance` 目录也填进去，否则会多嵌套一层。

安装器不联网、不运行 Skill 中的步骤、不改 Agent 的 JSON、不安装依赖、不覆盖同名目录。已有 Skill 时会停，不提供 `--force`。升级前先自己审阅差异，不能靠本包悄悄覆盖自定义内容。

复制失败可能留下部分目录，安装器不会递归清理不明文件。按提示核查这一个目录，不要扩大到整个 Skills 目录。

## 没有 Python 怎么办

只读手册不需要 Python。Skill 可以手工复制整个目录，或按平台功能导入 `.skill`。

不要为了看文档安装一整套开发环境，也不要为了装 Skill 打开未知来源的“自动修复程序”。

## 支持范围

| 功能 | 环境 | 是否连接设备 |
|---|---|---|
| 离线 HTML / PNG / Markdown | 普通浏览器或阅读器 | 不会 |
| Skill 内容 | 支持 Skills 的 Agent | 由 Agent 在用户授权下使用已有工具 |
| Skill 安装器 | Python 3.9+，Windows / Linux / macOS | 不会 |
| 校时 `--help` / `--check-config` | Python 3.9+ | 不会 |
| 校时默认只读 | Python 3.9+、curl，且目标与管理路径已确认 | 一个本地 NTP 请求及光猫 HTTP 时钟读取 |
| 校时 `--apply` | Linux / OpenWrt、所需标准库、curl、OpenSSL | 会认证，必要时临时访问并只改时间 |
| SSH `ont-ssh.init` | 已逐项核实的 SAF 应用内 `rc.common`，已准备程序与密钥并单独获批 | 只是源码模板，不自动部署；手工配置并启动后会开启 SSH 监听 |

公开整理版的功能检查边界见 [案例结果](10-case-results-and-lessons.md)。打包和语法通过，不等于在所有系统、Agent 或固件上完成行为测试。

完整包包含 SSH 方法和启动模板，但**不包含 Dropbear 可执行文件、客户端私钥、主机密钥或真实站点配置**。轻量 Agent 包和 `.skill` 只含 SSH 的方法参考，不带该启动模板。先读 [第 12 章](12-native-app-ssh.md)，不要因为安装 Skill 就去连接光猫或开服务。

## 模板怎么用

先读模板说明，再复制到你自己选定的私密记录位置：

- [只读启动提示词](../skills/telecom-ont-maintenance/assets/start-readonly.md)
- [只读盘点表](../skills/telecom-ont-maintenance/assets/read-only-inventory.md)
- [变更与验收表](../skills/telecom-ont-maintenance/assets/change-acceptance.md)
- [断网证据表](../skills/telecom-ont-maintenance/assets/dropout-evidence.md)

记录的是字段含义、状态、覆盖情况和验证，不是原始配置。密码、完整账号、唯一标识和票据不要填进去。模板不是自动脱敏器，填写后的内容公开前仍要逐项审阅。

## 怎样核对 SHA256

先从同一个 Release 下载对应文件与 `SHA256SUMS.txt`。

Windows PowerShell：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\telecom-ont-toolkit-v1.1.0.zip'
```

Linux：

```sh
sha256sum telecom-ont-toolkit-v1.1.0.zip
```

macOS：

```sh
shasum -a 256 telecom-ont-toolkit-v1.1.0.zip
```

把完整的 64 位结果与 `SHA256SUMS.txt` 的同名行比较。没有下载其他附件时，不要把“缺少其他文件”当成当前包损坏。

ZIP 内的 `PACKAGE-MANIFEST.json` 还列了每个包内文件的 SHA256；`BUILD-INFO.json` 标明版本和来源提交。清单不包含自身，避免循环校验。

SHA256SUMS 不是数字签名。如果攻击者能同时替换附件和校验表，仅有这张表无法抵御这种攻击，不要把它说成签名验证。

## 如何卸载

安装器只复制了一个目录。确认是自己安装的这份内容后，只移除 `telecom-ont-maintenance` 这一目录即可，不改其他 Skill，不重置 Agent 配置。

本包不会自动部署校时或 SSH、写入定时任务、开启 NTP 或修改光猫，所以卸载 Skill 不需要操作任何生产设备。若你后来自己部署了额外任务或服务，应按当时的部署记录单独处理。

## 给维护者：重建发行附件

源码中提供 [build-release.py](../tools/build-release.py)，从干净的已提交 Git 状态和明确的文件白名单构建，不把整个工作目录压进去。

构建使用 Python 3.9+ 和 Mistune 3.x；这只是发布者的依赖，读者阅读手册、安装 Skill 和运行参考工具不需要 Mistune。依赖清单见 [requirements-release.txt](../requirements-release.txt)。

```sh
python tools/check-repository.py
python tools/build-release.py --version v1.1.0
```

构建器不会联网、连接光猫、安装 Skill 或发布 GitHub。它生成本地附件和图文 Release 正文，发布仍需明确授权并由维护者执行。
