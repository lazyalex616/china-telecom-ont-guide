# Agent Skill 包：解压后从这里开始

这份包只装一个 Skill，不含校时程序，不会连接或修改光猫。先向装维师傅取得本人或已授权设备当前有效超密，通过安全存储交给 Agent，不贴进聊天日志和报告。

## 安装

在解压后的包目录运行，默认只预览：

```sh
python tools/install-skill.py
```

确认你的 Agent 支持 `~/.agents/skills/` 后，再复制：

```sh
python tools/install-skill.py --apply
```

需要 Python 3.9+ 和标准库，Linux / macOS 的命令可能是 `python3`。安装器不联网、不改 Agent 配置、不覆盖已有目录。其他平台先核实目录，再用 `--target` 指定 Skills 父目录。

不使用安装器，也可手动复制整个 `skills/telecom-ont-maintenance/`，不要只拿走 `SKILL.md`，`references/` 和 `assets/` 都要保留。

## 开始使用

复制 [只读启动提示词](skills/telecom-ont-maintenance/assets/start-readonly.md) 给你的 Agent，明确本次只读。Agent 必须已有经过授权的管理工具和路径，Skill 不会替它装浏览器或启用插件。

直接使用包内 [盘点表](skills/telecom-ont-maintenance/assets/read-only-inventory.md)、[变更验收表](skills/telecom-ont-maintenance/assets/change-acceptance.md) 和 [断网证据表](skills/telecom-ont-maintenance/assets/dropout-evidence.md)。填写后的内容仍需脱敏，不自动上传。

如果没有识别到 Skill，按 Agent 自身说明重新加载或指定 `SKILL.md`。不要因此重置全部配置。

完整教程、图解和高级校时参考请另外选 [完整工具包](https://github.com/lazyalex616/china-telecom-ont-guide/releases/latest)。没有超密不猜，建议不等于修改授权，不擅自重启、切桥接或改光路身份。

## 校验与卸载

ZIP 中的 `BUILD-INFO.json` 标明来源提交，`PACKAGE-MANIFEST.json` 列出文件摘要。Release 的 `SHA256SUMS.txt` 可检查下载完整性，它不是数字签名。

卸载只移除你自己安装的 `telecom-ont-maintenance` 目录，不动其他 Skill 或 Agent 配置。
