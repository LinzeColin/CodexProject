# DEVELOPMENT_LEDGER

Project: `arxiv-daily-push`
Active product version: `0.23.0`
Governance spec version: `1.0.0`

The append-only machine record is `development_events.jsonl`.

## Current State

- Product version: 0.23.0
- Current phase: S2PG
- Current gate: S2PGT01_EVIDENCE_PACKET_V2_COMPATIBILITY_READY_NO_PRODUCTION
- Confirmed iteration count: 96
- Reconstructed event count: 0
- Current task: `S2PGT01` has completed private EvidencePacket V2 compatibility evidence after S2PFT05. It validates D1-D4 source-domain report inputs, required packet fields, evidence-level labels, explicit old arXiv/D1 compatibility, and no-production/no-schema side-effect gates without public schema migration or D4 adapter implementation. `S2PHT01V1.1-T05` has verified that PR #152 merged the EMAIL_LEARNING_V1 M1-M4 renderer into main; S2PGT01 does not modify mail runtime paths. Stage 1 B1/arXiv remains `ARXIV_PRODUCTION_ACCEPTED`; V7.2 is the current product contract and requires all active/completed Stage2 agents to re-review completed work against V7.2 before new work.
- Blockers: No S1P5T03-R delivery blocker remains after GitHub Actions run `28027759062` uploaded artifact `7821452823` and passed 30/30 real historical as-of replay gates. Test10 (`28059194999`) proved the post-merge controlled Gmail SMTP path. `ADP-S1P5T05` prepared local Mac + Codex/local runner operation with state-dir queue/ledger/report/email evidence and launchd package draft. V7.2 contract baseline migration blockers are zero, but real restore, real SMTP production, scheduler installation, and final integrated production acceptance remain forbidden until V7.2 production stop gates, required P0/P1 remediation, and `S2PMT07` independent review pass. GitHub cloud scheduled production remains disabled and is not the daily production runner; `INTEGRATED_PRODUCTION_ACCEPTED` is not claimed.

## Phase Matrix

| Phase | Name | Status | Exit criteria | Evidence |
|---|---|---|---|---|
| A | Phase 1 repository foundation | completed | CLI skeleton, governance records, and tests pass | `docs/phase_records/PHASE_01.md` |
| B | Data contracts and arXiv source/ranking | completed | generic schemas and arXiv adapter/ranking gates pass | `docs/phase_records/PHASE_02.md`; `docs/phase_records/PHASE_03.md`; `docs/phase_records/PHASE_04.md` |
| C | Evidence and text lesson | completed | Claim Ledger and lesson verification pass | `docs/phase_records/PHASE_05.md`; `docs/phase_records/PHASE_06.md` |
| D | TTS/video/local pipeline/GitHub automation | completed | media gates, daily pipeline, and handoff gate pass | `docs/phase_records/PHASE_07.md`; `docs/phase_records/PHASE_08.md`; `docs/phase_records/PHASE_09.md`; `docs/phase_records/PHASE_10.md` |
| E | Weekly/monthly trial, all-arXiv queue delivery, and production handoff | completed | Phase 11 production gates plus Phase 12 all-arXiv scan, candidate queue, ROI ranking, daily lead, text-only teaching email gate, and production blockers documented | `docs/phase_records/PHASE_11.md`; `docs/phase_records/PHASE_11_TRIAL_EVIDENCE_VALIDATOR.md`; `docs/phase_records/PHASE_11_PRODUCTION_PREFLIGHT.md`; `docs/phase_records/PHASE_11_LIVE_ARXIV_INGEST.md`; `docs/phase_records/PHASE_11_SMTP_DELIVERY.md`; `docs/phase_records/PHASE_11_RELEASE_DELIVERY.md`; `docs/phase_records/PHASE_11_PRODUCTION_SCHEDULER.md`; `docs/phase_records/PHASE_11_SCHEDULED_EXECUTION_DRIVER.md`; `docs/phase_records/PHASE_11_DAILY_INPUT_BUILDER.md`; `docs/phase_records/PHASE_11_TRIAL_LEDGER_UPDATE.md`; `docs/phase_records/PHASE_11_TRIAL_LEDGER_STATE.md`; `docs/phase_records/PHASE_11_TRIAL_OPS_EVIDENCE.md`; `docs/phase_records/PHASE_11_TRIAL_REPLAY_EVIDENCE.md`; `docs/phase_records/PHASE_11_TRIAL_RECOVERY_EVIDENCE.md`; `docs/phase_records/PHASE_11_TRIAL_RESOURCE_EVIDENCE.md`; `docs/phase_records/PHASE_11_TRIAL_START_GATE.md`; `docs/phase_records/PHASE_11_TRIAL_START_WORKFLOW.md`; `docs/phase_records/PHASE_11_PRODUCTION_LAUNCH_READINESS.md`; `docs/phase_records/PHASE_11_POST_MERGE_LAUNCH_AUDIT.md`; `docs/phase_records/PHASE_11_PRODUCTION_REFS_READINESS.md`; `docs/phase_records/PHASE_11_PRODUCTION_REFS_TEMPLATE.md`; `docs/phase_records/PHASE_11_PRODUCTION_REFS_GITHUB_DISCOVERY.md`; `docs/phase_records/PHASE_11_TRIAL_START_LAUNCH_PREFLIGHT.md`; `docs/phase_records/PHASE_11_PROVISIONING_AUDIT_WORKFLOW.md`; `docs/phase_records/PHASE_11_PROVISIONING_AUDIT_REVIEW.md`; `docs/phase_records/PHASE_11_TWO_DAY_SIMULATION.md`; `docs/phase_records/PHASE_12_ALL_ARXIV_QUEUE_DELIVERY.md` |
| S1-A | Review8 V5 Stage 1 Window A | completed | Baseline lock, owner controls, unified local data model, arXiv connector contract, queue/content ledger, B1 report/email text interface, runtime recovery, migration package, post-migration bootstrap, 30 historical B1 previews, live arXiv preflight, controlled SMTP refs, accelerated real-arXiv acceptance artifact, test10 SMTP proof, and local production/migration prep within Stage 1 limits | `docs/pursuing_goal/BASELINE_LOCK.md`; `docs/phase_records/PHASE_S1_11_HISTORICAL_B1_PREVIEWS.md`; `docs/phase_records/PHASE_S1_12_LIVE_PREFLIGHT.md`; `governance/run_manifests/ADP-S1P5T04-ARXIV-PRODUCTION-ACCEPTED-20260623.json`; `governance/run_manifests/ADP-S1P5T05-LOCAL-PRODUCTION-AND-MIGRATION-PREP-20260624.json` |
| S2PA | V7.2 current product contract, V7.1 read-only inheritance, and V1.1 compatibility lock | completed | V7.2 root lock, CURRENT pointer, migration matrix, final three-agent review, AGENTS updates, three-base visibility, and validator/test enforcement without Stage 2 production acceptance; PR CI remains the merge attestation | `docs/pursuing_goal/CURRENT.yaml`; `docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml`; `docs/pursuing_goal/v7_2/machine_readable/product_contract_v7_2.yaml`; `docs/pursuing_goal/v7_2/AUDIT/final_review_matrix.yaml` |
| S2PB | V7.2-inherited D1 research/preprint source domain | in_progress | Promote bioRxiv and medRxiv through source-level shadow gates without regressing accepted arXiv local production, after V7.2 agent revalidation | `docs/pursuing_goal/v7_2/machine_readable/roadmap_v7_2.yaml`; `governance/run_manifests/ADP-S2PBT01-REAL-REPLAY-SHADOW-EVIDENCE-20260624.json`; legacy alias `S2P1T01` |
| S2PC | V7.2-inherited D2 top-journal source domain | in_progress | Continue from completed S2PCT01 Nature metadata-only shadow foundation to S2PCT02 Science without D2 source-domain acceptance or production inclusion, after V7.2 agent revalidation | `docs/pursuing_goal/v7_2/machine_readable/roadmap_v7_2.yaml`; `governance/run_manifests/ADP-S2P2T01-TOP-JOURNAL-SHADOW-FOUNDATION-20260624.json`; `https://github.com/LinzeColin/CodexProject/pull/119`; next `S2PCT02` |
| S2PF | V7.2-inherited D3 China local and extended official-source coverage | completed_local_validation | S2PFT01-S2PFT05 now cover mainland provincial templates, Hong Kong/Macau profiles, key cities, special zones, and full D3 governance qualification without formal production inclusion | `governance/run_manifests/ADP-S2PFT05-D3-FULL-GOVERNANCE-QUALIFICATION-20260625.json`; `docs/phase_records/PHASE_S2PFT05_D3_FULL_GOVERNANCE_QUALIFICATION.md` |
| S2PG | Unified evidence backbone, knowledge graph, and source-to-reading routing | in_progress | `S2PGT01` private EvidencePacket V2 compatibility is complete; continue later S2PG graph/routing work without silently migrating public schema or production queues | `docs/phase_records/PHASE_S2PGT01_EVIDENCE_PACKET_V2_COMPATIBILITY.md`; `governance/run_manifests/ADP-S2PGT01-EVIDENCE-PACKET-V2-COMPATIBILITY-20260625.json` |
| S2P1 | Review8 V6 source promotion | in_progress | Promote bioRxiv and medRxiv through source-level gates without regressing accepted arXiv local production | `docs/pursuing_goal/ARXIV_DAILY_PUSH_TWO_STAGE_ROADMAP_V6.md`; `docs/phase_records/PHASE_S2P1T01_PREPRINT_SOURCE_PROMOTION.md`; `governance/run_manifests/ADP-S2P1T01-PREPRINT-SOURCE-PROMOTION-20260624.json` |

## Iteration Records

### `ITER-20260625-ADP-S2PG-S2PGT01-EVIDENCE-PACKET-V2-COMPATIBILITY`

- Date: 2026-06-25
- Fact level: EXTRACTED from S2PGT01 compatibility code, focused packet fixtures, model/formula/parameter registry diff, and local S2PGT01 validation.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 032319edd56243f3c6887c7c707e00c91fdd733d
- Result commit: PENDING
- Phase: S2PG
- Task IDs: `S2PGT01`; acceptance `ACC-S2PGT01-EVIDENCE-V2`
- Goal: Define a private EvidencePacket V2 compatibility layer across D1-D4 source-domain reports, required packet fields, evidence-level labels, old arXiv compatibility, and no-production/no-schema side-effect gates.
- Files changed: S2PGT01 report builder/validator, CLI command, focused tests, phase record, run manifest, model/formula/parameter registries, traceability, delivery tasks, events, rendered governance inputs, and this ledger entry.
- Model changes: Added `MOD-ADP-070` for S2PGT01 EvidencePacket V2 compatibility.
- Formula changes: Added `FORM-ADP-072` with machine-verifiable AST fingerprints bound to the S2PGT01 implementation.
- Parameter changes: Added `PARAM-ADP-508` through `PARAM-ADP-515` for S2PGT01 model id, acceptance id, task id, packet version, required source domains, evidence levels, packet fields, and report filename.
- Commands run: `py_compile`; focused Stage2 source tests; semantic extractor.
- Test results: py_compile PASS; focused Stage2 source tests 71 OK; semantic extractor checked 72 formulas / 498 parameters. Final full ADP unittest, V7.2 validator, project governance, lean render, changed-only validation, parse checks, and diff checks remain pending before PR.
- Decisions: `ACC-S2PGT01-EVIDENCE-V2` is accepted only as private compatibility evidence. It does not implement D4 adapters, migrate public schema, mutate production queues, send SMTP, enable schedules, upload Releases, edit V7.2 contracts, or claim Stage 2/integrated production acceptance.
- Remaining risks: Later S2PG tasks still need knowledge graph and B1-B6 routing work. D4 source-domain implementation remains owned by S2PE/S2PET tasks and must not be implied by this compatibility layer.
- Rollback: Revert S2PGT01 code, tests, governance registrations, phase record, manifest, events, rendered governance sync, and this ledger entry; no runtime or production state was changed.
- Evidence: `arxiv-daily-push/docs/phase_records/PHASE_S2PGT01_EVIDENCE_PACKET_V2_COMPATIBILITY.md`; `governance/run_manifests/ADP-S2PGT01-EVIDENCE-PACKET-V2-COMPATIBILITY-20260625.json`; `arxiv-daily-push/docs/governance/delivery_tasks.yaml`.
- Next step: Run final validation, commit, push, and open PR for S2PGT01; then continue the next S2PG graph/routing task only under V7.2 no-production boundaries.

### `ITER-20260625-ADP-S2PF-S2PFT05-D3-FULL-GOVERNANCE-QUALIFICATION`

- Date: 2026-06-25
- Fact level: EXTRACTED from S2PDT04 and S2PFT01-S2PFT04 receipts, D3 governance fixture rows, model/formula/parameter registry diff, and local S2PFT05 validation.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: f48c8a8d5e247e156b6e416f81bbc0eb9022dc31
- Result commit: PENDING
- Phase: S2PF
- Task IDs: `S2PFT05`, legacy alias `S2P5T05`; next task `S2PGT01`
- Goal: Complete full D3 China official-source governance qualification after C0-C4 coverage, register S2PFT05 governance entries, and preserve V7.2 no-production boundaries.
- Files changed: S2PFT05 report builder/validator, CLI command, focused tests, phase record, run manifest, model/formula/parameter registries, traceability, delivery tasks, events, rendered governance inputs, three Chinese entry files, and this ledger entry.
- Model changes: Added `MOD-ADP-069` for S2PFT05 D3 full governance qualification.
- Formula changes: Added `FORM-ADP-071` with machine-verifiable AST fingerprints bound to the S2PFT05 implementation.
- Parameter changes: Added `PARAM-ADP-498` through `PARAM-ADP-507` for S2PFT05 model id, acceptance id, task ids, required components, required quota roles, governance gates, replay count, health tiers, and report filename.
- Commands run: `py_compile`; focused Stage2 source tests; semantic extractor; project dashboard generation.
- Test results: py_compile PASS; focused Stage2 source tests 67 OK; semantic extractor checked 71 formulas / 490 parameters; generator PASS. Final full ADP unittest, V7.2 validator, project governance, lean render, changed-only validation, parse checks, and diff checks remain pending before PR.
- Decisions: `ACC-S2PFT05-D3-FULL` is accepted only as local D3 governance qualification evidence. Formal D3 production inclusion, Stage 2 production acceptance, integrated production acceptance, SMTP, Release upload, GitHub production schedule, public schema migration, queue/schema mutation, mail production, and Email V1 production operation all remain false/disabled.
- Remaining risks: S2PGT01 EvidencePacket V2 is a potential public-schema boundary and must prove backward compatibility before any schema or production queue change. Inherited V7.1 P0=8/P1=37 and S2PMT07 still block any production acceptance claim.
- Rollback: Revert S2PFT05 code, tests, governance registrations, phase record, manifest, events, rendered governance sync, three Chinese entry-file updates, and this ledger entry; no runtime or production state was changed.
- Evidence: `arxiv-daily-push/docs/phase_records/PHASE_S2PFT05_D3_FULL_GOVERNANCE_QUALIFICATION.md`; `governance/run_manifests/ADP-S2PFT05-D3-FULL-GOVERNANCE-QUALIFICATION-20260625.json`; `arxiv-daily-push/docs/governance/delivery_tasks.yaml`.
- Next step: Run final validation, commit, push, and open PR for S2PFT05; then continue `S2PGT01` only after reading V7.2 and the S2PFT05 receipt.

### `ITER-20260625-ADP-S2PH-EMAIL-V1-MAIN-MERGE-STATUS`

- Date: 2026-06-25
- Fact level: EXTRACTED from GitHub PR #152 merge state, `origin/main@1cdad3d9e41f4543b06f158157f35878a30dbc93`, GitHub Actions success checks, Email V1 source/test scans, and governance-only post-merge status sync.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 1cdad3d9e41f4543b06f158157f35878a30dbc93
- Result commit: 69ceda49a4dd840039d32910c3f400dc0aba7c24
- Task IDs: `S2PHT01V1.1-T05`; references `S2PHT01V1.1-T02`, `S2PHT01V1.1-T03`, `S2PHT01V1.1-T04`
- Goal: Record that the EMAIL_LEARNING_V1 renderer is merged to main, remove stale local-validation/PR-pending wording, and preserve no-production-side-effect boundaries for later Stage2 work.
- Assumptions: This is a governance/status sync only; the runtime implementation was merged by PR #152 and no mail production code is changed in this iteration.
- Files changed: governance status matrix, delivery task record, append-only development event, run manifest, changelog, generated governance views, and this ledger.
- Model changes: None in this status sync. `MOD-ADP-037` was already updated by the merged Email V1 renderer PR.
- Formula changes: None in this status sync. `FORM-ADP-039` was already updated by the merged Email V1 renderer PR.
- Parameter changes: None in this status sync. Email V1 parameter bindings were already updated by the merged PR.
- Commands run: GitHub PR #152 merge and Actions inspection; `git fetch origin main`; `git diff --stat origin/main HEAD`; `git grep` Email V1 source/test bindings on `origin/main`; old V2/helper source scan on `origin/main`; generated governance dashboard sync; V7.2 contract validator; ADP project governance validator; changed-only governance with semantic checks; lean check-render; JSON/JSONL/YAML/manifest parse checks; `git diff --check`.
- Test results: PR #152 merged to main at `1cdad3d9e41f4543b06f158157f35878a30dbc93`; GitHub Actions on `ee3cecb7891ee63214b244dbb7e8b7f8fb6c0b2a` passed Project Governance run `28134309934`, Stage 1 bootstrap run `28134309925`, real 30-day backfill run `28134309930`, and live all-ArXiv cloud dry-run run `28134309943`; `origin/main` source/test scan confirms Email V1 bindings; old V2 template/helper scan has no matches; generated governance dashboard sync PASS; V7.2 contract validator PASS; ADP project governance errors 0 warnings 0; changed-only governance semantic errors 0 warnings 0; lean check-render drift 0 reference issues 0; JSON/JSONL/YAML/manifest parse OK; `git diff --check` PASS.
- Decisions: Treat M1-M4 as bound to EMAIL_LEARNING_V1 for the audited current paths on `main`; future mail entrypoints must pass the same Email V1 contract/readiness gate before they can be considered compliant.
- Remaining risks: Live SMTP, scheduler enablement, Release upload, production restore, and integrated production acceptance remain blocked by V7.2 gates; this status sync does not send email or enable production.
- Rollback: Revert only this governance/status sync commit; do not revert PR #152 unless the owner explicitly abandons Email V1.
- Next step: Commit, push, open PR, wait for CI, merge the governance sync, and notify the Stage2 main development thread.

### `ITER-20260625-ADP-S2PH-EMAIL-V1-T02-T04-RENDERER`

- Date: 2026-06-25
- Fact level: EXTRACTED from `mail_templates.py`, audited daily/B1/local/scheduled/shadow email paths, V7.2 Email Learning V1 overlay, model/formula/parameter registry diff, focused renderer tests, semantic extractor output, phase record, and run manifest.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 17a8a88421dbd8fef97c4286fa8563c327978b1b
- Result commit: 1cdad3d9e41f4543b06f158157f35878a30dbc93 via PR #152
- Task IDs: `S2PHT01V1.1-T02`, `S2PHT01V1.1-T03`, `S2PHT01V1.1-T04`
- Goal: Implement the V7.2/V1.1 EMAIL_LEARNING_V1 renderer and route audited M1-M4 email paths through the unified content object, HTML/plain template, ChatGPT new-chat link, and fail-closed visible marker gate.
- Assumptions: This changes private mail rendering and readiness gates only; it does not claim integrated production acceptance or enable live operations.
- Files changed: `mail_templates.py`, daily delivery and B1 email builders, local/scheduled readiness gates, Stage2 shadow preview tests, renderer tests, phase record, run manifest, model/formula/parameter registries, delivery plan/tasks, traceability, and this ledger.
- Model changes: Updated `MOD-ADP-037` to the private EMAIL_LEARNING_V1 renderer and routed audited mail package builders/readiness gates through it.
- Formula changes: Updated `FORM-ADP-039` to describe EMAIL_LEARNING_V1 M1-M4 rendering; refreshed affected AST fingerprints/evidence hashes for current daily/manual/B1 paths.
- Parameter changes: Rebound `PARAM-ADP-276` through `PARAM-ADP-279` and `PARAM-ADP-313` to Email V1 contract id, template version, M1-M4 product ids, forbidden visible marker count, and V1 subject contract.
- Commands run: py_compile; focused email-chain unittest; full ADP unittest; semantic extractor; project governance; changed-only governance with semantic checks; V7.2 contract validator; lean check-render; JSON/JSONL/YAML/CSV parse checks; old V2 template/helper scan; `git diff --check`.
- Test results: py_compile PASS; focused email-chain unittest 80 OK; full arxiv-daily-push unittest 280 OK after rebasing onto `origin/main`; semantic extractor checked 67 formulas and 451 parameters; project governance errors 0 warnings 0; changed-only governance semantic errors 0 warnings 0; V7.2 contract validator PASS; lean check-render drift 0 reference issues 0; JSON/JSONL/YAML/CSV parse OK; old V2 template/helper scan no matches; `git diff --check` PASS. Root governance full unittest was attempted before rebase and still had unrelated cross-project Review9/Alpha/EEI historical failures, so it is not used as this ADP PR acceptance gate.
- Decisions: Current daily delivery, B1 report email, local runner preview, scheduled readiness gate, and Stage2 shadow previews now require `EMAIL_LEARNING_V1` metadata and M1-M4 product ids. Old V2 visible markers and old daily email helper names are blocked by tests and source scan.
- Remaining risks: Live SMTP/scheduler/Release/integrated production acceptance remain blocked by V7.2 gates; new future mail entrypoints must be reviewed against the Email V1 gate before use.
- Rollback: Revert PR #152 if and only if the owner explicitly abandons Email V1; no data migration is required.
- Next step: Record post-merge governance status, then allow no-conflict Stage2 work to continue under V7.2 gates.

### `ITER-20260624-ADP-S2PA-V7-2-CURRENT-CONTRACT`

- Date: 2026-06-24
- Fact level: EXTRACTED from V7.1 repository contract hashes, owner-provided V1.1 task pack hash, V7.1/V1.1 reaudit report hash, T00 three-agent compatibility audit, and V7.2 final review matrix.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 4cb9344
- Result commit: PENDING
- Task IDs: `S2PAT06`, `S2PHT01V1.1-T00`; contextual next `S2PHT01V1.1-T01`; global next `S2PCT02`
- Goal: Publish V7.2 as the CURRENT product contract, preserve V7.1 as read-only history, merge valid V7.1 requirements with V1.1 EMAIL_LEARNING_V1 increments, and require all Stage2 agents to revalidate completed work against V7.2 before new work.
- Assumptions: V1.1 is an incremental input, not a replacement for V7.1; visible email-frontstage changes are separated from backend evidence, review, action, ROI and Delta ledgers.
- Files changed: V7.2 pursuing-goal package, `CURRENT.yaml`, ADP `AGENTS.md`, three base files, governance status/owner/version/assurance views, delivery plan/tasks, roadmap, project summary, validator/tests, and this event record.
- Model changes: None. This is a product-contract and governance baseline publication; production email code, public schema, SMTP, Release, scheduler, and Stage2 implementation code are unchanged.
- Formula changes: None.
- Parameter changes: None.
- Commands run: V7.2 contract validator; V7.2 contract unittest; ADP project governance validator; changed-only governance with semantic checks against `origin/main`; lean governance changed-only validation; semantic extractor; lean render check; `py_compile`; `git diff --check`; root governance full unittest.
- Test results: V7.2 contract validator PASS; V7.2 contract unittest 4 OK; ADP project governance errors 0 warnings 0; changed-only governance with semantic errors 0 warnings 0; lean check-render drift 0 reference issues 0; semantic extractor checked 54 formulas and 364 parameters; `py_compile` PASS; `git diff --check` PASS; root governance full unittest has unrelated non-ADP legacy failures while ADP targeted tests pass.
- Decisions: `ADP-PRODUCT-CONTRACT-V7.2` is the single CURRENT product contract on this branch; V7.1 remains read-only and hash-checked; `S2PHT01V1.1-T01` is the next email V1 read-only path audit; no-conflict `S2PCT02` Science metadata-only shadow may continue after recording V7.2 revalidation.
- Remaining risks: PR CI and final reviewer agents must still confirm no drift; any later EMAIL_LEARNING_V1 implementation must not modify production email code or public schema before T01/T02 gates.
- Rollback: Revert V7.2 directory, `CURRENT.yaml`, V7.2 governance status edits, validator/test changes, and this S2PAT06 record; V7.1 files remain untouched.
- Next step: Run V7.2 validator, project governance validator, semantic validator, lean render check, git diff check, and three-agent final review before PR.

### `ITER-20260624-ADP-S2PA-V7-1-PARALLEL-AUDIT-ROOT-LOCK`

- Date: 2026-06-24
- Fact level: EXTRACTED from owner-provided V7.1 package, parallel audit summary, repository `origin/main@ffa5ac76bc7b08a1ea2a4c925cf481017d10e6e0`, Stage 1 accepted-state evidence, and this branch's root-governance diff.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: ffa5ac76bc7b08a1ea2a4c925cf481017d10e6e0
- Result commit: PENDING
- Task IDs: `S2PAT05`, `S2PBT01`, legacy alias `S2P1T01`
- Goal: Lock V7.1 root governance and parallel-audit production blockers while preserving `ARXIV_PRODUCTION_ACCEPTED` and preventing any accidental `INTEGRATED_PRODUCTION_ACCEPTED` claim.
- Assumptions: The downloaded V7.1 package is the owner-approved source package; repository lock status is recorded separately in `V7_1_ROOT_LOCK.yaml` so original contract hashes remain reproducible.
- Files changed: root `AGENTS.md`, ADP `AGENTS.md`, V7.1 pursuing-goal package files, `V7_1_ROOT_LOCK.yaml`, three base files, `VERSION_MATRIX.yaml`, `delivery_tasks.yaml`, this ledger, event record, run manifest, governance validator/tests, and dashboard generation overlay.
- Model changes: None. V7.1 lock is a governance/product/audit contract, not a model/formula/parameter behavior change.
- Formula changes: None.
- Parameter changes: None.
- Commands run: pending final validation in this PR.
- Test results: pending final validation in this PR.
- Decisions: `ARXIV_PRODUCTION_ACCEPTED` is maintained; Stage 2 source work may continue in shadow as `S2PBT01` with legacy alias `S2P1T01`; `S2PMT07 -> INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION` remains the only final production gate; P0/P1 audit findings forbid real restore, real SMTP production, scheduler installation, and final integrated acceptance while open.
- Remaining risks: P0/P1 remediation remains outside this root-governance task; S2PBT01 no-send evidence must not be interpreted as production SMTP or formal source inclusion.
- Rollback: Revert V7.1 package import, lock file, AGENTS edits, three-base updates, validator/test additions, this iteration/event, and run manifest; keep Stage 1 local runner evidence unchanged.
- Next step: Run changed-only governance, semantic validator, root governance unit tests, lean check-render, and diff checks before PR.

### `ITER-20260624-ADP-S2PBT01-REAL-REPLAY-SHADOW-EVIDENCE`

