# Memory Atlas v1.2 Remediation Handoff

## Current Goal

Complete the reopened v1.2 remediation as R0-R8, with at most one phase per run and
one final GitHub main upload only after R8 passes.

## Current State

- R0: complete; original Roadmap/TaskPack restored with exact historical hashes.
- R1: complete locally; home Grid blocker fixed and three-viewport browser gate passes.
- R2: complete locally; v1.2 identity, question-led navigation, Chinese product copy,
  folded technical details and bidirectional full-geometry keyboard navigation pass.
- Release: `FAIL_REMEDIATION_REQUIRED`.
- GitHub push, app reinstall and Cloudflare deployment: not performed.
- Online website and installed app: still the prior release; do not present them as R0-R2.
- Final fetch moved `origin/main` to `b864009c657c6a9cebbf451e30389c1aa5809700`;
  local `main` is ahead 4 / behind 7. The incoming Cloudflare L2 history is preserved
  and was not merged, rebased or overwritten in R2.

## Key Decisions

- Real rendered/runtime evidence is required; source markers and document presence are
  not product acceptance.
- Automated browser acceptance replaces a blocking manual visual approval.
- Required viewports are `1470x661`, `1440x900` and `390x844`.
- Raw append-only and credential-exclusion boundaries remain unchanged.

## Read First

- `docs/remediation/memory_atlas_v1_2/R0_SOURCE_RECOVERY_AND_GAP_BASELINE.md`
- `docs/remediation/memory_atlas_v1_2/R1_HOME_LAYOUT_AND_MULTIVIEWPORT_GATE.md`
- `docs/remediation/memory_atlas_v1_2/R2_PRODUCT_IDENTITY_AND_INFORMATION_ARCHITECTURE.md`
- `docs/superpowers/plans/2026-07-10-memory-atlas-v1-2-remediation.md`
- `机器治理/证据与日志/remediation/v1_2_r2/status.json`

## Verified Commands

- `python3 -m pytest -q tests/test_memory_atlas_v1_2_home_layout_contract.py tests/test_memory_atlas_visual_acceptance.py`
- `npm run lint`
- `npm run build`
- `npm run validate:v1.2-home-multiviewport`
- `npm run validate:stage7-visual`
- `npm run validate:v1.2-s10-review`
- `npm run validate:v1.2-s11-review`
- `npm run validate:v1.2-s12-p1`

## Remaining Risks

- Command Palette buttons are not executable workflows.
- Proposal approval/apply/rollback and owner-daily lack complete user paths.
- Online snapshot still differs from the final local snapshot.
- The new browser gate is not yet part of the overall final audit.
- GitHub-only clean recovery is not yet proven.
- Final R8 reconciliation must retain both the local remediation commits and the seven
  remote Cloudflare L2 commits, including the HomeHub return-link surface.

## Next Phase

Run only `R3_REAL_COMMAND_PALETTE_WORKFLOWS`: define the allowlisted local command
bridge, keep hosted Pages read-only and verify the six accepted commands end to end.
Do not start R4, push, reinstall or deploy in the same run.
