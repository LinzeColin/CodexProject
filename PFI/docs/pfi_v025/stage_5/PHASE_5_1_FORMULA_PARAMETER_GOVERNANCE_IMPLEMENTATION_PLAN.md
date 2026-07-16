# PFI v0.2.5 Stage 5 / Phase 5.1 实施记录

## 唯一执行合同

- Phase：`V025-S5-P5.1` — 公式与参数治理。
- Tasks：`S5-P1-T1`、`S5-P1-T2`、`S5-P1-T3`、`S5-P1-T4`。
- Acceptance：`ACC-PFI-V025-STAGE5-WHOLE-REVIEW`，仅形成 Phase 5.1 candidate evidence；Stage 5 gate 尚未验收。
- 事实基线：commit `dbf2f726ae4356ce69cbb2500f9d1cfdbc285cec`（Stage 4 accepted_for_transition）。
- 本轮不执行 Phase 5.2 双消费/投资/现金流模型，不执行 Phase 5.3 真实数据不变量、敏感性或模型验证，不执行 Stage 5 whole-stage review。

## S5-P1-T1 — 公式注册表与生命周期

- `PFI/config/formulas/v025_formula_registry.json` 收录现行 `FORM-PFI-001..014`。
- 每项含 `formula_id`、`version`、中文名称/定义、inputs、output/outputs、unit、parameters、boundaries、dependencies、test refs、`effective_from`、`formula_hash`、validation/lifecycle status 和历史兼容说明。
- `formula_hash` 对排除自身 hash 字段后的 canonical JSON 重建；当前 14 项 mismatch=`0`。
- 生命周期为 `draft -> active -> deprecated|superseded`；active 同版本内容不可原地改写，superseded 必须声明 replacement version。
- `2026-07-15` 是这些 machine-readable registry versions 的生效日，不重写既有 Stage 2–4 runtime/evidence hash。

## S5-P1-T2 — 五载体零冲突

- canonical values 同步到 formula registry JSON、JSON-compatible `pfi_parameters.yaml`、Python runtime、application UI payload 与 rendered `模型参数文件.md`。
- 一致性键覆盖 registry version、base currency、FX direction/unit/example policy、lifecycle、记录分类策略、六维 IDs 与 aggregate-score prohibition。
- `parameter_consistency.json` 的 `conflict_count=0`。
- 本 Phase 只建立可供 UI 消费的同源 payload；Roadmap 不允许在 Phase 5.1 修改 Web UI，正式视觉呈现不在本轮伪造完成。

## S5-P1-T3 — CNY/FX 方向与单位

- 基础币种固定为 `CNY`。
- `AUD/CNY` 固定解释为 `1 AUD = X CNY`，rate unit 为 `CNY/AUD`，换算只允许 `amount_cny = amount_aud * fx_rate`。
- 例：`10.00 AUD * 4.81 CNY/AUD = 48.1000 CNY`；`4.81` 只用于方向单元测试，`production_default_fx_rate=null`。
- CNY 使用 identity；非 Decimal、float、零/负/非有限 rate、倒置方向或错误单位全部 fail closed；本层不舍入。

## S5-P1-T4 — 六维可信度

- `classification_confidence` 保留 v0.2.2 中文评分权重：30/10/20/15/15/10，合计 100；阈值 70；禁止按 source 分层。
- `source_coverage`、`reconciliation_coverage`、`valuation_coverage`、`model_validation`、`report_completeness` 独立存在。
- schema 精确要求六维且 `additionalProperties=false`；runtime 额外显式拒绝 `overall_confidence`。
- 当前 production FX、余额、负债、持仓和价格仍未加载；Phase 5.1 不宣称模型有效，真实模型验证仍属于 Phase 5.3。

## 验证、风险与回滚

- 目标测试：`PFI/tests/test_v025_stage5_formula_registry.py`。
- 回归：全部 Stage 4 tests 与旧 `test_pfi_parameters_consistency.py`，确保新增注册层不改变已验收 read model/legacy 参数合同。
- 治理：JSON/schema、renderer、changed-scope/full-shadow governance/sync 和 `git diff --check`。
- 回滚整个本地 Phase commit 即可；raw、ledger、数据库、真实财务行、生产 FX、GitHub 与 PFI.app 均未修改。
- 任一 hash 不可重建、载体 conflict、方向/单位歧义、单一总分出现，或需要 Phase 5.2 才能完成时，本 Phase 停止且不得声明 Stage 5 pass。
