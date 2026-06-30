# PFI

PFI V0.2 is the Personal Financial Intelligence project under
`LinzeColin/CodexProject/PFI`.

`PFI/` is the active PFI product root. `QBVS/` is a separate top-level system
under `LinzeColin/CodexProject/QBVS`; PFI investment management does not own
or cover QBVS.

## v0.2.4 Repair Pack Pre Stage 0

PFI v0.2.4 is the repair package following the completed v0.2.3 closeout.
The user-provided source package is named `v0.2.3-repair`; this thread maps it
to target version `v0.2.4`.

Pre-stage record status:

- current unit: `Pre Stage 0 / Phase P0.0`
- Stage 0 executed: no
- max work per run: one phase
- business UI changes in this run: no
- data logic changes in this run: no
- current-main audit: v0.2.3 docs/tests exist and `PFI/web/app/shell.js` passes `node --check`
- next gate: user acceptance or explicit instruction to enter v0.2.4 Stage 0

Records:

- `docs/pfi_v024/PRE_STAGE0_CONTEXT_LOCK.md`
- `docs/pfi_v024/SOURCE_TASK_PACK_MANIFEST.md`
- `docs/pfi_v024/RUN_CONTRACT.md`
- `reports/pfi_v024/pre_stage_0/evidence.json`

## v0.2.4 Stage 1 Phase 1.1 Status

Current run unit: `Stage 1 / Phase 1.1 - 现状定位`.

- Phase 1.1: candidate pass.
- Phase 1.2: not started; minimum shell integrity repair remains required.
- Phase 1.3: not started.
- Stage 1 complete: no.
- `PFI/web/app/shell.js`: not modified in Phase 1.1.
- Business UI changes: none.
- Data logic changes: none.
- Diagnosis: current `shell.js` is syntactically complete via Codex bundled Node
  and has no merge markers or syntax-fragment range; it still lacks a stable
  Stage 1 shell integrity API exposing version, initialization, route mount,
  and error boundary together.

Phase 1.1 records:

- `src/pfi_v02/stage_v024_stage1_shell_integrity.py`
- `tests/test_v024_stage1_phase11_shell_diagnosis.py`
- `reports/pfi_v024/stage_1/phase_1_1/evidence.json`
- `reports/pfi_v024/stage_1/phase_1_1/shell.js.snapshot`
- `reports/pfi_v024/stage_1/phase_1_1/shell_before_after_summary.md`
- `reports/pfi_v024/stage_1/phase_1_1/terminal.log`

## v0.2.4 Stage 0 Status

Current run unit: `Stage 0 whole-stage review - 复审并解决暴露问题`.

- Phase 0.1: candidate pass.
- Phase 0.2: candidate pass.
- Phase 0.3: candidate pass.
- Stage 0 candidate: complete.
- Stage 0 whole-stage review: pass.
- Stage 0 complete: yes.
- Stage 1: started; Phase 1.1 candidate pass, Phase 1.2 and 1.3 not started.
- Business UI changes: none.
- Data logic changes: none.

Phase 0.1 records:

- `docs/pfi_v024/REPAIR_SCOPE_LOCK.md`
- `src/pfi_v02/stage_v024_repair_contract.py`
- `tests/test_v024_stage0_phase01_contract.py`
- `reports/pfi_v024/stage_0/phase_0_1/evidence.json`

Phase 0.2 records:

- `docs/pfi_v024/HISTORY_DEPRECATION_POLICY.md`
- `tests/test_v024_stage0_phase02_contract.py`
- `reports/pfi_v024/stage_0/phase_0_2/evidence.json`

Phase 0.3 records:

- `tests/test_v024_stage0_phase03_contract.py`
- `reports/pfi_v024/stage_0/phase_0_3/evidence.json`

Whole-stage review records:

- `docs/pfi_v024/STAGE0_WHOLE_STAGE_REVIEW.md`
- `tests/test_v024_stage0_whole_review_contract.py`
- `reports/pfi_v024/stage_0/whole_stage_review/evidence.json`

## v0.2.3 Closeout Status

PFI v0.2.3 当前处于 v0.2.3 user-accepted closeout complete。
Stage 0-10 已按阶段完成并上传到 GitHub main；Stage 11 Phase 11.1
回归测试、Phase 11.2 文档冻结、Phase 11.3 最终候选交付、Stage 11
whole-stage review 和 Stage 11 user acceptance 已完成。

- user_acceptance_claimed=true
- user_acceptance_source=当前 Codex thread 用户明确回复“接受”
- Stage 11 Phase 11.3 已完成
- Stage 11 whole-stage review 已完成
- Stage 11 user acceptance 已完成
- Stage 11 GitHub main upload 由本轮 terminal gate 验证
- v0.2.3 closeout complete

v0.2.3 后续开发必须遵守 `docs/pfi_v023/STAGE11_DOC_FREEZE.md` 和
`docs/pfi_v023/STAGE11_CLOSEOUT.md`：
固定 10 个一级入口，`市场与研究` 是正式一级入口，历史 9 入口约束作废，
禁止虚构财务数据，每次 run work 最多只解决一个 phase，后续新阶段必须重新建立
scope、run contract、evidence 和验收 gate。

## v0.2.3 Three-Phase Recovery Review Status

当前本地 `codex/pfi` 分支已完成 v0.2.3 三阶段恢复复审的本地整体项目复审。
第一阶段 Stage 1-11 stage-by-stage review 已完成；第二阶段 Stage 1-3、Stage 4-6、
Stage 7-9、Stage 10-11 四组 group review 已完成；第三阶段整体项目复审和本地
非必要缓存清理已完成。GitHub main 同步和最终 bundle 备份由最终 commit 后 terminal gate
验证，避免在 commit 内自证远端状态。

记录文件：

