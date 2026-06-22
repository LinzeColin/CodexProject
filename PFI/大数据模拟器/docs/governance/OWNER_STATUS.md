# OWNER_STATUS

PFI_BIG_DATA_SIMULATOR 当前治理结论：实现一致性为 `PARTIAL`，交付状态为 `UNVERIFIED`；这不是生产上线声明。

## 1. Current Conclusion

- source_base_commit: `932446fd2154ac477ea0cb6862a60098b1e1ed55`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:b2b976ab6befc216f0344a19176a2a356642c131c48921f075bc0d0637e6daeb`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `3.0.0`
- version: `0.1.0`
- phase/gate: `B / GOV-SEMANTIC-PFI-in-progress`

## 2. This Run Change

Generated owner-facing views now separate implementation congruence from parameter source quality, empirical validation, operational validation, delivery evidence, and evidence freshness.

## 3. Owner Impact

- structural_completeness: `VERIFIED`
- implementation_congruence: `PARTIAL` (211/213 active parameters, 15/15 active formulas)
- parameter_source_quality: `PARTIAL`
- empirical_validation: `UNVERIFIED`
- operational_validation: `FAILED`
- delivery_evidence: `UNVERIFIED`
- evidence_freshness: `PARTIAL`
- delivery_readiness: `UNVERIFIED`

## 4. Decision Needed

- decision_id: `DEC-PFI_BIG_DATA_SIMULATOR-REVIEW6-001`
- question: 是否关闭 PARAM-110/PARAM-111 或保留 human review required。

## 5. A/B/C Choice Matrix

| Decision Item | Current Recommendation | Choice A | Choice B | Choice C | No Decision Consequence |
|---|---|---|---|---|---|
| `DEC-PFI_BIG_DATA_SIMULATOR-REVIEW6-001` | A | A: fund evidence hardening | B: keep blocked/conditional and defer | C: de-scope this project from delivery claims | remains `UNVERIFIED` with unresolved evidence. |

## 6. Current Blockers

1. two implementation parameters need review
2. calibration evidence
3. No third blocker recorded.

## 7. Evidence Required To Unblock

- owner: Codex/governance runner
- unblock_condition: Run the listed test commands and attach evidence.
- acceptance: ACC-SEMANTIC-PFI-001

## 8. Model Formula Parameter Change

- model_count: `15`
- total_formulas: `15`
- active_formulas: `15`
- total_parameters: `213`
- active_parameters: `213`
- active_values_changed_by_this_view: `0`

## 9. Tests And Acceptance

- required_commands: `validate_project_governance --all --semantic --drift-report`; `generate_governance_dashboard --write`
- release_gate: `GOV-SEMANTIC-PFI-in-progress`

## 10. Evidence Freshness

- tree_bound_events: `0`
- commit_bound_events: `0`
- legacy_unbound_events: `3`
- precommit_pending_events: `1`
- pending_or_stale_events: `4`

## 11. UNKNOWN

- unresolved_fact_ids: `14`

## 12. Next Unique Task

- task_id: `GOV-SEMANTIC-PFI-001`
- reason: Add extractors for simulator strategy defaults, risk controls, and active formula fingerprints.
