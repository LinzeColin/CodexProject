# PHASE S2PMT04 Scheduler Template A-013 Cross-Platform Supplement

## 状态

- status: `completed_local_validation`
- phase: `S2PM`
- task_id: `S2PMT04`
- finding_id: `A-013`
- finding_title: `调度模板路径未结构化转义，macOS plist 甚至不可解析`
- completed_at: `2026-06-26T20:42:28+10:00`

## 范围

本记录补强 V7.1 inherited P1 finding `A-013` 的跨平台 scheduler template 证据：

- macOS 保持 `plistlib` 生成的 disabled launchd plist 和逐参数 `ProgramArguments`。
- Linux `systemd` dry-run install 生成独立 `adp-stage1.env`，service 使用 `EnvironmentFile=`，`ExecStart=` 逐参数 quote。
- Windows dry-run install 生成 `$ArgumentList = @(...)`，由 `Join-CommandArgument` 统一转成 scheduled-task `-Argument`，避免旧的整段 shell-like 字符串。
- 回归覆盖路径中包含空格、中文、分号和 `&` 的 project/state path。

## 非范围

本记录不安装 scheduler，不执行 launchd bootstrap/systemctl/Register-ScheduledTask，不启用 SMTP、Release、production restore、真实生产队列、公共 Schema、DB migration、source adapter、ranking、`CURRENT` 或 V7.1/V7.2 合同文件；不关闭 inherited P0/P1；不声明 `INTEGRATED_PRODUCTION_ACCEPTED`、`DAILY_OPERATION` 或 Stage 2 生产通过。

## 代码证据

- `arxiv-daily-push/src/arxiv_daily_push/stage1_runtime.py`
- `arxiv-daily-push/tests/test_stage1_runtime.py`
- `governance/run_manifests/ADP-S2PMT04-SCHEDULER-TEMPLATE-A013-CROSS-PLATFORM-20260626.json`

## 验证

- `py_compile`: PASS
- `python3 -m unittest arxiv-daily-push/tests/test_stage1_runtime.py arxiv-daily-push/tests/test_stage2_lifecycle_cache.py -q`: 22 OK
- `python3 -m unittest arxiv-daily-push/tests/test_user_center_candidate_pool.py -q`: 7 OK
- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: 509 OK
- `python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 / warnings 0
- `python3 arxiv-daily-push/docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root arxiv-daily-push/docs/pursuing_goal/v7_2`: PASS
- `python3 -m json.tool governance/run_manifests/ADP-S2PMT04-SCHEDULER-TEMPLATE-A013-CROSS-PLATFORM-20260626.json`: PASS
- `git diff --check`: PASS
- 外部 `systemd-analyze` / `pwsh` parser: NOT RUN，本机命令不可用；本轮用 Python `plistlib`、`configparser` 和 PowerShell 参数数组结构检查作为 local gate。

## 剩余阻断

- 本修复只提供 A-013 的跨平台模板补强证据。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。
