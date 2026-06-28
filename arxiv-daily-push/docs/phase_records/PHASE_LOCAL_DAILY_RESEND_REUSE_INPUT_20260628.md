# 本地每日补发复用输入记录

- 任务 ID: `LOCAL-DAILY-RESEND-REUSE-INPUT`
- 时间: `2026-06-28T11:12:24+10:00`
- 范围: 只改本地 `local-runner daily` 的补发入口，使人工补发可以显式传入当天已生成的 `adp-daily-input-report.json`。
- 变更: 新增 CLI 参数 `--daily-input-report`，`run_local_daily` 支持 `daily_input_source=existing_report`，并写入 `daily_input_report_path` 作为证据。
- 防误发: 当复用报告中的 `date` 或 `daily_input.date` 与本次 `--date` 不一致时，runner 直接阻断。
- 不做事项: 不改邮件正文模板，不改公共 schema，不改评分/排序公式，不改来源板块，不启用 scheduler，不上传 Release，不切换 CURRENT，不声称真实补发已经成功。
- 验证:
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_resend_reuse_tests PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_local_runner.py -q` -> `12 OK`
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_resend_reuse_full PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest discover -s arxiv-daily-push/tests -q` -> `644 OK`
  - `git diff --check` -> `PASS`
  - `python3 arxiv-daily-push/scripts/update_user_center_timestamps.py --check` -> `18 pages valid`
- 回滚: 回退 `local_runner.py`、`cli.py`、`test_local_runner.py` 和本任务治理记录即可；不会产生队列、schema、scheduler 或 Release 侧状态迁移。