- `docs/pfi_v023/STAGE1_3_GROUP_REVIEW.md`
- `docs/pfi_v023/STAGE4_6_GROUP_REVIEW.md`
- `docs/pfi_v023/STAGE7_9_GROUP_REVIEW.md`
- `docs/pfi_v023/STAGE10_11_GROUP_REVIEW.md`
- `docs/pfi_v023/OVERALL_PROJECT_REVIEW.md`

## v0.2.1.1 Product UI Recovery Stage 0

`v0.2.1.1 Product UI Recovery` 是当前前端 UIUX 逻辑优化准备轮。用户已明确：当前 v0.2.1 前端优化不再作为正式 UI 完成状态，后续不能继续在 AI 化 Web Shell 上补丁式堆卡片、堆关键词或用字符串测试冒充验收。

本轮只完成 Stage 0 准备：读取 `/Users/linzezhang/Downloads/v0.2.1.1.rtf` 和 `/Users/linzezhang/Downloads/pfi_v0.2.1_controlled_ui_rebuild_task_pack_roadmap.md`，把错误的 Phase/Stage 母子关系纠正为 6 个执行 Stage，并锁定每次 pursuing goal 最多完成 1 个 Stage。本轮不修改 `PFI/web/index.html`、`PFI/web/app/shell.js` 或 `PFI/src/pfi_os/app/streamlit_app.py`。

Stage 0 交付入口：

| 文件 | 用途 |
| --- | --- |
| `PRODUCT.md` | PFI 产品上下文，供后续 UIUX 重建保持一致。 |
| `docs/pfi_v0211/SOURCE_TASK_PACK_MANIFEST.md` | v0.2.1.1 来源资料、冲突和默认处理。 |
| `docs/pfi_v0211/ROADMAP_LOCK.md` | 6-stage 执行路线、每轮边界和停止条件。 |
| `docs/pfi_v0211/STAGE0_PREPARATION.md` | Stage 0 准备轮记录和验证命令。 |
| `src/pfi_v02/stage_v0211_ui_recovery.py` | 机器可读 Stage 0 合同。 |
| `tests/test_v0211_stage0_preparation_contract.py` | Stage 0 合同测试。 |

## v0.2.1.1 Stage 2 - 页面骨架与去 AI 化

本轮只完成 Stage 2，不实现数据库迁移、上传入库闭环、持仓 SQLite 持久化、真实图表数据接入或最终验收。

- 正式 10 个一级入口均具备中文页面骨架和二级入口。
- `数据源与上传` 二级入口固定包含 `上传中心`、`导入中心`。
- 默认首页改为用户任务语言：净资产、现金余额、投资市值、本月支出、待复核交易、数据源状态。
- 正式 UI 清理运行边界、Task Pack、Demo、Prototype、手机预览、运行反馈控制台、多模态交互反馈、证据抽屉、运行证据、任务中心等污染词。
- 反馈、触感、声音、视觉、主题语言和备份恢复只在 `设置` 页出现。
- 交付记录：`docs/pfi_v0211/STAGE2_PAGE_SKELETON_CLEANUP.md`。
- 合同测试：`tests/test_v0211_stage2_page_skeleton_contract.py`。

## v0.2.1.1 Stage 3 - 真实操作流

本轮只完成 Stage 3，不声明 Stage 4 持久化与同步完成，也不声明 Stage 5 真实图表与最终验收完成。

- `数据源与上传` 增加上传中心、解析预览、字段映射、确认入库和待复核队列路径。
- `账本流水` 增加账本筛选、分类选择、保存复核和导出流水路径。
- `投资管理 > 持仓` 增加持仓编辑表单、未提交草稿标识、保存修改和恢复默认入口。
- `设置` 增加设置保存、恢复默认和保存状态；反馈控制台继续只在设置页显示。
- 持仓生产保存不得使用浏览器缓存；浏览器缓存只允许保存明确标注的未提交草稿。
- 无真实数据时显示中文空状态，不新增测试数据、样例流水、模拟持仓或虚构财务事实。
- 交付记录：`docs/pfi_v0211/STAGE3_REAL_OPERATION_FLOWS.md`。
- 合同测试：`tests/test_v0211_stage3_real_operation_flow_contract.py`。

## v0.2.1.1 Stage 4 - 持久化与同步

本轮只完成 Stage 4，不声明 Stage 5 真实图表与最终验收完成。

- `投资管理 > 持仓` 的生产保存路径为 Web Shell -> `/api/holdings` -> `V021HoldingsPersistenceService` -> SQLite operational DB。
- 持仓字段补齐为标的、名称、数量、成本、价格、币种、账户、更新时间和备注；备注写入 `metadata.note`。
- 新增 `/api/read-model`，用于首页、投资管理和报告与洞察读取同一持仓运行读模型。
- 新增 `/api/reports/holdings`，用于报告页读取同一 SQLite 持仓报告。
- 浏览器缓存只允许保存明确标注的未提交草稿；点击保存后必须写入 SQLite。
- 正式库无真实持仓时保持中文空状态，不生成模拟收益或模拟持仓。
- 交付记录：`docs/pfi_v0211/STAGE4_PERSISTENCE_SYNC.md`。
- 合同测试：`tests/test_v0211_stage4_persistence_sync_contract.py`。

## v0.2.1.1 Stage 5/6 - 真实图表、最终验收和项目级复审

`v0.2.1.1 Stage 5` 完成账户、投资、消费趋势图的真实数据源锁定：正式图表只读取 `/api/trends`，后端只从 SQLite operational DB 和 `MetaDatabase/PFI/alipay_daily` 派生；无真实数据时显示中文空状态，不显示硬编码曲线。

用户口径的 `Stage 6 项目级复审验收` 是 Stage 5 后的第二阶段 closeout，用于整体跨板块复审、修复发现的问题、同步 GitHub main、刷新本机 PFI.app 入口并清理非必要缓存。

交付入口：

