# CHANGELOG

## v0.2.4 Repair Pack Stage 1 Phase 1.3 - 2026-06-30

- 完成 `Stage 1 / Phase 1.3 - 验证`：记录 `node --check`、pytest 合同测试和 changed files audit。
- 新增 `tests/test_v024_stage1_phase13_validation_closeout.py` 和 `reports/pfi_v024/stage_1/phase_1_3/evidence.json`。
- Stage 1 当前为 candidate complete；whole-stage review、复审问题修复和 GitHub main upload 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher、`shell.js` 或真实指标计算。

## v0.2.4 Repair Pack Stage 1 Phase 1.2 - 2026-06-30

- 完成 `Stage 1 / Phase 1.2 - 最小恢复`：在 `shell.js` 中新增 `window.PFI_STAGE1_SHELL`，暴露 version、initialize、mountRoute 和 errorBoundary。
- 新增 `PFI/web/app/version.js`，提供 `window.PFI_STAGE1_VERSION` 和 `window.PFI_READ_STAGE1_VERSION` 版本读取接口。
- 新增 `tests/test_v024_stage1_phase12_shell_repair.py` 和 `reports/pfi_v024/stage_1/phase_1_2/evidence.json`。
- 本轮只做 shell integrity 最小恢复；Phase 1.3 和 Stage 1 whole-stage review 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher 或真实指标计算。

## v0.2.4 Repair Pack Stage 1 Phase 1.1 - 2026-06-30

- 完成 `Stage 1 / Phase 1.1 - 现状定位`：保存当前 `PFI/web/app/shell.js` 快照，记录语法检查结果，并定位当前残缺片段范围。
- 新增 `src/pfi_v02/stage_v024_stage1_shell_integrity.py`、`tests/test_v024_stage1_phase11_shell_diagnosis.py` 和 `reports/pfi_v024/stage_1/phase_1_1/evidence.json`。
- 当前 `shell.js` 在 Codex bundled Node 下语法检查通过；未发现 merge marker 或 syntax-fragment range。
- Phase 1.1 不修改 `shell.js`；Phase 1.2 仍需最小 shell integrity repair，Phase 1.3 和 Stage 1 whole-stage review 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Whole-Stage Review - 2026-06-30

- 完成 `Stage 0 whole-stage review - 复审并解决暴露问题`，复审 Phase 0.1、0.2、0.3 的合同、证据、测试和状态文件。
- 修复复审发现的两个 Stage 0 范围问题：缺少整体复审合同/evidence，以及顶层 run/status 文件仍停留在 Phase 0.3。
- 新增 `docs/pfi_v024/STAGE0_WHOLE_STAGE_REVIEW.md`、`tests/test_v024_stage0_whole_review_contract.py` 和 `reports/pfi_v024/stage_0/whole_stage_review/evidence.json`。
- Stage 0 已整体复审完成；Stage 1 尚未开始，仍需用户验收或明确指令。
- 本轮未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Phase 0.3 - 2026-06-30

- 完成 `Stage 0 / Phase 0.3 - Stage 0 测试与证据`，用合同测试覆盖 10 个正式一级入口、`市场与研究` 一级入口、禁止假财务数据和 evidence pack 完整性。
- 新增 `tests/test_v024_stage0_phase03_contract.py` 和 `reports/pfi_v024/stage_0/phase_0_3/evidence.json`。
- 扩展 `src/pfi_v02/stage_v024_repair_contract.py`，记录 Phase 0.3 机器合同和 Stage 0 candidate complete 状态。
- 本轮未执行 Stage 0 whole-stage review、Stage 1 或后续阶段，未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Phase 0.2 - 2026-06-30

- 完成 `Stage 0 / Phase 0.2 - 历史约束废弃`，明确历史 9 入口约束、市场与研究一级入口禁令、暗色 AI 控制台方向和样例财务数据验收均已作废。
- 新增 `docs/pfi_v024/HISTORY_DEPRECATION_POLICY.md`、`tests/test_v024_stage0_phase02_contract.py` 和 `reports/pfi_v024/stage_0/phase_0_2/evidence.json`。
- 扩展 `src/pfi_v02/stage_v024_repair_contract.py`，记录废弃约束和仍保留的历史参考原则。
- 本轮未执行 Phase 0.3 或 Stage 0 whole-stage review，未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Phase 0.1 - 2026-06-30

- 完成 `Stage 0 / Phase 0.1 - 需求合同冻结`，记录 v0.2.4 修补包定位、10 个正式一级入口、真实数据禁令和每轮最多一个 phase 的执行规则。
- 新增 `docs/pfi_v024/REPAIR_SCOPE_LOCK.md`、`src/pfi_v02/stage_v024_repair_contract.py`、`tests/test_v024_stage0_phase01_contract.py` 和 `reports/pfi_v024/stage_0/phase_0_1/evidence.json`。
- 本轮未执行 Phase 0.2、Phase 0.3 或 Stage 0 whole-stage review，未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Pre Stage 0 - 2026-06-30

- 建立 `v0.2.4` 修补包 pre stage 0；用户提供的 `v0.2.3-repair` roadmap/taskpack 作为来源输入，但当前 repo artifact 使用 `pfi_v024` 命名空间。
- 重新核验当前 GitHub main：`PFI/docs/pfi_v023` 和 v0.2.3 tests 已存在，`PFI/web/app/shell.js` 通过 `node --check`，TaskPack 内旧 GitHub audit 对当前 checkout 已过时。
- 新增 `docs/pfi_v024/PRE_STAGE0_CONTEXT_LOCK.md`、`SOURCE_TASK_PACK_MANIFEST.md`、`RUN_CONTRACT.md`、`src/pfi_v02/stage_v024_pre_stage0_contract.py` 和 `tests/test_v024_pre_stage0_contract.py`。
- 本轮未执行 Stage 0，未修改业务 UI、app bundle、launcher 或数据逻辑；停止等待用户验收或明确指令进入 Stage 0。

## v0.2.1.1 Product UI Recovery Stage 5/6 - 2026-06-29

- 完成 `v0.2.1.1 Stage 5` 真实图表与最终验收合同：账户、投资、消费趋势统一读取 `/api/trends`，来源限定为 SQLite operational DB 和 `MetaDatabase/PFI/alipay_daily`。
- 删除正式 Web Shell 的硬编码数字趋势回退；运行 API 不可用时只显示中文空状态。
- 隔离旧项目验收功能面板中的合成验收和测试数据路径，正式页面不再暴露 `fixture` 或合成验收入口。
- 新增 `docs/pfi_v0211/STAGE5_REAL_CHARTS_FINAL_ACCEPTANCE.md`、`docs/pfi_v0211/STAGE6_PROJECT_REVIEW_CLOSEOUT.md` 和 `tests/test_v0211_stage5_6_final_acceptance_contract.py`。
- Stage 6 项目级复审验收作为用户口径的第二阶段 closeout，覆盖跨板块复审、GitHub main 同步、本机 app 入口刷新和非必要缓存清理。

## v0.2.1.1 Product UI Recovery Stage 4 - 2026-06-29

- 完成 `S4 持久化与同步`，把 `投资管理 > 持仓` 保存路径接到本机 SQLite operational DB。
- 新增 `docs/pfi_v0211/STAGE4_PERSISTENCE_SYNC.md`、`tests/test_v0211_stage4_persistence_sync_contract.py`，并扩展 `src/pfi_v02/stage_v0211_ui_recovery.py` 的 Stage 4 合同。
- `src/pfi_v02/stage_v021_runtime_api.py` 新增 `/api/read-model` 和 `/api/reports/holdings`，让首页、投资管理和报告与洞察读取同一持仓读模型。
- 持仓编辑字段补齐账户、更新时间和备注；备注写入 SQLite snapshot 的 `metadata.note`。
- `web/app/shell.js` 保存持仓后刷新后端读模型，并同步更新首页、投资和报告卡片；生产保存不调用浏览器缓存。
- 正式库无真实持仓时继续显示中文空状态，不生成模拟收益或模拟持仓。

## v0.2.1.1 Product UI Recovery Stage 3 - 2026-06-29

- 完成 `S3 真实操作流`，把 Stage 2 页面骨架推进为可点击、可反馈、可复核的上传、账本、持仓和设置操作路径。
- 新增 `docs/pfi_v0211/STAGE3_REAL_OPERATION_FLOWS.md`、`tests/test_v0211_stage3_real_operation_flow_contract.py`，并扩展 `src/pfi_v02/stage_v0211_ui_recovery.py` 的 Stage 3 合同。
- `数据源与上传` 增加解析预览、字段映射、确认入库状态和待复核队列反馈；未选择真实文件时只提示中文空状态，不制造记录数。
- `账本流水` 增加筛选、分类选择、保存复核和导出流水；无真实流水时只导出空表头，不生成虚构流水。
- `投资管理 > 持仓` 保留未提交草稿标识，生产保存路径继续调用本机 `/api/holdings`，不把浏览器缓存作为生产保存来源。
- `设置` 增加保存设置、恢复默认和状态反馈；反馈控制台仍只在设置页显示。
- 本轮不声明 Stage 4 持久化与同步完成，不声明 Stage 5 真实图表与最终验收完成，不新增测试数据、样例流水、模拟持仓或虚构财务事实。

## v0.2.1.1 Product UI Recovery Stage 2 - 2026-06-29

- 完成 `S2 页面骨架与去 AI 化`，为 10 个正式一级入口建立中文页面骨架和二级入口。
- 新增 `docs/pfi_v0211/STAGE2_PAGE_SKELETON_CLEANUP.md`、`tests/test_v0211_stage2_page_skeleton_contract.py`，并扩展 `src/pfi_v02/stage_v0211_ui_recovery.py` 的 Stage 2 合同。
- Web Shell 默认首页改为用户任务语言：净资产、现金余额、投资市值、本月支出、待复核交易、数据源状态。
- 清理正式 UI 中运行边界、Task Pack、Demo、Prototype、手机预览、运行反馈控制台、多模态交互反馈、证据抽屉、运行证据、任务中心等污染词。
- `数据源与上传` 二级入口固定包含 `上传中心` 和 `导入中心`；`设置` 独立承接反馈、主题、语言、备份恢复等设置项。
- 本轮不做数据库 migration、上传入库闭环、持仓 SQLite 闭环、真实图表数据接入，也不声明 v0.2.1.1 整体完成。

## v0.2.1.1 Product UI Recovery Stage 0 - 2026-06-29

- 建立 v0.2.1.1 前端 UIUX 逻辑优化准备轮，明确当前 v0.2.1 前端优化不再作为正式 UI 完成状态，后续不得继续在旧 AI 化 Web Shell 上补丁式修补。
- 新增 `PRODUCT.md`、`docs/pfi_v0211/SOURCE_TASK_PACK_MANIFEST.md`、`docs/pfi_v0211/ROADMAP_LOCK.md`、`docs/pfi_v0211/STAGE0_PREPARATION.md`、`src/pfi_v02/stage_v0211_ui_recovery.py` 和 `tests/test_v0211_stage0_preparation_contract.py`。
- 将用户纠偏后的执行层级锁定为 6 个 Stage：S0 准备轮、S1 产品壳与路由、S2 页面骨架与去 AI 化、S3 真实操作流、S4 持久化与同步、S5 真实图表与最终验收；每次 run work 最多完成 1 个 Stage。
- 记录 Markdown roadmap 与 RTF 的来源差异：Stage 1 默认采用 RTF 最新稿的 10 个正式主导航入口，并把策略实验室唯一位置默认归到 `市场与研究 > 策略实验室`。
- 本轮不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`、`PFI/src/pfi_os/app/streamlit_app.py`，不刷新 app 入口，不清理缓存，不提前实现后续 Stage。

## v0.2.1 复审退回修复 - 2026-06-28

- 正式 Web Shell 删除运行边界/使用限制/隐私边界/只读/实盘/交易密码等用户可见边界类文案；约束保留在合同、测试和文档中。
- 新增 `src/pfi_v02/stage_v021_runtime_api.py`，提供本机 `GET/POST /api/holdings` 和 `GET /api/trends`。
- 持仓编辑保存路径改为 Web Shell -> 本机 API -> `V021HoldingsPersistenceService` -> SQLite operational database；浏览器缓存只保存明确标注的未提交草稿。
- 账户与资产、投资管理、消费管理趋势图改为从 SQLite 运行读模型派生；真实数据不足时显示中文空状态，不使用硬编码 demo 数组。
- 一级入口“策略实验室”和投资管理内部“策略实验室”统一进入 `/investment/strategy-lab`，复用同一功能面板、路由和状态。
- 新增 `tests/test_v021_review_rework_contract.py`，把复审失败项固化为回归测试，并扩展 Stage 2 合同禁词集合。

## v0.2.2 数据库治理 Stage 4 - 2026-06-28

- 完成 Stage 4 `Economic Event 与 Interconnection 逻辑`，覆盖 `S4-P1-T1..S4-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_interconnection.py`，建立 `economic_event_id`、`interconnection_group_id`、event type affects flags、Interconnection Matrix、Metric Dependency Graph 和 no-double-count 聚合函数。
- 新增 `docs/pfi_v022/STAGE4_INTERCONNECTION.md`、`docs/pfi_v02/INTERCONNECTION_MATRIX.md`、`tests/test_v022_interconnection_no_double_count.py` 和 `tests/test_v022_consumption_investment_outflow.py`，把 Stage 4 acceptance criteria、stop condition 和 validation 固化为可重复验证合同。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage4`，新增 `interconnection.event_type_policies`、`matrix_fields` 和 `metric_dependency_graph`。
- 双消费口径已锁定：投资入金、基金申购、黄金申购、投资买入进入消费总流出但不进入生活消费；退款抵消原消费；信用卡还款不重复计入生活消费。
- 本轮不实现 Stage 5 分类 taxonomy，不修改 v0.2.1 Web Shell UIUX 基线，不提交真实交易、支付、券商下单或自动投资能力。

## v0.2.2 数据库治理 Stage 3 - 2026-06-28

- 完成 Stage 3 `数据源、账户角色与可扩展结构`，覆盖 `S3-P1-T1..S3-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_source_profile.py`，建立 source profile schema、capabilities、`other_source_template`、账户多角色、角色生效期和 role-aware 计算合同。
- 新增 `docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md` 与 `tests/test_v022_stage3_source_account_profiles.py`，把 Stage 3 acceptance criteria、stop condition 和 validation 固化为可重复验证合同。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage3`，新增 `source_profile_schema`、`capability_labels_zh`、`other_source_template`、`account_role_schema` 和 `role_event_calculation_policy`。
- 本轮不实现 Stage 4 Interconnection Matrix，不修改 v0.2.1 Web Shell 交互架构，不提交真实交易、支付、券商下单或自动投资能力。

## v0.2.2 数据库治理 Stage 0 补做复核 - 2026-06-28

- 新增 `docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`，把 Stage 0 的 `S0-P1-T1..S0-P2-T2`、Milestone 0 acceptance criteria、stop condition、Agent 1/3 自检和验证命令整理为独立中文验收入口。
- 更新 `docs/pfi_v022/ROADMAP_LOCK.md`、`docs/pfi_v022/README.md`、`STAGE0_BASELINE_REPORT.md`、三基文件和 `HANDOFF.md`，明确 Stage 0 已补做复核且后续仍从 Stage 3 开始。
- 本轮不回滚 Stage 1/2，不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`、`PFI/web/styles/tokens.css`，不新增逻辑审查 HTML，也不做真实交易、自动投资或默认联网抓汇率。

## v0.2.2 数据库治理 Stage 2 - 2026-06-28

- 完成 Stage 2 `CNY 基准与汇率规则`，覆盖 `S2-P1-T1..S2-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_fx.py`，实现 06:00 Australia/Sydney 有效汇率日、普通运行本地快照读取、显式联网刷新、快照 hash 校验、金额转 CNY 和账本金额字段生成。
- 新增真实快照 `data/fx_snapshots/AUD_CNY/2026-06-28.json`：`fx_AUD_CNY_20260628`，`1 AUD = 4.6874 CNY`，来源 `Frankfurter v2 public API`。
- Web Shell 顶部汇率徽标从旧 CNY/AUD 口径更新为当前 `AUD/CNY=4.69（YYYY/MM/DD HH:MM）`，主页等主金额显示以 `CNY` 为主。
- `config/pfi_parameters.yaml`、`模型参数文件.md`、`功能清单.md`、`开发记录.md` 和 `config/parameter_changelog.md` 补齐 Stage 2 汇率、快照、原币辅助、缺失状态和非目标边界。
- 新增 `docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md` 与 `tests/test_v022_fx_effective_date.py`，把 Stage 2 acceptance criteria、stop condition 和 validation 固化为可重复验证合同。
- 本轮不实现 Stage 3 数据源结构，不新增参数中心页面，不提交真实交易、支付、券商下单或自动投资能力。

## v0.2.2 数据库治理 Stage 1 - 2026-06-28

- 完成 Stage 1 `模型参数文件重构`，覆盖 `S1-P1-T1..S1-P2-T3`。
- `模型参数文件.md` 新增中文参数总目录，覆盖货币、汇率、时间、数据源、账户角色、事件类型、Interconnection、消费分类、标签、置信度、消费模型、投资模型、现金流、可视化和测试。
- 新增 `config/pfi_parameters.yaml` 作为唯一机器可读参数源；参数草案中的 `config/pfi_v022_parameters.yaml` 已记录为 draft alias，不新增第二个漂移文件。
- 新增 `tests/test_pfi_parameters_consistency.py`，验证 Markdown、YAML、前端合同和 HTML 中的核心参数一致。
- 新增 `docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md`，记录 Stage 1 验收、非目标、参数命名决策和后续 Stage 2 边界。
- 本轮不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`，不实现真实汇率快照读取，不新增真实交易、自动投资、支付或券商提交能力。

## v0.2.1 前端优化 - 2026-06-27

- 建立 v0.2.1 前端优化 Stage 0 准备合同，锁定本轮是 PFI Web Shell 前端、交互、图表、上传命名、设置页和持仓编辑持久化优化，不是 V0.2 重构。
- 新增 `docs/pfi_v02/STAGE_V021_FRONTEND_OPTIMIZATION.md`，记录 roadmap、stage/task、acceptance criteria、stop condition、validation 和后续 pursuing goal 顺序。
- 新增 `src/pfi_v02/stage_v021_frontend_contract.py` 与 `tests/test_v021_stage0_frontend_contract.py`，把 CNY 基准、CNY/AUD 顶栏汇率、HTML 目标、多模态反馈设置页归属、统一导航和 P0-P8 任务清单固化为合同。
- 锁定后续 UI 货币契约：整体系统以 CNY 元为基准，所有页面顶部右上角显示当前 `AUD/CNY=4.69（YYYY/MM/DD HH:MM）` 徽标，读取当日 06:00 Australia/Sydney 汇率快照，缺失时显示中文空状态且不得伪造汇率。
- 本轮不重构 QBVS，不新增 Alpha/Ralpha/System/Development 产品一级入口，不提前实现后续 stage。

## 0.2.0 - 2026-06-27

- PFI 根项目确认为当前注册项目根。
- 三基人类入口统一为 Markdown 文件：`功能清单.md`、`开发记录.md`、`模型参数文件.md`。
- 补齐最小治理文件，记录 Stage 1/2 合同事实和生产未验证边界。
- 完成 PFI V0.2 Stage 2 本地合同验收，覆盖 phases 2A-2H。
- 新增 `docs/pfi_v02/STAGE2_ACCEPTANCE_AUDIT.md`，记录 phase/task evidence、stop-condition checks、validation results、本地 app-entry evidence 和缓存清理证据。
- 完成 PFI V0.2 Stage 3 本地可读 MVP，覆盖首页总览、账户地图、账本流水、待复核、同步全部、建议和报告入口。
- 新增 `src/pfi_v02/stage3_read_mvp.py` 与 `tests/test_stage3_readable_mvp.py`，将 Stage 3 3A-3D acceptance 固化为本地合同测试。
- Web shell 默认首页接入 Stage 3 read-model，左侧显示 V0.2 8 个一级入口；旧策略回测、盘感训练、大数据模拟器和 QBVS 兼容入口保留。
- 完成 PFI V0.2 Stage 4 投资与消费智能分析 MVP，覆盖投资总览、收益归因、风险分析、行为复盘、消费总览、分类分析、订阅检测、异常消费和现金流预测。
- 新增 `src/pfi_v02/stage4_analysis_mvp.py` 与 `tests/test_stage4_analysis_mvp.py`，将 Stage 4 4A/4B acceptance 固化为本地合同测试。
- Web shell 首页、投资管理和消费管理接入 Stage 4 analysis read-model；旧策略回测、盘感训练、大数据模拟器和 QBVS 独立系统引用继续保留。
- 完成 PFI V0.2 Stage 5 建议、报告、Alpha 只读出口 MVP，覆盖 recommendation model、review lifecycle、投资建议、消费建议、Top N ranking、四类报告、导出中心和 `pfi_context_snapshot_v1`。
- 新增 `src/pfi_v02/stage5_advice_report_alpha.py` 与 `tests/test_stage5_advice_report_alpha.py`，将 Stage 5 5A/5B/5C acceptance 固化为本地合同测试。
- Web shell 首页、建议与复盘、报告与洞察接入 Stage 5；仍保持 8 个一级入口，不新增 Alpha/Ralpha/System/Development 产品入口。
- 生产联通、真实账户凭证、支付提交、券商下单、Alpha repo 修改和实盘交易仍为独立后续 gate，未在 Stage 5 声明就绪。
- 完成 PFI V0.2 Stage 6 端到端验收与稳定化，覆盖 synthetic 多数据源、首页闭环、账本闭环、建议闭环、回归治理、交付回滚和 20 个总验收 gate。
- 新增 `src/pfi_v02/stage6_e2e_stabilization.py` 与 `tests/test_stage6_e2e_stabilization.py`，将 Stage 6 6A/6B/6C acceptance 固化为本地合同测试。
- Web shell 首页和报告与洞察接入 Stage 6；仍保持 8 个一级入口，不新增外部系统产品入口，QBVS 顶层独立且 PFI 不覆盖 QBVS。
- Stage 6 仍只证明本地 synthetic/read-only V0.2 可运行、可验证、可回滚；真实数据连接、外部 context consumer、PDF/ZIP、CDR/Open Banking 和生产发布证据为后续独立 gate。

## v0.2.1.1 Stage 1 - 2026-06-29

- 完成产品壳与路由受控重建：正式侧栏一级入口从旧 15 项收敛为 10 项。
- 新增正式一级入口 `市场与研究`，承接旧 `市场`、`研究` 与 `策略实验室`。
- `策略实验室` canonical route 改为 `/market-research/strategy-lab`；旧 `/strategy-lab` 和 `/investment/strategy-lab` 保留为兼容别名。
- Web Shell 路由从单纯 `replaceState` 升级为 `pushState` + `popstate`，支持浏览器前进后退。
- 新增 `docs/pfi_v0211/STAGE1_PRODUCT_SHELL_ROUTING.md` 与 `tests/test_v0211_stage1_product_shell_contract.py`。
- 本轮不实现图表、上传闭环、持仓编辑或报告。
