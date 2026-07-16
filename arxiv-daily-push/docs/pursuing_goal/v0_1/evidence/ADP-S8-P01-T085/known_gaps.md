# Known gaps · ADP-S8-P01-T085｜全链路迁移与数据一致性彩排

诚实披露**范围**、**验证形式**与 NOT_DEPLOYED 语义。

## 范围（诚实）
- **彩排 = 隔离重放已提交流水线工具**（黑盒 re-run，非重实现）。样本 = **500 行 D1 cn_items** 真实抽样（此前只在 scratchpad，本任务提交为可复现锚点），非全量生产库。全量生产迁移彩排随规模留待部署侧（T088 canary / T089 浸泡）。
- **链覆盖 8 阶段**：source registry(T014)→factsheet(T016)→content render(T018)→canonical(T024)→version(T026)→snapshot(T027)→restore(T029)→prediction(T071)。**未含**的下游（检索/事件/实体/watchlist/library）是**读取同一 canonical/version 底座的视图**，不引入新的行级迁移语义，故不重复彩排；本彩排锚定的是数据**迁移/一致性**主链（items→docs→versions→snapshot→restore）。
- **预测阶段解耦**：baselines 读 build_baselines.py 内嵌 G0/G1/G2 fixture，**不消费快照数据集**——彩排如实标注 `decoupled=True`，只验证其确定性可复现（G1/G2 有可复现基线），不声称预测消费了本次快照。这是 T071 既有设计（S6 预测底座用合成 fixture），非本任务缺陷。

## 提交的输入 fixture（诚实来源）
- `data-samples/items_500.json`（500 行）+ `fs_500.json`（500）：来自更早 session 的只读 D1 抽样（`scratchpad/t020/`），此前未提交。本任务提交它们使全链**可从已提交 fixture 重放**（此前只能靠已提交输出交叉核对）。已扫描：纯公开 feed 元数据（title/url/authors/categories/published_at），**0 email / 0 私密路径 / 0 凭证 / 0 PII**；等同已上线站点公开的信息。`fs_500` 由 `items_500` 经 extract_factsheet 确定性再导出、逐字节相等（彩排 stage-2 已证）。

## 验证形式（如实）
- **确定性重放**：8 阶段全在 tmp work_dir 跑，逐阶段比已提交锚点（registry_hash / canonical summary+id 集合 / snapshot_id+逐分区 logical_hash / restore counts）。snapshot_id 与 logical_hash **格式/引擎无关**（pyarrow 或 NDJSON 回退都复现）。
- **载重负控制**：①丢 1 行输入(500→499)→canonical 与 snapshot 阶段 matches_committed 双双 False（复现检查非空跑）；②伪 live build→production_untouched False；③poisoned row-ledger（未解释 −100 + 声称 preserved 却掉行）→ assess_row_ledger not-ok。
- **证据不可变**：5 个已提交锚点文件彩排前后 sha256 逐字节相等（彩排只读源真相，绝不覆盖）。
- **不含真机全量迁移/回滚**：本任务是 T085「一致性彩排」；**生产回滚+灾难恢复演练**是下一任务 **T086**；**14 日浸泡**是 **T089**；本任务不越界执行它们。
- **依赖 pyarrow==17.0.0/duckdb==1.1.3**（user-site，离线证据依赖，runtime/worker 不用；无则 snapshot 走 NDJSON 回退，logical_hash 仍复现）。
- **`assess_row_ledger` reason 仅查非空（复核者指出的次要边界）**：一条真丢失若配「非空但错误」的理由字符串会通过 ledger。**不影响本任务**——主保护是逐阶段 `matches_committed`（从已提交输入真实再导出比对锚点，载重且经独立复核复现），ledger 是次级 sanity；本任务每条 reason 都正确且与独立复现的计数绑定。未加 reason 语义校验（主观且无益）；如实披露此边界。

## NOT_DEPLOYED
- live 仍 `b189d3cc0703`（realtime_check.txt）；未改 worker/schema/source_registry；T077 视觉基线不重冻；未写生产 D1/R2。
