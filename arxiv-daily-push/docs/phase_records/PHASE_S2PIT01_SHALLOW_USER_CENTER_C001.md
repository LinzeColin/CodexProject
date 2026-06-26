# PHASE S2PIT01 SHALLOW USER CENTER C001

- task_id: `S2PIT01-SHALLOW-USER-CENTER-C001`
- parent_task_id: `S2PIT01`
- acceptance_id: `ACC-S2PIT01-USER-CENTER`
- inherited_finding: `C-001`
- phase: `S2PI`
- status: `completed_local_validation_no_closure_no_production`
- generated_at: `2026-06-27T04:55:54+10:00`
- current_contract: `ADP-PRODUCT-CONTRACT-V7.2`

## Scope

This record refreshes inherited P1 finding `C-001` so the S2PIT01 user-center first screen evidence points to the current shallow GitHub owner entry:

- `arxiv-daily-push/用户中心/README.md`
- `arxiv-daily-push/用户中心/一看三查.md`

Historical `docs/owner/00_用户中心/*` pages remain compatibility pointers or internal generated views, not the primary owner-reading surface.

## Current Evidence

- `S2PIT01_REQUIRED_USER_CENTER_PATHS` now requires `用户中心/README.md` and `用户中心/一看三查.md`.
- `build_s2pit01_user_center_report` now blocks missing required user-center paths instead of only displaying them.
- `test_s2pit01_user_center_passes_one_edit_two_click_and_no_production_gates` asserts the shallow paths are required and observed.
- `test_s2pit01_user_center_blocks_duplicate_fact_source_deep_click_and_side_effect` asserts old deep-only paths are insufficient and produce a missing-path blocking reason.
- No-write CLI evidence status: `pass`.
- Required/observed shallow paths: `用户中心/README.md`; `用户中心/一看三查.md`.
- Max click depth: `2`.
- Control domains observed: `budget_schedule`; `mail_review`; `profile`; `source_boards`.
- Report hash: `sha256:d79901a4725fd2d4eb1dbfeaafcede98e5661d8691faddf452f16fbb5ee50fc9`.
- `用户中心/README.md` hash: `sha256:9200146a3616339636f13db7d21ee56ace03790acb187e9c617c5339cc5747ca`.
- `用户中心/一看三查.md` hash: `sha256:54ff3b8df9f91f283ad2b2211108ef5f7c24fb16e8256b6b2c6e847059d3d342`.

## Non-Scope

No source or board change, no SMTP transport, no scheduler, no Release upload, no public schema change, no DB migration, no production queue mutation, no ranking change, no source adapter change, no Email V1 runtime/frontstage change, no CURRENT pointer change, no V7.1/V7.2 contract-file edit, no owner-experience final acceptance, no P0/P1 closure, no S2PLT04 completion, no daily-operation enablement, and no integrated production acceptance was introduced.

## Review Status

This is current local evidence and P1 receipt routing only. It does not close `C-001`; independent S2PMT07 review still controls P1 closure.
