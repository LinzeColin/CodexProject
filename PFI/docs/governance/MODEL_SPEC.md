# MODEL_SPEC

model_count: 10
formula_count: 20
parameter_count: 92
task_count: 10
acceptance_count: 10

## v0.2.5 Stage 12 Phase 12.1 非模型 release-regression 覆盖层

本 Phase 只修复真实 CSV encoding probe、同步对应 release identity，并执行真实只读 import、隔离 SQLite、正式浏览器、报告真值与质量回归；不修改任何 model、formula、parameter 的定义、表达式、数值、版本或运行状态。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，注册表总数保持 `10/20/92`。

4 个 immutable Git objects、8,815 条 raw、8,808 条 ledger 与 803 条 review 是 E2E observation，不是校准参数或模型有效性证明。`SRC-HOLDINGS=not_loaded` 时 holding execution 必须为 `not_run`，5 份报告维持 `3 blocked / 2 partial` 且不输出假零；Phase 12.1=`candidate_pass` 不证明 holdings/financial model production validity、Stage 12 whole-stage、production acceptance 或 final human acceptance。

## v0.2.5 Stage 9 整阶段模型与报告验证覆盖层

本整阶段审查引用既有 `MOD-PFI-010`、`FORM-PFI-015..020` 与 `PARAM-PFI-081..092`，不修改任何 model、formula、parameter 定义、表达式、数值、版本或运行状态。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，注册表总数保持 `10/20/92`。

reviewed snapshot 只把已有的四个双消费组件、完整度、公式状态、参数影响与限制绑定到正式 Shell 和同源导出。当前 `FORM-PFI-015/019` 有真实 invariant/coverage 证据，`FORM-PFI-016..018` 继续 blocked，`FORM-PFI-020` 仅 structure-level；historical/out-of-sample 仍 `blocked_insufficient_ground_truth`。Stage 9 `accepted_for_transition` 只证明数据充分性、公式状态、模型限制、参数可见性和人工复核 workflow 达到本 gate，不证明预测准确率、生产模型有效性、production acceptance 或 final human acceptance。

## v0.2.5 Stage 9 Phase 9.3 非模型人工决策与导出覆盖层

本 Phase 只把 Phase 9.2 的 immutable analysis pack 转换为只读 decision objects、人工复核事件和 HTML/PDF/CSV/Markdown 同源导出；不新增或修改任何 model、formula、parameter 的定义、表达式、值、版本或运行状态。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，注册表总数保持 `10/20/92`。

决策对象中的 confidence dimensions、证据、反证、失效条件、风险与 portfolio effect 都是可复核展示字段，不是新模型或自动执行规则；`accepted` 仅表示人工复核结果，`automatic_trading_allowed=false` 且 `trade_execution_available=false`。四格式 hash 一致、浏览器 `16/16` 与 PDF 实体渲染只证明 Phase 9.3 工程候选，不证明完整模型有效、Stage 9 whole-stage、production 或 final acceptance。

## v0.2.5 Stage 9 Phase 9.2 模型验证展示覆盖层

本 Phase 引用既有 `MOD-PFI-010`、`FORM-PFI-015..020` 与 `PARAM-PFI-081..092`，不修改任何 model、formula 或 parameter 的定义、表达式、值、版本或运行状态。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，注册表总数保持 `10/20/92`。

正式报告页显示已有真实快照支持的 `FORM-PFI-015/019`、因来源/chain 缺失而 blocked 的 `FORM-PFI-016/017/018`、structure-only 的 `FORM-PFI-020`，以及 4 组参数敏感性。`MOD-PFI-010` 保留 limitations 和 counter-evidence；historical/out-of-sample 缺 ground truth 时必须 `blocked_insufficient_ground_truth`。浏览器 `11/11` 与 pack tamper tests 只证明 Phase 9.2 展示/验证合同，不证明完整模型有效、Stage 9 whole review、production 或 final acceptance。

## v0.2.5 Stage 8 Phase 8.3 非模型无障碍覆盖层

本 Phase 只改变正式 Shell 的 accessibility semantics、contrast/focus/target 样式、防误操作描述与浏览器/视觉验证；不修改任何 model、formula 或 parameter 的定义、表达式、值、版本或运行状态。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，治理注册表总数保持 `10/20/92`。

