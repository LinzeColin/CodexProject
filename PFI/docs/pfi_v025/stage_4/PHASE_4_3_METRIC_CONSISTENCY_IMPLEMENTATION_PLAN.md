# PFI v0.2.5 Stage 4 / Phase 4.3 实施记录

## 唯一执行合同

- Phase：`V025-S4-P4.3` — Metric State 与跨页一致性。
- Tasks：`S4-P3-T1`、`S4-P3-T2`、`S4-P3-T3`、`S4-P3-T4`。
- Acceptance：`ACC-PFI-V025-S4-P43-METRIC-CONSISTENCY`。
- 事实基线：commit `1ab51eb518c30b10bab6a7d9b4442e7c462c6452`。
- 只完成 Phase 4.3；Stage 4 整阶段独立审查、整改、复审和 Stage 5 transition 均不在本轮。

## 真实输入边界

- 只读取已跟踪的 Stage 2 aggregate source manifest、Stage 3 page-independent event read-model hash、Phase 4.1 account read model 和 Phase 4.2 investment read model。
- `SRC-ACCOUNT-BALANCES`、`SRC-LIABILITIES`、`SRC-HOLDINGS`、`SRC-MARKET-PRICES`、`SRC-FX-SNAPSHOT` 均保持 `not_loaded`。
- 不读取私密财务行，不打开或写入 SQLite，不用交易流水推断余额/持仓，不使用 mock/sample/demo/synthetic/fixture/fake 财务数据。

## S4-P3-T1 — 严格 Metric State

- 保留 Task Pack 的 `metric_state.schema.json` 原文，并新增项目严格扩展 `metric_state_strict.schema.json`。
- 状态完整覆盖 `ready`、`confirmed_zero` 和 11 个非 ready 状态。
- 任一非 ready 状态的 `value` 必须为 `null`。
- `ready` 的财务零不允许直接显示；真实零必须使用 `confirmed_zero`。
- `confirmed_zero` 必须同时具备来源、记录数、coverage、as-of、公式/参数/数据/hash、分维度 confidence/coverage、模型验证和报告完整度证据。

## S4-P3-T2 — 可重建 Hash

- `dependency_set_hash = SHA256(canonical_json(sorted dependency hashes))`。
- `read_model_hash` 绑定 component read-model、Stage 2 source manifest、Stage 3 event snapshot、核心 metric state、formula hash 和 parameter hash。
- `observed_at` 与 surface/page identity 不进入 read-model hash；相同快照在不同页面和不同观察时刻得到同一 hash。
- 每个 metric 同时保存自己的 dependency map、dependency-set hash、component read-model hash 和全局 read-model hash。

## S4-P3-T3 — 五 Surface 同源

- 正式 surfaces 固定为 `homepage`、`accounts`、`investment`、`consumption`、`report`。
- 五个 surface 绑定相同 `read_model_hash`、`dependency_set_hash`、metric IDs 和 metric fingerprints；当前差异数为 `0`。
- `home -> homepage`、`insights -> report` 仅作为 v0.2.4 兼容 alias，不进入正式 surface 集或 hash。
- `/api/read-model-status` 返回统一 v0.2.5 snapshot；`web/app/data_state.js` 对严格合同 fail closed，并保留版本化旧 API。
- runtime/frontend 源码进入 release-hash 闭包，因此只更新源 manifest 与 embedded manifest 的派生 hash；未重装任何 App bundle。

## S4-P3-T4 — Evidence 与停止点

- Evidence Pack 位于 `PFI/reports/pfi_v025/stage_4/phase_4_3/`。
- 当前 7 个核心财务指标全部为 `not_loaded/null`，financial values emitted=`0`，confirmed-zero=`0`。
- Phase 4.3 只能成为 `candidate_pass`；12/12 Stage tasks 仅为 `candidate_complete`。
- 下一 gate 是 `ACC-PFI-V025-STAGE4-WHOLE-REVIEW`，必须另行执行独立整阶段审查、整改、复审和明确 transition acceptance；不得直接进入 Stage 5。

## 验证与回滚

- 运行 Roadmap 四条 Stage 4 pytest、Node surface/render contract、runtime/cache identity 回归、Stage 2/3 immutable-evidence 回归，以及 changed-scope governance/renderer。
- read model 是派生层；回滚本提交后按 Phase 4.1/4.2 输入重建即可，不覆盖 raw、ledger 或用户输入。
- 任一非 ready 显示财务零、五 surface hash/fingerprint 不一致、需要读取私密数据或治理失败时，本 Phase 不得声明 candidate pass。
