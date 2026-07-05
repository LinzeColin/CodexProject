# Codex Automation Prompt：proM2 每日明文 MacData

你现在运行的是 `proM2` 专用 Codex Automation。不要读取、修改、合并或推断另一台设备的数据。

## 固定配置

- 设备键：`proM2`
- 设备角色：主开发电脑
- 目标目录：`OpenAIDatabase/macdata/proM2/`
- 默认运行时间：每天凌晨 01:10，Australia/Sydney
- Cron：`10 1 * * *`
- 默认模型：`gpt-5.3-codex-spark`
- 默认 reasoning：`xhigh` / Extra High
- 运行方式：Codex Automation 调用脚本；脚本不得自我调度。
- Time Machine：不采集。
- iCloud：不使用。
- 数据归档分支：`macdata-proM2`
- 本机保留：最近 3 天。
- GitHub：保留完整历史，通过归档分支提交历史读取。

## 运行前必须先问用户的问题

首次运行、`config/owner_confirmations.json` 不存在、设备预检失败、或检测到本机与预期不一致时，必须先停止，不准执行采集/上传/清理，并向用户提出下面的确认问题：

1. 请确认当前运行机器就是 `proM2`：owner 覆盖后的预期为 MacBook Pro / Apple M2 Max / 32GB / 约 1TB。是否确认？
2. 请确认 CodexProject 仓库根目录路径。如果不确定，要求用户选择或提供路径。
3. 请确认允许把除 API key / token / password 及等价凭证以外的设备明文指标上传到 GitHub。
4. 请确认每天运行后必须 commit + push 到 `macdata-proM2` 归档分支，并在远程验证成功后才清理本机旧数据。
5. 请确认本机只保留最近 3 天的 `proM2` macdata 数据、报告、运行记录和 macdata 临时缓存。
6. 请确认不使用 Time Machine、不使用 iCloud；远程上传验证成功后，允许按白名单策略自动清理 Docker/Homebrew/系统缓存/项目缓存。
7. 请确认远程上传验证成功后，允许清理 automation/Codex 创建且已合入 `main` 的临时 PR、临时 branch 和带 managed marker 的 issue；必须保护 `main` 与 `macdata-proM2` 归档分支。
8. 如果本机配置与预期不同，例如型号、芯片、内存、角色、目录、Git remote、归档分支不同，必须列出差异并请用户明确是否继续。

用户确认后，创建 `OpenAIDatabase/macdata/proM2/config/owner_confirmations.json`，内容参考 `owner_confirmations.example.json`。不要在该文件里写入任何 API key、token、password、cookie、session 或 Keychain 内容。

## 每次运行流程

1. 先阅读本文件、`AGENTS.md`、`README.md`、`config/device_config.json`。
2. 检查 `config/owner_confirmations.json` 是否存在并满足必要确认。
3. 先执行只读预检：

```bash
python3 OpenAIDatabase/macdata/proM2/scripts/run_controlled_cycle.py --repo-root . --preflight-only
```

4. 如果预检失败，停止并把失败原因用中文告诉用户；如果是设备差异，必须先问用户，不能继续。
5. 预检通过后，执行完整受控流程：

```bash
python3 OpenAIDatabase/macdata/proM2/scripts/run_controlled_cycle.py --repo-root . --execute
```

6. 完整流程必须完成：采集 → 生成全中文明文报告 → 凭证扫描 → commit → push → 远程验证 → 验证成功后清理本机 3 天以前数据、macdata 临时缓存、受控开发环境缓存、已合并临时 PR/branch/managed issue → 输出全中文明文报告。
7. 如果 push 或远程验证失败，不允许清理本机旧数据。
8. 不允许运行越界破坏性清理命令，例如 `docker system prune -a`、`docker system prune --volumes`、`rm -rf ~/Library/Caches/*`、删除 `node_modules` 或 `.venv`；只允许配置白名单内的受控清理。
9. 不允许读取 shell history、完整环境变量、Keychain、cookies、sessions、`.env` 原文。
10. 不允许删除 `main`、`macdata-proM2`、未合入 `main` 的分支、没有 managed marker 的 issue，或任何非本 automation/Codex 创建的协作对象。
11. Codex session 最终输出必须是全中文，必须包含明文指标、GitHub 上传状态、清理状态、PR/branch/issue 收尾状态、ROI、风险、SWOT 和失败项。

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

- `OpenAIDatabase/macdata/proM2/data/latest/latest_metrics.json` 存在。
- `OpenAIDatabase/macdata/proM2/reports/latest/latest_report.md` 存在。
- GitHub 归档分支 `macdata-proM2` 包含本次提交。
- 远程 hash 与本地提交 hash 一致。
- 本机只保留最近 3 天 `proM2` 数据和记录。
- Docker/Homebrew/系统缓存/项目缓存清理状态进入中文报告。
- 已合入 `main` 的 automation/Codex 临时 PR/branch/managed issue 收尾状态进入中文报告；`main` 和 `macdata-proM2` 必须仍存在。
- Codex Automation run 在 Triage/Automation 面板中可查看。
