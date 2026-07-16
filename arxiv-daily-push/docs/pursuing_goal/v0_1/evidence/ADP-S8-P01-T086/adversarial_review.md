# 独立对抗复核 · ADP-S8-P01-T086｜生产回滚与灾难恢复演练

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **实现者不自签 PASS**：两轮独立复核。
- **裁决**：**CONFIRMED_SOUND**（初版被 4-lens 对抗复核判 HOLE_FOUND，修复后经聚焦复核 CONFIRMED_SOUND）。

## 第一轮：4-lens 透视多样对抗复核（workflow，4 独立 skeptic）
四个 lens 各独立重算（scratch dir 只读仓库）：
- **recovery-real**：SOUND——独立复现 worker 自哈希 452f7c5de919、registry d63cf6bd、d1 restore counts_consistent(329 版本)、r2 内容寻址、content 确定性、prediction re-benchmark。
- **isolation/production-untouched**：SOUND——worker/registry 源 sha256 演练前后不变；全树只写 tmp/`:memory:`；无 wrangler deploy/无 D1/R2/网络写；自行只读 GET live=b189d3cc0703。
- **honesty/RTO-RPO/completeness**：SOUND——worker「无 live rollback」诚实、RTO 隔离计算时间、RPO 逐组件成立、6 组件全覆盖、known_gaps 披露 T088/T089 与 D1 Time Travel 不声称。
- **blocker-classification**：**HOLE_FOUND**——`drill_content`/`drill_r2` 的 recoverable 是**同 run 自比**（`h1==h2`/`k1==k2`，确定性重言式，永不为假）→ content_bundle/r2 **永不可能被判 release blocker**，即使真实代码/输入漂移；实证:扰动 item[0].summary 使 hash 变 129f0ab2 但 recoverable 仍 True。违验收②「任何不可恢复项成为 release blocker」。

## 修复（诚实）
根因：「可恢复性」检查比对了**同 run 的确定性输出**（恒真），而非独立冻结的 committed 已知点。
- 新增 `recovery_known_points.json`（committed）冻结各组件已知点：content_bundle render hash `b70fe73e088f782d`、r2 内容寻址 key、d1 per-month（=已提交 T029）、registry hash、worker build_id。
- `drill_content` → `ok = (h == KNOWN["content_bundle_render_sha16"])`；`drill_r2` → `ok = (k1 == KNOWN["r2_object_key"]) and (k1 != k_diff)`；`drill_d1` → 加 per-month == 已提交 T029 比对。每组件 recoverable 现比对 **committed 锚点**（DR.KNOWN 从 committed 文件加载，非 live 重算）。
- 验证器加 **NC2（content 输入漂移→hash≠锚点→blocker）** + **NC3（r2 不同内容→key≠锚点→blocker）**，连同 NC1（registry）共 3 载重负控制。

## 第二轮：聚焦复核（fixed 代码，独立 skeptic）
四点全 PASS：
1. **每组件比对 committed 锚点非同 run**：逐函数确认 content/r2/d1/worker/registry/prediction 均比 committed 值；无 `h1==h2`/`k1==k2` 作 recoverable 信号。
2. **锚点真实（独立再导出）**：r2 key `raw/arxiv-all/v1/43/0f/430ffbdc…995817`、content `b70fe73e088f782d`、d1 `{2016-01:(1,1),2020-07:(1,1),2026-07:(327,326)}` 均与从 committed 输入独立再导出/committed T029 逐一相等——非反向拟合。
3. **falsifiable**：扰动 content→recoverable False(hash a1ef3237≠锚)；drill_r2 不同内容→False(key 9d6f965a≠锚)；翻转 registry enabled→False(c5db032a≠d63cf6bd)。
4. **无新空跑/回归**：CLI 6/6 recoverable、0 blocker；验证器 exit 0（NC1/2/3 全翻 blocker）；DR.KNOWN 从 committed `recovery_known_points.json` 加载非 live 重算；隔离(`:memory:`/mkdtemp/无生产写/worker+registry 字节不变)；自行只读 GET live=b189d3cc0703(≠源 build 452f7c5de919→NOT_DEPLOYED 成立)。
- 次要 note（非 hole）：`rto_rpo_actuals.json` 的 `rto_seconds` 墙钟随 run 微变；确定性字段(evidence_hashes/all_recoverable/release_blockers)稳定，RTO 已注明 informational 不断言。

## 结论
4-lens 复核抓到真实空跑（同 run 自比→content/r2 永不判 blocker），已修为比对 committed 已知点并加 3 载重负控制，聚焦复核 **CONFIRMED_SOUND**。满足「实现者不自签 PASS」的独立复核门槛，可进入治理登记与合入。

**★教训:「可恢复性/恢复」检查必须比对独立冻结的 committed 已知点,绝不能自比同 run 的确定性输出——后者恒真、永不触发 blocker,是隐蔽的验收空跑。透视多样(perspective-diverse)多 skeptic 复核比单一 skeptic 更能抓到此类单向验收空跑。★**
