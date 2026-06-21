# DELIVERY_PLAN

Project: `arxiv-daily-push`
Governance spec version: `1.0.0`

## Phase Map

| Phase | Purpose | Exit Gate |
|---|---|---|
| A | Phase 1 repository foundation | CLI skeleton, governance records, and focused tests pass |
| B | Phase 2-4 data contracts, arXiv source, and ranking | schema, adapter, and ranking gates pass |
| C | Phase 5-6 evidence gate and text lesson | Claim Ledger and lesson verification pass |
| D | Phase 7-10 TTS, video, local daily pipeline, and GitHub automation | media, resource, runner, and release gates pass |
| E | Phase 11 weekly/monthly, 30-day trial, and handoff | full operational acceptance passes |

## Task Summary

machine_summary:

- task_count: 38
- acceptance_count: 38

## Delivery Tasks

The machine-readable task source is `delivery_tasks.yaml`.

| Task ID | Phase | Status | Acceptance | Test result | Evidence |
|---|---|---|---|---|---|
| ADP-PHASE1-FOUNDATION-001 | A | completed | ADP-ACC-PHASE1-FOUNDATION | 4 tests OK; validator 0 errors; diff check pass | `docs/phase_records/PHASE_01.md` |
| ADP-PHASE2-DATA-CONTRACTS-001 | B | completed | ADP-ACC-PHASE2-DATA-CONTRACTS | 13 tests OK; schema parse OK; validator 0 errors; sync 0 errors | `docs/phase_records/PHASE_02.md` |
| ADP-PHASE3-ARXIV-ADAPTER-001 | B | completed | ADP-ACC-PHASE3-ARXIV-ADAPTER | 19 tests OK; adapter fixture parse OK; validator 0 errors | `docs/phase_records/PHASE_03.md` |
| ADP-PHASE4-RANKING-001 | B | completed | ADP-ACC-PHASE4-RANKING | 26 tests OK; ranking golden score and gates pass | `docs/phase_records/PHASE_04.md` |
| ADP-PHASE5-EVIDENCE-GATE-001 | C | completed | ADP-ACC-PHASE5-EVIDENCE-GATE | 32 tests OK; Claim Ledger gates pass | `docs/phase_records/PHASE_05.md` |
| ADP-PHASE6-LESSON-001 | C | completed | ADP-ACC-PHASE6-LESSON | 37 tests OK; lesson evidence linkage pass | `docs/phase_records/PHASE_06.md` |
| ADP-PHASE7-TTS-001 | D | completed | ADP-ACC-PHASE7-TTS | 42 tests OK; narration dry-run gate pass | `docs/phase_records/PHASE_07.md` |
| ADP-PHASE8-VIDEO-001 | D | completed | ADP-ACC-PHASE8-VIDEO | 47 tests OK; storyboard dry-run gate pass | `docs/phase_records/PHASE_08.md` |
| ADP-PHASE9-LOCAL-PIPELINE-001 | D | completed | ADP-ACC-PHASE9-LOCAL-PIPELINE | 51 tests OK; local dry-run pipeline pass | `docs/phase_records/PHASE_09.md` |
| ADP-PHASE10-RUNNER-RELEASE-EMAIL-001 | D | completed | ADP-ACC-PHASE10-RUNNER-RELEASE-EMAIL | 55 tests OK; handoff side-effect gate pass; validator 0 errors | `docs/phase_records/PHASE_10.md` |
| ADP-PHASE11-ACCEPTANCE-HANDOFF-001 | E | completed | ADP-ACC-PHASE11-ACCEPTANCE-HANDOFF | 60 tests OK; handoff readiness pass; production acceptance blocked until live evidence exists | `docs/phase_records/PHASE_11.md` |
| ADP-PHASE11-EVIDENCE-REF-HARDENING-002 | E | completed | ADP-ACC-PHASE11-EVIDENCE-REF-HARDENING | 61 tests OK; production pass requires evidence refs | `docs/phase_records/PHASE_11_EVIDENCE_REF_HARDENING.md` |
| ADP-PHASE11-TRIAL-EVIDENCE-VALIDATOR-003 | E | completed | ADP-ACC-PHASE11-TRIAL-EVIDENCE-VALIDATOR | 67 tests OK; 33 root tests OK; validator 0 errors; production pass requires validated trial report | `docs/phase_records/PHASE_11_TRIAL_EVIDENCE_VALIDATOR.md` |
| ADP-PHASE11-PRODUCTION-PREFLIGHT-004 | E | completed | ADP-ACC-PHASE11-PRODUCTION-PREFLIGHT | 71 tests OK; 34 root tests OK; current environment preflight blocked as expected | `docs/phase_records/PHASE_11_PRODUCTION_PREFLIGHT.md` |
| ADP-PHASE11-TRIAL-BOOTSTRAP-005 | E | completed | ADP-ACC-PHASE11-TRIAL-BOOTSTRAP | 74 tests OK; bootstrap workflow/runbook gate pass | `docs/phase_records/PHASE_11_TRIAL_BOOTSTRAP_WORKFLOW.md` |
| ADP-PHASE11-LIVE-ARXIV-INGEST-006 | E | completed | ADP-ACC-PHASE11-LIVE-ARXIV-INGEST | 78 tests OK; live local fetch blocked by Python SSL CA as expected | `docs/phase_records/PHASE_11_LIVE_ARXIV_INGEST.md` |
| ADP-PHASE11-SMTP-DELIVERY-007 | E | completed | ADP-ACC-PHASE11-SMTP-DELIVERY | 83 tests OK; SMTP dry-run and mocked send gate pass; no real SMTP evidence claimed | `docs/phase_records/PHASE_11_SMTP_DELIVERY.md` |
| ADP-PHASE11-RELEASE-DELIVERY-008 | E | completed | ADP-ACC-PHASE11-RELEASE-DELIVERY | 9 focused tests OK; Release dry-run and mocked gh create gate pass; no real Release evidence claimed | `docs/phase_records/PHASE_11_RELEASE_DELIVERY.md` |
| ADP-PHASE11-PRODUCTION-SCHEDULER-009 | E | completed | ADP-ACC-PHASE11-PRODUCTION-SCHEDULER | 8 focused tests OK; timezone schedule workflow gate pass; no scheduled production side effects enabled | `docs/phase_records/PHASE_11_PRODUCTION_SCHEDULER.md` |
| ADP-PHASE11-SCHEDULED-EXECUTION-010 | E | completed | ADP-ACC-PHASE11-SCHEDULED-EXECUTION | 13 focused tests OK; scheduled execution driver emits evidence and blocks dry-run side effects from production acceptance | `docs/phase_records/PHASE_11_SCHEDULED_EXECUTION_DRIVER.md` |
| ADP-PHASE11-DAILY-INPUT-BUILDER-011 | E | completed | ADP-ACC-PHASE11-DAILY-INPUT-BUILDER | 18 focused tests OK; arXiv SourceBatch converts to summary-claim daily input and scheduled daily-run accepts builder reports | `docs/phase_records/PHASE_11_DAILY_INPUT_BUILDER.md` |
| ADP-PHASE11-TRIAL-LEDGER-012 | E | completed | ADP-ACC-PHASE11-TRIAL-LEDGER | 106 tests OK; production-ready scheduled daily-run evidence appends to trial ledger while 30-day acceptance remains blocked | `docs/phase_records/PHASE_11_TRIAL_LEDGER_UPDATE.md` |
| ADP-PHASE11-TRIAL-LEDGER-STATE-013 | E | completed | ADP-ACC-PHASE11-TRIAL-LEDGER-STATE | 15 focused tests OK; workflow restore/export bash syntax pass; state exporter CLI pass | `docs/phase_records/PHASE_11_TRIAL_LEDGER_STATE.md` |
| ADP-PHASE11-TRIAL-OPS-EVIDENCE-014 | E | completed | ADP-ACC-PHASE11-TRIAL-OPS-EVIDENCE | 16 focused tests OK; operational evidence annotation and export gates pass | `docs/phase_records/PHASE_11_TRIAL_OPS_EVIDENCE.md` |
| ADP-PHASE11-TRIAL-REPLAY-EVIDENCE-015 | E | completed | ADP-ACC-PHASE11-TRIAL-REPLAY-EVIDENCE | 16 focused tests OK; replay evidence builder blocks incomplete coverage and missing durable refs | `docs/phase_records/PHASE_11_TRIAL_REPLAY_EVIDENCE.md` |
| ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-016 | E | completed | ADP-ACC-PHASE11-TRIAL-RECOVERY-EVIDENCE | 21 focused tests OK; recovery evidence builder blocks dry-run notifications, missing refs, and non-production recovery reports | `docs/phase_records/PHASE_11_TRIAL_RECOVERY_EVIDENCE.md` |
| ADP-PHASE11-TRIAL-RESOURCE-EVIDENCE-017 | E | completed | ADP-ACC-PHASE11-TRIAL-RESOURCE-EVIDENCE | 27 focused tests OK; resource evidence builder blocks missing preflight matches, blocked preflight, missing durable refs, and lowered expected days | `docs/phase_records/PHASE_11_TRIAL_RESOURCE_EVIDENCE.md` |
| ADP-PHASE11-TRIAL-START-GATE-018 | E | completed | ADP-ACC-PHASE11-TRIAL-START-GATE | 34 focused tests OK; start gate blocks missing confirmation, missing durable refs, SMTP dry-run probes, and blocked preflight reports | `docs/phase_records/PHASE_11_TRIAL_START_GATE.md` |
| ADP-PHASE11-TRIAL-START-WORKFLOW-019 | E | completed | ADP-ACC-PHASE11-TRIAL-START-WORKFLOW | 20 focused tests OK; workflow validator checks manual dispatch, artifact set, side-effect vars, durable refs, and secret safety | `docs/phase_records/PHASE_11_TRIAL_START_WORKFLOW.md` |
| ADP-PHASE11-PRODUCTION-LAUNCH-READINESS-020 | E | completed | ADP-ACC-PHASE11-PRODUCTION-LAUNCH-READINESS | 12 focused tests OK; launch gate blocks draft/unmerged PR, head SHA mismatch, missing durable refs, and missing confirmation | `docs/phase_records/PHASE_11_PRODUCTION_LAUNCH_READINESS.md` |
| GOV-SEMANTIC-ADP-001 | E | completed | ACC-SEMANTIC-ADP-001 | semantic extractor 152 parameters/31 formulas OK; selector probe matched final 21 parameters; root governance 89 OK; arXiv unit 143 OK; changed-only semantic 0 errors | `governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json` |
| ADP-PHASE11-POST-MERGE-LAUNCH-AUDIT-021 | E | completed | ADP-ACC-PHASE11-POST-MERGE-LAUNCH-AUDIT | 143 arXiv tests OK; 83 root tests OK; project governance 0 errors; changed-only semantic 0 errors; launch gate blocks only external refs/confirmation | `docs/phase_records/PHASE_11_POST_MERGE_LAUNCH_AUDIT.md` |
| ADP-PHASE11-PRODUCTION-REFS-BUNDLE-023 | E | completed | ADP-ACC-PHASE11-PRODUCTION-REFS-BUNDLE | 9 focused tests OK; semantic extractor 158 parameters/32 formulas OK; refs gate blocks secret-like inputs and missing required names | `docs/phase_records/PHASE_11_PRODUCTION_REFS_READINESS.md` |
| ADP-PHASE11-RELEASE-PERMISSIONS-024 | E | completed | ADP-ACC-PHASE11-RELEASE-PERMISSIONS | 6 focused tests OK; trial-start and scheduled workflow contracts require `contents: write` while uploads remain explicitly gated | `docs/phase_records/PHASE_11_RELEASE_PERMISSIONS.md` |
| ADP-PHASE11-PRODUCTION-REFS-TEMPLATE-025 | E | completed | ADP-ACC-PHASE11-PRODUCTION-REFS-TEMPLATE | 16 focused tests OK; no-secret production refs template emits JSON and remains blocked until owner fills durable refs | `docs/phase_records/PHASE_11_PRODUCTION_REFS_TEMPLATE.md` |
| ADP-PHASE11-PRODUCTION-REFS-GITHUB-DISCOVERY-026 | E | completed | ADP-ACC-PHASE11-PRODUCTION-REFS-GITHUB-DISCOVERY | 19 focused tests OK; discovery command builds refs from no-secret GitHub metadata and fails closed without `gh` | `docs/phase_records/PHASE_11_PRODUCTION_REFS_GITHUB_DISCOVERY.md` |
| ADP-PHASE11-TRIAL-START-LAUNCH-PREFLIGHT-027 | E | completed | ADP-ACC-PHASE11-TRIAL-START-LAUNCH-PREFLIGHT | 13 focused tests OK; trial-start workflow now runs production refs discovery and launch readiness before live source, SMTP, Release, or start gate | `docs/phase_records/PHASE_11_TRIAL_START_LAUNCH_PREFLIGHT.md` |
| ADP-PHASE11-PRODUCTION-TRIAL-START-022 | E | blocked | ADP-ACC-PHASE11-PRODUCTION-TRIAL-START | precheck recorded PR #32/main CI, default_branch_ref, and trial_start_workflow_ref; still missing launch confirmation, runner, SMTP, Release, and workflow-vars refs | `docs/phase_records/PHASE_11_PRODUCTION_TRIAL_START_PRECHECK.md` |

