# macdata proM2 Codex Automation Task Pack

这是 `proM2` 专用任务包。它只服务于 `proM2`，不读取、不写入、不合并另一台设备的数据。

## 结论

- 使用方式：Codex Automation + 受控脚本。
- 脚本不会自动运行，不包含 launchd、cron、后台守护进程或自动安装脚本。
- Codex Automation 是唯一调度入口；脚本只是被调用的确定性工具。
- 每次运行都会生成全中文明文指标和报告。
- 每次运行通过唯一 `automation-c/macdata-proM2-*` 短命分支提交非 draft PR，由 trusted Settlement 合入 `main` 并删除事务分支；不创建 Issue。
- 只有 `main` 上逐文件 SHA-256 对账成功且 GitHub 回到 `0/0/0` 后，才删除本机 3 天以前的 macdata，并按 owner 白名单清理 Docker、Homebrew、系统缓存和项目缓存。
- PR/branch 收尾只由 trusted Settlement 执行；设备脚本只做只读终态审计。
- Time Machine 不采集，iCloud 不使用。

## 目录

```text
OpenAIDatabase/macdata/proM2/
  README.md
  AGENTS.md
  config/
    device_config.json
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
unzip /path/to/macdata_proM2_codex_automation_taskpack.zip
```

运行测试：

```bash
python3 -m unittest discover -s OpenAIDatabase/macdata/proM2/tests -p 'test_*.py'
python3 -m unittest OpenAIDatabase.macdata.tests.test_automation_c -q
```

## 首次运行前

让 Codex 读取：

```text
OpenAIDatabase/macdata/proM2/docs/CODEX_AUTOMATION_PROMPT.md
```

Codex 必须先问你 `FIRST_RUN_QUESTIONS.md` 里的确认问题。确认后，Codex 创建：

```text
OpenAIDatabase/macdata/proM2/config/owner_confirmations.json
```

没有这个确认文件，完整脚本会拒绝运行。

## 手动预检

```bash
python3 OpenAIDatabase/macdata/proM2/scripts/run_controlled_cycle.py --repo-root . --preflight-only
```

## 手动完整运行

只有确认无误时才运行：

```bash
python3 OpenAIDatabase/macdata/proM2/scripts/run_controlled_cycle.py --repo-root . --execute
```

本地无副作用模拟：

```bash
python3 OpenAIDatabase/macdata/proM2/scripts/run_controlled_cycle.py --repo-root . --simulate-transaction --simulation-stage raw --simulation-run-id proM2-test
```

## 禁止事项

- 不要把本包改成 launchd、cron 或本地守护进程。
- 不要扩大 Docker/Homebrew/系统缓存/项目缓存清理边界；Docker 默认不使用 `-a`，不清理 volumes；项目缓存只按白名单目录删除。
- 不要 direct-push `main`，不要重建 `macdata-proM2`，不要让设备脚本关闭 Issue 或删除非自身短命事务分支。
- 不要读取 API key、token、password、cookie、session、Keychain、shell history、完整环境变量、`.env` 原文。
- 不要让 `proM2` 任务读取或合并另一台设备的数据。
