# DEVELOPMENT_LEDGER

product_version: v0.2.4 Repair Pack
model_count: 1
formula_count: 1
parameter_count: 23
task_count: 9
acceptance_count: 9

## 2026-06-27

- PFI 根项目三基入口统一为 Markdown 文件名。
- 补齐 PFI 根最小治理文件。
- 完成 PFI V0.2 Stage 2 本地合同验收、入口验收和缓存清理记录。
- 完成 PFI V0.2 Stage 3 首页、账户、账本可读 MVP，本地只读 read-model 和 Web shell 8 入口刷新。
- 完成 PFI V0.2 Stage 4 投资与消费智能分析 MVP，本地只读 analysis read-model 和 Web shell 投资/消费分析刷新。
- 完成 PFI V0.2 Stage 5 建议、报告、Alpha 只读出口 MVP，本地只读 delivery model 和 Web shell 建议/报告入口刷新。
- 完成 PFI V0.2 Stage 6 端到端验收与稳定化，本地 synthetic E2E、20 gate audit、ACC-* audit、回归治理和回滚计划刷新。
- 建立 PFI v0.2.1 前端优化 Stage 0 准备合同，锁定 CNY 基准、CNY/AUD 06:00 顶栏汇率、HTML Web Shell 目标、统一导航和后续 P0-P8 验收顺序。
- 不新增生产或实盘能力声明；同步全部只生成计划，不执行外部动作。

## 2026-06-28

- 完成 PFI v0.2.2 Stage 0 任务锁定与文件定位，生成 `docs/pfi_v022/STAGE0_BASELINE_REPORT.md`、`docs/pfi_v022/ROADMAP_LOCK.md` 和 Stage 0 合同测试。
- 完成 PFI v0.2.2 Stage 1 模型参数文件重构，新增 `config/pfi_parameters.yaml`、`docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md` 和 `tests/test_pfi_parameters_consistency.py`。
- product_version v0.2.2 数据库治理 Stage 1 对应本轮参数治理文档状态；`VERSION` 继续保留 v0.2.1 前端优化，表示当前 Web Shell UI 基线未在 Stage 1 修改。
- Stage 1 参数治理覆盖 `S1-P1-T1..S1-P2-T3`，建立中文参数总目录、机器可读参数源、公式中文解释、阈值说明表和变量中文别名。
- 本轮不修改 v0.2.1 HTML Web Shell，不实现 Stage 2 汇率快照读取，不新增真实交易、自动投资、支付或券商提交能力。
- 完成 PFI v0.2.2 Stage 2 CNY 基准与汇率规则，新增 `src/pfi_v02/stage_v022_fx.py`、真实快照 `data/fx_snapshots/AUD_CNY/2026-06-28.json`、`docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md` 和 `tests/test_v022_fx_effective_date.py`。
- product_version v0.2.2 数据库治理 Stage 2 对应本轮 CNY/Fx 文档状态；`VERSION` 继续保留 v0.2.1 前端优化，表示 UIUX 基线仍沿用 v0.2.1 HTML Web Shell。
- Stage 2 覆盖 `S2-P1-T1..S2-P2-T3`，建立 `AUD/CNY` 真实快照、06:00 有效汇率日、普通运行不默认联网、原币辅助显示和账本金额字段。
- 完成 PFI v0.2.2 Stage 3 数据源、账户角色与可扩展结构，新增 `src/pfi_v02/stage_v022_source_profile.py`、`docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md` 和 `tests/test_v022_stage3_source_account_profiles.py`。
- product_version v0.2.2 数据库治理 Stage 3 对应本轮 source/account profile 文档状态；`VERSION` 继续保留 v0.2.1 前端优化，表示 UIUX 基线仍沿用 v0.2.1 HTML Web Shell。
- Stage 3 覆盖 `S3-P1-T1..S3-P2-T3`，建立 source profile schema、capabilities、`other_source_template`、账户多角色、生效期和 role/event type 计算策略。
- 完成 PFI v0.2.2 Stage 4 Economic Event 与 Interconnection 逻辑，新增 `src/pfi_v02/stage_v022_interconnection.py`、`docs/pfi_v022/STAGE4_INTERCONNECTION.md`、`docs/pfi_v02/INTERCONNECTION_MATRIX.md`、`tests/test_v022_interconnection_no_double_count.py` 和 `tests/test_v022_consumption_investment_outflow.py`。
- product_version v0.2.2 数据库治理 Stage 4 对应本轮 interconnection/no-double-count 文档状态；`VERSION` 继续保留 v0.2.1 前端优化，表示 UIUX 基线仍沿用 v0.2.1 HTML Web Shell。
- Stage 4 覆盖 `S4-P1-T1..S4-P2-T3`，建立 `economic_event_id`、`interconnection_group_id`、事件影响 flags、Interconnection Matrix、Metric Dependency Graph、双消费口径和 no-double-count 规则。

