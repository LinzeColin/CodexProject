# Changelog

## 2026-06-29 09:09:03 Australia/Sydney - S2PMT07-S2PLT04-COMPLETION-REPORT-DEPENDENCY-ORDER

- Fixed the S2PLT04 completion report validator/template ordering so the report no longer requires later final-bundle manifest evidence (`FINAL_BUNDLE_MANIFEST` / `FINAL_ACCEPTANCE_BUNDLE_PRESENT`) as a prerequisite.
- The real `FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json` is still missing and S2PLT01/S2PLT02/S2PLT03 terminal acceptance is still not proven by this change.
- S2PLT04 completion report, final command execution, handoff, signoff, final manifest, P0/P1 top-level closure, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, and integrated production acceptance remain blocked or false.

## 2026-06-29 08:46:12 Australia/Sydney - S2PMT07-CLI-MODULE-ENTRYPOINT

- Added the missing `__main__` module entrypoint so `python3 -B -m arxiv_daily_push.cli plan-final-bundle-prerequisites --json` dispatches to the same CLI path as direct `main([...])` calls.
- The module command now returns blocked JSON with `next_required_step=S2PLT04_COMPLETION_REPORT` and exit code `2`; this is a proof-chain executability fix only.
- S2PLT04 completion report, final command execution, handoff, signoff, final manifest, P0/P1 top-level closure, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, and integrated production acceptance remain blocked or false.

## 2026-06-29 00:40:23 Australia/Sydney - S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-DRAFT-CLI

- Added `build-final-reviewer-assignment-artifact-draft` CLI to produce a stdout-only, ordered JSON draft for the future independent final reviewer assignment artifact from explicit owner/coordinator inputs.
- The draft command computes `assignment_hash=sha256:1b31de0eae2283814fa5e458d69700774f2ae8441187a3e8f0fd3a03740c2dec` and validates with no errors, but writes no live artifact, assigns no reviewer, satisfies no assignment gate, closes no P0/P1 findings, completes no S2PLT04 step, executes no final commands, and accepts no production.
- SMTP, scheduler, Release, restore, public schema, DB migration, production queue, source adapter, ranking, CURRENT/V7, V7.1 baseline, V7.2 contract, DAILY_OPERATION, and integrated production acceptance remain unchanged.

## 2026-06-29 00:14:34 Australia/Sydney - S2PMT07-FINAL-BUNDLE-PREREQUISITE-PLAN-CLI

- Expose `adp plan-final-bundle-prerequisites --json` as a blocked, no-production S2PMT07 prerequisite plan CLI.
- The plan consumes committed `FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json` as `NO_PRODUCTION_SIDE_EFFECT_ATTESTATION=pass` while keeping reviewer assignment, P0/P1 zero proof, S2PLT04 report, final command execution, handoff, signoff, manifest, final bundle, P0/P1 closure, and production acceptance blocked.
- 2026-06-28 23:58:57 Australia/Sydney: Added remaining S2PMT07 final-bundle artifact CLI validators for manifest, S2PLT04 completion report, no-production attestation, and next-agent handoff; manifest/report/handoff remain blocked when missing, committed no-production attestation validates pass, and no final-bundle artifact, P0/P1 closure, S2PLT04 completion, SMTP, scheduler, Release, restore, DAILY_OPERATION, or integrated production acceptance is claimed.
- 2026-06-28 23:41:05 Australia/Sydney: Added `validate-final-command-execution` CLI validation for future `FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json`; missing artifact returns blocked/exit 2 with `final_command_execution_missing`, and final command execution, reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 23:23:48 Australia/Sydney: Added `validate-p0-p1-zero-proof` CLI validation for future `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json`; missing artifact returns blocked/exit 2 with `p0_p1_zero_proof_artifact_missing`, and P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 23:04:29 Australia/Sydney: Added `build-final-closure-decision-owner-packet` CLI output for the existing S2PMT07 independent final closure decision owner/reviewer packet; the command exposes the future closure-decision artifact ref and required owner actions while reviewer assignment, closure decision, P0/P1 zero proof, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 22:44:37 Australia/Sydney: Added `validate-final-acceptance-bundle` CLI readiness precheck for S2PMT07 final acceptance bundle artifacts; command returns blocked/exit 2 with missing real artifact list while `FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json` remains recognized as present, and reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 22:23:15 Australia/Sydney: Hardened all S2PMT07 final-bundle artifact validators with recursive template placeholder rejection, so copied template values containing `REPLACE_WITH` or `RECOMPUTE_WITH` cannot pass even if the relevant artifact hash is recomputed; the real assignment artifact, reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 22:03:08 Australia/Sydney: Hardened S2PMT07 independent final reviewer assignment artifact validation so copied template placeholders such as `REPLACE_WITH_REAL_TIMESTAMP_AUSTRALIA_SYDNEY` and `REPLACE_WITH_REAL_INDEPENDENT_REVIEWER_ID` are rejected even if `assignment_hash` is recomputed; the real assignment artifact, reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 21:37:18 Australia/Sydney: Added `build-final-reviewer-assignment-owner-packet` CLI output for the existing S2PMT07 independent final reviewer assignment owner/coordinator packet; the command exposes required owner actions and review refs while assignment artifact, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 21:07:59 Australia/Sydney: Added `validate-final-reviewer-assignment` CLI validation for future `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json`; missing artifact returns blocked, valid temporary artifact can pass schema/hash/no-production checks, and reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 20:43:00 Australia/Sydney: Promoted `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` into the formal S2PMT07 final bundle required item list and directory-level artifact validation keys; the real assignment artifact remains missing, so final bundle, P0/P1 closure, S2PLT04, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 20:10:59 Australia/Sydney: Hardened S2PMT07 final bundle readiness so `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` validation is a hard prerequisite for top-level final bundle readiness even when directory-level final bundle artifact validation passes; the assignment artifact remains missing, and reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 19:40:00 Australia/Sydney: Wired S2PMT07 final bundle readiness to consume a future `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` artifact; the current artifact remains missing, and reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 19:05:22 Australia/Sydney: Added template-only S2PMT07 final bundle artifact skeletons under `FINAL_ACCEPTANCE_BUNDLE/templates/`; these templates do not satisfy readiness, and manifest, P0/P1 zero proof, S2PLT04 completion report, independent signoff, final command execution, next-agent handoff, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 17:32:43 Australia/Sydney: Synced S2PMT07 final bundle readiness with the committed no-production side-effect attestation artifact; readiness now consumes `FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json` while final bundle manifest, P0/P1 zero proof, S2PLT04 completion, independent signoff, final command execution, next-agent handoff, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 16:32:45 Australia/Sydney: Added S2PMT07 local runtime no-production gate; local ADP daily/health/watchdog LaunchAgents are disabled/not running and `ADP_ALLOW_SMTP_SEND=false`, while no SMTP, scheduler, Release, restore, P0/P1 closure, S2PLT04 completion, final bundle, DAILY_OPERATION, or integrated production acceptance is claimed.
- 2026-06-28 16:01:08 Australia/Sydney: Restored A-005 trust-boundary parameter selector coverage for `PARAM-ADP-955..959`; implementation congruence now verifies 1050/1050 active parameters while S2PMT07 independent final reviewer assignment, P0/P1 zero proof, S2PLT04, final bundle, and all production gates remain blocked.
- 2026-06-28 15:26:22 Australia/Sydney: Added S2PMT07 independent final closure decision owner/reviewer packet; it exposes required owner/reviewer actions, zero-proof decision location, assignment prerequisite, review refs, and no-production flags while the actual reviewer assignment, closure decision, P0/P1 zero proof, final bundle, S2PLT04, and all production gates remain blocked.
- 2026-06-28 14:11:24 Australia/Sydney: Added S2PMT07 remaining blocker matrix; current seven final-gate blockers are mapped to required future evidence and owner actions while P0/P1 closure, S2PLT04, final bundle, SMTP/scheduler/Release/restore, CURRENT/V7, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 13:12:48 Australia/Sydney: Added S2PLT02 explicit M4 watermark proof validator; current service date 2026-06-28 remains blocked because no explicit proof record exists, while S2PLT02 acceptance and all production gates remain false.
- 2026-06-28 12:47:11 Australia/Sydney: Added S2PLT02 delivery evidence ledger over committed M1-M4 real-delivery manifests; current state remains partial at 1/2 natural days and 4/8 emails with duplicate counts zero, while S2PLT02 acceptance and all production gates remain blocked.
- 2026-06-28 10:26:53 Australia/Sydney: Added local daily M1-M4 send orchestration; runner now builds four Email V1 products, records per-product SMTP evidence, syncs actual sent count to user center, and skips already-sent same-day products during catch-up.
- 2026-06-28 11:28:25 Australia/Sydney: Recorded real 2026-06-28 M1-M4 resend execution evidence; M1 was treated as historical sent and M2-M4 were sent by SMTP, updating GitHub user center to 4 / 4 without claiming Stage 2 production acceptance.
- 2026-06-28 10:08:17 Australia/Sydney: Added S2PMT07 mainline attestation state; target S2PMT07 evidence commit is contained in origin/main with open PR count 0 and ADP/arxiv/s2p remote branch count 0, while P0/P1 closure, final bundle, S2PLT04, and all production gates remain blocked.
- 2026-06-28 08:48:03 Australia/Sydney: Added S2PMT07 independent final reviewer assignment request state; reviewer assignment, closure decision, zero-proof artifact, P0/P1 closure, S2PLT04, final bundle, and production gates remain blocked.
- 2026-06-28 08:21:10 Australia/Sydney: Added S2PMT07 independent final closure decision request state; reviewer assignment, closure decision, zero-proof artifact, P0/P1 closure, S2PLT04, final bundle, and production gates remain blocked.
- 2026-06-28 07:56:58 Australia/Sydney: Added S2PMT07 P0/P1 zero-proof assembly state; candidate inputs are visible but independent final closure decision, zero-proof artifact, P0/P1 closure, S2PLT04, final bundle, and production gates remain blocked.
- 2026-06-28 07:41:22 Australia/Sydney: Added S2PMT07 final bundle prerequisite plan; current final bundle artifacts remain missing and no production gates changed.
- 2026-06-28 07:13:17 Australia/Sydney: Added S2PMT07 next-agent handoff artifact validator; current handoff remains missing and no production gates changed.
- 2026-06-28 06:48:44 Australia/Sydney: Added S2PMT07 no-production side-effect attestation artifact validator; current attestation remains missing and no production gates changed.
- 2026-06-28 06:18:50 Australia/Sydney: Added S2PMT07 independent review signoff artifact validator; current signoff remains missing and no production gates changed.
- 2026-06-28 05:57:25 Australia/Sydney: Added S2PMT07 final command execution artifact validator; current artifact remains missing and no production gates changed.
- Added `S2PMT07-FINAL-BUNDLE-MANIFEST-VALIDATOR` so any future `FINAL_ACCEPTANCE_BUNDLE/manifest.json` must pass strict schema version, exact manifest decision, bundle item hashes, artifact validation statuses, closure-state proof, no-production flags, and manifest-hash validation; current state remains blocked with the manifest and final bundle missing, inherited P0=8/P1=37, no S2PLT04 completion, no SMTP/scheduler/Release/restore, no schema/DB/queue/source/ranking/CURRENT/V7 changes, no P0/P1 closure, and no integrated production acceptance.
- Added `S2PMT07-P0-P1-ZERO-PROOF-VALIDATOR` so any future `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` must pass strict schema version, candidate evidence refs, zero P0/P1 counts, final bundle refs, no-production flags, and decision-hash validation; current state remains blocked with the artifact missing, inherited P0=8/P1=37, no final bundle, no S2PLT04 completion, no SMTP/scheduler/Release/restore, no schema/DB/queue/source/ranking/CURRENT/V7 changes, no P0/P1 closure, and no integrated production acceptance.
- Added `S2PMT07-P0-P1-ZERO-PROOF-READINESS` so future P0/P1 closure must provide `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` with required fields, independent final closure decision, zero open P0/P1 counts, and no-production attestation; current state remains blocked with the artifact missing, inherited P0=8/P1=37, no final bundle, no S2PLT04 completion, no SMTP/scheduler/Release/restore, no schema/DB/queue/source/ranking/CURRENT/V7 changes, no P0/P1 closure, and no integrated production acceptance.
- Added `S2PMT07-P0-P1-TECHNICAL-CANDIDATE-READINESS` so existing 8 P0 and 37 P1 finding-level technical closure candidates are visible to S2PMT07 final acceptance bundle readiness as prebundle evidence only; this does not create P0/P1 zero proof, close inherited P0/P1, complete S2PLT04, create the final bundle, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Synced `S2PLT04-FINAL-BUNDLE-READINESS-SYNC` so the S2PLT04 integration-candidate precheck now embeds final acceptance bundle readiness detail and required missing items; this does not create the final acceptance bundle, complete S2PLT04, close P0/P1, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Synced `S2PLT04-STATE-CONTENT-EVIDENCE-BUNDLE-SYNC` so the S2PLT04 integration-candidate precheck now binds local state-consistency and content evidence to deterministic no-production bundles with source tasks, evidence refs, and hashes; this does not complete S2PLT04, create the final acceptance bundle, close P0/P1, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Synced `S2PLT04-S2PLT01-REPLAY-REVIEW-EVIDENCE-SYNC` so the S2PLT04 integration-candidate precheck now consumes the existing S2PLT01 independent replay review receipt as non-terminal local evidence; this does not satisfy S2PLT01 authoritative acceptance, complete S2PLT04, create the final acceptance bundle, close P0/P1, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Synced `S2PLT04-S2PLT02-PRECHECK-EVIDENCE-SYNC` so the S2PLT04 integration-candidate precheck now consumes the existing S2PLT02 live two-day readiness precheck as non-terminal local evidence; this does not satisfy S2PLT02 authoritative completion, prove the real two-day run, complete S2PLT04, create the final acceptance bundle, close P0/P1, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Synced `S2PLT04-LOCAL-DRILL-EVIDENCE-SYNC` so the S2PLT04 integration-candidate precheck now consumes the existing S2PLT03 local no-production resilience drill bundle as non-terminal local evidence; this does not satisfy S2PLT03 authoritative completion, complete S2PLT04, create the final acceptance bundle, close P0/P1, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Recorded `S2PLT03` as a deterministic fail-closed resilience, capacity, rollback, and state-count precheck with explicit blockers for missing S2PLT02 acceptance, missing rate-limit/parser-drift/restart/disk drills, missing backup restore-point, missing executable rollback, missing ledger count conservation, and inherited P0/P1 open findings; this does not accept S2PLT03, run live drills, execute production restore, send SMTP, enable scheduler, upload Release, mutate schema/DB/queues, change source adapters/ranking/CURRENT/V7 contracts, close P0/P1, enable daily operation, or claim integrated production acceptance.
- Synced `S2PLT01-REPLAY-REVIEW-STATUS-SYNC` so current replay-chain records recognize the existing local no-production S2PLT01 replay payload execution and independent replay review receipts, while leaving S2PLT01 acceptance, S2PLT04, S2PMT07, P0/P1 closure, SMTP, scheduler, Release, CURRENT/V7 contracts, daily operation, and integrated production acceptance blocked.
- Recorded `S2PMT07-P1-C002-TECHNICAL-REVIEW` with verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making C-002 owner-status runtime-state evidence a finding-level technical closure candidate after empty/delayed/failed states were added to the S2PIT02 gate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW` with verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making B-008 fake SMTP crash-window evidence a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW` with verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making B-007 multiprocess race evidence a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW` with verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making A-005 trust-boundary evidence a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW` with verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making A-004 typed frontstage evidence a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.

