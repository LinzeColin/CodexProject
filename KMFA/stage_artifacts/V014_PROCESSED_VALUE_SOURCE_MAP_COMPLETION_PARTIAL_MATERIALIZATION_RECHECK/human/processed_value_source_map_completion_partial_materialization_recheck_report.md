# V014 Partial Materialization Recheck

Decision: NO_GO

This phase rechecks the private partial value-source fill coverage for the partial application slots. It does not materialize processed values and does not compare raw and processed values.

## Public-safe aggregate result

- Previous awaiting target slots: 101
- Partial materializable target slots: 101
- Partial target slots still awaiting value source: 0
- Partial application blocked target slots: 12
- Partial materialization replay ready: `true`
- Raw-to-processed comparison performed: `false`

Next required input: `run_partial_materialization_replay_or_resolve_non_actionable_group_decisions`.
