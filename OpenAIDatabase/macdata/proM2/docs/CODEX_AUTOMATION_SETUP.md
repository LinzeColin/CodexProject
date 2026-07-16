# proM2 Codex Automation 建立与监控说明

## 目标

建立一个受控的 Codex Automation：每天 01:10 运行 `proM2` macdata，输出全中文明文指标和报告，通过短命 Automation C PR 合入 `main`，验证成功且回到 `0/0/0` 后只保留本机最近 3 天记录并执行受控缓存清理。

## 在 Codex 里创建 Automation

在 CodexProject 项目里对 Codex 说：

```text
请为当前项目创建一个 Project / Standalone Automation。
名称：macdata proM2 daily controlled archive
Schedule：每天 01:10 Australia/Sydney
Cron：10 1 * * *
Model：gpt-5.3-codex-spark
Reasoning：xhigh / Extra High
运行位置：Local project，尽量不使用 Worktree，减少本机额外副本和负载。
请使用下面这个 prompt 文件作为 automation prompt：
OpenAIDatabase/macdata/proM2/docs/CODEX_AUTOMATION_PROMPT.md
```

Codex 官方文档说明，project-scoped automations 运行时，本机 Codex app 必须开着、机器必须开机、项目路径必须可用；automation runs 会出现在 Codex app 的 Automations pane / Triage 中。官方文档也说明可显式选择 model 和 reasoning effort。

## 你如何监控

每天运行后检查：

1. Codex app sidebar → Automations。
2. 查看 `macdata proM2 daily controlled archive`。
3. 查看当天 run 是否成功。
4. 查看 Triage 中的中文明文报告。
5. 查看 GitHub `main` 是否出现当天数据，并确认旧 `macdata-proM2` 和短命事务分支均不存在。
6. 查看本机 `OpenAIDatabase/macdata/proM2/reports/latest/latest_report.md`。

## 成功状态

- 远程上传已验证。
- 本机三天保留达成。
- 受控开发环境清理状态进入报告。
- trusted Settlement 与 `0/0/0` 只读终态审计进入报告。
- GitHub 上仅 `main` 持久存在，不残留 `macdata-proM2` 或短命事务分支。
- 没有凭证扫描失败。
- 没有设备角色不匹配。
- 报告为全中文。

## 如果 Automation 没有运行

优先检查：

1. Mac 是否开机。
2. Codex app 是否正在运行。
3. CodexProject 项目路径是否仍存在。
4. Automation 是否启用。
5. Schedule 是否为 `10 1 * * *`，时区是否为 Australia/Sydney。
6. GitHub remote 是否可 push。
