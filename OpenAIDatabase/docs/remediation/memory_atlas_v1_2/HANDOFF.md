# Memory Atlas v1.2 Remediation Handoff

## Current Goal

Complete reopened v1.2 remediation R0-R8 with at most one phase per run and one final
GitHub main upload only after R8 passes.

## Current State

- R0: complete; original Roadmap/TaskPack restored with exact historical hashes.
- R1: complete locally; Home Grid blocker and three-viewport browser gate pass.
- R2: complete locally; v1.2 identity, question-led IA, Chinese copy and keyboard
  navigation pass.
- R3: complete locally; six exact Command Palette workflows execute through the fixed
  loopback API; hosted static remains read-only and deep explore is prefill-only.
- R4: complete locally; proposal review, one-use human authorization, real exact apply,
  fixed validation, automatic/manual rollback, persisted rollback after workspace reopen,
  interrupted transaction recovery and raw review-only behavior pass.
- Requirements after R4: `VERIFIED 40 / PARTIAL 11 / FAILED 5 / NOT_VERIFIED 2`.
- Release: `FAIL_REMEDIATION_REQUIRED`.
- GitHub push, app reinstall and Cloudflare deployment: not performed.
- Online website and installed app: still the prior release; do not present them as R0-R4.
- Final fetch moved `origin/main` to `07a6e50d593c7b9c74b8f3870b614be86a87160d`.
  At the R4 security head, local `main` was ahead 12 / behind 12 before closeout records.
  Remote history remains unmerged and must be preserved for R8 reconciliation.

## Key Decisions

- Rendered/runtime evidence is required; source markers and document presence are not
  product acceptance.
- Required browser viewports are `1470x661`, `1440x900` and `390x844`.
- Hosted static remains read-only. Command and proposal execution are local-app only.
- Proposal callers cannot provide target paths, content, argv, environment, validation
  commands or URLs. Apply-ready bundles use fixed roots and validators server-side.
- Proposal target parents must already exist and are opened descriptor-relative with
  no-follow semantics. Raw/private/credential/Git/executable targets remain forbidden.
- Durable rollback must survive workspace reopen and interrupted apply recovery.
- Raw append-only and credential-exclusion boundaries remain unchanged.

## Read First

- `docs/remediation/memory_atlas_v1_2/R4_PROPOSAL_APPROVAL_APPLY_ROLLBACK_WORKFLOW.md`
- `docs/remediation/memory_atlas_v1_2/R3_REAL_COMMAND_PALETTE_WORKFLOWS.md`
- `docs/remediation/memory_atlas_v1_2/R0_SOURCE_RECOVERY_AND_GAP_BASELINE.md`
- `docs/superpowers/plans/2026-07-10-memory-atlas-v1-2-remediation.md`
- `机器治理/证据与日志/remediation/v1_2_r4/status.json`

## Verified Commands

- `python3 -m unittest tests.test_memory_atlas_proposal_apply tests.test_memory_atlas_app_runtime -q`
- `python3 -m unittest tests.test_memory_atlas_launcher -q`
- `python3 -m unittest tests.test_s04p1_chatgpt_sync tests.test_s04p2_codex_agent_sync tests.test_personalization_architecture -q`
- `npm run lint`
- `npm run build`
- `npm run validate:v1.2-proposal-e2e`
- `npm run validate:v1.2-command-workflows`
- `npm run validate:v1.2-home-multiviewport`
- `npm run validate:stage7-visual`
- `python3 scripts/privacy_guard.py --database-dir . --scan-only`

## Remaining Risks

- Owner Daily still lacks a complete product entry and rendered run result path.
- P0 Galaxy/Memory River/filter workflows still need R6 requirement closure.
- Online snapshot still differs from the final local snapshot.
- R4 and the newer browser gates are not yet integrated into the overall final audit.
- GitHub-only clean recovery is not yet proven.
- Final R8 reconciliation must retain both local remediation commits and the incoming
  remote Cloudflare/HomeHub history without force-pushing either side.

## Next Phase

Run only `R5_OWNER_DAILY_PRODUCT_ENTRY`: build and verify the real local Owner Daily UI
entry, step results and actionable fail-closed state. Do not start R6, reconcile Git,
push, reinstall or deploy in the same run.
