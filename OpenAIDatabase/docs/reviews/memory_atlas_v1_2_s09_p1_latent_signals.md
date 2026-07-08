# Memory Atlas v1.2 S09 P1 Latent Signals

## Scope

- task_id: `MA-V12-S09P1`
- acceptance_id: `ACC-MA-V12-S09P1`
- status: `phase_s09_p1_latent_signals_completed_pending_s09_p2`
- validator: `validate:v1.2-s09-p1`
- config: `机器治理/行为智能模型/latent_signals.v1_2_s09_p1.json`
- builder: `scripts/build_memory_atlas_latent_signals.py`
- output: `data/derived/behavior_intelligence/latent_signals.json`

S09 P1 only generates evidence-backed latent signal candidates. It does not
create self-iteration suggestions, proposal expiry, decision-debt ledger,
proposal apply execution, raw mutation, remote push, or GitHub main upload.

## Acceptance

Each latent signal contains:

- `claim_zh`
- `supporting_evidence_refs`
- `contradicting_evidence_refs`
- `alternative_explanation_zh`
- `confidence`
- `evidence_strength_badge`
- `next_validation_zh`

The Evidence Strength Badge follows the v1.2 task pack:

- `A`: 多来源、多时间点、多证据一致
- `B`: 单来源但多次出现
- `C`: 新兴信号，证据较少
- `D`: 假设，需要验证

Current output:

| Signal | Claim Type | Badge | Confidence | Next Validation |
|---|---|---:|---:|---|
| `latent_asset_compounding_b40981a7787e` | `reusable_asset_candidate` | B | 0.63 | 只沉淀能被另一 agent 从 GitHub 恢复并运行的最小资产；无法复跑的说明先不扩写。 |
| `latent_automation_reuse_ef89cc773c20` | `workflow_reuse_candidate` | B | 0.63 | 下一轮只选一个最高分候选，验证是否能用一个 dry-run 命令减少重复操作；若不能，就降级为记录项。 |
| `latent_discussion_artifact_e73037ee7630` | `artifact_closure_candidate` | B | 0.63 | 下次出现同类主题时，先要求一个可验收文件或命令；若无法定义，就归档为暂不推进候选。 |
| `latent_quality_ceiling_38f9e3b406ca` | `quality_ceiling_candidate` | B | 0.63 | 下一次同类优化前写明质量上限和停止条件；达到上限后只修阻断验收的问题。 |
| `latent_scope_contract_faa8ed208720` | `scope_boundary_candidate` | B | 0.63 | 下一次同类 run 开始前写出非目标列表；若新增需求不在非目标例外内，就进入下一 phase 而非本轮扩张。 |

## Safety

- Claims are phrased as falsifiable candidates, not final conclusions.
- Every signal has support and counter-evidence.
- Every signal has an alternative explanation and next validation.
- Confidence is capped at `0.85`; current output max is `0.63`.
- The builder blocks psychological diagnosis terms and personality labels inside signal claims, alternatives and next validations.
- `atlasctl.py audit --check latent-safety` validates the same machine gate.

## Validation

- `python -B -m unittest OpenAIDatabase.tests.test_s09p1_latent_signals -q`
- `python OpenAIDatabase/scripts/atlasctl.py analyze --stage latent --dry-run`
- `python OpenAIDatabase/scripts/atlasctl.py audit --check latent-safety`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s09-p1`

## Boundary

Machine-readable boundary summary: Memory Atlas v1.2 S09 P1 Latent Signals; MA-V12-S09P1; ACC-MA-V12-S09P1; phase_s09_p1_latent_signals_completed_pending_s09_p2; validate:v1.2-s09-p1; latent_signals.json; Evidence Strength Badge; supporting_evidence_refs; contradicting_evidence_refs; alternative_explanation_zh; confidence; next_validation_zh; No GitHub main upload in this phase; No remote push in this phase; No raw mutation; No psychological diagnosis output; No personality label output; No self-iteration suggestions; proposal expiry deferred to S09 P2; decision debt ledger deferred to S09 P3; pending S09 P2.