- Date: 2026-06-24
- Fact level: EXTRACTED from local no-send real replay output, compact run manifest, and S2P1/S2PBT alias constraint.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 6f4d1124efe072ec6324c5f7cada65c7d6f44e0d
- Result commit: PENDING
- Task IDs: `S2PBT01`, `S2P1T01`
- Goal: Run real historical bioRxiv/medRxiv replay through the no-send shadow path and persist compact evidence while preserving V7 production constraints.
- Assumptions: Legacy `S2P1T01` is alias `S2PBT01`; this evidence may support source-level progression but cannot claim `INTEGRATED_PRODUCTION_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, or formal production inclusion.
- Files changed: S2P1 phase record, task record, owner-facing files, real replay manifest, and governance event records.
- Model changes: No new model beyond `MOD-ADP-050`.
- Formula changes: No new formula beyond `FORM-ADP-052`.
- Parameter changes: No new parameter beyond `PARAM-ADP-372` through `PARAM-ADP-376`.
- Commands run: local no-send `stage2-preprint-replay-shadow` through `arxiv_daily_push.cli.main(...)` with `state_dir=/tmp/adp_s2p1_replay_real_20260624/state`, `start_date=2024-01-01`, `count=30`, `lookback_days=14`, `max_records=10`, `fetcher=curl`, and no production side-effect flags.
- Test results: replay status pass; success_count 30/30; unique_date_count 30; real_preprint_source_id_count 30; duplicate_selected_count 0; duplicate_canonical_count 0; future_leakage_count 0; queue_continuity_break_count 0; P0/P1 0; shadow_hours 720.0.
- Successes: The real no-send replay wrote queue, ledger, replay report, 48h shadow report, promotion report, and email previews to `/tmp`; compact Git evidence is stored at `governance/run_manifests/ADP-S2PBT01-REAL-REPLAY-SHADOW-EVIDENCE-20260624.json`.
- Failures: None in the no-send replay evidence path.
- Decisions: Do not commit the 46M temporary artifact tree; keep only the compact evidence manifest and hashes. Do not enable SMTP, Release, GitHub schedule, video, PDF/full-text, or formal source inclusion.
- Remaining risks: V7 root contract and CI hash gate are still external blockers; any V6/V7 naming or contract conflict must be marked `R-CONFLICT` or `CONTRACT-HASH-MISMATCH`.
- Rollback: Remove the real replay manifest and this governance sync; no production config or Stage 1 accepted state changes are needed.
- Next step: Wait for or reconcile V7 route-lock governance, then decide whether the passed no-send real replay evidence can support source-level progression.

### `ITER-20260624-ADP-S2P1T01-REPLAY-SHADOW-GOVERNANCE-SYNC`

- Date: 2026-06-24
- Fact level: EXTRACTED from changed-only governance feedback, regenerated assurance status, and S2P1T01 PR diff coverage.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 6f4d1124efe072ec6324c5f7cada65c7d6f44e0d
- Result commit: PENDING
- Task IDs: `S2P1T01`
- Goal: Synchronize the replay/shadow builder work with the full PR diff from `origin/main` so the latest event covers all S2P1T01 changed files.
- Assumptions: This is governance sync only; it does not complete S2P1T01 or enable any production side effect.
- Files changed: latest development event coverage, `VERSION_MATRIX.current_iteration`, regenerated assurance/status owner views, and existing S2P1T01 governance records.
- Model changes: No new model beyond `MOD-ADP-050`.
- Formula changes: No new formula beyond `FORM-ADP-052`.
- Parameter changes: No new parameter beyond `PARAM-ADP-372` through `PARAM-ADP-376`.
- Commands run: focused S2P1 tests, full ADP tests, semantic extractor, schema JSON parse, and changed-only governance validation feedback loop.
- Test results: Focused S2P1 tests 41 OK; full ADP tests 218 OK; replay/shadow fixture tests 6 OK; semantic extractor checked 52 formulas and 359 active parameters.
- Decisions: Keep `S2P1T01` `in_progress`; durable real 30-date preprint replay and 48h shadow evidence remain the next gate.
- Remaining risks: Real replay/shadow evidence is not attached yet; Stage 2 production acceptance is not claimed.
- Rollback: Revert this governance sync event and restore `VERSION_MATRIX.current_iteration` to the previous S2P1T01 iteration if the replay/shadow builder is reverted.
- Next step: Run changed-only governance again, then run durable real replay/shadow evidence if local/API conditions permit.

### `ITER-20260624-ADP-S2P1T01-REPLAY-SHADOW-BUILDER`

- Date: 2026-06-24
- Fact level: EXTRACTED from S2P1 replay/shadow code, focused fixture tests, CLI wiring, semantic governance registration, and no-side-effect policy fields.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 6f4d1124efe072ec6324c5f7cada65c7d6f44e0d
- Result commit: PENDING
- Task IDs: `S2P1T01`
- Goal: Add the deterministic 30-date replay plus 48-hour shadow evidence builder required before bioRxiv/medRxiv source promotion can complete.
- Assumptions: Historical replay may be accelerated from real as-of dates rather than waiting 30 live days; S2P1 remains no-send and excluded from formal production until durable real replay/shadow evidence passes.
- Files changed: `stage2_sources.py`, CLI replay command, S2P1 replay tests, governance registries, model spec, delivery task record, phase record, owner-facing project records, and this ledger/event record.
- Model changes: Added `MOD-ADP-050` for S2P1T01 preprint replay and 48h shadow evidence.
- Formula changes: Added `FORM-ADP-052`; refreshed dependent S2P1 and CLI formula fingerprints.
- Parameter changes: Added `PARAM-ADP-372` through `PARAM-ADP-376` for replay/shadow report model IDs and output filenames.
- Commands run: focused `test_stage2_sources.py` replay/shadow fixture tests and semantic/governance registration preparation.
- Test results: Fixture-backed replay/shadow path passed 30 unique historical dates with queue/ledger/email persistence, no duplicate selected source/canonical IDs, no future leakage, no P0/P1 blockers, at least 48h shadow aggregate, and `stage2_production_accepted=false`.
- Successes: S2P1 now has a single command that can generate replay report, shadow 48h report, promotion report, queue state, ledger rows, and email previews in an explicit local `state_dir` without SMTP, Release, video, PDF, full-text, or scheduler side effects.
- Failures: Durable real 30-date replay against live bioRxiv/medRxiv historical data has not yet been attached, so `S2P1T01` remains `in_progress`.
- Decisions: Keep Stage 1 arXiv local runner as the accepted production path; keep GitHub cloud scheduled production disabled; do not claim `STAGE2_PRODUCTION_ACCEPTED`.
- Remaining risks: Live preprint API date windows may be sparse, drift, or select duplicate canonical DOIs; the next run must record real artifact paths and promotion-gate output before source promotion can pass.
- Rollback: Revert replay/shadow builder code, CLI command, tests, `MOD-ADP-050`, `FORM-ADP-052`, `PARAM-ADP-372..376`, this iteration/event, and related task/phase records.
- Next step: Run `stage2-preprint-replay-shadow` against real historical bioRxiv/medRxiv data, inspect the report, and only then decide whether `S2P1T01` can move from `in_progress` to completed.

### `ITER-20260624-ADP-S2P1T01-PREPRINT-SOURCE-PROMOTION`

- Date: 2026-06-24
- Fact level: EXTRACTED from official bioRxiv/medRxiv API docs, S2P1 adapter/gate/shadow code, focused tests, full ADP tests, schema parse, semantic governance validation, and live fixed-interval canaries.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: d328d5d76ff1ea519d59c5316f7497ba6ef03e2a
- Result commit: PENDING
- Task IDs: `S2P1T01`
- Goal: Add bioRxiv and medRxiv as disabled Stage 2 metadata-only preprint sources, prove bounded ingest and shadow daily behavior, and keep accepted Stage 1 arXiv local production unchanged.
- Assumptions: bioRxiv/medRxiv may only use the official public details JSON endpoint; S2P1 cannot count as accepted until both 30-date terminal replay and 48-hour shadow evidence pass; no preprint source may enter formal production in this iteration.
- Files changed: preprint adapter, S2P1 promotion/shadow logic, CLI commands, generic source contracts, global scan and lesson source labeling, source registry, owner controls, source schemas, focused tests/fixtures, governance registries, phase record, run manifest, and owner-facing project records.
- Model changes: Added `MOD-ADP-047`, `MOD-ADP-048`, and `MOD-ADP-049` for Stage 2 preprint ingest, S2P1 promotion gate, and S2P1 shadow daily path.
- Formula changes: Added `FORM-ADP-049`, `FORM-ADP-050`, and `FORM-ADP-051`; refreshed dependent formula fingerprints after implementation changes.
- Parameter changes: Added `PARAM-ADP-360` through `PARAM-ADP-371`; updated `SOURCE_TYPES` to include `preprint`.
- Commands run: focused S2P1/source/global/lesson/registry/contract tests; full `arxiv-daily-push` unittest discovery; schema JSON parse; semantic extractor validation; live `fetch-preprint-latest` curl canaries for bioRxiv and medRxiv; single live `stage2-preprint-shadow-daily` canary.
- Test results: 39 focused tests OK; 216 ADP tests OK; schema JSON parse PASS; semantic extractor checked 51 formulas and 354 active parameters; live bioRxiv canary selected `biorxiv:10.1101-2023.12.30.573731`; live medRxiv canary selected `medrxiv:10.1101-2023.10.21.23297352`; single shadow daily canary passed with selected source `medrxiv:10.1101-2023.10.21.23297352`.
- Successes: bioRxiv/medRxiv records map into generic `preprint` SourceItems; duplicate DOI and empty-window behavior fail closed; Stage 2 sources are present but disabled/zero-weight in owner controls; shadow daily writes separate queue, ledger, report, and email preview without SMTP, Release, video, or production inclusion.
- Failures: Local Python `urllib` live fetch was blocked by CA trust; the controlled live canary used the implemented `curl` fallback. The 30-date terminal replay and 48-hour shadow evidence have not run yet.
- Decisions: Keep Stage 1 arXiv local runner as the accepted production path; keep bioRxiv/medRxiv out of formal production; do not enable GitHub cloud scheduled production; do not send SMTP; do not upload Release assets; do not introduce video requirements.
- Remaining risks: Upstream preprint API shape or availability may drift; shadow evidence needs continuous local state validation; source promotion could still be blocked by replay duplicates, future leakage, P0/P1 evidence issues, or queue discontinuity.
- Rollback: Revert S2P1T01 adapter/gate/shadow code, tests, fixtures, governance records, phase record, and run manifest; keep Stage 1 arXiv local runner files unchanged.
- Next step: Run `S2P1T01_REPLAY_AND_48H_SHADOW_EVIDENCE`, then re-run the promotion gate before any Stage 2 acceptance claim.

### `ITER-20260624-ADP-S1P5T05-LOCAL-PRODUCTION-MIGRATION-PREP`

- Date: 2026-06-24
- Fact level: EXTRACTED from owner deployment decision, local runner code/tests, migration runbooks, and S1P5T05 manifest.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 699e717f38d0c08b4e6f627cb5ca57297b564f95
- Result commit: PENDING
- Task IDs: `ADP-S1P5T05-LOCAL-PRODUCTION-AND-MIGRATION-PREP`; next V6 task is `S2P1T01`
- Goal: Prepare Stage 1 local production daily-run and 2026-06-30 migration without enabling GitHub cloud scheduled production.
- Assumptions: Final runner strategy is local Mac + Codex/local runner; GitHub is code, PR/CI, evidence, status, and backup only; secrets stay in local env or Keychain-backed setup.
- Files changed: `local_runner.py`, CLI local-runner commands, scheduled execution local enablement flag, migration packaging, local runner tests, local and Stage 1 migration runbooks, governance task/event/status files, and S1P5T05 manifest.
- Model changes: Added Stage 1 local Codex runner orchestration and migration-prep model; no Stage 2 source adapter implemented yet.
- Formula changes: No ranking, ROI, queue scoring, source selection, email frontstage, or Stage 2 formula changed.
- Parameter changes: Added local daily-run enablement, state-dir queue/ledger/report/email evidence names, local SMTP secret-name policy, and launchd package label.
- Commands run: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s1p5t05_focus_now PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_local_runner.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_stage1_migration.py -q`
- Test results: 15 tests OK.
- Successes: local runner dry-run persists queue, content ledger, reports, and email previews; real SMTP path fails closed without env keys and passes with fake SMTP; write=false does not persist state; launchd package is generated but not installed.
- Failures: None in focused validation.
- Decisions: Keep GitHub cloud scheduled production disabled; do not install launchd or send real local SMTP in this task.
- Remaining risks: Owner-controlled local SMTP env/Keychain smoke and optional launchd install still need explicit execution; Stage 2 source gates are not implemented yet.
- Rollback: Revert local runner code, tests, runbooks, S1P5T05 manifest/event, and generated governance files.
- Next step: Start `S2P1T01` bioRxiv/medRxiv source promotion.

### `ITER-20260624-ADP-S1P5T04-POST-MERGE-TEST10-GATE-040`

- Date: 2026-06-24
- Fact level: EXTRACTED from GitHub PR #102, GitHub Actions workflow/run API, `origin/main` workflow YAML, scheduled workflow job statuses, and existing Stage 1 governance records.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 255442601540040b9d20f1493f4afd44a28f5b3a
- Result commit: PENDING
- Task IDs: `ADP-S1P5T04-POST-MERGE-TEST10-040`; current V6 task remains `S1P5T04`
- Goal: Advance Stage 1 from post-PR service-date correction to the exact controlled post-merge test10 gate without enabling production scheduling.
- Assumptions: test10 must run from `main`, leave `generated_at` empty, use `max_results_per_category=1`, send only one Gmail SMTP test email to `linzezhang35@gmail.com`, and preserve fail-closed production scheduling.
- Files changed: governance status, owner status, delivery plan/task records, development event, version matrix, dashboard decision policy, root governance test expectation, and this run manifest only.
- Model changes: No ranking, queue, report, email content, workflow, SMTP, Release, Stage 2, or video model changed.
- Formula changes: No formula expression changed.
- Parameter changes: No active parameter value changed.
- Commands run: GitHub API query for manual delivery workflow runs, scheduled workflow runs, scheduled job states, and PR #102 merge state; `origin/main` workflow inspection for `ZoneInfo("Australia/Sydney")`.
- Test results: PR #102 merged as `ef64ba2777b318cc0c2bafbf03e1f85b1caf4eaa`; PR CI runs `28057755238`, `28057755234`, `28057755254`, and `28057755244` completed success; manual workflow has runs 1 through 9 only; scheduled runs `28057072176`, `28056782115`, and `28056430312` had `scheduled` job conclusion `skipped`.
- Successes: `origin/main` contains the Sydney service-date conversion in manual and scheduled workflows; no post-merge test10 has been sent yet; production schedule remains fail-closed.
- Failures: Stage 1 still lacks the post-merge controlled test10 email evidence.
- Decisions: Keep production schedule disabled; next owner action is a single manual test10 trigger from `main`.
- Remaining risks: The owner could select a non-main ref, fill `generated_at`, or trigger duplicate manual runs; Codex must verify artifact fields after test10 before any production-schedule decision.
- Rollback: Revert this governance sync and return next task to `ADP-S1P5T04-SYDNEY-SERVICE-DATE-039`.
- Next step: Owner triggers test10, then Codex verifies run id, artifacts, subject date, SMTP sent state, and scheduled production disabled/skipped state.

### `ITER-20260624-ADP-S1P5T04-SYDNEY-SERVICE-DATE-039`

- Date: 2026-06-24
- Fact level: EXTRACTED from GitHub Actions manual test9 run `28056192503`, scheduled-execution artifact fields, workflow YAML, focused workflow tests, YAML parse checks, and date-conversion sample checks.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: ab2ec5eb15dd1b2c0f7f053b062e1bb61e4d3e4a
- Result commit: PENDING
- Task IDs: `ADP-S1P5T04-SYDNEY-SERVICE-DATE-039`; current V6 task remains `S1P5T04`
- Goal: Correct the Stage 1 cloud workflows so daily input/report/email dates use `Australia/Sydney` service date rather than the first 10 characters of a UTC timestamp.
- Assumptions: `generated_at` remains the audit timestamp; `date` is the human service date used for daily artifacts and subject lines. This task does not change ranking, queue, email template content, production enablement, SMTP authorization, Release upload, Stage 2, or video behavior.
- Files changed: manual delivery, scheduled production, trial start, and phase12 cloud dry-run workflows plus focused workflow tests and governance records.
- Model changes: No ranking, queue, report, or email content model changed.
- Formula changes: No formula expression changed; workflow date resolution now computes `datetime.fromisoformat(...).astimezone(ZoneInfo("Australia/Sydney")).date()` for service-date output.
- Parameter changes: No active parameter value changed.
- Commands run: focused workflow unit tests; full arxiv-daily-push unit test suite; Ruby YAML parse for four workflows; explicit date conversion samples including test9 timestamp; `git diff --check`.
- Test results: focused workflow tests returned 10 tests OK; full arxiv-daily-push suite returned 201 tests OK; YAML parse passed for the four changed workflows; sample `2026-06-23T20:51:43Z` converts to `2026-06-24` in `Australia/Sydney`; `git diff --check` passed.
- Successes: The manual delivery and scheduled paths can no longer use `${value:0:10}` or `${generated_at:0:10}` for service-date output; tests assert the Sydney timezone conversion contract.
- Failures: test9 itself used the pre-fix workflow, so it is delivery evidence only and not final human-date acceptance evidence.
- Decisions: Keep production schedule disabled; do not send another real email until this PR passes CI and is merged, then require a separate controlled test10 trigger.
- Remaining risks: PR CI and the next controlled email must prove the fixed workflow on GitHub/cloud runner; repository production variables remain fail-closed.
- Rollback: Revert the four workflow date-resolution blocks, the focused workflow assertions, and this governance sync.
- Next step: Open PR, wait for CI, merge if green, then ask owner before triggering test10.

### `ITER-20260623-ADP-PHASE12-EMAIL-HUMAN-FORMAT-036`

- Date: 2026-06-23
- Fact level: EXTRACTED from owner email-quality requirements, `global_scan.py`, focused renderer/scheduled-execution/SMTP notification tests, and governance task records.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 3922760a3153a98e42ec48fa19f7353010e83efb
- Result commit: PENDING
- Task IDs: `ADP-PHASE12-EMAIL-HUMAN-FORMAT-036`; current V6 task remains `S1P5T04`
- Goal: Convert the Stage 1 daily email frontstage into a Chinese teaching brief with higher information density and lower owner cognitive load.
- Assumptions: Stage 1 remains text-first; no video requirement, no GitHub Release reading entry, no production scheduler enablement, no new SMTP send, no Stage 2, and no ranking/queue algorithm change.
- Files changed: daily email renderer, focused email/scheduled execution tests, phase record, delivery task records, owner/status views, Chinese entry files, version matrix, this ledger, and development event.
- Model changes: No ranking model change. Frontstage rendering in `MOD-ADP-034` now hides ROI/Release/video/delivery-policy/backend wording from the owner email.
- Formula changes: No formula expression changed.
- Parameter changes: No active scoring parameter changed; frontstage visibility flags remain false.
- Commands run: focused email/scheduled/notification unit tests; full arxiv-daily-push unit test suite; semantic extractor; changed-only governance validation; root governance tests; git diff and cache hygiene checks.
- Test results: focused command returned 23 tests OK; `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_email_human_all PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q` returned 200 tests OK; semantic extractor checked 48 formulas and 342 parameters; changed-only governance validation returned errors 0 and warnings 0; root governance tests returned 154 tests OK; git diff check passed; cache check found no `__pycache__` or `.pyc` files under `arxiv-daily-push`, `tests`, or `scripts`.
- Successes: Plain-text and HTML emails now use teaching-first Chinese sections, no `class="score"` frontend marker, no visible `ROI score`, `roi_total_score`, `Release 资料包`, `GitHub Release`, `12秒视频`, `delivery policy`, `后台`, or `日报` wording in tested owner-facing bodies.
- Failures: PR CI and a controlled manual Gmail SMTP test remain pending.
- Decisions: Keep production schedule disabled; do not send a real email or enable production until PR CI is green and owner separately confirms the controlled test.
- Remaining risks: Live article titles or generated lesson text could still expose unforeseen formatting issues; the next proof must be PR CI plus a controlled email after approval.
- Rollback: Revert the `ADP-PHASE12-EMAIL-HUMAN-FORMAT-036` email renderer, tests, and governance records.
- Next step: Push PR, wait for CI, then ask before any controlled Gmail SMTP test.

### `ITER-20260622-S1-008`

- Date: 2026-06-22
- Fact level: EXTRACTED from `stage1_migration.py`, focused migration tests, runtime smoke primitives, semantic extractor, and governance registry updates.
- Version before: 0.18.0
- Version after: 0.19.0
- Base commit: b754ef7552e41b9e9d34d06afe625bb9b3e5711b
- Result commit: PENDING
- Task IDs: S1-09-MIGRATION_PACKAGE-001
- Goal: Add the Review8 Stage 1 migration package export and verification controls for a low-resource package, source-file hash inventory, SQLite/runtime smoke, backup manifest, restore drill, and secret-name-only checklist.
- Assumptions: S1-09 is a deterministic migration-readiness interface only; it does not enable production scheduling, send Gmail SMTP, upload GitHub Releases, generate video, run a 30-day replay, start background work, or claim `ARXIV_PRODUCTION_ACCEPTED`.
- Files read: S1-08 runtime controls, storage/database inspector, CLI, V5 baseline lock and task pack, previous S1 governance records, semantic extractor, and focused tests.
- Files changed: `stage1_migration.py`, migration CLI dispatch, focused migration tests, migration runbook, version files, changelog, model/formula/parameter registries, model spec, version matrix, traceability, delivery tasks, phase record, ledger/event records, generator S1 next-task policy, root governance test expectations, and run manifest.
- Model changes: Added MOD-ADP-042 `adp-stage1-migration-package-v1`.
- Formula changes: Added FORM-ADP-044 and refreshed FORM-ADP-024/FORM-ADP-042/FORM-ADP-043 fingerprints because `cli.py::main` gained migration subcommands.
- Parameter changes: Added PARAM-ADP-326 through PARAM-ADP-331 for migration schema, acceptance ID, package byte cap, required secret-name count, required source-path count, and package file count.
- Commands run: focused migration/runtime/CLI tests; version CLI; full arxiv-daily-push unit tests; semantic extractor; project governance; all-project governance; changed-only semantic governance; root governance tests; information quality validation; JSON manifest parse; diff/cache/CSV checks.
- Test results: focused migration/runtime/CLI tests 17 OK; version CLI returned 0.19.0; arxiv-daily-push unit tests 214 OK; semantic extractor checked 44 active formulas and 314 active parameters with no errors; project governance 0 errors 0 warnings; all-project governance 0 errors 0 warnings; changed-only semantic governance 0 errors 0 warnings; root governance tests 129 OK; information quality PASS errors 0 warnings 0.
- Successes: The migration surface writes only the explicit output directory, inventories source files by SHA256, inspects the Stage 1 SQLite database, runs low-resource runtime smoke, produces a backup manifest and restore checklist, verifies package hashes, scans outputs for obvious secret values, and blocks enabled production flags.
- Failures: No new machine or cloud runner bootstrap was executed in S1-09 by design; no real Gmail email, GitHub Release, video, 30 historical previews, or live production days were executed.
- Decisions: Bump product version to 0.19.0 because S1-09 adds a backward-compatible migration export/verify CLI and transfer contract while preserving disabled production side effects.
- Remaining risks: 30 historical previews, two live production days, and production trial evidence remain incomplete before `ARXIV_PRODUCTION_ACCEPTED`.
- Rollback: Remove `stage1_migration.py`, migration CLI dispatch/tests/runbook, restore version 0.18.0, and revert S1-09 governance records and run manifest.
- Next step: S1-11-HISTORICAL_B1_PREVIEWS-001.

### `ITER-20260622-S1-007`

- Date: 2026-06-22
- Fact level: EXTRACTED from `stage1_runtime.py`, focused runtime recovery tests, full ADP unit tests, semantic extractor, and governance registry updates.
- Version before: 0.17.0
- Version after: 0.18.0
- Base commit: 5f4995964164cd70c9222bbba974bfa0892853a0
- Result commit: PENDING
- Task IDs: S1-08-LOCAL_RUNTIME_RECOVERY-001
- Goal: Add the Review8 Stage 1 local runtime recovery controls for explicit tick heartbeat/checkpoint state, watchdog stale-state blocking, SQLite backup/restore with SHA256 manifest and explicit confirmation, runtime production-flag audit, and scheduler install/uninstall dry-run templates.
- Assumptions: S1-08 is a deterministic local recovery interface only; it does not install a real scheduler, enable production scheduling, send Gmail SMTP, upload GitHub Releases, generate video, run a 30-day replay, start background work, or claim `ARXIV_PRODUCTION_ACCEPTED`.
- Files read: `arxiv-daily-push/AGENTS.md`, V5 baseline lock and task pack, storage/database inspector, CLI, previous S1 governance records, semantic extractor, and focused tests.
- Files changed: `stage1_runtime.py`, runtime CLI dispatch, focused runtime tests, version files, changelog, model/formula/parameter registries, model spec, version matrix, traceability, delivery tasks, phase record, ledger/event records, generator S1 next-task policy, root governance test expectations, and run manifest.
- Model changes: Added MOD-ADP-041 `adp-stage1-local-runtime-recovery-v1`.
- Formula changes: Added FORM-ADP-043 and refreshed FORM-ADP-024/FORM-ADP-042 fingerprints because `cli.py::main` gained runtime recovery subcommands.
- Parameter changes: Added PARAM-ADP-316 through PARAM-ADP-325 for runtime schema, acceptance ID, action count, backup byte cap, stale heartbeat threshold, disabled production flag count, OS task count, scheduler platform list, heartbeat filename, and lock filename.
- Commands run: focused runtime recovery plus CLI tests; full arxiv-daily-push unit tests; semantic extractor.
- Test results: focused runtime recovery and CLI tests 13 OK; arxiv-daily-push unit tests 210 OK; semantic extractor checked 43 active formulas and 308 active parameters with no errors.
- Successes: The runtime surface writes only explicit state/artifact paths, blocks stale heartbeat and stale locks, refuses restore without explicit confirmation, verifies backup hashes, blocks enabled production side-effect flags, and keeps scheduler install/uninstall as template-only dry-runs.
- Failures: No real scheduler was installed by design; no real Gmail email, GitHub Release, video, 30 historical previews, or live production days were executed in S1-08.
- Decisions: Bump product version to 0.18.0 because S1-08 adds a backward-compatible local runtime recovery CLI and contract while preserving disabled production side effects.
- Remaining risks: S1-09 migration package, 30 historical previews, two live production days, and production trial evidence remain incomplete before `ARXIV_PRODUCTION_ACCEPTED`.
- Rollback: Remove `stage1_runtime.py`, runtime recovery CLI dispatch/tests, restore version 0.17.0, and revert S1-08 governance records and run manifest.
- Next step: S1-09-MIGRATION_PACKAGE-001.

### `ITER-20260622-S1-006`

- Date: 2026-06-22
- Fact level: EXTRACTED from `stage1_b1_report.py`, focused B1 report/email tests, full ADP unit tests, semantic extractor, and governance registry updates.
- Version before: 0.16.0
- Version after: 0.17.0
- Base commit: bbcdc21caab1c4377810d66bb95359ed3ef18611
- Result commit: PENDING
- Task IDs: S1-07-B1_REPORT_EMAIL_TEXT-001
- Goal: Add the Review8 Stage 1 B1/arXiv Chinese teaching report and email preview package with supported claim evidence, candidate queue summary, owner subject contract, artifact/audit output, and no production side effects.
- Assumptions: S1-07 is a deterministic local text delivery interface only; it does not send Gmail SMTP, upload GitHub Releases, generate video, enable production scheduling, run 30 historical previews, or claim `ARXIV_PRODUCTION_ACCEPTED`.
- Files read: `arxiv-daily-push/AGENTS.md`, V5 baseline lock and task pack, daily input builder, Claim Ledger gate, lesson renderer, Stage 1 queue, CLI, focused tests, semantic extractor, and existing governance registries.
- Files changed: `stage1_b1_report.py`, B1 report/email CLI dispatch, focused B1 report tests, version files, changelog, model/formula/parameter registries, model spec, version matrix, traceability, delivery tasks, phase record, ledger/event records, and run manifest.
- Model changes: Added MOD-ADP-040 `adp-stage1-b1-report-email-v1`.
- Formula changes: Added FORM-ADP-042 and refreshed FORM-ADP-024 because `cli.py::main` gained the `build-b1-report-email` subcommand.
- Parameter changes: Added PARAM-ADP-310 through PARAM-ADP-315 for B1 report schema, board ID/name, subject contract, critical claim coverage gate, and prohibited email marker count.
- Commands run: focused B1 report/email plus CLI tests; full arxiv-daily-push unit tests; semantic extractor.
- Test results: focused B1 report/email and CLI tests 9 OK; arxiv-daily-push unit tests 203 OK; semantic extractor checked 42 active formulas and 298 active parameters with no errors.
- Successes: The package validates arXiv daily input and supported claims, blocks unsupported P0 claims, renders Chinese teaching report/email previews, keeps claim IDs in report/audit rather than the user email foreground, includes candidate queue summary, removes frontend percentage/ROI/video clutter, writes artifacts only when explicitly requested, and keeps SMTP/Release/video/network side effects false.
- Failures: No real Gmail email or GitHub Release was sent in S1-07 by design; production acceptance remains blocked.
- Decisions: Bump product version to 0.17.0 because S1-07 adds a backward-compatible Stage 1 B1 report/email text CLI and contract while preserving disabled production side effects.
- Remaining risks: S1-08 runtime recovery, S1-09 migration package, 30 historical previews, two live production days, and production trial evidence remain incomplete before `ARXIV_PRODUCTION_ACCEPTED`.
- Rollback: Remove `stage1_b1_report.py`, `build-b1-report-email` CLI dispatch/tests, restore version 0.16.0, and revert S1-07 governance records and run manifest.
- Next step: S1-08-LOCAL_RUNTIME_RECOVERY-001.

### `ITER-20260622-S1-005`

- Date: 2026-06-22
- Fact level: EXTRACTED from `stage1_queue.py`, owner-controls-backed queue parameters, focused Stage 1 queue/owner tests, generated owner ledger, semantic extractor, and governance registry updates.
- Version before: 0.15.0
- Version after: 0.16.0
- Base commit: 89fe618f953b73e168f4f218b8c3edfc0102f6f9
- Result commit: PENDING
- Task IDs: S1-06-SCORING-QUEUE-LEDGER-001
- Goal: Add the Review8 Stage 1 scoring, 10000 active queue cap, 365-day inclusive event window, source-share cap fixture behavior, reason-code ledger rows, stable tie ordering, and canonical CONTENT_LEDGER output without production side effects.
- Assumptions: S1-06 is a deterministic fixture and contract layer only; it does not run production replay, fetch sources, expand beyond Stage 1 arXiv scope, generate reports/media, send SMTP, upload Releases, enable scheduling, or claim production acceptance.
- Files read: `AGENTS.md`, `arxiv-daily-push/AGENTS.md`, Review8 V4 baseline files, owner controls, ranking/global_scan/storage/CLI boundaries, owner docs generator, semantic extractor, existing governance registries, and focused owner/CLI tests.
- Files changed: `stage1_queue.py`, Stage 1 queue CLI dispatch, owner content ledger column source, focused queue tests, owner controls tests, generated owner docs, version files, changelog, model/formula/parameter registries, model spec, version matrix, traceability, delivery tasks, ledger/event records, and run manifest.
- Model changes: Added MOD-ADP-039 `adp-stage1-scoring-queue-ledger-v1`.
- Formula changes: Added FORM-ADP-041 for weighted research scoring, queue priority scoring, 10000 cap, 365-day boundary, lifecycle/source/capacity reason codes, stable ordering, and canonical content ledger rows.
- Parameter changes: Added PARAM-ADP-287 through PARAM-ADP-309 for queue schema, max active items, max event age, source share cap, soft quotas, research weights, queue-priority weights, and ledger column count. No frozen owner control values were changed.
- Commands run: focused Stage 1 queue/owner tests; owner docs render; semantic hash calculation for FORM-ADP-041 and PARAM-ADP-287 through PARAM-ADP-309. Final full tests and validators are recorded in the corresponding development event and run manifest.
- Test results: focused Stage 1 queue/owner tests 12 OK before final validation.
- Successes: Deterministic queue report handles 10001st-item eviction, 365/366-day boundary, soft quota borrowing, feasible multi-source 40% cap, lifecycle reactivation/retraction/supersession reason codes, prior ledger references, canonical CONTENT_LEDGER columns, and CLI JSON output.
- Failures: Initial source-cap test used a mathematically impossible two-source 40% cap fixture; corrected to a feasible three-source fixture. Initial ledger implementation omitted the required video ledger columns; corrected before governance hash capture.
- Decisions: Bump product version to 0.16.0 because S1-06 adds a backward-compatible Stage 1 scoring/queue/ledger CLI and contract while preserving disabled production side effects.
- Remaining risks: S1-06 proves fixture-level deterministic behavior only; B1 report/email text interface, runtime recovery, migration package, real production trial start, and 30-day acceptance evidence remain incomplete.
- Rollback: Remove `stage1_queue.py`, stage1-queue CLI dispatch/tests, restore owner ledger placeholder columns to the prior S1-03 form if reverting the contract, restore version 0.15.0, and revert S1-06 governance records and run manifest.
- Next step: S1-07-B1_REPORT_EMAIL_TEXT-001.

