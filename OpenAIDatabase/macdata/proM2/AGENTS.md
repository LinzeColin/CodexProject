# AGENTS.md：proM2 macdata 规则

## 强制边界

1. 只操作 `OpenAIDatabase/macdata/proM2/`。
2. 不读取、不修改、不合并 `OpenAIDatabase/macdata/` 下其他设备目录。
3. 不采集 Time Machine。
4. 不使用 iCloud。
5. 不设置 launchd、cron、后台服务或自动启动脚本。
6. 远程上传验证成功后，按 owner 确认的白名单策略自动清理 Docker、Homebrew、系统缓存和项目缓存。
7. 不读取 API key、token、password、cookie、session、Keychain、shell history、完整环境变量、`.env` 原文。
8. 除凭证类数据外，用户允许设备明文指标进入 GitHub。
9. 首次运行和设备差异时必须先问用户。
10. 每次运行必须经 `automation-c/*` 短命 PR、trusted Settlement 合入 `main` 并逐文件远程验证；验证失败不得清理本机旧数据。
13. 禁止重建 `macdata-proM2` 永久分支；设备脚本只审计 `0/0/0`，不得成为第二个 GitHub janitor。
11. 本机仅保留最近 3 天 `proM2` 数据、报告、运行记录和 macdata 临时缓存；开发环境清理不得读取或输出凭证。
12. 报告必须全中文。

## 稳定交付原则

- 先预检，后执行。
- 先上传，后清理。
- 先验证，后删除。
- 采不到的字段写“未采集”，不能猜。
- 如果出现设备不匹配、Git remote 不可用、push 失败、凭证扫描失败，必须停止并明文报告。
