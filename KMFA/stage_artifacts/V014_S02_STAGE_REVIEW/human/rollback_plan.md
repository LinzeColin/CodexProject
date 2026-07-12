# v0.1.4 Stage 2 Review Rollback Plan

Rollback is public-safe and local-only:

1. Revert `KMFA/stage_artifacts/V014_S02_STAGE_REVIEW/`.
2. Revert `KMFA/tools/check_v014_s02_stage_review.py` and `KMFA/tests/test_v014_s02_stage_review.py`.
3. Revert Stage 2 review rows in governance registries and Chinese project records.
4. Keep `/Users/linzezhang/Downloads/KMFA_MetaData` untouched.

No raw/private data should be moved into or out of Git during rollback.
