# 每日早晚钉钉考勤检查｜晚报

每天北京时间 18:15 在 KMFA local main checkout 执行。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type evening --timezone Asia/Shanghai
```

输出中文摘要：取数状态、异常人数、管理报告状态、HR 报告状态、通知状态、OneDrive 归档状态、清理状态、数据库大小、泄密风险。不得创建 PR、issue、branch 或 worktree。
