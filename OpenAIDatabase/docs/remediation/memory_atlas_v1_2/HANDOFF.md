# Memory Atlas v1.2 Remediation Handoff

## Current Goal

Complete the reopened v1.2 remediation as R0-R8, with at most one phase per run and
one final GitHub main upload only after R8 passes.

## Current State

- R0: complete; original Roadmap/TaskPack restored with exact historical hashes.
- R1: complete locally; home Grid blocker fixed and three-viewport browser gate passes.
- R2: complete locally; v1.2 identity, question-led navigation, Chinese product copy,
  folded technical details and bidirectional full-geometry keyboard navigation pass.
- R3: complete locally; all six Command Palette workflows execute through a fixed,
  same-origin loopback API in a temporary installer-shaped runtime. Static hosting
  emits no command POST, and deep explore remains prefill-only with no auto-submit.
- Release: `FAIL_REMEDIATION_REQUIRED`.
- GitHub push, app reinstall and Cloudflare deployment: not performed.
- Online website and installed app: still the prior release; do not present them as R0-R3.
- Final fetch moved `origin/main` to `bd06ee38c1b8c52bcafd68b3c3b0a752a53cae62`.
  At the R3 implementation head local `main` was ahead 6 / behind 10; the closeout
  records add one local commit. The incoming ten-commit Cloudflare L2 history is
  preserved and was not merged, rebased or overwritten.

## Key Decisions

- Real rendered/runtime evidence is required; source markers and document presence are
  not product acceptance.
- Automated browser acceptance replaces a blocking manual visual approval.
- Required viewports are `1470x661`, `1440x900` and `390x844`.
- Hosted static builds remain read-only; command execution is local-app only.
- The local command endpoint accepts one exact allowlisted command ID, never a caller
  supplied path, flag, environment variable, URL or shell fragment.
- Raw append-only and credential-exclusion boundaries remain unchanged.

## Read First

- `docs/remediation/memory_atlas_v1_2/R0_SOURCE_RECOVERY_AND_GAP_BASELINE.md`
- `docs/remediation/memory_atlas_v1_2/R1_HOME_LAYOUT_AND_MULTIVIEWPORT_GATE.md`
- `docs/remediation/memory_atlas_v1_2/R2_PRODUCT_IDENTITY_AND_INFORMATION_ARCHITECTURE.md`
- `docs/remediation/memory_atlas_v1_2/R3_REAL_COMMAND_PALETTE_WORKFLOWS.md`
- `docs/superpowers/plans/2026-07-10-memory-atlas-v1-2-remediation.md`
- `机器治理/证据与日志/remediation/v1_2_r3/status.json`

## Verified Commands

- `python3 -m unittest tests.test_memory_atlas_app_runtime tests.test_memory_atlas_launcher tests.test_s04p1_chatgpt_sync tests.test_s04p2_codex_agent_sync tests.test_personalization_architecture -q`
- `npm run lint`
- `npm run build`
- `npm run validate:v1.2-command-workflows`
- `npm run validate:v1.2-home-multiviewport`
- `npm run validate:stage7-visual`
- `python3 scripts/privacy_guard.py --database-dir . --scan-only`

## Remaining Risks

- Proposal approval/apply/rollback and owner-daily lack complete user paths.
- Online snapshot still differs from the final local snapshot.
- The new browser gate is not yet part of the overall final audit.
- GitHub-only clean recovery is not yet proven.
- A future trusted command child that deliberately creates a new session could escape
  the current process-group timeout; the current fixed allowlist does not do so.
- Final R8 reconciliation must retain both the local remediation commits and the ten
  remote Cloudflare L2 commits, including the HomeHub return-link surface and updated
  deployment-evidence semantics.

## Next Phase

Run only `R4_PROPOSAL_APPROVAL_APPLY_ROLLBACK_WORKFLOW`: build and verify the real
human approval, apply, validation and rollback user path. Do not start R5, reconcile
Git, push, reinstall or deploy in the same run.
