# KMFA v0.1.4 S14-P2 Risk Register

| Risk | Control | Status |
|---|---|---|
| 开票纳税候选被误用为纳税申报或发票开具依据 | D 级展示，tax/invoice operation gates 全部 false | controlled |
| S14-P2 越界进入政策证据、Stage 14 review 或 upload | validator 检查 S14-P3、Stage 14 review 和 GitHub upload 均为 false | controlled |
| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |
