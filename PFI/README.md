# PFI

PFI V0.2 is the Personal Financial Intelligence project under
`LinzeColin/CodexProject/PFI`.

`PFI/` is the active PFI product root. `QBVS/` is a separate top-level system
under `LinzeColin/CodexProject/QBVS`; PFI investment management does not own
or cover QBVS.

## v0.2.2 数据库治理 Stage 7

`v0.2.2 数据库治理` 当前完成 Stage 7：模型公式、阈值与评分标准。本轮把置信度、消费、投资、现金流公式和阈值集中到机器可读参数、中文参数说明、合同模块和行为测试中；不实现 Stage 8 Runtime Diff、Stage 9 参数中心、Stage 10 建议生命周期，不新增真实交易、自动投资、支付或券商提交能力。

Stage 7 source files:

| Purpose | Path |
| --- | --- |
| 中文参数总目录 | `模型参数文件.md` |
| 机器可读参数源 | `config/pfi_parameters.yaml` |
| 参数变更记录 | `config/parameter_changelog.md` |
| Stage 1 验收报告 | `docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md` |
| Stage 2 验收报告 | `docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md` |
| Stage 3 验收报告 | `docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md` |
| Stage 4 验收报告 | `docs/pfi_v022/STAGE4_INTERCONNECTION.md` |
| Stage 5 验收报告 | `docs/pfi_v022/STAGE5_LEDGER_TAXONOMY.md` |
| Stage 6 验收报告 | `docs/pfi_v022/STAGE6_TAGS_CUSTOM_VIEWS.md` |
| Stage 7 验收报告 | `docs/pfi_v022/STAGE7_FORMULA_SCORING.md` |
| Interconnection Matrix | `docs/pfi_v02/INTERCONNECTION_MATRIX.md` |
| Stage 0-13 roadmap lock | `docs/pfi_v022/ROADMAP_LOCK.md` |
| Stage 7 contract | `src/pfi_v02/stage_v022_database_governance.py` |
| Stage 5 ledger taxonomy | `src/pfi_v02/stage_v022_ledger_taxonomy.py` |
| Stage 6 tags/views | `src/pfi_v02/stage_v022_tags_views.py` |
| Stage 7 formula scoring | `src/pfi_v02/stage_v022_formula_scoring.py` |
| Stage 6 local HTML | `web/pfi_v022_tag_views.html` |
| 汇率快照读取模块 | `src/pfi_v02/stage_v022_fx.py` |
| 数据源与账户角色模块 | `src/pfi_v02/stage_v022_source_profile.py` |
| Interconnection 模块 | `src/pfi_v02/stage_v022_interconnection.py` |
| 真实汇率快照 | `data/fx_snapshots/AUD_CNY/2026-06-28.json` |
| Stage 2 FX test | `tests/test_v022_fx_effective_date.py` |
| Stage 3 source/account test | `tests/test_v022_stage3_source_account_profiles.py` |
| Stage 4 no-double-count test | `tests/test_v022_interconnection_no_double_count.py` |
| Stage 4 consumption/investment outflow test | `tests/test_v022_consumption_investment_outflow.py` |
| Stage 5 ledger taxonomy test | `tests/test_v022_stage5_ledger_taxonomy.py` |
| Stage 6 tags/views test | `tests/test_v022_stage6_tags_views.py` |
| Stage 7 formula/scoring test | `tests/test_v022_stage7_formula_scoring.py` |
| 参数一致性测试 | `tests/test_pfi_parameters_consistency.py` |

Stage 7 locked parameters:

- 主货币：`CNY`。
- 当前前端徽标：`AUD/CNY=4.69（YYYYMMDD--HH:MM）`。
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
- `interconnection_group_id`：同一资金链路进入一个关联组。
- `消费总流出`：普通消费、投资入金、基金申购、黄金申购、投资买入、费用进入该口径，退款抵消。
- `生活消费`：普通生活消费进入该口径，退款抵消；投资入金、基金申购、投资买入不进入。
- Stage 4 stop condition：`投资入金未进入消费总流出`、`基金申购未进入消费总流出`、`投资入金错误进入生活消费`、同一 `interconnection_group_id` 重复进入核心金额。
- Agent 1 复核消费、投资、现金流口径；Agent 2 复核 source -> transaction -> group -> economic event -> ledger -> metric 链路。
- Stage 5 事件类型表：消费、投资入金、基金申购、黄金申购、投资买入、投资卖出、退款、费用、信用卡还款、内部转账、收入、估值、汇率兑换。
- Stage 5 双消费展示：首页、消费页、报告必须同时展示 `消费总流出` 与 `生活消费` 并解释差异。
- Stage 5 分类约束：`L1 ≤ 12`、每类 `L2 ≤ 5`、总 `L2 ≤ 50`、每笔交易主分类数量为 `1`。
- Stage 5 默认 taxonomy：餐饮食品、居住家庭、交通出行、购物用品、医疗健康、教育成长、娱乐社交、订阅服务、金融费用、投资资金流出、家庭责任、调整其他。
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
- v0.2.1 historical header format was `CNY/AUD=4.70（YYYYMMDD--HH:MM）`.
- v0.2.2 Stage 2 current header format is `AUD/CNY=4.69（YYYYMMDD--HH:MM）`, meaning `1 AUD = 4.69 CNY`.
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
- 本轮不实现 Stage 9 可视化与 UI/UX，不修改 v0.2.1 HTML Web Shell UIUX 基线，不联网、不调用外部 LLM、不生成真实 agent 任务。