3px focus、44px target 和 12% visual-diff gate 都是 UI 验收合同，不是财务模型参数。20 路由/3776 文本样本零阻断、CDP AX 与键盘通过只证明 Phase 8.3 工程候选；不证明模型有效、Stage 8 whole-stage、production 或 final human acceptance。

## v0.2.5 Stage 8 Phase 8.2 非模型交互反馈覆盖层

本 Phase 只改变正式 Shell 的状态动效、反馈时间预算、触觉/声音能力路由、后台任务时间线和 official candidate frontend source 注入；不修改任何 model、formula 或 parameter 的定义、表达式、值、版本或运行状态。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，治理注册表总数保持 `10/20/92`。

100/300/1000/10000ms 是 UI 反馈阈值，不是财务模型参数；220ms 是界面动效上限，不进入参数注册表。`completedUnits/totalUnits` 仅反映调用方提供的真实工作量，elapsed time 不生成预测百分比。浏览器 16/16 只证明 Phase 8.2 交互候选，不证明模型有效、Phase 8.3、Stage 8 whole-stage、production 或 final human acceptance。

## v0.2.5 Stage 8 Phase 8.1 非模型设计覆盖层

本 Phase 只改变正式 Shell 的亮色 token、组件规则、10 种页面 archetype、图表状态可访问性和 desktop/mobile 布局；不修改任何 model、formula 或 parameter 的定义、表达式、值、版本与运行状态。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，治理注册表总数保持 `10/20/92`。

浏览器验证不加载财务数据，empty/error 图表隐藏 canvas 且不画假线；20/20 视口通过只证明 Phase 8.1 的视觉与响应式候选，不证明模型有效、Phase 8.2/8.3、Stage 8 whole-stage、production 或 final human acceptance。

## v0.2.5 Stage 7 Phase 7.3 非模型 lineage 展示覆盖层

本 Phase 只把既有 `MOD-PFI-008..010`、`FORM-PFI-001..020`、`PARAM-PFI-001..092` 与当前 source/economic-event/read-model lineage 作为正式只读二级页面展示，不修改定义、公式表达式、参数值、版本或 financial result。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，治理注册表总数保持 `10/20/92`；参数中心显示的 96 entries 包含配置域中的非治理展示项，不能误报为新增 governance parameter ID。

ready 指标必须同时显示 data range、formula/parameter/data/read-model hash、source IDs 与 economic-event lineage；not-ready 指标保持 `value=null` 并提供中文阻断原因。当前真实只读聚合 `8,815 = 6,879 complete + 1,936 review + 0 silent drop` 是 lineage observation，不是模型校准参数或新增财务值。Phase 7.3 candidate 不证明 Stage 7 whole-stage、production 或 final human acceptance。

## v0.2.5 Stage 7 Phase 7.2 非模型持久化覆盖层

本 Phase 不修改任何 model、formula 或 parameter 的定义、值、版本和状态，`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，总数保持 `10/20/92`。新增的是持仓 CRUD、SQLite change-set、设置偏好、revision 冲突和刷新/浏览器重开/服务重启合同。浏览器中的 contract sentinel 明确不是真实财务输入；缺少真实持仓、价格和 FX 时所有金额保持 `null`、`financial_values_emitted=0`。Phase 7.2 acceptance 不覆盖 Phase 7.3、Stage 7 whole-stage、production 或 final human acceptance。

## v0.2.5 Stage 7 Phase 7.1 非模型持久化覆盖层

本 Phase 不修改任何 model、formula 或 parameter 的定义、值、版本和状态，`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，总数保持 `10/20/92`。新增的是上传/解析/复核/账本的事务与恢复合同；1571/74 是真实只读源副本的观察计数，不是参数、阈值、预测或模型有效性证据。Phase 7.1 acceptance 不覆盖 Phase 7.2/7.3、Stage 7 whole-stage、production 或 final human acceptance。

## 当前模型

`MOD-PFI-010` / `FORM-PFI-015..020` 是 v0.2.5 Phase 5.2 财务模型能力合同。`FORM-PFI-015` 先以 `source_record_id` 和标准化后的 `(economic_event_id, event_type)` 去重，再分别投影 gross user activity、living consumption、investment funding、investment-domain allocation 四个分量；生活消费退款必须显式链接且不得超额，投资入金与投资申购可作为同一资金链的不同活动阶段，但均不被写成净资产损失。

