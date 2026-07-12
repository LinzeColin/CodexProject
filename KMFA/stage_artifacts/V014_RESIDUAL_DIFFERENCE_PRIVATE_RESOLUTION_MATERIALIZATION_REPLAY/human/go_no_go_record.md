# Go/No-Go Record

- decision: `NO_GO`
- reason: private records were materialized for the next comparison gate, but raw-to-processed comparison and business consistency verification were not performed in this phase.
- checks: `10` pass / `0` fail
- next required input: `run_residual_difference_raw_to_processed_comparison_precheck`
