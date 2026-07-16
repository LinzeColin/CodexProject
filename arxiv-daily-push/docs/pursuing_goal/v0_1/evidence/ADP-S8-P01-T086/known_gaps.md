# Known gaps · ADP-S8-P01-T086｜生产回滚与灾难恢复演练

诚实披露**范围**、**验证形式**与 NOT_DEPLOYED 语义。

## 范围（诚实）
- **隔离演练 ≠ 执行真实生产回滚**：本任务证「**可恢复性**」——每组件恢复到已知点在隔离沙箱（tmp/内存 SQLite）完成并一致；**不发起 `wrangler versions deploy`、不写生产 D1/R2**。真实 canary 回滚在部署侧属 **T088**；14 日浸泡里演练每个 stop-the-line trigger 属 **T089**。
- **worker 组件**：演练证「回滚**目标可识别 + 完整性可验**」——源自哈希复现声明 build_id（`452f7c5de919`），故任一已提交 worker 版本可由 build_id 识别并 `wrangler versions deploy` 回滚（live 回滚目标=`b189d3cc0703`/T040）。**实际 live 回滚未执行**（会碰生产）。这是诚实边界，非缺陷。
- **RTO 是本地隔离演练的实测秒**（perf_counter），代表**恢复计算**时间；**不含**生产部署/网络/D1 冷启动/DNS 传播的真实 RTO——真实生产 RTO 更大，留待部署侧（T088/T089）实测。故 RTO 作为 informational actual 上报，验证器**不**断言其精确值，只断言恢复完成且复现已知 hash。
- **RPO 定性**：PERMANENT 类（R2 原文/append-only 版本/canonical 身份）RPO=0（不可变/append-only，永不丢）；REGENERABLE 类（factsheet/render/快照/镜像）数据 RPO=0（可从永久源重建）。Cloudflare D1 平台级 Time Travel（30 日 PITR）未在本演练声称/使用——本演练的**开放格式**恢复点是 T027 月快照 + append-only 版本记录，不依赖厂商 PITR。

## 验证形式（如实）
- **确定性恢复断言**：6 组件的 recoverable/hash 断言无 clock/network/randomness；逐组件 recovered_hash 比已知点（worker build_id / registry d63cf6bd / D1 counts_consistent / R2 内容寻址 key / content·prediction 确定性 hash）。
- **★恢复比对 COMMITTED 已知点（非同 run 自比）★**：`recovery_known_points.json` 冻结各组件已知点（content_bundle render hash `b70fe73e`、r2 内容寻址 key、d1 per-month=已提交 T029、registry hash、worker build_id）；每组件 recoverable=re-derivation 是否复现该已提交锚点。漂移（代码或输入）即翻 False。
- **载重负控制（3 个，全 falsifiable）**：①翻转一个 source 的 enabled → registry recompile≠d63cf6bd → blocker；②content 输入漂移 → render hash≠已提交锚点 → blocker；③r2 不同内容 → key≠已提交锚点 → blocker；外加 worker/registry 源文件演练前后 sha256 字节不变（只读、无 live rollback）。
- **复核记录（诚实）**：初版 content_bundle/r2 的 recoverable 是**同 run 自比**（h1==h2 确定性重言式，永不为假）→ 4-lens 对抗复核判 HOLE_FOUND（漂移不判 blocker，违验收②）。已修为比对**已提交锚点**（recovery_known_points.json），NC2/NC3 证实现在 falsifiable。**教训:「可恢复性」检查必须比对独立冻结的 committed 已知点,不能自比同 run 的确定性输出——后者恒真、永不触发 blocker。**
- **依赖 pyarrow==17.0.0/duckdb==1.1.3**（user-site，离线；D1 恢复走 T027 logical NDJSON，不强依赖）。

## NOT_DEPLOYED
- live 仍 `b189d3cc0703`（realtime_check.txt）；未改 worker/schema/source_registry；未发起真实回滚；未写生产 D1/R2。
