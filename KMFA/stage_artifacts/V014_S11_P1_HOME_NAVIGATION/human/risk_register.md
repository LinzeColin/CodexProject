# KMFA v0.1.4 S11-P1 Risk Register

| Risk | Control | Status |
|---|---|---|
| 首页导航被误解为正式经营报告 | validator 锁定 report grade D、formal_report_allowed=false、business_decision_basis_allowed=false | controlled |
| v1.4 HTML 样板只被引用但未反映到实现 | validator 同时检查 v1.4 审计基线和首页 HTML 的按钮、反馈面板、报告中心入口 | controlled |
| 单 phase 越界进入 S11-P2/S11-P3 或 Stage 11 review | phase boundaries 与 validator 均要求 false | controlled |
| public evidence 泄露 raw/private 信息 | validator 扫描本 phase evidence 文本并锁定 raw/private boundary | controlled |
