# S19 每日早晚钉钉考勤检查完成记录

## 范围

- 新增 S19 public-safe 钉钉考勤自动化结构。
- Automation 名称固定为 `每日早晚钉钉考勤检查`。
- 每天北京时间 08:35 运行晨报，18:15 运行晚报。
- OneDrive 私有归档固定为 `/Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/`，当月目录下直接保存运行文件。
- 张霖泽 DingTalk userId 固定为 `1iv-1t2oesv2yd`。
- DWS live backend 使用 `dws contact dept list-children/list-members` 枚举组织成员，并调用 `dws attendance record get` 与 `dws attendance summary`。

## 边界

- GitHub 不保存真实员工考勤明文、SQLite、raw API response、报告正文或凭据材料。
- DWS profile 不可用时返回 `DWS_UNAVAILABLE`，不生成样例员工或假打卡。
- 管理报告不包含“关键人员风险”章节。
- 本记录代表 2026-07-07 已完成一次 DWS live 取数验证；通知仍未实际发送。

## Live 验证摘要

- 验证日期: `2026-07-07`
- 验证运行: `s19_evening_20260707_095119`
- 当前可见组织人数: `44`
- record 成功: `44`
- summary 成功: `44`
- 当天有打卡记录: `42`
- 已知无考勤记录且 record 为空: `张霖泽`, `林全意`
- 非预期空 record: `0`
- 原始私有归档: `/Users/linzezhang/OneDrive/dingtalk_attendance/202607/s19_evening_20260707_095119.raw.jsonl.gz`
- raw SHA256: `aabfb6415d95f55d76890d74ef60d3430785f404210679631be470eb47f3a811`

## 关键文件

- `KMFA/tools/dingtalk_attendance/`
- `KMFA/metadata/dingtalk_attendance/`
- `KMFA/tests/test_dingtalk_attendance.py`
- `KMFA/stage_artifacts/S19_DINGTALK_ATTENDANCE/machine/s19_manifest.json`
