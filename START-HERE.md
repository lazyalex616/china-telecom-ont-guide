# 下载后从这里开始

**先向装维师傅取得本人或已授权设备当前有效的超级管理员账号和密码。没有超密，先做阅读和准备，不猜密码。**

这是中文电信光猫维护工具包，不是一键桥接或破解器。安装 Skill 不会自动登录、修改或扫描设备。

## 1. 只看教程

完整包中直接打开 `offline-handbook.html`。不需要 Python、Git、联网或开启本地服务，四张技术图已内嵌。源文档仍保留在 `docs/` 中。

如果只下载了独立 HTML，浏览器打开即可。涉及代码和配置的链接会指向线上版本，离线读正文和图片不受影响。

## 2. 给 Agent 安装 Skill

在**解压后的包目录**打开终端，先预览，不写入：

```sh
python tools/install-skill.py
```

确认你使用的是支持 `~/.agents/skills/` 的 Agent，再明确执行复制：

```sh
python tools/install-skill.py --apply
```

Linux / macOS 的 Python 命令可能叫 `python3`。安装器只需要 Python 3.9 或以上和标准库，不下载任何东西，不改 Agent 配置，不覆盖已有目录。

其他 Agent 可用 `--target` 明确指定它实际支持的 Skills 父目录，不自动猜路径。例如，确认你的 Claude Code 版本使用该目录后：

```sh
python tools/install-skill.py --target ~/.claude/skills
```

上面仍然只是预览，需要复制才再加 `--apply`。若平台支持 `.skill` 导入，可直接使用 Release 的 `telecom-ont-maintenance.skill`。这个文件本质是 ZIP，不是脚本或模型。

不想运行安装器，也可以手动把整个 `skills/telecom-ont-maintenance/` 目录复制到 Agent 的 Skills 目录，保留 `references/` 和 `assets/`。已有同名目录时先停，不要覆盖自己的修改。

## 3. 直接把这句话交给 Agent

```text
请使用 telecom-ont-maintenance Skill。我的设备属于本人或已获明确授权，
我会从装维师傅取得当前有效超密，并通过安全凭据存储提供，不贴在报告里。
本次只允许盘点，不允许保存设置、开启命令入口、重拨、重启或新增网络配置。
先确认目标设备、拓扑、谁在拨号和管理路径，再使用包内模板整理覆盖清单。
没有授权的现有管理通道时先说明限制，不要自动安装、启用插件或切换浏览器。
```

如果 Agent 没有识别到 Skill，按它自身的说明重新加载会话或指定 `SKILL.md`，不要为了加载 Skill 随便改整份配置。启动提示词和记录模板在 `skills/telecom-ont-maintenance/assets/`，完整包另有分任务提示词。

## 4. 高级用户再看校时工具

先查看帮助，完全不联网：

```sh
python tools/ont-clock.py --help
```

**不要把示例中的管理地址当成你的实际设备。** 先确认地址、设备身份和安全管理路径，再按校时章节准备你自己的私密配置。

`--check-config` 只检查本地文件；默认运行会发送 NTP 和 HTTP 只读请求；`--apply` 可能开启临时命令访问并修改光猫时间。三者不是同一权限。写入还要求本机配置 `allow_time_change=true`，仅支持 Linux / OpenWrt 和两个已记录样本。

原型在两个案例中验证过，公开整理版没有再次连接生产设备测试，不保证其他固件即插即用。先读完整校时章节，再决定是否采用。

## 5. 想了解 SSH，先看方法和边界

阅读 [12：原生应用 SSH](docs/12-native-app-ssh.md)。两台样本通过已有合法维护通道，在光猫原生 SAF 应用中安装 Dropbear，实际密钥登录成功；不是刷固件，也不是找到了通用 SSH 开关。

完整包附 `tools/ont-ssh.init`，默认占位地址不能启动。它不是安装器，不包含密钥或 Dropbear 二进制，不适用于未核实的主系统启动目录。只安装 Skill 不会运行它，轻量 Agent 包也不带这个模板。

应用内 root 不等于主系统 root，自启动已注册不等于重启实测通过。安装、临时入口、路由器写入和真实登录验证都要各自获得授权；不能为了发布或读教程去连接生产设备。

## 下载完整性

Release 提供 `SHA256SUMS.txt`。校验下载包的 SHA256 应与其中同名文件一致，这只能检查文件有没有变化，不等于对运行结果或固件兼容性作保证。

完整说明、兼容范围和卸载方法：[安装与使用详解](docs/11-download-and-use.md)。