| 文件 | 用途 |
| --- | --- |
| `docs/pfi_v0211/STAGE5_REAL_CHARTS_FINAL_ACCEPTANCE.md` | Stage 5 真实图表与最终验收记录。 |
| `docs/pfi_v0211/STAGE6_PROJECT_REVIEW_CLOSEOUT.md` | Stage 6 项目级复审验收记录。 |
| `tests/test_v0211_stage5_6_final_acceptance_contract.py` | Stage 5/6 合同、真实图表数据源和正式 UI 污染回归测试。 |

## v0.2.2 数据库治理整体复审

`v0.2.2 数据库治理` 当前完成 Stage 0-13 的整体项目复审解决。正式页面、报告、图表、首页摘要和建议只允许读取真实 MetaDatabase 派生数据或中文真实空态；不得使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据作为验收依据。不新增真实交易、自动投资、支付或券商提交能力。

整体复审证据为 `docs/pfi_v022/reviews/OVERALL_PROJECT_REVIEW_20260629.md`、`docs/pfi_v022/reviews/TEST_DATA_AUDIT_FINAL_20260629.md` 和 `reports/pfi_v022_overall_closeout_summary.md`。GitHub main 同步和 app 入口重装纳入本轮整体 closeout，均按 `PFI/` 与 `MetaDatabase/PFI/` path-limited 范围执行。阻塞项数量：`0`。

## v0.2.2 Stage 1-13 复审

当前 pursuing goal 为重新复审并解决 Stage 1-13。第一阶段每次 run work 只复审解决 1 个 Stage，第二阶段整体项目复审解决已完成；本轮 closeout 完成 GitHub main 同步和 app 入口重装。

当前复审进度：

- Stage 1 复审并解决：已完成，报告为 `docs/pfi_v022/reviews/STAGE1_REVIEW_20260628.md`，测试为 `tests/test_v022_review_stage1.py`；已补齐 3 个阈值/开关键说明。
- Stage 2 复审并解决：已完成，报告为 `docs/pfi_v022/reviews/STAGE2_REVIEW_20260628.md`，测试为 `tests/test_v022_review_stage2.py`；已补齐 CNY 主显示现金流影响面和账本金额字段中文标签映射。
- Stage 3 复审并解决：已完成，报告为 `docs/pfi_v022/reviews/STAGE3_REVIEW_20260628.md`，测试为 `tests/test_v022_review_stage3.py`；已补齐 taskpack 默认账户角色和 source profile 角色扩展示例。
- Stage 4 复审并解决：已完成，报告为 `docs/pfi_v022/reviews/STAGE4_REVIEW_20260628.md`，测试为 `tests/test_v022_review_stage4.py`；已修复同一关联组来源两侧 economic_event_id 不一致导致重复计量，并补齐现金流依赖图。
- Stage 5 复审并解决：已完成，报告为 `docs/pfi_v022/reviews/STAGE5_REVIEW_20260628.md`，测试为 `tests/test_v022_review_stage5.py`；已修复分类单主分类真实验证，并补齐后续压缩到 10 类以内的机器验收字段。
- Stage 6-13 复审并解决：已完成；Stage 13 报告为 `docs/pfi_v022/reviews/STAGE13_REVIEW_20260629.md`，测试为 `tests/test_v022_review_stage13.py`。
- 整体项目复审解决：已完成。
- GitHub main 同步：本轮 closeout 已按 `PFI/` 与 `MetaDatabase/PFI/` path-limited 范围执行。
- app 入口重装：已刷新 `/Applications/PFI.app`、`~/Downloads/PFI.app`、`~/Desktop/PFI.app`，macOS app acceptance lite `29 pass / 0 fail / 2 info`。

Stage 13 source files:

| Purpose | Path |
| --- | --- |
| 中文参数总目录 | `模型参数文件.md` |
| 机器可读参数源 | `config/pfi_parameters.yaml` |
| v0.2.2 参数交付镜像 | `config/pfi_v022_parameters.yaml` |
| 参数变更记录 | `config/parameter_changelog.md` |
| Stage 1 验收报告 | `docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md` |
| Stage 1 复审报告 | `docs/pfi_v022/reviews/STAGE1_REVIEW_20260628.md` |
| Stage 2 验收报告 | `docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md` |
| Stage 3 验收报告 | `docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md` |
| Stage 4 验收报告 | `docs/pfi_v022/STAGE4_INTERCONNECTION.md` |
| Stage 4 复审报告 | `docs/pfi_v022/reviews/STAGE4_REVIEW_20260628.md` |
| Stage 5 验收报告 | `docs/pfi_v022/STAGE5_LEDGER_TAXONOMY.md` |
| Stage 5 复审报告 | `docs/pfi_v022/reviews/STAGE5_REVIEW_20260628.md` |
| Stage 6 验收报告 | `docs/pfi_v022/STAGE6_TAGS_CUSTOM_VIEWS.md` |
| Stage 7 验收报告 | `docs/pfi_v022/STAGE7_FORMULA_SCORING.md` |
| Stage 8 验收报告 | `docs/pfi_v022/STAGE8_RUNTIME_DIFF_IMPACTED_METRICS.md` |
| Stage 12 交付报告 | `docs/pfi_v022/STAGE12_DELIVERY_REPORT.md` |
| Stage 12 2 轮 × 6 Agent 自检 | `docs/pfi_v022/SIX_AGENT_DELIVERY_REVIEW.md` |
| Stage 12 UI/UX 审查 HTML | `web/pfi_v022_logic_review.html` |
| Stage 12 最终摘要 | `reports/pfi_v022_summary.md` |
| Stage 13 后置复核报告 | `docs/pfi_v022/STAGE13_POST_REVIEW.md` |
| Stage 13 Codex Review Ticket | `review_queue/codex_review_stage13_owner_specified_20260628.md` |
| Stage 13 Downloads 清理记录 | `docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md` |
| Stage 13 复审报告 | `docs/pfi_v022/reviews/STAGE13_REVIEW_20260629.md` |
| Stage 13 复审摘要 | `reports/pfi_v022_stage13_review_summary.md` |
| 整体项目复审解决 | `docs/pfi_v022/reviews/OVERALL_PROJECT_REVIEW_20260629.md` |
| 最终测试数据审计 | `docs/pfi_v022/reviews/TEST_DATA_AUDIT_FINAL_20260629.md` |
| 整体 closeout 摘要 | `reports/pfi_v022_overall_closeout_summary.md` |
| Stage 9 验收报告 | `docs/pfi_v022/STAGE9_VISUALIZATION_UIUX.md` |
| Stage 9 Interconnection Map | `docs/pfi_v022/INTERCONNECTION_MAP.md` |
| Stage 10 验收报告 | `docs/pfi_v022/STAGE10_REPORT_ADVICE_REVIEW.md` |
| Stage 11 验收报告 | `docs/pfi_v022/STAGE11_TEST_VALIDATION.md` |
| Interconnection Matrix | `docs/pfi_v02/INTERCONNECTION_MATRIX.md` |
| Stage 0-13 roadmap lock | `docs/pfi_v022/ROADMAP_LOCK.md` |
| Stage 11 contract | `src/pfi_v02/stage_v022_database_governance.py` |
| Stage 5 ledger taxonomy | `src/pfi_v02/stage_v022_ledger_taxonomy.py` |
| Stage 6 tags/views | `src/pfi_v02/stage_v022_tags_views.py` |
| Stage 7 formula scoring | `src/pfi_v02/stage_v022_formula_scoring.py` |
| Stage 8 runtime diff | `src/pfi_v02/stage_v022_runtime_diff.py` |
| Stage 9 visualization UIUX | `src/pfi_v02/stage_v022_visualization_uiux.py` |
| Stage 10 report advice review | `src/pfi_v02/stage_v022_report_advice_review.py` |
| Stage 11 test validation | `src/pfi_v02/stage_v022_test_validation.py` |
| Stage 6 local HTML | `web/pfi_v022_tag_views.html` |
| Stage 9 local HTML | `web/interconnection-map.html` |
| 汇率快照读取模块 | `src/pfi_v02/stage_v022_fx.py` |
| 数据源与账户角色模块 | `src/pfi_v02/stage_v022_source_profile.py` |
| Interconnection 模块 | `src/pfi_v02/stage_v022_interconnection.py` |
| 真实汇率快照 | `data/fx_snapshots/AUD_CNY/2026-06-28.json` |
| Stage 2 FX test | `tests/test_v022_fx_effective_date.py` |
| Stage 3 source/account test | `tests/test_v022_stage3_source_account_profiles.py` |
| Stage 4 no-double-count test | `tests/test_v022_interconnection_no_double_count.py` |
| Stage 4 consumption/investment outflow test | `tests/test_v022_consumption_investment_outflow.py` |
| Stage 4 review fix test | `tests/test_v022_review_stage4.py` |
| Stage 5 ledger taxonomy test | `tests/test_v022_stage5_ledger_taxonomy.py` |
| Stage 5 review fix test | `tests/test_v022_review_stage5.py` |
| Stage 6 tags/views test | `tests/test_v022_stage6_tags_views.py` |
| Stage 7 formula/scoring test | `tests/test_v022_stage7_formula_scoring.py` |
| 参数一致性测试 | `tests/test_pfi_parameters_consistency.py` |

Stage 7 locked parameters:

- 主货币：`CNY`。
- 当前前端徽标：`AUD/CNY=4.69（YYYY/MM/DD HH:MM）`。
- 汇率读取时间：`06:00 Australia/Sydney`。
- 当前真实快照：`fx_AUD_CNY_20260628`，`1 AUD = 4.6874 CNY`，来源 `Frankfurter v2 public API`。
- 普通运行默认联网：`false`，只读 `data/fx_snapshots/` 本地快照。
- 显式刷新命令：`PYTHONPATH=src python3 -B -m pfi_v02.stage_v022_fx refresh --allow-network`。
- 汇率缺失状态：显示 `汇率数据待更新`，不得伪造实时汇率或强制联网。
- 低置信复核线：`70 分`。
- 大额消费阈值：`CNY 2000` 或 `AUD 500`。
- 夜间窗口：`22:00-06:00`。
- 现金流窗口：`7/21/30/60/90/180/360`。
- 支持 source type：`wallet`、`bank`、`broker`、`fund_platform`、`bullion_platform`、`payment_platform`、`manual_snapshot`、`other`。
- source capabilities：现金流水、投资交易、基金交易、黄金交易、余额快照、费用、退款、转账。
- 新增 source 模板：`other_source_template`。
- 账户角色字段：`role_effective_from`、`role_effective_to`。
- `economic_event_id`：同一真实经济事件只有一个 ID。
- `interconnection_group_id`：同一资金链路进入一个关联组；核心金额优先按 `interconnection_group_id + event_type` 去重，缺少关联组时按 `economic_event_id + event_type` 兜底。
- `消费总流出`：普通消费、投资入金、基金申购、黄金申购、投资买入、费用进入该口径，退款抵消。
- `生活消费`：普通生活消费进入该口径，退款抵消；投资入金、基金申购、投资买入不进入。
- Stage 4 stop condition：`投资入金未进入消费总流出`、`基金申购未进入消费总流出`、`投资入金错误进入生活消费`、同一 `interconnection_group_id` 重复进入核心金额。
- 现金流依赖图：投资入金、基金申购、黄金申购、投资买入、投资卖出、收入、费用、退款、信用卡还款、内部转账、汇率兑换。
- Agent 1 复核消费、投资、现金流口径；Agent 2 复核 source -> transaction -> group -> economic event -> ledger -> metric 链路。
- Stage 5 事件类型表：消费、投资入金、基金申购、黄金申购、投资买入、投资卖出、退款、费用、信用卡还款、内部转账、收入、估值、汇率兑换。
- Stage 5 双消费展示：首页、消费页、报告必须同时展示 `消费总流出` 与 `生活消费` 并解释差异。
- Stage 5 分类约束：`L1 ≤ 12`、每类 `L2 ≤ 5`、总 `L2 ≤ 50`、每笔交易主分类数量为 `1`；分类验证会拒绝非单主分类 taxonomy。
- Stage 5 默认 taxonomy：餐饮食品、居住家庭、交通出行、购物用品、医疗健康、教育成长、娱乐社交、订阅服务、金融费用、投资资金流出、家庭责任、调整其他。
- Stage 5 future merge：当前 12 个 L1 可压缩为 7 个 future merge 分组，低于 `10` 类目标；多维分析交给 Stage 6 标签系统。
- Stage 5 stop condition：事件类型不足、影响口径缺失、投资入金或基金申购未进入消费总流出、生活消费被投资资金流污染、分类超限、后续无法合并分类。
- Stage 6 标签表：`pfi_tags`、`pfi_tag_assignments`、`pfi_tag_rules`、`pfi_tag_history`、`pfi_custom_views`。
- Stage 6 默认标签组：通用、消费、投资、数据质量、现金流、复盘。
- Stage 6 自定义标签生命周期：新增、重命名、停用、删除；系统默认标签不可物理删除。
- Stage 6 标签规则维度：金额、时间、分类、事件类型、账户角色。
- Stage 6 自定义视图示例：订阅检查、投资追涨复盘、夜间大额复盘。
- Stage 6 stop condition：标签不能持久化、一笔记录只能有一个标签、标签只能手动添加、默认标签缺失关键维度、自定义标签无法修改、标签历史不可追踪、标签无法筛选账本、标签不参与报告、自定义视图不能保存。
- Stage 7 置信度权重：字段完整度 30、金额方向 10、规则命中 20、商户/对手方 15、关联匹配 15、历史一致性 10，总分 100。
- Stage 7 复核阈值：统一 `70`，不得按 source 名称设置分层阈值。
- Stage 7 消费公式：`消费总流出 = 生活消费 + 投资入金 + 基金申购 + 黄金申购 + 投资买入 + 金融费用 - 退款抵消`；`生活消费 = 普通生活消费 - 退款抵消`。
- Stage 7 大额消费：`CNY >= 2000` 或原币 `AUD >= 500`；夜间窗口 `22:00-06:00`；订阅评分阈值 `75`。
- Stage 7 投资市值：`quantity * latest_price * fx_rate_to_cny`；成本、已实现、未实现、总收益均记录费用、税费和汇率影响。
- Stage 7 投资行为：频繁交易、换手率、持仓周期、追涨、杀跌、现金拖累、集中度暴露。
- Stage 7 现金流窗口：`7/21/30/60/90/180/360`。
- Stage 7 储备金安全线：`max(user_min_reserve_cny, average_fixed_monthly_expense_cny * reserve_months)`，默认 `reserve_months=3`。
- Stage 7 投资入金挤压：当 planned investment deposit 使未来生活现金低于储备金安全线时标记 `投资挤压现金`。

## v0.2.1 前端优化 Stage 0

`v0.2.1 前端优化` 已进入 Stage 0 准备轮。本轮只锁定前端优化范围、CNY 基准、HTML Web Shell 目标、统一导航、设置页反馈归属和后续 stage 验收合同，不提前实现 Stage 1+。

Stage 0 source files:

| Purpose | Path |
| --- | --- |
| v0.2.1 record | `docs/pfi_v02/STAGE_V021_FRONTEND_OPTIMIZATION.md` |
| Frontend contract | `src/pfi_v02/stage_v021_frontend_contract.py` |
| Stage 0 test | `tests/test_v021_stage0_frontend_contract.py` |

Currency and header contract:

- Base currency is `CNY`.
- v0.2.1 historical header used the old CNY/AUD badge; current formal UI uses `AUD/CNY=4.69（YYYY/MM/DD HH:MM）`.
- v0.2.2 Stage 2 current header format is `AUD/CNY=4.69（YYYY/MM/DD HH:MM）`, meaning `1 AUD = 4.69 CNY`.
- The badge reads the effective local `06:00 Australia/Sydney` exchange snapshot from `data/fx_snapshots/`.
- Missing exchange data must show `汇率数据待更新`; PFI must not invent a live rate.

## Stage 1

Stage 1 builds the common skeleton for accounts, assets, data sources, ledger,
investment, consumption, recommendations, and reports.

Target first-level entries:

1. 首页总览
2. 账户与资产
3. 账本流水
4. 投资管理
5. 消费管理
6. 数据源与上传
7. 建议与复盘
8. 报告与洞察

Stage 1 source files:

| Purpose | Path |
| --- | --- |
| IA contract | `src/pfi_v02/stage1_ia.py` |
| Stage 1 record | `docs/pfi_v02/STAGE1_CORE_SKELETON.md` |
| Owner feature list | `功能清单.md` |
| Development record | `开发记录.md` |
| Model and parameter file | `模型参数文件.md` |
| External QBVS system | `../QBVS/qbvs` |
| Raw-data archive | `../MetaDatabase/PFI` |

## Stage 2

Stage 2 builds the data-source and low-operation sync MVP contract. It adds:

- full registry for 支付宝日常、支付宝基金、Moomoo AU、中国券商、ABC Bullion、CBA、微信、其他平台
- CBA CSV parser and watch folder detection
- Alipay daily CSV/ZIP parser and low-confidence review queue
- default local upload panel for 支付宝 CSV/ZIP bills at `http://localhost:8501`
- private Alipay import output under `~/.pfi/runtime/imports/alipay_daily`
- non-CSV contracts for 支付宝基金、中国券商、ABC Bullion
- Moomoo AU read-only OpenD/API contract that records external QBVS references
- WeChat ZIP/CSV/XLS/XLSX import contract
- reconciliation contracts for fund and bullion triangles

Stage 2 source files:

| Purpose | Path |
| --- | --- |
| Data source registry | `src/pfi_v02/stage2_registry.py` |
| CBA and Alipay import pipeline | `src/pfi_v02/stage2_import.py` |
| Non-CSV and reconciliation contracts | `src/pfi_v02/stage2_contracts.py` |
| Stage 2 record | `docs/pfi_v02/STAGE2_DATA_SYNC_MVP.md` |
| Stage 2 tests | `tests/test_stage2_*.py` |

## Stage 3

Stage 3 builds the owner-readable homepage/account/ledger MVP. It adds:

- homepage financial status cards: 净资产、现金、投资资产、本月支出、数据健康
- account map for 支付宝、支付宝基金、Moomoo AU、中国券商、ABC Bullion、CBA、微信
- account and asset list across investment、daily、cash、asset、liability categories
- AUD/CNY/USD/HKD fixture-based cross-currency view
- platform balance vs PFI ledger reconciliation status
- normalized ledger rows with batch/raw/parser evidence chains
- A/B/C/D owner review queue for low-confidence transactions
- sync-all plan that does not execute external login, payment, broker order, or real account mutation
- Web shell target 8 first-level entries

Stage 3 source files:

| Purpose | Path |
| --- | --- |
| Readable MVP read-model | `src/pfi_v02/stage3_read_mvp.py` |
| Stage 3 record | `docs/pfi_v02/STAGE3_READABLE_MVP.md` |
| Stage 3 tests | `tests/test_stage3_readable_mvp.py` |
| Web shell | `web/index.html`, `web/app/shell.js` |

## Stage 4

Stage 4 builds the investment and consumption analysis MVP. It adds:

- investment summary: total market value, unrealized PnL, allocation, cash position
- attribution split: market, active decision, fees, FX, cash drag
- risk analysis: concentration, drawdown, currency exposure, liquidity
- behavior review: chase, panic sell, frequent trading, holding period tags when trade evidence exists
- PFI strategy lab keeps strategy backtesting, parameter scan, market-feel training, and big-data simulator
- QBVS remains independent under `../QBVS`
- consumption summary: month spend, budget remaining, fixed/flexible spend
- classification analysis for Alipay, WeChat, and CBA with low-confidence review
- recurring subscription detection
- anomaly detection for large, duplicate, night, weekend, and impulsive spending
- 30/90/180 day cashflow forecast with life cash separated from investment cash

Stage 4 source files:

| Purpose | Path |
| --- | --- |
| Analysis MVP read-model | `src/pfi_v02/stage4_analysis_mvp.py` |
| Stage 4 record | `docs/pfi_v02/STAGE4_ANALYSIS_MVP.md` |
| Stage 4 tests | `tests/test_stage4_analysis_mvp.py` |
| Web shell | `web/index.html`, `web/app/shell.js` |

## Stage 5

Stage 5 builds the advice, report, and Alpha read-only export MVP. It adds:

- recommendation model with domain, evidence, expected effect, tradeoff, action, and owner decision
- review lifecycle for accept, reject, snooze, review, and effect measurement
- investment recommendations for concentration, trading frequency, cash position, and strategy pause/launch
- consumption recommendations for budget, subscription, anomaly, and cost saving with savings targets
- Top N recommendation ranking for the homepage without hiding the full lifecycle queue
- monthly, investment, consumption, and data-quality reports
- reproducible Markdown, JSON, and CSV export center with content hashes
- `pfi_context_snapshot_v1` read-only context export for external Alpha consumption
- explicit constraints: `trading_password_available=false` and `live_trade_submission_authorized=false`

Stage 5 source files:

| Purpose | Path |
| --- | --- |
| Advice/report/export model | `src/pfi_v02/stage5_advice_report_alpha.py` |
| Stage 5 record | `docs/pfi_v02/STAGE5_ADVICE_REPORT_ALPHA_EXPORT.md` |
| Stage 5 tests | `tests/test_stage5_advice_report_alpha.py` |
| Web shell | `web/index.html`, `web/app/shell.js` |

## Stage 6

Stage 6 completes the V0.2 synthetic E2E stabilization and delivery/rollback gate. It adds:

- multi-source fixture/contract matrix for 支付宝、支付宝基金、Moomoo AU、中国券商、ABC Bullion、CBA、微信
- homepage loop that must show accounts, investment, consumption, data health, and recommendations
- ledger loop for transfer, investment buy, consumption, refund, fee, valuation, fund redemption, bullion buy, and credit-card repayment
- recommendation loop for generate, display, accept, reject, snooze, review, and effect measurement
- regression/governance gate covering top-level QBVS smoke, Stage 6 focused tests, changed-only governance, and no broad refactor
- delivery/rollback gate with owner docs, diff summary, rollback plan, and follow-up list

Stage 6 source files:

| Purpose | Path |
| --- | --- |
| E2E stabilization model | `src/pfi_v02/stage6_e2e_stabilization.py` |
| Stage 6 record | `docs/pfi_v02/STAGE6_E2E_STABILIZATION.md` |
| Stage 6 tests | `tests/test_stage6_e2e_stabilization.py` |
| Web shell | `web/index.html`, `web/app/shell.js` |

## Boundaries

- No automatic real-money trading.
- No trading password.
- No broker-order or payment submission.
- No Alpha product page inside PFI.
- No Ralpha, System, or Development product page inside PFI.
- No Alpha repository modification in Stage 5.
- Stage 6 does not connect real accounts, does not submit payments or broker orders, and does not claim production release readiness.
- `../QBVS/qbvs` is an external independent system reference, not a PFI-owned runtime.
- User-provided raw data is archived under `../MetaDatabase` when explicitly authorized.

## Validation

```bash
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract -q
PYTHONPATH=src python3 -B -m unittest tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp tests.test_stage4_analysis_mvp tests.test_stage5_advice_report_alpha tests.test_stage6_e2e_stabilization -q
node --check web/app/shell.js
(cd ../QBVS && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q)
```

## v0.2.2 Stage 8

Stage 8 - 本地运行 Diff 与 Impacted Metrics 已加入 PFI 的数据库治理路线。

- 新增 `src/pfi_v02/stage_v022_runtime_diff.py`：生成依赖 hash snapshot、比较 diff、输出 impacted metrics report、判断 LLM 触发条件、生成本地 Codex Review Ticket 数据。
- 新增 `tests/test_v022_stage8_runtime_diff.py`：验证 `S8-P1-T1..S8-P3-T3`，包括无 diff 不联网、不生成 Codex ticket、不触发 LLM，标签显示名变化不污染净资产、投资收益、现金流窗口。
- 新增 `docs/pfi_v022/STAGE8_RUNTIME_DIFF_IMPACTED_METRICS.md`：中文验收报告。
- 新增 `review_queue/CODEX_REVIEW_TICKET_TEMPLATE.md`：本地中文复审票据模板，包含触发原因、影响指标、涉及文件、期望检查、禁止事项、中文业务解释。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage8`，记录 runtime refresh、P0/P1/P2 impacted metrics 和 LLM trigger policy。
- Stage 9 可视化与 UI/UX 已在后续单独 gate 中实现。

## v0.2.2 Stage 9

Stage 9 - 可视化与 UI/UX 已加入 PFI 的数据库治理路线。

- 新增 `src/pfi_v02/stage_v022_visualization_uiux.py`：生成参数中心模型、参数变更影响预览、Interconnection Map、现金流可视化模型和 Metric Drilldown Debugger。
- 新增 `tests/test_v022_stage9_visualization_uiux.py`：验证 `S9-P1-T1..S9-P4-T3`，不只检查 marker，也检查合同结构、可视化数据状态、现金流窗口、drilldown 字段和本地 HTML 外网依赖。
- 新增 `docs/pfi_v022/STAGE9_VISUALIZATION_UIUX.md`：中文验收报告。
- 新增 `docs/pfi_v022/INTERCONNECTION_MAP.md`：Mermaid 关系图，覆盖 `source -> raw -> normalized -> group -> event -> ledger -> metrics -> UI`。
- 新增 `web/interconnection-map.html`：本地 HTML 单文件审查页，覆盖首页总览、参数中心、Interconnection Map、Metric Dependency Graph、消费分类与标签、投资模型、消费模型、现金流可视化、Runtime Diff Dashboard、Agent Review Queue、验收清单。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage9`，记录 `visualization_uiux` 参数、Stage 9 task ids、本地 HTML 不依赖外网、现金流窗口和可点击节点。
- Stage 10 报告、建议与复盘已在后续单独 gate 中实现。

## v0.2.2 Stage 10

Stage 10 - 报告、建议与复盘已加入 PFI 的数据库治理路线。

- 新增 `src/pfi_v02/stage_v022_report_advice_review.py`：生成月报、投资报告、数据质量报告、行动建议定义、行动建议评分公式、建议生命周期和建议样本。
- 新增 `tests/test_v022_stage10_report_advice_review.py`：验证 `S10-P1-T1..S10-P2-T3`，覆盖双消费口径、投资成本行为、数据质量 Interconnection 指标、行动建议非自动投资、评分公式和生命周期。
- 新增 `docs/pfi_v022/STAGE10_REPORT_ADVICE_REVIEW.md`：中文验收报告。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage10`，记录 `report_advice_review` 参数、Stage 10 task ids、行动建议评分权重和生命周期状态。
- 报告口径锁定：月报同时显示消费总流出和生活消费；投资报告显示收益、成本、费用、汇率、交易频率、风格、现金拖累；数据质量报告显示未匹配转账、重复候选、低置信、标签变更、参数变更、hash diff。
- 建议生命周期锁定：`pending`、`accepted`、`rejected`、`snoozed`、`reviewed`、`effect_measured`。
- 行动建议与复盘不是自动买卖建议，不生成券商订单、支付动作或自动投资动作。
- Stage 11 测试与验证已在后续单独 gate 中实现。

## v0.2.2 Stage 11

Stage 11 - 测试与验证已加入 PFI 的数据库治理路线。

- 新增 `src/pfi_v02/stage_v022_test_validation.py`：生成基于真实 `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` 的金融逻辑、跨板块一致性和可视化一致性验证模型。
- 新增 `tests/test_v022_stage11_test_validation.py`：验证 `S11-P1-T1..S11-P3-T3`，覆盖投资入金计入消费总流出、基金申购计入消费总流出、退款抵消、信用卡还款不重复计入生活消费。
- 新增 `docs/pfi_v022/STAGE11_TEST_VALIDATION.md`：中文验收报告。
- `config/pfi_parameters.yaml` 记录 `test_validation` 参数、Stage 11 task ids、图表来源字段、图表新鲜度、性能状态、真实数据来源和中文真实空态策略。
- `S11-P2-T3` 跨板块一致性锁定：首页消费总流出 = 消费页消费总流出 = 月报消费总流出；首页投资资产 = 投资页投资资产 = 投资报告投资资产；现金流预测来源能追溯到真实账本事件，暂无真实计划事件时显示中文真实空态。
- `S11-P3-T3` 可视化一致性锁定：每个图表必须追溯 `metric_id`、`formula_id`、`parameter_hash`、`data_hash`，并显示 `compute time` 和 `cache status`。
- Stage 11 复审后，真实 `8815` 条标准化流水作为可视化性能门输入；暂无真实 CBA -> Moomoo、信用卡还款、计划事件或持仓快照时不构造金额、交易 ID 或持仓。
- 本轮不实现 Stage 12 文档同步与最终交付，不执行 Stage 13 后置触发型复核，不修改 v0.2.1 主 Web Shell UIUX 基线，不联网、不调用外部 LLM、不生成真实 agent 任务。

## v0.2.2 Stage 12

Stage 12 - 文档同步与交付已加入 PFI 的数据库治理路线。

- Task ID 清单：`S12-P1-T1`、`S12-P1-T2`、`S12-P1-T3`、`S12-P2-T1`、`S12-P2-T2`、`S12-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_delivery.py`：生成三基文件、本地 HTML、Roadmap 验证、最终摘要和 2 轮 × 6 Agent 自检交付模型。
- 新增 `tests/test_v022_stage12_delivery.py`：验证 `S12-P1-T1..S12-P2-T3`，覆盖参数中心、标签系统、Interconnection 可视化、双消费口径、现金流图表、diff ticket、Stage -> Phase -> Task 和用户人工复核要求。
- 新增 `web/pfi_v022_logic_review.html`：本地 UI/UX 审查 HTML，中文、可打开、可点击，覆盖参数、分类、标签、图表、diff、Interconnection。
- 新增 `docs/pfi_v022/STAGE12_DELIVERY_REPORT.md`：Stage 12 Roadmap 与验证报告，采用 Stage -> Phase -> Task，不使用 milestone 列表替代。
- 新增 `docs/pfi_v022/SIX_AGENT_DELIVERY_REVIEW.md`：2 轮 × 6 Agent 自检报告，阻塞项为 0。
- 新增 `reports/pfi_v022_summary.md`：最终中文摘要，说明做了什么、怎么验收、哪些未做、哪些需要用户人工复核。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage12`，新增 `delivery` 参数域和 `stage12_task_ids`；`config/pfi_v022_parameters.yaml` 是 Task Pack 要求的参数交付镜像。
- 本轮不执行 Stage 13 后置触发型复核，不修改 v0.2.1 主 Web Shell UIUX 基线，不清理或迁移 Downloads 污染文件夹。
- Stage 12 复审后，`web/pfi_v022_logic_review.html` 只作为本地审查页，不进入正式运行页面；摘要和交付报告只覆盖 Stage 12，不再声明 Stage 13 执行或 Downloads 清理。
- Stage 12 承接真实数据证据：`MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`，`8815` 条标准化支付宝流水；缺少真实数据的区域继续使用中文真实空态。

## v0.2.2 Stage 13

Stage 13 - 后置触发型复核已加入 PFI 的数据库治理路线，并已完成本轮复审。

- Stage 13 单轮历史边界：本轮只复审解决 Stage 13；整体项目复审解决不在本轮实现；GitHub 同步不在本轮执行；app 入口重装不在本轮执行；禁止全仓无差别扫描；不联网；不调用外部 LLM；阻塞项数量：`0`。
- Task ID 清单：`S13-P1-T1`、`S13-P1-T2`、`S13-P1-T3`。
- `S13-P1-T1`：在 `交付前人工指定` 触发下生成本地 Codex Review Ticket：`PFI/review_queue/codex_review_stage13_owner_specified_20260628.md`。
- `S13-P1-T2`：仅对异常区域进行复核，scope files 由 ticket 指定，禁止全仓无差别扫描。
- `S13-P1-T3`：复核结果写入 `PFI/开发记录.md`，包含问题、修复、验证、剩余风险。
- Downloads 污染文件夹清理：`PFI_V022_STAGE0_PRE_CANONICAL_SYNC_20260628T090028` 等 6 个 PFI 预同步临时目录已归档到 `PFI/docs/pfi_v022/downloads_cleanup/PFI_V022_PRE_CANONICAL_SYNC_ARCHIVE_20260628.tar.gz` 并移出 Downloads。
- `PFI.app` 当前仍在 Downloads；用户提供的 taskpack、roadmap、zip、md 源文件名保留在 `PFI/docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md`，本轮不恢复或制造缺失源文件。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage13`，新增 `post_review` 参数域和 `stage13_task_ids`。
- `PFI/reports/pfi_v022_stage13_review_summary.md` 是 Stage 13 独立摘要，`PFI/reports/pfi_v022_summary.md` 继续保持 Stage12-only。
- Stage 13 单轮复审时不执行整体项目复审解决、GitHub 同步或 app 入口重装；当前整体项目复审解决已在后续总门完成。阻塞项数量：`0`。

## v0.2.2 整体项目复审解决

整体项目复审解决已完成，覆盖 Stage 0-13、真实 MetaDatabase、正式 8501 app、测试数据边界、GitHub main 同步和 app 入口重装。

- 真实 MetaDatabase：`MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`，`8815` 条真实标准化流水。
- 正式页面、报告、图表、首页摘要和建议：只允许读取真实 MetaDatabase 派生数据或中文真实空态。
- 数据边界：不得使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据作为验收依据。
- 验证总门：完整 PFI pytest `321 passed, 729 subtests passed`；Stage 0-13 + overall 回归 `139 passed, 692 subtests passed`。
- 真实浏览器矩阵：`/tmp/pfi_v022_overall_review_recheck/summary.json`，`131 pass / 0 fail`，覆盖桌面/移动端、二级入口、全局搜索 `406/8815`、禁词扫描和 console/page errors `0`。
- GitHub main 同步：本轮 closeout 执行，path-limited 到 `PFI/` 与 `MetaDatabase/PFI/`。
- app 入口重装：已执行，`/Applications/PFI.app`、`~/Downloads/PFI.app` 绑定 canonical PFI，`~/Desktop/PFI.app` 指向 `/Applications/PFI.app`。
- 阻塞项数量：`0`。

## v0.2.1.1 Stage 1 - 产品壳与路由

- 本轮只完成 Stage 1，不实现图表、上传闭环、持仓编辑或报告。
- 正式一级入口固定为 10 个：首页总览、账户与资产、账本流水、投资管理、消费管理、数据源与上传、建议与复盘、报告与洞察、市场与研究、设置。
- 旧入口“首页 / 市场 / 研究 / 持仓 / 策略实验室 / 数据与系统”不再显示为一级导航，只保留为 route alias、命令别名和搜索别名。
- 策略实验室 canonical route 改为 `/market-research/strategy-lab`；旧 `#/strategy-lab` 和 `#/investment/strategy-lab` 兼容跳转到同一路由。
- 合同与交付记录：`docs/pfi_v0211/STAGE1_PRODUCT_SHELL_ROUTING.md`。