`FORM-PFI-016` 对净资产、现金与余额滚动执行 exact Decimal 恒等式，discrepancy 必须精确等于 0；任何依赖非 ready、分量缺失或差异均 fail closed 并返回 null。`FORM-PFI-017..019` 分别登记投资收益/成本与 fee、tax、FX、idle-cash drag，按 365 日基准求解 XIRR，以及 `7/21/30/60/90/180/360` 七个现金流窗口；零分母、无法括根、不收敛或多次符号变化均禁止发布看似确定的结果。

`FORM-PFI-020` 复用 v0.2.2 的分类/标签合同：L1 最多 12、单 L1 下 L2 最多 5、L2 总数最多 50、每笔恰好一个 primary category；支持 default/custom tags、历史和 all/any 视图过滤。`PARAM-PFI-081..092` 固定 model version、四口径 labels/events、窗口、taxonomy/tag policy 与 XIRR day basis/tolerance/max iterations/multiple-root policy，并在 formula JSON、parameter YAML、Python、UI/report payload、渲染的模型参数文件五载体间做一致性校验。

Phase 5.2 只证明确定性公式、边界与 fail-closed capability；未读取真实财务行、未执行真实数据 invariant/metamorphic/sensitivity/model validation，也未修改真实 Web/UI 或报告源。上述实证与真实绑定只属于 Phase 5.3，不能由本 Phase 推断为模型有效、Stage 5 pass 或 production acceptance。

Phase 5.3 使用 immutable Git blob `4038bbe1e6ebb19c46f28e550e3951afcfd5a1ba` 只读重放 8,815 条真实记录；6,879 条进入 published、1,936 条进入 review、silent drop 为 0，输入恒等式 `8,815 = 6,879 + 1,936 + 0`。`FORM-PFI-015` 的双口径去重/分区与 `FORM-PFI-019` 的七窗口计数通过真实 invariant、permutation、exact-duplicate、positive-scaling、date-translation 和 boundary sensitivity 检查；源对象前后 identity 不变，公开证据只包含计数、状态与 hash，不包含财务金额或私有行。

本 Phase 没有修改模型、公式或参数值。`FORM-PFI-016..017` 因余额/负债/持仓/价格/FX 仍 `not_loaded` 而 blocked，`FORM-PFI-018` 因没有完整 dated cashflow chain 而 blocked，`FORM-PFI-020` 仅完成结构合同检查；classification accuracy、historical/OOS 与阈值敏感性因缺少 ground truth/scores 不得伪造。consumer payload 在 homepage、consumption_page、report 三个合同表面 hash 一致，但真实 UI 与报告 renderer source 不在本 Phase Allowed Files 内，`actual_ui_render_binding_completed=false`、`actual_report_render_binding_completed=false`，必须由独立 Stage 5 whole-stage review 处理，不能据此声明 Stage pass 或 production acceptance。

`MOD-PFI-001` 记录 PFI V0.2 根项目合同：账户、资产、账本、数据源、投资分析、消费分析、建议、报告、Alpha 只读 context export、Stage 6 synthetic E2E 和 rollback 边界。证据来自 `PFI/README.md`、`PFI/docs/pfi_v02/STAGE1_CORE_SKELETON.md`、`PFI/docs/pfi_v02/STAGE2_DATA_SYNC_MVP.md`、`PFI/docs/pfi_v02/STAGE2_ACCEPTANCE_AUDIT.md`、`PFI/docs/pfi_v02/STAGE3_READABLE_MVP.md`、`PFI/docs/pfi_v02/STAGE4_ANALYSIS_MVP.md`、`PFI/docs/pfi_v02/STAGE5_ADVICE_REPORT_ALPHA_EXPORT.md` 和 `PFI/docs/pfi_v02/STAGE6_E2E_STABILIZATION.md`。

`MOD-PFI-003` / `FORM-PFI-003` 是 v0.2.5 Phase 3.1 deterministic role-routing policy：`proposed_role` 只有显式存在于 `role_registry` 时才生成 publishable assignment；否则生成 `review_required` 且 `publish_allowed=false`。该规则禁止使用来源名称、label、provider 或文件名推断角色。

`PARAM-PFI-028..035` 分别登记 source type/capability extension policy、role registry count、多角色与重叠生效期、unknown-role policy、unknown-role publish permission 和 source-name classification permission。它们来自 `PFI/config/sources/v025_phase_3_1_source_account_policy.json`，不包含财务值。

Phase 3.1 的 Source Profile 还强制绑定 `parser_id`、`parser_version` 与 `sha256 source_hash`。本 Phase 不读取真实财务数据，不证明 parser 的标准化语义，也不实现 review queue 持久化、economic event、ledger、idempotency 或 reconciliation。

`MOD-PFI-004` / `FORM-PFI-004` 是 Phase 3.2 deterministic lineage/event policy：normalized identity 绑定 source provenance；group identity 绑定显式 exact link rule 或 singleton 及排序成员；economic event identity 绑定 group、registered event type 与 policy hash。任何金额/时间相似、来源名称或 provider label 都不能用于归组。

`FORM-PFI-005` 对 economic event、完整 raw/normalized/group lineage、policy/flags 与排序后的逐笔 postings 使用 UTF-8 sorted-key canonical JSON SHA-256，产生稳定 idempotency key；多币种 posting 不汇总为无 FX 依据的金额。

`PARAM-PFI-036..047` 登记 normalization version、最多 6 位 decimal、direction set、两条 grouping rule、source-name/amount-time heuristic 禁用、event time 策略、10 类 event registry、unknown-event fail-closed、单 metric 同 event 上限 1、SHA-256 与 canonical JSON serialization。Phase 3.2 的最小 typed contract values 只做 unit contract validation，不是财务 fixture fallback、真实重复导入、对账、持久化或 production acceptance。

`MOD-PFI-005` / `FORM-PFI-006` 是 Phase 3.3 real-data reconciliation/idempotency policy：只读解析 immutable Git object；只有 upstream accepted、非零金额且能用显式 source event type 与 signed direction 安全映射的记录才发布。未决 transfer/refund 分别因缺 link/account-role 或 offset 进入 review queue，不允许来源名称推断或金额/时间近似挂链。相同 Ledger idempotency key 只插入一次。

`FORM-PFI-007` 先按 `economic_event_id` 去重，再按 metric impact flags 投影；page identity 不进入 snapshot hash，因此 homepage、consumption、investment、cashflow、report 共享相同 `read_model_hash`。`PARAM-PFI-048..057` 登记 immutable snapshot、禁止 financial fixture、未决 transfer/refund policy、两项 inference 禁用、每 metric 最大计数 1、snapshot-not-page hash scope 以及日期粒度 normalization。Phase 3.3 证据输出只有聚合计数、hash 和脱敏 lineage，不输出财务值或私有标识。

`MOD-PFI-006` / `FORM-PFI-008` 是 Phase 4.1 account snapshot 与现金对账规则：只有 opening/closing、coverage、as_of、source id、record count 与 source hash 完整时，才以 Decimal 执行 `expected_closing_balance = opening_balance + confirmed_net_flows + adjustments`；`discrepancy = observed_closing_balance - expected_closing_balance` 必须精确等于 0。`PARAM-PFI-058..060` 固定 tolerance=0、non-ready value 禁用、confirmed-zero 必须完整证据。当前余额/负债源均 `not_loaded`，因此三个账户 metrics 只输出 null 状态，不读取财务行、不从交易推断余额；测试中的小数值只验证合同，不是 production acceptance。

`MOD-PFI-007` / `FORM-PFI-009..010` 是 Phase 4.2 持仓、显式成本与 PIT 估值规则：持仓 snapshot 必须保留 source/hash/quantity_as_of 与显式交易关联状态；成本基础精确等于 acquisition cost 加 capitalized fees，method 不得猜测；价格及所需 FX 不得晚于 valuation time，非 CNY 使用方向明确的 `BASE_TO_CNY`，CNY 使用恒等汇率 1。`PARAM-PFI-061..067` 固定允许的成本方法、unknown/future/fixture 禁止项、CNY identity 与 exact Decimal no-rounding。当前 holdings/prices/FX 均 `not_loaded`，所以三个投资 metrics 均为 null；unit contract values 不是 production valuation evidence。

`MOD-PFI-008` / `FORM-PFI-011..013` 是 Phase 4.3 strict Metric State 与统一 snapshot 规则：source-only sum 不使用交易推断缺失余额；net worth 只有账户资产、投资市值、负债全部 ready 或完整 confirmed_zero 时才计算；dependency/read-model identity 使用 compact sorted-key canonical JSON SHA-256，并排除 page identity 与 observation time。`PARAM-PFI-068..072` 登记 13 状态、zero policy、sha256、canonical serialization 与五个 surface IDs。当前七个核心 metrics 全部 `not_loaded/null`，无 production financial value；消费双口径及模型有效性仍属于 Stage 5。

`MOD-PFI-009` / `FORM-PFI-014` 是 Phase 5.1 公式生命周期、CNY/AUD 单位与可信度分维治理：现行 `FORM-PFI-001..014` 都有 immutable version 与可重建 hash；CNY identity 不造 FX，AUD 只接受 `AUD_TO_CNY` 和 `CNY/AUD` 乘法。`PARAM-PFI-073..080` 固定 registry version、CNY、方向/单位、示例非生产策略、lifecycle、分类阈值/权重、六维 IDs 与 overall-score prohibition。六维是独立质量事实，不可合成一个替代分数；Phase 5.2/5.3 模型与真实数据验证尚未执行。

## 非模型验收事实

Stage 6 whole-stage review 是非模型 Gate：只绑定既有 10-entry navigation、45 page contracts、7 aliases、History/Reload/Invalid/keyboard/AX/no-JS 行为与证据 schema；`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，总数保持 `10/20/92`。初审 `C0/I4/M1` 经证据/浏览器/验收绑定整改后复审 `C0/I0/M0`；接受仅授权 Stage 7 entry，不证明财务模型、production 或 final acceptance。

Stage 6 Phase 6.3 是非模型浏览器路由/无障碍验收：canonical pathname、History API state、invalid-route recovery、keyboard focus 与 AX tree 不新增或修改 math/stat/ML、ranking/scoring、业务公式、规则引擎或 LLM routing。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，总数保持 `10/20/92`。绿色 browser/AX evidence 只证明 Phase 6.3 candidate，不证明 Stage 6 whole review、财务模型、production 或 final acceptance。

Stage 6 Phase 6.2 是非模型页面/路由合同：45 个页面的 job-to-be-done、data object、primary action、UI state、focus/scroll 与 no-JS fallback 不新增或修改 math/stat/ML、ranking/scoring、业务公式、规则引擎或 LLM routing。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，总数保持 `10/20/92`。浏览器证据不证明财务模型、完整 history/a11y、Stage 6 或 production acceptance。

Stage 6 Phase 6.1 是非模型导航/alias 合同：固定 10 个一级入口、canonical route、7 个历史 redirect 与单一 responsive DOM；不新增或修改 math/stat/ML、ranking/scoring、业务公式、规则引擎或 LLM routing。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，总数保持 `10/20/92`。浏览器证据只证明导航合同与 release identity，不证明页面内容、财务模型、production 或 final human acceptance。

Stage 4 whole-stage review 是非模型 Gate：只绑定 `MOD-PFI-006..008` 的既有实现/evidence、fail-closed 状态与用户阶段授权；`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`。接受结果为 `pass_with_not_loaded_sources`，不把未加载生产依赖写成模型有效或真实财务值。

v0.2.4 Stage 0-9、用户确认、真实数据边界、post-overall consistency 与 final delivery gate 由 `FEAT-PFI-V024-OVERALL`、`FEAT-PFI-V024-FINAL-DELIVERY`、对应 evidence 和 Roadmap acceptance 管理；它们不是 math/stat/ML、ranking/scoring、公式、规则引擎或 LLM routing model，不单独登记 model ID。

## 边界

本文件不声明生产就绪，不声明实盘执行能力，不要求真实凭证。

## v0.2.5 Stage 0 Phase 0.2 非模型合同

- Iteration / Contract / Acceptance：`ITER-20260711-PFI-V025-S0-P02` / `PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS` / `ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT`。
- 本轮只冻结 active requirements、历史 disposition、产品/集成边界与 one-Phase run contract；`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`。
- 既有数量保持 `model/formula/parameter/task/acceptance = 1/1/23/10/10`；不新增或改写模型、公式、参数运行值、canonical delivery task 或 Acceptance。
- 旧 v0.2 定义和值继续作为历史/既有实现事实保存；与 v0.2.5 Active Requirements 冲突时仅作 reference，不得覆盖当前合同或证明当前完成。
- 当前结论仅为 Phase 0.2 contract candidate；evidence assembly 与 pre-commit validation 已完成，仍等待原子提交和 external post-commit attestation；不声明 Stage pass、release、安装或生产验收。

## v0.2.5 Stage 0 Phase 0.3 非模型合同

- Iteration / Contract / Acceptance：`ITER-20260711-PFI-V025-S0-P03` / `PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE` / `ACC-PFI-V025-S0-P03-GAP-EVIDENCE`。
- 本轮只归一化历史 findings、聚合 current gaps、形成 Stage 0 Evidence Pack 并准备验收请求；`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`。
- 既有数量保持 `model/formula/parameter/task/acceptance = 1/1/23/10/10`；不新增或改写模型、假设、公式、参数运行值、canonical delivery task 或 canonical Acceptance。
- Phase 0.2 已由 external attestation 解析；本 overlay 不改写其历史 tracked lifecycle。Phase 0.3 当前为 `candidate_pass_pending_postcommit_attestation / approved_pending_postcommit_attestation`；second-remediation corrected provisional 与 canonical exact-25 final-tree gates 已通过，仅待 atomic commit 与 external postcommit attestation；模型、假设、公式与参数运行值均未改变。
- Stage 0 whole-stage review 与 Stage 1 均为 `not_started`；本轮不声明 Phase acceptance、Stage pass、release、安装或生产验收。

### PFI-V025-S0-P03-COMP-FND030 非模型补偿

- 本补偿沿用 `ITER-20260711-PFI-V025-S0-P03` 与 `ACC-PFI-V025-S0-P03-GAP-EVIDENCE`，只修正 FND-030 的 source-path 分类和派生 gap/count/evidence；不新增 canonical task、Acceptance 或 version。
- `PFI/web/app/home.js` 不是 Roadmap 或 Active Requirements 指定源；正式首页源为 `PFI/web/app/pages/home.js`。因此 FND-030 为 `N/A/non-gap`，不构成 model、formula、parameter 或 rule-engine 变更。
- `model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；数量继续为 `1/1/23/10/10`，既有模型、假设、公式和参数运行值均不变。
- 上方原 Phase lifecycle 是补偿前历史快照；当前仅为 `classification_compensation_pending_postcommit_attestation`，不得据此声明 Phase、Stage、release 或 production acceptance。Stage 0 whole-stage review 与 Stage 1 均为 `not_started`。