- Added `S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE` so the B-008 P0 receipt now includes a local fake SMTP accept-after-kill runner-boundary proof with restart reconciliation blocked without `provider_accept_ref`, durable fake provider ref finalization to `SENT`, stable `mail_key`/`message_id`, no duplicate resend, and no real SMTP side effects; this is evidence routing only and leaves independent signoff, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE` so the B-007 P0 receipt now includes a local multiprocess runner-boundary proof with 4 worker processes, 400 observed M1-M4 attempts, 4 active revisions, 396 blocked duplicates, and all worker exit codes equal to zero; this is evidence routing only and leaves independent signoff, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Fixed A-003 transactional outbox retry safety so `ACCEPTED_PENDING_COMMIT` cannot be claimed before provider reconciliation and `BLOCKED`/`SENT` rows with `retry_safe=false` cannot be reclaimed after lease expiry; recorded `S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW` with reviewer verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making A-003 a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW` with a read-only reviewer verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making A-002 a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, production restore, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW` with a read-only reviewer verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making A-001 a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, production restore, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW` with a read-only reviewer verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making B-001 a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded B-001 isolated launchd proof reconciliation in GitHub evidence surfaces so the previous missing isolated install-run-uninstall proof is now reviewable by S2PMT07 independent review; P0/P1 counters, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance remain unchanged.
## Unreleased - 2026-06-24

