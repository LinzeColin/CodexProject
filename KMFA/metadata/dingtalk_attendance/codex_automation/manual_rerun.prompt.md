# 每日早晚钉钉考勤检查｜手动补跑

手动补跑时只允许选择 `morning` 或 `evening`。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type morning --timezone Asia/Shanghai
```

补跑仍需遵守 live-only、OneDrive 私有归档、三天 operational cache 清理和泄密扫描。
