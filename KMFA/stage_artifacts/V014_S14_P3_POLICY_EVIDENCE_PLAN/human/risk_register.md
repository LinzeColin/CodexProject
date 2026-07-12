# KMFA v0.1.4 S14-P3 Risk Register

| Risk | Control | Status |
|---|---|---|
| 证据目录被误用为政策资格结论 | D 级展示，policy conclusion/submission gates 全部 false | controlled |
| S14-P3 越界进入 Stage 14 review 或 upload | validator 检查 Stage 14 review 和 GitHub upload 均为 false | controlled |
| raw/private 数据泄漏 | 只复用 public-safe metadata，raw inbox read/list/stat/hash/mutation 全为 false | controlled |