### `ITER-20260622-S1-004`

- Date: 2026-06-22
- Fact level: EXTRACTED from `source_registry.py`, source-registry CLI dispatch, focused source registry/source ingest tests, full ADP unit tests, semantic extractor, and governance registry updates.
- Version before: 0.14.1
- Version after: 0.15.0
- Base commit: 17afce7844f1fc67de0721940af3bda8eab582f9
- Result commit: PENDING
- Task IDs: S1-05-ARXIV-CONNECTOR-CONTRACT-001
- Goal: Add the Review8 Stage 1 source registry and arXiv connector contract that proves the single owner-controls source list, SRC-ARXIV/arxiv.atom.v1 active adapter, offline fixture validation, and max 10 metadata canary cap without production side effects.
- Assumptions: S1-05 is a connector boundary and evidence contract only; it does not enable B1 non-arXiv sources, run a live network canary during local validation, download PDFs, send SMTP, upload Releases, enable production scheduling, or claim production acceptance.
- Files read: `AGENTS.md`, `arxiv-daily-push/AGENTS.md`, Review8 V4 baseline files, owner controls, source ingest, arXiv adapter, CLI, SourceItem contracts, existing governance registries, and focused source/CLI tests.
- Files changed: `source_registry.py`, source-registry CLI dispatch, source ingest canary cap, source registry schema/tests, focused source ingest test, version files, changelog, model/formula/parameter registries, model spec, version matrix, traceability, delivery tasks, ledger/event records, and run manifest.
- Model changes: Added MOD-ADP-038 `adp-source-registry-contract-v1`.
- Formula changes: Added FORM-ADP-040, updated FORM-ADP-017 max_results domain to 1..10, and refreshed FORM-ADP-024 implementation evidence because `cli.py::main` gained the source-registry subcommand.
- Parameter changes: Updated PARAM-ADP-075 from 25 to 10 for Review8 Window A source ingest canary cap and added PARAM-ADP-280 through PARAM-ADP-286 for source registry schema, connector version, canonical config path, active source, active adapter, max canary results, and allowed enabled source count.
- Commands run: focused source registry/source ingest/arXiv adapter/CLI unit tests; full arxiv-daily-push unit tests; semantic extractor; project governance validator; all-project governance validator; changed-only semantic sync validator; root governance unit tests; information-quality validator; source registry schema JSON parse; manifest JSON parse; CSV width checks.
- Test results: focused source registry/source ingest/arXiv adapter/CLI tests 20 OK; arxiv-daily-push unit tests 193 OK; semantic extractor checked 40 active formulas and 285 active parameters with no errors; project governance errors 0 warnings 0; all-project governance errors 0 warnings 0; changed-only semantic sync errors 0 warnings 0; root governance tests 128 OK; information-quality PASS; source registry schema and manifest JSON parse OK; parameter registry and traceability CSV widths consistent.
- Successes: Source registry report passes from `config/owner_controls.yaml` plus offline arXiv Atom fixture, blocks non-arXiv enabled sources in Window A, keeps PDF/bulk/paid/secret/production side effects disabled, and enforces max 10 metadata records.
- Failures: The pre-rebase semantic extractor correctly caught PARAM-ADP-075 active value drift and FORM-ADP-024 CLI fingerprint drift before registry updates; the first full unit run caught the version command still expecting 0.14.0, fixed by updating the focused version test to 0.15.0.
- Decisions: Bump product version to 0.15.0 because S1-05 adds a backward-compatible source registry CLI/schema/contract and changes the Review8 Window A active canary cap from 25 to 10 while preserving disabled production side effects.
- Remaining risks: Queue/content ledger replay, B1 delivery interface, local runtime recovery, migration package, production trial start, and 30-day acceptance evidence remain incomplete.
- Rollback: Remove source_registry module, source-registry CLI dispatch/tests/schema, restore SOURCE_INGEST_MAX_RESULTS to 25 if returning to pre-Review8 Window A semantics, restore version 0.14.1, and revert S1-05 governance records and run manifest.
- Next step: S1-06-SCORING-QUEUE-LEDGER-001.

### `ITER-20260621-055`

- Date: 2026-06-22
- Fact level: EXTRACTED from owner V2 mockup/notes, email renderer code, SMTP multipart boundary, focused V2 tests, full ADP tests, semantic extractor, and governance validation.
- Version before: 0.14.0
- Version after: 0.14.1
- Base commit: f6d6131a6f87274fbfa29edc587b1b5523f1c85c
- Result commit: PENDING
- Task IDs: ADP-PHASE12-EMAIL-DECISION-UI-V2-038
- Goal: Rebuild the daily email as a Chinese decision-first HTML/plain-text frontstage with the exact `YYYYMMDD -- Project Name -- arXiv Group -- Theme` subject contract, optional Release-hosted MP4 link, q-fin candidate filtering, feedback actions, and hidden backend ROI/Claim Ledger foreground details.
- Assumptions: This is a frontstage delivery-quality fix only; it does not enable scheduled production, send SMTP, upload Releases, reduce all-arXiv scan scope, change queue persistence, or log secrets.
- Files changed: lesson frontstage, daily email renderer, SMTP HTML alternative boundary, video transcript wording, schema/tests, version files, governance registries, phase record, run manifest, and governance tests.
- Model changes: Added MOD-ADP-037 `adp-email-decision-ui-v2`; refreshed MOD-ADP-034 to `adp-manual-delivery-test-v1.4`.
- Formula changes: Added FORM-ADP-039; refreshed FORM-ADP-008, FORM-ADP-018, FORM-ADP-034, and FORM-ADP-036 evidence after renderer changes.
- Parameter changes: Refreshed PARAM-ADP-186 and added PARAM-ADP-276 through PARAM-ADP-279 for HTML alternative, plain-text length, q-fin candidate filter, and lesson frontstage.
- Commands run: focused email V2 tests, semantic extractor, full ADP tests, governance dashboard generation, root governance tests, changed-only semantic governance validation, information-quality validation, manifest JSON parse, diff check, and cache check.
- Test results: focused email V2 tests 35 OK; semantic extractor checked 39 active formulas and 278 active parameters; arxiv-daily-push tests 189 OK; governance dashboard PASS; root governance tests 128 OK; changed-only governance sync errors 0 warnings 0; information quality PASS; manifest JSON and CSV width checks PASS; cache check PASS.
- Successes: Email frontstage is no longer shaped like backend evidence; visible ROI, Claim Ledger, delivery policy, Release landing clutter, numeric `x/5` foreground scoring, and irrelevant q-fin candidate pollution are suppressed.
- Failures: No revised-format real Gmail email has been sent yet after this correction.
- Decisions: Keep production schedule disabled; open PR, wait for CI, merge, then perform one controlled manual Release plus Gmail SMTP rerun.
- Remaining risks: Live Gmail rendering still needs the controlled manual workflow proof after PR CI and merge.
- Rollback: Revert version 0.14.1 email decision UI V2 code, tests, schema updates, governance records, phase record, manifest, and event; restore version 0.14.0.
- Next step: Open PR, wait for PR CI green, then controlled manual Release + Gmail SMTP rerun after merge.

### `ITER-20260622-S1-003`

- Date: 2026-06-22
- Fact level: EXTRACTED from `storage.py`, storage CLI dispatch, focused storage tests, full ADP unit tests, semantic extractor, and governance registry updates.
- Version before: 0.13.1
- Version after: 0.14.0
- Base commit: f05525698a51f88828cd5aeadac4c7c8859e74a2
- Result commit: PENDING
- Task IDs: S1-04-SQLITE-DATA-MODEL-001
- Goal: Add the Review8 Stage 1 local SQLite/WAL/FTS5 document and event storage model with migration, inspection, SourceItem persistence, full-text search, rollback, and governance traceability.
- Assumptions: S1-04 is local-storage-only and does not fetch sources, retain PDFs, send SMTP, upload Releases, enable the production scheduler, or claim production acceptance.
- Files read: `AGENTS.md`, `arxiv-daily-push/AGENTS.md`, Review8 V4 baseline files, existing governance registries, CLI, generic SourceItem contracts, and focused CLI/storage tests.
- Files changed: `storage.py`, CLI storage subcommands, focused storage/CLI tests, version files, changelog, model/formula/parameter registries, model spec, version matrix, traceability, delivery tasks, ledger/event records, and run manifest.
- Model changes: Added MOD-ADP-036 `adp-sqlite-data-model-v1`.
- Formula changes: Added FORM-ADP-038 and refreshed FORM-ADP-024 implementation evidence because `cli.py::main` gained storage subcommands.
- Parameter changes: Added PARAM-ADP-268 through PARAM-ADP-275 for schema version, default DB filename, WAL mode, FTS5 requirement, rollback target, object table count, relation type count, and time field count.
- Commands run: focused storage/CLI unit tests with ResourceWarning as error; full arxiv-daily-push unit tests; semantic extractor; project governance validator; all-project governance validator; changed-only semantic sync validator; root governance unit tests; information-quality validator; manifest JSON parse; CSV width checks.
- Test results: focused storage/CLI tests 9 OK; arxiv-daily-push unit tests 186 OK; semantic extractor checked 38 active formulas and 274 active parameters with no errors; project governance errors 0 warnings 0; all-project governance errors 0 warnings 0; changed-only semantic sync errors 0 warnings 0; root governance tests 128 OK; information-quality PASS; manifest JSON parse OK; parameter registry and traceability CSV widths consistent.
- Successes: Migration creates schema version 1 with WAL and FTS5, stores SourceItem data idempotently, supports FTS search, and rolls back to version 0.
- Failures: First semantic extractor run caught FORM-ADP-024 CLI fingerprint drift after adding storage subcommands; fixed by refreshing FORM-ADP-024 machine evidence. Project governance initially caught ledger and generated assurance count drift; those generated views were refreshed.
- Decisions: Bump product version to 0.14.0 because S1-04 adds a backward-compatible local storage CLI and schema capability while preserving disabled production side effects.
- Remaining risks: Connector contract, queue/content ledger replay, B1 delivery interface, local runtime recovery, migration package, production trial start, and 30-day acceptance evidence remain incomplete.
- Rollback: Remove storage module, storage CLI dispatch/tests, version 0.14.0 governance records, and run manifest; restore version 0.13.1.
- Next step: S1-05-ARXIV-CONNECTOR-CONTRACT-001.

### `ITER-20260621-054`

- Date: 2026-06-22
- Fact level: EXTRACTED from manual run `27934320671`, the email renderer, MP4 transcript renderer, scheduled Release notes, focused regression tests, and governance registry updates.
- Version before: 0.13.0
- Version after: 0.13.1
- Base commit: ecd43e80a29193120d788ef8125d4ebca233dca3
- Result commit: PENDING
- Task IDs: ADP-PHASE12-EMAIL-FRONTSTAGE-QUALITY-037
- Goal: Correct the human front-stage after the controlled manual email technically succeeded but foregrounded a low-value 12-second video/Release path and exposed backend ROI scoring in the MP4 transcript.
- Assumptions: The Chinese email body is the daily reading entry point; Release is backend evidence/download storage; MP4 is optional; backend ROI evidence remains available in GitHub artifacts.
- Files changed: daily email renderer, scheduled Release notes wording, MP4 transcript renderer, focused tests, version/changelog files, model/formula/parameter/traceability registries, delivery task, phase record, run manifest, and event.
- Model changes: Refined MOD-ADP-034 to `adp-manual-delivery-test-v1.3`.
- Formula changes: Refreshed FORM-ADP-036 with email-as-reading-entry, Release-as-backend-storage, optional-video, and MP4 transcript ROI suppression constraints.
- Parameter changes: Updated PARAM-ADP-186 and added PARAM-ADP-267, preserving owner controls PARAM-ADP-187 through PARAM-ADP-266.
- Commands run: focused front-stage tests; full arXiv unit tests; semantic extractor; governance dashboard generation; root governance tests; changed-only governance validation; information-quality validation; JSON/JSONL/CSV parse checks; diff/cache checks.
- Test results: focused front-stage tests 27 OK; arXiv unit tests 182 OK; semantic extractor checked 37 active formulas and 266 active parameters; root governance tests 126 OK; changed-only governance errors 0 warnings 0; information quality PASS.
- Successes: Email no longer includes the Release landing page as a reading entry, no longer foregrounds `【12秒视频】`, marks video as optional, and the MP4 transcript no longer includes `ROI score`.
- Failures: No revised-format real email has been sent yet after this correction.
- Decisions: Keep production schedule disabled; rerun the controlled manual Release + Gmail SMTP workflow only after PR CI passes and this fix merges to `main`.
- Remaining risks: The next real email can still expose live formatting issues; scheduled production remains blocked until separately approved.
- Rollback: Revert version 0.13.1 front-stage quality code, tests, phase record, event, manifest, and governance records, then restore version 0.13.0.
- Next step: Complete post-rebase validation, update PR, wait for CI green, merge, then rerun the controlled manual Release + Gmail SMTP workflow.

### `ITER-20260621-053`

- Date: 2026-06-22
- Fact level: EXTRACTED from owner email-format requirements, the successful controlled manual delivery run `27932072771`, daily email renderer code, focused email/scheduled-execution tests, and sample preview output.
- Version before: 0.12.4
- Version after: 0.12.5
- Base commit: b7451f8533d7f9c33bc3a2739c297de93ff2f615f
- Result commit: PENDING
- Task IDs: ADP-PHASE12-EMAIL-HUMAN-FORMAT-036
- Goal: Refine the daily email front-end into a human-scannable Chinese layout with compact arXiv subject, 12-second video link, concise evidence, action guidance, and candidate queue summary while keeping ROI scoring in backend artifacts.
- Assumptions: The owner wants the email front-end optimized for direct reading and decision-making; backend GitHub artifacts remain the correct place for ROI scores, ranking details, and delivery evidence.
- Files changed: daily email renderer, global scan/scheduled execution tests, version/changelog files, pyproject version metadata, model/formula/parameter/traceability registries, delivery task, phase record, run manifest, generated views, and event.
- Model changes: Refined MOD-ADP-034 to `adp-manual-delivery-test-v1.2`.
- Formula changes: Refreshed FORM-ADP-036 with human email front-end constraints.
- Parameter changes: Added PARAM-ADP-186 for the daily email front-end format contract.
- Commands run: focused email and scheduled execution tests; full arXiv unit tests; semantic extractor; governance dashboard generation; root governance tests; information-quality validation; changed-only governance validation; JSON parse; diff/cache checks.
- Test results: focused email and scheduled execution tests 20 OK; arXiv unit tests 177 OK; semantic extractor checked 36 active formulas and 185 active parameters; governance, information quality, JSON, diff, and cache checks passed before rebase and will be rerun after conflict resolution.
- Successes: Daily email subject now follows `YYYYMMDD -- Project Name -- arXiv Group -- Theme`. Body no longer starts with `project`, `date`, `recipient`, and no longer injects visible ROI score or delivery policy text. Body keeps Chinese sections, 12-second video link, Release link, concise evidence, action-time guidance, and candidate queue summary.
- Failures: No revised-format real email has been sent yet in this preparation commit.
- Decisions: Keep production schedule disabled; rerun the controlled manual Release + Gmail SMTP workflow only after PR CI passes and this format change merges to `main`.
- Remaining risks: The next real email can still expose formatting issues in a live article title or generated lesson section; scheduled production remains blocked until separately approved.
- Rollback: Revert version 0.12.5 email format code, tests, phase record, event, manifest, and governance records, then restore version 0.12.4.
- Next step: Complete post-rebase validation, open PR, wait for PR CI green, merge, then rerun the manual Release + Gmail SMTP workflow.


### `ITER-20260622-S1-002`