- Added `S2PMT04-INSTALL-LIFECYCLE-B001` dedicated local evidence and refreshed `S2PMT07-P0-REVIEW-RECEIPT-REFRESH-B001` so P0 receipt row B-001 points to controlled install/status/trigger-probe/uninstall lifecycle proof instead of older aggregate lifecycle/cache evidence; the real isolated install-run-uninstall proof remains missing and blocked, and this leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, launchd bootstrap, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT03-OUTBOX-DELIVERY-A003` dedicated local evidence and refreshed `S2PMT07-P0-REVIEW-RECEIPT-REFRESH-A003` so P0 receipt row A-003 points to transactional outbox Message-ID stability, changed-revision rekeying, 100-claim contention, SMTP accepted-before-commit fail-closed handling, provider-ref finalization, and at-least-once/no-exactly-once proof instead of aggregate lease-fencing evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002` dedicated local evidence and refreshed `S2PMT07-P0-REVIEW-RECEIPT-REFRESH-A002` so P0 receipt row A-002 points to real Stage 1 backup/restore probes for new-target restore, overwrite restore with previous-target backup preservation, invalid overwrite target preservation, and temporary-file cleanup instead of aggregate atomic recovery evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, production restore, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT02-RESTORE-PATH-SAFETY-A001` dedicated local evidence and refreshed `S2PMT07-P0-REVIEW-RECEIPT-REFRESH-A001` so P0 receipt row A-001 points to real Stage 1 restore probes for relative path traversal, absolute path escape, symlink escape, and invalid overwrite target preservation instead of aggregate atomic recovery evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, production restore, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PAT05-TRACEABILITY-CHAIN-C010` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C010` so P1 receipt row C-010 points to a 247-row clickable feature/task/test/run-evidence chain in the shallow GitHub user center instead of aggregate traceability surfaces; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PIT05-FOUR-CHECK-FRESHNESS-C003` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C003` so P1 receipt row C-003 points to four-check freshness, fact-source, drift-state, CI alarm, and page alarm proof instead of aggregate owner UX evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT06-SAFE-MANUAL-ACTION-C012` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C012` so P1 receipt row C-012 points to safe retry/cancel/requeue/skip/regenerate action proof instead of aggregate owner UX evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PIT02-OWNER-STATUS-C002` dedicated shallow GitHub mail/queue status evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C002` so P1 receipt row C-002 points to owner-visible `2 / 4` mail count, `299 = 30 + 269` candidate-pool conservation, sent/blocked/queued state coverage, and explicit `pending_daily_snapshot` review/action/asset/ROI fields instead of older deep owner-doc runtime dashboard evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PIT01-SHALLOW-USER-CENTER-C001` dedicated shallow GitHub user-center evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C001` so P1 receipt row C-001 points to `用户中心/README.md` and `用户中心/一看三查.md` path-gate proof instead of older deep owner-doc evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT04-PROCESS-LIFECYCLE-B002` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-B002` so P1 receipt row B-002 points to process-lifecycle SIGTERM/SIGINT matrix proof instead of older aggregate lifecycle/cache evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT01-ZERO-CRITICAL-CLAIM-A019` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-A019` so P1 receipt row A-019 points to the Stage 1 B1 zero-critical-claim gate proof instead of older aggregate security-boundary evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-FUTURE-HEARTBEAT-A015` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-A015` so P1 receipt row A-015 points to the future-heartbeat/DST/clock-skew phase record and manifest instead of the older aggregate S2PMT05 stress-E2E surface; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-A010-A016` so P1 receipt rows A-010, A-011, A-013, A-014, and A-016 point to their dedicated artifact atomic-publish, artifact SHA-256, scheduler-template, supporting-file-collision, and lesson-revision evidence records instead of older aggregate S2PMT02/S2PMT03/S2PMT04 surfaces; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-A006-A009` so P1 receipt rows A-006 through A-009 point to their dedicated S2PMT03 runtime-lock, state-history, state-consistency, and optimistic-fencing phase records/manifests instead of the older aggregate `S2PMT03_LEASE_FENCING` evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH` so 16 P1 independent-review receipt rows point to their dedicated current phase records and run manifests, including corrected B-013 routing to `S2PMT05-RESULT-VALIDITY-B013`; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Synced `S2PMT07-FINAL-COMMAND-BLOCKER-SYNC` so the S2PMT07 fail-closed machine report, phase record, manifest, semantic parameters, and regression tests explicitly include `independent_final_command_execution_missing`; this aligns machine blockers with the V7.2/formula contract while keeping independent signoff, P0/P1 closure, S2PLT04, final bundle creation, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Refreshed `S2PMT07-P0-REVIEW-RECEIPT-REFRESH-B007-B008` so the P0 independent-review receipt points B-007 and B-008 to their dedicated 20260627 phase records and run manifests instead of the older S2PMT05 stress-E2E summary; added a final-gate regression test while keeping independent signoff, P0/P1 closure, S2PLT04, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-SMTP-CRASH-WINDOW-B008` local SMTP accepted-before-local-commit crash-window evidence so S2PMT05 now requires outbox claim before SMTP acceptance, explicit `ACCEPTED_PENDING_COMMIT`, stable idempotent `message_id`, blocked resend without durable provider accept ref, local finalization with `smtp-accept://...` provider ref, and no real SMTP side effects while keeping SMTP production enablement, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-DUPLICATE-TRIGGER-B007` local duplicate-trigger race evidence so S2PMT05 now requires github_schedule/local_launchd/manual_retry/restart_catchup actor coverage, M1-M4 x 100 repeated trigger attempts, `mail_key`/`lease_owner`/`fencing_token` receipts, exactly one active revision per product, reason-coded `MAIL_KEY_ALREADY_CLAIMED` blocked attempts, and no scheduler side effects while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-TIME-POLICY-B010` local structured time-policy evidence so S2PMT05 now requires Australia/Sydney 05:00 schedule, 3600-second misfire grace, one-cycle catch-up bound, DST fold/gap cases, 8h sleep recovery, NTP backward/forward clock-jump cases, local business-date cycle IDs plus UTC watermarks, and no duplicate M4 watermark while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-E2E-B012` local 35-day E2E audit-bundle evidence so S2PMT05 now requires daily 3+1, weekly, monthly, review, action, and ROI count conservation, section artifacts, artifact index, link graph, deterministic bundle hash, and reachable review/action/ROI links while keeping real 35-day production replay, SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-FAULT-INJECTION-B009` local systematic fault-injection evidence so S2PMT05 now requires ENOSPC, read-only target, SQLITE_BUSY, corrupt JSON cache, corrupt PDF artifact, corrupt backup manifest, backup path collision, explicit recovery states, no partial artifact commits, durable evidence preservation, and fail-closed recovery actions while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-CAPACITY-BASELINE-B006` local formal capacity baseline evidence so S2PMT05 now requires load/stress/spike/soak rows, 1x/2x/5x multipliers, throughput/latency/queue/memory/disk/error metrics, bounded recoverable queue age, accelerated local 24h soak, and rebuildable-only spike shedding while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-BACKPRESSURE-B014` local backpressure priority evidence so S2PMT05 now requires 2x/5x peak profiles, high-priority SLO protection, explicit low-priority delay/drop reason codes, durable evidence preservation, and rebuildable-only shedding while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-RESULT-VALIDITY-B013` local result-validity evidence so S2PMT05 now requires semantic alignment, Claim Ledger references, evidence references, mechanism/action specificity, non-template variance, and unsupported P0 negative-control blocking while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT04-CACHE-LOW-DISK-B005` local cache low-disk degradation evidence so low disk pressure blocks new downloads and rebuildable cache writes, preserves durable evidence, keeps cleanup dry-run, and avoids queue/delete side effects while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added a local runner GitHub user-center sync gate so daily pass and real SMTP attempts require the shallow `用户中心/复习行动与收益.md` learning snapshot to be updated from S2PJT02/S2PJT03 reports; missing reports, failed sync, or remaining `待今日运行快照写入` fields now block readiness while SMTP enablement, scheduler, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Added the root governance rule that development runs must not leave open PRs as delivery state; created or inherited PRs must be merged or closed before closeout, and any still-needed stale/conflicting/draft work must be re-cut from current `main` as a clean branch rather than left open.
- Added `S2PLT04` integration candidate precheck so current Stage 2 evidence can be summarized into a blocked no-production report covering S2PLT01 review evidence, missing S2PLT02/S2PLT03 completion, local state/content evidence, inherited P0/P1 blockers, missing final bundle, and blocked S2PMT07; S2PLT04 completion, `S2_INTEGRATION_CANDIDATE_READY`, SMTP, scheduler, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Added `S2PLT01-INDEPENDENT-REPLAY-REVIEW` so the S2PLT01 replay payload execution package can be independently reviewed with reviewer identity, reviewer role, independence flag, CI/evidence refs, execution-report validation, retained inherited P0/P1 blockers, and deterministic `review_hash`; S2PLT01 acceptance, production replay, S2PMT07 final signoff, SMTP, scheduler, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Added `S2PLT01-REPLAY-PAYLOAD-EXECUTION` so explicit 30-day replay records, 120 M1-M4 `EMAIL_LEARNING_V1` no-send mail previews, and D1-D4 terminal source states can be packaged into a validated no-production replay payload execution report with entry precheck binding and deterministic `execution_hash`; S2PLT01 acceptance, production replay, SMTP, scheduler, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Hardened the `S2PMT04` / Stage 1 scheduler dry-run macOS launchd template for inherited A-013 by replacing handwritten plist XML and `/bin/sh -lc` command strings with `plistlib` generated structured `ProgramArguments`, `WorkingDirectory`, and `EnvironmentVariables`; real scheduler install, launchd bootstrap, SMTP, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Added `S2PLT01-REPLAY-EVIDENCE-GATE` so the S2PLT01 precheck can validate provided 30-day replay records, 120 M1-M4 `EMAIL_LEARNING_V1` no-send mail previews, D1-D4 terminal source states, zero leakage/P0P1 counters, and evidence refs without executing replay or claiming S2PLT01 acceptance; inherited P0/P1, S2PLT04, S2PMT07, SMTP, scheduler, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Hardened the `S2PMT02` / Stage 1 B1 report artifact publishing path for inherited A-010 by validating the package before any formal artifact write, staging all files under `.b1_staging`, publishing a complete package directory only after staged byte-hash verification, and cleaning staging on publish failure; production email, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Hardened the `S2PMT02` / Stage 1 B1 report artifact manifest for inherited A-011 by making `artifact_files.sha256` equal the written file byte SHA-256 while preserving the prior canonical content hash as `content_hash`; production email, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Hardened the `S2PMT02` / Stage 1 runtime backup path for inherited A-014 by copying supporting files to source-hash-prefixed manifest paths so different directories with the same filename are preserved without silent overwrite; production backup/restore, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Hardened the `S2PMT02` / Stage 1 runtime restore path for inherited A-001/A-002 by rejecting manifest database paths outside the backup root and validating a temporary restored SQLite file before atomic target replacement; production restore, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Synced post-merge `S2PBT05` owner/status governance wording so `OWNER_STATUS`, `ASSURANCE_STATUS`, `delivery_tasks`, and `model_registry` no longer describe `S2PBT05` as missing after PR #224; remaining blockers stay inherited P0/P1, full replay, 120 mail previews, terminal source states, S2PLT04, S2PMT07, and integrated production acceptance.
- Completed `S2PBT05` D1 source-domain qualification receipt from completed `S2PBT01` / legacy `S2P1T01` bioRxiv and medRxiv real no-send replay/shadow evidence, removing only the `s2pbt05_missing` S2PLT01 blocker while keeping inherited V7.1 P0=8/P1=37, missing full replay execution, missing 120 mail-preview proof, missing terminal source-state proof, formal D1 production inclusion, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contract files, DAILY_OPERATION, Stage2 production acceptance, and integrated production acceptance unchanged.
- Recorded `S2PLT01` fail-closed full-system replay entry precheck with machine-verifiable blockers that originally included missing `S2PBT05`, inherited V7.1 P0=8/P1=37, missing full 30-day replay execution, missing 120 mail-preview proof, and missing terminal source-state proof while keeping replay execution, S2PLT01 acceptance, S2PLT04 completion, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contract files, inherited P0/P1 closure, DAILY_OPERATION, Stage2 production acceptance, and integrated production acceptance unchanged.
- Recorded `S2PMT07` fail-closed final gate precheck with machine-verifiable blockers for missing independent reviewer proof, inherited V7.1 P0=8/P1=37, missing S2PLT04 completion, missing final acceptance bundle, missing independent signoff, and missing independent final command execution while keeping SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contract files, inherited P0/P1 closure, DAILY_OPERATION, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PMT06` local Chinese owner UX and safe-control evidence with first-screen status, fixed top/bottom navigation, breadcrumbs, status feedback states, recoverable error cards, safe config-change flow, append-only revision ledger, queue search/filter/sort/export/drilldown, safe retry/cancel/requeue/skip/regenerate previews, feedback visibility, accessibility/mail-client compatibility, source-to-ROI traceability, and no-production side-effect gates while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contract files, inherited P0/P1 closure, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PMT05` local pressure/fault/time/E2E evidence with deterministic load/stress/spike profiles, accelerated local 24h soak coverage, dual scheduler race protection, SMTP accepted-before-local-commit crash-window handling, ENOSPC/read-only/SQLITE_BUSY/corrupt-artifact fault injection, Australia/Sydney DST and clock-skew policy, 35-day 3+1/weekly/monthly/review/action/ROI count conservation, backpressure/degradation gates, deterministic isolation, and no-production side-effect gates while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, V7.1/V7.2 contract files, Stage2 production acceptance, inherited P0/P1 closure, and integrated production acceptance unchanged.
- Completed `S2PMT04` local automatic lifecycle and cache-cleanup evidence with disabled dry-run launchd wake path, STOPPED/STARTING/RECOVERING/LEADER/RUNNING/DRAINING/CHECKPOINTING/CLEANING state sequence, startup reconciliation, durable shutdown receipts, whitelist/symlink guarded dry-run cache cleanup, parseable launchd plist generation, and no-production side-effect gates while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, V7.1/V7.2 contract files, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PJT05` local-only monthly cognitive delta, capability growth, economic conversion, and forecast review evidence with passing S2PJT04 weekly reports, month-start/month-end cognitive snapshots, changed viewpoints with evidence, capability growth traceability, at least one verifiable calculated conversion, forecast review, next-month focus, deterministic monthly report hash, and no-production side-effect gates while keeping SMTP, scheduler, Release, DB migration, public schema, queue mutation, ranking, source adapters, Email V1 runtime/frontstage, CURRENT, V7.1/V7.2 contract files, owner-experience final acceptance, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PJT02` local-only review schedule and due queue evidence with default `1/3/7/14/30/90` intervals, feedback-adjustment readiness, due-today/7-day/overdue/completed count recomputation, deterministic due queue hash, and no-scheduler/no-production side-effect gates while keeping SMTP, Release, DB migration, public schema, queue mutation, ranking, source adapters, Email V1 runtime/frontstage, CURRENT, V7.1/V7.2 contract files, owner-experience final acceptance, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PJT01` local-only lifecycle state evidence for review/action/asset/conversion/mastery states with append-only history, count conservation, ledger mapping, dry-run rollback migration proof, and no-production/no-schema/no-email-frontstage side-effect gates while keeping real DB migration, SMTP, scheduler, Release, queue mutation, ranking, source adapters, Email V1 runtime/frontstage, CURRENT, V7.1/V7.2 contract files, owner-experience final acceptance, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PIT02` local-only runtime dashboard evidence for the Chinese owner center by aggregating S2PIT01 user-center evidence, Stage 1 runtime audit, watchdog, read-only storage inspect, and explicit production-boundary state into a local dashboard report and `00_用户中心/01_当前状态.md` while keeping live service probes, SMTP, scheduler, Release, public schema, DB migration, queue mutation, ranking, source adapters, Email V1 runtime/frontstage, CURRENT, V7.1/V7.2 contract files, owner-experience final acceptance, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PIT01` metadata-only/local Chinese user-center and one-edit owner-control entry evidence with `00_用户中心`, `00_只改这里`, four separated control domains, two-click reachability, `config/owner_controls.yaml` as the only editable fact source, read-only SQLite inspect input, compatible config compilation, and no-production/no-schema/no-email-frontstage side-effect gates while keeping CURRENT, V7.1/V7.2 contract files, SMTP, scheduler, Release, DB migration, public schema, queue mutation, source adapters, Email V1 runtime, owner-experience final acceptance, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PET04` / legacy `S2P4T04` metadata-only D4 US-TP and D4 qualification evidence across OSTP, BIS, FTC, FCC, CISA, and CHIPS Program with required technology policy signals, upstream S2PET01-S2PET03 gates, D4 30-date replay, 2-day shadow, B4/B5/B6 routing, 35/15/30/20 budget explanations, official identity, traceability, and no-production/no-schema side-effect gates while keeping live source fetching, D4 production inclusion, SMTP, scheduler, Release, public schema, queue mutation, V7.1/V7.2 contracts, Email V1 runtime/frontstage, and integrated production acceptance unchanged.
- Completed `S2PET03` / legacy `S2P4T03` metadata-only D4 US-FM financial, market, and macro source backbone evidence across SEC/EDGAR, Federal Reserve, Treasury, CFTC, OCC, FDIC, and CFPB with SEC form classification, CIK and Accession identifiers, company/fund/asset relations, upstream S2PET02 gate, official identity, traceability, and no-production/no-schema/no-investment-advice/no-trading side-effect gates while keeping live source fetching, paid market data, D4 production inclusion, SMTP, scheduler, Release, public schema, queue mutation, V7.1/V7.2 contracts, Email V1 runtime/frontstage, and integrated production acceptance unchanged.
- Completed `S2PET02` / legacy `S2P4T02` metadata-only D4 US-LG cross-agency legal backbone evidence across Federal Register, Regulations.gov, GovInfo, and Congress.gov with Docket/FR/CFR/bill/report/public-law/certified-text relations, upstream S2PET01 gate, official identity, traceability, and no-production/no-schema/no-legal-advice side-effect gates while keeping live source fetching, PDF/full-text download, D4 production inclusion, SMTP, scheduler, Release, public schema, queue mutation, V7.1/V7.2 contracts, Email V1 runtime/frontstage, and integrated production acceptance unchanged.
- Completed `S2PET01` / legacy `S2P4T01` metadata-only D4 US-TA official technology-agency source foundation evidence across NSF, DARPA, DOE, NIH, NASA, NIST, USPTO, and FDA with required signal taxonomy, official identity, traceability, and no-production/no-schema/no-email-frontstage side-effect gates while keeping live source fetching, D4 production inclusion, SMTP, scheduler, Release, public schema, queue mutation, V7.1/V7.2 contracts, Email V1 runtime/frontstage, and integrated production acceptance unchanged.
- Repaired `S2PAT07` V7.2 Email V1 root-governance pointers after `S2PHT01V1.1-T01-T05` reached main: CURRENT, V7.2 root lock, product contract, roadmap, current pointer registry, migration matrix, handoff, README, validator, and hashes now agree that Email V1 is `EMAIL_LEARNING_V1_MERGED_TO_MAIN_NO_PRODUCTION_SIDE_EFFECTS` while `S2PCT02` remains the global current task and SMTP, scheduler, Release, runtime mail code, public schema, DB/migration, V7.1, and integrated production acceptance remain unchanged.
- Completed `S2PGT05` / legacy `S2P6T02` private cross-board calibration and explainable queue evidence with B1-B6 percentile calibration, D1-D4 source balance, waiting credit, selected/queued/deferred readable reasons, deterministic ordering, stable queue hashing, and no-production/no-schema/no-email-frontstage side-effect gates while keeping production ranking, real queue mutation, source-domain production inclusion, SMTP, scheduler, Release, V7.2 contracts, Email V1 frontstage/runtime, and integrated production acceptance unchanged.
- Completed `S2PGT04` private support/refute/frontier delta and signal-resonance evidence with route linkage, required delta-type coverage, supported/refuted evidence states, resonance groups, signal-strength, explanation, evidence-ref, and no-production/no-schema/no-email-frontstage side-effect gates while keeping public schema migration, production queues, SMTP, scheduler, Release, source-domain production inclusion, V7.2 contracts, Email V1 runtime/frontstage, and integrated production acceptance unchanged.
- Completed `S2PGT03` private D1-D4 to B1-B6 multi-label routing evidence with source-domain, B1-B3 primary board, B4-B6 cross-cutting board, reason-code, explanation, evidence-ref, source-domain mapping, and no-production/no-schema side-effect gates while keeping public schema migration, production queues, SMTP, scheduler, Release, source-domain production inclusion, V7.2 contracts, Email V1 runtime, and integrated production acceptance unchanged.
- Completed `S2PGT02` / legacy `S2P6T01` private cross-source identity-resolution and knowledge-graph relation spine evidence across DOI, PMID, arXiv, Chinese document number, Federal Register document number, and CIK identifiers with duplicate-canonical, relation-evidence, idempotency, and no-production/no-schema side-effect gates while keeping public schema migration, production queues, SMTP, scheduler, Release, source-domain production inclusion, V7.2 contracts, and integrated production acceptance unchanged.
- Completed `S2PGT01` EvidencePacket V2 compatibility evidence with private D1-D4 source-domain report gates, required packet fields, metadata/abstract/full-text/cross-source evidence-level labels, old arXiv compatibility proof, and no-production/no-schema side-effect gates while leaving D4 source adapters, public schema migration, SMTP, scheduler, Release, queue mutation, V7.2 contracts, and integrated production acceptance unchanged.
- Completed `S2PFT05` / legacy `S2P5T05` full D3 China official-source governance qualification with C0-C4 component coverage, quota roles, quota balance, health balance, elimination explanations, fallback route, 30-date replay, and metadata-only gates while keeping formal D3 production inclusion, Stage 2 production acceptance, integrated production acceptance, SMTP, Release, scheduler, queue/schema mutation, public schema migration, V7.2 contract files, mail runtime, and production side effects disabled.
- Completed `S2PFT04` / legacy `S2P5T04` China special-zone metadata-only discovery evidence with zone ID, zone type, authority role, policy focus area, parent-city mapping, health tier, authority, dedupe, and metadata-only gates while keeping D3 full acceptance, Stage 2 production acceptance, SMTP, Release, scheduler, queue/schema mutation, public schema migration, V7.2 contract, mail runtime, and production side effects disabled.
- Completed `S2PFT03` / legacy `S2P5T03` first 24 China key-city metadata-only coverage evidence with city ID, alias, local department role, region group, region weight, health tier, authority, and metadata-only gates while keeping D3 full acceptance, Stage 2 production acceptance, SMTP, Release, scheduler, queue/schema mutation, public schema migration, special-zone, V7.2 contract, and production email side effects disabled.
- Completed `S2PFT02` / legacy `S2P5T02` Hong Kong and Macau independent profile evidence with separate jurisdiction identity, language profile, legal-system state, government-structure, authority, metadata-only, and mainland-template reuse gates while keeping D3 full acceptance, Stage 2 production acceptance, SMTP, Release, scheduler, queue/schema mutation, public schema migration, city, special-zone, V7.2 contract, and production email side effects disabled.
- Recorded PR #152/#153 as merged to `main`, confirming audited M1-M4 mail paths use `EMAIL_LEARNING_V1` while SMTP, scheduler, Release, public schema, DB/migration, CURRENT, V7.1, and integrated production acceptance remain unchanged.
- Completed `S2PFT01` / legacy `S2P5T01` China mainland provincial template coverage evidence for 31 provincial-level IDs while keeping D3 full acceptance, Stage 2 production acceptance, SMTP, Release, scheduler, queue/schema mutation, public schema migration, HK/MO, city, special-zone, V7.2 contract, and production email side effects disabled.
- Implemented `S2PHT01V1.1-T02-T04` EMAIL_LEARNING_V1 M1-M4 renderer: shared content object, responsive HTML/plain text template, ChatGPT new-chat links, arXiv/PDF links, candidate queue summary compatibility, and forbidden visible marker gate.
- Routed audited daily delivery, Stage1 B1 report email, local runner previews, scheduled readiness checks, and Stage2 shadow previews through Email V1 while keeping SMTP transport, scheduler trigger/production enablement, Release upload, source adapters, ranking, queue algorithms, public schema, DB/migrations, CURRENT, and V7.1 unchanged.
- Completed `S2PDT04` / legacy `S2P3T04` China official D3 readiness review evidence without granting D3 source-domain production acceptance.
- Added `adp stage2-china-d3-readiness-review`, 30-date replay, 2-day shadow, authority, B2-B6 board-routing, metadata-only/no-production gates, model/formula/parameter governance registrations, V7.2 revalidation receipt, and S2PDT04 manifest/phase evidence while keeping D3 core acceptance, Stage 2 production acceptance, SMTP, Release, schedule, queue mutation, public schema migration, PDF/full-text download, paid API use, paywall bypass, V7.1 CURRENT switching, V7.2 mail/schema pre-run, and production inclusion disabled.
- Completed `S2PDT03` / legacy `S2P3T03` China legal metadata, version/effectivity, reprint relation, and old-conclusion update shadow evidence.
- Added `adp stage2-china-legal-metadata-relation-shadow`, legal status and relation fixtures, legal status taxonomy/version effectivity/reprint relation/forced update/metadata-only gates, model/formula/parameter governance registrations, and S2PDT03 manifest/phase evidence while keeping legal advice, D3 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, queue mutation, schema migration, PDF/full-text download, paid API use, paywall bypass, V7.1 CURRENT switching, V7.2 mail/schema pre-run, and production inclusion disabled.
- Advanced V7.1 root routing to `S2PDT04` / legacy `S2P3T04` China official D3 source-domain readiness review.
- Completed `S2PDT02` / legacy `S2P3T02` China C1 central department and key ministry metadata-only source map evidence.
- Added `adp stage2-china-c1-department-source-map`, C1 department fixtures, sector coverage/official identity/alias/industry route/board route/metadata-only gates, model/formula/parameter governance registrations, and S2PDT02 manifest/phase evidence while keeping D3 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, queue mutation, schema migration, PDF/full-text download, paid API use, paywall bypass, V7.1 CURRENT switching, V7.2 mail/schema pre-run, and production inclusion disabled.
- Advanced V7.1 root routing to `S2PDT03` / legacy `S2P3T03` China legal metadata, effectivity/version, and reprint relation shadow.
- Completed `S2PCT07` D2 source-domain qualification and cross-type calibration as qualification-ready no-production evidence.
- Added `adp stage2-d2-source-domain-qualification`, upstream/domain/replay/shadow/forced-event/queue/type calibration gates, model/formula/parameter governance registrations, and S2PCT07 manifest/phase evidence while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, queue mutation, schema migration, PDF/full-text download, paid API use, paywall bypass, marketing-material acceptance, and production inclusion disabled.
- Advanced V7.1 root routing to `S2PDT01` / legacy `S2P3T01` China C0 national authoritative backbone.
- Completed `S2PCT06` authoritative research institution, laboratory, industry technical report, and product technical note metadata-only no-send shadow evidence.
- Added `adp stage2-authoritative-reports-shadow`, authoritative technical report fixtures, publisher identity/interest relation/evidence level/traceability gates, model/formula/parameter governance registrations, and S2PCT06 manifest/phase evidence while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, video, PDF/full-text download, paid API use, paywall bypass, marketing-material acceptance, and production inclusion disabled.
- Advanced V7.1 root routing to `S2PCT07` D2 source-domain qualification and cross-type calibration.
- Completed `S2PCT05` engineering open-source, code, benchmark, model-card, release, and standards public-signal metadata-only no-send shadow evidence.
- Added `adp stage2-engineering-signals-shadow`, engineering signal fixtures, officiality/version/paper-relation/reproducibility gates, model/formula/parameter governance registrations, and S2PCT05 manifest/phase evidence while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, video, PDF/full-text download, paid API use, repository clone, and paywall bypass disabled.
- Advanced V7.1 root routing to `S2PCT06` authoritative research institution and industry technical report framework.
- Completed `S2PCT04` / legacy `S2P2T04` top-journal profile, publication relation, correction, and retraction metadata-only no-send shadow evidence across Nature, Science, and The Lancet shadow batches.
- Added profile taxonomy for research, review, editorial, news, correction, and retraction; relation edges for original publication, discusses, corrects, and retracts; and forced-event updates where correction requires revision and retraction invalidates prior conclusions.
- Added `adp stage2-top-journal-profile-shadow`, profile relation fixtures, prior state fixtures, model/formula/parameter governance registrations, and S2PCT04 manifest/phase evidence while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, video, PDF/full-text download, and paywall bypass disabled.
- Advanced V7.1 root routing to `S2PCT05` engineering open-source, code, benchmark, model-card, release, and standards public-signal framework.
- Completed `S2PCT03` / legacy `S2P2T03` The Lancet main-journal metadata-only no-send shadow evidence using official public Lancet Online First RSS and current issue RSS cross-checks.
- Added Lancet medical article-type gates, DOI-query-ready PubMed relation metadata, duplicate DOI/source handling, separate Lancet shadow queue/ledger/email preview persistence, and `adp stage2-lancet-shadow-daily`.
- Verified focused top-journal/stage2 tests, semantic governance preparation, and a live Lancet RSS no-send canary while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, video, PubMed full-record harvesting, PDF/full-text download, and paywall bypass disabled.
- Advanced V7.1 root routing to `S2PCT04` / legacy `S2P2T04` journal profile, publication relation, correction, and retraction modeling.
- Completed `S2PCT02` / legacy `S2P2T02` Science main-journal metadata-only no-send shadow evidence using the official public Science RSS feed.
- Added Science article-type gates for Research Article, Report, Review, and Perspective, duplicate DOI/source handling, separate Science shadow queue/ledger/email preview persistence, and `adp stage2-science-shadow-daily`.
- Verified focused top-journal/stage2 tests, semantic governance, and a live Science RSS no-send canary while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, video, PDF/full-text download, and paywall bypass disabled.
- Advanced V7.1 root routing to `S2PCT03` / legacy `S2P2T03` The Lancet metadata-only shadow, and hardened dashboard generation so stale owner decisions do not override the next task after a task transition.
- Added `S2PCT01` / legacy `S2P2T01` V7.1 D2 top-journal shadow foundation using official public Nature RSS metadata, filtering to `s41586-*` main-journal research article links only.
- Added `adp fetch-top-journal-latest` and `adp stage2-top-journal-shadow-daily` with separate no-send queue, ledger, dry-run package, and email preview persistence; kept Stage 2 production acceptance, SMTP, Release, schedule, and video disabled.
- Verified a live Nature RSS no-send canary with 3 real `s41586` source IDs and local queue/ledger/email preview artifacts under `/tmp`.
- Implemented the `S2P1T01` bioRxiv/medRxiv source-promotion foundation: metadata-only preprint adapter, disabled Stage 2 source registry entries, promotion gate, separate shadow daily queue/ledger/email preview path, and fixture tests.
- Verified one live bioRxiv and one live medRxiv fixed-interval canary plus one no-send shadow daily canary; kept formal production inclusion blocked until 30-date terminal replay and 48h shadow evidence pass.
- Added `adp local-runner preflight|daily|launchd-package` for Stage 1 local Mac + Codex/local runner operation.
- Added local queue, local content ledger JSONL, per-run report, and plain/HTML email preview persistence under an owner-controlled state directory.
- Added a disabled launchd package draft and 2026-06-30 migration runbook without installing the scheduler, sending production SMTP, enabling GitHub cloud scheduled production, uploading Release artifacts, or generating video.
- Set the next executable roadmap task to `S2P1T01` after `ADP-S1P5T05` local production and migration prep.

