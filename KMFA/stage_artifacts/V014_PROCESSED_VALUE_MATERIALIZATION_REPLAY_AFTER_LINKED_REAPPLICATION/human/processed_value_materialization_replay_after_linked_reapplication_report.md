# Linked Materialization Replay

- phase: `V014_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_LINKED_REAPPLICATION`
- status: `completed_validated_local_only_linked_materialization_replay_no_go`
- decision: `NO_GO`
- processed target slots: `149`
- linked materialization input records: `77`
- linked materialized records: `77`
- linked blocked records: `0`
- processed target slots outside linked replay scope: `72`
- linked-scope comparison precheck ready: `true`
- raw-to-processed comparison performed: `false`
- next recommended phase: `V014_LINKED_SCOPE_RAW_TO_PROCESSED_COMPARISON_PRECHECK`

This phase materializes linked-scope private value sources only. Full materialization and raw-to-processed comparison remain separate gates.
