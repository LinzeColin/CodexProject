# MODEL_SPEC

model_count: 1
formula_count: 1
parameter_count: 23
task_count: 9
acceptance_count: 9

## 当前模型

`MOD-PFI-001` 记录 PFI V0.2 根项目合同：账户、资产、账本、数据源、投资分析、消费分析、建议、报告、Alpha 只读 context export、Stage 6 synthetic E2E 和 rollback 边界。证据来自 `PFI/README.md`、`PFI/docs/pfi_v02/STAGE1_CORE_SKELETON.md`、`PFI/docs/pfi_v02/STAGE2_DATA_SYNC_MVP.md`、`PFI/docs/pfi_v02/STAGE2_ACCEPTANCE_AUDIT.md`、`PFI/docs/pfi_v02/STAGE3_READABLE_MVP.md`、`PFI/docs/pfi_v02/STAGE4_ANALYSIS_MVP.md`、`PFI/docs/pfi_v02/STAGE5_ADVICE_REPORT_ALPHA_EXPORT.md` 和 `PFI/docs/pfi_v02/STAGE6_E2E_STABILIZATION.md`。

## 非模型验收事实

v0.2.4 Stage 0-9、用户确认、真实数据边界与 post-overall consistency gate 由 `FEAT-PFI-V024-OVERALL`、`EVID-PFI-V024-OVERALL` 和 Roadmap acceptance 管理；它们不是 math/stat/ML、ranking/scoring、公式、规则引擎或 LLM routing model，不单独登记 model ID。

## 边界

本文件不声明生产就绪，不声明实盘执行能力，不要求真实凭证。
