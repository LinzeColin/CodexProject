# KMFA v0.1.4 S11-P2 Risk Register

| Risk | Control | Status |
|---|---|---|
| 数据源检查板被误解为数据已可用于正式报告 | validator 锁定 report grade D、formal_report_allowed=false、business_decision_basis_allowed=false | controlled |
| 状态变更被误解为写回原始数据 | HTML 和 manifest 均锁定 control event only、raw_layer_write_allowed=false | controlled |
| v1.4 human-flow 搜索和状态反馈缺失 | validator 检查搜索输入、反馈区、状态变更动作和详情预览 | controlled |
| 单 phase 越界进入 S11-P3 或 Stage 11 review | phase boundaries 与 validator 均要求 false | controlled |
| public evidence 泄露 raw/private 信息 | validator 扫描本 phase evidence 文本并锁定 raw/private boundary | controlled |