## 0.23.1 - 2026-06-23

- Reopened strict Stage 1 acceptance for `S1P5T03-R REAL_ARXIV_30_DAY_BACKFILL_AND_LEDGER_RECONCILE`.
- Added cloud-runner real historical arXiv 30-day backfill workflow, replay CLI, tests, and persisted `CONTENT_LEDGER.csv` rows for 30 selected and 269 queued candidates.
- Recorded GitHub/cloud run `28027759062` artifact `7821452823` as the strict 30-day backfill proof; kept production scheduling, SMTP send, Release upload, Stage 2, and video generation disabled.
- Implemented `ADP-PHASE12-EMAIL-HUMAN-FORMAT-036`: Stage 1 owner email now renders as a Chinese teaching brief and hides ROI score, Release, video, delivery-policy, and backend wording from the frontstage.

## 0.23.0 - 2026-06-23

- Recorded PR #82 GitHub/cloud artifact `7818287996` as
  `ARXIV_PRODUCTION_ACCEPTED` for Stage 1 arXiv.
- Added project-root `功能清单`, `开发记录`, and `模型参数文件` human entry files,
  with the V6 roadmap rendered directly in `开发记录`.
- Hardened scheduled/trial workflows so all-arXiv fallback collection uses
  `ADP_ARXIV_MAX_RESULTS_PER_CATEGORY:-3`, matching accepted evidence volume.
- Kept production scheduling disabled and fail-closed until GitHub repo
  variables/secrets are explicitly verified or enabled.
- Added `adp build-stage1-accelerated-acceptance` for S1P5T04 accelerated real-arXiv acceptance evidence.
- Updated the live all-arXiv cloud dry-run workflow to collect up to 3 items per primary archive and build a 30-sample accelerated acceptance artifact on GitHub runner.
- Kept production scheduling disabled, sent no new email, and preserved Stage 1 text-only/no-video/no-Release requirements.

## 0.22.0 - 2026-06-23

- Converted S1-12 production enablement to Stage 1 text-only delivery: all-arXiv scan, candidate queue, ROI-ranked lead selection, Chinese teaching email, and GitHub Actions text artifacts.
- Removed video/MP4 and GitHub Release upload as production-readiness requirements for Stage 1; Gmail SMTP remains the only controlled frontstage side effect.
- Kept production scheduler and `ARXIV_PRODUCTION_ACCEPTED` disabled pending PR CI, manual controlled SMTP test evidence, and later acceptance gates.
- Imported the V6 task-numbering roadmap under `docs/pursuing_goal/`, locked current progress to `S1P5T04`, and recorded GitHub/cloud-runner manual Gmail SMTP run `28002478689` as the first controlled send evidence.

## 0.21.0 - 2026-06-23

- Added S1-11 historical B1/arXiv preview evidence generation via `adp historical-b1-previews`.
- Added deterministic 30-sample B1 report/email preview generation with unique source IDs, content hashes, email IDs, claim evidence audits, and content ledger rows.
- Kept live network fetch, production scheduler, real SMTP send, GitHub Release upload, video generation, and `ARXIV_PRODUCTION_ACCEPTED` disabled.

