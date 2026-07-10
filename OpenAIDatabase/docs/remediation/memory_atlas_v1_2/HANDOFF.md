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
- R5: complete locally; Owner Daily has a real product entry, shared eight-step no-write
  runner, exact loopback API, human-first result workspace and failed-step-only retry.
- R6: complete locally; the exact twelve P0 visuals use one redacted 217-event snapshot,
  literal source/time/project/task filtering, keyboard evidence drill-down, filtered
  opportunity detail and bounded no-write Formula what-if controls.
- Requirements after R6: `VERIFIED 48 / PARTIAL 5 / FAILED 4 / NOT_VERIFIED 1`.
- Release: `FAIL_REMEDIATION_REQUIRED`.
- GitHub push, app reinstall and Cloudflare deployment: not performed.
- Online website and installed app: still the prior release; do not present them as R0-R6.
- Final fetch moved `origin/main` to `07a6e50d593c7b9c74b8f3870b614be86a87160d`.
  At the R6 implementation/review head, local `main` was ahead 33 / behind 12 before
  closeout records.
  Remote history remains unmerged and must be preserved for R8 reconciliation.

## Key Decisions

- Rendered/runtime evidence is required; source markers and document presence are not
  product acceptance.
- Required browser viewports are `1470x661`, `1440x900` and `390x844`.
- R6 acceptance owns exactly twelve P0 visual IDs. All use the same literal
  source/time/project/task state and a shared evidence workspace; source markers are
  regression evidence only.
- Public visual facets are bounded derived metadata only. Formula what-if is local
  no-write proxy comparison, not an income prediction or financial advice.
- Hosted static remains read-only. Command and proposal execution are local-app only.
- Owner Daily is also local-app only. It is not a seventh R3 command and cannot accept
  browser-supplied argv, paths, environment or execution mode.
- The exact eight Owner Daily step IDs, order and dry-run argv are server-side. Runs
  continue after failure and retry only the exact failed allowlisted step.
- Mutating loopback endpoints require an exact Host/Origin spelling match; child results
  fail closed on unsafe `true` fields at arbitrary nested depth.
- Proposal callers cannot provide target paths, content, argv, environment, validation
  commands or URLs. Apply-ready bundles use fixed roots and validators server-side.
- Proposal target parents must already exist and are opened descriptor-relative with
  no-follow semantics. Raw/private/credential/Git/executable targets remain forbidden.
- Durable rollback must survive workspace reopen and interrupted apply recovery.
- Raw append-only and credential-exclusion boundaries remain unchanged.

## Read First

- `docs/remediation/memory_atlas_v1_2/R6_P0_VISUALIZATION_AND_FILTERING.md`
- `docs/remediation/memory_atlas_v1_2/R5_OWNER_DAILY_PRODUCT_ENTRY.md`
- `docs/remediation/memory_atlas_v1_2/R4_PROPOSAL_APPROVAL_APPLY_ROLLBACK_WORKFLOW.md`
- `docs/remediation/memory_atlas_v1_2/R3_REAL_COMMAND_PALETTE_WORKFLOWS.md`
- `docs/remediation/memory_atlas_v1_2/R0_SOURCE_RECOVERY_AND_GAP_BASELINE.md`
- `docs/superpowers/plans/2026-07-10-memory-atlas-v1-2-remediation.md`
- `机器治理/证据与日志/remediation/v1_2_r6/status.json`

## Verified Commands

- `python3 -m unittest tests.test_memory_atlas_owner_daily tests.test_memory_atlas_app_runtime tests.test_s04p3_github_backup tests.test_memory_atlas_proposal_apply tests.test_memory_atlas_launcher tests.test_s04p1_chatgpt_sync tests.test_s04p2_codex_agent_sync tests.test_personalization_architecture -q`
- `python3 -m unittest tests.test_memory_atlas_visual_workflows tests.test_memory_atlas_data -q`
- `npm run lint`
- `npm run build`
- `npm run validate:v1.2-visual-models`
- `npm run validate:v1.2-visual-workflows`
- `npm run validate:v1.2-s14-p1`
- `npm run validate:v1.2-owner-daily-e2e`
- `npm run validate:v1.2-proposal-e2e`
- `npm run validate:v1.2-command-workflows`
- `npm run validate:v1.2-home-multiviewport`
- `npm run validate:stage7-visual`
- `python3 scripts/privacy_guard.py --database-dir . --scan-only`

## Remaining Risks

- Online snapshot still differs from the final local snapshot.
- Raw/archive proof is still empty or incomplete for recovery purposes.
- R4, R5, R6 and the newer browser gates are not yet integrated into the overall final audit.
- GitHub-only clean recovery is not yet proven.
- Final R8 reconciliation must retain both local remediation commits and the incoming
  remote Cloudflare/HomeHub history without force-pushing either side.

## Next Phase

Run only `R7_DATA_PARITY_RAW_EVIDENCE_AND_RECOVERY`: build one immutable release
snapshot, prove local/Pages candidate parity, materialize authorized recovery evidence
without credentials and rehearse GitHub-only recovery in a clean temporary directory.
Do not start R8, reconcile Git, push, reinstall or deploy in the same run.
