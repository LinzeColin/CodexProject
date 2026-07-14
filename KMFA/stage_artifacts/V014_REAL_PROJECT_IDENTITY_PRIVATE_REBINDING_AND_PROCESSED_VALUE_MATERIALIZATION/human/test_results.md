# 测试结果

- focused unit test: `PASS`，1 test / 1 passed。
- phase validator: `PASS`，4 个真实身份绑定、32 条指标、28 个已物化槽位、12 个现金未决槽位，decision=`NO_GO`。
- governance validators: `PASS`，project governance、lean governance、changed-only sync 均为 0 errors / 0 warnings；37 个声明变更文件与实际变更集一致。
- structured parse: `PASS`，JSON/JSONL/CSV/YAML 均可解析；3 个新增参数均为 34 列、`active` / `EXTRACTED`。
- raw immutability: `PASS`，5 个原始文件前后逐文件快照完全一致。
- raw/private/secret scan: `PASS`，raw 文件名泄漏 0、禁止业务后缀 0、高信号 secret 0、tracked/unignored private runtime 0。
- whitespace check: `PASS`，`git diff --check -- KMFA` 无输出。
