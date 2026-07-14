# KMFA v0.1.4 S14-P1 Risk Register

| Risk | Control | Status |
|---|---|---|
| 资金计划信号被误用为付款或银行操作依据 | D 级展示、payment/bank/loan actions 全部 false | controlled |
| S14-P1 越界进入开票纳税、政策证据、复审或 upload | validator 检查 S14-P2/P3、Stage 14 review 和 GitHub upload 均为 false | controlled |
| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |
