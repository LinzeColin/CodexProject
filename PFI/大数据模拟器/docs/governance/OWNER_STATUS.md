# OWNER_STATUS

## 1. 当前结论

PFI_BIG_DATA_SIMULATOR 当前治理结论：实现一致性为 `PARTIAL`，方法/实证为 `UNVERIFIED` / `UNVERIFIED`，交付状态为 `UNVERIFIED`；这不是生产上线声明。

## 2. 本次运行改变了什么

Owner 视图现在把实现一致性、参数来源、方法依据、实证验证、运行验证、交付证据和证据新鲜度分开，避免把 `MACHINE_VERIFIED` 误读为模型有效或可上线。

## 3. 为什么重要

区分真实稳健表现与大规模搜索偏差。

## 4. 需要人类决定什么

- decision_id: `DEC-PFI_BIG_DATA_SIMULATOR-REVIEW8-001`
- decision_question: 是否投入多市场、OOS、成本和多重检验控制，验证 PFI 策略族不是数据挖掘赢家。
- human_owner_role: `model_owner + risk_owner + research_owner`
- human_assignment_status: `HUMAN_ASSIGNMENT_REQUIRED`

## 5. 默认建议

- current_recommendation: A: validate OOS and multiple-testing controls before ranking strategy claims
- estimated_effort: P1; model/risk/research owner review
- estimated_cost_or_resource: multi-market snapshots, compute time, multiple-testing protocol

## 6. 不决策后果

PFI remains UNVERIFIED and cannot support strategy approval.

## 7. 下一行动、责任角色和验收证据

- next_task_id: `TASK-PFI-B-001`
- responsible_role: `model_owner + risk_owner + research_owner`
- acceptance_ids: `ACC-PFI-B-001`
- unblock_condition: Heuristic constants and historical run claims may lack direct calibration/source evidence; unresolved items remain blocked tasks.

## 8. 九层 Assurance 状态

- structural_completeness: `VERIFIED`
- implementation_congruence: `PARTIAL` (211/213 active parameters, 15/15 active formulas)
- parameter_source_quality: `PARTIAL`
- methodological_rationale: `UNVERIFIED`
- empirical_validation: `UNVERIFIED`
- operational_validation: `FAILED`
- delivery_evidence: `UNVERIFIED`
- evidence_freshness: `PARTIAL`
- delivery_readiness: `UNVERIFIED`

## 9. A/B/C Choice Matrix

| Decision Item | Current Recommendation | Choice A | Choice B | Choice C | No Decision Consequence |
|---|---|---|---|---|---|
| `DEC-PFI_BIG_DATA_SIMULATOR-REVIEW8-001` | A: validate OOS and multiple-testing controls before ranking strategy claims | 执行预注册、walk-forward、FDR/Reality Check、快筛-精确一致性和成本压力。 | 保持模拟研究，不提升策略有效性状态。 | 暂停策略族交付声称。 | PFI remains UNVERIFIED and cannot support strategy approval. |

## 10. Current Blockers

1. two implementation parameters need review
2. calibration evidence
3. model_owner + risk_owner + research_owner must provide project-specific evidence before readiness can improve.

## 11. Evidence Required To Unblock

- evidence_required: pre-registration, OOS metrics, corrected significance, sensitivity results
- principal_risks: data mining, survivor bias, underestimated costs, resource blowups
- generated_from_refs: `PFI/大数据模拟器/docs/governance/ASSURANCE_STATUS.yaml, PFI/大数据模拟器/docs/governance/delivery_tasks.yaml`

## 12. Model Formula Parameter Change

- model_count: `15`
- total_formulas: `15`
- active_formulas: `15`
- total_parameters: `213`
- active_parameters: `213`
- active_values_changed_by_this_view: `0`

## 13. Tests And Acceptance

- required_commands: `validate_project_governance --all --semantic --drift-report`; `generate_governance_dashboard --write`
- release_gate: `GOV-SEMANTIC-PFI-in-progress`

## 14. Evidence Freshness

- final_commit_binding: `CI_ATTESTED:governance/run_manifests/GOV-REVIEW6-FINAL-PORTFOLIO-001.json`
- tree_bound_events: `0`
- commit_bound_events: `1`
- legacy_unbound_events: `3`
- precommit_pending_events: `0`
- pending_or_stale_events: `4`

## 15. UNKNOWN

- unresolved_fact_ids: `14`

## 16. 技术元数据

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:fd24bf9f219db8c72deda2fece6e6f0244793d018f41cda88688bfd3cf8bfbe5`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `4.0.0`
- version: `0.1.0`
- phase/gate: `B / GOV-SEMANTIC-PFI-in-progress`

## 17. Next Unique Task

- task_id: `TASK-PFI-B-001`
- reason: Resolve calibration evidence for strategy catalog rule constants and indicator thresholds.
