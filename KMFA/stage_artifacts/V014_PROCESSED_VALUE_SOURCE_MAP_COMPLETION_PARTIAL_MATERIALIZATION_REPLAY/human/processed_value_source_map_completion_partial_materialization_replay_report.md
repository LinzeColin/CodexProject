# V014 Partial Materialization Replay

Decision: NO_GO

This phase performs a private partial materialization replay for slots that passed the previous private recheck. It does not compare raw and processed values, and it does not read the raw inbox.

## Public-safe aggregate result

- Partial materialized target slots: 101
- Partial unmaterialized target slots: 0
- Partial application blocked target slots: 12
- Partial raw-to-processed comparison ready: `true`
- Raw-to-processed comparison performed: `false`
- GitHub upload performed: `false`

Next required input: `run_partial_raw_to_processed_value_comparison_or_resolve_non_actionable_group_decisions`.
