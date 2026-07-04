# KMFA v0.1.4 S13-P2 Risk Register

| Risk | Control | Status |
|---|---|---|
| 回款优先级被误用为催收或经营决策 | 报告等级 D、formal_report_allowed=false、business_decision_basis_allowed=false、legal_collection_decision_allowed=false | controlled |
| S13-P2 越界进入跨表复核、复审或 upload | validator 检查 S13-P3、Stage 13 review 和 GitHub upload 均为 false | controlled |
| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |
