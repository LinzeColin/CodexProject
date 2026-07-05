# macdata airM2 Codex Automation Task Pack

这是 `airM2` 专用任务包。它只服务于 `airM2`，不读取、不写入、不合并另一台设备的数据。

## 结论

- 使用方式：Codex Automation + 受控脚本。
- 脚本不会自动运行，不包含 launchd、cron、后台守护进程或自动安装脚本。
- Codex Automation 是唯一调度入口；脚本只是被调用的确定性工具。
- 每次运行都会生成全中文明文指标和报告。
- 每次运行都会 commit + push 到 GitHub 归档分支 `macdata-airM2`。
- 只有远程验证成功后，才删除本机 3 天以前的 `airM2` macdata 数据、报告、记录和 macdata 临时缓存，并执行用户确认过的受控 Docker、Homebrew、用户态系统缓存、项目缓存清理。
- Time Machine 不采集，iCloud 不使用。

## 目录

```text
OpenAIDatabase/macdata/airM2/
  README.md
  AGENTS.md
  HANDOFF.md
  功能清单.md
  开发记录.md
  模型参数文件.md
  config/
    device_config.json
    owner_confirmations.json
    owner_confirmations.example.json
  scripts/
    run_controlled_cycle.py
  docs/
    CODEX_AUTOMATION_PROMPT.md
    CODEX_AUTOMATION_SETUP.md
    FIRST_RUN_QUESTIONS.md
    OPERATIONS_RUNBOOK.md
  data/
    current_3days/raw/
    latest/
    run_logs/
    cache/archive_push/
  reports/
    current_3days/
    latest/
  tests/
    test_macdata_package.py
```

## 安装到 CodexProject

在仓库根目录解压本包：

```bash
cd /path/to/CodexProject
unzip /path/to/macdata_airM2_codex_automation_taskpack.zip
```

运行测试：

```bash
python3 -m unittest discover -s OpenAIDatabase/macdata/airM2/tests -p 'test_*.py'
```

## 首次运行前

让 Codex 读取：

```text
OpenAIDatabase/macdata/airM2/docs/CODEX_AUTOMATION_PROMPT.md
```

Codex 必须先问你 `FIRST_RUN_QUESTIONS.md` 里的确认问题。确认后，Codex 创建：

```text
OpenAIDatabase/macdata/airM2/config/owner_confirmations.json
```

没有这个确认文件，完整脚本会拒绝运行。

## 手动预检

```bash
python3 OpenAIDatabase/macdata/airM2/scripts/run_controlled_cycle.py --repo-root . --preflight-only
```

## 手动完整运行

只有确认无误时才运行：

```bash
python3 OpenAIDatabase/macdata/airM2/scripts/run_controlled_cycle.py --repo-root . --execute
```

## 禁止事项

- 不要把本包改成 launchd、cron 或本地守护进程。
- 不要使用 sudo、`docker system prune -a`、Docker volumes 删除、`rm -rf ~/Library/Caches/*` 或删除项目源码/数据；清理只允许走脚本里的受控目标和命令。
- 不要读取 API key、token、password、cookie、session、Keychain、shell history、完整环境变量、`.env` 原文。
- 不要让 `airM2` 任务读取或合并另一台设备的数据。
