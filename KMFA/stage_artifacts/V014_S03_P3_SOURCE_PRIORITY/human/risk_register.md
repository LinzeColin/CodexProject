# KMFA v0.1.4 S03-P3 Risk Register

| Risk | Control | Status |
|---|---|---|
| Priority policy misread as actual business conflict | Outputs mark policy_fixture_only=true and business_conflict_observed_count=0 | controlled |
| Cross-source queue accidentally auto-selects a source | Validator requires auto_selection_allowed=false and manual_review_required=true | controlled |
| Public evidence exposes raw identifiers | Validator and scans check for raw/private filenames, hashes, field/header plaintext and business values | controlled |
