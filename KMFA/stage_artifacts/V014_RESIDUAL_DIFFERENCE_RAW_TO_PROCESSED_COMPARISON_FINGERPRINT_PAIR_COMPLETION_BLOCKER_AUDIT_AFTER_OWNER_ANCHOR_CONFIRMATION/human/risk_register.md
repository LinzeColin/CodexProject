# Risk Register

- Risk: blocker audit is mistaken for raw-to-processed comparison.
- Control: public evidence keeps raw_to_processed_value_comparison_performed=false and business_value_consistency_verified=false.
- Risk: private blocker audit records leak target details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during blocker audit.
- Control: this phase reads existing ignored private pair-completion artifacts only and does not touch the raw inbox.
