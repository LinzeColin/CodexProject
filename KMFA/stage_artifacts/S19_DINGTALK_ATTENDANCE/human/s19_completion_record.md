# S19 每日早晚钉钉考勤检查完成记录

## 范围

- 新增 S19 public-safe 钉钉考勤自动化结构。
- Automation 名称固定为 `每日早晚钉钉考勤检查`。
- 每天北京时间 08:35 运行晨报，18:15 运行晚报。
- OneDrive 私有归档固定为 `/Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/`，当月目录下直接保存运行文件。
- 张霖泽 DingTalk userId 固定为 `1iv-1t2oesv2yd`。

## 边界

- GitHub 不保存真实员工考勤明文、SQLite、raw API response、报告正文或凭据材料。
- 未配置真实钉钉权限时返回 `CONFIG_MISSING`，不生成样例员工或假打卡。
- 管理报告不包含“关键人员风险”章节。
- 本记录不代表真实钉钉取数成功，也不代表通知已实际发送。

## 关键文件

- `KMFA/tools/dingtalk_attendance/`
- `KMFA/metadata/dingtalk_attendance/`
- `KMFA/tests/test_dingtalk_attendance.py`
- `KMFA/stage_artifacts/S19_DINGTALK_ATTENDANCE/machine/s19_manifest.json`