## v0.2.5 Stage 1 Whole-Stage 非模型合同

> 历史 tracked candidate snapshot；当前状态已由 matching external attestation 与 Stage 2 Phase 2.1 event 取代。

- Iteration / Contract / Acceptance：`ITER-20260713-PFI-V025-S1-WHOLE-REVIEW` / `PFI-V025-STAGE1-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE1-WHOLE-REVIEW`。
- 本轮复核 release identity、cache、isolated candidate、浏览器/LaunchServices evidence 与治理绑定；按 `PFI-V025-S1-NO-FINDER-20260713` 不再执行 Finder 操作；`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`。
- 既有 `MOD-PFI-001`、`FORM-PFI-001` 与 23 个 parameters 的值、version、status 与 date 均不改变；`PARAM-PFI-003` 只增加 whole-review provenance。
- 历史 tracked lifecycle 为 `candidate_pass_pending_postcommit_attestation`；matching external attestation SHA-256 `a03651248d67f727f001b52c0a08961416155506b374fa08123247ebfa8f0d2a` 已激活。当前 Stage 1=`accepted_for_transition`、Stage 2=`in_progress`，production 与 final human acceptance 仍为 false。

## v0.2.5 Stage 2 Phase 2.1 非模型合同

- Iteration / Contract / Acceptance：ITER-20260714-PFI-V025-S2-P21 / PFI-V025-STAGE2-PHASE21-DATA-ROOT-SOURCE-MANIFEST / ACC-PFI-V025-S2-P21-DATA-ROOT-SOURCE-MANIFEST；Acceptance ID 为项目治理分配，Roadmap/Task Pack 未提供 ACC-*。
- 本 Phase 只登记 canonical private root、source metadata 与 metric dependencies；model_ids_changed=[]、formula_ids_changed=[]、parameter_ids_changed=[]，既有 1/1/23 registries 不变。
- 8815 条交易只证明 consumption classification source input available；标准化、经济事件、幂等账本与对账合同未完成，因此分类及所有财务指标仍 blocked/null，不构成账户余额、负债、持仓、价格、现金、净资产或 CNY 估值证据。
- operational SQLite 只做脱敏完整性/schema 元数据探测，未执行财务计算、migration 或 runtime behavior change。Stage 2 仍 in_progress，production/final human acceptance=false。

