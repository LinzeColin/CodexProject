# 测试结果

- focused unit test: `PASS`（2 tests）
- phase/private validator: `PASS`（resolved=1, unresolved=3, materialized=31, decision=NO_GO）
- source phase private validator: `PASS`（bindings=4, materialized=28, unresolved_cash=12）
- project governance validator: `PASS`（errors=0, warnings=0）
- lean governance validator: `PASS`（errors=0, warnings=0）
- governance sync validator: `PASS`（37 个 public-safe changed files，errors=0, warnings=0）
- JSON / JSONL / CSV parse: `PASS`；active parameters=`1298`
- YAML parse: `PASS`（bundled Python 无 PyYAML，使用本机 Ruby/Psych 解析 6 个 YAML）；active formulas=`273`
- raw/private/secret scan: `PASS`（raw files=5, private tracked=0, private unignored=0, private leaks=0, high-signal secrets=0）
- Python compile: `PASS`
- `git diff --check`: `PASS`