- Date: 2026-06-22
- Fact level: EXTRACTED for owner_controls config, generated owner views, schema, CLI commands, tests, model/formula/parameter registry updates, and semantic extractor evidence.
- Version before: 0.12.5
- Version after: 0.13.0
- Base commit: 823f374a751a37b55e7eeb63cc8d91498d06da46
- Result commit: PENDING
- Task IDs: S1-03-OWNER-CONTROLS-001
- Goal: Create the Review8 V4 single owner-editable control file and generated owner-readable views without changing runtime scoring, source ingestion, SMTP, Release, or scheduler behavior.
- Assumptions: `config/owner_controls.yaml` is the owner-editable source; `docs/owner/*` are generated views and not additional editable facts.
- Files read: `AGENTS.md`, `docs/governance/STANDARD.md`, Review8 V4 task pack, `arxiv-daily-push/docs/governance/*`, CLI, scoring/ranking constants, semantic extractor, and focused tests.
- Files changed: owner controls config, owner controls schema, owner controls module, CLI owner subcommands, owner focused tests, generated owner views, version files, model/formula/parameter registries, model spec, version matrix, traceability, delivery tasks, ledger/event records, and run manifest.
- Model changes: Added MOD-ADP-035 `adp-owner-controls-v1`.
- Formula changes: Added FORM-ADP-037 and refreshed FORM-ADP-024 implementation evidence because `cli.py::main` gained owner subcommands.
- Parameter changes: Added PARAM-ADP-187 through PARAM-ADP-266 for owner controls scalar values and owner weight groups with machine `yaml_path` selectors.
- Commands run: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s103_owner2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_owner_controls.py -q`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s103_cli PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_cli.py -q`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s103_semantic2 PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_semantic_extractors.py arxiv-daily-push`.
- Test results: owner focused tests 5 OK; CLI focused tests 5 OK; semantic extractor checked 37 active formulas and 265 active parameters with no errors.
- Successes: Owner controls validate, preview impact without side effects, generate four owner-readable files, and block bad owner scoring weights in regression tests.
- Failures: Initial owner focused test caught an over-broad secret-key pattern that treated `max_context_tokens` as a token; fixed by narrowing secret-key matching. First semantic extractor run caught FORM-ADP-024 CLI fingerprint drift; fixed by refreshing the formula evidence.
- Decisions: Bump product version to 0.13.0 because S1-03 adds a backward-compatible owner controls CLI/config/view capability while preserving disabled production side effects.
- Remaining risks: SQLite/WAL/FTS5 model, arXiv connector contract hardening, queue replay, B1 report/email text interface, local runtime recovery, migration package, real production trial start, two live days, and 30-day trial evidence remain incomplete.
- Rollback: Revert version 0.13.0 owner_controls files, generated owner views, CLI subcommands, owner tests, and governance registry updates; restore version 0.12.5 while keeping production variables disabled.
- Next step: Complete final validation and then continue with S1-04 SQLite data model.

### `ITER-20260622-S1-001`

- Date: 2026-06-22
- Fact level: EXTRACTED for imported baseline hashes, version drift, GitHub Actions run evidence, and governance file updates; PROPOSED for future S1 tasks.
- Version before: 0.12.4
- Version after: 0.12.4
- Base commit: bbdc69bb49758e4ad84f91f45fbe7921b82b1414
- Result commit: PENDING
- Task IDs: S1-02-BASELINE-LOCK-TRACEABILITY-001
- Goal: Lock the Review8 V4 two-stage baseline into arXiv Daily Push governance and bind the successful manual delivery run without claiming production acceptance.
- Assumptions: S1-02 is governance-only and does not change scoring, ranking, Claim Ledger, email, Release, scheduler, source ingest, or media runtime behavior.
- Files read: `AGENTS.md`, `arxiv-daily-push/AGENTS.md`, `arxiv-daily-push/README.md`, `arxiv-daily-push/PLANS.md`, `arxiv-daily-push/docs/governance/*`, and the Review8 V4 ZIP.
- Files changed: pursuing-goal baseline files, project entry docs, governance delivery/version/traceability/ledger files, changelog, pyproject version metadata, generated governance views, manifest, and focused governance tests.
- Model changes: None.
- Parameter changes: None.
- Commands run: PENDING final validation.
- Test results: PENDING final validation.
- Successes: V4 baseline imported with matching hashes; pyproject version aligned to 0.12.4; GitHub run `27932072771` scoped as controlled manual delivery evidence only.
- Failures: None recorded so far.
- Decisions: Keep product version at 0.12.4 because S1-02 is a governance baseline lock, not a product behavior change.
- Remaining risks: S1 owner controls, owner views, SQLite data model, local runtime recovery, migration package, 30-day trial, two live days, and final production acceptance remain incomplete.
- Rollback: Revert S1-02 baseline files, documentation updates, governance records, generated views, manifest, and focused test changes.
- Next step: Complete S1-02 validation, then run S1-03 owner controls.

### `ITER-20260621-001`

- Date: 2026-06-21
- Fact level: EXTRACTED for created Phase 1 files and PROPOSED for future phases
- Version before: none
- Version after: 0.1.0
- Base commit: 18c3773dd5cb9d618993a5685eed7fb668349ac3
- Result commit: 4090ec69fea8fd5329eeee03a8ab842a5347b909
- Task IDs: ADP-PHASE1-FOUNDATION-001
- Goal: Start arXiv Daily Push inside CodexProject using the prepared pursuing goal baseline.
- Assumptions: Phase 1 remains foundation-only and does not implement ingest, ranking, evidence, TTS, video, runner, or SMTP transport.
- Files read: root AGENTS, governance standard, projects registry, codex-dex, project-governance skill, Phase 0 and pursuing goal preparation outputs.
- Files changed: arxiv-daily-push project files, root README, governance/projects.yaml.
- Model changes: Added MOD-ADP-001 active foundation gate and planned MOD-ADP-002/MOD-ADP-003.
- Parameter changes: Added PARAM-ADP-001 through PARAM-ADP-019.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`; `python3 scripts/validate_project_governance.py --project arxiv-daily-push`; `python3 scripts/validate_project_governance.py --changed-only`; `git diff --check`.
- Test results: 4 unit tests OK; project governance errors 0 warnings 0; changed-only governance errors 0 warnings 0; diff check exit 0.
- Successes: Project skeleton and governance records created.
- Failures: none recorded at file creation time.
- Decisions: Use public CodexProject path `arxiv-daily-push` and preserve future multi-source boundaries.
- Remaining risks: Later phases need environment setup and additional implementation.
- Rollback: Remove `arxiv-daily-push/` and restore `README.md` plus `governance/projects.yaml`.
- Next step: Start Phase 2 data contracts after the next run contract.

### `ITER-20260621-002`

- Date: 2026-06-21
- Fact level: EXTRACTED for Phase 2 contracts, schemas, state machine, tests, and governance updates.
- Version before: 0.1.0
- Version after: 0.2.0
- Base commit: 4090ec69fea8fd5329eeee03a8ab842a5347b909
- Result commit: PENDING
- Task IDs: ADP-PHASE2-DATA-CONTRACTS-001
- Goal: Implement generic SourceItem, EvidenceClaim, Lesson, Storyboard, Publication, and RunRecord contracts without network or media side effects.
- Assumptions: Phase 2 remains offline-only and does not implement arXiv ingest, ranking, evidence extraction, lesson generation, media generation, runner automation, or SMTP transport.
- Files changed: contract/state code, schema files, tests, README, CHANGELOG, VERSION, and governance records.
- Model changes: Added MOD-ADP-004 active generic contract and RunRecord state gate.
- Parameter changes: Added PARAM-ADP-020 through PARAM-ADP-028.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`; `python3 -m json.tool arxiv-daily-push/schemas/*.schema.json`.
- Test results: 13 unit tests OK; all schema JSON files parse OK.
- Successes: Generic source boundary accepts arXiv and a future GitHub source; P0 locator requirement and skipped state transitions fail closed.
- Failures: Initial `RunRecord.stages` empty-array validation failed and was fixed in `state_machine.py`.
- Decisions: Keep runtime validation dependency-free; use schemas as external contract and stdlib validators for local gates.
- Remaining risks: Phase 4 ranking and real arXiv adapter are not implemented.
- Rollback: Revert Phase 2 commit and restore version/governance records to 0.1.0.
- Next step: Start Phase 4 arXiv adapter/ranking only after final Phase 2 validation passes.

### `ITER-20260621-003`

- Date: 2026-06-21
- Fact level: EXTRACTED for arXiv adapter code, local fixture, CLI commands, tests, and governance updates.
- Version before: 0.2.0
- Version after: 0.3.0
- Base commit: e5f15384887e8e4878a228673dfb487345d1a5c1
- Result commit: PENDING
- Task IDs: ADP-PHASE3-ARXIV-ADAPTER-001
- Goal: Implement the first concrete arXiv SourceAdapter without bulk ingest or media side effects.
- Assumptions: Phase 3 validates URL construction and Atom parsing locally; live scheduled ingestion remains future work.
- Files changed: arXiv adapter code, CLI commands, fixture, tests, source config, version files, and governance records.
- Model changes: Added MOD-ADP-005 active arXiv Atom source adapter.
- Parameter changes: Added PARAM-ADP-029 through PARAM-ADP-034.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 19 unit tests OK.
- Successes: arXiv Atom fixture maps into generic SourceItem and validates against Phase 2 contract.
- Failures: Initial CLI indentation error was caught by tests and fixed before governance validation.
- Decisions: Keep Phase 3 tests offline and cap Phase 3 query construction at 50 results per call.
- Remaining risks: Live arXiv API availability, rate limits, and daily freshness are not yet covered by scheduler/runner gates.
- Rollback: Revert Phase 3 adapter code, tests, fixture, and governance updates.
- Next step: Start Phase 4 queue/ranking once final Phase 3 validation passes.

### `ITER-20260621-004`

- Date: 2026-06-21
- Fact level: EXTRACTED for ranking code, CLI command, local fixture, golden tests, and governance updates.
- Version before: 0.3.0
- Version after: 0.4.0
- Base commit: 8538e98f62838c1f2c1fad86f564b10838691219
- Result commit: PENDING
- Task IDs: ADP-PHASE4-RANKING-001
- Goal: Implement deterministic 100-point candidate ranking with auditable component scores and fail-closed eligibility gates.
- Assumptions: Phase 4 ranks explicit candidate inputs only and does not fetch live sources, extract claims, generate lessons, send email, or create media.
- Files changed: ranking code, CLI command, ranking fixture, ranking tests, version files, and governance records.
- Model changes: Activated MOD-ADP-002 as adp-ranking-v1.
- Parameter changes: Activated PARAM-ADP-009 through PARAM-ADP-016 as adp-ranking-parameters-v1.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 26 unit tests OK.
- Successes: Golden candidate scores 85.5 points; missing P0 evidence, metadata conflicts, and recent duplicate selections fail closed.
- Failures: none recorded at implementation time.
- Decisions: Use normalized 0..1 component signals multiplied by fixed weights summing to 100.
- Remaining risks: Live source freshness and automatic Claim Ledger extraction remain future gates.
- Rollback: Revert Phase 4 ranking code, tests, fixture, and governance updates.
- Next step: Start Phase 5 Claim Ledger extraction and publication gate after final Phase 4 validation passes.

### `ITER-20260621-005`

- Date: 2026-06-21
- Fact level: EXTRACTED for Claim Ledger gate code, CLI command, local fixture, tests, and governance updates.
- Version before: 0.4.0
- Version after: 0.5.0
- Base commit: 5a8034552810fb1efa2b9ff85f774180c85ac1f2
- Result commit: PENDING
- Task IDs: ADP-PHASE5-EVIDENCE-GATE-001
- Goal: Implement deterministic Claim Ledger construction and publication hard-block gates.
- Assumptions: Phase 5 consumes explicit evidence claims and does not parse PDFs, generate lesson text, send email, or create media.
- Files changed: evidence gate code, CLI command, Claim Ledger fixture, evidence gate tests, version files, and governance records.
- Model changes: Activated MOD-ADP-003 as adp-claim-gate-v1.
- Parameter changes: Activated PARAM-ADP-017 and PARAM-ADP-018 as adp-evidence-parameters-v1.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 32 unit tests OK.
- Successes: Missing P0 locator, unsupported P0, metadata conflict, and unsupported arXiv peer-review claims block publication.
- Failures: Initial empty `Publication.artifacts` output failed validation and was fixed by recording the Claim Ledger artifact.
- Decisions: Treat Claim Ledger as a required publication artifact before publication is ready.
- Remaining risks: Lesson generation and text-level claim coverage remain future gates.
- Rollback: Revert Phase 5 evidence gate code, tests, fixture, and governance updates.
- Next step: Start Phase 6 evidence-linked lesson generation.


### `ITER-20260621-006`

- Date: 2026-06-21
- Fact level: EXTRACTED for lesson generation code, CLI command, local fixture, tests, and governance updates.
- Version before: 0.5.0
- Version after: 0.6.0
- Base commit: 7d67c585ec1a808da23ffd0e097dddc6af617b02
- Result commit: PENDING
- Task IDs: ADP-PHASE6-LESSON-001
- Goal: Implement deterministic Chinese Lesson JSON generation from supported Claim Ledger evidence.
- Assumptions: Phase 6 remains text-only and does not synthesize narration, download models, render video, run schedulers, or send SMTP mail.
- Files changed: lesson generation code, CLI command, lesson fixture, lesson tests, version files, and governance records.
- Model changes: Activated MOD-ADP-006 as adp-lesson-v1.
- Parameter changes: Activated PARAM-ADP-035 and PARAM-ADP-036 as adp-lesson-parameters-v1.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 37 unit tests OK.
- Successes: Generated Lesson JSON references only supported claim IDs; unverified non-P0 claims are excluded; blocked ledgers prevent generation; unregistered section claims fail validation.
- Failures: none recorded at implementation time.
- Decisions: Use deterministic template generation with visible `[claim_id]` markers rather than model-generated free text.
- Remaining risks: Narration/TTS, media rendering, daily scheduler, Release upload, and real SMTP transport remain future gates.
- Rollback: Revert Phase 6 lesson code, tests, fixture, and governance updates.
- Next step: Start Phase 7 narration/TTS dry-run and resource gate.


### `ITER-20260621-007`

- Date: 2026-06-21
- Fact level: EXTRACTED for narration dry-run code, CLI command, schema, local fixture, tests, and governance updates.
- Version before: 0.6.0
- Version after: 0.7.0
- Base commit: 847652080c949a6678231677409de9d9dbb96989
- Result commit: PENDING
- Task IDs: ADP-PHASE7-TTS-001
- Goal: Implement narration/TTS-ready dry-run JSON and resource gates without audio synthesis or retained media.
- Assumptions: Phase 7 remains dry-run only and does not download models, synthesize voice, write audio files, render video, run schedulers, or send SMTP mail.
- Files changed: narration dry-run code, CLI command, narration schema, narration fixture, tests, version files, and governance records.
- Model changes: Activated MOD-ADP-007 as adp-narration-v1.
- Parameter changes: Activated PARAM-ADP-037 through PARAM-ADP-040 as adp-narration-parameters-v1.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 42 unit tests OK.
- Successes: Dry-run narration plan maps Lesson sections to segments, real TTS mode is blocked, audio paths are rejected, and runtime parameters expose real synthesis disabled.
- Failures: none recorded at implementation time.
- Decisions: Keep Phase 7 artifact as JSON only and defer any media writes until later resource gates pass.
- Remaining risks: Video rendering, daily scheduler, Release upload, and real SMTP transport remain future gates.
- Rollback: Revert Phase 7 narration code, schema, tests, fixture, and governance updates.
- Next step: Start Phase 8 video/storyboard dry-run and media QA gate.


### `ITER-20260621-008`

- Date: 2026-06-21
- Fact level: EXTRACTED for storyboard/video dry-run code, CLI command, fixture, tests, and governance updates.
- Version before: 0.7.0
- Version after: 0.8.0
- Base commit: 7332df2c5abed8aefbf694afe839ac496efafe06
- Result commit: PENDING
- Task IDs: ADP-PHASE8-VIDEO-001
- Goal: Implement Storyboard dry-run and video media gate without rendering or retained media.
- Assumptions: Phase 8 remains dry-run only and does not render video, write media, download assets, run schedulers, or send SMTP mail.
- Files changed: video dry-run code, CLI command, video fixture, tests, version files, and governance records.
- Model changes: Activated MOD-ADP-008 as adp-video-dry-run-v1.
- Parameter changes: Activated PARAM-ADP-041 through PARAM-ADP-044 as adp-video-parameters-v1.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 47 unit tests OK.
- Successes: Storyboard dry-run maps narration segments to scenes, media gate blocks real rendering/writes/downloads, media paths are rejected, and scene claims must stay inside narration claims.
- Failures: none recorded at implementation time.
- Decisions: Keep Phase 8 artifact as JSON storyboard only and defer real video rendering until resource gates pass.
- Remaining risks: Local pipeline orchestration, Release upload, runner scheduling, and real SMTP transport remain future gates.
- Rollback: Revert Phase 8 video dry-run code, tests, fixture, and governance updates.
- Next step: Start Phase 9 local daily pipeline dry-run.

### `ITER-20260621-009`

- Date: 2026-06-21
- Fact level: EXTRACTED for local dry-run pipeline code, CLI command, fixture, tests, and governance updates.
- Version before: 0.8.0
- Version after: 0.9.0
- Base commit: 8eda3772f881a0aaaa388c3c488de7e3a0ef773c
- Result commit: PENDING
- Task IDs: ADP-PHASE9-LOCAL-PIPELINE-001
- Goal: Implement local daily dry-run orchestration through completed RunRecord and email preview.
- Assumptions: Phase 9 remains manual dry-run only and does not schedule runs, upload Releases, send SMTP mail, or retain media.
- Test results: 51 unit tests OK.
- Next step: Start Phase 10 runner/release/email dry-run handoff.

### `ITER-20260621-010`

- Date: 2026-06-21
- Fact level: EXTRACTED for runner/release/email dry-run handoff code, CLI command, tests, and governance updates.
- Version before: 0.9.0
- Version after: 0.10.0
- Base commit: f7615d001c21ddc2778f802b2ca264702dd37308
- Result commit: PENDING
- Task IDs: ADP-PHASE10-RUNNER-RELEASE-EMAIL-001
- Goal: Implement Phase 10 handoff preview for runner, release, and email transport without enabling any external side effect.
- Assumptions: Phase 10 requires a completed local dry-run RunRecord and keeps scheduler, GitHub Actions runner, unattended execution, Release upload, and real SMTP sending disabled.
- Files changed: handoff code, CLI command, handoff tests, version files, and governance records.
- Model changes: Activated MOD-ADP-010 as adp-handoff-v1.
- Parameter changes: Activated PARAM-ADP-048 through PARAM-ADP-050 as adp-handoff-parameters-v1.
- Commands run: project unit tests; root governance tests; schema parse; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 55 project tests OK; 30 root governance tests OK; schemas parse; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Handoff contract encodes disabled runner/release/email transport side effects.
- Failures: none recorded at implementation time.
- Decisions: Use dry-run artifact previews rather than writing release assets or sending email.
- Remaining risks: Phase 11 final acceptance handoff is still pending; no live 30-day run evidence is claimed.
- Rollback: Revert Phase 10 handoff code, tests, and governance updates.
- Next step: Start Phase 11 final acceptance and handoff package after Phase 10 validation passes.

### `ITER-20260621-011`

- Date: 2026-06-21
- Fact level: EXTRACTED for final acceptance/handoff readiness code, CLI command, tests, and governance updates.
- Version before: 0.10.0
- Version after: 0.11.0
- Base commit: 06ce53098bb5f84b05e8f3e6c0a4c789ece298d8
- Result commit: PENDING
- Task IDs: ADP-PHASE11-ACCEPTANCE-HANDOFF-001
- Goal: Generate final acceptance and handoff readiness package without making unsupported production or 30-day trial claims.
- Assumptions: Handoff readiness can pass locally, but production acceptance remains blocked until real 30-day, scheduler, Release, SMTP, and resource evidence exists.
- Files changed: acceptance code, CLI command, acceptance tests, version files, and governance records.
- Model changes: Activated MOD-ADP-011 as adp-acceptance-v1.
- Parameter changes: Activated PARAM-ADP-051 through PARAM-ADP-055 as adp-acceptance-parameters-v1.
- Commands run: project unit tests; root governance tests; schema parse; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 60 project tests OK; 31 root governance tests OK; schemas parse; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Acceptance package separates dry-run readiness from production acceptance.
- Failures: none recorded at implementation time.
- Decisions: Do not mark production acceptance pass without explicit operational evidence references.
- Remaining risks: Live production readiness still requires external runner, SMTP, Release, and 30-day trial execution.
- Rollback: Revert Phase 11 acceptance code, tests, and governance updates.
- Next step: Provide final handoff and stop unless operational prerequisites are supplied.

### `ITER-20260621-012`

- Date: 2026-06-21
- Fact level: EXTRACTED for acceptance evidence-reference hardening, tests, and governance updates.
- Version before: 0.11.0
- Version after: 0.11.1
- Base commit: b6c1dce15a4fc850c7e555af178deda92899d120
- Result commit: PENDING
- Task IDs: ADP-PHASE11-EVIDENCE-REF-HARDENING-002
- Goal: Prevent boolean-only operational evidence from marking production acceptance as passed.
- Assumptions: Every production pass requirement must include a non-empty evidence reference.
- Files changed: acceptance code, acceptance tests, version files, and governance records.
- Model changes: Updated MOD-ADP-011 to adp-acceptance-v1.1.
- Parameter changes: Added PARAM-ADP-056 for evidence-reference requirements.
- Commands run: project unit tests; root governance tests; schema parse; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 61 project tests OK; 32 root governance tests OK; schemas parse; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Production acceptance cannot pass on true flags without evidence refs.
- Failures: none recorded at implementation time.
- Decisions: Keep production acceptance blocked unless both requirement flags and evidence references are present.
- Remaining risks: Live production readiness still requires external runner, SMTP, Release, and 30-day trial execution.
- Rollback: Revert evidence-reference hardening and restore version 0.11.0.
- Next step: Continue only with real operational prerequisite setup or evidence collection.

### `ITER-20260621-013`

- Date: 2026-06-21
- Fact level: EXTRACTED for 30-day trial evidence validator, acceptance integration, CLI command, tests, schema, and governance updates.
- Version before: 0.11.1
- Version after: 0.11.2
- Base commit: a67a988acf3778392ae584742fad8bf2c89d7d1d
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-EVIDENCE-VALIDATOR-003
- Goal: Require a validated 30-day trial evidence report before production acceptance can pass.
- Assumptions: The validator defines and enforces the evidence package but does not fabricate or execute the live 30-day trial.
- Files changed: trial evidence validator, acceptance gate, CLI command, tests, schema, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-012 as adp-trial-evidence-v1 and updated MOD-ADP-011 to adp-acceptance-v1.2.
- Parameter changes: Added PARAM-ADP-057 through PARAM-ADP-064.
- Commands run: project unit tests; root governance tests; schema parse; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 67 project tests OK; 33 root governance tests OK; schemas parse; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Production acceptance now rejects raw refs/booleans unless they come from a validated trial report.
- Failures: initial changed-only sync failed because the latest event did not cover the full branch diff; fixed by updating the latest development event and run manifest to the current 100-file diff list.
- Decisions: Treat weekly/monthly replay and recovery drill evidence as required parts of the 30-day trial evidence package.
- Remaining risks: Live production acceptance still requires external scheduler, SMTP, Release, resources, and actual 30-day run evidence.
- Rollback: Revert Phase 11 trial evidence validator and restore version 0.11.1.
- Next step: Run project and governance validation, then sync the PR.

### `ITER-20260621-014`

- Date: 2026-06-21
- Fact level: EXTRACTED for production preflight gate, CLI command, schema, tests, and governance updates.
- Version before: 0.11.2
- Version after: 0.11.3
- Base commit: 0d0e23fda99410770283401bfdb70ee8026cd489
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-PREFLIGHT-004
- Goal: Add a fail-closed gate before any scheduled production execution.
- Assumptions: Production runs must block if runtime commands, secret key presence, disk, memory, Git artifact hygiene, or cache/staging checks fail.
- Files changed: production preflight code, CLI command, tests, schema, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-013 as adp-production-preflight-v1.
- Parameter changes: Added PARAM-ADP-065 through PARAM-ADP-070.
- Commands run: project unit tests; root governance tests; schema parse; project governance validator; changed-only enforce-sync; production preflight CLI; dashboard generation; git diff check.
- Test results: 71 project tests OK; 34 root governance tests OK; schemas parse; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; production preflight exits 2 with blocked status as expected on current environment; dashboard PASS; git diff check exit 0.
- Successes: Preflight does not log secret values and does not read Codex auth.
- Failures: production preflight correctly blocks current environment because `gh`, `ffmpeg`, and `docker` are missing; SMTP/Release/runner env keys are missing; free disk is 25.36 GiB below the 80 GiB threshold.
- Decisions: Treat current local missing `gh`, `ffmpeg`, `docker`, SMTP env keys, Release target, and runner label as expected production blockers.
- Remaining risks: Production acceptance still requires provisioning the blocked prerequisites and running a real 30-day trial.
- Rollback: Revert Phase 11 production preflight gate and restore version 0.11.2.
- Next step: Run project and governance validation, then sync the PR.

### `ITER-20260621-015`

- Date: 2026-06-21
- Fact level: EXTRACTED for manual production trial bootstrap workflow, runbook, CLI validator, schema, tests, and governance updates.
- Version before: 0.11.3
- Version after: 0.11.4
- Base commit: 6ca3847899ea4c2647d90d219e0c5995fd6aedc5
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-BOOTSTRAP-005
- Goal: Add a manual GitHub Actions entrypoint that can start the real trial path only after production preflight succeeds.
- Assumptions: Bootstrap mode is manual-only and does not schedule production, upload Releases, send SMTP mail, render media, download models, or claim 30-day acceptance.
- Files changed: trial bootstrap validator, CLI command, workflow, runbook, tests, schema, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-014 as adp-trial-bootstrap-v1.
- Parameter changes: Added PARAM-ADP-071 through PARAM-ADP-074.
- Commands run: project unit tests; schema parse; trial bootstrap CLI; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 74 project tests OK; 35 root governance tests OK; schemas parse; trial bootstrap plan pass; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Bootstrap workflow requires explicit confirmation, targets a private self-hosted runner label, runs production preflight first, uploads preflight evidence, and leaves Release/SMTP side effects disabled.
- Failures: none recorded at implementation time.
- Decisions: Keep cron scheduling and real production side effects disabled until a provisioned runner produces a passing preflight artifact.
- Remaining risks: Production acceptance still requires actual runner provisioning, SMTP/Release configuration, preflight pass on runner, scheduled execution, and 30-day trial evidence.
- Rollback: Revert Phase 11 trial bootstrap workflow, runbook, validator, tests, and restore version 0.11.3.
- Next step: Run root governance validation, update run manifest, and sync the PR.

### `ITER-20260621-016`

- Date: 2026-06-21
- Fact level: EXTRACTED for live arXiv source ingest code, CLI command, SourceBatch schema, tests, phase record, and governance updates.
- Version before: 0.11.4
- Version after: 0.11.5
- Base commit: 26d82979344b49ad0628264713bf6423c4a1c11e
- Result commit: PENDING
- Task IDs: ADP-PHASE11-LIVE-ARXIV-INGEST-006
- Goal: Add a real arXiv latest-source ingest command with incremental duplicate filtering and fail-closed network/API behavior.
- Assumptions: Source ingest may use live arXiv Atom metadata but must not download PDFs, bulk harvest, bypass TLS, schedule runs, send email, or publish content.
- Files changed: source ingest code, CLI command, tests, SourceBatch schema, README, CHANGELOG, runbook, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-015 as adp-live-arxiv-ingest-v1.
- Parameter changes: Added PARAM-ADP-075 through PARAM-ADP-080.
- Commands run: project unit tests; schema parse; live arXiv fetch command; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: 78 project tests OK; 36 root governance tests OK; schemas parse; live fetch command blocked on current local Python SSL certificate verification; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Source ingest returns valid SourceBatch objects, filters duplicate source IDs, blocks duplicate-only batches, and blocks network/API failures.
- Failures: Current local machine cannot complete HTTPS arXiv fetch because Python certificate verification fails for `https://export.arxiv.org/api/query`.
- Decisions: Do not bypass TLS verification or switch to insecure fetch behavior; require runner CA trust repair before live trial source collection.
- Remaining risks: Production acceptance still requires actual runner provisioning, CA trust fix, SMTP/Release configuration, preflight pass on runner, scheduled execution, and 30-day trial evidence.
- Rollback: Revert live arXiv ingest command, SourceBatch schema, tests, and restore version 0.11.4.
- Next step: Run root governance validation, update run manifest, and sync the PR.

### `ITER-20260621-017`

- Date: 2026-06-21
- Fact level: EXTRACTED for SMTP delivery boundary code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.5
- Version after: 0.11.6
- Base commit: 3d8efa4017d15e00d4e1202faa42209ff3c7e227
- Result commit: PENDING
- Task IDs: ADP-PHASE11-SMTP-DELIVERY-007
- Goal: Add a fail-closed SMTP notification delivery boundary with dry-run evidence and explicit real-send gating.
- Assumptions: Notification delivery must default to dry-run; real SMTP requires explicit `--allow-send`, configured SMTP environment keys, TLS, and no secret/body logging.
- Files changed: SMTP delivery code, CLI command, tests, SMTP delivery schema, notification example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-016 as adp-smtp-delivery-v1.
- Parameter changes: Added PARAM-ADP-081 through PARAM-ADP-085.
- Commands run: focused notification/CLI tests; send-notification dry-run CLI. Full project and governance validation pending in this iteration.
- Test results: focused notification/CLI tests 9 OK; send-notification dry-run evidence emitted.
- Successes: Dry-run mode requires no secrets and makes no SMTP connection; real send blocks without env keys; mocked SMTP send starts TLS, logs in, sends to `linzezhang35@gmail.com`, and does not log password values in the report.
- Failures: none for focused tests; real production SMTP remains unverified because SMTP secrets and runner are not provisioned in this local environment.
- Decisions: Keep scheduler/workflow SMTP side effects disabled until production preflight and explicit production enablement exist.
- Remaining risks: Production acceptance still requires actual runner provisioning, CA trust fix, SMTP/Release configuration, preflight pass on runner, scheduled execution, weekly/monthly replay, recovery drill, and 30-day trial evidence.
- Rollback: Revert SMTP delivery command, schema, tests, and restore version 0.11.5.
- Next step: Run full project and governance validation, update run manifest, and sync the PR.

### `ITER-20260621-018`

- Date: 2026-06-21
- Fact level: EXTRACTED for Release delivery boundary code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.6
- Version after: 0.11.7
- Base commit: cf8af2b082385f118d40e34f03bd91af5d1c270e
- Result commit: PENDING
- Task IDs: ADP-PHASE11-RELEASE-DELIVERY-008
- Goal: Add a fail-closed GitHub Release delivery boundary with dry-run evidence and explicit real-upload gating.
- Assumptions: Release delivery must default to dry-run; real GitHub Release creation requires explicit `--allow-upload`, a configured target, safe assets, `gh`, no clobber upload, and no notes/stdout/stderr logging.
- Files changed: Release delivery code, CLI command, tests, Release delivery schema, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-017 as adp-release-delivery-v1.
- Parameter changes: Added PARAM-ADP-086 through PARAM-ADP-091.
- Commands run: focused Release/CLI tests; full project tests; schema parse; publish-release dry-run CLI; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: focused Release/CLI tests 9 OK; project tests 88 OK; schemas parse; publish-release dry-run evidence emitted; root governance tests 38 OK; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Dry-run mode makes no `gh` call; real upload blocks without `ADP_RELEASE_TARGET`; forbidden secret-like assets block before command execution; mocked `gh release create` succeeds without `--clobber` and without logging notes, stdout, or stderr.
- Failures: none for focused tests; real private Release delivery remains unverified because `gh` auth, runner, target, and production assets are not provisioned in this local environment.
- Decisions: Keep scheduled Release side effects disabled until production preflight and explicit production enablement exist.
- Remaining risks: Production acceptance still requires actual runner provisioning, CA trust fix, SMTP/Release configuration, preflight pass on runner, scheduled execution, weekly/monthly replay, recovery drill, and 30-day trial evidence.
- Rollback: Revert Release delivery command, schema, tests, and restore version 0.11.6.
- Next step: Run full project and governance validation, update run manifest, and sync the PR.

### `ITER-20260621-019`

- Date: 2026-06-21
- Fact level: EXTRACTED for scheduled production workflow gate, CLI validator, schema, tests, runbook, and governance updates.
- Version before: 0.11.7
- Version after: 0.11.8
- Base commit: fecc32812a863d151f0ea4070ebbb814ec62bc39
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-SCHEDULER-009
- Goal: Add a fail-closed scheduled production workflow gate for 04:45 health check, 05:00 daily run, and 05:10 watchdog in Australia/Sydney.
- Assumptions: GitHub Actions schedule supports IANA timezone fields; scheduled workflows run from the default branch; production work must remain disabled unless explicit GitHub variables are configured.
- Files changed: scheduled GitHub workflow, production scheduler validator, CLI command, tests, production scheduler schema, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-018 as adp-production-scheduler-v1.
- Parameter changes: Added PARAM-ADP-092 through PARAM-ADP-096.
- Commands run: focused scheduler/CLI tests; full project tests; schema parse; plan-production-scheduler CLI; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: focused scheduler/CLI tests 8 OK; project tests 91 OK; schemas parse; scheduler plan evidence emitted with status pass; root governance tests 39 OK; project governance errors 0 warnings 0; changed-only enforce-sync errors 0 warnings 0; dashboard PASS; git diff check exit 0.
- Successes: Workflow declares Australia/Sydney 04:45, 05:00, and 05:10 slots; scheduled runs skip unless `ADP_PRODUCTION_ENABLED=true`; preflight runs before scheduled mode; scheduled gate contains no SMTP send or Release upload commands.
- Failures: none for focused tests; real scheduled production remains unverified because workflow is not merged to default, production variables are not enabled, and private runner/preflight evidence is not present.
- Decisions: Use timezone-aware schedule syntax from current GitHub Actions documentation and keep scheduled production side effects disabled by default.
- Remaining risks: Production acceptance still requires actual default-branch scheduling, runner provisioning, CA trust fix, SMTP/Release configuration, preflight pass on runner, scheduled execution, weekly/monthly replay, recovery drill, and 30-day trial evidence.
- Rollback: Revert scheduled production workflow, scheduler validator, schema, tests, and restore version 0.11.7.
- Next step: Run full project and governance validation, update run manifest, and sync the PR.

### `ITER-20260621-020`

- Date: 2026-06-21
- Fact level: EXTRACTED for scheduled execution driver code, CLI command, workflow artifact wiring, schema, tests, runbook, and governance updates.
- Version before: 0.11.8
- Version after: 0.11.9
- Base commit: 04d7d9e
- Result commit: PENDING
- Task IDs: ADP-PHASE11-SCHEDULED-EXECUTION-010
- Goal: Add the controlled runtime bridge that produces scheduled health-check, daily-run, and watchdog evidence after production preflight.
- Assumptions: Scheduled execution must still fail closed unless preflight passes, daily-run is explicitly enabled, daily input exists, and real SMTP/Release evidence is produced.
- Files changed: scheduled execution driver, CLI command, scheduled GitHub workflow, scheduled execution schema, tests, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-019 as adp-scheduled-execution-v1 and updated MOD-ADP-018 scheduler validation to require the execution artifact.
- Parameter changes: Added PARAM-ADP-097 through PARAM-ADP-101.
- Commands run: focused scheduled execution/scheduler/CLI tests; full project tests; schema parse; run-scheduled-production health-check CLI; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: focused scheduled execution/scheduler/CLI tests 13 OK; final full validation recorded in the run manifest after this iteration.
- Successes: Health-check creates evidence after preflight; daily-run blocks until `ADP_SCHEDULED_RUN_ENABLED=true`; dry-run SMTP/Release produces degraded exit 2; mocked real SMTP and Release create production-ready evidence refs.
- Failures: none for focused tests; real production evidence remains unavailable without default-branch schedule, private runner, daily input, SMTP, Release, and resource evidence.
- Decisions: Keep the workflow free of `--allow-send` and `--allow-upload` flags; real side effects are only requested through explicit environment variables and dedicated transport validators.
- Remaining risks: Production acceptance still requires live source pass, real daily content generation input, SMTP/Release secrets, runner preflight pass, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
- Rollback: Revert scheduled execution driver, workflow execution artifact changes, schema, tests, and restore version 0.11.8.
- Next step: Provision runner variables/secrets and run a controlled preflight plus health-check evidence pass.

### `ITER-20260621-021`

- Date: 2026-06-21
- Fact level: EXTRACTED for daily input builder code, CLI command, scheduled workflow artifact wiring, schema, tests, runbook, and governance updates.
- Version before: 0.11.9
- Version after: 0.11.10
- Base commit: 267c879
- Result commit: PENDING
- Task IDs: ADP-PHASE11-DAILY-INPUT-BUILDER-011
- Goal: Add the deterministic bridge from live arXiv SourceBatch output to scheduled daily pipeline input.
- Assumptions: Daily input may only use arXiv Atom summary and metadata claims; it must not download PDFs, perform bulk harvest, infer peer review, send email, upload Releases, or claim 30-day production acceptance.
- Files changed: daily input builder, CLI command, scheduled execution compatibility, scheduled workflow source/daily-input artifacts, daily input schema, tests, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-020 as adp-daily-input-builder-v1 and updated MOD-ADP-018 scheduler validation to require daily input artifact wiring.
- Parameter changes: Added PARAM-ADP-102 through PARAM-ADP-107.
- Commands run: focused daily input/scheduled/scheduler/CLI tests; full project tests; schema parse; fixture build-daily-input CLI; root governance tests; project governance validator; changed-only enforce-sync; dashboard generation; git diff check.
- Test results: focused daily input/scheduled/scheduler/CLI tests: 18 tests OK; final full validation recorded in the run manifest after this iteration.
- Successes: Builder converts a fixture SourceBatch into a daily input package with P0 Atom summary evidence; missing summaries and recent duplicate selections block; scheduled daily-run accepts builder reports; scheduled workflow uploads source batch and daily input artifacts when no override path is set.
- Failures: none for focused tests; real production evidence remains unavailable without default-branch schedule, private runner, live source pass, SMTP, Release, and resource evidence.
- Decisions: Keep automatic daily input claims conservative and restricted to arXiv Atom metadata until a later evidence extraction phase is explicitly implemented.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release secrets and refs, weekly/monthly replay, recovery drill, resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Revert daily input builder, workflow source/daily-input artifact changes, schema, tests, and restore version 0.11.9.
- Next step: Provision runner variables/secrets and run a controlled preflight plus health-check/daily input evidence pass without claiming production acceptance.

### `ITER-20260621-022`

- Date: 2026-06-21
- Fact level: EXTRACTED for trial ledger updater code, CLI command, scheduled workflow artifact wiring, schema, tests, runbook, and governance updates.
- Version before: 0.11.10
- Version after: 0.11.11
- Base commit: 76d976b
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-LEDGER-012
- Goal: Add the deterministic bridge from production-ready scheduled daily-run evidence to the 30-day trial evidence ledger.
- Assumptions: Ledger updates may append one daily entry but must not claim 30-day acceptance until the embedded trial validator passes every gate.
- Files changed: trial ledger updater, CLI command, scheduled execution compatibility fields, scheduled workflow ledger artifact, trial ledger schema, tests, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-021 as adp-trial-ledger-v1 and updated MOD-ADP-018 scheduler validation to require the trial ledger update artifact.
- Parameter changes: Added PARAM-ADP-108 through PARAM-ADP-112.
- Commands run: focused trial ledger/scheduled/scheduler/CLI tests; workflow Build scheduled daily input bash syntax; workflow Update trial evidence ledger bash syntax. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial ledger and scheduled tests: 19 tests OK; workflow ledger step bash -n pass.
- Successes: Ledger update blocks non-production scheduled reports and duplicate daily evidence; it can upgrade global Release/SMTP/resource flags only when explicit production evidence is provided; scheduled workflow uploads a trial ledger update artifact after daily-run.
- Failures: none for focused tests; real production acceptance remains unavailable without default-branch schedule, private runner, live source pass, SMTP, Release, weekly/monthly, recovery, and 30-day evidence.
- Decisions: Keep weekly/monthly replay and recovery drill evidence outside automatic daily ledger updates.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
- Rollback: Revert trial ledger updater, workflow ledger artifact changes, schema, tests, and restore version 0.11.10.
- Next step: Provision runner variables/secrets and run controlled preflight plus production-ready daily evidence collection without claiming 30-day acceptance.

### `ITER-20260621-023`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial ledger state persistence workflow wiring, CLI exporter, tests, runbook, and governance updates.
- Version before: 0.11.11
- Version after: 0.11.12
- Base commit: 94f1d1f
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-LEDGER-STATE-013
- Goal: Carry the 30-day trial evidence ledger forward across scheduled GitHub Actions runs without retaining local media, model, secret, or cache artifacts.
- Assumptions: GitHub Actions artifact restore is the durable state channel; explicit configured state files take priority; blocked ledger updates must not overwrite the prior state artifact.
- Files changed: scheduled workflow state restore/export wiring, CLI export command, trial ledger and scheduler tests, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-022 as adp-trial-ledger-state-v1 and updated scheduler validation to require state artifact restore/export wiring.
- Parameter changes: Added PARAM-ADP-113 through PARAM-ADP-117.
- Commands run: focused trial ledger/scheduler/CLI tests; workflow Build scheduled daily input bash syntax; workflow Resolve trial ledger state bash syntax; workflow Update trial evidence ledger bash syntax; workflow Export trial evidence ledger state bash syntax; export-trial-ledger-state fixture CLI. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial ledger state tests: 15 tests OK; workflow restore/export bash -n pass; export-trial-ledger-state fixture CLI pass and JSON parse OK.
- Successes: Scheduled daily-run now restores prior `adp-trial-evidence-ledger` state when available, appends through `update-trial-ledger --path`, exports only the `trial_evidence` object after a successful append, and uploads a replacement state artifact only on export success.
- Failures: none for focused tests; real artifact restore remains unverified until the workflow runs on the default branch with retained artifacts.
- Decisions: Keep trial evidence state in GitHub Actions artifacts rather than Git, and never upload a replacement state artifact for blocked ledger updates.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
- Rollback: Revert trial ledger state restore/export workflow changes, export command, tests, and restore version 0.11.11.
- Next step: Provision runner variables/secrets and run controlled default-branch scheduled evidence collection with artifact retention.

### `ITER-20260621-024`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial operational evidence annotation code, CLI commands, tests, runbook, and governance updates.
- Version before: 0.11.12
- Version after: 0.11.13
- Base commit: f9cb3de
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-OPS-EVIDENCE-014
- Goal: Add an audited merge path for weekly/monthly replay, recovery drill, and other operational evidence refs without hand-editing trial evidence JSON.
- Assumptions: Operational evidence refs are produced by future controlled operations; this command only validates and merges explicit refs and cannot create the underlying weekly/monthly/recovery evidence.
- Files changed: trial ops annotator, CLI commands, tests, runtime example, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-023 as adp-trial-ops-evidence-v1.
- Parameter changes: Added PARAM-ADP-118 through PARAM-ADP-122.
- Commands run: focused trial ops/trial/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial ops tests: 16 tests OK.
- Successes: The annotator merges weekly/monthly replay and recovery refs, can unlock the final trial validator when complete daily evidence already exists, blocks verified flags without refs, and blocks exporting unupdated evidence.
- Failures: none for focused tests; real weekly/monthly replay and recovery drill remain unverified until controlled production operations emit durable refs.
- Decisions: Keep operational evidence annotation as explicit-ref-only; do not infer that replay or recovery occurred from the existence of daily ledger state.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
- Rollback: Revert trial ops annotator, CLI commands, tests, runbook/docs/governance updates, and restore version 0.11.12.
- Next step: Provision runner variables/secrets and run controlled default-branch scheduled evidence collection with explicit weekly/monthly and recovery evidence refs.

### `ITER-20260621-025`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial replay evidence code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.13
- Version after: 0.11.14
- Base commit: 010e9ba
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-REPLAY-EVIDENCE-015
- Goal: Add an audited weekly/monthly replay evidence builder from accumulated production daily trial entries.
- Assumptions: Replay evidence must be generated from production-ready daily refs and archived under a durable ref before it can be merged into trial evidence.
- Files changed: trial replay builder, CLI command, replay schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-024 as adp-trial-replay-v1.
- Parameter changes: Added PARAM-ADP-123 through PARAM-ADP-127.
- Commands run: focused trial replay/trial ops/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial replay tests: 16 tests OK.
- Successes: The replay builder validates production daily refs, duplicate-free daily coverage, 7 consecutive days for weekly replay, 30 consecutive days for monthly replay, and durable replay refs before emitting annotation hints.
- Failures: Initial monthly replay logic trusted a lowered `period.expected_days`; focused tests caught it and the implementation now requires at least 30 days.
- Decisions: Keep replay evidence generation separate from trial evidence mutation; `annotate-trial-ops-evidence` remains the only merge path.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, resource telemetry, recovery drill, actual archived weekly/monthly replay evidence, and 30 unique daily production evidence entries.
- Rollback: Revert trial replay builder, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.13.
- Next step: Provision runner variables/secrets and run controlled default-branch scheduled evidence collection with replay and recovery artifacts.

### `ITER-20260621-026`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial recovery evidence code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.14
- Version after: 0.11.15
- Base commit: c28ea57
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-016
- Goal: Add an audited recovery drill evidence builder from failed/degraded and recovered scheduled daily-run reports.
- Assumptions: Recovery evidence must be generated from archived scheduled execution reports with real sent notifications and durable refs before it can be merged into trial evidence.
- Files changed: trial recovery builder, CLI command, recovery schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-025 as adp-trial-recovery-v1.
- Parameter changes: Added PARAM-ADP-128 through PARAM-ADP-132.
- Commands run: focused trial recovery/replay/ops/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial recovery/replay/ops/CLI tests: 21 tests OK.
- Successes: The recovery builder validates failed or degraded scheduled execution evidence, real sent failure/recovery notifications, production-ready recovery refs, durable failure/recovery refs, and date consistency before emitting annotation hints.
- Failures: none for focused tests; real production recovery drill remains unverified until controlled production operations emit durable refs.
- Decisions: Keep recovery evidence generation separate from scheduler execution and trial evidence mutation; `annotate-trial-ops-evidence` remains the only merge path.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, resource telemetry, archived weekly/monthly replay evidence, archived recovery drill evidence, and 30 unique daily production evidence entries.
- Rollback: Revert trial recovery builder, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.14.
- Next step: Provision runner variables/secrets and run controlled default-branch scheduled evidence collection with replay and recovery artifacts.

### `ITER-20260621-027`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial resource evidence code, timestamped preflight resource refs, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.15
- Version after: 0.11.16
- Base commit: 750155b
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-RESOURCE-EVIDENCE-017
- Goal: Add an audited resource telemetry evidence builder for 30-day trial daily resource refs.
- Assumptions: Global resource evidence must be generated from 30 unique daily resource refs that match passing production preflight reports and a durable resource evidence ref before it can be merged into trial evidence.
- Files changed: trial resource builder, production preflight resource ref generation, CLI command, resource schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-026 as adp-trial-resource-v1.
- Parameter changes: Added PARAM-ADP-133 through PARAM-ADP-137.
- Commands run: focused trial resource/preflight/scheduled/ops/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial resource/preflight/scheduled/ops/CLI tests: 27 tests OK.
- Successes: The resource builder validates 30 unique daily resource refs, matching passing production preflight reports, required resource gates, durable resource refs, and blocks lowered expected-day attempts.
- Failures: none for focused tests; real 30-day production resource telemetry remains unverified until controlled production operations emit durable refs.
- Decisions: Use timestamped production preflight resource refs so every daily run can be matched to its own resource gate evidence.
- Remaining risks: Production acceptance still requires live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Revert trial resource builder, timestamped preflight resource ref change, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.15.
- Next step: Provision runner variables/secrets and run controlled default-branch scheduled evidence collection with resource, replay, and recovery artifacts.

### `ITER-20260621-028`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial start gate code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.16
- Version after: 0.11.17
- Base commit: 4e572b8
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-START-GATE-018
- Goal: Add an audited start-readiness gate for the real 30-day production trial.
- Assumptions: A real trial may be marked start-ready only after production preflight, bootstrap, scheduler, live source ingest, real SMTP, real Release, durable refs, and explicit confirmation all pass.
- Files changed: trial start gate, CLI command, schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-027 as adp-trial-start-v1.
- Parameter changes: Added PARAM-ADP-138 through PARAM-ADP-143.
- Commands run: focused trial start/bootstrap/scheduler/preflight/source/SMTP/Release/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial start/bootstrap/scheduler/preflight/source/SMTP/Release/CLI tests: 34 tests OK.
- Successes: The start gate validates all required upstream reports, real SMTP and Release probes, durable refs, explicit confirmation, and blocks dry-run or incomplete start evidence.
- Failures: none for focused tests; real default-branch trial start evidence remains unverified until controlled production operations archive durable refs.
- Decisions: Keep trial start as a no-side-effect gate so setup can be audited before enabling daily production evidence collection.
- Remaining risks: Production acceptance still requires default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Revert trial start gate, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.16.
- Next step: Run controlled default-branch trial start evidence after runner variables/secrets and durable refs are provisioned.

### `ITER-20260621-029`

- Date: 2026-06-22
- Fact level: EXTRACTED for trial start workflow, validator code, CLI command, schema, tests, runbook, and governance updates.
- Version before: 0.11.17
- Version after: 0.11.18
- Base commit: 6caec78
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-START-WORKFLOW-019
- Goal: Add an audited manual default-branch workflow that can collect trial start evidence artifacts after runner variables, SMTP secrets, and Release target are provisioned.
- Assumptions: The workflow remains manual-only, preflight-first, artifact-backed, and cannot run real SMTP or Release probes unless explicit GitHub variables enable them.
- Files changed: trial start workflow, workflow validator, CLI command, workflow schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-028 as adp-trial-start-workflow-v1.
- Parameter changes: Added PARAM-ADP-144 through PARAM-ADP-148.
- Commands run: focused trial start workflow/start/bootstrap/scheduler/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused trial start workflow/start/bootstrap/scheduler/CLI tests: 20 tests OK.
- Successes: The workflow validator checks manual dispatch, confirmation gate, private runner targeting, preflight-first ordering, source-before-delivery ordering, complete artifact uploads, durable start refs, side-effect vars, and secret safety.
- Failures: none for focused tests; real workflow evidence remains unverified until the workflow is merged to default branch and run on the private runner with configured GitHub variables/secrets.
- Decisions: Keep the workflow dispatch explicit and leave SMTP/Release side effects disabled unless `ADP_ALLOW_SMTP_SEND` and `ADP_ALLOW_RELEASE_UPLOAD` are true for a controlled start probe.
- Remaining risks: Production acceptance still requires a passing default-branch trial start workflow run, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Revert trial start workflow, validator, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.17.
- Next step: Merge to default branch, provision runner/secrets/vars, run the manual trial start workflow, archive `adp-trial-start-gate`, then begin controlled 30-day evidence collection.

### `ITER-20260621-030`

- Date: 2026-06-22
- Fact level: EXTRACTED for production launch readiness code, CLI command, schema, tests, runbook, and governance updates; EXTRACTED from GitHub connector for current PR #14 draft/unmerged state.
- Version before: 0.11.18
- Version after: 0.11.19
- Base commit: fc5a100
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-LAUNCH-READINESS-020
- Goal: Add an audited launch readiness gate before dispatching the default-branch trial start workflow.
- Assumptions: Launch may proceed only after PR #14 is non-draft and merged to `main`, the expected head SHA is bound, the trial start workflow contract is ready, and runner/secrets/Release/vars/default-branch refs are durable.
- Files changed: production launch readiness gate, CLI command, launch schema, tests, runbook, README, CHANGELOG, phase record, version files, and governance records.
- Model changes: Added MOD-ADP-029 as adp-production-launch-readiness-v1.
- Parameter changes: Added PARAM-ADP-149 through PARAM-ADP-153.
- Commands run: focused production launch/workflow/CLI tests. Full validation is recorded in the run manifest after this iteration.
- Test results: focused production launch/workflow/CLI tests: 12 tests OK.
- Successes: The launch gate validates PR merged/non-draft state, expected head SHA binding, trial start workflow readiness, durable external readiness refs, explicit launch confirmation, and no secret/auth/side-effect behavior.
- Failures: none for focused tests; current PR #14 is draft and unmerged, so real launch readiness correctly remains blocked.
- Decisions: Keep launch readiness as an explicit input gate that consumes current PR metadata JSON and durable readiness refs rather than merging PRs, dispatching workflows, or reading secret values.
- Remaining risks: Production launch still requires PR ready/merge, private runner provisioning, GitHub secrets and vars, default-branch workflow dispatch, real SMTP/Release evidence, and archived start-gate artifacts; production acceptance still requires 30 unique daily production evidence entries plus replay, recovery, and resource evidence.
- Rollback: Revert production launch readiness gate, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.18.
- Next step: Mark PR ready, merge to `main`, provision runner/secrets/vars, rerun `plan-production-launch` with durable refs, then dispatch the default-branch trial start workflow.

### `ITER-20260621-031`

- Date: 2026-06-22
- Fact level: EXTRACTED for latest main governance requirements and root `semantic_coverage` validation behavior; PLANNED for future arXiv semantic extractor work.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: 21f97f2
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Synchronize PR #14 with the latest `main` governance semantic coverage rollout contract without changing arXiv Daily Push runtime behavior.
- Assumptions: arXiv Daily Push cannot claim `machine_verified` semantic coverage until active parameter values and formula implementation fingerprints are extracted and validated by a dedicated machine extractor.
- Files changed: root semantic coverage project registry entry, arXiv delivery task binding, generated dashboard/status/owner status views, run manifest, and governance ledger records.
- Model changes: No runtime model behavior change.
- Parameter changes: No active parameter value change.
- Commands run: pending final validation after merge conflict resolution and generated status refresh.
- Test results: semantic extractor checked 93 active parameters and 31 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 86 OK; arXiv unit tests 143 OK; dashboard generation PASS after temporarily restoring full registered project validation context; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; `git diff --check` exit 0; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 222M, `arxiv-daily-push` 1.7M, `.git` 90M.
- Successes: The semantic coverage rollout is task-bound and explicitly non-terminal, preventing the project from silently bypassing the new root governance gate.
- Failures: none recorded yet; semantic extraction remains unimplemented and therefore planned.
- Decisions: Keep `semantic_extractors` disabled for arXiv Daily Push until extractor evidence exists; do not mark semantic coverage as machine verified in this merge-sync increment.
- Remaining risks: Production launch still requires PR ready/merge, private runner provisioning, GitHub secrets and vars, default-branch workflow dispatch, real SMTP/Release evidence, and archived start-gate artifacts; production acceptance still requires 30 unique daily production evidence entries plus replay, recovery, and resource evidence.
- Rollback: Remove the arXiv `semantic_coverage` block, `GOV-SEMANTIC-ADP-001` task, generated owner/status changes, run manifest, and this ledger/event update.
- Next step: After governance validation passes, finish merging latest `main` into PR #14, push, then reassess ready/merge and default-branch trial-start prerequisites.

### `ITER-20260621-032`

- Date: 2026-06-22
- Fact level: EXTRACTED from GitHub PR #14 merge metadata, local `main`, workflow file presence, workflow run/status checks, and the `plan-production-launch` post-merge gate result.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: 9616264221cecc8077fc862692ec6025f1e4872b
- Result commit: PENDING
- Task IDs: ADP-PHASE11-POST-MERGE-LAUNCH-AUDIT-021
- Goal: Record the post-merge production launch audit after PR #14 was merged to `main`.
- Assumptions: This iteration must not dispatch workflows, provision runners, read or write secrets, send SMTP mail, create Releases, or claim 30-day production acceptance.
- Files changed: post-merge phase record, delivery plan/task records, development ledger/status, production trial runbook, development event, run manifest, and generated governance dashboard/status views.
- Model changes: No runtime model behavior change.
- Parameter changes: No active parameter value change.
- Commands run: `plan-production-launch` with merged PR #14 metadata and expected head SHA; arXiv unit tests; root governance tests; project governance validator; dashboard generator; changed-only enforce-sync semantic validator; `git diff --check`; project cache scan; storage check.
- Test results: launch gate expected blocked with PR/default-branch gates passing and only `launch_confirmed`, `default_branch_ref`, `runner_ref`, `smtp_secret_ref`, `release_target_ref`, `workflow_vars_ref`, and `trial_start_workflow_ref` missing; 143 arXiv tests OK; 83 root governance tests OK; project governance errors 0 warnings 0; changed-only enforce-sync semantic errors 0 warnings 0; dashboard generation PASS; diff check exit 0; no arXiv `__pycache__` or `.pyc`; pre-shrink storage arXiv 1.6M, `.git` 89M, worktree 221M.
- Successes: PR #14 is merged; local `main` is at merge commit `9616264221cecc8077fc862692ec6025f1e4872b`; workflow files are present on default branch; post-merge `plan-production-launch` no longer blocks on draft/unmerged PR or head SHA mismatch.
- Failures: No workflow runs or combined status checks exist for the merge commit; launch still blocks because durable external refs and explicit confirmation are missing.
- Decisions: Do not dispatch the trial start workflow until durable refs and explicit launch confirmation are available.
- Remaining risks: Semantic coverage remains planned and not machine verified; production acceptance still requires default-branch trial start evidence, live source pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
- Rollback: Revert the post-merge phase record, delivery task, ledger/status/runbook updates, run manifest, event record, and generated dashboard/status changes.
- Next step: Provision or record durable readiness refs for runner, SMTP secrets, Release target, workflow variables, default-branch workflow location, and launch confirmation; then rerun `plan-production-launch` before dispatching the trial start workflow.

### `ITER-20260621-033`

- Date: 2026-06-22
- Fact level: EXTRACTED for machine selector/fingerprint validation and HUMAN_REVIEW_REQUIRED remainder binding.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: b52b88c1c7eadba64cb98fef655edc828f92b751
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Move arXiv Daily Push semantic coverage from planned to in-progress without changing runtime behavior.
- Assumptions: Partial semantic extraction is valuable only when machine selectors point at implementation/config/test surfaces, not at the governance registry itself.
- Files changed: governance project registry, arXiv parameter registry semantic columns, formula registry semantic fields, delivery task, version matrix, ledger/status, run manifest, and root governance tests/dashboard.
- Model changes: No runtime model behavior change.
- Parameter changes: No active parameter value change; semantic metadata added for 45 active parameter selectors.
- Commands run: `validate_semantic_extractors.py arxiv-daily-push`; `validate_project_governance.py --project arxiv-daily-push`; root governance unittest discover; arXiv unit test discover; `generate_governance_dashboard.py --write`; `validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`; `git diff --check`; arXiv cache scan; storage check.
- Test results: semantic extractor checked 45 active parameters and 9 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 84 OK; arXiv unit tests 143 OK; dashboard generation PASS; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; `git diff --check` exit 0; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 221M, `arxiv-daily-push` 1.7M, `.git` 89M.
- Successes: `validate_semantic_extractors.py arxiv-daily-push` checks 45 active parameters and 9 active formula fingerprints with no errors; the all-project semantic drift gate also passes after temporarily restoring full registered project validation context.
- Failures: 107 active parameters and 22 active formulas still require follow-up machine selectors or explicit human review before semantic coverage can become machine_verified.
- Decisions: Keep semantic coverage `in_progress` and keep `GOV-SEMANTIC-ADP-001` open until the remaining semantic surface is resolved.
- Remaining risks: Production launch and production acceptance remain blocked by external refs, runner/secrets/Release evidence, trial start evidence, and 30-day operational evidence.
- Rollback: Remove ArXiv semantic extractor enablement, semantic registry columns/fields, semantic run manifest/event, generated status/dashboard changes, and this test update.
- Next step: Expand selectors for the remaining active parameters/formulas or decide which should stay as owner-approved HUMAN_REVIEW_REQUIRED.

### `ITER-20260621-034`

- Date: 2026-06-22
- Fact level: EXTRACTED for additional machine selector/fingerprint validation and HUMAN_REVIEW_REQUIRED remainder binding.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: cc893e4e11ffe690a8f0d6010053c7a1ab5a09b4
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Expand arXiv Daily Push semantic coverage without changing runtime behavior.
- Assumptions: Remaining parameters that describe external production refs, operational evidence, or composite behavioral assertions stay HUMAN_REVIEW_REQUIRED until a durable source selector is explicit.
- Files changed: arXiv parameter registry semantic columns, formula registry semantic fields, governance project registry, delivery task, version matrix, ledger/status, run manifest, development event, and root governance tests/dashboard.
- Model changes: No runtime model behavior change.
- Parameter changes: No active parameter value change; semantic metadata added for 27 more active parameter selectors.
- Commands run: `validate_semantic_extractors.py arxiv-daily-push`; `validate_project_governance.py --project arxiv-daily-push`; root governance unittest discover; arXiv unit test discover; `generate_governance_dashboard.py --write`; `validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`; `git diff --check`; arXiv cache scan; storage check.
- Test results: semantic extractor checked 72 active parameters and 31 active formulas with no errors; project governance errors 0 warnings 0 after temporarily restoring full registered project validation context; root governance tests 85 OK; arXiv unit tests 143 OK; dashboard generation PASS; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; `git diff --check` exit 0 after LF normalization; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 221M, `arxiv-daily-push` 1.7M, `.git` 89M.
- Successes: `validate_semantic_extractors.py arxiv-daily-push` checks 72 active parameters and all 31 active formula fingerprints with no errors; the all-project semantic drift gate also passes after temporarily restoring full registered project validation context.
- Failures: 80 active parameters still require follow-up machine selectors or explicit human review before semantic coverage can become machine_verified.
- Decisions: Keep semantic coverage `in_progress` and keep `GOV-SEMANTIC-ADP-001` open until the remaining parameter surface is resolved.
- Remaining risks: Production launch and production acceptance remain blocked by external refs, runner/secrets/Release evidence, trial start evidence, and 30-day operational evidence.
- Rollback: Remove the second semantic extractor expansion, `GOV-SEMANTIC-ADP-EXTRACT-002.json`, generated status/dashboard changes, event update, and this test update.
- Next step: Resolve the remaining 80 parameters through machine selectors where possible, then provision durable production launch refs before trial start.

### `ITER-20260621-035`

- Date: 2026-06-22
- Fact level: EXTRACTED for additional existing-selector parameter validation and HUMAN_REVIEW_REQUIRED remainder binding.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: 579b9a0b621ac7b1cb8b26216664ec3eda1b920c
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Narrow the remaining arXiv Daily Push semantic review surface without changing runtime behavior.
- Assumptions: Only direct existing selectors that matched `active_value` in preflight are promoted to MACHINE_VERIFIED; production refs, real delivery probes, composite behavioral assertions, and 30-day operating evidence remain HUMAN_REVIEW_REQUIRED.
- Files changed: arXiv parameter registry semantic columns, governance project registry, delivery task, version matrix, ledger/status, run manifest, development event, and root governance tests/dashboard.
- Model changes: No runtime model behavior change.
- Parameter changes: No active parameter value change; semantic metadata added for 21 more active parameter selectors.
- Commands run: `validate_semantic_extractors.py arxiv-daily-push`; `validate_project_governance.py --project arxiv-daily-push`; root governance unittest discover; arXiv unit test discover; `generate_governance_dashboard.py --write`; `validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`; `git diff --check`; arXiv cache scan; storage check.
- Test results: semantic extractor checked 93 active parameters and 31 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 86 OK; arXiv unit tests 143 OK; dashboard generation PASS after temporarily restoring full registered project validation context; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; `git diff --check` exit 0; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 222M, `arxiv-daily-push` 1.7M, `.git` 90M.
- Successes: Existing selector preflight promoted run/stage enums, arXiv adapter id, media/download disabled gates, scheduler workflow fields, trial-day constants, and trial-start manual confirmation to machine-checked evidence.
- Failures: 59 active parameters still require follow-up machine selectors, explicit owner review, or external production evidence before semantic coverage can become machine_verified.
- Decisions: Keep semantic coverage `in_progress` and keep `GOV-SEMANTIC-ADP-001` open until the remaining parameter surface is resolved.
- Remaining risks: Production launch and production acceptance remain blocked by external refs, runner/secrets/Release evidence, trial start evidence, and 30-day operational evidence.
- Rollback: Remove the third semantic extractor expansion, `GOV-SEMANTIC-ADP-EXTRACT-003.json`, generated status/dashboard changes, event update, and this test update.
- Next step: Either add narrowly scoped selector transforms for composite remaining parameters or provision durable production launch refs before trial start.

### `ITER-20260621-036`

- Date: 2026-06-22
- Fact level: EXTRACTED for selector transform behavior, additional parameter validation, and HUMAN_REVIEW_REQUIRED remainder binding.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: 662451767eb280765ea01f0d08bf7f54c2add0ec
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Add narrowly scoped semantic selector transforms and reduce the remaining arXiv Daily Push review surface without changing runtime behavior.
- Assumptions: `contains`, `contains_all`, `filter`, and ordered join transforms only inspect deterministic source/config/workflow text and constants; parameters that depend on real external refs or production evidence remain HUMAN_REVIEW_REQUIRED.
- Files changed: semantic extractor validator, root governance tests, arXiv parameter registry semantic columns, governance project registry, delivery task, version matrix, ledger/status, run manifest, development event, and dashboard.
- Model changes: No arXiv Daily Push runtime model behavior change; root semantic extractor selector behavior expanded for governance validation only.
- Parameter changes: No active parameter value change; semantic metadata added for 38 more active parameter selectors.
- Commands run: selector transform focused tests; `validate_semantic_extractors.py arxiv-daily-push`; `validate_project_governance.py --project arxiv-daily-push`; root governance unittest discover; arXiv unit test discover; `generate_governance_dashboard.py --write`; `validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`; `git diff --check`; arXiv cache scan; storage check.
- Test results: selector transform focused tests 2 OK; semantic extractor checked 131 active parameters and 31 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 88 OK; arXiv unit tests 143 OK; dashboard generation PASS after temporarily restoring full registered project validation context; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; manifest JSON and `git diff --check` pass; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 222M, `arxiv-daily-push` 1.8M, `.git` 90M.
- Successes: Selector transforms can now machine-check source text containment, subset filtering, and deterministic set ordering; 38 additional active parameters are machine-checked.
- Failures: 21 active parameters still require follow-up machine selectors, explicit owner review, or external production evidence before semantic coverage can become machine_verified.
- Decisions: Keep semantic coverage `in_progress` and keep `GOV-SEMANTIC-ADP-001` open.
- Remaining risks: Production launch and production acceptance remain blocked by external refs, runner/secrets/Release evidence, trial start evidence, and 30-day operational evidence.
- Rollback: Revert the selector transform changes, remove the fourth semantic extractor expansion, `GOV-SEMANTIC-ADP-EXTRACT-004.json`, generated status/dashboard changes, event update, and test update.
- Next step: Resolve the remaining external/composite parameters or provision durable production launch refs before trial start.

### `ITER-20260621-037`

- Date: 2026-06-22
- Fact level: EXTRACTED for final semantic selector behavior, active parameter validation, and machine_verified coverage binding.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: d7ad354519374946c70440abae213410c2cb061d
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-ADP-001
- Goal: Complete machine semantic coverage for arXiv Daily Push active parameters and formulas without changing runtime behavior.
- Assumptions: Final selectors inspect deterministic source/config/workflow text and Python AST constants only; external production evidence remains outside semantic registry completion and still blocks Phase 11 production acceptance.
- Files changed: semantic extractor validator, root governance tests, arXiv parameter registry semantic columns, governance project registry, delivery task, version matrix, ledger/status, run manifest, development event, and dashboard.
- Model changes: No arXiv Daily Push runtime model behavior change; root semantic extractor selector behavior expanded for governance validation only.
- Parameter changes: No active parameter value change; semantic metadata added for the final 21 active parameter selectors.
- Commands run: selector transform focused test; selector probe for the final 21 parameters; `validate_semantic_extractors.py arxiv-daily-push`; `validate_project_governance.py --project arxiv-daily-push`; root governance unittest discover; arXiv unit test discover; `generate_governance_dashboard.py --write`; `validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`; manifest JSON parse; `git diff --check`; arXiv cache scan; storage check.
- Test results: selector transform focused test 1 OK; selector probe matched all final 21 active parameter values; semantic extractor checked 152 active parameters and 31 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 89 OK; arXiv unit tests 143 OK; dashboard generation PASS after temporarily restoring full registered project validation context; changed-only enforce-sync semantic errors 0 warnings 0 with `arxiv-daily-push` changed and all registered project validation errors 0 warnings 0; manifest JSON parse passed; `git diff --check` passed after EOF cleanup; no arXiv `__pycache__` or `.pyc`; pre-shrink storage worktree 222M, `arxiv-daily-push` 1.8M, `.git` 90M.
- Successes: All 152 active parameters and all 31 active formulas machine-check under `GOV-SEMANTIC-ADP-001`; next tracked task is external production trial start provisioning.
- Failures: No active semantic registry rows remain HUMAN_REVIEW_REQUIRED; production launch and production acceptance remain blocked by external runner/secrets/Release/workflow/trial evidence.
- Decisions: Mark semantic coverage `machine_verified` and complete `GOV-SEMANTIC-ADP-001`; keep production launch/30-day acceptance blocked until real external evidence exists.
- Remaining risks: Production launch and production acceptance remain blocked by external refs, runner/secrets/Release evidence, trial start evidence, and 30-day operational evidence.
- Rollback: Revert the final selector transform changes, remove the fifth semantic extractor expansion, `GOV-SEMANTIC-ADP-EXTRACT-005.json`, generated status/dashboard changes, event update, and test update.
- Next step: Provision durable production refs and run the default-branch trial start workflow with explicit confirmation.

### `ITER-20260621-038`

- Date: 2026-06-22
- Fact level: EXTRACTED from GitHub PR #32 metadata, main Project Governance CI metadata, local default-branch workflow file presence, and the `plan-production-launch` precheck result.
- Version before: 0.11.19
- Version after: 0.11.19
- Base commit: df28c70f255d4db0cabf15d6555ce34a8b2fa560
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Record a no-secret production trial start precheck after PR #32 merged to `main`.
- Assumptions: `default_branch_ref` and `trial_start_workflow_ref` can be proven from current Git/default-branch state without reading secrets or dispatching workflows; private runner, SMTP secret, Release target, workflow variable readiness, and explicit launch confirmation still require external owner-provisioned refs.
- Files changed: production trial start precheck phase record, run manifest, development event, delivery task/status sources, runbook, version matrix, and generated governance dashboard/status files.
- Model changes: No arXiv Daily Push runtime model behavior change.
- Parameter changes: No active parameter value change.
- Commands run: GitHub PR #32 metadata fetch; GitHub Actions run lookup for merge commit `df28c70f255d4db0cabf15d6555ce34a8b2fa560`; `plan-production-launch` with PR #32 metadata, expected head SHA, merged default-branch ref, and default-branch trial-start workflow ref; focused production launch/workflow/CLI tests; arXiv unit test discover; root governance unittest discover; dashboard generation; project governance validation; changed-only enforce-sync semantic validation; `git diff --check`.
- Test results: PR #32 metadata shows closed/merged/non-draft/base main with head SHA `426709648fde32bbaf0d0a1f4f6006318891f5f2` and merge commit `df28c70f255d4db0cabf15d6555ce34a8b2fa560`; main Project Governance CI run `27913796642` completed success with attestation artifact `project-governance-ci-attestation-27913796642-1`; launch precheck exited 2 as expected, with PR/default-branch/workflow gates passing and only `launch_confirmed`, `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref` blocking; focused production launch/workflow/CLI tests 12 OK; arXiv unit tests 143 OK; root governance tests 91 OK; dashboard generation PASS; project governance errors 0 warnings 0; changed-only enforce-sync semantic errors 0 warnings 0 with all registered project validation errors 0 warnings 0; `git diff --check` pass.
- Successes: `default_branch_ref` and `trial_start_workflow_ref` are now durable and recorded without reading secrets or triggering production side effects.
- Failures: Production launch remains blocked by missing explicit launch confirmation and missing durable runner, SMTP secret, Release target, and workflow variable readiness refs.
- Decisions: Keep `ADP-PHASE11-PRODUCTION-TRIAL-START-022` blocked until remaining external refs exist; do not dispatch `.github/workflows/arxiv-daily-push-trial-start.yml` yet.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove the precheck phase record, run manifest, development event, runbook/status/delivery task updates, and generated dashboard/status changes.
- Next step: Provision durable `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`; then rerun `plan-production-launch` with `--confirm-launch`.

### `ITER-20260621-039`

- Date: 2026-06-22
- Fact level: EXTRACTED from production refs code, CLI command, schema, tests, runbook, and machine semantic registry validation.
- Version before: 0.11.19
- Version after: 0.11.20
- Base commit: 468738d44a2bf99b6fbdebaab85d7360ab731f4f
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-REFS-BUNDLE-023
- Goal: Add a no-secret production refs readiness bundle before default-branch launch readiness consumes external runner, SMTP, Release, and workflow variable refs.
- Assumptions: The bundle may validate names, ready flags, labels, targets, and durable refs, but it must not read or store SMTP hosts, SMTP ports, usernames, passwords, tokens, API keys, Codex auth, or any credential values.
- Files changed: production refs validator, CLI command and launch integration, production refs schema, focused tests, runbook section, phase record, changelog/version files, model/formula/parameter/traceability registries, delivery task, delivery plan, model spec, and development ledger.
- Model changes: Added MOD-ADP-030 `adp-production-refs-v1`; updated FORM-ADP-024 fingerprint because `cli.py::main` changed; added FORM-ADP-032.
- Parameter changes: Added PARAM-ADP-154 through PARAM-ADP-159 for production refs validator id, required SMTP secret names, required workflow var names, required ref keys, secret-value key blocklist, and no-side-effect safety.
- Commands run: focused production refs/launch pytest; semantic extractor validation; project governance validation; pending full local validation and GitHub CI.
- Test results: focused production refs/launch pytest 9 OK; semantic extractor checked 158 active parameters and 32 active formulas with no errors; project governance content errors reduced to sparse-checkout missing registered project noise plus generated view sync before final pass.
- Successes: `plan-production-refs` now blocks missing required names and secret-like payloads, emits a no-side-effect readiness report, and `plan-production-launch` can consume a passing refs report to fill external readiness refs.
- Failures: No real owner-provisioned runner/SMTP/Release/workflow refs were available in this run; production launch and 30-day acceptance remain blocked.
- Decisions: Keep `ADP-PHASE11-PRODUCTION-TRIAL-START-022` blocked until a real passing production refs report, explicit launch confirmation, and default-branch trial-start workflow evidence exist.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Revert production refs module, CLI integration, schema, tests, runbook/phase record/governance updates, and restore version 0.11.19.
- Next step: Provision owner-approved durable `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref` through `plan-production-refs`, then rerun `plan-production-launch --confirm-launch`.

### `ITER-20260621-040`

- Date: 2026-06-22
- Fact level: EXTRACTED from workflow permissions, scheduler/workflow validators, focused tests, and semantic registry checks.
- Version before: 0.11.20
- Version after: 0.11.21
- Base commit: 4795473858926de7e8e2b9f3eb4e8346ca3a20a2
- Result commit: PENDING
- Task IDs: ADP-PHASE11-RELEASE-PERMISSIONS-024, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Require GitHub Actions `contents: write` for the controlled Release evidence paths used by trial-start and scheduled production workflows.
- Assumptions: The permission is necessary for real draft Release evidence, but does not authorize upload by itself; `ADP_ALLOW_RELEASE_UPLOAD=true`, Release target, safe assets, `gh`, and Release delivery validation are still required.
- Files changed: trial-start workflow, scheduled production workflow, scheduler validator, trial-start workflow validator, focused tests, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, and run manifest.
- Model changes: No new runtime model; MOD-ADP-018 and MOD-ADP-028 now include machine-checked Release write permission parameters.
- Formula changes: Refreshed FORM-ADP-020 and FORM-ADP-030 implementation fingerprints after adding Release write permission checks.
- Parameter changes: Added PARAM-ADP-160 and PARAM-ADP-161 for scheduled and trial-start workflow `contents: write` permission requirements.
- Commands run: focused workflow/scheduler tests; trial-start workflow plan CLI JSON parse; production scheduler plan CLI JSON parse; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check.
- Test results: focused workflow/scheduler tests 6 OK; trial-start workflow plan JSON OK; production scheduler plan JSON OK; semantic extractor checked 160 active parameters and 32 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 93 OK; arXiv unit tests 148 OK; changed-only enforce-sync semantic validation errors 0 warnings 0 across all registered projects; manifest JSON and development_events JSONL parse OK; git diff check OK.
- Successes: Real Release evidence paths will no longer fail only because workflow token permissions are read-only.
- Failures: No workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch blocked until external refs and explicit confirmation exist; keep Release upload disabled by default despite `contents: write`.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Restore workflow `contents` permissions to read, remove release write permission checks, remove PARAM-ADP-160/161, phase record, manifest, and related governance updates, then restore version 0.11.20.
- Next step: Provision owner-approved durable `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`; run `plan-production-refs`, then rerun `plan-production-launch --confirm-launch`.

### `ITER-20260621-041`

- Date: 2026-06-22
- Fact level: EXTRACTED from production refs template code, CLI output, no-secret example JSON, focused tests, and semantic registry checks.
- Version before: 0.11.21
- Version after: 0.11.22
- Base commit: bd3512a3ee85d9b943fa1bf9ef39e7c1fc02cb6c
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-REFS-TEMPLATE-025, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Add a no-secret owner-fillable production refs input template so external runner, SMTP secret-name, Release target, and workflow variable refs can be provisioned without hand-writing the JSON contract or exposing secret values.
- Assumptions: The template may include required GitHub secret names and workflow variable names, but must not include SMTP host values, SMTP port values, usernames, passwords, tokens, API keys, Codex auth, or credential blobs.
- Files changed: production refs module, CLI command, no-secret example input JSON, focused tests, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, and run manifest.
- Model changes: No new runtime model; MOD-ADP-030 now also generates the no-secret input template for the same production refs readiness contract.
- Formula changes: Refreshed FORM-ADP-024 because `cli.py::main` changed, and refreshed FORM-ADP-032 after adding `build_production_refs_input_template`.
- Parameter changes: Added PARAM-ADP-162 for required production refs template sections.
- Commands run: focused production refs/launch/CLI tests; print-production-refs-template JSON parse; generated template through plan-production-refs expected blocked path; example JSON parse; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check; cache check.
- Test results: focused production refs/launch/CLI tests 16 OK; print-production-refs-template JSON OK; generated template plan-production-refs blocked as expected; example production refs JSON parsed OK; semantic extractor checked 161 active parameters and 32 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 94 OK; arXiv unit tests 150 OK; changed-only enforce-sync semantic validation errors 0 warnings 0 across all registered projects; manifest JSON and development_events JSONL parse OK; git diff check OK; no __pycache__, pyc, pytest, mypy, or ruff cache files remained.
- Successes: Owner provisioning now has a deterministic no-secret template that defaults blocked until real durable refs are filled.
- Failures: No owner-provisioned runner/SMTP/Release/workflow refs, launch confirmation, workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch blocked until a filled passing production refs report, explicit launch confirmation, and default-branch trial-start workflow evidence exist.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove the template function, CLI command, example JSON, tests, runbook/phase record/governance updates, and restore version 0.11.21.
- Next step: Fill the no-secret production refs template with owner-approved durable `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`; run `plan-production-refs`, then rerun `plan-production-launch --confirm-launch`.

### `ITER-20260621-042`

- Date: 2026-06-22
- Fact level: EXTRACTED from GitHub metadata discovery code, focused tests, local blocked CLI evidence, and semantic registry checks.
- Version before: 0.11.22
- Version after: 0.11.23
- Base commit: aa8a31f8033f337a7ea0c62ffa446a1c8ca0200b
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PRODUCTION-REFS-GITHUB-DISCOVERY-026, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Add a runner-side no-secret GitHub metadata discovery command so external production refs can be produced from actual Actions metadata instead of hand-filled JSON where possible.
- Assumptions: `gh api` can list secret names, variables, and self-hosted runners on the provisioned private runner; secret values remain unreadable and must never be logged.
- Files changed: production refs module, CLI command, focused tests, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, and run manifest.
- Model changes: No new runtime model; MOD-ADP-030 now includes no-secret GitHub metadata discovery for production refs readiness input.
- Formula changes: Refreshed FORM-ADP-024 because `cli.py::main` changed, and refreshed FORM-ADP-032 after adding GitHub metadata discovery helpers.
- Parameter changes: Added PARAM-ADP-163 for the default GitHub repository used by production refs metadata discovery.
- Commands run: focused production refs/launch/CLI tests; local `discover-production-refs` blocked path with missing `gh`; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check; cache check.
- Test results: focused production refs/launch/CLI tests 19 OK; local `discover-production-refs` exited 2 as expected because `gh` is unavailable and emitted a redacted JSON error; final semantic/governance results recorded in the run manifest.
- Successes: Provisioned-runner refs discovery can now generate the same `adp-production-refs-v1` report from GitHub Actions metadata without exposing secrets.
- Failures: No owner-provisioned runner/SMTP/Release/workflow refs, launch confirmation, workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch blocked until a passing discovered or filled production refs report, explicit launch confirmation, and default-branch trial-start workflow evidence exist.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove GitHub metadata discovery functions, CLI command, tests, runbook/phase record/governance updates, and restore version 0.11.22.
- Next step: Run `discover-production-refs` on the provisioned private runner after owner secrets/vars/runner are configured; feed the report to `plan-production-launch --confirm-launch`.

### `ITER-20260621-043`

- Date: 2026-06-22
- Fact level: EXTRACTED from trial-start workflow ordering, validator checks, focused tests, runbook, and semantic registry checks.
- Version before: 0.11.23
- Version after: 0.11.24
- Base commit: 46932dd4535695326a9f90c34f5f42bdca49d7df
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TRIAL-START-LAUNCH-PREFLIGHT-027, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Make the default-branch trial-start workflow run production refs discovery and launch readiness before live source, SMTP, Release, or trial-start gate work.
- Assumptions: The private runner will have `gh` metadata access only after owner provisioning; the workflow may read secret names and variable names but must never read secret values or Codex auth.
- Files changed: trial-start workflow, workflow validator, focused tests, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, event, and run manifest.
- Model changes: No new runtime model; MOD-ADP-028 now requires production refs discovery and launch readiness before trial-start workflow source, SMTP, Release, or start-gate work.
- Formula changes: Refreshed FORM-ADP-030 after adding production refs and launch readiness ordering checks.
- Parameter changes: Updated PARAM-ADP-145 artifact coverage and added PARAM-ADP-164 for trial-start launch preflight ordering.
- Commands run: focused trial-start workflow/production launch/CLI tests; trial-start workflow plan CLI JSON; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check.
- Test results: focused tests 13 OK; `plan-trial-start-workflow` returned pass with production refs and launch readiness ordering checks; semantic extractor checked 163 active machine-checked parameters and 32 active formulas with no errors; project governance errors 0 warnings 0; root governance tests 96 OK; arXiv unit tests 153 OK; changed-only enforce-sync semantic validation errors 0 warnings 0 across all registered projects; manifest JSON and development_events JSONL parse OK; git diff check OK.
- Successes: The trial-start workflow now fails closed before source/SMTP/Release work if production refs discovery or launch readiness blocks.
- Failures: No owner-provisioned runner/SMTP/Release/workflow refs, workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch and Phase 11 acceptance blocked until the default-branch workflow produces real start evidence and the 30-day trial evidence package passes.
- Remaining risks: Production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove trial-start workflow production refs and launch precheck steps, revert workflow contract checks, remove PARAM-ADP-164 and related governance records, and restore version 0.11.23.
- Next step: After owner provisioning, dispatch the default-branch trial-start workflow with explicit confirmation and archive the new refs, launch, source, SMTP, Release, and start-gate artifacts.

### `ITER-20260621-044`

- Date: 2026-06-22
- Fact level: EXTRACTED from GitHub-hosted provisioning audit workflow text, focused workflow tests, local blocked discovery output, and semantic registry checks.
- Version before: 0.11.24
- Version after: 0.11.25
- Base commit: 12d022784bc79863ed4ae380ac1638c6bf85ca19
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PROVISIONING-AUDIT-WORKFLOW-028, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Add a GitHub-hosted no-secret provisioning audit workflow before private-runner trial-start dispatch.
- Assumptions: The workflow may inspect GitHub Actions metadata for runner labels, secret names, and variable names through `ADP_GITHUB_METADATA_TOKEN` or `github.token`, but it must not read secret values, Codex auth, local media/model/cache artifacts, or dispatch production trial-start work.
- Files changed: provisioning audit workflow, production refs workflow test, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, event, and run manifest.
- Model changes: No new runtime model; MOD-ADP-030 now includes a GitHub-hosted no-secret provisioning audit workflow before private-runner trial-start dispatch.
- Formula changes: No implementation formula change; FORM-ADP-032 documents the provisioning audit wrapper around existing no-secret discovery.
- Parameter changes: Added PARAM-ADP-165 for the GitHub-hosted production provisioning audit workflow.
- Commands run: focused production refs/launch/CLI tests; local `discover-production-refs` blocked path with missing `gh`; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check.
- Test results: Focused tests and blocked local discovery passed before final governance validation; final validation results are recorded in the run manifest for this iteration.
- Successes: Owner can now run a no-secret GitHub-hosted provisioning audit and archive `adp-production-provisioning-audit` before occupying the private self-hosted runner.
- Failures: No owner-provisioned runner/SMTP/Release/workflow refs, workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch and Phase 11 acceptance blocked until provisioning audit, default-branch trial-start, SMTP/Release, replay/recovery/resource, and 30-day daily evidence pass.
- Remaining risks: The audit can prove GitHub metadata only when token permissions can list self-hosted runners, repository secret names, and variables; production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove provisioning audit workflow, workflow test, PARAM-ADP-165, phase record, manifest, and related governance records, then restore version 0.11.24.
- Next step: Configure owner-approved GitHub metadata permissions, run the provisioning audit workflow on `main`, then dispatch the default-branch trial-start workflow only after the audit and launch readiness pass.

### `ITER-20260621-045`

- Date: 2026-06-22
- Fact level: EXTRACTED from provisioning audit review code, CLI fixture output, focused tests, and semantic registry checks.
- Version before: 0.11.25
- Version after: 0.11.26
- Base commit: 4e25ce2db01466b1053809d9b4aaeb949837fb4e
- Result commit: PENDING
- Task IDs: ADP-PHASE11-PROVISIONING-AUDIT-REVIEW-029, ADP-PHASE11-PRODUCTION-TRIAL-START-022
- Goal: Add a no-side-effect review gate for downloaded provisioning audit artifacts before private-runner trial-start dispatch.
- Assumptions: The downloaded audit artifact must already be no-secret and generated by the GitHub-hosted provisioning audit workflow; the review command only validates and binds durable refs.
- Files changed: production refs module, CLI command, focused tests, runbook, phase record, version/changelog files, model/formula/parameter/traceability registries, delivery task, event, and run manifest.
- Model changes: No new runtime model; MOD-ADP-030 now includes provisioning audit artifact review.
- Formula changes: Refreshed FORM-ADP-032 after adding `build_provisioning_audit_review` and `validate_provisioning_audit_review`.
- Parameter changes: Added PARAM-ADP-166 for the provisioning audit review validator identifier.
- Commands run: focused production refs/launch/CLI tests; review-provisioning-audit fixture pass and blocked sample; semantic extractor validation; project governance validation; root governance tests; arXiv unit tests; changed-only enforce-sync semantic validation; manifest JSON parse; development_events JSONL parse; git diff check.
- Test results: Focused tests and CLI samples passed before final governance validation; final validation results are recorded in the run manifest for this iteration.
- Successes: A downloaded audit artifact can now be machine-reviewed and bound to durable workflow run and artifact refs before any trial-start dispatch.
- Failures: No owner-run provisioning audit artifact, owner-provisioned runner/SMTP/Release/workflow refs, workflow dispatch, SMTP send, Release upload, or trial-start evidence was produced in this run.
- Decisions: Keep production launch and Phase 11 acceptance blocked until provisioning audit review, default-branch trial-start, SMTP/Release, replay/recovery/resource, and 30-day daily evidence pass.
- Remaining risks: The review proves only downloaded artifact registration; production acceptance still requires passing default-branch trial start evidence, live source pass on the runner, real SMTP/Release refs, archived weekly/monthly replay evidence, archived recovery drill evidence, actual resource telemetry, and 30 unique daily production evidence entries.
- Rollback: Remove provisioning audit review function, CLI command, tests, PARAM-ADP-166, phase record, manifest, and related governance records, then restore version 0.11.25.
- Next step: Run the provisioning audit workflow on `main`, download its artifact, run `review-provisioning-audit` with durable refs, then dispatch the default-branch trial-start workflow only after audit review and launch readiness pass.

### `ITER-20260621-046`

- Date: 2026-06-22
- Fact level: EXTRACTED from two-day simulation code, CLI report, focused tests, full arXiv tests, and semantic registry checks.
- Version before: 0.11.26
- Version after: 0.11.27
- Base commit: c75fa25fc79eed87ef510b4ce990ab663e362db5
- Result commit: PENDING
- Task IDs: ADP-PHASE11-TWO-DAY-SIMULATION-030
- Goal: Satisfy the updated Phase 11 local acceptance target with a deterministic two-day simulation instead of requiring 30 production days.
- Assumptions: The simulation can prove only the local scheduled-path behavior with mocked SMTP and mocked Release boundaries; it must not fetch live network data, read secret values, read Codex auth, retain media/model/cache artifacts, or claim production acceptance.
- Files changed: simulation module, CLI command, focused tests, version/changelog files, model/formula/parameter/traceability registries, delivery task, phase record, event, and run manifest.
- Model changes: Added MOD-ADP-031 for the two-day simulation acceptance gate.
- Formula changes: Refreshed FORM-ADP-024 because `cli.py::main` changed, and added FORM-ADP-033 for two-day simulation validation.
- Parameter changes: Added PARAM-ADP-167 through PARAM-ADP-169 for the simulation model ID, required simulated day count, and no-production-claim safety flags.
- Commands run: focused simulation tests; `run-two-day-simulation` CLI with start date 2026-06-22; simulation report JSON parse; full arXiv unit test discovery; semantic extractor validation; governance manifest and JSONL parse.
- Test results: focused two-day simulation tests 3 OK; two-day simulation CLI status pass with `two_day_simulation_ready=true`, `observed_day_count=2`, and `production_acceptance_claimed=false`; simulation report JSON parse OK; arXiv unit tests 160 OK; semantic extractor checked 168 active parameters and 33 active formulas with no errors.
- Successes: The updated local goal has a durable two-day simulation report covering 2026-06-22 and 2026-06-23, with unique simulated source/publication IDs and explicit no-real-side-effect gates.
- Failures: No real owner-run provisioning audit artifact, owner-provisioned runner/SMTP/Release/workflow refs, workflow dispatch, SMTP send, Release upload, default-branch trial-start run, or 30-day production evidence was produced in this run.
- Decisions: Treat the two-day simulation as sufficient for the updated local Phase 11 acceptance target while preserving the separate real production-trial path as blocked until external owner evidence exists.
- Remaining risks: Real production launch still requires owner-provisioned durable refs, explicit launch confirmation, default-branch workflow evidence, and real SMTP/Release/resource evidence.
- Rollback: Remove the two-day simulation module, CLI command, tests, MOD-ADP-031, FORM-ADP-033, PARAM-ADP-167 through PARAM-ADP-169, phase record, manifest, and related governance records, then restore version 0.11.26.
- Next step: Sync the two-day simulation changes to GitHub and, only if real production launch is requested later, run the provisioning audit and default-branch trial-start path with owner-provided refs.

### `ITER-20260621-047`

- Date: 2026-06-22
- Fact level: EXTRACTED from official arXiv taxonomy/API documentation, Phase 12 implementation, focused tests, and workflow contract checks.
- Version before: 0.11.27
- Version after: 0.12.0
- Base commit: c775a956b29e976c965c0c58e7ba25d250c70eae
- Result commit: PENDING
- Task IDs: ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-031
- Goal: Upgrade scheduled production input from legacy cs.AI-only defaults to all-arXiv primary archive scanning with candidate queue persistence, ROI ranking, one daily lead paper, Release-hosted video artifact link, and email queue summary.
- Assumptions: Phase 12 may prove code and workflow gates with local fixture source batches, but real production remains disabled until owner-provisioned runner networking/TLS, SMTP, Release target, and default-branch workflow evidence pass.
- Files changed: global scan module, CLI, scheduled execution, scheduler validator, trial-start gate/workflow validator, scheduled and trial-start workflows, focused tests, runbook, config examples, README, version/changelog files, model/formula/parameter/traceability registries, delivery task, phase record, event, and run manifest.
- Model changes: Added MOD-ADP-032 `adp-all-arxiv-scan-v1`.
- Formula changes: Added FORM-ADP-034 Phase 12 all-arXiv scan queue delivery gate.
- Parameter changes: Added PARAM-ADP-170 through PARAM-ADP-176 for all-arXiv model id, archive count, per-archive window, queue size, ROI thresholds, ROI weights, and mail video-link policy.
- Commands run: full arXiv unit test discovery; project semantic extractor; targeted root governance manifest tests; project governance changed-only sync check; workflow legacy-query grep; JSON/CSV format checks; git diff check.
- Test results: arXiv unit tests 165 OK; semantic extractor checked 34 active formulas and 175 active parameters with no errors; targeted root governance tests 2 OK; changed-only governance sync reported 0 errors and 0 warnings before the validator continued into unrelated missing project directories; workflow legacy-query grep found no `ADP_ARXIV_QUERY` or `cat:cs.AI` production entry; manifest JSON, JSONL, CSV width, and git diff checks passed.
- Successes: Production workflows no longer default to `cat:cs.AI`; scheduled daily-run can restore/persist a candidate queue, scan the arXiv primary archive set, rank by requested ROI/learning criteria, emit Phase 12 artifacts, and require a Release video artifact link before real SMTP can count.
- Failures: No production variables were enabled, no real SMTP message was sent, no real Release was uploaded, no live runner all-arXiv fetch was proven, and no real MP4 rendering was claimed.
- Decisions: Keep `ADP_PRODUCTION_ENABLED`, `ADP_SCHEDULED_RUN_ENABLED`, `ADP_ALLOW_SMTP_SEND`, and `ADP_ALLOW_RELEASE_UPLOAD` disabled until Phase 12 is verified on the owner-provisioned runner and Release/SMTP evidence passes.
- Remaining risks: Real production launch still requires owner-provisioned GitHub Actions runner networking/TLS, SMTP app password, Release target, default-branch workflow evidence, real Release-hosted video/MP4 artifacts, resource telemetry, replay/recovery evidence, and 30 daily production entries.
- Rollback: Remove `global_scan.py`, Phase 12 CLI commands, workflow updates, delivery-package gates, tests, runbook/config/governance updates, and restore version 0.11.27.
- Next step: Open PR for Phase 12, wait for CI, merge only after checks pass, then configure production variables only after runner-side all-arXiv scan, queue, Release link, and SMTP evidence pass.

### `ITER-20260621-048`

- Date: 2026-06-22
- Fact level: EXTRACTED from workflow contracts, live dry-run command implementation, MP4 render implementation, focused tests, and full arXiv unit tests.
- Version before: 0.12.0
- Version after: 0.12.1
- Base commit: 05c69c6522a74901f33350e03046f03a6f47b061
- Result commit: PENDING
- Task IDs: ADP-PHASE12-PRODUCTION-ENABLEMENT-032
- Goal: Prepare Phase 12 production enablement for true cloud execution without self-hosted runner dependency, while adding live all-arXiv dry-run and real MP4 artifact gates before production can be enabled.
- Assumptions: GitHub-hosted `ubuntu-latest` with installed `ffmpeg` is sufficient for the lightweight MP4 artifact; production schedule, SMTP, and Release uploads remain disabled until explicit cloud evidence and owner-controlled manual tests pass.
- Files changed: cloud dry-run workflow, scheduled/trial-start/production-trial/provisioning-audit workflows, global scan, video rendering, production preflight, scheduler/trial workflow validators, simulation fixtures, focused tests, version/changelog/governance records, and Phase 12 cloud phase record.
- Model changes: Added MOD-ADP-033 `adp-phase12-cloud-enablement-v1`.
- Formula changes: Added FORM-ADP-035 for cloud dry-run, GitHub-hosted runner, real MP4, and side-effect gates; FORM-ADP-034 requires `.mp4` video links rather than JSON manifests.
- Parameter changes: Added PARAM-ADP-177 through PARAM-ADP-180 for live dry-run id, MP4 render id, cloud disk threshold, and GitHub-hosted runner requirement.
- Commands run: full arXiv unit tests; workflow self-hosted grep; focused workflow/preflight/video/global scan tests; changed-only governance validation; GitHub Actions run `27924078126`.
- Test results: arXiv unit tests 171 OK; all arXiv workflow YAML files contain no `self-hosted`, `runner_label`, or `ADP_SELF_HOSTED`; GitHub Actions run `27924078126` passed with 20/20 archive buckets, 16 candidates, sample daily input, and a real MP4 artifact of 80246 bytes.
- Successes: Active workflows now target GitHub-hosted runners, live dry-run verified all 20 archive buckets and emitted a sample daily input, real MP4 rendering succeeded through ffmpeg, and email video links require a Release `.mp4` asset.
- Failures: No real GitHub Release was uploaded, no Gmail SMTP test email was sent, and no production schedule variables were enabled.
- Decisions: Keep production launch blocked until Release `.mp4`, Gmail SMTP manual test, PR CI, and owner confirmation pass.
- Remaining risks: PR CI, SMTP secret configuration, Release permissions, and controlled manual side-effect tests remain before production enablement.
- Rollback: Revert version 0.12.1 changes, remove the cloud dry-run workflow and MP4 render command, restore version 0.12.0, and keep production variables disabled.
- Next step: Push branch, open PR, run the Phase 12 cloud dry-run on GitHub-hosted Actions, inspect `adp-phase12-cloud-dry-run`, then run controlled Release/Gmail SMTP manual test only after dry-run passes.

### `ITER-20260621-049`

- Date: 2026-06-22
- Fact level: EXTRACTED from manual workflow contract, focused tests, and scheduled execution delivery-package behavior.
- Version before: 0.12.1
- Version after: 0.12.2
- Base commit: beb075a419b8b4c6cb6f73807284dcaa930866e2
- Result commit: PENDING
- Task IDs: ADP-PHASE12-MANUAL-DELIVERY-TEST-033
- Goal: Prepare the controlled GitHub Release plus Gmail SMTP manual test path requested after PR CI, without enabling production scheduling.
- Assumptions: The manual workflow will be dispatched from the default branch after PR CI and merge; it may perform one Release upload and one Gmail SMTP send only after the exact confirmation string is supplied.
- Files changed: manual delivery workflow, focused workflow test, scheduled execution email-link assertion, version/changelog files, model/formula/parameter/traceability registries, delivery task, phase record, event, and run manifest.
- Model changes: Added MOD-ADP-034 `adp-manual-delivery-test-v1`.
- Formula changes: Added FORM-ADP-036 for default-branch manual Release + SMTP test gating.
- Parameter changes: Added PARAM-ADP-181 through PARAM-ADP-184 for confirmation string, default-branch guard, real side-effect flags, and Release-backed email path.
- Commands run: focused manual workflow and scheduled execution tests.
- Test results: focused manual workflow and scheduled execution tests 8 OK.
- Successes: The manual workflow has no schedule trigger, uses GitHub-hosted `ubuntu-latest`, defaults Gmail SMTP host/port/username, requires `ADP_SMTP_PASSWORD`, creates Release assets before SMTP, and sends no video attachment.
- Failures: No real GitHub Release has been uploaded and no Gmail SMTP email has been sent in this preparation commit.
- Decisions: Keep production schedule disabled until this manual workflow is merged, dispatched, and verified by received email plus Release/video links.
- Remaining risks: GitHub workflow_dispatch availability requires the workflow on the default branch; missing/invalid Gmail app password or GitHub token Release permission will fail the manual test.
- Rollback: Remove the manual delivery workflow, tests, version 0.12.2 governance records, and restore version 0.12.1 while keeping production variables disabled.
- Next step: Commit and push this PR update, wait for PR CI green, merge the safe manual-test entrypoint to main, then run the GitHub Actions manual delivery workflow with the confirmation string.

### `ITER-20260621-050`

- Date: 2026-06-22
- Fact level: EXTRACTED from GitHub Actions run `27926461430`, manual delivery execution artifact, workflow contract, and focused regression test.
- Version before: 0.12.2
- Version after: 0.12.3
- Base commit: 932446fd2154ac477ea0cb6862a60098b1e1ed55
- Result commit: PENDING
- Task IDs: ADP-PHASE12-MANUAL-DELIVERY-RELEASE-DEDUPE-034
- Goal: Repair the manual Release plus Gmail SMTP test workflow so the next default-branch dispatch can create a Release before sending SMTP.
- Assumptions: Duplicate Release asset names caused the first manual workflow's `gh release create` failure; SMTP correctly remained blocked because no Release-hosted video link existed.
- Files changed: manual delivery workflow, focused workflow test, version/changelog files, phase record, event, run manifest, delivery task, traceability, and version matrix.
- Model changes: No new model; refines MOD-ADP-034.
- Formula changes: No new formula; refreshes FORM-ADP-036 implementation evidence after workflow asset dedupe.
- Parameter changes: No new parameter; preserves PARAM-ADP-184 Release-backed email path.
- Commands run: pending final validation.
- Test results: pending final validation; failed manual run `27926461430` confirmed GitHub-hosted runner, Release blocked, SMTP dry_run, and production schedule not enabled.
- Successes: Workflow now deduplicates Release assets by filename before scheduled delivery.
- Failures: No real Release upload or Gmail SMTP send has passed yet after this repair.
- Decisions: Keep production schedule disabled; rerun manual workflow only after PR CI passes and repair merges to main.
- Remaining risks: A second manual workflow run can still fail on Release permissions, Gmail SMTP authentication, or provider policy.
- Rollback: Revert version 0.12.3 workflow dedupe, tests, phase record, manifest, event, and restore version 0.12.2 while keeping production variables disabled.
- Next step: Validate locally, open repair PR, wait for PR CI green, merge, then rerun the manual Release + Gmail SMTP workflow.

### `ITER-20260621-051`

- Date: 2026-06-22
- Fact level: EXTRACTED from GitHub Actions runs `27927785092` and `27928505758`, manual delivery execution artifact, release delivery implementation, cloud dry-run failure logs, and focused regression tests.
- Version before: 0.12.3
- Version after: 0.12.4
- Base commit: 0da8463ad03c94c73c784213199bde8fee110a8d
- Result commit: PENDING
- Task IDs: ADP-PHASE12-MANUAL-DELIVERY-INTERNAL-RELEASE-DEDUPE-035
- Goal: Repair the lower GitHub Release delivery boundary after the second controlled manual dispatch showed duplicate asset paths still reached `gh release create` from inside scheduled delivery, then harden the PR cloud dry-run against transient arXiv 429/timeout blocks.
- Assumptions: The workflow-level filename dedupe passed, but the release transport boundary still needed to skip repeated identical paths and fail closed for distinct files that publish with the same Release asset filename. PR CI run `27928505758` also proved the live all-ArXiv dry-run can be partially successful and still fail closed on transient arXiv rate limits.
- Files changed: release delivery code, live all-ArXiv retry code, focused release delivery/global scan tests, version/changelog files, model/formula/parameter/traceability registries, delivery task, phase record, event, run manifest, and generated governance status views.
- Model changes: Refined MOD-ADP-017 to `adp-release-delivery-v1.1`.
- Formula changes: Refreshed FORM-ADP-019 implementation evidence after release delivery asset dedupe and FORM-ADP-035 after bounded transient retry was added to live cloud dry-run.
- Parameter changes: Added PARAM-ADP-185 for Release asset path dedupe.
- Commands run: focused release delivery tests; focused global scan retry tests; semantic extractor; governance dashboard generation; full arXiv unit tests; root governance unit tests; final governance and information-quality validation pending in this PR preparation loop.
- Test results: focused release delivery tests 6 OK; focused global scan tests 9 OK; semantic extractor checked 36 active formulas and 184 active parameters before final rerun; arXiv unit tests 176 OK before final rerun.
- Successes: `release_delivery.py` now removes repeated identical asset paths before command construction and blocks conflicting duplicate Release filenames without logging secrets, `gh` stdout/stderr, or Release notes text. Live all-ArXiv cloud dry-run now retries bounded transient 429/timeout blocks while still requiring 20/20 archive buckets.
- Failures: Second manual workflow run `27927785092` failed closed before this repair; PR CI run `27928505758` failed closed after arXiv returned HTTP 429 for later archive buckets; no real Release upload or Gmail SMTP send has passed yet after this repair.
- Decisions: Keep production schedule disabled; rerun manual workflow only after this PR passes CI and merges to `main`.
- Remaining risks: A third workflow_dispatch can still fail on GitHub Release permissions, Gmail SMTP authentication, provider policy, repeated upstream arXiv throttling, or a newly exposed runtime issue.
- Rollback: Revert version 0.12.4 release delivery dedupe, tests, phase record, manifest, event, and restore version 0.12.3 while keeping production variables disabled.
- Next step: Complete local validation, open repair PR, wait for PR CI green, merge, then rerun the manual Release + Gmail SMTP workflow.

## Unknown Historical Periods

None for this new project baseline.


### `ITER-20260623-S1-009`

- Date: 2026-06-23
- Fact level: EXTRACTED from S1-10 implementation, migration-bound bootstrap tests, and governance registries.
- Version before: 0.19.0
- Version after: 0.20.0
- Base commit: 014d0a5fbc6111e99c4fba33f3e363d0643e10ad
- Result commit: PENDING
- Task IDs: S1-10-POST_MIGRATION_BOOTSTRAP-001
- Goal: Verify the post-migration target machine or GitHub-hosted runner bootstrap boundary before historical previews and live-day evidence.
- Assumptions: S1-10 readiness requires a verified S1-09 migration manifest and explicit runtime smoke evidence, but it must not claim production delivery or enable side effects.
- Files changed: stage1 bootstrap module, CLI, focused tests, version/changelog files, model/formula/parameter/traceability registries, delivery task, phase record, event, run manifest, and generated status views.
- Model changes: Added MOD-ADP-043 `adp-stage1-post-migration-bootstrap-v1`.
- Formula changes: Added FORM-ADP-045 for migration-bound target-runner bootstrap readiness.
- Parameter changes: Added PARAM-ADP-332 through PARAM-ADP-339 for bootstrap schema, acceptance ID, target environment count, secret-name count, GitHub env count, Python minimum, network timeout, and probe URL.
- Commands run: focused bootstrap/migration/CLI tests; version CLI; full arxiv-daily-push unit tests; semantic extractor; project/all/changed-only governance validators; root governance tests; information quality validator; JSON/CSV parse checks; git diff check; cache hygiene check.
- Test results: focused bootstrap/migration/CLI tests 16 OK; version CLI returned 0.20.0; arxiv-daily-push unit tests 220 OK; semantic extractor checked 45 active formulas and 322 active parameters with no errors; project/all/changed-only governance validators 0 errors 0 warnings; root governance tests 130 OK; information quality PASS errors 0 warnings 0; JSON/CSV/diff/cache hygiene PASS.
- Successes: Tampered migration package blocks bootstrap; cloud-runner proof requires GitHub-hosted workflow/environment evidence; production side effects remain disabled.
- Failures: No 30 historical previews, live SMTP delivery days, Release upload, scheduler enablement, or production acceptance evidence exists.
- Decisions: Proceed next to S1-11 historical B1 previews only after final governance validation and CI binding.
- Remaining risks: Local SSL CA count can be zero on this Mac, so real live network readiness must be proven by explicit probe on the target runner when required.
- Rollback: Revert version 0.20.0 S1-10 bootstrap code/tests and governance records, then restore version 0.19.0.
- Next step: S1-11-HISTORICAL_B1_PREVIEWS-001

### `ITER-20260623-S1-010`

- Date: 2026-06-23
- Fact level: EXTRACTED from `stage1_historical_previews.py`, focused S1-11 tests, CLI preview generation, semantic extractor, and governance registry updates.
- Version before: 0.20.0
- Version after: 0.21.0
- Base commit: f12a408b5ace76d38487793d04329cc1e009af7a
- Result commit: PENDING
- Task IDs: S1-11-HISTORICAL_B1_PREVIEWS-001
- Goal: Generate 30 independent historical B1/arXiv report and email preview packages before live-day delivery while preserving no-production-side-effect boundaries.
- Assumptions: S1-11 evidence is historical preview evidence only; it must not claim live delivery, send Gmail SMTP, upload GitHub Releases, generate video, enable production scheduling, or claim `ARXIV_PRODUCTION_ACCEPTED`.
- Files changed: stage1 historical preview module, CLI dispatch, focused tests, version/changelog files, model/formula/parameter/traceability registries, delivery task, phase record, development event, run manifest, generated status views, and root governance test expectations.
- Model changes: Added MOD-ADP-044 `adp-stage1-historical-b1-previews-v1`.
- Formula changes: Added FORM-ADP-046 and refreshed formulas whose implementation fingerprint includes `cli.py::main`.
- Parameter changes: Added PARAM-ADP-340 through PARAM-ADP-348 for preview schema, acceptance ID, required preview count, minimum unique date/source counts, artifact kind count, source type, supported input format count, and disabled side-effect key count.
- Commands run: focused S1-11 historical/B1/queue/CLI tests; version CLI; full arxiv-daily-push unit tests; semantic extractor; historical-b1-previews CLI artifact smoke.
- Test results: focused S1-11 historical/B1/queue/CLI tests 21 OK; version CLI returned 0.21.0; arxiv-daily-push unit tests 225 OK; semantic extractor checked 46 active formulas and 331 active parameters with no errors; historical-b1-previews CLI passed with 30 previews, 30 unique dates, 30 unique source IDs, 30 unique content hashes, 30 unique email IDs, 150 artifact files, manifest exists, future leakage count 0, and SMTP/Release/video/network/scheduler side effects false.
- Successes: Deterministic offline historical previews are available; 30-preview generation validates unique dates, source IDs, content hashes, email IDs, claim evidence, content ledger rows, optional five-file artifacts per preview, future-leakage blocking, and disabled side effects.
- Failures: No controlled live B1 email days, real production trial start, replay/recovery/resource evidence, or final production acceptance evidence exists.
- Decisions: Bump product version to 0.21.0 because S1-11 adds a backward-compatible historical preview evidence CLI and validation model while preserving disabled production side effects.
- Remaining risks: Historical fixtures can still overfit; S1-12 must prove live target-runner arXiv/network/SMTP evidence before owner-facing production claims.
- Rollback: Remove `stage1_historical_previews.py`, historical preview CLI dispatch/tests, restore version 0.20.0, and revert S1-11 governance records and run manifest.
- Next step: S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001

### `ITER-20260623-S1-011`

- Date: 2026-06-23
- Fact level: EXTRACTED from GitHub Actions PR #67 workflow run `27987189886`, job `82831357067`, artifact `7806168015`, and artifact JSON inspection.
- Version before: 0.21.0
- Version after: 0.21.0
- Base commit: 4ef8e2f614a4ebfcbd6a81907049d63ad503b3c1
- Result commit: PENDING
- Task IDs: S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001
- Goal: Record target-runner live arXiv preflight evidence for S1-12 without claiming controlled Gmail SMTP delivery or production acceptance.
- Assumptions: PR #67 Phase 12 cloud dry-run is target-runner live arXiv evidence only; it does not prove B1 live email delivery, two natural-day delivery, real Gmail SMTP sending, scheduler enablement, Release upload, or `ARXIV_PRODUCTION_ACCEPTED`.
- Files changed: S1-12 delivery task, delivery plan, version matrix current gate, phase preflight record, development ledger/event, run manifest, generated status views, and root governance test expectations.
- Model changes: No model implementation changed; existing MOD-ADP-033 live all-arXiv dry-run evidence is referenced.
- Formula changes: No formula implementation changed.
- Parameter changes: No parameter value changed.
- Commands run: GitHub Actions artifact inspection; project/all/changed-only governance validators; root governance tests; information quality validator; JSON/CSV parse checks; git diff check; cache hygiene check.
- Test results: GitHub Actions PR #67 live all-ArXiv dry-run passed with 20/20 archives verified, max_results_per_category 1, artifact digest `sha256:2011bf655a2d8237b5c20f3111c70d6242a4b6582b5e90069d1f63d43a4da81a`, and SMTP/Release/scheduler disabled. Final local validator results are recorded in the run manifest.
- Successes: S1-12 now has target-runner live arXiv preflight evidence and a durable artifact reference instead of a pure `NOT_RUN` task state.
- Failures: Two real natural-day controlled B1 Gmail SMTP delivery evidence is still absent; this iteration remains `in_progress`.
- Decisions: Keep product version at 0.21.0 because this iteration records governance evidence only and does not change product behavior, model formulas, or active parameters.
- Remaining risks: The live arXiv preflight used all 20 primary archives while the S1 Window A low-resource guidance still requires careful operator control; real SMTP credentials and two-day delivery evidence remain the blocking gate.
- Rollback: Revert the S1-12 preflight phase record, run manifest, delivery task status change, ledger/event entry, generated status views, and test expectation update.
- Next step: Execute controlled B1 Gmail SMTP delivery evidence for day 1 of 2 on the target runner, with production scheduler still disabled.

### `ITER-20260623-S1-012`

- Date: 2026-06-23
- Fact level: EXTRACTED from Stage 1 text-only production enablement code, workflows, tests, semantic registry sync, and YAML workflow parsing.
- Version before: 0.21.0
- Version after: 0.22.0
- Base commit: 2ff5adc7d10a971fd5bf4303a9d8936313bd070a
- Result commit: PENDING
- Task IDs: S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001
- Goal: Prepare S1-12 for controlled B1/arXiv live email delivery by converting production enablement to all-arXiv text artifacts plus Gmail SMTP, with no video or GitHub Release production gate.
- Assumptions: This iteration is PR/preflight preparation only; it must not send a real email, enable production scheduling, upload a Release, generate video, or claim `ARXIV_PRODUCTION_ACCEPTED`.
- Files changed: all-arXiv delivery package, scheduled execution, preflight/scheduler/refs/launch/trial gates, four GitHub Actions workflows, schema/tests, version/changelog, semantic registries, and governance records.
- Model changes: Refined existing Stage 1/Phase 12 models for text-only production enablement while preserving public validator IDs.
- Formula changes: Refreshed FORM-ADP-013, 014, 015, 020, 021, 023, 024, 025, 029, 030, 031, 032, 034, 035, 036, 039, and CLI-linked S1 formulas 042-046.
- Parameter changes: Updated active text-only values for Release/video/preflight/ref/workflow parameters including PARAM-ADP-053, 065, 066, 101, 110, 117, 131, 140, 142, 145, 147, 148, 152, 156, 157, 160, 161, 162, 183, 184, 186, and 277.
- Commands run: py_compile, focused S1-12 tests, full arxiv-daily-push unit tests, YAML parse for four workflows, semantic extractor. Final governance validation pending after record generation.
- Test results: arxiv-daily-push unit tests 190 OK; focused S1-12 tests 38 OK; semantic extractor 46 formulas and 331 parameters OK; four workflow YAML files parse OK.
- Successes: Stage 1 frontstage email is Chinese text-first, candidate-queue aware, and no longer requires video/Release links; workflows target GitHub-hosted ubuntu-latest and keep contents read-only.
- Failures: PR CI, controlled manual Gmail SMTP test, two natural-day evidence, production scheduler enablement, and final acceptance evidence are not complete.
- Decisions: Do not enable production scheduled runs; open PR and wait for CI before any manual SMTP test.
- Remaining risks: GitHub Actions expression syntax and Gmail SMTP provider behavior still require cloud-run verification; schedule must remain disabled until explicit owner acceptance.
- Rollback: Revert version 0.22.0 S1-12 text-only production enablement code, workflows, schema/tests, and governance updates, restoring 0.21.0 with production disabled.
- Next step: Open PR, wait for PR CI green, then run one controlled manual Gmail SMTP test on GitHub/cloud runner.

### `ITER-20260623-S1P5T04-ROADMAP-V6`

- Date: 2026-06-23
- Fact level: EXTRACTED from `/Users/linzezhang/Downloads/ARXIV_DAILY_PUSH_TWO_STAGE_ROADMAP_V6.md`, GitHub Actions run `28002478689`, and scheduled-execution artifact `7811543123`.
- Version before: 0.22.0
- Version after: 0.22.0
- Base commit: 66d11bc2ad98b17fd3e5b9889941f69bdbaf5b90
- Result commit: PENDING
- Task IDs: `S1P5T04`
- Goal: Import V6 as the active task-numbering roadmap and record the first controlled GitHub/cloud-runner Gmail SMTP evidence without enabling production scheduling.
- Assumptions: V6 controls task numbering and zero-media scope. Later owner instruction controls the Stage 1 runner choice as GitHub/cloud runner; production scheduling remains disabled until Stage 1 acceptance passes.
- Files changed: V6 roadmap source file, pursuing-goal baseline lock, README, AGENTS, required governance registries, traceability/version/task records, S1P5T04 run manifest, PR changed-scope base-ref workflow repair, and this ledger.
- Model changes: No model implementation changed.
- Formula changes: No formula expression changed; current machine fingerprints/evidence hashes were refreshed for FORM-ADP-013, FORM-ADP-014, FORM-ADP-024, FORM-ADP-034, and FORM-ADP-042 through FORM-ADP-046 after the CI semantic gate identified drift.
- Parameter changes: No active parameter value changed; PARAM-ADP-183 metadata was reverified for the manual-delivery evidence boundary.
- Commands run: source roadmap SHA-256 and line-count check; GitHub Actions workflow/job/artifact inspection; scheduled execution artifact inspection without printing email body or secrets; semantic extractor; changed-only governance sync; root governance tests; ADP unit tests.
- Test results: Manual workflow `28002478689` completed `success`; job `manual-delivery-test` completed `success`; scheduled execution artifact reports `status=succeeded`, `mode=daily-run`, `notification_status=sent`, `real_smtp_send_enabled=true`, recipient `linzezhang35@gmail.com`, Chinese lesson true, candidate queue summary true, video link false; semantic extractor checked 46 formulas and 331 parameters; changed-only governance sync reports 0 errors 0 warnings.
- Successes: V6 roadmap is now the current task-numbering roadmap under `docs/pursuing_goal/`; future closeouts must report the current V6 Task ID; first controlled Gmail SMTP evidence is present on GitHub/cloud runner.
- Failures: First PR #73 CI attempt failed because the pull_request changed-scope gate used the force-pushed old head SHA as `GOVERNANCE_BASE_REF`; fixed by switching pull_request diff base to `github.event.pull_request.base.sha`. Email template quality is owner-rejected for now but explicitly deferred; complete two-day controlled evidence and `ARXIV_PRODUCTION_ACCEPTED` remain incomplete.
- Decisions: Continue from `S1P5T04` and prioritize Stage 1 acceptance evidence before template redesign or Stage 2 expansion.
- Remaining risks: Need second controlled live-day evidence, final Stage 1 acceptance report, and production-schedule enablement gate; must not accidentally enable production scheduler early.
- Rollback: Remove the V6 roadmap file, revert baseline/README/AGENTS/ledger edits, and continue with the previous V5 task labels.
- Next step: Close the remaining `S1P5T04` evidence gap and only then evaluate `ARXIV_PRODUCTION_ACCEPTED`.

### `ITER-20260623-S1P5T04-CONTROLLED-SMTP-EVIDENCE`

- Date: 2026-06-23
- Fact level: EXTRACTED from GitHub Actions run `28002478689`, rerun job `82921274100`, and scheduled-execution artifacts `7811543123` and `7816791617`.
- Version before: 0.22.0
- Version after: 0.22.0
- Base commit: 055ad784b379a282aea8530f2b22b29f0b62f300
- Result commit: PENDING
- Task IDs: `S1P5T04`
- Goal: Record the second controlled GitHub/cloud-runner Gmail SMTP send evidence without enabling production scheduling or claiming Stage 1 acceptance.
- Assumptions: Two controlled sends prove repeatable Gmail SMTP delivery on GitHub/cloud runner, but they do not prove two distinct natural days because both scheduled-execution reports use daily date `2026-06-23`.
- Files changed: S1P5T04 evidence manifest, delivery task evidence refs, owner/status/assurance views, traceability row, model governance note, development event, and root governance test expectation.
- Model changes: No runtime model behavior changed.
- Formula changes: No formula implementation changed.
- Parameter changes: No active parameter value changed.
- Commands run: GitHub Actions rerun job `82921274100`; artifact inspection for `7811543123` and `7816791617` without printing email body or secrets.
- Test results: Both scheduled-execution artifacts report `production_evidence_ready=true`, `notification_status=sent`, recipient `linzezhang35@gmail.com`, Chinese lesson true, candidate queue summary true, and video link false.
- Successes: Controlled SMTP evidence count is now `2`; production schedule remains disabled; runner is GitHub/cloud, not local Mac.
- Failures: Both sends share daily date `2026-06-23`; second distinct natural-day evidence and `ARXIV_PRODUCTION_ACCEPTED` remain incomplete.
- Decisions: Keep `S1P5T04` in progress and do not enable production scheduling.
- Remaining risks: Natural-day cadence proof, final acceptance report, and owner production-schedule approval remain open.
- Rollback: Remove the S1P5T04 second SMTP evidence manifest and governance status updates.
- Next step: Collect or explicitly owner-approve the remaining distinct natural-day evidence gate before evaluating `ARXIV_PRODUCTION_ACCEPTED`.

### `ITER-20260623-S1P5T04-ACCELERATED-ACCEPTANCE`

- Date: 2026-06-23
- Fact level: EXTRACTED from code, tests, semantic registry sync, PR #76 cloud artifact inspection, and the controlled SMTP manifest.
- Version before: 0.22.0
- Version after: 0.23.0
- Base commit: 681cafd26dad312f78136fcb5ba095340e16e972
- Result commit: PENDING
- Task IDs: `S1P5T04`
- Goal: Replace the stale natural-day wait with a fail-closed accelerated real-arXiv acceptance path that can be proven by GitHub/cloud PR CI without enabling production scheduling.
- Assumptions: A same-day accelerated replay can satisfy the owner instruction only if it uses real arXiv candidates, controlled SMTP refs, target-runner artifacts, no secret leakage, and no production side effects.
- Files changed: accelerated acceptance module/CLI/tests, trial evidence evaluator, cloud dry-run workflow, version files, formula/model/parameter registries, traceability/status views, and this run manifest.
- Model changes: Added `MOD-ADP-045` / `adp-stage1-accelerated-acceptance-v1`.
- Formula changes: Added `FORM-ADP-047`; updated `FORM-ADP-014` for accelerated replay slots and refreshed CLI-linked formula fingerprints.
- Parameter changes: Added `PARAM-ADP-349` through `PARAM-ADP-351` for accelerated acceptance model ID, acceptance ID, and 30-sample real candidate requirement.
- Commands run: py_compile for changed Python files; focused accelerated/trial tests; workflow YAML parse; semantic extractor; negative-control CLI against PR #76 max=1 artifact.
- Test results: Focused tests: 6 OK; semantic extractor: 47 formulas and 334 parameters checked; negative-control artifact with 16 candidates correctly blocked.
- Successes: Stage 1 now has a cloud-runner acceptance path that can pass in one PR CI run if live all-arXiv max=3 yields at least 30 real candidates.
- Failures: `ARXIV_PRODUCTION_ACCEPTED` is not claimed in this commit; PR CI must still produce the passing 30-sample artifact.
- Decisions: Keep production scheduler disabled and keep Gmail SMTP from sending during accelerated acceptance evidence generation.
- Remaining risks: Live arXiv availability and candidate volume can still make PR CI fail closed; production-schedule owner approval remains separate.
- Rollback: Revert `stage1_accelerated_acceptance.py`, trial accelerated-mode changes, workflow max=3 acceptance step, 0.23.0 version bump, and related governance records.
- Next step: Open PR, wait for PR CI; if the cloud artifact passes with 30 real candidates, record the artifact and then evaluate `ARXIV_PRODUCTION_ACCEPTED`.

### `ITER-20260623-S1P5T04-ARXIV-PRODUCTION-ACCEPTED`

- Date: 2026-06-23
- Fact level: EXTRACTED from PR #82, GitHub Actions runs `28019921535`, `28019921329`, `28019921500`, and artifact `7818287996`.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 6767bf37d125e475784eb80180ea2ca2ede89515
- Result commit: PENDING
- Task IDs: `S1P5T04`; `S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001`
- Goal: Record the post-merge Stage 1 arXiv acceptance evidence and synchronize governance state without enabling scheduled production.
- Assumptions: The owner-approved accelerated path can satisfy Stage 1 only when GitHub/cloud runner evidence uses real all-arXiv candidates, existing controlled SMTP refs, no secret leakage, no Release/video requirement, and no production scheduling side effects.
- Files changed: workflow default sample count, production/trial workflow tests, governance generator, S1-12 task state, traceability/version/status views, root arXiv human entry files, and this accepted manifest.
- Model changes: No model implementation changed; this iteration records the accepted PR #82 artifact for `MOD-ADP-045`.
- Formula changes: No formula expression changed.
- Parameter changes: No active parameter value changed; workflow default fallback now aligns with the accepted max_results_per_category `3` evidence path.
- Commands run: GitHub PR #82 workflow inspection; artifact `7818287996` field inspection; focused scheduler/trial workflow tests pending local rerun after governance generation.
- Test results: PR #82 Stage 1 bootstrap, Project Governance, and live all-ArXiv cloud dry-run all completed success. Artifact `7818287996` reports `status=pass`, `accepted_for_production=true`, `ARXIV_PRODUCTION_ACCEPTED`, 49 real arXiv candidates, 30 selected samples, 20/20 primary archive buckets, two controlled SMTP refs, no blockers, no video/Release requirement, and `production_schedule_enabled=false`.
- Successes: Stage 1 arXiv acceptance is now recorded as `ARXIV_PRODUCTION_ACCEPTED`; production remains cloud/GitHub-runner based and does not depend on the user's Mac background process.
- Failures: GitHub repository variables/secrets for scheduled production send are not inspected or enabled in this sync; email template quality remains owner-rejected and deferred.
- Decisions: Keep production schedule disabled until repo variables `ADP_PRODUCTION_ENABLED`, `ADP_SCHEDULED_RUN_ENABLED`, `ADP_ALLOW_SMTP_SEND`, and `ADP_ALLOW_RELEASE_UPLOAD` are explicitly verified or enabled.
- Remaining risks: Repo variable state may still block daily scheduled sends; Stage 2 source expansion must not start until the accepted arXiv baseline is stable; template redesign can change frontstage quality but not Stage 1 acceptance.
- Rollback: Revert accepted manifest, event, S1-12 task completion, workflow fallback default, root human entry files, and generated governance status updates.
- Next step: Verify or enable GitHub repo production variables/secrets for scheduled daily email, then optionally handle the deferred email frontstage template task.

### `ITER-20260623-S1P5T03-R-REAL-ARXIV-30-ASOF-REPLAY`

- Date: 2026-06-23
- Fact level: EXTRACTED from `stage1_real_replay.py`, focused tests, local real arXiv control run, `CONTENT_LEDGER.csv`, and GitHub Actions run `28027759062` artifact `7821452823`.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 738887de4034ad42d90347d0fa0db6c0f3ed966f
- Result commit: PENDING_PR_CI_ACCEPTANCE_SYNC
- Task IDs: `S1P5T03-R REAL_ARXIV_30_DAY_BACKFILL_AND_LEDGER_RECONCILE`
- Goal: Correct the strict Stage 1 acceptance boundary by requiring 30 real historical arXiv as-of-date replays and persistent selected/queued/email ledger closure before restoring `ARXIV_PRODUCTION_ACCEPTED`.
- Assumptions: Manual delivery tests prove one-time cloud live delivery behavior only; they do not prove 30-day historical backfill or durable CONTENT_LEDGER continuity.
- Files changed: real replay module, CLI command, cloud backfill workflow, focused tests, real CONTENT_LEDGER, model/formula/parameter/traceability registries, delivery task, phase record, run manifest, development event, and owner-facing status files.
- Model changes: Added MOD-ADP-046 `adp-stage1-real-arxiv-30-asof-replay-v1`.
- Formula changes: Added FORM-ADP-048 for real 30 as-of-date replay, future-leakage, duplicate-lead, queue-continuity, P0/P1, artifact, and no-production-side-effect validation.
- Parameter changes: Added PARAM-ADP-352 through PARAM-ADP-359 for model/schema/acceptance IDs, required count, lookback, max results, artifact file count, and all-arXiv submittedDate query policy.
- Commands run: focused real replay tests; local live real arXiv 30 as-of replay via curl; GitHub Actions `arXiv Daily Push real 30-day backfill` run `28027759062`.
- Test results: focused real replay tests passed locally; local live replay and GitHub/cloud replay both produced status pass, 30/30 success, 30 unique dates, 30 unique selected real arXiv IDs, future leakage 0, duplicate lead 0, queue continuity breaks 0, unsupported P0/P1 0, 30 daily inputs, 30 reports, 30 email previews, 30 queue ledgers, and 299 CONTENT_LEDGER rows.
- Successes: `docs/owner/CONTENT_LEDGER.csv` no longer contains the S1-06 placeholder row; it now has 30 selected lead rows and 269 queued candidate rows with email/artifact state.
- Failures: None for S1P5T03-R; production schedule, SMTP send, Release upload, Stage 2, video, and template redesign remain intentionally disabled or deferred.
- Decisions: Do not start Stage 2, do not enable production schedule, do not send production email, do not optimize the frontstage email template in this task.
- Remaining risks: Future scheduled production still requires a separate owner-approved flag/secrets task; Stage 2 and email template quality work remain outside this acceptance gate.
- Rollback: Remove S1P5T03-R code/workflow/tests/governance records and restore the previous strict acceptance state only if the owner explicitly abandons this real-backfill gate.
- Next step: Stop S1P5T03-R, keep production schedule disabled, and wait for owner instruction before any production scheduler, SMTP, Release upload, Stage 2, video, or template task.

### `ITER-20260624-ADP-S1P5T04-POST-MERGE-TEST10-040`

- Date: 2026-06-24
- Fact level: EXTRACTED from GitHub Actions run `28059194999`, authenticated artifact downloads, and scheduled production run metadata.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 2f715f37ee21df59cc1cf092d712bd9399157469
- Result commit: PENDING
- Task IDs: `ADP-S1P5T04-POST-MERGE-TEST10-040`; `S1P5T04`
- Goal: Record the owner-triggered post-merge manual Gmail SMTP test10 evidence from `main` after the Australia/Sydney service-date fix.
- Assumptions: test10 is a controlled manual delivery proof; it does not enable scheduled production, Release upload, Stage 2, or video.
- Files changed: governance status/task/event files, dashboard generator decision policy, root governance tests, and the test10 verified run manifest.
- Model changes: No ranking, queue, report, email content, SMTP, Release, Stage 2, or video model changed.
- Formula changes: No formula expression changed.
- Parameter changes: No active parameter value changed.
- Commands run: GitHub Actions API run/job/artifact inspection; authenticated artifact downloads for artifacts `7834307458`, `7834306281`, `7834305857`, and `7834283976`; scheduled workflow metadata inspection.
- Test results: manual run `28059194999` is run number 10 on `main`, head SHA `2f715f37ee21df59cc1cf092d712bd9399157469`, and completed success. GitHub-hosted Ubuntu jobs `guard` and `manual-delivery-test` completed success. scheduled-execution artifact `7834307458` reports `status=succeeded`, `preflight_status=pass`, `production_evidence_ready=true`, `notification_report.status=sent`, `real_smtp_send_enabled=true`, recipient `linzezhang35@gmail.com`, and subject `20260624 -- arXiv Computer Science -- Computer Science -- Open Problem: Is AdamW Effective Under Heavy-Tailed Noise?`. The daily input reports `date=2026-06-24`, `archive_count=20`, `blocked_archive_count=0`, and `candidate_count=16`.
- Successes: Post-merge Sydney service-date behavior is proven on GitHub/cloud runner and the controlled Gmail SMTP path sent to the configured recipient without logging email body or secret values.
- Failures: None for test10. Release upload remains disabled/dry-run and no video link is required for current Stage 1 text-first delivery.
- Decisions: Keep production schedule disabled; the next task is an explicit owner decision gate before any `ADP_PRODUCTION_ENABLED`, `ADP_SCHEDULED_RUN_ENABLED`, `ADP_ALLOW_SMTP_SEND`, or `ADP_ALLOW_RELEASE_UPLOAD` production enablement.
- Remaining risks: The user may still reject frontstage template quality, but that is not a Stage 1 acceptance blocker. Production schedule must not be enabled without a separate instruction and verification run.
- Rollback: Revert EVENT-20260624-ADP-083, the test10 verified manifest, task 040 completion, task 041 boundary, and generated status files.
- Next step: Stop Stage 1 delivery work at `S1P5T04`; wait for owner instruction on whether to enable production schedule or improve the email template.

### `ITER-20260624-ADP-S2PCT01-STAGE1-BOOTSTRAP-CI-RETRY-HARDENING`

- Date: 2026-06-24
- Fact level: EXTRACTED from PR #119 CI failure logs, Stage1 bootstrap code, focused tests, and governance changed-only validation.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: b74161397c3cda14580ad96918fa03bf64a67aee
- Result commit: PENDING
- Task IDs: `S2PCT01`; legacy alias `S2P2T01`
- Goal: Keep V7.1 D2 `S2PCT01` Nature/top-journal no-send shadow evidence moving while hardening the required Stage1 bootstrap cloud network probe that failed twice on arXiv API `TimeoutError`.
- Files changed: Stage1 bootstrap network probe, CLI retry/timeout flags, Stage1 bootstrap workflow flags, focused retry tests, V7.1-aligned governance status/event coverage, existing semantic formula fingerprints, and root compatibility manifests.
- Model changes: No ranking, queue, email, SMTP, Release, video, or production model changed; the bootstrap network probe now records bounded attempts and still fails closed after retry exhaustion.
- Formula changes: No formula expression changed; refreshed existing machine fingerprints/evidence hashes for CLI-linked and Stage1/Stage2 formula records after code changes.
- Parameter changes: Added CLI controls `--network-timeout-seconds` and `--network-max-attempts`; workflow uses 30 seconds and 3 attempts.
- Test results: project governance validator passed with errors 0 warnings 0; changed-only semantic governance passed with errors 0 warnings 0; Lean check-render drift 0; root governance tests 235 OK; focused ADP top-journal/stage2/bootstrap tests 22 OK; git diff check passed.
- Successes: Required arXiv API probe is no longer single-attempt brittle, and failed attempts are auditable in the bootstrap report.
- Failures: Root governance full suite and changed-only validation required follow-up synchronization after V7.1 main merge; this entry records the corrected direction, not final CI green.
- Decisions: V7.1 root/audit lock stays active; `S2PCT01` / legacy `S2P2T01` remains Nature metadata-only no-send shadow only; no SMTP, Release, GitHub schedule, video, `STAGE2_PRODUCTION_ACCEPTED`, `D2_SOURCE_DOMAIN_ACCEPTED`, or `INTEGRATED_PRODUCTION_ACCEPTED` is enabled or claimed. `S2PBT01 -> S2P1T01` remains the already-passed D1 shadow/evidence alias, not the current Nature task.
- Remaining risks: If all bounded arXiv API probe attempts fail, the Stage1 bootstrap workflow still blocks as designed; P0/P1 V7.1 audit findings still prevent production restore and integrated production acceptance.
- Rollback: Revert bootstrap retry code, CLI/workflow flags, tests, EVENT-20260624-ADP-093, and compatibility manifest/status updates.
- Next step: Re-run ADP tests, root governance tests, changed-only governance, then push PR #119 for GitHub CI.

### `ITER-20260624-ADP-S2PCT01-POST-MERGE-STATUS`

- Date: 2026-06-24
- Fact level: EXTRACTED from merged PR #119, main merge commit `047f45382fe1d0c259c87d60971295cb030f3c1b`, GitHub check-run status, model/formula/parameter registry diff, and local post-merge project governance validation.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 047f45382fe1d0c259c87d60971295cb030f3c1b
- Result commit: PENDING
- Task IDs: `S2PCT01`, legacy alias `S2P2T01`; next task `S2PCT02`, legacy alias `S2P2T02`
- Goal: Close the S2PCT01 Nature/top-journal metadata-only no-send shadow foundation after PR #119 merged to main, register its missing model/formula/parameter governance entries, and route the next S2PC task to S2PCT02 without claiming D2 or Stage2 production acceptance.
- Files changed: three owner-facing base files, project and roadmap canonical governance, assurance/status/owner/version views, delivery tasks, model/formula/parameter registries, S2PCT01 manifest, and this event/ledger.
- Model changes: Added governance registration for `MOD-ADP-051` Nature/top-journal metadata ingest and `MOD-ADP-052` top-journal shadow daily path; implementation code was already merged in PR #119.
- Formula changes: Added `FORM-ADP-053` and `FORM-ADP-054` with machine-verified AST fingerprints bound to the merged S2PCT01 implementation.
- Parameter changes: Added `PARAM-ADP-377` through `PARAM-ADP-381` for top-journal ingest/shadow model IDs, canary limit, supported journal, queue filename, and ledger filename.
- Test results: focused top-journal/stage2 tests 28 OK; live Lancet RSS no-send canary passed with selected `lancet:10.1016/s0140-6736(26)00918-9`, `article_type=article`, and `pubmed_relation_gate=doi_query_ready`; semantic extractor checked 58 formulas and 376 active parameters; project governance and changed-only governance both passed with 0 errors/0 warnings; Lean check-render drift 0; V7.1 task-pack validator PASS; root governance tests 238 OK; manifest/JSONL parse and `git diff --check` passed.
- Decisions: `ACC-S2PCT01-NATURE` is accepted only as metadata-only no-send shadow foundation evidence. `D2_SOURCE_DOMAIN_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, Release upload, GitHub production schedule, video, PDF/full-text download, and paywall bypass all remain false/disabled.
- Remaining risks: S2PCT02 Science adapter and article-type gates are not implemented yet; V7.1 P0/P1 and S2PMT07 still block any formal source-domain or integrated production acceptance.
- Rollback: Revert this post-merge status/registry sync and restore current task pointers to S2PCT01 if PR #119 is reverted.
- Next step: Implement S2PCT02 Science metadata-only no-send shadow evidence with focused source tests and governance validation.

### `ITER-20260624-ADP-S2PCT03-LANCET-SHADOW`

- Date: 2026-06-24
- Fact level: EXTRACTED from Lancet RSS fixtures, live RSS canary, model/formula/parameter registry diff, and local S2PCT03 validation.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: bcd3ff572b6e4ce5481d104879d52ebe621768a2
- Result commit: PENDING
- Task IDs: `S2PCT03`, legacy alias `S2P2T03`; next task `S2PCT04`, legacy alias `S2P2T04`
- Goal: Complete The Lancet main-journal metadata-only no-send shadow evidence after Science, register Lancet model/formula/parameter governance entries, and route the next S2PC task to top-journal profile/correction/retraction without claiming D2 or Stage2 production acceptance.
- Files changed: Lancet adapter, shadow daily path, CLI, fixture/tests, phase record, run manifest, model/formula/parameter registries, traceability, delivery tasks, root lock, and rendered governance inputs.
- Model changes: Added `MOD-ADP-055` Lancet metadata ingest and `MOD-ADP-056` Lancet no-send shadow daily path.
- Formula changes: Added `FORM-ADP-057` and `FORM-ADP-058` with machine-verifiable AST fingerprints bound to the S2PCT03 implementation.
- Parameter changes: Updated `PARAM-ADP-379` to `nature;science;lancet` and added `PARAM-ADP-387` through `PARAM-ADP-393` for Lancet RSS URLs, accepted article types, PubMed DOI-query URL template, shadow model id, queue filename, and ledger filename.
- Test results: focused top-journal/stage2 tests 28 OK; live Lancet RSS no-send canary passed with selected `lancet:10.1016/s0140-6736(26)00918-9`, `article_type=article`, and `pubmed_relation_gate=doi_query_ready`; semantic extractor checked 58 formulas and 376 active parameters; project governance and changed-only governance both passed with 0 errors/0 warnings; Lean check-render drift 0; V7.1 task-pack validator PASS; root governance tests 238 OK; manifest/JSONL parse and `git diff --check` passed.
- Decisions: `ACC-S2PCT03-LANCET` is accepted only as metadata-only no-send shadow evidence. `D2_SOURCE_DOMAIN_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, Release upload, GitHub production schedule, video, PubMed full-record harvesting, PDF/full-text download, and paywall bypass all remain false/disabled.
- Remaining risks: S2PCT04 profile/correction/retraction modeling is not implemented yet; V7.1 P0/P1 and S2PMT07 still block any formal source-domain or integrated production acceptance.
- Rollback: Revert Lancet code, fixture/tests, governance registrations, phase record, manifest, events, root-lock pointer, and rendered governance sync.
- Next step: Implement S2PCT04 journal profile, publication relation, correction, and retraction forced-event modeling with focused tests and governance validation.

### `ITER-20260624-ADP-S2PCT04-JOURNAL-PROFILE`

- Date: 2026-06-24
- Fact level: EXTRACTED from top-journal profile fixtures, prior state fixtures, model/formula/parameter registry diff, and local S2PCT04 validation.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: f33cbce7b5cf67f966a6478b502a138afed25e94
- Result commit: PENDING
- Task IDs: `S2PCT04`, legacy alias `S2P2T04`; next task `S2PCT05`
- Goal: Complete top-journal profile taxonomy, publication relation, correction, and retraction metadata-only no-send shadow evidence after Nature, Science, and Lancet, register S2PCT04 governance entries, and route the next S2PC task to engineering public signals without claiming D2 or Stage2 production acceptance.
- Files changed: profile/relation shadow code, CLI, publication event and prior state fixtures, focused tests, phase record, run manifest, model/formula/parameter registries, project/roadmap/delivery tasks, root lock, and rendered governance inputs.
- Model changes: Added `MOD-ADP-057` top-journal profile and publication relation shadow path.
- Formula changes: Added `FORM-ADP-059` with machine-verifiable AST fingerprints bound to the S2PCT04 implementation.
- Parameter changes: Added `PARAM-ADP-394` through `PARAM-ADP-399` for profile model id, required journals, required profile kinds, forced event types, ledger filename, and acceptance id.
- Test results: focused top-journal/stage2 tests 32 OK; CLI fixture canary passed with empty validation errors, all profile kinds observed, four relation types present, forced_event_update_count 2, and all production flags false.
- Decisions: `ACC-S2PCT04-JOURNAL-PROFILE` is accepted only as metadata-only no-send shadow evidence. `D2_SOURCE_DOMAIN_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, Release upload, GitHub production schedule, video, PDF/full-text download, and paywall bypass all remain false/disabled.
- Remaining risks: S2PCT05 engineering public-signal framework is not implemented yet; V7.1 P0/P1 and S2PMT07 still block any formal source-domain or integrated production acceptance.
- Rollback: Revert S2PCT04 code, fixture/tests, governance registrations, phase record, manifest, events, root-lock pointer, and rendered governance sync.
- Next step: Implement S2PCT05 engineering open-source, code, benchmark, model-card, release, and standards public-signal framework with focused tests and governance validation.

### `ITER-20260624-ADP-S2PCT05-ENGINEERING-SIGNALS`

- Date: 2026-06-24
- Fact level: EXTRACTED from engineering signal fixtures, S2PCT04 profile report fixtures, model/formula/parameter registry diff, and local S2PCT05 validation.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: f96f78c96498754dcccdd362d663db58bb3dcc8f
- Result commit: PENDING
- Task IDs: `S2PCT05`; no legacy alias; next task `S2PCT06`
- Goal: Complete engineering open-source, code, benchmark, model-card, release, and standards public-signal metadata-only no-send shadow evidence after S2PCT04 profile/relation evidence, register S2PCT05 governance entries, and route the next S2PC task to authoritative report sources without claiming D2 or Stage2 production acceptance.
- Files changed: engineering signal shadow code, CLI, engineering signal fixture, focused tests, phase record, run manifest, model/formula/parameter registries, project/roadmap/delivery tasks, root lock, and rendered governance inputs.
- Model changes: Added `MOD-ADP-058` engineering public-signal shadow path.
- Formula changes: Added `FORM-ADP-060` with machine-verifiable AST fingerprints bound to the S2PCT05 implementation.
- Parameter changes: Added `PARAM-ADP-400` through `PARAM-ADP-406` for engineering signal model id, required signal types, allowed relation types, accepted officiality states, accepted reproducibility states, ledger filename, and acceptance id.
- Test results: focused top-journal/stage2 tests 36 OK; CLI fixture canary passed with empty validation errors, all five signal types observed, engineering_signal_count 5, known_document_count 13, officiality/version/relation/reproducibility gates pass, and all production flags false.
- Decisions: `ACC-S2PCT05-ENGINEERING-SIGNALS` is accepted only as metadata-only no-send shadow evidence. `D2_SOURCE_DOMAIN_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, Release upload, GitHub production schedule, video, repository clone, PDF/full-text download, paid API use, and paywall bypass all remain false/disabled.
- Remaining risks: S2PCT06 authoritative research institution and industry technical report framework is not implemented yet; V7.1 P0/P1 and S2PMT07 still block any formal source-domain or integrated production acceptance.
- Rollback: Revert S2PCT05 code, fixture/tests, governance registrations, phase record, manifest, events, root-lock pointer, and rendered governance sync.
- Next step: Implement S2PCT06 authoritative research institution and industry technical report framework with focused tests and governance validation.

### `ITER-20260625-ADP-S2PF-S2PFT01-PROVINCIAL-COVERAGE`

- Date: 2026-06-25
- Fact level: EXTRACTED from S2PDT04 readiness manifest, mainland provincial template fixture rows, model/formula/parameter registry diff, and local S2PFT01 validation.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 3845fa52a1ab2a41ecbf0a5ba4a57d802885a82a
- Result commit: PENDING
- Task IDs: `S2PFT01`, legacy alias `S2P5T01`; next task `S2PFT02`
- Goal: Complete China mainland provincial-level template coverage after S2PDT04, register S2PFT01 governance entries, and preserve V7.2 no-production boundaries.
- Files changed: S2PFT01 report builder/validator, CLI command, focused tests, phase record, run manifest, model/formula/parameter registries, traceability, delivery tasks, rendered governance inputs, and this ledger entry.
- Model changes: Added `MOD-ADP-065` China provincial template coverage model.
- Formula changes: Added `FORM-ADP-067` with machine-verifiable AST fingerprints bound to the S2PFT01 implementation.
- Parameter changes: Added `PARAM-ADP-459` through `PARAM-ADP-468` for S2PFT01 model id, acceptance id, task ids, required mainland provincial IDs, locality types, core department roles, health tiers, identity states, and report filename.
- Test results: focused Stage2 source tests 51 OK; full arxiv-daily-push unittest 278 OK; semantic extractor checked 67 formulas and 451 parameters; V7.2 contract validator PASS; project governance 0 errors/0 warnings; JSON/YAML/JSONL/CSV parse OK.
- Decisions: `ACC-S2PFT01-PROVINCES` is accepted only as metadata-only provincial template coverage evidence. D3 full source-domain acceptance, Stage 2 production acceptance, integrated production acceptance, SMTP, Release upload, GitHub production schedule, public schema migration, queue/schema mutation, mail production, Hong Kong/Macau profiles, city coverage, and special-zone discovery all remain false/disabled.
- Remaining risks: S2PFT02 Hong Kong/Macau, S2PFT03 city coverage, S2PFT04 special-zone discovery, and S2PFT05 full D3 governance remain unimplemented. Inherited V7.1 P0=8/P1=37 and S2PMT07 still block any production acceptance claim.
- Rollback: Revert S2PFT01 code, tests, governance registrations, phase record, manifest, events, rendered governance sync, and this ledger entry; no runtime or production state was changed.
- Next step: Run final render/changed-only validation, then open a clean PR for S2PFT01.

### `ITER-20260625-ADP-S2PF-S2PFT02-HK-MO-PROFILE`

- Date: 2026-06-25
- Fact level: EXTRACTED from S2PFT01 receipt, Hong Kong and Macau profile fixture rows, model/formula/parameter registry diff, and local S2PFT02 validation.
- Version before: 0.23.0
- Version after: 0.23.0
- Base commit: 9bfe50b2195e8cfc04eb493e028c0f72e1ae0a90
- Result commit: PENDING
- Task IDs: `S2PFT02`, legacy alias `S2P5T02`; next task `S2PFT03`
- Goal: Complete Hong Kong and Macau independent profile evidence after S2PFT01, register S2PFT02 governance entries, and preserve V7.2 no-production boundaries.
- Files changed: S2PFT02 report builder/validator, CLI command, focused tests, phase record, run manifest, model/formula/parameter registries, traceability, delivery tasks, rendered governance inputs, and this ledger entry.
- Model changes: Added `MOD-ADP-066` Hong Kong and Macau independent profile model.
- Formula changes: Added `FORM-ADP-068` with machine-verifiable AST fingerprints bound to the S2PFT02 implementation.
- Parameter changes: Added `PARAM-ADP-469` through `PARAM-ADP-478` for S2PFT02 model id, acceptance id, task ids, required jurisdiction ids, required language profiles, allowed legal system states, required profile fields, forbidden template states, and report filename.
- Test results: focused Stage2 source tests 55 OK; full arxiv-daily-push unittest 284 OK; semantic extractor checked 68 formulas and 461 parameters; V7.2 validator PASS; ADP project governance errors 0 warnings 0; lean check-render drift_count 0 reference_issue_count 0; changed-only lean governance errors 0 warnings 0; JSON/YAML/JSONL/CSV parse OK; `git diff --check` PASS.
- Decisions: `ACC-S2PFT02-HK-MO` is accepted only as metadata-only Hong Kong and Macau independent profile evidence. D3 full source-domain acceptance, Stage 2 production acceptance, integrated production acceptance, SMTP, Release upload, GitHub production schedule, public schema migration, queue/schema mutation, mail production, city coverage, and special-zone discovery all remain false/disabled. Email V1 PR #152 and governance PR #153 are merged to main; S2PFT02 does not modify mail runtime paths and preserves the Email V1 contract/readiness gate.
- Remaining risks: S2PFT03 city coverage, S2PFT04 special-zone discovery, and S2PFT05 full D3 governance remain unimplemented. Inherited V7.1 P0=8/P1=37 and S2PMT07 still block any production acceptance claim.
- Rollback: Revert S2PFT02 code, tests, governance registrations, phase record, manifest, events, rendered governance sync, and this ledger entry; no runtime or production state was changed.
- Post-merge evidence: PR #155 merged to main at `69ceda49a4dd840039d32910c3f400dc0aba7c24` after 7/7 GitHub check-runs passed: governance, stage1-bootstrap, real-arxiv-30-day-backfill, live-all-arxiv-dry-run, and classify-arxiv-runtime-change x3.
- Next step: Continue `S2PFT03` key-city metadata-only coverage under V7.2 boundaries; do not enable production source inclusion, SMTP, scheduler, Release, public schema, queue/schema mutation, or integrated production acceptance.

### `ITER-20260625-ADP-S2PF-S2PFT03-KEY-CITY-COVERAGE`

- Timestamp: `2026-06-25T10:30:00+10:00`
- Fact level: EXTRACTED from S2PFT02 receipt, 24 key-city fixture rows, model/formula/parameter registry diff, and local S2PFT03 validation.
- Base commit: `3ceaf7a532e334aa390e521700d640870f1e94fd`
- Status: merged to main via PR #174 after GitHub workflows passed; no production side effects.
- Phase: S2PF
- Task IDs: `S2PFT03`, legacy alias `S2P5T03`; next task `S2PFT04`
- Goal: Complete first 24 China key-city metadata-only coverage evidence after S2PFT02, register S2PFT03 governance entries, and preserve V7.2 no-production boundaries.
- Files changed: S2PFT03 report builder/validator, CLI command, focused tests, phase record, run manifest, model/formula/parameter registries, traceability, delivery tasks, events, rendered governance inputs, and this ledger entry.
- Model changes: Added `MOD-ADP-067` key-city coverage model.
- Formula changes: Added `FORM-ADP-069` with machine-verifiable AST fingerprints bound to the S2PFT03 implementation.
- Parameter changes: Added `PARAM-ADP-479` through `PARAM-ADP-487` for S2PFT03 model id, acceptance id, task ids, required city ids, required city department roles, allowed region groups, allowed health tiers, and report filename.
- Validation: py_compile PASS; focused Stage2 source tests 59 OK; full arxiv-daily-push unittest 288 OK; semantic extractor 69 formulas / 470 parameters checked; V7.2 validator PASS; ADP project governance 0/0; changed-only governance semantic 0/0; lean check-render drift 0; GitHub workflows success for governance, Stage 1 bootstrap, live all-ArXiv cloud dry-run, and real 30-day backfill.
- Decisions: `ACC-S2PFT03-CITIES` is accepted only as metadata-only first key-city coverage evidence. D3 full source-domain acceptance, Stage 2 production acceptance, integrated production acceptance, SMTP, Release upload, GitHub production schedule, public schema migration, queue/schema mutation, mail production, and special-zone discovery all remain false/disabled. Email V1 PR #152 and governance PR #153 are merged to main; S2PFT03 does not modify mail runtime paths and preserves the Email V1 contract/readiness gate.
- Remaining risks: S2PFT04 special-zone discovery and S2PFT05 full D3 governance remain unimplemented. Inherited V7.1 P0=8/P1=37 and S2PMT07 still block any production acceptance claim.
- Rollback: Revert S2PFT03 code, tests, governance registrations, phase record, manifest, events, rendered governance sync, and this ledger entry; no runtime or production state was changed.
- Evidence: `arxiv-daily-push/docs/phase_records/PHASE_S2PFT03_KEY_CITY_COVERAGE.md`; `governance/run_manifests/ADP-S2PFT03-KEY-CITY-COVERAGE-20260625.json`; `arxiv-daily-push/docs/governance/delivery_tasks.yaml`.
- Next step: Continue `S2PFT04` special-zone metadata-only discovery under V7.2 boundaries; do not enable production source inclusion, SMTP, scheduler, Release, public schema, queue/schema mutation, or integrated production acceptance.

### `ITER-20260625-ADP-S2PF-S2PFT03-MAIN-MERGE-STATUS`

- Timestamp: `2026-06-25T14:40:00+10:00`
- Fact level: EXTRACTED from PR #174, merge commit `6924b5bf4cc49f7355c9c1f16d0b5cfbd78ded9b`, and GitHub workflow status.
- Phase: S2PF
- Task IDs: `S2PFT03`, legacy alias `S2P5T03`; next task `S2PFT04`
- Result: PR #174 merged to main after GitHub workflows passed.
- GitHub checks: Project Governance success; Stage 1 bootstrap success; live all-ArXiv cloud dry-run success; real 30-day backfill success.
- Decisions: S2PFT03 remains metadata-only/no-send key-city coverage evidence. D3 full source-domain acceptance, Stage 2 production acceptance, integrated production acceptance, SMTP, Release upload, GitHub production schedule, public schema migration, queue/schema mutation, mail production, and special-zone discovery all remain false/disabled.
- Rollback: Revert only this post-merge governance/status sync. Revert PR #174 separately only if the owner explicitly abandons S2PFT03.

### `ITER-20260625-ADP-S2PF-S2PFT04-SPECIAL-ZONE-DISCOVERY`

- Timestamp: `2026-06-25T15:20:00+10:00`
- Fact level: EXTRACTED from S2PFT03 receipt, 10 special-zone fixture rows, model/formula/parameter registry diff, and local S2PFT04 validation.
- Base commit: `42839a260b5768b51678b0575bc42dbbb016a30e`
- Status: local validation passed, PR/CI pending.
- Phase: S2PF
- Task IDs: `S2PFT04`, legacy alias `S2P5T04`; next task `S2PFT05`
- Goal: Complete China special-zone metadata-only discovery evidence after S2PFT03, register S2PFT04 governance entries, and preserve V7.2 no-production boundaries.
- Files changed: S2PFT04 report builder/validator, CLI command, focused tests, phase record, run manifest, model/formula/parameter registries, traceability, delivery tasks, events, rendered governance inputs, and this ledger entry.
- Model changes: Added `MOD-ADP-068` special-zone discovery model.
- Formula changes: Added `FORM-ADP-070` with machine-verifiable AST fingerprints bound to the S2PFT04 implementation.
- Parameter changes: Added `PARAM-ADP-488` through `PARAM-ADP-497` for S2PFT04 model id, acceptance id, task ids, required zone ids, authority roles, zone types, policy focus areas, health tiers, and report filename.
- Validation: py_compile PASS; focused Stage2 source tests 63 OK; full arxiv-daily-push unittest 292 OK; semantic extractor 70 formulas / 480 parameters checked; V7.2 validator PASS; ADP project governance 0/0; changed-only governance semantic 0/0; lean check-render drift 0; JSON/YAML/JSONL/CSV parse OK; git diff --check PASS.
- Decisions: `ACC-S2PFT04-ZONES` is accepted only as metadata-only special-zone discovery evidence. D3 full source-domain acceptance, Stage 2 production acceptance, integrated production acceptance, SMTP, Release upload, GitHub production schedule, public schema migration, queue/schema mutation, mail production, and Email V1 production operation all remain false/disabled.
- Remaining risks: S2PFT05 full D3 governance remains unimplemented. Inherited V7.1 P0=8/P1=37 and S2PMT07 still block any production acceptance claim.
- Rollback: Revert S2PFT04 code, tests, governance registrations, phase record, manifest, events, rendered governance sync, and this ledger entry; no runtime or production state was changed.
- Evidence: `arxiv-daily-push/docs/phase_records/PHASE_S2PFT04_SPECIAL_ZONE_DISCOVERY.md`; `governance/run_manifests/ADP-S2PFT04-SPECIAL-ZONE-DISCOVERY-20260625.json`; `arxiv-daily-push/docs/governance/delivery_tasks.yaml`.
- Next step: Run full validation, commit, push, and open PR for S2PFT04.

### `ITER-20260625-ADP-S2PG-S2PGT02-KNOWLEDGE-GRAPH-SPINE`

- Timestamp: `2026-06-25T18:40:00+10:00`
- Fact level: EXTRACTED from S2PGT01 receipt, cross-source identity/relation fixtures, model/formula/parameter registry diff, and local S2PGT02 validation.
- Base commit: `475028ce73854d0beddbe3edd8f2b495bcdc957f`
- Status: local validation passed, PR/CI pending.
- Phase: S2PG
- Task IDs: `S2PGT02`, legacy alias `S2P6T01`; next task `S2PGT03`
- Goal: Complete private cross-source identity-resolution and knowledge-graph relation spine evidence after S2PGT01, register S2PGT02 governance entries, and preserve V7.2 no-production boundaries.
- Files changed: S2PGT02 report builder/validator, CLI command, focused tests, phase record, run manifest, model/formula/parameter registries, traceability, delivery tasks, events, rendered governance inputs, and this ledger entry.
- Model changes: Added `MOD-ADP-071` knowledge-graph relation spine model.
- Formula changes: Added `FORM-ADP-073` with machine-verifiable AST fingerprints bound to the S2PGT02 implementation.
- Parameter changes: Added `PARAM-ADP-516` through `PARAM-ADP-524` for S2PGT02 model id, acceptance id, task ids, required identifier types, allowed relation types, required relation fields, required gates, and report filename.
- Validation: py_compile PASS; focused Stage2 source tests 75 OK; full arxiv-daily-push unittest 304 OK; semantic extractor 73 formulas / 507 parameters checked; V7.2 validator PASS; ADP project governance 0 errors / 0 warnings; changed-only governance semantic 0 errors / 0 warnings; lean check-render drift 0 reference_issue_count 0; JSON/YAML/JSONL/CSV parse OK; `git diff --check` PASS.
- Decisions: `ACC-S2PGT02-KG` is accepted only as private identity/relation spine evidence. Public schema migration, production queue mutation, source-domain production inclusion, Stage 2 production acceptance, integrated production acceptance, SMTP, Release upload, scheduler, V7.2 contract edits, and Email V1 production operation all remain false/disabled.
- Remaining risks: S2PGT03 source-reading mapping and S2PGT04 delta/resonance relation evidence remain unimplemented. Inherited V7.1 P0=8/P1=37 and S2PMT07 still block any production acceptance claim.
- Rollback: Revert S2PGT02 code, tests, governance registrations, phase record, manifest, events, rendered governance sync, and this ledger entry; no runtime or production state was changed.
- Evidence: `arxiv-daily-push/docs/phase_records/PHASE_S2PGT02_KNOWLEDGE_GRAPH_SPINE.md`; `governance/run_manifests/ADP-S2PGT02-KNOWLEDGE-GRAPH-SPINE-20260625.json`; `arxiv-daily-push/docs/governance/delivery_tasks.yaml`.
- Next step: Run final validation, commit, push, and open PR for S2PGT02.

### `ITER-20260625-ADP-S2PG-S2PGT03-SOURCE-BOARD-ROUTING`

- Timestamp: `2026-06-25T19:30:00+10:00`
- Fact level: EXTRACTED from S2PGT01 receipt, V7.1 architecture mapping, D1-D4 route fixtures, model/formula/parameter registry diff, and local S2PGT03 validation.
- Base commit: `ceb6065997aed26a560f73f88fa8fea46d409b15`
- Status: local validation passed, PR/CI pending.
- Phase: S2PG
- Task IDs: `S2PGT03`; next task `S2PGT04`
- Goal: Complete private D1-D4 to B1-B6 multi-label routing evidence after S2PGT01, register S2PGT03 governance entries, and preserve V7.2 no-production boundaries.
- Files changed: S2PGT03 report builder/validator, CLI command, focused tests, phase record, run manifest, model/formula/parameter registries, traceability, delivery tasks, events, rendered governance inputs, and this ledger entry.
- Model changes: Added `MOD-ADP-072` source-board routing model.
- Formula changes: Added `FORM-ADP-074` with machine-verifiable AST fingerprints bound to the S2PGT03 implementation.
- Parameter changes: Added `PARAM-ADP-525` through `PARAM-ADP-535` for S2PGT03 model id, acceptance id, task id, source domains, primary boards, cross-cutting boards, reason codes, route fields, required gates, source-domain board rule keys, and report filename.
- Validation: py_compile PASS; focused Stage2 source tests 79 OK; full arxiv-daily-push unittest 308 OK; semantic extractor 74 formulas / 518 parameters checked; V7.2 validator PASS; ADP project governance 0 errors / 0 warnings; changed-only governance semantic 0 errors / 0 warnings; lean check-render drift 0 reference_issue_count 0; JSON/YAML/JSONL/CSV parse OK; `git diff --check` PASS.
- Decisions: `ACC-S2PGT03-ROUTING` is accepted only as private source-to-reading-board routing evidence. Public schema migration, production queue mutation, source-domain production inclusion, Stage 2 production acceptance, integrated production acceptance, SMTP, Release upload, scheduler, V7.2 contract edits, Email V1 runtime changes, and production operation all remain false/disabled.
- Remaining risks: S2PGT04 support/refute/frontier delta/resonance evidence remains unimplemented. Inherited V7.1 P0=8/P1=37 and S2PMT07 still block any production acceptance claim.
- Rollback: Revert S2PGT03 code, tests, governance registrations, phase record, manifest, events, rendered governance sync, and this ledger entry; no runtime or production state was changed.
- Evidence: `arxiv-daily-push/docs/phase_records/PHASE_S2PGT03_SOURCE_BOARD_ROUTING.md`; `governance/run_manifests/ADP-S2PGT03-SOURCE-BOARD-ROUTING-20260625.json`; `arxiv-daily-push/docs/governance/delivery_tasks.yaml`.
- Next step: Commit, push, and open PR for S2PGT03.