## v0.2.5 Stage 2 Phase 2.2 FX 生效日规则模型

- `MOD-PFI-002` / `FORM-PFI-002` 以 Australia/Sydney local date/time、06:00 cutoff 与显式 source-closed dates 计算 `effective_business_date = previous_open_date(local_date - I(local_time < 06:00:00))`。
- `PARAM-PFI-024..027` 分别固定 timezone、cutoff、AUD_TO_CNY direction 与 ordinary-runtime network=false；版本均为 `pfi-v0.2.5-fx-effective-day-v1`。
- 输入缺少 timezone/source metadata、snapshot hash 不匹配、pair direction 错误或 snapshot 来自未来时 fail closed；生产 snapshot 未加载时 rate/hash/id 保持 null。
- 本模型只确定日期与状态，不抓取、不预测、不硬编码汇率。Stage 2 仍 in_progress，Phase 2.3 与 whole-stage acceptance 未执行。

## v0.2.5 Stage 2 Phase 2.3 非模型沙盒合同

- Iteration / Contract / Acceptance：`ITER-20260714-PFI-V025-S2-P23` / `PFI-V025-STAGE2-PHASE23-SAFE-SANDBOX` / `ACC-PFI-V025-S2-P23-SAFE-SANDBOX`。
- 本 Phase 只实现 immutable source snapshot、ephemeral SQLite copy、privacy/no-fake gate 与真实性能 evidence；`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，registry 数量保持 `2/2/27`。
- elapsed time 与 peak Python allocation 是三次观察样本，不是预测模型、评分、业务公式、阈值参数或 SLA；不得用于推断生产性能保证。
- source 缺失时 blocked 且不允许 financial fixture fallback；未加载的生产 FX/余额/负债/持仓/价格继续保持 not_loaded/null。Stage 2 whole-stage review 与用户接受尚未开始。

## v0.2.5 Stage 2 Whole-Stage 非模型验收

- Iteration / Contract / Acceptance：`ITER-20260714-PFI-V025-S2-WHOLE-REVIEW` / `PFI-V025-STAGE2-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE2-WHOLE-REVIEW`。
- 本 Gate 只审查 Phase evidence、source disposition、privacy/no-fake、governance 与 human acceptance binding；`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，数量保持 `2/2/27`。
- Stage 2 接受只表示数据源与时间真相边界已审计，不表示任何财务指标已计算、模型已实证验证、生产性能达标或 production release。
- 既有 `MOD-PFI-002`/`FORM-PFI-002` 继续只定义 FX effective business date；production rate 仍 null，普通运行不联网。

## v0.2.5 Stage 3 Whole-Stage 非模型验收

- Iteration / Contract / Acceptance：`ITER-20260714-PFI-V025-S3-WHOLE-REVIEW` / `PFI-V025-STAGE3-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE3-WHOLE-REVIEW`。
- 本 Gate 只审查 Phase evidence、真实快照 partition、lineage/idempotency/no-double-count、privacy、governance 与 human acceptance binding；`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，既有 `MOD-PFI-001..005`、`FORM-PFI-001..007`、`PARAM-PFI-001..057` 的定义和值不变。
- Stage 3 接受结果为 `pass_with_review_queue`：1,250 条未确认 transfer 与 249 条未确认 refund 禁止发布并保留复核，不构成 confirmed business links。
- 本验收不证明账户余额、负债、持仓、市值、净资产、review queue persistence、production readiness 或最终人工验收；Stage 4 entry 已授权但 Stage 4 未开始。

## v0.2.5 Stage 5 Whole-stage 验收覆盖层

本 Gate 不修改模型、公式或参数版本和值。它只把 `FORM-PFI-015` 的四项真实只读指标绑定正式三页面，并验证同源、脱敏与 fail-closed。`FORM-PFI-016/017/018/020` 的缺来源、dated chain、ground truth 或 OOS 验证残余继续 blocked；Stage 5 transition acceptance 不得被解释为这些模型已有效。
