# 测试结果

- focused unit test: `PASS`，1 test。
- phase validator with private resolution: `PASS`，resolved=8、unresolved=40、decision=NO_GO。
- `validate_project_governance.py --project KMFA`: `PASS`，errors=0、warnings=0。
- `lean_governance.py validate --project KMFA`: `PASS`，errors=0、warnings=0。
- `validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`: `PASS`，errors=0、warnings=0。
- changed/untracked raw/private scan: `PASS`，37 个 KMFA 路径中禁止 raw/secret 文件后缀=0、tracked private runtime=0。
- high-signal secret scan: `PASS`，命中文件=0。
- raw filename leak scan: `PASS`，命中文件=0。
- raw immutability: `PASS`，5 个原始文件前后逐文件快照完全一致。
- `git diff --check -- KMFA`: `PASS`。

本 phase 只证明 8 个结构映射和 raw 不变性；40 个业务值槽位及 72 个差异仍未关闭，不声明处理数据与原始数据一致。
