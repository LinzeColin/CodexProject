# KMFA v0.1.4 S13-P1 Risk Register

| Risk | Control | Status |
|---|---|---|
| 经营初稿被误用为正式报告 | 报告等级 D、formal_report_allowed=false、business_decision_basis_allowed=false | controlled |
| S13-P1 越界进入回款/跨表/复审/upload | validator 检查 S13-P2/P3、Stage 13 review 和 GitHub upload 均为 false | controlled |
| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |
