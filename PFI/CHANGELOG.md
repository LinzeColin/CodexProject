# CHANGELOG

## v0.2.2 数据库治理 Stage 0 补做复核 - 2026-06-28

- 新增 `docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`，把 Stage 0 的 `S0-P1-T1..S0-P2-T2`、Milestone 0 acceptance criteria、stop condition、Agent 1/3 自检和验证命令整理为独立中文验收入口。
- 更新 `docs/pfi_v022/ROADMAP_LOCK.md`、`docs/pfi_v022/README.md`、`STAGE0_BASELINE_REPORT.md`、三基文件和 `HANDOFF.md`，明确 Stage 0 已补做复核且后续仍从 Stage 3 开始。
- 本轮不回滚 Stage 1/2，不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`、`PFI/web/styles/tokens.css`，不新增逻辑审查 HTML，也不做真实交易、自动投资或默认联网抓汇率。

## v0.2.2 数据库治理 Stage 2 - 2026-06-28

- 完成 Stage 2 `CNY 基准与汇率规则`，覆盖 `S2-P1-T1..S2-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_fx.py`，实现 06:00 Australia/Sydney 有效汇率日、普通运行本地快照读取、显式联网刷新、快照 hash 校验、金额转 CNY 和账本金额字段生成。
- 新增真实快照 `data/fx_snapshots/AUD_CNY/2026-06-28.json`：`fx_AUD_CNY_20260628`，`1 AUD = 4.6874 CNY`，来源 `Frankfurter v2 public API`。
- Web Shell 顶部汇率徽标从历史 `CNY/AUD=4.70` 更新为当前 `AUD/CNY=4.69（YYYYMMDD--HH:MM）`，主页等主金额显示以 `CNY` 为主。
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
- 锁定后续 UI 货币契约：整体系统以 CNY 元为基准，所有页面顶部右上角显示 `CNY/AUD=4.70（YYYYMMDD--HH:MM）`，读取当日 06:00 Australia/Sydney 汇率快照，缺失时显示中文空状态且不得伪造汇率。
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