## ITER-20260710-PFI-CF-L2

- 日期：2026-07-10。
- 事实等级：本地 build、隐私扫描、13 项兼容性测试、桌面/移动端渲染、Wrangler dry-run、永久 workers.dev 部署与 HTTP 检查均为 VERIFIED。
- 版本前后：`v0.2.1 前端优化` / `v0.2.1 前端优化`。
- Task / Acceptance：`CF-L2-20260710` / `ACC-CF-L2-20260710`。
- 目标：增加隔离的定性脱敏 L2 产品壳，不读取真实账户、组合、交易、券商凭据、私密报告或本地数据库。
- 结果：静态 build、private dist scan、响应式 QA 和 Wrangler 4.110.0 dry-run 通过；永久 deployment `7c6d216e-0fd3-43e6-904b-404aac0d776e` 已上线 `https://codex-pfi.linzezhang35.workers.dev`，根页面与 `public-surface.json` 均为 HTTP 200。
- 模型与参数边界：不修改投资、消费、现金流、汇率、分类、推荐或执行逻辑；`PARAM-PFI-023` 只记录公开 adapter 的 L2 兼容合同。
- 回滚：删除 `web/cloudflare-public` 与本次治理记录；PFI 私密核心和真实财务数据不受影响。
- 下一门槛：仅剩可选 `pfi.linzezhang.com` 绑定；真实账户、broker、支付和执行能力仍不在 L2 范围。

## ITER-20260710-PFI-V024-R1

- Task / Acceptance：`PFI-V024-R1-20260710` / `ACC-PFI-V024-R1`。
- 结果：恢复 v0.2.4 canonical closeout history；sparse worktree 通过 immutable Git OID 只读验证真实 `MetaDatabase/PFI`，不触发 lazy fetch，不复制或改写财务数据。
- 验证：focused `33 passed`、v0.2.3 `200 passed`、v0.2.4 `219 passed`、check-render `0/0`、独立复核 `APPROVED`。
- 下一门槛：独立 `v0.2.4 overall re-review`。

## ITER-20260710-PFI-V024-OVERALL-REREVIEW

- Task / Acceptance：`PFI-V024-OVERALL-REREVIEW-20260710` / `ACC-PFI-V024-OVERALL-REREVIEW`。
- 当前范围：复核原 `v0.2.3-repair` Stage 0-9、Phase R1、真实数据和 final-delivery boundary；不执行 GitHub upload 或 app reinstall。
- 当前证据：40/40 phase/whole-stage evidence unit 四件套完整，84 个 JSON 可解析，真实数据为 4 raw / 8815 processed / as of 2026-06-03。
- 当前结果：overall re-review pass；focused `12 passed`、v0.2.3 `200 passed`、v0.2.4 `231 passed`、semantic/UI/data/renderer/reviewer gates 全部通过。`product goal 未完成`，唯一下一 gate 为 `PFI-V024-FINAL-DELIVERY`。
