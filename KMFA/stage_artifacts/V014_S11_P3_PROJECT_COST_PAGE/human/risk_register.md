# KMFA v0.1.4 S11-P3 Risk Register

| Risk | Control | Status |
|---|---|---|
| 项目成本页面被误解为正式项目成本报告 | validator 锁定 report grade D、formal_report_allowed=false、business_decision_basis_allowed=false | controlled |
| 报告预览被误解为可绕过质量等级 | HTML、manifest 和 validator 均锁定 quality_grade_bypass_allowed=false | controlled |
| 项目详情交互写回 raw 层 | control event only，raw_layer_write_allowed=false | controlled |
| 单 phase 越界进入 Stage 11 review 或 GitHub upload | phase boundaries 与 validator 均要求 false | controlled |
| public evidence 泄露 raw/private 信息 | validator 扫描本 phase evidence 文本并锁定 raw/private boundary | controlled |