## 0.20.0 - 2026-06-23

- Added S1-10 post-migration bootstrap verification for the target machine or GitHub-hosted cloud runner.
- Added `adp post-migration-bootstrap` to verify Python, Git checkout, SSL context, SQLite/FTS5, runtime smoke, GitHub Actions runner env, workflow runner contract, and secret-name-only readiness.
- Added a GitHub-hosted Stage 1 bootstrap workflow that runs on `ubuntu-latest`, uploads JSON evidence, and keeps production schedule, SMTP send, Release upload, video, and large replay disabled.

## 0.19.0 - 2026-06-22

- Added S1-09 low-resource migration package export and verification via `adp migration export|verify`.
- Added package manifest hash verification, new-machine bootstrap checklist, secret-name checklist, restore drill, and low-resource smoke artifact generation.
- Kept production scheduling, real SMTP, Release upload, video generation, 30-day replay, and Stage 2 promotion disabled.

## 0.18.0 - 2026-06-22

- Added S1-08 local runtime recovery controls for `adp tick`, `adp watchdog`, `adp backup`, `adp restore`, `adp runtime-audit`, and `adp scheduler install|uninstall`.
- Added heartbeat/checkpoint state, stale-heartbeat watchdog checks, SHA256 SQLite backup/restore manifests, and scheduler dry-run template generation.
- Kept production scheduling, real SMTP, Release upload, video generation, and long-running local background execution disabled.

## 0.17.0 - 2026-06-22

- Added S1-07 B1/arXiv Chinese teaching report and email preview artifact generation.
- Added `adp build-b1-report-email` for text-first Markdown, HTML, plain-text email, HTML email, and audit JSON output.
- Added fail-closed validation for 100% critical-claim evidence coverage, Chinese-first email content, no real SMTP, no Release upload, and no video requirement.

## 0.16.0 - 2026-06-22

- Promoted the V5 two-stage text-delivery baseline for Stage 1 B1/arXiv and marked conflicting V4/media requirements as inactive for the current acceptance path.
- Added the V5 Stage 1 scoring, 10,000 queue, 365-day window, reason-code, and text-first content-ledger contract.
- Added `adp stage1-queue` JSON output plus deterministic tests for 10,001st-item eviction, 365-day boundary handling, soft quota borrowing, source-share cap enforcement, lifecycle reason codes, stable tie ordering, and canonical `CONTENT_LEDGER.csv` columns.
- Updated generated owner ledger columns to use the Stage 1 text content-ledger contract while keeping production acceptance, scheduler, SMTP, Release upload, video generation, and broad source expansion disabled.

## 0.15.0 - 2026-06-22

- Added the Review8 Stage 1 source registry and arXiv connector contract for `SRC-ARXIV` / `arxiv.atom.v1`.
- Added `adp source-registry validate` JSON output, source registry schema, offline fixture validation, and fail-closed connector contract tests.
- Lowered the Stage 1 Window A online arXiv metadata canary cap from 25 to 10 without enabling PDFs, bulk harvest, SMTP, Release upload, scheduler, or production acceptance.

## 0.14.1 - 2026-06-22

- Rebuilt the daily email as a responsive HTML plus concise Chinese plain-text decision brief based on the V2 mockup: exact `YYYYMMDD -- Project Name -- arXiv Group -- Theme` subject, read/skim/skip, evidence level, reading time, first-principles chain, decision mapping, key questions, evidence gaps, minimal experiment, optional `.mp4` video link, and feedback actions.
- Removed frontend numeric `x/5` score labels from the subject, plain-text body, and HTML body; ranking/ROI scores remain backend-only evidence.
- Added a human-frontstage lesson payload so backend Claim Ledger and ROI details remain auditable while user-visible email hides Claim Ledger IDs, visible ROI scores, delivery policy text, Release landing-page clutter, and irrelevant q-fin candidate pollution.
- Kept production schedule disabled; this change prepares the next PR CI and controlled manual Gmail SMTP plus GitHub Release rerun only.

## 0.14.0 - 2026-06-22

- Added the Review8 Stage 1 local SQLite/WAL/FTS5 document and event storage model.
- Added `adp storage migrate`, `adp storage inspect`, and `adp storage rollback` JSON CLI commands.
- Added deterministic migration, SourceItem persistence, full-text search, inspection, and rollback tests.
- Kept source fetching, PDF retention, SMTP, Release upload, scheduler enablement, and production acceptance unchanged.

## 0.13.1 - 2026-06-22

- Corrected the Phase 12 human front-stage after manual run `27934320671`: the email text is now the reading entry point, Release is backend evidence/download storage, and video is an optional file link.
- Removed backend ROI score exposure from the MP4 transcript.
- Kept production schedule disabled; this change prepares the next controlled manual Release plus Gmail SMTP rerun only.

## 0.13.0 - 2026-06-22

- Added `config/owner_controls.yaml` as the single owner-editable control file for Stage 1 Window A.
- Added `adp owner validate`, `adp owner preview-impact --days 30`, and `adp owner render-docs --write` to validate controls, preview impact, and generate four owner-readable files.
- Added generated `docs/owner/OWNER_CONSOLE.md`, `SOURCE_CATALOG.md`, `MODEL_AND_QUEUE.md`, and `CONTENT_LEDGER.csv` views from machine facts only.
- Kept production schedule, SMTP, Release upload, source ingestion expansion, and scoring runtime behavior unchanged.

## 0.12.5 - 2026-06-22

- Refined the daily email front-end format for human scanning, actionability, and information density.
- Changed the daily email subject to `YYYYMMDD -- arXiv <Project Group> -- <arXiv Group> -- <Theme>`.
- Removed front-end `project`, `date`, `recipient`, ROI score, and delivery policy lines from the daily email body while preserving ROI evidence in backend artifacts.
- Kept Release/video links, Chinese lesson text, concise evidence, candidate queue summary, and no video email attachment policy.
- Kept production schedule disabled; this change only prepares the next controlled manual email test.

## 0.12.4 - 2026-06-22

- Fixed GitHub Release delivery to deduplicate repeated identical asset paths before invoking `gh release create`.
- Added fail-closed blocking for distinct Release assets that would publish with the same filename.
- Recorded second manual delivery run `27927785092`, where workflow-level dedupe passed but the lower release delivery boundary still blocked before SMTP.
- Added bounded transient retry handling for live all-arXiv cloud dry-runs after PR CI run `27928505758` hit arXiv 429 limits while preserving the 20/20 archive pass requirement.
- Bound successful GitHub Actions manual delivery run `27932072771` as controlled Release/Gmail SMTP evidence while preserving the no-production-acceptance boundary.
- Locked the Review8 two-stage V4 pursuing-goal baseline under `docs/pursuing_goal/BASELINE_LOCK.md` and started Stage 1 Window A traceability without changing runtime behavior.
- Kept production schedule disabled and preserved no-secret/no-attachment Release-link delivery policy.

## 0.12.3 - 2026-06-22

- Fixed the manual GitHub Release plus Gmail SMTP test workflow to deduplicate Release assets by filename before invoking scheduled delivery.
- Preserved fail-closed behavior: if Release creation fails, the workflow still blocks SMTP instead of sending an email without a video/Release link.
- Kept scheduled production disabled and unchanged.

## 0.12.2 - 2026-06-22

- Added a default-branch-only manual GitHub Actions workflow for one controlled GitHub Release plus Gmail SMTP delivery test.
- The manual workflow scans all arXiv primary archive buckets, selects one ROI-ranked daily paper, renders a lightweight MP4, creates a Release with the MP4 and JSON artifacts, then sends one email to `linzezhang35@gmail.com` containing Chinese lesson text, Release link, video link, and candidate queue summary.
- Kept scheduled production disabled: the workflow has no `schedule:` trigger, does not read repository production enablement variables, and requires the exact `SEND_TEST_EMAIL_TO_LINZEZHANG35_GMAIL_COM` confirmation string before side effects.

## 0.12.1 - 2026-06-22

- Added Phase 12 cloud production-enablement workflow for GitHub-hosted live all-arXiv dry-run evidence across all 20 primary archive buckets.
- Added `adp run-live-all-arxiv-dry-run` and `adp render-lightweight-mp4` evidence paths that produce a live-selected sample daily input and a real lightweight `.mp4` artifact.
- Migrated arXiv Daily Push scheduled, trial-start, provisioning-audit, and production-trial workflows away from self-hosted runner targeting to GitHub-hosted `ubuntu-latest`.
- Tightened email video-link gating so JSON video manifests no longer satisfy production-ready email evidence; a GitHub Release `.mp4` asset link is required.
- Kept production schedule, SMTP sending, and Release uploading disabled by default pending cloud dry-run, Release, and manual Gmail SMTP evidence.

## 0.12.0 - 2026-06-22

- Added Phase 12 all-arXiv primary archive scanning via `adp plan-all-arxiv-scan` and `adp build-all-arxiv-daily-input`.
- Added persistent candidate queue behavior with ROI/learning-value ranking, one daily lead selection, high-value queue carry-forward, and queue fallback when no new high-value paper is available.
- Updated scheduled and trial-start workflows to remove the old `cat:cs.AI` production default and build Phase 12 all-arXiv daily input artifacts instead.
- Added Release-hosted video artifact link requirements before real SMTP can count as production-ready scheduled evidence.
- Updated runbook and config examples for all-arXiv scope, candidate queue state, GitHub Release artifact links, and fail-closed production enablement.

## 0.11.27 - 2026-06-22

- Added `adp run-two-day-simulation` for the updated Phase 11 two-day simulation acceptance path.
- The simulation runs two unique scheduled daily paths with mocked SMTP and Release boundaries, appends both days to trial evidence, and verifies no duplicate dates, source IDs, or publication IDs.
- Kept the simulation fail-closed and explicit: it does not fetch network data, send real SMTP mail, upload a real Release, read Codex auth, log secret values, retain media/cache artifacts, or claim production acceptance.

## 0.11.26 - 2026-06-22

- Added `adp review-provisioning-audit` to register a downloaded `adp-production-provisioning-audit` artifact before trial-start dispatch.
- The review gate requires a valid passing production refs report plus durable workflow run and artifact refs.
- Kept the review fail-closed and no-side-effect: it does not read secret values, Codex auth, dispatch workflows, send SMTP mail, upload Releases, or claim production acceptance.

## 0.11.25 - 2026-06-22

- Added a manual `arxiv-daily-push-provisioning-audit.yml` workflow that runs on `ubuntu-latest` before trial start and uploads `adp-production-provisioning-audit`.
- Reused `discover-production-refs` to validate runner label, required SMTP secret names, Release target variable, and workflow variables without occupying the private runner.
- Kept the audit fail-closed and no-secret: it does not read secret values, Codex auth, dispatch trial start, send SMTP, create Releases, or claim production acceptance.

## 0.11.24 - 2026-06-22

- Updated the default-branch trial-start workflow to run no-secret production refs discovery before any live source, SMTP, Release, or start-gate work.
- Added an in-workflow `plan-production-launch` readiness precheck that consumes the production refs artifact and fails closed before side effects.
- Added workflow contract checks and artifacts for `adp-trial-start-production-refs` and `adp-trial-start-launch-readiness` while keeping Phase 11 production acceptance blocked until real trial evidence exists.

## 0.11.23 - 2026-06-22

- Added `adp discover-production-refs` to use `gh api` on a provisioned runner and build a no-secret production refs report from GitHub Actions metadata.
- Added metadata discovery coverage for runner label, required SMTP secret names, Release target variable, and workflow variable names without printing `gh` stdout/stderr or secret values.
- Kept local execution fail-closed when `gh` is unavailable and kept production launch/30-day acceptance blocked until real external refs and trial evidence exist.

## 0.11.22 - 2026-06-22

- Added `adp print-production-refs-template` to emit a no-secret owner-fillable JSON template before `plan-production-refs`.
- Added a repository example production refs input template that defaults to blocked readiness and contains only secret/variable names plus empty refs.
- Kept production launch blocked until owner-provisioned durable refs, explicit confirmation, default-branch trial-start evidence, and 30-day production evidence exist.

## 0.11.21 - 2026-06-22

- Added machine-checked GitHub Actions `contents: write` permission requirements for controlled Release probes.
- Updated trial-start and scheduled production workflow contracts so real Release evidence can be created only after explicit enablement.
- Kept SMTP/Release side effects disabled by default and production acceptance blocked until external refs and 30-day evidence exist.

## 0.11.20 - 2026-06-22

- Added `adp plan-production-refs` and `adp-production-refs-v1` to collect external runner, SMTP secret-name, Release target, and workflow variable readiness refs without reading or logging secret values.
- Added fail-closed checks for required SMTP secret names, required workflow variable names, durable readiness refs, explicit ready flags, and suspicious secret-value input fields.
- Updated `adp plan-production-launch` so a passing production refs report can fill the external runner/SMTP/Release/workflow refs while keeping launch and 30-day production acceptance blocked until real external evidence exists.

## 0.11.19 - 2026-06-22

- Added `adp plan-production-launch` and `adp-production-launch-readiness-v1` to fail closed before default-branch trial start workflow dispatch.
- Added launch readiness validation for PR merged/non-draft state, expected head SHA binding, trial start workflow contract, private runner ref, SMTP secrets ref, Release target ref, workflow variable ref, and explicit launch confirmation.
- Added launch readiness schema and tests covering pass, current draft/unmerged PR blocking, head SHA mismatch blocking, and CLI JSON output.

## 0.11.18 - 2026-06-22

- Added `.github/workflows/arxiv-daily-push-trial-start.yml` to collect default-branch trial start evidence on the private runner.
- Added `adp plan-trial-start-workflow` and `adp-trial-start-workflow-v1` to validate manual dispatch, preflight-first ordering, live source and delivery probe ordering, artifact uploads, durable refs, and explicit SMTP/Release variable gates.
- Added workflow plan schema and tests covering manual-only behavior, required artifacts, side-effect gating, secret-name-only mapping, and CLI JSON output.

## 0.11.17 - 2026-06-22

- Added `adp plan-trial-start` and `adp-trial-start-v1` to build a fail-closed readiness report before starting the real 30-day production trial.
- Added start gating across passing production preflight, bootstrap workflow, scheduler contract, live arXiv source batch, real sent SMTP probe, real created Release probe, explicit confirmation, and durable GitHub/runner/state/start refs.
- Added trial start schema and tests covering pass, missing confirmation, missing durable refs, SMTP dry-run blocking, blocked preflight, and CLI JSON output.

## 0.11.16 - 2026-06-22

- Added `adp build-trial-resource-evidence` and `adp-trial-resource-v1` to verify 30-day resource telemetry from daily trial resource refs and passing production preflight reports.
- Tightened production preflight resource refs so passing preflight reports use timestamped `production-preflight://` refs instead of a static `current` ref.
- Added resource schema and tests covering pass, missing matching preflight blocking, blocked preflight blocking, missing durable resource ref blocking, and CLI JSON output.

## 0.11.15 - 2026-06-22

- Added `adp build-trial-recovery-evidence` and `adp-trial-recovery-v1` to build fail-closed recovery drill evidence from a failed/degraded scheduled daily-run and a recovered production-ready rerun.
- Added recovery validation requiring real sent failure/recovery notifications, production-ready recovery refs, matching daily dates when available, and durable failure/recovery evidence refs.
- Added recovery schema and tests covering pass, dry-run failure notification blocking, missing recovery ref blocking, non-production-ready recovery blocking, and CLI JSON output.

## 0.11.14 - 2026-06-22

- Added `adp build-trial-replay-evidence` and `adp-trial-replay-v1` to build fail-closed weekly/monthly replay evidence from the accumulated trial ledger.
- Added replay validation requiring production-ready daily refs, no duplicate dates/source/publication IDs, 7 consecutive days for weekly replay, 30 consecutive days for monthly replay, and a durable replay evidence ref.
- Added replay schema and tests covering weekly/monthly pass, monthly coverage blocking, missing durable ref blocking, duplicate-date blocking, and CLI JSON output.

## 0.11.13 - 2026-06-22

- Added `adp annotate-trial-ops-evidence` for fail-closed annotation of explicit weekly/monthly replay, recovery drill, scheduler, Release, SMTP, and resource evidence refs.
- Added `adp export-trial-ops-state` so a passing ops annotation can carry forward the updated `trial_evidence` JSON without hand-editing state.
- Added tests that block verified operational flags without refs and prove weekly/monthly plus recovery evidence can unlock the final trial validator when all daily evidence already exists.

## 0.11.12 - 2026-06-22

- Added `adp export-trial-ledger-state` to export the accumulated `trial_evidence` JSON from a passing ledger update report.
- Updated the scheduled workflow to restore the prior `adp-trial-evidence-ledger` artifact with `gh run download` and upload the new state after successful daily ledger append.
- Added tests and scheduler validation for cross-run trial ledger state persistence while keeping 30-day production acceptance blocked until the validator passes.

## 0.11.11 - 2026-06-21

- Added `adp update-trial-ledger` and `adp-trial-ledger-v1` to append production-ready scheduled daily-run evidence into the Phase 11 trial evidence package.
- Updated the scheduled workflow to upload an `adp-trial-ledger-update` artifact after daily-run evidence while preserving fail-closed behavior for duplicate days, dry-run side effects, and missing production refs.
- Added trial ledger schema and tests covering blocked non-production evidence, duplicate daily evidence, global evidence flag upgrades, CLI JSON output, and scheduled workflow wiring.

## 0.11.10 - 2026-06-21

- Added `adp build-daily-input` and `adp-daily-input-builder-v1` to convert live arXiv source batches into ranked daily pipeline inputs using only Atom summary claims.
- Updated scheduled daily-run workflow wiring to build and upload `adp-scheduled-source-batch` and `adp-scheduled-daily-input` artifacts when no override input path is configured.
- Added daily input schema and tests covering summary-derived P0 claims, missing-summary blocking, recent-selection blocking, CLI JSON output, and scheduled execution compatibility.

## 0.11.9 - 2026-06-21

- Added `adp run-scheduled-production` and `adp-scheduled-execution-v1` as the controlled execution driver for scheduled health-check, daily-run, and watchdog modes.
- Updated the scheduled GitHub workflow to upload `adp-scheduled-execution` evidence after preflight while still failing closed when preflight, daily input, SMTP, or Release evidence is missing.
- Added scheduled execution schema and tests covering dry-run notification evidence, scheduled-run gating, degraded dry-run side effects, and mocked production-ready SMTP/Release evidence.

## 0.11.8 - 2026-06-21

- Added `.github/workflows/arxiv-daily-push-scheduled.yml` with `Australia/Sydney` 04:45 health-check, 05:00 daily-run, and 05:10 watchdog schedule slots.
- Added `adp plan-production-scheduler` and `adp-production-scheduler-v1` to validate the scheduled workflow gate without enabling production side effects.
- Added scheduler schema and tests covering timezone schedules, production variable gates, preflight-first ordering, and no SMTP/Release side effects.

## 0.11.7 - 2026-06-21

- Added `adp publish-release` for dry-run GitHub Release evidence and explicit Release creation.
- Added `adp-release-delivery-v1` with target gating, safe asset checks, no clobber upload, and no notes/stdout/stderr logging.
- Added Release delivery schema and tests covering dry-run, missing-target blocking, forbidden secret-like assets, mocked `gh release create`, and CLI JSON output.

## 0.11.6 - 2026-06-21

- Added `adp send-notification` for dry-run notification evidence and explicit SMTP delivery.
- Added `adp-smtp-delivery-v1` with fail-closed environment-key checks, TLS-required delivery, body hashing, and no secret/body logging.
- Added SMTP delivery schema and tests covering dry-run, missing-env blocking, and mocked real send.

## 0.11.5 - 2026-06-21

- Added `adp fetch-arxiv-latest` for small-window live arXiv Atom source ingestion.
- Added incremental duplicate filtering by prior `source_id` and a SourceBatch schema.
- Added fail-closed network/API/Atom parsing behavior with tests and current local SSL-blocker evidence.

## 0.11.4 - 2026-06-21

- Added a manual GitHub Actions production trial bootstrap workflow that runs production preflight before any trial work.
- Added `adp plan-trial-bootstrap` to validate the workflow/runbook contract without enabling cron, Release upload, or SMTP sending.
- Added a production trial runbook and trial bootstrap schema/tests.

## 0.11.3 - 2026-06-21

- Added `adp preflight-production` as a fail-closed gate before any scheduled production run.
- Preflight now checks production commands, required secret environment key presence without logging values, disk, memory, Git artifact hygiene, and local cache/staging directories.
- Added production preflight schema and tests covering blocked and passing reports.

## 0.11.2 - 2026-06-21

