# 04 - Data Model

## 1. Model layers

系统把以下层分开，前端通过统一 ID 和 evidence 连接：

1. identity：实体、别名、标识、法域、状态；
2. classification：行业、子行业、供应链阶段和角色；
3. structure：法律集团、业务分部、品牌、产品、设施；
4. relationships：所有权、供应链、资本、并购、治理、商业、技术、政策；
5. events：融资、并购、合同、扩产、政策、人员等离散变化；
6. provenance：来源、文档、证据、冲突、修订；
7. exploration：session、focus、history、filters、pins 和 comparison；
8. scoring：model、profile/version、run、result、explanation；
9. governance：operation log、calibration run 和 proposal。

## 2. Entity types

- `legal_entity`
- `brand`
- `business_segment`
- `product`
- `facility`
- `asset`
- `industry`
- `security`
- `fund`
- `person`
- `government_body`
- `contract`
- `standard`
- `theme`

品牌、产品、业务分部和法律实体必须分开。合同主体最终应解析到法律实体；无法解析时标记 `needs_resolution`。

## 3. Relationship families

1. `corporate_structure`
2. `ownership_control`
3. `supply_chain_operations`
4. `capital_financing`
5. `mergers_acquisitions`
6. `governance_people`
7. `commercial_dependency`
8. `technology_data_ip`
9. `government_policy`
10. `strategic_signal`

具体关系类型见 `data/relationship_taxonomy.csv`。

## 4. Relationship core

每条关系至少包含：

- subject/object 和人类可读角色；
- relationship type/family；
- reported/derived/disputed/superseded/revoked/unknown；
- valid/announced/filed/observed 时间；
- amount/percentage 及语义；
- qualifiers；
- confidence 和 coverage；
- 至少一条 evidence；
- derivation rule/version（如 derived）。

## 5. Supply-chain attributes

`stage_from/to`、tier、materiality、concentration、substitutability、lead time、capacity、geography、facility、contract status、coverage 和 last verified。

未知属性保持 null/unknown，不以默认 0 参与评分。供应链边方向默认为供应方 -> 采购/依赖方；UI 可切换“上游/下游”视角。

## 6. Time model

至少区分：

- `valid_from/to`
- `announced_at`
- `effective_at`
- `transaction_date`
- `filed_at`
- `report_period_start/end`
- `as_of_date`
- `observed_at`
- `retrieved_at/ingested_at`
- `reviewed_at`

As-of 重建使用 validity 和 supersession，不以当前值覆盖历史。

## 7. Exploration state

`exploration_session` 保存当前 focus、layers、as-of、profile 和 filters。`exploration_steps` 保存 start/reroot/back/forward/restore。

逻辑约束：

- sequence 唯一且单调；
- reroot 不复制底层实体/关系；
- 状态可序列化为 URL；
- 历史回退可重现同一查询；
- 画布布局可重新计算，不属于事实状态。

## 8. Scoring model

- `scoring_model`：公式、输入 schema、版本和状态；
- `scoring_profile`：用户/系统命名 profile；
- `scoring_profile_version`：权重、阈值、半衰期、缺失值策略、原因；
- `scoring_run`：数据快照、model/profile version、参数和 hash；
- `score_result`：raw、evidence quality、adjusted、coverage、contributions、missing inputs。

Profile 版本不可原地覆盖。Rollback 创建新版本并指向被回滚版本。

## 9. Logs and calibration

`operation_logs` 追加写入，记录 actor/action/object/old/new/diff/reason/version/result。无 API 可修改历史日志。

`calibration_runs` 固定 cadence 14 天，保存 snapshot、coverage、drift、quality、proposal 和 proposal status。Proposal 默认 proposed，不自动更改 active profile。

## 10. Database invariants

- published relationship/event evidence coverage = 100%；
- unknown 不得被转换为 zero/false；
- amount 有值时必须有 currency 和 amount_kind；
- percentage 0-100；
- 权重合计 1.0，单项 <=0.70；
- half-life 30-1825 天；
- calibration cadence = 14；
- score result 可追溯 model/profile/data snapshot；
- operation log 追加式；
- reroot 查询受预算约束。

逻辑 DDL 见 `specs/domain_schema.sql`。
