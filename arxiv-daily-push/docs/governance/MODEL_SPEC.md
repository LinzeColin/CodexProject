# MODEL_SPEC

Project: `arxiv-daily-push`
Governance spec version: `1.0.0`

machine_summary:

- model_count: 32
- formula_count: 34
- parameter_count: 176

Fact levels follow `docs/governance/STANDARD.md`.

## A. Model Overview

| Model ID | Name | Kind | Purpose | Status | Version | Implementation reference |
|---|---|---|---|---|---|---|
| MOD-ADP-001 | Phase 1 readiness and notification dry-run gate | deterministic rule engine | Classify local readiness and render non-secret email notifications | active | adp-foundation-v1 | `src/arxiv_daily_push/doctor.py`, `src/arxiv_daily_push/notifications.py` |
| MOD-ADP-004 | Generic data contract and RunRecord state gate | deterministic contract/state validator | Validate generic data boundaries and allowed run-state transitions without network or media work | active | adp-contracts-v1 | `src/arxiv_daily_push/contracts.py`, `src/arxiv_daily_push/state_machine.py` |
| MOD-ADP-005 | arXiv Atom source adapter | deterministic source adapter | Build bounded arXiv API URLs and map Atom entries into generic SourceItem records | active | adp-arxiv-adapter-v1 | `src/arxiv_daily_push/arxiv_adapter.py` |
| MOD-ADP-002 | 100-point arXiv selection score | deterministic scoring model | Select the daily learning item from eligible arXiv candidates | active | adp-ranking-v1 | `src/arxiv_daily_push/ranking.py` |
| MOD-ADP-003 | Claim Ledger publication gate | deterministic evidence gate | Block publication when key claims lack source locators or metadata is conflicted | active | adp-claim-gate-v1 | `src/arxiv_daily_push/evidence_gate.py` |
| MOD-ADP-006 | Evidence-linked Chinese lesson generator | deterministic lesson generator | Generate text-only Chinese Lesson JSON from supported Claim Ledger evidence | active | adp-lesson-v1 | `src/arxiv_daily_push/lesson.py` |
| MOD-ADP-007 | Narration and TTS dry-run gate | deterministic narration planner | Generate narration/TTS-ready dry-run JSON from Lesson objects while blocking media artifacts | active | adp-narration-v1 | `src/arxiv_daily_push/narration.py` |
| MOD-ADP-008 | Storyboard and video dry-run media gate | deterministic storyboard planner | Generate Storyboard JSON while blocking render/write/download media outputs | active | adp-video-dry-run-v1 | `src/arxiv_daily_push/video.py` |
| MOD-ADP-009 | Local daily dry-run pipeline | deterministic orchestration pipeline | Run a local daily dry-run through publication, Lesson, Narration, Storyboard, RunRecord completion, and email preview | active | adp-local-pipeline-v1 | `src/arxiv_daily_push/pipeline.py` |
| MOD-ADP-010 | Runner release email dry-run handoff | deterministic handoff gate | Build a handoff preview while keeping scheduler, Release upload, unattended execution, and real SMTP disabled | active | adp-handoff-v1 | `src/arxiv_daily_push/handoff.py` |
| MOD-ADP-011 | Final acceptance and handoff readiness gate | deterministic acceptance gate | Generate final handoff readiness package and accept production evidence only from validated trial reports | active | adp-acceptance-v1.2 | `src/arxiv_daily_push/acceptance.py` |
| MOD-ADP-012 | Thirty-day operational trial evidence validator | deterministic production evidence validator | Validate the 30-day trial evidence package before production acceptance can pass | active | adp-trial-evidence-v1 | `src/arxiv_daily_push/trial.py` |
| MOD-ADP-013 | Production preflight fail-closed gate | deterministic production readiness validator | Block scheduled production execution unless runtime, secret-key, resource, Git artifact, and cache gates pass | active | adp-production-preflight-v1 | `src/arxiv_daily_push/production_preflight.py` |
| MOD-ADP-014 | Manual production trial bootstrap gate | deterministic workflow contract validator | Validate the GitHub workflow/runbook entrypoint for preflight-first trial startup while keeping production side effects disabled | active | adp-trial-bootstrap-v1 | `src/arxiv_daily_push/trial_bootstrap.py`, `.github/workflows/arxiv-daily-push-production-trial.yml` |
| MOD-ADP-015 | Live arXiv latest source ingest | deterministic source ingest adapter | Fetch a small latest arXiv Atom window, parse SourceItems, and filter previously seen source IDs without downloading PDFs | active | adp-live-arxiv-ingest-v1 | `src/arxiv_daily_push/source_ingest.py` |
| MOD-ADP-016 | SMTP notification delivery boundary | deterministic notification transport gate | Produce dry-run SMTP delivery evidence by default and send real mail only with explicit allow flag plus configured SMTP environment keys | active | adp-smtp-delivery-v1 | `src/arxiv_daily_push/smtp_delivery.py` |
| MOD-ADP-017 | GitHub Release delivery boundary | deterministic release transport gate | Produce dry-run Release delivery evidence by default and create a GitHub Release only with explicit upload flag, configured target, safe assets, and `gh` | active | adp-release-delivery-v1 | `src/arxiv_daily_push/release_delivery.py` |
| MOD-ADP-018 | Scheduled production workflow gate | deterministic scheduler contract validator | Validate Australia/Sydney 04:45 health-check, 05:00 daily-run, 05:10 watchdog, and Release write permission while keeping production side effects disabled by default | active | adp-production-scheduler-v1 | `src/arxiv_daily_push/production_scheduler.py`, `.github/workflows/arxiv-daily-push-scheduled.yml` |
| MOD-ADP-019 | Scheduled execution driver | deterministic scheduled execution gate | Convert scheduled health-check, daily-run, and watchdog invocations into evidence artifacts while blocking unsupported production acceptance | active | adp-scheduled-execution-v1 | `src/arxiv_daily_push/scheduled_execution.py`, `.github/workflows/arxiv-daily-push-scheduled.yml` |
| MOD-ADP-020 | Daily input builder | deterministic source-to-input builder | Convert a passing arXiv SourceBatch into ranked daily pipeline input using Atom summary claims only | active | adp-daily-input-builder-v1 | `src/arxiv_daily_push/daily_input.py`, `.github/workflows/arxiv-daily-push-scheduled.yml` |
| MOD-ADP-021 | Trial evidence ledger update | deterministic trial ledger updater | Append one production-ready scheduled daily-run report into the 30-day trial evidence ledger without claiming acceptance early | active | adp-trial-ledger-v1 | `src/arxiv_daily_push/trial_ledger.py`, `.github/workflows/arxiv-daily-push-scheduled.yml` |
| MOD-ADP-022 | Trial ledger state persistence | deterministic workflow state bridge | Restore and upload small trial evidence ledger state artifacts across scheduled GitHub Actions runs | active | adp-trial-ledger-state-v1 | `.github/workflows/arxiv-daily-push-scheduled.yml`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-023 | Trial operational evidence annotation | deterministic operational evidence annotator | Merge explicit weekly/monthly replay, recovery drill, scheduler, Release, SMTP, and resource refs into trial evidence without hand-editing JSON | active | adp-trial-ops-evidence-v1 | `src/arxiv_daily_push/trial_ops.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-024 | Trial replay evidence builder | deterministic replay evidence validator | Build weekly/monthly replay evidence from production-ready daily trial entries and block missing durable refs or incomplete coverage | active | adp-trial-replay-v1 | `src/arxiv_daily_push/trial_replay.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-025 | Trial recovery evidence builder | deterministic recovery evidence validator | Build recovery drill evidence from a failed/degraded scheduled daily-run plus a recovered production-ready rerun while blocking dry-run notifications or missing durable refs | active | adp-trial-recovery-v1 | `src/arxiv_daily_push/trial_recovery.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-026 | Trial resource telemetry evidence builder | deterministic resource evidence validator | Build resource pressure evidence from daily trial resource refs and passing production preflight reports while blocking static or unmatched refs | active | adp-trial-resource-v1 | `src/arxiv_daily_push/trial_resource.py`, `src/arxiv_daily_push/production_preflight.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-027 | Trial start readiness gate | deterministic start-readiness validator | Aggregate preflight, bootstrap, scheduler, live source, SMTP, Release, and durable-ref evidence before a real 30-day production trial can be marked start-ready | active | adp-trial-start-v1 | `src/arxiv_daily_push/trial_start.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-028 | Trial start evidence workflow validator | deterministic workflow contract validator | Validate the manual GitHub workflow that collects default-branch trial start evidence artifacts, production refs discovery, launch readiness, and Release write permission on the private runner | active | adp-trial-start-workflow-v1 | `src/arxiv_daily_push/trial_start_workflow.py`, `src/arxiv_daily_push/cli.py`, `.github/workflows/arxiv-daily-push-trial-start.yml` |
| MOD-ADP-029 | Production launch readiness gate | deterministic launch-readiness validator | Block default-branch trial start dispatch until PR, workflow, runner, secrets, Release target, variables, refs, and confirmation are launch-ready | active | adp-production-launch-readiness-v1 | `src/arxiv_daily_push/production_launch.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-030 | Production refs readiness bundle | deterministic no-secret readiness validator | Generate a no-secret owner-fillable template, discover GitHub Actions metadata, run a GitHub-hosted provisioning audit, and review downloaded audit artifacts before launch readiness consumes refs | active | adp-production-refs-v1 | `src/arxiv_daily_push/production_refs.py`, `src/arxiv_daily_push/cli.py`, `.github/workflows/arxiv-daily-push-provisioning-audit.yml` |
| MOD-ADP-031 | Two-day simulation acceptance gate | deterministic simulation validator | Run the updated two-day Phase 11 simulation with mocked SMTP and Release boundaries while blocking network fetch, real side effects, secret reads, cache/media retention, and production acceptance claims | active | adp-two-day-simulation-v1 | `src/arxiv_daily_push/simulation.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-032 | All-arXiv Phase 12 scan queue delivery gate | deterministic source selection and delivery gate | Build all-arXiv daily input from bounded primary archive scans, persist ROI-ranked queue state, and require Release-hosted video artifact links before production email evidence can count | active | adp-all-arxiv-scan-v1 | `src/arxiv_daily_push/global_scan.py`, `src/arxiv_daily_push/scheduled_execution.py`, `.github/workflows/arxiv-daily-push-scheduled.yml` |

## B. Assumptions

| Assumption ID | Statement | Evidence | Scope | Status |
|---|---|---|---|---|
| ASM-ADP-001 | Phase 1 must not implement ingest, ranking, TTS, video, GitHub runner, or real email send. | `README.md`, `AGENTS.md`, `docs/phase_records/PHASE_01.md` | Phase 1 | active |
| ASM-ADP-002 | Email is the notification channel and `linzezhang35@gmail.com` is the recipient. | `config.py`, `config/examples/notification.example.yaml` | all phases | active |
| ASM-ADP-003 | Phase 1-11 use arXiv first while preserving generic source boundaries for later sources. | `docs/pursuing_goal/06_PURSUING_GOAL_READY_PROMPT.md` | all phases | active |
| ASM-ADP-004 | Phase 2 is limited to offline generic contracts and state validation; it must not fetch sources or generate publishable content. | `docs/phase_records/PHASE_02.md`, `src/arxiv_daily_push/contracts.py`, `src/arxiv_daily_push/state_machine.py` | Phase 2 | active |
| ASM-ADP-005 | Phase 3 implements the first arXiv adapter but keeps tests offline and does not perform scheduled or bulk ingestion. | `docs/phase_records/PHASE_03.md`, `src/arxiv_daily_push/arxiv_adapter.py`, `tests/fixtures/arxiv_atom_sample.xml` | Phase 3 | active |
| ASM-ADP-006 | Phase 4 ranks only explicit candidate inputs with supported P0 evidence and non-conflicting metadata; it does not extract claims or fetch live sources. | `docs/phase_records/PHASE_04.md`, `src/arxiv_daily_push/ranking.py`, `tests/test_ranking.py` | Phase 4 | active |
| ASM-ADP-007 | Phase 5 builds a Claim Ledger from explicit evidence claims and blocks publication on unsupported P0 claims, metadata conflicts, or unsupported arXiv peer-review claims. | `docs/phase_records/PHASE_05.md`, `src/arxiv_daily_push/evidence_gate.py`, `tests/test_evidence_gate.py` | Phase 5 | active |
| ASM-ADP-008 | Phase 6 generates deterministic Chinese Lesson JSON only from supported Claim Ledger evidence and does not create narration, TTS, video, runner automation, or SMTP output. | `docs/phase_records/PHASE_06.md`, `src/arxiv_daily_push/lesson.py`, `tests/test_lesson.py` | Phase 6 | active |
| ASM-ADP-009 | Phase 7 generates dry-run narration/TTS plan JSON from Lesson objects and blocks audio synthesis, model downloads, audio writes, and media retention. | `docs/phase_records/PHASE_07.md`, `src/arxiv_daily_push/narration.py`, `tests/test_narration.py` | Phase 7 | active |
| ASM-ADP-010 | Phase 8 generates Storyboard JSON and video media gate outputs in dry-run mode while blocking rendering, media writes, and asset downloads. | `docs/phase_records/PHASE_08.md`, `src/arxiv_daily_push/video.py`, `tests/test_video.py` | Phase 8 | active |
| ASM-ADP-011 | Phase 9 runs a local daily dry-run pipeline without scheduler, Release upload, or real SMTP send. | `docs/phase_records/PHASE_09.md`, `src/arxiv_daily_push/pipeline.py`, `tests/test_pipeline.py` | Phase 9 | active |
| ASM-ADP-012 | Phase 10 builds a runner/release/email handoff preview from a completed RunRecord while all external side effects remain disabled. | `docs/phase_records/PHASE_10.md`, `src/arxiv_daily_push/handoff.py`, `tests/test_handoff.py` | Phase 10 | active |
| ASM-ADP-013 | Phase 11 generates a truthful acceptance/handoff readiness package; production acceptance remains blocked unless real operational evidence is supplied. | `docs/phase_records/PHASE_11.md`, `src/arxiv_daily_push/acceptance.py`, `tests/test_acceptance.py` | Phase 11 | active |
| ASM-ADP-014 | Production acceptance pass requires non-empty evidence references for every true operational evidence flag. | `docs/phase_records/PHASE_11_EVIDENCE_REF_HARDENING.md`, `src/arxiv_daily_push/acceptance.py`, `tests/test_acceptance.py` | Phase 11 hardening | active |
| ASM-ADP-015 | Production acceptance pass requires operational evidence generated by the 30-day trial evidence validator, not raw manually supplied booleans. | `docs/phase_records/PHASE_11_TRIAL_EVIDENCE_VALIDATOR.md`, `src/arxiv_daily_push/trial.py`, `tests/test_trial.py` | Phase 11 hardening | active |
| ASM-ADP-016 | Scheduled production execution must be blocked unless runtime commands, secret environment keys, disk, memory, Git artifact hygiene, and local cache/staging checks pass without logging secret values. | `docs/phase_records/PHASE_11_PRODUCTION_PREFLIGHT.md`, `src/arxiv_daily_push/production_preflight.py`, `tests/test_production_preflight.py` | Phase 11 production preflight | active |
| ASM-ADP-017 | Production trial startup must be manual-only until prerequisites pass, run preflight before any trial work, upload preflight evidence, and avoid Release upload or SMTP sending in bootstrap mode. | `docs/phase_records/PHASE_11_TRIAL_BOOTSTRAP_WORKFLOW.md`, `src/arxiv_daily_push/trial_bootstrap.py`, `.github/workflows/arxiv-daily-push-production-trial.yml` | Phase 11 trial bootstrap | active |
| ASM-ADP-018 | Live arXiv source ingest must use the official Atom API, keep request windows small, filter duplicate source IDs, avoid PDF/bulk download, and fail closed on network, TLS, API, or SourceItem validation errors. | `docs/phase_records/PHASE_11_LIVE_ARXIV_INGEST.md`, `src/arxiv_daily_push/source_ingest.py`, `tests/test_source_ingest.py` | Phase 11 source ingest readiness | active |
| ASM-ADP-019 | SMTP notification transport must default to dry-run, require explicit `--allow-send` for real mail, use only external environment keys for secrets, require TLS, and never log SMTP secret values or email body text. | `docs/phase_records/PHASE_11_SMTP_DELIVERY.md`, `src/arxiv_daily_push/smtp_delivery.py`, `tests/test_notifications.py` | Phase 11 SMTP delivery readiness | active |
| ASM-ADP-020 | GitHub Release transport must default to dry-run, require explicit `--allow-upload` for real Release creation, use `ADP_RELEASE_TARGET` or `--target`, avoid clobber upload, and never log Release notes, secrets, `gh` stdout, or `gh` stderr. | `docs/phase_records/PHASE_11_RELEASE_DELIVERY.md`, `src/arxiv_daily_push/release_delivery.py`, `tests/test_release_delivery.py` | Phase 11 Release delivery readiness | active |
| ASM-ADP-021 | Scheduled production workflow must declare Australia/Sydney 04:45 health-check, 05:00 daily-run, and 05:10 watchdog slots, support manual rerun, run preflight first, and remain disabled unless production GitHub variables are explicitly configured. | `docs/phase_records/PHASE_11_PRODUCTION_SCHEDULER.md`, `.github/workflows/arxiv-daily-push-scheduled.yml`, `src/arxiv_daily_push/production_scheduler.py`, `tests/test_production_scheduler.py` | Phase 11 scheduler readiness | active |
| ASM-ADP-022 | Scheduled execution must produce evidence artifacts after preflight and may count as production evidence only when daily run, real SMTP, real Release, and resource evidence refs are present. | `docs/phase_records/PHASE_11_SCHEDULED_EXECUTION_DRIVER.md`, `src/arxiv_daily_push/scheduled_execution.py`, `tests/test_scheduled_execution.py` | Phase 11 scheduled execution readiness | active |
| ASM-ADP-023 | Daily input generation must use only arXiv Atom summary/metadata evidence, avoid PDF download and bulk harvest, and fail closed before scheduled daily-run if the source batch, summary, metadata, or ranking gate is unsafe. | `docs/phase_records/PHASE_11_DAILY_INPUT_BUILDER.md`, `src/arxiv_daily_push/daily_input.py`, `tests/test_daily_input.py` | Phase 11 daily input readiness | active |
| ASM-ADP-024 | Trial ledger updates may append daily evidence only from production-ready scheduled daily-run reports and must block duplicates, dry-run evidence, missing refs, unsupported claims, and misleading failure output. | `docs/phase_records/PHASE_11_TRIAL_LEDGER_UPDATE.md`, `src/arxiv_daily_push/trial_ledger.py`, `tests/test_trial_ledger.py` | Phase 11 trial ledger readiness | active |
| ASM-ADP-025 | Trial evidence ledger state must be carried forward as a small GitHub Actions artifact, never committed to Git, and must not be replaced when a daily ledger update is blocked. | `docs/phase_records/PHASE_11_TRIAL_LEDGER_STATE.md`, `.github/workflows/arxiv-daily-push-scheduled.yml`, `tests/test_production_scheduler.py` | Phase 11 trial ledger state readiness | active |
| ASM-ADP-026 | Weekly/monthly replay and recovery drill evidence must be merged through explicit refs, not by hand-editing trial evidence or inferring that the operations occurred. | `docs/phase_records/PHASE_11_TRIAL_OPS_EVIDENCE.md`, `src/arxiv_daily_push/trial_ops.py`, `tests/test_trial_ops.py` | Phase 11 operational evidence readiness | active |
| ASM-ADP-027 | Weekly/monthly replay evidence must be generated from production-ready daily trial entries and archived under a durable replay ref before it can be merged into trial evidence. | `docs/phase_records/PHASE_11_TRIAL_REPLAY_EVIDENCE.md`, `src/arxiv_daily_push/trial_replay.py`, `tests/test_trial_replay.py` | Phase 11 replay evidence readiness | active |
| ASM-ADP-028 | Recovery drill evidence must be generated from an archived failed/degraded scheduled daily-run report and a recovered production-ready rerun report with real sent notifications before it can be merged into trial evidence. | `docs/phase_records/PHASE_11_TRIAL_RECOVERY_EVIDENCE.md`, `src/arxiv_daily_push/trial_recovery.py`, `tests/test_trial_recovery.py` | Phase 11 recovery evidence readiness | active |
| ASM-ADP-029 | Resource telemetry evidence must be generated from unique daily trial resource refs that match passing production preflight reports before the global resource gate can be merged into trial evidence. | `docs/phase_records/PHASE_11_TRIAL_RESOURCE_EVIDENCE.md`, `src/arxiv_daily_push/trial_resource.py`, `tests/test_trial_resource.py` | Phase 11 resource evidence readiness | active |
| ASM-ADP-030 | A real 30-day production trial may be marked start-ready only after preflight, bootstrap, scheduler, live source, real SMTP, real Release, durable evidence refs, and explicit confirmation all pass. | `docs/phase_records/PHASE_11_TRIAL_START_GATE.md`, `src/arxiv_daily_push/trial_start.py`, `tests/test_trial_start.py` | Phase 11 trial start readiness | active |
| ASM-ADP-031 | The default-branch trial start evidence path must be manual-only, preflight-first, production-refs-checked, launch-readiness-checked, artifact-backed, and gated by explicit GitHub variables before any real SMTP or Release probe can run. | `docs/phase_records/PHASE_11_TRIAL_START_WORKFLOW.md`, `docs/phase_records/PHASE_11_TRIAL_START_LAUNCH_PREFLIGHT.md`, `.github/workflows/arxiv-daily-push-trial-start.yml`, `src/arxiv_daily_push/trial_start_workflow.py`, `tests/test_trial_start_workflow.py` | Phase 11 trial start workflow readiness | active |
| ASM-ADP-032 | Production launch may proceed only after the PR is non-draft and merged into `main`, the expected head SHA is bound, the workflow contract is ready, and durable refs exist for runner, SMTP secrets, Release target, workflow variables, and default-branch workflow location. | `docs/phase_records/PHASE_11_PRODUCTION_LAUNCH_READINESS.md`, `src/arxiv_daily_push/production_launch.py`, `tests/test_production_launch.py` | Phase 11 production launch readiness | active |
| ASM-ADP-033 | Production runner, SMTP secret, Release target, and workflow variable readiness must be collected through a no-secret template or GitHub metadata discovery as names and durable refs only; secret values and credential material must never enter the readiness report. | `src/arxiv_daily_push/production_refs.py`, `config/examples/production_refs.input.example.json`, `tests/test_production_refs.py`, `docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md` | Phase 11 production refs readiness | active |
| ASM-ADP-034 | The updated local Phase 11 goal is satisfied by a deterministic two-day simulation only when both scheduled daily runs and ledger appends pass with mocked SMTP/Release boundaries and no production acceptance claim. | `docs/phase_records/PHASE_11_TWO_DAY_SIMULATION.md`, `src/arxiv_daily_push/simulation.py`, `tests/test_simulation.py`, `governance/run_manifests/ADP-PHASE11-TWO-DAY-SIMULATION-20260622.json` | Phase 11 two-day simulation | active |
| ASM-ADP-035 | Production daily source selection must scan the primary arXiv archive set, not collapse to the legacy cs.AI-only query, and must persist a candidate queue with ROI-ranked fallback before real SMTP/Release delivery can count. | `docs/phase_records/PHASE_12_ALL_ARXIV_QUEUE_DELIVERY.md`, `src/arxiv_daily_push/global_scan.py`, `.github/workflows/arxiv-daily-push-scheduled.yml`, `tests/test_global_scan.py` | Phase 12 all-arXiv production path | active |

## C. Functions and Formulas

The machine-readable source is `formula_registry.yaml`.

- FORM-ADP-001 classifies Phase 1 readiness as `blocked`, `warn`, or `pass`.
- FORM-ADP-002 renders dry-run email subject/body without secrets.
- FORM-ADP-005 validates generic contract fields, enum sets, and P0 evidence locator requirements.
- FORM-ADP-006 validates allowed `RunRecord` transitions and terminal states.
- FORM-ADP-007 maps arXiv Atom metadata into generic `SourceItem` records with bounded query parameters.
- FORM-ADP-003 applies the active 100-point ranking weights and evidence/metadata eligibility gate.
- FORM-ADP-004 applies the active Claim Ledger publication hard-block rules.
- FORM-ADP-008 generates and validates Lesson JSON only from supported Claim Ledger claim IDs.
- FORM-ADP-009 generates narration dry-run JSON while blocking real TTS synthesis, audio writes, and model downloads.
- FORM-ADP-010 generates Storyboard dry-run JSON while blocking video rendering, media writes, and asset downloads.
- FORM-ADP-011 runs the local dry-run pipeline through the required RunRecord state sequence.
- FORM-ADP-012 builds a handoff only from a completed RunRecord and requires every external side-effect flag to be false.
- FORM-ADP-013 separates handoff readiness from production acceptance and blocks unsupported 30-day/live-operation claims; every production pass requirement also needs a non-empty evidence reference from `adp-trial-evidence-v1`.
- FORM-ADP-014 validates 30-day trial evidence across daily uniqueness, traceability, scheduler, Release, SMTP, resource, weekly/monthly replay, and recovery gates.
- FORM-ADP-015 blocks production execution unless runtime command, secret-key presence, disk, memory, Git artifact hygiene, and local cache/staging gates pass.
- FORM-ADP-016 validates the manual GitHub trial bootstrap workflow and runbook before a real 30-day trial can be started.
- FORM-ADP-017 fetches latest arXiv Atom SourceItems, validates them, and filters already-seen source IDs before ranking.
- FORM-ADP-018 emits SMTP delivery evidence in dry-run mode by default and blocks real sends unless explicit allow-send, SMTP env keys, recipient, TLS, and delivery checks pass.
- FORM-ADP-019 emits GitHub Release delivery evidence in dry-run mode by default and blocks real Release creation unless explicit allow-upload, Release target, safe assets, `gh`, and no-clobber checks pass.
- FORM-ADP-020 validates the scheduled production workflow contract across timezone schedule slots, manual rerun, production variable gates, preflight-first ordering, artifact evidence, Release write permission, and default side-effect disablement.
- FORM-ADP-021 runs one scheduled mode and only marks production evidence ready when preflight, daily run, real SMTP, real Release, and resource evidence refs all pass.
- FORM-ADP-022 builds daily pipeline input from a passing arXiv SourceBatch using only Atom summary claims, then applies ranking and duplicate gates.
- FORM-ADP-023 appends a scheduled daily-run report to trial evidence only when production-ready refs, P0 traceability, publication safety, and duplicate gates pass.
- FORM-ADP-024 restores prior trial evidence state from a configured path or previous artifact and exports the updated state only after a successful ledger append.
- FORM-ADP-025 merges explicit operational evidence refs into trial evidence and blocks verified operational flags that lack refs.
- FORM-ADP-026 builds weekly/monthly replay evidence only from production-ready daily entries with duplicate-free consecutive coverage and a durable replay ref.
- FORM-ADP-027 builds recovery drill evidence only from a failed/degraded scheduled daily-run and a recovered production-ready rerun with real sent notifications and durable failure/recovery refs.
- FORM-ADP-028 builds resource telemetry evidence only from unique daily resource refs that match passing production preflight reports and a durable resource evidence ref.
- FORM-ADP-029 builds trial start readiness only from passing preflight, bootstrap, scheduler, live source, real SMTP, real Release, durable refs, and explicit confirmation while performing no side effects.
- FORM-ADP-030 validates the manual default-branch trial start evidence workflow across dispatch confirmation, preflight, production refs and launch readiness ordering, artifact coverage, durable refs, secret safety, Release write permission, and explicit side-effect variable gates.
- FORM-ADP-031 validates production launch readiness across PR merged/non-draft state, expected head SHA binding, workflow contract readiness, durable external readiness refs, explicit launch confirmation, and no-side-effect safety.
- FORM-ADP-032 validates production refs template generation, GitHub metadata discovery, provisioning audit workflow, downloaded audit artifact review, and readiness across required runner, SMTP secret-name, Release target, workflow variable, durable-ref, no-secret-input, redacted discovery-error, audit artifact refs, and no-side-effect gates.
- FORM-ADP-033 validates the two-day simulation across consecutive dates, mocked scheduled daily runs, mocked SMTP/Release evidence, trial ledger appends, unique source/publication IDs, no secret leakage, no Codex auth read, no network fetch, and no production acceptance claim.
- FORM-ADP-034 validates the Phase 12 all-arXiv scan, ROI/learning-value ranking, candidate queue fallback, Release-hosted video artifact link, Chinese lesson email, candidate queue summary, and no legacy cs.AI-only production default.

## D. Parameters

The canonical parameter catalog is `parameter_registry.csv`.

- Active Phase 1 parameters: PARAM-ADP-001 through PARAM-ADP-008.
- Active Phase 2 contract/state parameters: PARAM-ADP-020 through PARAM-ADP-028.
- Active Phase 3 arXiv adapter parameters: PARAM-ADP-029 through PARAM-ADP-034.
- Active Phase 4 ranking weights: PARAM-ADP-009 through PARAM-ADP-016.
- Active Phase 5 evidence gate parameters: PARAM-ADP-017 through PARAM-ADP-018.
- Active Phase 6 lesson parameters: PARAM-ADP-035 through PARAM-ADP-036.
- Active Phase 7 narration/TTS dry-run parameters: PARAM-ADP-037 through PARAM-ADP-040.
- Active Phase 8 video dry-run parameters: PARAM-ADP-041 through PARAM-ADP-044.
- Active Phase 9 local pipeline parameters: PARAM-ADP-045 through PARAM-ADP-047.
- Active Phase 10 handoff parameters: PARAM-ADP-048 through PARAM-ADP-050.
- Active Phase 11 acceptance parameters: PARAM-ADP-051 through PARAM-ADP-056 and PARAM-ADP-064.
- Active Phase 11 trial evidence parameters: PARAM-ADP-057 through PARAM-ADP-063.
- Active Phase 11 production preflight parameters: PARAM-ADP-065 through PARAM-ADP-070.
- Active Phase 11 trial bootstrap parameters: PARAM-ADP-071 through PARAM-ADP-074.
- Active Phase 11 live source ingest parameters: PARAM-ADP-075 through PARAM-ADP-080.
- Active Phase 11 SMTP delivery parameters: PARAM-ADP-081 through PARAM-ADP-085.
- Active Phase 11 Release delivery parameters: PARAM-ADP-086 through PARAM-ADP-091.
- Active Phase 11 scheduler parameters: PARAM-ADP-092 through PARAM-ADP-096 plus PARAM-ADP-160.
- Active Phase 11 scheduled execution parameters: PARAM-ADP-097 through PARAM-ADP-101.
- Active Phase 11 daily input builder parameters: PARAM-ADP-102 through PARAM-ADP-107.
- Active Phase 11 trial ledger parameters: PARAM-ADP-108 through PARAM-ADP-112.
- Active Phase 11 trial ledger state parameters: PARAM-ADP-113 through PARAM-ADP-117.
- Active Phase 11 trial operational evidence parameters: PARAM-ADP-118 through PARAM-ADP-122.
- Active Phase 11 trial replay evidence parameters: PARAM-ADP-123 through PARAM-ADP-127.
- Active Phase 11 trial recovery evidence parameters: PARAM-ADP-128 through PARAM-ADP-132.
- Active Phase 11 trial resource evidence parameters: PARAM-ADP-133 through PARAM-ADP-137.
- Active Phase 11 trial start gate parameters: PARAM-ADP-138 through PARAM-ADP-143.
- Active Phase 11 trial start workflow parameters: PARAM-ADP-144 through PARAM-ADP-148 plus PARAM-ADP-161 and PARAM-ADP-164.
- Active Phase 11 production launch readiness parameters: PARAM-ADP-149 through PARAM-ADP-153.
- Active Phase 11 production refs readiness parameters: PARAM-ADP-154 through PARAM-ADP-159 plus PARAM-ADP-162, PARAM-ADP-163, PARAM-ADP-165, and PARAM-ADP-166.
- Active Phase 11 two-day simulation parameters: PARAM-ADP-167 through PARAM-ADP-169.
- Active Phase 12 all-arXiv scan queue delivery parameters: PARAM-ADP-170 through PARAM-ADP-176.
- Planned video evidence policy parameter: PARAM-ADP-019.

## E. Methodology

Phase 2 implements deterministic, dependency-free validation for the generic
objects required by the pursuing goal: `SourceItem`, `EvidenceClaim`, `Lesson`,
`Storyboard`, `Publication`, and `RunRecord`. The runtime validators intentionally
mirror the schema boundaries without introducing a JSON Schema dependency.

The `RunRecord` state machine is deliberately narrow: it accepts only explicit
forward transitions, blocks skipped evidence states, and treats `completed`,
`blocked`, and `failed` as terminal states. It does not imply that ingest,
ranking, evidence extraction, lesson generation, media generation, runner
automation, or SMTP transport is implemented.

Phase 3 adds the first concrete adapter for arXiv Atom responses. It uses the
official API shape documented by arXiv: query URLs are sent to `export.arxiv.org`
and results are Atom feeds. The adapter maps entries to generic `SourceItem`
objects and keeps arXiv-specific fields in `metadata.arxiv`.

Phase 4 adds deterministic candidate ranking. It requires valid `SourceItem`
records, explicit `EvidenceClaim` inputs with at least one supported P0 claim,
non-conflicting metadata, and normalized component signals. The output is a
queue audit with component scores, blocking reasons, and the selected candidate.

Phase 5 builds a Claim Ledger from explicit evidence claims and gates
publication. It produces a `Publication` record with a Claim Ledger artifact and
blocks on missing P0 locators, unsupported P0 claims, metadata conflicts, and
arXiv peer-review claims that only cite arXiv.

Phase 6 generates text-only Chinese Lesson JSON from supported Claim Ledger
claims. It rejects blocked ledgers, excludes unverified or unsupported non-P0
claims, requires Lesson and section claim IDs to be known supported claims, and
requires visible `[claim_id]` markers in every generated section body.

Phase 7 generates narration/TTS-ready dry-run JSON from Lesson objects. It maps
each Lesson section to a narration segment, estimates duration without audio
output, reports local TTS resource readiness, and keeps real synthesis, audio
writes, model downloads, and retained media artifacts blocked.

Phase 8 generates Storyboard JSON from narration segments. It maps each segment
to a visual scene, reports local video media readiness, and keeps rendering,
media writes, asset downloads, and retained video artifacts blocked.

Phase 9 runs the local daily dry-run pipeline over explicit source and claim
inputs. It produces the publication gate output, Lesson, Narration, Storyboard,
RunRecord completion, and an email preview without scheduling or sending.

Phase 10 builds the runner/release/email handoff preview from a completed
dry-run payload. The handoff records the intended recipient and artifact
previews, but validation requires scheduler, GitHub Actions runner, unattended
execution, Release upload, and real SMTP sending to remain disabled.

Phase 11 generates the final acceptance and handoff readiness package. It
validates the Phase 10 handoff, lists production requirements, and marks
production acceptance as blocked unless 30-day trial, scheduler, Release, SMTP,
and resource-pressure evidence are explicitly supplied by a validated trial
evidence report with non-empty evidence references.

The Phase 11 trial evidence validator reads a JSON evidence package and checks
the real completion criteria before acceptance can pass: 30 unique daily run
dates, no duplicate source/publication IDs, P0 traceability, no misleading or
unsupported publication, 05:00 scheduler evidence, 04:45 health check and manual
rerun evidence, private Release refs, real SMTP refs for
`linzezhang35@gmail.com`, resource/secret hygiene refs, weekly/monthly replay,
and failure recovery drill evidence. It does not perform scheduling, Release
upload, SMTP sending, video rendering, or secret inspection.

The production preflight gate runs before any scheduled production execution. It
checks command availability, required secret environment key presence without
logging values, disk and memory thresholds, Git tracked/untracked artifact
hygiene, and local cache/staging directories. It blocks execution if any gate is
missing or unsafe, and it does not read `~/.codex/auth.json`, send email, upload
Releases, schedule jobs, render media, or download models.

The production trial bootstrap gate validates the GitHub workflow and runbook
used to start the real trial path. The workflow is manual-only, requires
`confirm_production_trial=true`, targets a private self-hosted runner label,
runs `adp preflight-production` before project tests, uploads the preflight JSON
artifact, and keeps cron scheduling, Release upload, and SMTP sending disabled
in bootstrap mode.

The live arXiv source ingest gate fetches a small latest Atom window from the
official query API, parses entries through the generic `SourceItem` adapter, and
filters out previously seen `source_id` values before ranking. It avoids PDF
download and bulk harvest, records the API request metadata, and blocks on
network, TLS, API, Atom parsing, duplicate-only, or SourceItem validation
failures.

The SMTP notification delivery gate renders the existing email notification into
delivery evidence. It defaults to dry-run and does not require secrets in that
mode. Real SMTP sending requires the explicit `--allow-send` flag, the configured
recipient, all SMTP environment keys, valid port parsing, TLS startup, login, and
successful `send_message`. Reports include the subject, recipient, body SHA256,
and key names only; they do not log SMTP secret values or the email body.

The GitHub Release delivery gate turns an explicit list of local evidence
artifacts into Release delivery evidence. It defaults to dry-run and does not
call GitHub in that mode. Real Release creation requires `--allow-upload`,
`ADP_RELEASE_TARGET` or `--target`, `gh`, non-empty safe assets, a tag, title,
and notes. Reports include asset names, sizes, SHA256 values, tag, target, and a
redacted command preview only; they do not log Release notes, secret values,
`gh` stdout, or `gh` stderr, and they never use clobber upload.

The scheduled production workflow gate validates the GitHub Actions schedule
contract before real scheduled execution is allowed. It requires timezone-aware
`Australia/Sydney` schedule slots for the 04:45 health check, 05:00 daily run,
and 05:10 watchdog; it supports manual rerun with explicit confirmation; it
skips scheduled work unless `ADP_PRODUCTION_ENABLED=true`; it runs production
preflight before any scheduled mode; uploads preflight and scheduled execution
evidence artifacts; and keeps real SMTP sending and Release upload off unless
their dedicated enablement variables are explicitly configured.

The scheduled execution driver is the runtime bridge after the scheduler gate.
It reads the production preflight report, runs one scheduled mode, and produces
an `adp-scheduled-execution-v1` report. Health-check can succeed when preflight
passes. Daily-run remains blocked until `ADP_SCHEDULED_RUN_ENABLED=true` and a
daily input package is supplied. Dry-run SMTP or dry-run Release side effects
produce `degraded` evidence with exit code 2. Production evidence can be counted
only when the daily run completes and real SMTP, real Release, and resource
evidence refs are all present.

The daily input builder connects live arXiv source ingest to scheduled daily
execution. It accepts only a validated `adp-live-arxiv-ingest-v1` SourceBatch,
creates supported P0 evidence claims from Atom `<summary>` text, adds bounded
ranking signals, selects one candidate through the existing ranking gate, and
emits a daily input package usable by `run-daily-dry-run` and scheduled
daily-run. It blocks on missing summaries, blocked source batches, metadata
conflicts, recent duplicate selections, and ineligible ranking results. It does
not download PDFs, perform bulk harvest, or infer peer review status from arXiv.

The trial evidence ledger updater connects scheduled daily-run execution
artifacts to the 30-day trial evidence package. It validates the scheduled
execution report, requires `production_evidence_ready=true`, extracts a single
daily run entry with daily run, Release, SMTP, and resource refs, blocks
duplicate dates/source IDs/publication IDs, and re-runs the 30-day trial
evidence validator after appending. It may return a passing ledger update while
the embedded trial evidence report remains blocked until all 30-day, scheduler,
weekly/monthly, recovery, and resource gates are satisfied.

The trial ledger state persistence bridge carries that JSON state between
scheduled workflow runs. It prefers an explicit configured trial evidence path;
otherwise it uses `gh run download` to recover the previous successful
`adp-trial-evidence-ledger` artifact. After a successful append it exports the
updated `trial_evidence` JSON with `export-trial-ledger-state` and uploads the
replacement state artifact. Blocked ledger updates do not overwrite the previous
state.

The trial operational evidence annotator merges explicit weekly/monthly replay,
recovery drill, scheduler, Release, SMTP, and resource refs into the accumulated
trial evidence JSON. It blocks verified flags without refs and exports updated
state only when the annotation actually changed evidence.

The trial replay evidence builder generates an auditable weekly/monthly replay
report from the accumulated daily trial entries. It requires production-ready
daily refs, duplicate-free date/source/publication coverage, 7 consecutive days
for weekly replay, 30 consecutive days for monthly replay, and a durable replay
ref before its annotation hint can be used by the ops annotator.

The trial recovery evidence builder generates an auditable recovery drill report
from one failed, blocked, or degraded scheduled daily-run report and one later
production-ready scheduled daily-run rerun. It requires real sent failure and
recovery notifications, daily run, Release, SMTP, and resource refs on the
recovery execution, durable refs for both executions, and matching daily dates
when both reports include `daily_run_report` details. Its output is an
annotation hint for the ops annotator and does not rerun the scheduler, send
mail, upload Releases, mutate the trial ledger, or claim production acceptance.

The trial resource telemetry evidence builder generates an auditable resource
evidence report from the accumulated trial ledger and archived production
preflight reports. It requires 30 unique daily `resource_gate_ref` values, a
matching passing production preflight report for each daily ref, passing disk,
memory, Git artifact, cache, and secret-environment gates, and a durable
resource evidence ref before its annotation hint can be used by the ops
annotator. Production preflight refs are timestamped so each daily run can be
matched to its own resource gate evidence.

## F. Strategy Logic

- Unrecognized source or claim enum -> validation error.
- P0 claim without a stable locator -> validation error.
- Skipped `RunRecord` transition -> validation error.
- Terminal `RunRecord` state with `running` status -> validation error.
- CLI `validate-record` returns exit 2 when validation errors are present.
- arXiv query `max_results` above the local Phase 3 cap -> validation error.
- arXiv API error Atom entry -> adapter error.
- Parsed arXiv entry -> `source_type=arxiv`, `source_adapter=arxiv.atom.v1`, arXiv fields under `metadata.arxiv`.
- Missing P0 evidence before ranking -> candidate ineligible.
- arXiv metadata conflicts before ranking -> candidate ineligible.
- Ranking weights not summing to 100 -> validation error.
- Same candidate ranking input -> same score and deterministic tie-break order.
- P0 claim without supported status -> publication blocked.
- arXiv peer-review claim without independent non-arXiv evidence -> publication blocked.
- Blocked Claim Ledger -> lesson generation blocked.
- Unsupported or unregistered claim ID in Lesson -> lesson validation error.
- Missing visible claim marker in section body -> lesson validation error.
- Non-dry-run TTS mode -> narration generation error.
- Audio path in dry-run narration -> narration validation error.
- Model download or audio write flag in Phase 7 -> narration validation error.
- Video render, media write, or asset download flag in Phase 8 -> storyboard validation error.
- Scene claim outside narration claims -> storyboard validation error.
- Incomplete RunRecord in Phase 10 -> handoff generation error.
- Scheduler, GitHub Actions runner, unattended execution, Release upload, or real SMTP enabled in Phase 10 -> handoff validation error.
- Missing 30-day trial, scheduler, Release, SMTP, or resource evidence in Phase 11 -> production acceptance blocked.
- Production evidence boolean without a non-empty evidence reference -> production acceptance blocked.
- Production evidence not generated by `adp-trial-evidence-v1` -> production acceptance blocked.
- Trial evidence with fewer than 30 unique dates -> production evidence blocked.
- Trial evidence with duplicate source or publication IDs -> production evidence blocked.
- Trial evidence with untraceable P0 claims, unsupported publications, misleading failure output, missing weekly/monthly replay, missing recovery drill, or missing resource/secret hygiene refs -> production evidence blocked.
- Trial replay without a requested weekly or monthly mode -> replay evidence blocked.
- Trial replay without a durable replay ref -> replay evidence blocked.
- Trial replay with duplicate daily dates, source IDs, publication IDs, missing production refs, or insufficient consecutive coverage -> replay evidence blocked.
- Trial recovery without a failed/degraded scheduled daily-run and a succeeded production-ready rerun -> recovery evidence blocked.
- Trial recovery without real sent failure and recovery notifications -> recovery evidence blocked.
- Trial recovery without durable failure and recovery refs -> recovery evidence blocked.
- Trial recovery with mismatched failure/recovery daily dates when both are present -> recovery evidence blocked.
- Trial resource evidence without 30 unique daily resource refs -> resource evidence blocked.
- Trial resource evidence without matching passing preflight reports -> resource evidence blocked.
- Trial resource evidence without a durable resource ref -> resource evidence blocked.
- Missing production command, secret environment key, disk threshold, memory threshold, Git artifact hygiene, or local cache/staging cleanliness -> production preflight blocked.
- Production preflight never logs secret values and never reads Codex auth.
- Trial bootstrap without manual confirmation, self-hosted runner targeting, preflight-first ordering, artifact upload, GitHub secret-name mapping, or runbook evidence path -> bootstrap validation blocked.
- Trial bootstrap never enables cron, Release upload, SMTP sending, secret value logging, or Codex auth access.
- Live arXiv ingest with network/TLS/API/Atom errors -> source batch blocked.
- Live arXiv ingest with only previously seen source IDs -> source batch blocked to avoid duplicate publication.
- Live arXiv ingest never downloads PDFs or performs bulk harvest.
- SMTP delivery without `--allow-send` -> dry-run evidence only, no SMTP connection.
- SMTP delivery with `--allow-send` but missing SMTP env keys, invalid port, wrong recipient, SMTP failure, or refused recipient -> blocked.
- SMTP delivery reports never log SMTP secret values or email body text.
- Scheduled workflow without `run-scheduled-production` or `adp-scheduled-execution` artifact upload -> scheduler validation blocked.
- Scheduled daily execution without `ADP_SCHEDULED_RUN_ENABLED=true` -> scheduled execution blocked.
- Scheduled daily execution without daily input package -> scheduled execution blocked.
- Scheduled daily execution with dry-run SMTP or dry-run Release -> scheduled execution degraded and not production evidence.
- Scheduled production evidence ready without daily run, Release, email, and resource refs -> validation error.
- Daily input builder source batch blocked -> daily input report blocked.
- Daily input builder missing Atom summary -> daily input report blocked.
- Daily input builder selected candidate recently used -> daily input report blocked.
- Daily input builder pass -> daily input contains SourceItem, supported claims, date, run_id, and selection audit.
- All-arXiv scan plan missing a primary archive bucket or collapsing to `cat:cs.AI` -> Phase 12 daily input blocked.
- All-arXiv daily selection chooses one new high-value candidate first, otherwise consumes a queued high-value candidate, otherwise blocks if no candidate meets the minimum threshold.
- Phase 12 candidate queue persists high-value unselected candidates as a small JSON artifact and never stores PDFs, media, model weights, or secrets.
- Scheduled production email cannot count as production-ready unless it includes Chinese lesson content, candidate queue summary, and a GitHub Release-hosted video artifact link.
- Production refs discovery without `gh`, with failed GitHub metadata access, missing runner label, missing SMTP secret names, missing workflow variables, empty `ADP_RELEASE_TARGET`, or secret-like input -> refs report blocked or redacted discovery error.
- Production pass with any missing requirement -> acceptance validation error.

## G. Validation

Current focused validation:

- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`
- `python3 -m json.tool arxiv-daily-push/schemas/*.schema.json`
- `python3 scripts/validate_project_governance.py --project arxiv-daily-push`
- `python3 scripts/validate_project_governance.py --changed-only --enforce-sync`
- `git diff --check`

Uncovered planned scenarios:

- arXiv network ingest idempotency.
- Claim extraction from paper text/PDF.
- TTS/video sample gates.
- Live 30-day operational trial evidence.
- GitHub self-hosted runner, private Release, and real email transport health.
- GitHub metadata discovery on the actual private runner after owner provisioning.
- Actual production preflight pass on a provisioned runner with SMTP, Release, and media dependencies installed.
- Actual 30-day trial start and scheduled daily run execution on the provisioned runner.
- Local Python HTTPS certificate validation for `https://export.arxiv.org/api/query` currently blocks live source ingest on this machine.
- Real SMTP delivery against the provisioned production SMTP server and archived message evidence.
- Actual weekly/monthly replay execution archived under a durable GitHub Actions artifact or private Release ref.
- Actual recovery drill execution archived under a durable GitHub Actions artifact or private Release ref.
- Actual 30-day resource telemetry evidence archived under a durable GitHub Actions artifact or private Release ref.
