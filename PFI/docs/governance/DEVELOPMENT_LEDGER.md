# DEVELOPMENT_LEDGER

product_version: v0.2.1 前端优化
model_count: 1
formula_count: 1
parameter_count: 22
task_count: 6
acceptance_count: 6

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
