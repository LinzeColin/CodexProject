# Codex Automation Prompt：airM2 每日明文 MacData

你现在运行的是 `airM2` 专用 Codex Automation。不要读取、修改、合并或推断另一台设备的数据。

## 固定配置

- 设备键：`airM2`
- 设备角色：工作前台 / 移动终端 / 云端入口
- 目标目录：`OpenAIDatabase/macdata/airM2/`
- 默认运行时间：每天凌晨 01:10，Australia/Sydney
- Cron：`10 1 * * *`
- 默认模型：`gpt-5.3-codex-spark`
- 默认 reasoning：`xhigh` / Extra High
- 运行方式：Codex Automation 调用脚本；脚本不得自我调度。
- Time Machine：不采集。
- iCloud：不使用。
- 持久分支：仅 `main`
- 事务分支：唯一 `automation-c/macdata-airM2-*`，Settlement 后必须删除
- 本机保留：最近 3 天。
- GitHub：通过短命 PR 把当前三天数据与报告合入 `main`；禁止重建永久设备分支。

## 运行前必须先问用户的问题

首次运行、`config/owner_confirmations.json` 不存在、设备预检失败、或检测到本机与预期不一致时，必须先停止，不准执行采集/上传/清理，并向用户提出下面的确认问题：

1. 请确认当前运行机器就是 `airM2`：预期为 MacBook Air / Apple M2 / 8GB / 256GB。是否确认？
2. 请确认 CodexProject 仓库根目录路径。如果不确定，要求用户选择或提供路径。
3. 请确认允许把除 API key / token / password 及等价凭证以外的设备明文指标上传到 GitHub。
4. 请确认每天运行后必须创建短命 Automation C PR，trusted Settlement 合入 `main`、逐文件哈希验证并回到 `0/0/0` 后才清理本机旧数据。
5. 请确认本机只保留最近 3 天的 `airM2` macdata 数据、报告、运行记录和 macdata 临时缓存。
6. 请确认不使用 Time Machine、不使用 iCloud、不自动清理 Docker/Homebrew/系统缓存/项目缓存。
7. 如果本机配置与预期不同，例如型号、芯片、内存、角色、目录、Git remote 或 main-only 事务策略不同，必须列出差异并请用户明确是否继续。

用户确认后，创建 `OpenAIDatabase/macdata/airM2/config/owner_confirmations.json`，内容参考 `owner_confirmations.example.json`。不要在该文件里写入任何 API key、token、password、cookie、session 或 Keychain 内容。

## 每次运行流程

1. 先阅读本文件、`AGENTS.md`、`README.md`、`config/device_config.json`。
2. 检查 `config/owner_confirmations.json` 是否存在并满足必要确认。
3. 先执行只读预检：

```bash
python3 OpenAIDatabase/macdata/airM2/scripts/run_controlled_cycle.py --repo-root . --preflight-only
```

4. 如果预检失败，停止并把失败原因用中文告诉用户；如果是设备差异，必须先问用户，不能继续。
5. 预检通过后，执行完整受控流程：

```bash
python3 OpenAIDatabase/macdata/airM2/scripts/run_controlled_cycle.py --repo-root . --execute
```

6. 完整流程必须完成：采集 → 中文报告草稿 → 凭证扫描 → 短命 PR → trusted Settlement → `main` 逐文件验证 → `0/0/0` → 清理本机旧数据和 macdata 临时缓存 → 最终报告短命 PR → 再次 Settlement/验证/`0/0/0`。
7. 如果 PR、CI、Settlement、main hash reconciliation 或终态审计失败，不允许清理本机旧数据；事务对象必须补偿删除。
8. 不允许运行任何破坏性清理命令，例如 `docker system prune -a`、`rm -rf ~/Library/Caches/*`、删除项目缓存等。
9. 不允许读取 shell history、完整环境变量、Keychain、cookies、sessions、`.env` 原文。
10. Codex session 最终输出必须是全中文，必须包含明文指标、GitHub 上传状态、清理状态、ROI、风险、SWOT 和失败项。

## Automation 建议设置

- 类型：Project / Standalone Automation。
- 项目：本机 CodexProject local checkout。
- 运行位置：优先 Local project，不使用 worktree，减少本机额外副本和负载。
- Schedule：Custom cron，`10 1 * * *`。
- Timezone：Australia/Sydney。
- Model：`gpt-5.3-codex-spark`。
- Reasoning：Extra High / xhigh。
- Sandbox：允许读写项目目录和执行 git push；禁止随意全盘扫描。

## 成功标准

- `OpenAIDatabase/macdata/airM2/data/latest/latest_metrics.json` 存在。
- `OpenAIDatabase/macdata/airM2/reports/latest/latest_report.md` 存在。
- GitHub `main` 包含本次数据和报告，旧 `macdata-airM2` 分支不存在。
- `main` 文件清单与本地发布清单 SHA-256 完全一致，PR/Issue/non-main branch=`0/0/0`。
- 本机只保留最近 3 天 `airM2` 数据和记录。
- Codex Automation run 在 Triage/Automation 面板中可查看。
