# PHASE S2PIT01 USER CENTER

- task_id: `S2PIT01`
- acceptance_id: `ACC-S2PIT01-USER-CENTER`
- phase: `S2PI`
- status: `completed_local_validation_current_shallow_user_center`
- generated_at: `2026-06-25T23:59:40+10:00`
- current_contract: `ADP-PRODUCT-CONTRACT-V7.2`

## Scope

S2PIT01 adds deterministic evidence for the shallow GitHub Chinese `用户中心/README.md` first screen and the one-edit control entry. The owner-facing entry separates four common control domains: profile, mail/review, source/boards, and budget/schedule. Historical `docs/owner/00_用户中心/*` pages may remain as compatibility pointers, but they are not the primary owner-reading entry.

## Acceptance Evidence

- `adp stage2-user-center` builds `stage2_s2pit01_user_center_report.json`.
- The report requires `owner_controls` validation to pass.
- The report requires a read-only SQLite storage inspect report to pass.
- The report requires exactly one editable fact source: `config/owner_controls.yaml`.
- Current required user-center paths are `用户中心/README.md` and `用户中心/一看三查.md`.
- Common controls must be reachable within two clicks from the shallow GitHub user center.
- Every control domain compiles back to `config/owner_controls.yaml`.

## Non-Scope

No SMTP transport, scheduler, Release upload, public schema, DB migration, queue mutation, ranking change, source adapter change, Email V1 frontstage change, V7.1/V7.2 contract-file change, Stage2 production acceptance, owner-experience final acceptance, or integrated production acceptance was introduced.

## Validation

- `py_compile`: PASS
- focused Stage2 source tests: 110 OK
- full ADP unittest: 339 OK
- semantic extractor: 81 formulas / 600 parameters checked
- project governance: 0 errors / 0 warnings
- changed-only governance semantic: 0 errors / 0 warnings
- V7.2 validator: PASS