- Added a Phase 11 trial evidence validator for 30-day production evidence packages.
- Added `adp evaluate-trial` for validating daily run uniqueness, traceability, scheduler, Release, SMTP, resource, weekly/monthly replay, and recovery evidence.
- Hardened production acceptance so manual operational flags cannot pass unless they come from a validated trial evidence report.

## 0.11.1 - 2026-06-21

- Hardened Phase 11 production acceptance: every production pass requirement now needs both a true flag and a non-empty evidence reference.
- Added regression coverage that blocks boolean-only operational evidence from marking production acceptance as passed.

## 0.11.0 - 2026-06-21

- Added Phase 11 acceptance and handoff readiness package generation.
- Added `adp build-acceptance` for converting Phase 10 handoff JSON into a truthful acceptance package.
- Acceptance output blocks production acceptance unless explicit 30-day, scheduler, Release, SMTP, and resource evidence is provided.
- Added acceptance tests covering default blocked status, unsupported claim prevention, invalid handoff rejection, future evidence pass, and CLI output.

## 0.10.0 - 2026-06-21

- Added Phase 10 runner/release/email dry-run handoff.
- Added `adp build-handoff` for converting a completed dry-run pipeline payload into a handoff preview.
- Added fail-closed validation that keeps scheduler, GitHub Actions runner, Release upload, unattended execution, and real SMTP sending disabled.
- Added handoff tests covering completed RunRecord requirements, disabled external side effects, validation errors, and CLI output.

## 0.9.0 - 2026-06-21

- Added Phase 9 local daily dry-run pipeline orchestration.
- Added `adp run-daily-dry-run` for local source/claim JSON pipeline execution.
- Added RunRecord state transitions through completed, publication gate, Lesson, Narration, Storyboard, and email preview output.
- Added pipeline fixture and tests covering successful completion, evidence blocking, email preview, and CLI output.

## 0.8.0 - 2026-06-21

- Added Phase 8 storyboard/video dry-run generation from narration JSON.
- Added `adp generate-storyboard` for local storyboard rendering.
- Added video media gate with rendering, media writes, and asset downloads blocked in Phase 8.
- Added video fixture and tests covering dry-run storyboard generation, real render blocking, media path rejection, claim subset validation, and CLI output.

## 0.7.0 - 2026-06-21

- Added Phase 7 dry-run narration/TTS plan generation from Lesson JSON.
- Added `adp generate-narration` for local narration plan rendering.
- Added TTS resource gate with real synthesis, audio writes, and model downloads blocked in Phase 7.
- Added narration schema, fixture, and tests covering dry-run boundaries, real TTS blocking, audio path rejection, CLI output, and runtime parameters.

## 0.6.0 - 2026-06-21

- Added Phase 6 deterministic Chinese Lesson JSON generation from supported Claim Ledger evidence.
- Added `adp generate-lesson` for local lesson rendering from source/claim JSON fixtures.
- Added lesson validation that blocks unsupported or unknown claim references and requires visible claim markers in section bodies.
- Added lesson fixture and tests covering supported-claim linkage, unverified claim exclusion, blocked ledger handling, validation failures, and CLI output.

## 0.5.0 - 2026-06-21

- Added Phase 5 Claim Ledger construction and publication hard-block gate.
- Added `adp gate-publication` for local source/claim JSON gate checks.
- Added fail-closed checks for missing P0 locators, unsupported P0 claims, metadata conflicts, and unsupported arXiv peer-review claims.
- Added Claim Ledger fixture and evidence gate tests.

## 0.4.0 - 2026-06-21

- Added Phase 4 deterministic 100-point ranking and queue audit.
- Added fail-closed gates for missing P0 evidence, unsupported P0 evidence, metadata conflicts, and recent duplicate selections.
- Added `adp rank-candidates` for local candidate ranking from JSON fixtures.
- Added ranking golden tests and a small queue fixture.

## 0.3.0 - 2026-06-21

- Added Phase 3 arXiv Atom source adapter.
- Added offline Atom fixture parsing into generic `SourceItem` records.
- Added arXiv query URL rendering without network fetch.
- Added source adapter tests using local fixtures only.

## 0.2.0 - 2026-06-21

- Added Phase 2 generic contracts for `SourceItem`, `EvidenceClaim`, `Lesson`, `Storyboard`, `Publication`, and `RunRecord`.
- Added dependency-free runtime validators and a deterministic `RunRecord` state machine.
- Added `adp validate-record` for local `RunRecord` validation.
- Kept Phase 2 offline-only: no network ingest, ranking, TTS, video, runner automation, or real SMTP sending.

## 0.1.0 - 2026-06-21

- Created Phase 1 repository foundation for `arXiv Daily Push`.
- Added CLI skeleton with `version`, `doctor`, and `render-email`.
- Added dry-run notification contract for `linzezhang35@gmail.com`.
- Added local resource and storage pressure guardrails.
- Added CodexProject governance records for Phase 1.

- Added S2PJT03 local action, capability asset, and expected/actual ROI ledger evidence without production side effects.

- Added S2PJT04 local weekly report and attention reallocation evidence without production side effects.

- Added S2PHT05 local semantic content quality gate evidence without mail production or other production side effects.

- Added S2PIT03 local source/model/parameter/queue view evidence without production side effects.

- Added S2PIT04 local content/mail/review/action/asset/ROI ledger reconciliation evidence without production side effects.
- Added S2PKT01 local M1-M4 EMAIL_LEARNING_V1 mail contract evidence without production side effects.
- Added S2PKT02 local M1 science/theory frontier mail evidence without production side effects.
- Added S2PKT03 local M2 engineering/product/industry frontier mail evidence without production side effects.
- Added S2PKT04 local M3 policy/capital/geopolitical frontier mail evidence without production side effects.
- Added S2PKT05 local M4 cross-board 3+1 mail orchestration evidence without production side effects.
- Added S2PMT01 local security and evidence-boundary gates without production side effects.
- Added S2PMT02 local atomic storage and recovery hardening evidence without production side effects.

- Added S2PMT03 local lease fencing, state concurrency, transactional outbox, SMTP crash-window, and M4 watermark evidence without production side effects.
- Added S2PLT01 replay payload contract evidence without replay execution or production side effects.
- Added S2PMT03 A-016 lesson revision identity hardening with stable `lesson_key`, immutable content/evidence-sensitive `lesson_revision_id`, and no production side effects.
- Added S2PMT03 B-003 local watchdog stale-lock recovery gate that blocks live-owner takeover and only permits expired dead-owner recovery through row-version and fencing-token claim semantics, with no production side effects.
- Added S2PMT03 B-011 local M4 watermark hardening for M2 failure, M3 timeout, late terminal data, rerun idempotence, and cross-cycle leakage without production side effects.
- Added S2PMT04 B-004 local startup convergence gate for persistent-state count conservation without production side effects.
- Added S2PMT04 B-015 local transaction completion gate for shutdown save/cleanup recovery receipts without production side effects.
- Added S2PLT02 fail-closed live 2-day readiness precheck for the 2 natural day / 8 M1-M4 real-email requirement without starting live operation, SMTP, scheduler, Release, schema, DB, queue, source adapter, ranking, CURRENT, or V7 contract side effects.
- Added owner-center entry governance rule requiring shallow GitHub-rendered `用户中心` pages as the primary owner-readable surface, with local `.adp` runtime files treated as evidence only.
- Added shallow GitHub user-center total candidate pool disclosure: 299 total candidates, 30 report/mail-preview index entries, 269 pending candidates, public ranking formula/weights, and regression tests; no production side effects.
- Added S2PMT01 A-020 local supply-chain machine gate for workflow permissions, GitHub Action references, and high/critical vulnerability exception approvals without production side effects.
- Added S2PMT01/S2PMT07 A-020 SBOM and CI enforcement refresh: deterministic local SBOM summary, project-governance A-020 security-boundary test gate, and finding-level technical review candidate evidence without closing P1/P0 or enabling production.
- Added S2PMT06 C-005 dedicated recoverable-error evidence and S2PMT07 P1 receipt refresh without closing P1 or enabling production side effects.
- Added S2PMT06 C-006/C-007 dedicated safe-config and append-only audit evidence with S2PMT07 P1 receipt refresh, without closing P1 or enabling production side effects.
- Recorded `S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE` to aggregate all eight inherited P0 finding-level technical review receipts while preserving P0=8/P1=37, final S2PMT07 blockers, and all no-production boundaries.
- Recorded `S2PMT07-P1-A006-A009-TECHNICAL-REVIEW` to mark A-006/A-007/A-008/A-009 as finding-level technical closure candidates while preserving P0=8/P1=37 and all no-production boundaries.
- Added `S2PMT07-FINAL-ACCEPTANCE-BUNDLE-READINESS` as a fail-closed final acceptance bundle readiness sub-gate that lists required final bundle evidence while preserving P0=8/P1=37, no final bundle, no production side effects, and no integrated production acceptance.
- Added S2PLT03 local no-production resilience drill bundle evidence while preserving S2PLT02/P0/P1/S2PLT04/S2PMT07 blockers and all production stop gates.
- Added S2PMT07 S2PLT04 completion report validator for future `FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json` payloads while preserving missing-report, missing-final-bundle, P0=8/P1=37, no-production, and no-integrated-acceptance blockers.
- Added S2PMT07 independent final reviewer assignment artifact validator for future `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` payloads while preserving missing-artifact, missing-reviewer, P0=8/P1=37, no-production, and no-integrated-acceptance blockers.
- Added local daily resend recovery support for `--daily-input-report`, allowing M1-M4 catch-up to reuse an existing same-day `adp-daily-input-report.json` without live arXiv fetch, with date-mismatch blocking and no production acceptance claim.
- Added S2PMT07 directory-level final bundle artifact validation while preserving missing-final-bundle, P0=8/P1=37, no-production, and no-integrated-acceptance blockers.
- Added S2PLT02 partial real delivery evidence binding for the recorded 2026-06-28 M1-M4 resend: one observed real natural day and four observed emails now feed the two-day precheck, while S2PLT02 acceptance and production gates remain blocked.
- Added S2PMT07 independent final reviewer assignment owner packet while preserving missing assignment artifact, P0=8/P1=37, no-production, and no-integrated-acceptance blockers.
- Added S2PMT07 final bundle committed artifact consumption so readiness consumes committed final-bundle artifacts through nested validators while preserving missing-final-bundle, P0=8/P1=37, no-production, and no-integrated-acceptance blockers.
