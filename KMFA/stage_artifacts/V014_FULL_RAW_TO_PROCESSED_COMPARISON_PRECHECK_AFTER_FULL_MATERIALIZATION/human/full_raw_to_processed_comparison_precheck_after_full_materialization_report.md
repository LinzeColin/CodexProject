# Full Raw-To-Processed Comparison Precheck After Full Materialization

- phase: `V014_FULL_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_FULL_MATERIALIZATION`
- status: `completed_validated_local_only_full_comparison_precheck_blocked_no_go`
- decision: `NO_GO`
- full materialized records: `149`
- candidate catalog records: `366`
- exact fingerprint matches: `77`
- missing candidate records: `72`
- outside-scope missing candidate records: `72`
- full comparison ready: `false`
- full raw-to-processed comparison complete: `false`
- next recommended phase: `V014_OUTSIDE_SCOPE_RAW_CANDIDATE_ALIGNMENT_AFTER_FULL_PRECHECK`

This phase prechecks private fingerprints only. It confirms the 77 linked records remain comparable and identifies 72 outside-scope materialized records without raw-derived candidate records. It does not read the raw inbox and does not complete full raw-to-processed comparison or reconciliation.
