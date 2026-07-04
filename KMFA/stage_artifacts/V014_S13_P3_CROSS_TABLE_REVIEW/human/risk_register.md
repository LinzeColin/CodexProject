# KMFA v0.1.4 S13-P3 Risk Register

| Risk | Control | Status |
|---|---|---|
| 跨表复核被误用为正式经营报告 | 报告等级 D、formal_report_allowed=false、business_decision_basis_allowed=false | controlled |
| 差异队列被自动关闭或自动选源 | validator 检查 difference_auto_resolution_allowed=false、auto_source_selection_allowed=false、difference_closure_count=0 | controlled |
| S13-P3 越界进入 Stage 13 review 或 upload | validator 检查 Stage 13 review、S14、GitHub upload 均为 false | controlled |
| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |
