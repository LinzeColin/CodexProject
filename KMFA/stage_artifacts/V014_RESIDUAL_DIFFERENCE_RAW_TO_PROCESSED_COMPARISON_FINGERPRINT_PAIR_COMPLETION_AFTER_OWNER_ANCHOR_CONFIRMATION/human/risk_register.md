# Risk Register

- Risk: pair completion is mistaken for raw-to-processed comparison.
- Control: public evidence keeps raw_to_processed_value_comparison_performed=false and business_value_consistency_verified=false.
- Risk: private pair records leak target details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during pair completion.
- Control: this phase reads existing ignored private artifacts only and does not touch the raw inbox.