## Release Gates

| Gate | Required evidence | Status |
|---|---|---|
| Phase 1 unit tests | unittest output | pass |
| Phase 2 contract/state tests | unittest output | pass |
| Phase 2 schema syntax | `json.tool` output | pass |
| Phase 3 arXiv adapter tests | unittest output and fixture parse | pass |
| Phase 4 ranking tests | golden score, evidence gate, metadata conflict gate, duplicate gate | pass |
| Phase 5 Claim Ledger gate tests | P0 locator, unsupported P0, metadata conflict, peer-review claim gate | pass |
| Phase 6 lesson linkage tests | supported claim IDs, unregistered claim rejection, visible claim markers | pass |
| Phase 7 narration/TTS dry-run gate | dry-run narration JSON, blocked real TTS, no audio paths | pass |
| Phase 8 storyboard/video dry-run gate | dry-run storyboard JSON, blocked render/write/download | pass |
| Phase 9 local dry-run pipeline | completed RunRecord, publication gate, Lesson, Narration, Storyboard, email preview | pass |
| Phase 10 runner/release/email handoff | completed RunRecord input, side-effect flags false, recipient preview | pass |
| Phase 11 final acceptance handoff | handoff readiness package, no unsupported 30-day/live-operation claim | pass |
| Phase 11 evidence-ref hardening | every production pass requirement needs non-empty evidence ref | pass |
| Phase 11 trial evidence validator | 30-day evidence package validates daily uniqueness, traceability, scheduler, Release, SMTP, resource, weekly/monthly replay, and recovery evidence | pass |
| Phase 11 production preflight | runtime commands, secret env keys, disk, memory, Git artifacts, and cache/staging checks | pass for gate; current environment blocked as expected |
| Phase 11 trial bootstrap workflow | manual GitHub workflow, self-hosted runner input, preflight-first ordering, artifact upload, and runbook | pass for bootstrap; no production side effects enabled |
| Phase 11 live arXiv source ingest | small-window Atom fetch, SourceItem validation, duplicate filtering, no PDF/bulk download | pass for code gate; current local live fetch blocked by Python SSL CA |
| Phase 11 SMTP delivery boundary | dry-run default, explicit allow-send, env-key checks, TLS-required mocked send, no secret/body logging | pass for code gate; no real production SMTP evidence claimed |
| Phase 11 Release delivery boundary | dry-run default, explicit allow-upload, target check, safe assets, no clobber upload, no notes/stdout/stderr logging | pass for code gate; no real private Release evidence claimed |
| Phase 11 scheduled production workflow gate | Australia/Sydney 04:45/05:00/05:10 schedules, manual rerun, production variable gates, preflight-first artifact, no SMTP/Release side effects | pass for scheduler contract; not enabled on default branch |
| Phase 11 scheduled execution driver | scheduled health-check, daily-run, watchdog execution reports, preflight refs, dry-run degradation, real SMTP/Release evidence refs before production count | pass for driver contract; no real production evidence claimed |
| Phase 11 daily input builder | passing SourceBatch to daily input report, Atom summary P0 claim, ranking selection audit, no PDF/bulk harvest, recent duplicate blocking | pass for builder contract; no real production evidence claimed |
| Phase 11 trial ledger update | production-ready scheduled daily-run append, duplicate blocking, daily refs, P0 traceability, and embedded trial validator output | pass for ledger update contract; no 30-day acceptance claimed |
| Phase 11 trial ledger state persistence | restore previous trial evidence ledger artifact, export updated state only after append, and avoid Git/media/secret/cache state retention | pass for state persistence contract; no real production evidence claimed |
| Phase 11 trial operational evidence annotation | explicit weekly/monthly replay, recovery, scheduler, Release, SMTP, and resource refs can be merged without hand-editing trial evidence | pass for annotation contract; no real production evidence claimed |
| Phase 11 trial replay evidence | weekly/monthly replay report from production daily entries, duplicate-free consecutive coverage, and durable replay ref before annotation | pass for replay evidence contract; no real production replay claimed |
| Phase 11 trial recovery evidence | failed/degraded scheduled daily-run plus recovered production-ready rerun with real sent notifications and durable refs before annotation | pass for recovery evidence contract; no real production recovery drill claimed |
| Phase 11 trial resource evidence | 30 unique daily resource refs matched to passing production preflight reports and durable resource evidence ref before annotation | pass for resource evidence contract; no real 30-day resource telemetry claimed |
| Phase 11 trial start gate | passing preflight, bootstrap, scheduler, live source, real SMTP, real Release, durable refs, and explicit confirmation before start-ready | pass for start-readiness contract; no real trial start or production acceptance claimed |
| Phase 11 trial start workflow | manual default-branch workflow that collects preflight, bootstrap, scheduler, source, SMTP, Release, and start-gate artifacts with explicit side-effect variables | pass for workflow contract; not yet run on default branch |
| Phase 11 production launch readiness | non-draft merged PR, expected head SHA binding, ready trial start workflow contract, durable runner/secret/Release/variable/default-branch refs, and explicit launch confirmation | pass for launch readiness contract; PR/default-branch gates are now satisfied after merge, while external durable refs and confirmation remain blocked |
| Phase 11 post-merge launch audit | latest required code merged to main, default branch contains workflow files, and launch gate blocks only external refs/confirmation | pass for audit; production launch remains blocked until durable refs and confirmation exist |
| Phase 11 Release permission hardening | trial-start and scheduled workflows declare `contents: write` for controlled draft Release creation | pass for contract; upload still blocked until explicit variables and Release delivery checks pass |
| Phase 11 production refs readiness bundle | no-secret runner, SMTP secret-name, Release target, and workflow variable readiness refs report | pass for refs bundle contract; real external refs still must be owner-provisioned before launch |
| Phase 11 production refs input template | no-secret owner-fillable JSON input template for production refs readiness | pass for template contract; generated template defaults blocked until durable refs are filled |
| Semantic coverage rollout contract | task-bound machine checks for active parameter values and formula fingerprints | machine_verified; 161 active parameters and all 32 active formulas machine-check, 0 active rows remain HUMAN_REVIEW_REQUIRED |
| Phase 11 production trial start | explicit confirmation, durable default branch, runner, SMTP, Release, workflow vars, and trial-start workflow refs | blocked; default branch and trial-start workflow refs recorded, while confirmation, runner, SMTP, Release, workflow-vars, and default-branch trial-start run evidence are not present |
| Production 30-day acceptance | 30-day run, scheduler, Release, SMTP, and resource evidence | blocked; evidence not present |
| Project governance | validator output | pass |
| Changed-only sync | validator output | pass |
| Diff hygiene | `git diff --check` | pass |
| Secrets/media guard | file review and `.gitignore` | pass |
