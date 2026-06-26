# MODEL_SPEC

Project: `arxiv-daily-push`
Governance spec version: `1.0.0`

machine_summary:

- model_count: 106
- formula_count: 108
- parameter_count: 919

Fact levels follow `docs/governance/STANDARD.md`.

## Governance Notes

- `S1-02-BASELINE-LOCK-TRACEABILITY-001` locked the Review8 V4 two-stage
  pursuing-goal baseline and repaired version metadata drift only. It did not
  change active model algorithms, formulas, parameter values, scoring behavior,
  ranking behavior, Claim Ledger gates, SMTP behavior, Release behavior,
  scheduler behavior, or media behavior.

- `LOCAL-RUNNER-USER-CENTER-SYNC-GATE` adds `MOD-ADP-106`. It requires
  `local_runner` daily pass and real SMTP attempts to depend on successful
  shallow GitHub user-center learning snapshot sync from S2PJT02/S2PJT03
  reports. Missing reports, failed write, or remaining
  `待今日运行快照写入` fields block the daily report and block SMTP send
  attempts. It does not enable SMTP, install scheduler, upload Release,
  change public schema or DB, mutate production queues, change source adapters
  or ranking, edit CURRENT or V7.1/V7.2 contracts, close inherited P0/P1,
  enable DAILY_OPERATION, or claim integrated production acceptance.

- `S2PMT05-DUPLICATE-TRIGGER-B007` refreshes `MOD-ADP-098` and
  `FORM-ADP-100`. It adds a local multi-actor duplicate-trigger gate for
  inherited B-007 with github_schedule/local_launchd/manual_retry/
  restart_catchup actor coverage, M1-M4 x 100 attempts, `mail_key`,
  `lease_owner`, `fencing_token`, exactly one active revision per product,
  reason-coded `MAIL_KEY_ALREADY_CLAIMED` blocked attempts, and no scheduler
  side effects. It does not install scheduler, trigger real catch-up, enable
  SMTP, upload Release, change public schema or DB, mutate production queues,
  change source adapters or ranking, edit CURRENT or V7.1/V7.2 contracts,
  close inherited P0/P1, enable DAILY_OPERATION, or claim integrated
  production acceptance.

- `S2PMT05-SMTP-CRASH-WINDOW-B008` refreshes `MOD-ADP-098` and
  `FORM-ADP-100`. It adds a local SMTP accepted-before-local-commit
  crash-window gate for inherited B-008 with outbox claim before SMTP
  acceptance, explicit `ACCEPTED_PENDING_COMMIT`, stable same-revision
  `message_id`, changed `message_id` for changed content revision, blocked
  resend without durable `provider_accept_ref`, local finalization with
  `smtp-accept://...` provider ref, and no real SMTP side effects. It does not
  send SMTP, install scheduler, trigger real catch-up, upload Release, change
  public schema or DB, mutate production queues, change source adapters or
  ranking, edit CURRENT or V7.1/V7.2 contracts, close inherited P0/P1, enable
  DAILY_OPERATION, or claim integrated production acceptance.

- `S2PMT05-CAPACITY-BASELINE-B006` refreshes `MOD-ADP-098` and
  `FORM-ADP-100`. It adds a local formal capacity baseline gate for inherited
  B-006 with load/stress/spike/soak rows, 1x/2x/5x multipliers,
  throughput/latency/queue/memory/disk/error metrics, max queue age `1800`,
  max error rate `0.001`, accelerated local 24h soak, and rebuildable-only
  spike shedding. It does not run a real production load test, enable SMTP,
  install scheduler, upload Release, change public schema or DB, mutate
  production queues, change source adapters or ranking, edit CURRENT or
  V7.1/V7.2 contracts, close inherited P0/P1, enable DAILY_OPERATION, or claim
  integrated production acceptance.

- `S2PMT05-FAULT-INJECTION-B009` refreshes `MOD-ADP-098` and
  `FORM-ADP-100`. It adds a local systematic fault-injection gate for
  inherited B-009 with ENOSPC, read-only target, SQLITE_BUSY, corrupt JSON
  cache, corrupt PDF artifact, corrupt backup manifest, backup path collision,
  explicit recovery states, no partial artifact commit, durable evidence
  preservation, and fail-closed checks. It does not execute production restore,
  enable SMTP, install scheduler, upload Release, change public schema or DB,
  mutate production queues, change source adapters or ranking, edit CURRENT or
  V7.1/V7.2 contracts, close inherited P0/P1, enable DAILY_OPERATION, or claim
  integrated production acceptance.

- `S2PMT05-TIME-POLICY-B010` refreshes `MOD-ADP-098` and `FORM-ADP-100`.
  It adds a local structured time-policy gate for inherited B-010 with
  Australia/Sydney 05:00 schedule, 3600-second misfire grace, one-cycle
  catch-up bound, DST fold/gap cases, 8h sleep recovery, NTP backward/forward
  clock-jump cases, local business-date cycle IDs plus UTC watermarks, and no
  duplicate M4 watermark. It does not install scheduler, trigger a real
  catch-up run, enable SMTP, upload Release, change public schema or DB, mutate
  production queues, change source adapters or ranking, edit CURRENT or
  V7.1/V7.2 contracts, close inherited P0/P1, enable DAILY_OPERATION, or claim
  integrated production acceptance.

- `S2PMT05-E2E-B012` refreshes `MOD-ADP-098` and `FORM-ADP-100`. It adds a
  local 35-day E2E audit-bundle gate for inherited B-012 with daily 3+1,
  weekly, monthly, review, action, and ROI count conservation, section
  artifacts, artifact index, link graph, deterministic bundle hash, and
  reachable review/action/ROI links. It does not execute a real 35-day
  production replay, enable SMTP, install scheduler, upload Release, change
  public schema or DB, mutate production queues, change source adapters or
  ranking, edit CURRENT or V7.1/V7.2 contracts, close inherited P0/P1, enable
  DAILY_OPERATION, or claim integrated production acceptance.

- `S1P5T04` imported the V6 task-numbering roadmap and recorded two
  controlled GitHub/cloud-runner Gmail SMTP send artifacts from run
  `28002478689`: `7811543123` and `7816791617`. PR #82 then produced the
  post-merge cloud artifact `7818287996`, which reports
  `ARXIV_PRODUCTION_ACCEPTED` with 49 real arXiv candidates, 30 selected samples,
  20/20 primary archive buckets, and no production side effects. Production
  scheduling remains disabled until GitHub repository variables/secrets are
  explicitly enabled and verified.

- `S1P5T03-R` reconciled the stricter owner standard after the manual delivery
  test by running 30 real historical arXiv as-of dates on GitHub/cloud runner.
  PR #94 run `28027759062` artifact `7821452823` reports 30/30 success,
  30 unique dates, 30 real arXiv source IDs, no future leakage, no duplicate
  lead, no queue-continuity breaks, no P0/P1, and 299 persistent
  `CONTENT_LEDGER.csv` rows. This restores strict Stage 1
  `ARXIV_PRODUCTION_ACCEPTED` while production scheduling remains disabled.

- `S1P5T04` / `0.23.0` adds `MOD-ADP-045`, an accelerated real-arXiv
  acceptance evidence builder. It can only pass from a GitHub/cloud live
  all-arXiv dry-run with at least 30 real candidates plus the existing
  controlled SMTP refs; it sends no new email and keeps production scheduling
  disabled.

- `S2P1T01` / `0.23.0` adds disabled Stage 2 bioRxiv and medRxiv
  metadata-only preprint source promotion scaffolding. The new models can fetch
  small official details API windows, build separate shadow queue/ledger/email
  previews, and run no-send shadow evidence, but they cannot enter formal
  production until a 30-date terminal replay and 48-hour shadow gate both pass.

- `S2P1T01` replay/shadow evidence adds `MOD-ADP-050`. It runs deterministic
  30-date historical preprint replay through the no-send shadow daily path,
  persists local queue/ledger/report/email-preview artifacts, builds a 48-hour
  shadow aggregate, and feeds the source promotion gate. It still does not claim
  full Stage 2 production acceptance.

- `S2PCT01` / legacy `S2P2T01` adds `MOD-ADP-051` and `MOD-ADP-052`.
  They cover Nature/top-journal metadata-only ingest and no-send shadow daily
  evidence after PR #119 merged to `main@047f453`; they do not claim D2
  source-domain acceptance, Stage 2 production acceptance, SMTP, Release,
  scheduler, PDF/full-text download, or paywall bypass.

- `S2PCT02` / legacy `S2P2T02` adds `MOD-ADP-053` and `MOD-ADP-054`.
  They cover Science metadata-only ingest, Research Article/Report/Review/
  Perspective article-type gates, DOI identity, and no-send shadow daily
  evidence. They do not claim D2 source-domain acceptance, Stage 2 production
  acceptance, SMTP, Release, scheduler, PDF/full-text download, or paywall
  bypass.

- `S2PCT03` / legacy `S2P2T03` adds `MOD-ADP-055` and `MOD-ADP-056`.
  They cover The Lancet metadata-only ingest, Online First/current RSS
  alignment, medical article-type gates, DOI-query-ready PubMed relation
  metadata, and no-send shadow daily evidence. They do not claim D2
  source-domain acceptance, Stage 2 production acceptance, SMTP, Release,
  scheduler, PubMed full-record harvesting, PDF/full-text download, or paywall
  bypass.

- `S2PCT04` / legacy `S2P2T04` adds `MOD-ADP-057`. It covers top-journal
  profile taxonomy, publication relation edges, correction/retraction forced
  events, and old-conclusion update behavior without claiming D2 source-domain
  acceptance, Stage 2 production acceptance, SMTP, Release, scheduler,
  PDF/full-text download, or paywall bypass.

- `S2PCT05` adds `MOD-ADP-058`. It covers engineering public-signal taxonomy,
  officiality checks, version traceability, paper relation metadata, and
  reproducibility state gates for official code repositories, releases,
  model cards, benchmark results, and standards/specifications. It has no
  legacy alias and does not claim D2 source-domain acceptance, Stage 2
  production acceptance, SMTP, Release, scheduler, repository clone, PDF/full
  text download, paid API use, or paywall bypass.

- `S2PCT06` adds `MOD-ADP-059`. It covers authoritative research institution
  reports, public laboratory technical reports, industry technical reports, and
  product technical notes linked to known S2PCT05 engineering public signals.
  It validates publisher identity, interest relation, evidence level, report
  version/source traceability, and canonical-paper traceability. It has no
  legacy alias and does not claim D2 source-domain acceptance, Stage 2
  production acceptance, SMTP, Release, scheduler, PDF/full-text download, paid
  API use, paywall bypass, or marketing-material acceptance.

- `S2PCT07` adds `MOD-ADP-060`. It calibrates D2 source-domain qualification
  readiness across top-journal, engineering public-signal, and authoritative
  report shadow evidence. It validates upstream pass gates, complete domain
  type coverage, 30-date replay, 48h no-production shadow, forced-event
  propagation, queue explanations, and zero type-calibration spread while
  keeping D2 source-domain acceptance and all production flags false.

- `S2PDT01` adds `MOD-ADP-061`. It validates China C0 national authority
  metadata-only source taxonomy, official identity, document traceability, and
  no-production boundaries after D2 qualification readiness while keeping D3
  core source-domain acceptance and all production flags false.

- `S2PDT02` adds `MOD-ADP-062`. It validates China C1 central department
  metadata-only source maps, aliases, industry routes, board routes, official
  domains, and no-production boundaries after S2PDT01 C0 foundation while
  keeping D3 core source-domain acceptance, production flags, V7.1 CURRENT
  switching, and V7.2 mail/schema pre-run false.

- `S2PDT03` adds `MOD-ADP-063`. It validates China legal metadata status,
  version/effectivity relations, reprint/original-source guard, forced rescore
  and old-conclusion update, and no-production boundaries after S2PDT02 C1
  source map while keeping legal advice, D3 core source-domain acceptance,
  production flags, V7.1 CURRENT switching, and V7.2 mail/schema pre-run false.

- `S2PDT04` adds `MOD-ADP-064`. It validates China official D3 readiness
  evidence across 30-date replay, 2-day shadow, authority evidence, B2-B6 board
  routing, and metadata-only no-production boundaries after S2PDT01/S2PDT02/
  S2PDT03 while keeping D3 core source-domain acceptance, production flags,
  V7.1 CURRENT switching, V7.2 contract edits, and V7.2 mail/schema pre-run
  false.

- `S2PFT01` / legacy `S2P5T01` adds `MOD-ADP-065`. It validates mainland
  provincial-level template coverage, core local department roles, health
  tiers, official identity, and metadata-only no-production boundaries after
  S2PDT04 D3 readiness while keeping D3 full source-domain acceptance,
  Hong Kong/Macau, city coverage, special-zone discovery, production flags,
  V7.2 contract edits, and V7.2 mail/schema pre-run false.

- `S2PFT02` / legacy `S2P5T02` adds `MOD-ADP-066`. It validates Hong Kong
  and Macau as independent metadata-only jurisdiction profiles with separate
  legal-system states, government-structure models, language profiles,
  authority evidence, and explicit mainland-template reuse blockers while
  keeping D3 full source-domain acceptance, city coverage, special-zone
  discovery, production flags, V7.2 contract edits, and V7.2 mail/schema
  pre-run false.

- `S2PFT03` / legacy `S2P5T03` adds `MOD-ADP-067`. It validates first
  key-city metadata-only coverage across 24 required city IDs, aliases, local
  department roles, region groups, health tiers, and authority evidence while
  keeping D3 full source-domain acceptance, special-zone discovery, production
  flags, V7.2 contract edits, and V7.2 mail/schema pre-run false.

- `S2PFT04` / legacy `S2P5T04` adds `MOD-ADP-068`. It validates special-zone
  metadata-only discovery across 10 required zone IDs, supported zone types,
  authority roles, policy focus areas, parent-city mappings, health tiers,
  authority and dedupe gates while keeping D3 full source-domain acceptance,
  production flags, V7.2 contract edits, and V7.2 mail/schema pre-run false.

- `S2PFT05` / legacy `S2P5T05` adds `MOD-ADP-069`. It validates full D3
  governance qualification across C0-C4 component evidence, quota roles,
  quota balance, health balance, elimination explanation, fallback route,
  30-date replay, and metadata-only gates while keeping formal production
  inclusion, Stage 2 production acceptance, integrated production acceptance,
  production flags, V7.2 contract edits, and V7.2 mail/schema pre-run false.

- `S2PGT01` adds `MOD-ADP-070`. It defines a private EvidencePacket V2
  compatibility layer across D1-D4 source-domain reports, required packet
  fields, evidence-level labels, and old arXiv/D1 compatibility while keeping
  public schema migration, D4 adapter implementation, production queues, SMTP,
  scheduler, Release, V7.2 contract edits, and integrated production
  acceptance false.

- `S2PGT02` / legacy `S2P6T01` adds `MOD-ADP-071`. It defines a
  private cross-source identity and knowledge-graph relation spine across DOI,
  PMID, arXiv, Chinese document number, Federal Register document number, and
  CIK identifiers while keeping public schema migration, production queue
  mutation, source-domain production inclusion, SMTP, scheduler, Release,
  V7.2 contract edits, and integrated production acceptance false.

- `S2PGT03` adds `MOD-ADP-072`. It defines private D1-D4 to B1-B6
  source-to-reading-board routing evidence with reason codes, explanations,
  evidence refs, source-domain routing rules, and disabled public schema,
  queue, source production, SMTP, scheduler, Release, V7.2 contract, and
  integrated production flags.

- `S2PGT04` adds `MOD-ADP-073`. It defines private support/refute/frontier
  delta and signal-resonance evidence after S2PGT03 while keeping visible
  Email V1 frontstage changes, public schema migration, production queue
  mutation, source-domain production inclusion, SMTP, scheduler, Release,
  V7.2 contract edits, and integrated production acceptance false.

- `S2PGT05` / legacy `S2P6T02` adds `MOD-ADP-074`. It defines private
  cross-board percentile calibration, source balance, waiting credit,
  deterministic ordering, readable selected/queued/deferred reasons, and stable
  queue hashing while keeping production ranking changes, real queue mutation,
  public schema migration, source-domain production inclusion, Email V1
  frontstage changes, SMTP, scheduler, Release, V7.2 contract edits, and
  integrated production acceptance false.

- `S2PET04` / legacy `S2P4T04` adds `MOD-ADP-078`. It defines metadata-only D4 US technology policy and D4 qualification evidence for OSTP, BIS, FTC, FCC, CISA, CHIPS Program, 30-date replay, 2-day shadow, B4/B5/B6 board routing, and 35/15/30/20 budget explanations while keeping D4 production inclusion, source fetching, public schema, queue, SMTP, scheduler, Release, Email V1 runtime, V7.1/V7.2 contract edits, and integrated production acceptance false.
- `S2PET03` / legacy `S2P4T03` adds `MOD-ADP-077`. It defines metadata-only D4 US financial and macro source backbone evidence for SEC/EDGAR, Federal Reserve, Treasury, CFTC, OCC, FDIC, and CFPB with SEC forms, CIK, Accession, company/fund/asset relations, and no production, investment-advice, trading, or paid-market-data side effects.
- `S2PET02` / legacy `S2P4T02` adds `MOD-ADP-076`. It defines metadata-only D4 US legal backbone evidence for Federal Register, Regulations.gov, GovInfo, and Congress.gov with Docket/FR/CFR/bill/report/public-law/certified-text relations and no production side effects.
- `S2PET01` / legacy `S2P4T01` adds `MOD-ADP-075`. It defines metadata-only
  US-TA official technology-agency source foundation evidence across NSF,
  DARPA, DOE, NIH, NASA, NIST, USPTO, and FDA while keeping live fetches,
  production inclusion, public schema migration, SMTP, scheduler, Release,
  V7.1/V7.2 contract edits, and integrated production acceptance false.

## A. Model Overview

| Model ID | Name | Kind | Purpose | Status | Version | Implementation reference |
|---|---|---|---|---|---|---|
| MOD-ADP-001 | Phase 1 readiness and notification dry-run gate | deterministic rule engine | Classify local readiness and render non-secret email notifications | active | adp-foundation-v1 | `src/arxiv_daily_push/doctor.py`, `src/arxiv_daily_push/notifications.py` |
| MOD-ADP-004 | Generic data contract and RunRecord state gate | deterministic contract/state validator | Validate generic data boundaries and allowed run-state transitions without network or media work | active | adp-contracts-v1 | `src/arxiv_daily_push/contracts.py`, `src/arxiv_daily_push/state_machine.py` |
| MOD-ADP-005 | arXiv Atom source adapter | deterministic source adapter | Build bounded arXiv API URLs and map Atom entries into generic SourceItem records | active | adp-arxiv-adapter-v1 | `src/arxiv_daily_push/arxiv_adapter.py` |
| MOD-ADP-002 | 100-point arXiv selection score | deterministic scoring model | Select the daily learning item from eligible arXiv candidates | active | adp-ranking-v1 | `src/arxiv_daily_push/ranking.py` |
| MOD-ADP-003 | Claim Ledger publication gate | deterministic evidence gate | Block publication when key claims lack source locators or metadata is conflicted | active | adp-claim-gate-v1 | `src/arxiv_daily_push/evidence_gate.py` |
| MOD-ADP-006 | Evidence-linked Chinese lesson generator | deterministic lesson generator | Generate text-only Chinese Lesson JSON from supported Claim Ledger evidence with stable grouping and revision-sensitive identity | active | adp-lesson-v1 | `src/arxiv_daily_push/lesson.py` |
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
| MOD-ADP-017 | GitHub Release delivery boundary | deterministic release transport gate | Produce dry-run Release delivery evidence by default and create a GitHub Release only with explicit upload flag, configured target, deduplicated safe assets, and `gh` | active | adp-release-delivery-v1.1 | `src/arxiv_daily_push/release_delivery.py` |
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
| MOD-ADP-028 | Trial start evidence workflow validator | deterministic workflow contract validator | Validate the manual GitHub workflow that collects default-branch trial start evidence artifacts, cloud production refs, launch readiness, real MP4 evidence, and Release write permission on GitHub-hosted runner | active | adp-trial-start-workflow-v1 | `src/arxiv_daily_push/trial_start_workflow.py`, `src/arxiv_daily_push/cli.py`, `.github/workflows/arxiv-daily-push-trial-start.yml` |
| MOD-ADP-029 | Production launch readiness gate | deterministic launch-readiness validator | Block default-branch trial start dispatch until PR, workflow, runner, secrets, Release target, variables, refs, and confirmation are launch-ready | active | adp-production-launch-readiness-v1 | `src/arxiv_daily_push/production_launch.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-030 | Production refs readiness bundle | deterministic no-secret readiness validator | Generate a no-secret owner-fillable template, discover GitHub Actions metadata, run a GitHub-hosted provisioning audit, and review downloaded audit artifacts before launch readiness consumes refs | active | adp-production-refs-v1 | `src/arxiv_daily_push/production_refs.py`, `src/arxiv_daily_push/cli.py`, `.github/workflows/arxiv-daily-push-provisioning-audit.yml` |
| MOD-ADP-031 | Two-day simulation acceptance gate | deterministic simulation validator | Run the updated two-day Phase 11 simulation with mocked SMTP and Release boundaries while blocking network fetch, real side effects, secret reads, cache/media retention, and production acceptance claims | active | adp-two-day-simulation-v1 | `src/arxiv_daily_push/simulation.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-032 | All-arXiv Phase 12 scan queue delivery gate | deterministic source selection and delivery gate | Build all-arXiv daily input from bounded primary archive scans, persist ROI-ranked queue state, and require Release-hosted `.mp4` video artifact links before production email evidence can count | active | adp-all-arxiv-scan-v1 | `src/arxiv_daily_push/global_scan.py`, `src/arxiv_daily_push/scheduled_execution.py`, `.github/workflows/arxiv-daily-push-scheduled.yml` |
| MOD-ADP-033 | Phase 12 cloud production enablement gate | deterministic cloud workflow and media evidence validator | Verify GitHub-hosted workflow contracts, live all-arXiv 20-bucket dry-run readiness, real lightweight MP4 artifact rendering, and disabled production side effects before Release/SMTP manual tests | active | adp-phase12-cloud-enablement-v1 | `src/arxiv_daily_push/global_scan.py`, `src/arxiv_daily_push/video.py`, `.github/workflows/arxiv-daily-push-phase12-cloud-dry-run.yml` |
| MOD-ADP-034 | Phase 12 manual Release and SMTP delivery test gate | deterministic manual workflow contract | Prepare a default-branch-only workflow that creates one GitHub Release and sends one Gmail SMTP test email using the V2 decision-first frontstage and owner subject contract while keeping scheduled production disabled | active | adp-manual-delivery-test-v1.4 | `.github/workflows/arxiv-daily-push-manual-delivery-test.yml`, `src/arxiv_daily_push/scheduled_execution.py`, `src/arxiv_daily_push/global_scan.py`, `tests/test_manual_delivery_workflow.py` |
| MOD-ADP-035 | Review8 V4 owner controls and generated owner views | deterministic owner configuration validator and view generator | Validate the single owner-editable control file, preview no-side-effect impact, and generate four owner-readable files from machine facts | active | adp-owner-controls-v1 | `src/arxiv_daily_push/owner_controls.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-036 | Review8 Stage 1 SQLite document and event data model | deterministic local storage schema and migration gate | Create, inspect, validate, populate, search, and rollback the low-resource local SQLite/WAL/FTS5 document/event model | active | adp-sqlite-data-model-v1 | `src/arxiv_daily_push/storage.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-037 | Phase 12 email decision UI V2 | deterministic human-frontstage email renderer | Render a Chinese decision-first HTML email plus concise plain-text fallback from the all-arXiv daily package, with `YYYYMMDD -- Project Name -- arXiv Group -- Theme` subject and no foreground numeric score labels, while keeping backend ROI and Claim Ledger evidence out of the user-facing foreground | active | adp-email-decision-ui-v2 | `src/arxiv_daily_push/global_scan.py`, `src/arxiv_daily_push/lesson.py`, `src/arxiv_daily_push/smtp_delivery.py`, `src/arxiv_daily_push/video.py` |
| MOD-ADP-038 | Review8 Stage 1 source registry and arXiv connector contract | deterministic source registry and connector contract validator | Bind the source registry to owner controls, prove only SRC-ARXIV/arxiv.atom.v1 is active, and cap canaries at 10 metadata records without production side effects | active | adp-source-registry-contract-v1 | `src/arxiv_daily_push/source_registry.py`, `src/arxiv_daily_push/source_ingest.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-039 | Review8 Stage 1 scoring, queue, and content ledger contract | deterministic weighted scoring, queue ranking, and ledger renderer | Score explicit Stage 1 research signals, rank up to 10000 active items, enforce the 365-day window, record reason codes, and emit canonical CONTENT_LEDGER rows without production side effects | active | adp-stage1-scoring-queue-ledger-v1 | `src/arxiv_daily_push/stage1_queue.py`, `src/arxiv_daily_push/owner_controls.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-040 | Review8 Stage 1 B1/arXiv report and email text package | deterministic Chinese teaching report and email renderer | Render B1/arXiv teaching report/email previews with supported claim evidence, candidate queue summary, byte-verifiable artifact manifests, human-frontstage wording, and no production side effects | active | adp-stage1-b1-report-email-v1 | `src/arxiv_daily_push/stage1_b1_report.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-041 | Review8 Stage 1 local runtime recovery controls | deterministic local runtime and recovery gate | Provide low-resource tick, watchdog, backup, restore, runtime audit, and scheduler install/uninstall dry-run controls with explicit state/artifact paths and no production side effects | active | adp-stage1-local-runtime-recovery-v1 | `src/arxiv_daily_push/stage1_runtime.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-042 | Review8 Stage 1 migration package and transfer checklist | deterministic migration package and verification gate | Export and verify a low-resource Stage 1 migration package with file hashes, SQLite/runtime smoke evidence, restore instructions, and secret-name-only checklist without production side effects | active | adp-stage1-migration-package-v1 | `src/arxiv_daily_push/stage1_migration.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-043 | Review8 Stage 1 post-migration bootstrap gate | deterministic target-runner bootstrap validator | Verify Python, Git checkout, SSL, SQLite/FTS5, runtime smoke, GitHub-hosted workflow runner boundary, GitHub Actions env names, and secret-name-only readiness without production side effects | active | adp-stage1-post-migration-bootstrap-v1 | `src/arxiv_daily_push/stage1_bootstrap.py`, `src/arxiv_daily_push/cli.py`, `.github/workflows/arxiv-daily-push-stage1-bootstrap.yml` |
| MOD-ADP-044 | Review8 Stage 1 historical B1 preview batch | deterministic offline/input-backed B1 report and email preview evidence generator | Generate 30 independent historical B1/arXiv report/email preview packages from supported inputs or deterministic fixtures before live-day delivery while preserving no-production-side-effect and no-future-leakage gates | active | adp-stage1-historical-b1-previews-v1 | `src/arxiv_daily_push/stage1_historical_previews.py`, `src/arxiv_daily_push/stage1_b1_report.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-045 | S1P5T04 accelerated real arXiv acceptance evidence | deterministic accelerated acceptance evidence builder | Build Stage 1 acceptance readiness evidence from a passing live all-arXiv cloud dry-run, 30 real candidates, and controlled SMTP refs while preserving disabled production scheduling | active | adp-stage1-accelerated-acceptance-v1 | `src/arxiv_daily_push/stage1_accelerated_acceptance.py`, `src/arxiv_daily_push/trial.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-047 | Stage 2 bioRxiv/medRxiv preprint metadata ingest | deterministic source adapter | Fetch small public bioRxiv/medRxiv details API windows and map metadata into generic preprint SourceItem records without PDF, full-text, scheduler, SMTP, Release, video, or secret side effects | active | adp-stage2-preprint-ingest-v1 | `src/arxiv_daily_push/preprint_adapter.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-048 | S2P1T01 preprint source promotion gate | deterministic source promotion validator | Require passing bioRxiv and medRxiv SourceBatches plus 30-date terminal replay and 48-hour no-production shadow evidence before Stage 2 preprint source promotion can pass | active | adp-s2p1-preprint-source-promotion-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-049 | S2P1 preprint shadow daily path | deterministic shadow delivery pipeline | Build ROI-ranked bioRxiv/medRxiv shadow daily inputs, persist a separate preprint queue and JSONL ledger, and generate email previews without production inclusion or external side effects | active | adp-s2p1-preprint-shadow-daily-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/global_scan.py`, `src/arxiv_daily_push/lesson.py` |
| MOD-ADP-050 | S2P1T01 preprint replay and 48h shadow evidence | deterministic historical replay and shadow evidence builder | Run 30 historical bioRxiv/medRxiv preprint as-of dates through the no-send shadow daily path, persist local queue/ledger/report/email preview artifacts, build a 48h shadow aggregate, and feed the S2P1T01 promotion gate without claiming full Stage 2 production acceptance | active | adp-s2p1-preprint-replay-shadow-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-051 | S2PCT01 Nature/top-journal metadata ingest | deterministic source adapter | Fetch and map bounded official Nature RSS metadata into top-journal SourceItems while filtering non-main-journal article URLs and blocking PDF/full-text/paywall/production side effects | active | adp-stage2-top-journal-ingest-v1 | `src/arxiv_daily_push/top_journal_adapter.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-052 | S2PCT01 top-journal no-send shadow daily path | deterministic shadow source runner | Persist separate top-journal queue, JSONL ledger, report, and email preview artifacts from metadata-only SourceItems while keeping Stage 1 arXiv production, SMTP, Release, video, scheduler, and formal D2 inclusion disabled | active | adp-stage2-top-journal-shadow-daily-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/lesson.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-053 | S2PCT02 Science metadata ingest | deterministic source adapter | Fetch and map bounded official Science RSS metadata into top-journal SourceItems while classifying Research Article, Report, Review, and Perspective items and blocking PDF/full-text/paywall/production side effects | active | adp-stage2-top-journal-ingest-v1 | `src/arxiv_daily_push/top_journal_adapter.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-054 | S2PCT02 Science no-send shadow daily path | deterministic shadow source runner | Persist separate Science queue, JSONL ledger, report, and email preview artifacts from metadata-only SourceItems while keeping Stage 1 arXiv production, SMTP, Release, video, scheduler, and formal D2 inclusion disabled | active | adp-s2pct02-science-shadow-daily-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/lesson.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-055 | S2PCT03 Lancet metadata ingest | deterministic source adapter | Fetch and map bounded official Lancet RSS metadata into top-journal SourceItems while preserving Online First/current issue and PubMed DOI-query-ready metadata boundaries | active | adp-stage2-top-journal-ingest-v1 | `src/arxiv_daily_push/top_journal_adapter.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-056 | S2PCT03 Lancet no-send shadow daily path | deterministic shadow source runner | Persist separate Lancet queue, JSONL ledger, report, and email preview artifacts from metadata-only SourceItems while keeping Stage 1 arXiv production and formal D2 inclusion disabled | active | adp-s2pct03-lancet-shadow-daily-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/lesson.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-057 | S2PCT04 top-journal profile and publication relation shadow | deterministic metadata-only profile and relation model | Build a top-journal profile report across completed Nature, Science, and Lancet shadow batches with publication relation edges and correction/retraction forced updates while keeping all production flags false | active | adp-s2pct04-top-journal-profile-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-058 | S2PCT05 engineering public-signal shadow | deterministic metadata-only engineering signal model | Validate official code repositories, releases, model cards, benchmark results, and standards/specifications linked to known papers while keeping all production flags false | active | adp-s2pct05-engineering-signals-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-059 | S2PCT06 authoritative report source shadow | deterministic metadata-only authoritative report model | Validate research institution, lab, industry technical report, and product technical note metadata linked to known engineering signals while keeping all production flags false | active | adp-s2pct06-authoritative-reports-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-060 | S2PCT07 D2 source-domain qualification and cross-type calibration | deterministic source-domain qualification model | Calibrate top-journal, engineering signal, and authoritative report shadow evidence with replay, shadow, forced-event, queue explanation, and type calibration gates while keeping D2 acceptance and production flags false | active | adp-s2pct07-d2-source-domain-qualification-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-061 | S2PDT01 China C0 national authority source foundation | deterministic official-source foundation model | Validate law/regulation, NPC, State Council, gazette, and Supreme Court/Procuratorate metadata-only official-source evidence with traceability and no-production gates | active | adp-s2pdt01-china-c0-source-foundation-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-062 | S2PDT02 China C1 central department source map | deterministic official-department source-map model | Validate macro, science/technology, industry, finance, market-regulation, and key-industry department source maps with aliases, routes, official domains, and no-production gates | active | adp-s2pdt02-china-c1-department-source-map-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-063 | S2PDT03 China legal metadata relation shadow | deterministic legal-metadata relation shadow model | Validate legal status taxonomy, version/effectivity relations, reprint/original-source guard, forced rescore, old-conclusion update, and no-production gates | active | adp-s2pdt03-china-legal-metadata-relation-shadow-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-064 | S2PDT04 China D3 readiness review | deterministic D3 readiness review model | Validate 30-date replay, 2-day shadow, authority evidence, B2-B6 board routing, metadata-only gate, and disabled D3/production side-effect flags | active | adp-s2pdt04-china-d3-readiness-review-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-065 | S2PFT01 China provincial template coverage | deterministic provincial template coverage model | Validate 31 mainland provincial-level templates, locality types, core department roles, health tiers, official identity, and disabled full-D3/production side-effect flags | active | adp-s2pft01-china-provincial-template-coverage-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-066 | S2PFT02 Hong Kong and Macau independent profile | deterministic jurisdiction profile model | Validate Hong Kong and Macau jurisdiction profiles, legal system states, language profiles, government structures, authority evidence, metadata-only gates, and mainland-template reuse blockers | active | adp-s2pft02-hk-mo-independent-profile-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-067 | S2PFT03 key-city coverage | deterministic key-city metadata coverage model | Validate first 24 China key-city records, aliases, local department roles, region groups, health tiers, authority evidence, and disabled full-D3/production side-effect flags | active | adp-s2pft03-key-city-coverage-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-068 | S2PFT04 special-zone discovery | deterministic special-zone metadata discovery model | Validate 10 China special-zone records, zone types, authority roles, policy focus areas, parent-city mappings, health tiers, authority and dedupe gates, and disabled full-D3/production side-effect flags | active | adp-s2pft04-special-zone-discovery-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-069 | S2PFT05 D3 full governance qualification | deterministic D3 governance qualification model | Validate C0-C4 component evidence, quota roles, quota/health balance, elimination explanations, fallback routes, 30-date replay, metadata-only gates, and disabled production side-effect flags | active | adp-s2pft05-d3-full-governance-qualification-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-070 | S2PGT01 EvidencePacket V2 compatibility | deterministic evidence compatibility model | Validate D1-D4 source-domain report inputs, EvidencePacket V2 field shape, evidence-level labels, old arXiv compatibility, and disabled schema/production side-effect flags | active | adp-s2pgt01-evidence-packet-v2-compatibility-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-071 | S2PGT02 knowledge-graph relation spine | deterministic identity and relation model | Validate cross-source identifier normalization, duplicate canonical identity blocking, evidence-backed relation rows, idempotent graph hashing, and disabled schema/production side-effect flags | active | adp-s2pgt02-knowledge-graph-spine-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-072 | S2PGT03 source-board routing | deterministic routing evidence model | Validate D1-D4 source-domain coverage, B1-B6 board routing, reason codes, source-domain rules, explanations, evidence refs, and disabled schema/production side-effect flags | active | adp-s2pgt03-source-board-routing-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-073 | S2PGT04 delta resonance | deterministic delta and resonance model | Validate support/refute/frontier delta evidence, resonance groups, signal strength, explanations, evidence refs, and disabled schema/email-frontstage/production side-effect flags | active | adp-s2pgt04-delta-resonance-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-074 | S2PGT05 cross-board calibration | deterministic calibration and queue evidence model | Validate board-percentile calibration, D1-D4 source balance, waiting credit, selected/queued/deferred reasons, deterministic queue order, stable queue hashing, and disabled ranking/queue/schema/production side-effect flags | active | adp-s2pgt05-cross-board-calibration-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-075 | S2PET01 US-TA source foundation | deterministic US official technology agency source foundation model | Validate NSF, DARPA, DOE, NIH, NASA, NIST, USPTO, FDA agency coverage, signal taxonomy, official identity, traceability, metadata-only behavior, and disabled production side-effect flags | active | adp-s2pet01-us-ta-source-foundation-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-076 | S2PET02 US-LG legal backbone | deterministic US legal source relation backbone model | Validate Federal Register, Regulations.gov, GovInfo, Congress.gov coverage, legal document types, Docket/FR/CFR/bill/report/public-law/certified-text relations, traceability, metadata-only behavior, and disabled production side-effect flags | active | adp-s2pet02-us-lg-legal-backbone-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-077 | S2PET03 US-FM source backbone | deterministic US financial and macro source relation backbone model | Validate SEC/EDGAR, Fed, Treasury, CFTC, OCC, FDIC, CFPB coverage, SEC form classification, CIK and Accession identifiers, company/fund/asset relations, traceability, metadata-only behavior, and disabled production/trading side-effect flags | active | adp-s2pet03-us-fm-source-backbone-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |
| MOD-ADP-078 | S2PET04 US-TP D4 qualification | deterministic metadata-only US technology policy and D4 qualification model | Validate OSTP, BIS, FTC, FCC, CISA, CHIPS Program coverage, US-TP signal taxonomy, D4 30-date replay, 2-day shadow evidence, B4/B5/B6 board routing, 35/15/30/20 budget explanations, upstream S2PET01-S2PET03 readiness, traceability, and disabled production side-effect flags | active | adp-s2pet04-us-tp-d4-qualification-v1 | `src/arxiv_daily_push/stage2_sources.py`, `src/arxiv_daily_push/cli.py` |

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
| ASM-ADP-036 | Controlled manual Release and Gmail SMTP testing may perform real side effects only from an explicit default-branch workflow_dispatch and must not enable scheduled production. | `.github/workflows/arxiv-daily-push-manual-delivery-test.yml`, `tests/test_manual_delivery_workflow.py`, `docs/phase_records/PHASE_12_MANUAL_DELIVERY_TEST.md` | Phase 12 manual delivery test | active |
| ASM-ADP-037 | Review8 V4 owner control must be a single human-editable YAML file, while owner-visible Markdown/CSV views are generated artifacts and not second editable fact sources. | `config/owner_controls.yaml`, `src/arxiv_daily_push/owner_controls.py`, `tests/test_owner_controls.py`, `docs/owner/OWNER_CONSOLE.md` | Review8 Stage 1 owner controls | active |
| ASM-ADP-038 | Review8 Stage 1 Window A storage must remain local SQLite/WAL/FTS5 with deterministic migration and rollback, and must not perform bulk imports, PDF retention, production scheduler enablement, SMTP send, Release upload, or source expansion. | `src/arxiv_daily_push/storage.py`, `tests/test_storage.py`, `tests/test_cli.py`, `docs/pursuing_goal/BASELINE_LOCK.md` | Review8 Stage 1 SQLite data model | active |
| ASM-ADP-039 | Review8 Stage 1 Window A source registry must keep `config/owner_controls.yaml` as the single editable source list, enable only SRC-ARXIV with arxiv.atom.v1, cap canaries at 10, and block PDFs, bulk harvest, paid APIs, secrets, scheduler enablement, SMTP, Release upload, and production acceptance claims. | `src/arxiv_daily_push/source_registry.py`, `src/arxiv_daily_push/source_ingest.py`, `config/owner_controls.yaml`, `tests/test_source_registry.py`, `docs/pursuing_goal/BASELINE_LOCK.md` | Review8 Stage 1 connector contract | active |
| ASM-ADP-040 | Review8 Stage 1 scoring and queue behavior must use owner_controls.yaml as the active parameter source, keep at most 10000 active items, treat 365 days as an inclusive event-age boundary, retain deterministic reason codes for every non-active item, and emit canonical content ledger columns without claiming production replay output. | `src/arxiv_daily_push/stage1_queue.py`, `config/owner_controls.yaml`, `tests/test_stage1_queue.py`, `docs/pursuing_goal/BASELINE_LOCK.md` | Review8 Stage 1 scoring and ledger | active |
| ASM-ADP-041 | Review8 Stage 1 B1/arXiv text delivery must produce Chinese teaching report/email previews with supported claim evidence, candidate queue summary, human-frontstage wording, and no video, Release upload, real SMTP send, production scheduler enablement, or visible backend ROI/policy clutter. | `src/arxiv_daily_push/stage1_b1_report.py`, `tests/test_stage1_b1_report.py`, `docs/pursuing_goal/BASELINE_LOCK.md` | Review8 Stage 1 B1 report/email text | active |
| ASM-ADP-042 | Review8 Stage 1 local runtime recovery must provide explicit heartbeat/checkpoint, watchdog, backup, restore, runtime audit, and scheduler install/uninstall dry-run controls while keeping production scheduling, real SMTP, Release upload, video generation, and long-running local background work disabled. | `src/arxiv_daily_push/stage1_runtime.py`, `tests/test_stage1_runtime.py`, `docs/pursuing_goal/BASELINE_LOCK.md` | Review8 Stage 1 local runtime recovery | active |
| ASM-ADP-043 | Review8 Stage 1 migration packaging must produce a low-resource, hash-verifiable package and new-machine checklist while keeping production scheduling, real SMTP, Release upload, video generation, 30-day replay, and secret-value persistence disabled. | `src/arxiv_daily_push/stage1_migration.py`, `tests/test_stage1_migration.py`, `docs/runbooks/STAGE1_MIGRATION_RUNBOOK.md`, `docs/pursuing_goal/BASELINE_LOCK.md` | Review8 Stage 1 migration package | active |
| ASM-ADP-044 | Review8 Stage 1 post-migration bootstrap must prove an explicit target machine or GitHub-hosted cloud runner boundary before heavy historical previews or live-day evidence, and must not silently fall back to the user's Mac background runtime. | `src/arxiv_daily_push/stage1_bootstrap.py`, `.github/workflows/arxiv-daily-push-stage1-bootstrap.yml`, `tests/test_stage1_bootstrap.py`, `docs/pursuing_goal/BASELINE_LOCK.md` | Review8 Stage 1 post-migration bootstrap | active |
| ASM-ADP-045 | S2P1T01 preprint source promotion must keep bioRxiv and medRxiv disabled/zero-weight until both the 30-date terminal replay and 48-hour no-production shadow gate pass; no GitHub cloud scheduled production, SMTP send, Release upload, video generation, PDF download, full-text download, or Stage 1 arXiv production mutation is allowed. | `src/arxiv_daily_push/preprint_adapter.py`, `src/arxiv_daily_push/stage2_sources.py`, `config/owner_controls.yaml`, `tests/test_preprint_adapter.py`, `tests/test_stage2_sources.py`, `docs/phase_records/PHASE_S2P1T01_PREPRINT_SOURCE_PROMOTION.md` | Stage 2 source promotion | active |

## C. Functions and Formulas

The machine-readable source is `formula_registry.yaml`.

- FORM-ADP-001 classifies Phase 1 readiness as `blocked`, `warn`, or `pass`.
- FORM-ADP-002 renders dry-run email subject/body without secrets.
- FORM-ADP-005 validates generic contract fields, enum sets, and P0 evidence locator requirements.
- FORM-ADP-006 validates allowed `RunRecord` transitions and terminal states.
- FORM-ADP-007 maps arXiv Atom metadata into generic `SourceItem` records with bounded query parameters.
- FORM-ADP-003 applies the active 100-point ranking weights and evidence/metadata eligibility gate.
- FORM-ADP-004 applies the active Claim Ledger publication hard-block rules.
- FORM-ADP-008 generates and validates Lesson JSON only from supported Claim Ledger claim IDs, with stable `lesson_key` and immutable content/evidence/model-sensitive `lesson_revision_id`.
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
- FORM-ADP-019 emits GitHub Release delivery evidence in dry-run mode by default and blocks real Release creation unless explicit allow-upload, Release target, deduplicated safe assets, `gh`, and no-clobber checks pass.
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
- FORM-ADP-049 validates metadata-only preprint SourceBatches from the official bioRxiv/medRxiv details API with bounded canary size, DOI identity, abstract-level evidence, and no external side effects.
- FORM-ADP-050 validates the S2P1T01 preprint source promotion gate across source, 30-date replay, 48-hour shadow, no-production, no-SMTP, no-Release, and no-video requirements.
- FORM-ADP-051 validates the S2P1 shadow daily path across preprint candidate ranking, separate queue persistence, JSONL ledger persistence, email previews, and no mutation of the accepted Stage 1 arXiv local path.
- FORM-ADP-052 validates the S2P1 replay/shadow aggregate across 30 historical preprint dates, 48h shadow coverage, unique selected source/canonical IDs, no future leakage, no P0/P1 blockers, queue/ledger/email persistence, and no production side effects.
- FORM-ADP-053 validates Nature/top-journal metadata ingest across official RSS input, accepted `s41586` article URL identity, bounded canary size, SourceItem mapping, and no PDF/full-text/paywall/production side effects.
- FORM-ADP-054 validates the top-journal no-send shadow daily path across separate queue persistence, JSONL ledger persistence, email preview persistence, no Stage 1 arXiv mutation, and disabled SMTP/Release/video/scheduler/formal inclusion flags.
- FORM-ADP-055 validates Science metadata ingest across official RSS input, DOI identity, Research Article/Report/Review/Perspective classification, bounded canary size, SourceItem mapping, and no PDF/full-text/paywall/production side effects.
- FORM-ADP-056 validates the S2PCT02 Science no-send shadow daily path across separate queue persistence, JSONL ledger persistence, email preview persistence, no Stage 1 arXiv mutation, and disabled SMTP/Release/video/scheduler/D2 acceptance flags.
- FORM-ADP-057 validates S2PCT03 Lancet metadata ingest across official Online First/current RSS, medical article-type gates, DOI canonicalization, PubMed DOI-query-ready relation metadata, duplicate separation, and no PDF/full-text/paywall side effects.
- FORM-ADP-058 validates S2PCT03 Lancet no-send shadow daily across separate queue/ledger/email preview persistence, dry-run only execution, and disabled SMTP/Release/video/scheduler/PubMed harvesting/D2 acceptance flags.
- FORM-ADP-059 validates S2PCT04 top-journal profile/relation evidence across completed Nature/Science/Lancet batches, profile taxonomy coverage, publication relation edges, correction/retraction forced updates, and disabled production/D2 side-effect flags.
- FORM-ADP-060 validates S2PCT05 engineering public-signal evidence across required signal-type coverage, officiality, version traceability, paper relation, reproducibility state, and disabled production/D2 side-effect flags.
- FORM-ADP-061 validates S2PCT06 authoritative report source evidence across required report-type coverage, publisher type, publisher identity, interest relation, evidence level, engineering-signal traceability, canonical-paper traceability, and disabled production/D2 side-effect flags.
- FORM-ADP-062 validates S2PCT07 D2 source-domain qualification readiness across upstream pass evidence, complete domain type coverage, 30-date replay, 48h shadow, forced-event propagation, selected/queued/deferred queue explanations, zero type-calibration spread, and disabled production/D2 acceptance flags.
- FORM-ADP-063 validates S2PDT01 China C0 national authority metadata-only source foundation across upstream D2 qualification, required authority taxonomy, official identity, document traceability, metadata-only no-download boundaries, and disabled D3/production acceptance flags.
- FORM-ADP-064 validates S2PDT02 China C1 central department metadata-only source map across upstream C0 foundation, required sector coverage, official identity, aliases, industry/board routes, metadata-only no-download boundaries, disabled D3/production acceptance flags, and no V7.2 mail/schema pre-run.
- FORM-ADP-065 validates S2PDT03 China legal metadata relation shadow across upstream C1 source map, required legal statuses, required relation types, date confusion guard, reprint/original-source guard, forced rescore/old-conclusion update, metadata-only no-download boundaries, disabled legal-advice/D3/production acceptance flags, and no V7.2 mail/schema pre-run.
- FORM-ADP-066 validates S2PDT04 China D3 readiness review across upstream S2PDT01/S2PDT02/S2PDT03 pass gates, 30-date replay, 2-day shadow, authority evidence, B2-B6 board routing, metadata-only no-production boundaries, disabled D3/production acceptance flags, and no V7.2 contract/mail/schema pre-run.
- FORM-ADP-067 validates S2PFT01 China provincial template coverage across upstream S2PDT04 pass evidence, 31 mainland provincial IDs, locality type coverage, core local department roles, health tiers, official identity, metadata-only no-download boundaries, disabled D3 full acceptance flags, and no V7.2 contract/mail/schema pre-run.
- FORM-ADP-068 validates S2PFT02 Hong Kong and Macau independent profiles across upstream S2PFT01 pass evidence, required jurisdiction ids, zh_hant/en/pt language profiles, common-law and Portuguese-heritage civil-law legal states, independent government structures, authority evidence, metadata-only no-download boundaries, mainland-template reuse blockers, disabled D3 full acceptance flags, and no V7.2 contract/mail/schema pre-run.
- FORM-ADP-069 validates S2PFT03 key-city coverage across upstream S2PFT02 pass evidence, 24 required city ids, aliases, local department roles, allowed region groups, positive region weights, health tiers, authority evidence, metadata-only no-download boundaries, disabled D3 full acceptance flags, and no V7.2 contract/mail/schema pre-run.
- FORM-ADP-070 validates S2PFT04 special-zone discovery across upstream S2PFT03 pass evidence, 10 required zone ids, supported zone types, required authority roles, policy focus areas, parent-city mappings, health tiers, authority and dedupe gates, metadata-only no-download boundaries, disabled D3 full acceptance flags, and no V7.2 contract/mail/schema pre-run.
- FORM-ADP-071 validates S2PFT05 D3 full governance qualification across upstream S2PDT04 and S2PFT01-S2PFT04 pass evidence, C0-C4 components, quota roles, quota balance, health balance, elimination explanations, fallback routes, 30-date replay, metadata-only no-download boundaries, disabled formal production inclusion and integrated production acceptance flags, and no V7.2 contract/mail/schema pre-run.
- FORM-ADP-072 validates S2PGT01 EvidencePacket V2 compatibility across D1-D4 source-domain reports, required packet fields, required evidence-level labels, explicit D1/old arXiv compatibility, and disabled public schema migration, queue mutation, SMTP, scheduler, Release, V7.2 contract edit, and production acceptance flags.
- FORM-ADP-073 validates S2PGT02 private knowledge-graph relation spine across DOI, PMID, arXiv, Chinese document number, Federal Register document number, and CIK identifiers, duplicate canonical identity blocking, relation evidence, idempotent graph hashing, and disabled public schema, queue, SMTP, scheduler, Release, V7.2 contract edit, and production acceptance flags.
- FORM-ADP-074 validates S2PGT03 private source-board routing across D1-D4 source domains, B1-B3 primary boards, B4-B6 cross-cutting boards, route reasons, explanations, evidence refs, source-domain mapping rules, and disabled public schema, queue, source production inclusion, SMTP, scheduler, Release, V7.2 contract edit, and production acceptance flags.
- FORM-ADP-075 validates S2PGT04 private support/refute/frontier delta resonance across upstream routing, required delta types, supported/refuted evidence states, resonance groups, signal strength, explanations, evidence refs, and disabled public schema, queue, Email V1 frontstage, source production inclusion, SMTP, scheduler, Release, V7.2 contract edit, and production acceptance flags.
- FORM-ADP-076 validates S2PGT05 private cross-board calibration across upstream delta resonance, B1-B6 percentile calibration, D1-D4 source balance, waiting-credit bounds, selected/queued/deferred readable reasons, deterministic order, stable queue hash, and disabled public schema, production queue, production ranking, Email V1 frontstage, source production inclusion, SMTP, scheduler, Release, V7.2 contract edit, and production acceptance flags.
- FORM-ADP-080 validates S2PET04 US-TP D4 qualification across upstream S2PET01-S2PET03 readiness, required OSTP/BIS/FTC/FCC/CISA/CHIPS source systems, required technology policy signal types, official identity, traceability, 30-date replay, 2-day shadow with no SMTP, B4/B5/B6 board routes, 35/15/30/20 budget explanations, and disabled live-fetch, production, queue, SMTP, scheduler, Release, public schema, V7.1 CURRENT, V7.2 contract, Email V1 runtime, and integrated production acceptance flags.
- FORM-ADP-079 validates S2PET03 US-FM source backbone across upstream S2PET02 readiness, required source systems, SEC form types, finance/macro signal types, CIK and Accession identifiers, relation types, official identity, traceability, relation endpoint evidence, and disabled live-fetch, paid-market-data, investment-advice, trading, production, queue, SMTP, scheduler, Release, public schema, V7.1 CURRENT, V7.2 contract, and integrated production acceptance flags.
- FORM-ADP-078 validates S2PET02 US-LG legal backbone across upstream S2PET01 readiness, required source systems, document types, relation types, official identity, traceability, relation endpoint evidence, and disabled PDF/full-text, legal-advice, live-fetch, production, queue, SMTP, scheduler, Release, public schema, V7.1 CURRENT, V7.2 contract, and integrated production acceptance flags.
- FORM-ADP-077 validates S2PET01 US-TA source foundation across required US official technology agencies, signal types, official identity, traceability, metadata-only records, and disabled PDF/full-text, production, queue, SMTP, scheduler, Release, public schema, V7.1 CURRENT, V7.2 contract, and integrated production acceptance flags.
- FORM-ADP-034 validates the Phase 12 all-arXiv scan, ROI/learning-value ranking, candidate queue fallback, Release-hosted `.mp4` video artifact link, Chinese lesson email, candidate queue summary, and no legacy cs.AI-only production default.
- FORM-ADP-035 validates GitHub-hosted Phase 12 cloud dry-run, all primary archive coverage, MP4 artifact rendering, and disabled side-effect gates.
- FORM-ADP-036 validates controlled manual Release and Gmail SMTP test workflow gates, including the human-scannable Chinese email front-end, without enabling scheduled production.
- FORM-ADP-037 validates owner_controls schema, no-secret/no-paid-service policy, Window A resource caps, owner weight groups, no-side-effect impact preview, and generated owner views.
- FORM-ADP-038 validates the local SQLite/WAL/FTS5 schema migration, inspection, rollback, SourceItem persistence, FTS search readiness, and no-side-effect Stage 1 storage boundary.
- FORM-ADP-039 validates the V2 decision-first email frontstage: owner subject contract, Chinese plain text, responsive HTML, frontstage lesson payload, q-fin candidate filtering, optional MP4 link card, feedback actions, no foreground numeric score labels, and hidden backend ROI/Claim Ledger foreground details.
- FORM-ADP-040 validates the Stage 1 source registry and connector contract: single owner-controls fact source, only SRC-ARXIV active, arxiv.atom.v1 adapter, canary max 10, no PDF/bulk/paid/secret/production side effects, and offline fixture SourceItem validation.
- FORM-ADP-041 validates Stage 1 weighted research scoring, queue priority scoring, 10000 active-item cap, 365-day inclusive boundary, lifecycle reason codes, source-share cap behavior, stable tie ordering, and canonical content ledger rows.
- FORM-ADP-042 validates Stage 1 B1/arXiv report/email text delivery: supported daily input claims, 100% critical claim evidence coverage in audit fields, Chinese report/email previews, owner subject contract, candidate queue summary, validation before formal artifact writes, staged package-directory publish with byte-level artifact_files.sha256 values and content_hash preserved separately, hidden backend ROI/policy clutter, and no SMTP/Release/video/network side effects.
- FORM-ADP-043 validates Stage 1 local runtime recovery: explicit heartbeat/checkpoint tick, watchdog stale-state rejection, SHA256 SQLite backup/restore with explicit confirmation, production flag audit, and scheduler dry-run templates without applying OS scheduler changes.
- FORM-ADP-044 validates Stage 1 migration package export and verify: required source hash inventory, SQLite/runtime low-resource smoke, backup manifest, package file hash verification, secret-name-only checklist, and disabled production side effects.
- FORM-ADP-045 validates Stage 1 post-migration bootstrap: target runner support, GitHub-hosted workflow boundary, Python/Git/SSL/SQLite checks, runtime smoke, secret-name-only readiness, optional arXiv HTTPS probe, and disabled production side effects.
- FORM-ADP-046 validates S1-11 historical B1 previews: exactly 30 independent B1/arXiv report/email preview packages, supported JSON/JSONL/object or deterministic fixture input, unique dates/source/content/email identifiers, zero future-information leakage, 100% critical claim coverage, content ledger rows, optional five-file artifacts per preview, and disabled SMTP/Release/video/network/scheduler side effects.

## D. Parameters

The canonical parameter catalog is `parameter_registry.csv`.

- Active Phase 1 parameters: PARAM-ADP-001 through PARAM-ADP-008.
- Active Phase 2 contract/state parameters: PARAM-ADP-020 through PARAM-ADP-028.
- Active Phase 3 arXiv adapter parameters: PARAM-ADP-029 through PARAM-ADP-034.
- Active Phase 4 ranking weights: PARAM-ADP-009 through PARAM-ADP-016.
- Active Phase 5 evidence gate parameters: PARAM-ADP-017 through PARAM-ADP-018.
- Active Phase 6/S2PMT03 lesson parameters: PARAM-ADP-035 through PARAM-ADP-036 and PARAM-ADP-870 through PARAM-ADP-872.
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
- Active Phase 11 Release delivery parameters: PARAM-ADP-086 through PARAM-ADP-091 plus PARAM-ADP-185.
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
- Active Phase 12 cloud production enablement parameters: PARAM-ADP-177 through PARAM-ADP-180.
- Active Phase 12 manual delivery test parameters: PARAM-ADP-181 through PARAM-ADP-184 plus PARAM-ADP-186 and PARAM-ADP-267.
- Active Review8 Stage 1 owner controls parameters: PARAM-ADP-187 through PARAM-ADP-266.
- Active Review8 Stage 1 SQLite storage parameters: PARAM-ADP-268 through PARAM-ADP-275.
- Active Phase 12 email decision UI V2 parameters: PARAM-ADP-276 through PARAM-ADP-279.
- Active Review8 Stage 1 source registry contract parameters: PARAM-ADP-280 through PARAM-ADP-286.
- Active Review8 Stage 1 scoring queue ledger parameters: PARAM-ADP-287 through PARAM-ADP-309.
- Active Review8 Stage 1 B1 report/email text parameters: PARAM-ADP-310 through PARAM-ADP-315.
- Active Review8 Stage 1 local runtime recovery parameters: PARAM-ADP-316 through PARAM-ADP-325.
- Active Review8 Stage 1 migration package parameters: PARAM-ADP-326 through PARAM-ADP-331.
- Active Review8 Stage 1 post-migration bootstrap parameters: PARAM-ADP-332 through PARAM-ADP-339.
- Active Review8 Stage 1 historical B1 preview parameters: PARAM-ADP-340 through PARAM-ADP-348.
- Active S1P5T04 accelerated acceptance parameters: PARAM-ADP-349 through PARAM-ADP-351.
- Active S2P1T01 preprint source promotion parameters: PARAM-ADP-360 through PARAM-ADP-371.
- Active S2P1T01 replay/shadow evidence parameters: PARAM-ADP-372 through PARAM-ADP-376.
- Active S2PCT01 Nature/top-journal shadow parameters: PARAM-ADP-377 through PARAM-ADP-381.
- Active S2PCT02 Science/top-journal shadow parameters: PARAM-ADP-382 through PARAM-ADP-386.
- Active S2PCT03 Lancet/top-journal medical shadow parameters: PARAM-ADP-387 through PARAM-ADP-393, with PARAM-ADP-379 updated to `nature;science;lancet`.
- Active S2PCT04 top-journal profile/relation parameters: PARAM-ADP-394 through PARAM-ADP-399.
- Active S2PCT05 engineering public-signal parameters: PARAM-ADP-400 through PARAM-ADP-406.
- Active S2PCT06 authoritative report source parameters: PARAM-ADP-407 through PARAM-ADP-415.
- Active S2PCT07 D2 qualification parameters: PARAM-ADP-416 through PARAM-ADP-423.
- Active S2PDT01 China C0 source parameters: PARAM-ADP-424 through PARAM-ADP-431.
- Active S2PDT02 China C1 department source-map parameters: PARAM-ADP-432 through PARAM-ADP-439.
- Active S2PDT03 China legal metadata relation parameters: PARAM-ADP-440 through PARAM-ADP-449.
- Active S2PDT04 China D3 readiness parameters: PARAM-ADP-450 through PARAM-ADP-458.
- Active S2PFT01 China provincial template parameters: PARAM-ADP-459 through PARAM-ADP-468.
- Active S2PFT02 Hong Kong and Macau independent profile parameters: PARAM-ADP-469 through PARAM-ADP-478.
- Active S2PFT03 key-city coverage parameters: PARAM-ADP-479 through PARAM-ADP-487.
- Active S2PFT04 special-zone discovery parameters: PARAM-ADP-488 through PARAM-ADP-497.
- Active S2PFT05 D3 full governance qualification parameters: PARAM-ADP-498 through PARAM-ADP-507.
- Active S2PGT01 EvidencePacket V2 compatibility parameters: PARAM-ADP-508 through PARAM-ADP-515.
- Active S2PGT02 knowledge-graph relation spine parameters: PARAM-ADP-516 through PARAM-ADP-524.
- Active S2PGT03 source-board routing parameters: PARAM-ADP-525 through PARAM-ADP-535.
- Active S2PGT04 delta resonance parameters: PARAM-ADP-536 through PARAM-ADP-544.
- Active S2PGT05 cross-board calibration parameters: PARAM-ADP-545 through PARAM-ADP-559.
- Active S2PET01 US-TA source foundation parameters: PARAM-ADP-560 through PARAM-ADP-568.
- Active S2PET02 US-LG legal backbone parameters: PARAM-ADP-569 through PARAM-ADP-579.
- Active S2PET03 US-FM source backbone parameters: PARAM-ADP-580 through PARAM-ADP-592.
- Active S2PET04 US-TP D4 qualification parameters: PARAM-ADP-593 through PARAM-ADP-607.
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
`confirm_production_trial=true`, targets GitHub-hosted `ubuntu-latest`,
runs `adp preflight-production` before project tests, installs/checks `ffmpeg`, uploads the preflight JSON
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

The Review8 V4 owner controls model treats `config/owner_controls.yaml` as the
only owner-editable control surface for Stage 1 Window A. The validator checks
required sections, no-paid-service and no-production flags, Window A resource
caps, no token-like values, canonical generated owner view paths, and every
declared source, board, scoring, queue, ranking, ROI, and attention-budget
weight group. The impact preview is intentionally no-side-effect and reports
ranking or queue deltas as not computed until S1-06 replay data exists. The
four `docs/owner/` files are generated views, not additional editable facts.

The S1-04 SQLite data model creates a local-only document and event storage
contract before later source connector, queue, ledger, runtime recovery, and
migration work. Migration requires SQLite FTS5, sets WAL mode, creates the
schema_migrations table, 18 object tables, and `document_fts`, then returns a
machine-readable pass/blocked report. `store_source_item` accepts only a valid
generic `SourceItem`, writes raw/canonical/version/FTS rows idempotently, and
does not fetch sources, download PDFs, send mail, upload Releases, enable
scheduling, or claim production acceptance. Rollback supports target version 0
only and drops the Stage 1 schema.

The S1-05 source registry model uses `config/owner_controls.yaml` as the only
editable source registry. `source_registry.py` renders a machine report from
that config, validates the arXiv connector contract, and returns blocked status
for any non-arXiv enabled source, wrong adapter, canary limit drift, fixture
parse failure, production flag, or prohibited side effect. The model is a
boundary and evidence contract; it does not add B1 non-arXiv ingestion, run a
network canary during local validation, download PDFs, send mail, upload
Releases, install a scheduler, or claim production acceptance.

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
- Trial bootstrap without manual confirmation, GitHub-hosted runner targeting, preflight-first ordering, artifact upload, GitHub secret-name mapping, or runbook evidence path -> bootstrap validation blocked.
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
- Scheduled daily execution with dry-run SMTP or missing Stage 1 text artifacts -> scheduled execution degraded and not production evidence.
- Scheduled production evidence ready without daily run, text artifact, email, and resource refs -> validation error.
- Daily input builder source batch blocked -> daily input report blocked.
- Daily input builder missing Atom summary -> daily input report blocked.
- Daily input builder selected candidate recently used -> daily input report blocked.
- Daily input builder pass -> daily input contains SourceItem, supported claims, date, run_id, and selection audit.
- All-arXiv scan plan missing a primary archive bucket or collapsing to `cat:cs.AI` -> Phase 12 daily input blocked.
- All-arXiv daily selection chooses one new high-value candidate first, otherwise consumes a queued high-value candidate, otherwise blocks if no candidate meets the minimum threshold.
- Phase 12 candidate queue persists high-value unselected candidates as a small JSON artifact and never stores PDFs, media, model weights, or secrets.
- Scheduled production email cannot count as production-ready unless it includes Chinese lesson content, candidate queue summary, HTML/plain text bodies, and a Stage 1 text artifact ref; video/Release links are not required for Stage 1.
- Production refs input without cloud runner evidence, missing SMTP secret names, missing workflow variables, or secret-like input -> refs report blocked or redacted discovery error.
- Phase 12 cloud dry-run without 20 verified primary archive buckets, sample daily input, or Stage 1 text artifacts -> production enablement blocked.
- Owner controls with production enabled, paid service allowed, token-like value, wrong owner view list, Window A resource overrun, or weight total drift -> owner validation blocked.
- Owner impact preview can report S1-06 deterministic fixture queue readiness but cannot claim production replay or ranking impact until real replay data exists.
- `docs/owner/*` files are regenerated from `config/owner_controls.yaml`; manual edits are drift, not facts.
- SQLite storage migration without FTS5 support, WAL journal mode, schema version 1, all 18 object tables, or `document_fts` -> storage report blocked.
- SQLite storage inspect on a missing database file -> blocked report with `blocking_reasons`.
- SQLite storage rollback with target version other than 0 -> `StorageError`.
- SourceItem storage before migration or with invalid generic SourceItem data -> `StorageError`.
- SourceItem storage with the same content -> idempotent raw/canonical/version/FTS rows rather than duplicate document versions.
- Source registry with any enabled source other than `SRC-ARXIV` -> blocked report.
- Source registry with `SRC-ARXIV` not bound to B1, `official_atom_api`, or `arxiv.atom.v1` -> blocked report.
- Source registry with `SOURCE_INGEST_MAX_RESULTS` or canary max above 10 -> blocked report.
- Source registry with PDF download, bulk harvest, paid API, secret requirement, production enabled, or production acceptance claimed -> blocked report.
- Source registry fixture Atom parse or SourceItem validation failure -> blocked report.
- Production pass with any missing requirement -> acceptance validation error.

## G. Validation

Current focused validation:

- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`
- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_owner_controls.py -q`
- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_storage.py arxiv-daily-push/tests/test_cli.py -q`
- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage1_queue.py arxiv-daily-push/tests/test_owner_controls.py -q`
- `adp stage1-queue --input <fixture.json> --as-of-date 2026-06-22 --generated-at 2026-06-22T21:00:00+10:00 --json`
- `adp owner validate`
- `adp owner preview-impact --days 30`
- `adp owner render-docs --write`
- `python3 -m json.tool arxiv-daily-push/schemas/*.schema.json`
- `python3 scripts/validate_project_governance.py --project arxiv-daily-push`
- `python3 scripts/validate_project_governance.py --changed-only --enforce-sync`
- `git diff --check`

Uncovered planned scenarios:

- arXiv network ingest idempotency.
- Claim extraction from paper text/PDF.
- TTS/video sample gates.
- Live 30-day operational trial evidence.
- GitHub-hosted cloud dry-run workflow run and real email transport health.
- Actual production preflight pass on GitHub-hosted Actions with SMTP and Stage 1 text artifact dependencies available.
- Actual 30-day trial start and scheduled daily run execution on the default branch.
- Local Python HTTPS certificate validation for `https://export.arxiv.org/api/query` currently blocks live source ingest on this machine.
- Real SMTP delivery against the provisioned production SMTP server and archived message evidence.
- Actual weekly/monthly replay execution archived under a durable GitHub Actions artifact ref.
- Actual recovery drill execution archived under a durable GitHub Actions artifact ref.
- Actual 30-day resource telemetry evidence archived under a durable GitHub Actions artifact ref.

## S1-12 Text-Only Production Enablement Delta

- Stage 1 production readiness now requires all-arXiv source selection, candidate queue persistence, Chinese teaching email, HTML/plain text delivery, Gmail SMTP evidence, and GitHub Actions text artifacts.
- Video generation, MP4 links, and GitHub Release upload are not Stage 1 production-readiness gates. Release delivery remains a legacy/optional transport module and must not be used to claim S1-12 completion.
- `ARXIV_PRODUCTION_ACCEPTED` is now evidenced by strict S1P5T03-R PR #94 run `28027759062` artifact `7821452823`; PR #82 artifact `7818287996` remains one-time live cloud-chain evidence. Production schedule enablement remains controlled by GitHub repository variables/secrets and fail-closed workflow gates.

## S2PIT01 Chinese User Center Evidence

- `MOD-ADP-079` / `FORM-ADP-081` define local owner-experience evidence for `S2PIT01`.
- The only editable fact source is `config/owner_controls.yaml`; `docs/owner/00_用户中心/*` and generated owner views are read-only navigation or render artifacts.
- Passing S2PIT01 requires owner_controls validation, read-only storage inspect status, four control domains, two-click reachability, compatible config compilation, and all production/schema/email side-effect flags false.
- S2PIT01 does not claim `OWNER_EXPERIENCE_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source-adapter change, or Email V1 runtime change.

## S2PHT05 Content Quality Gate Evidence

- `MOD-ADP-086` / `FORM-ADP-088` define local semantic content quality gate evidence for `S2PHT05`.
- Passing S2PHT05 requires S2PHT01-S2PHT04 dependency receipts with V7.2 revalidation, at least 10 gold items, all required semantic dimension scores >= 4.0, supported or partially supported claim entailment, quote/source locations, template similarity <= 0.35, counterevidence, boundary conditions, personal action evidence, Stage 1 arXiv/evidence/email regression checks, at least two manual review samples, deterministic quality hashing, and all production/schema/email side-effect flags false.
- S2PHT05 does not change mail production code and does not claim `OWNER_EXPERIENCE_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source-adapter change, ranking change, or Email V1 runtime change.
## S2PKT01 Mail Contract Evidence

- `MOD-ADP-089` / `FORM-ADP-091` define local M1-M4 `EMAIL_LEARNING_V1` mail contract readiness evidence.
- Passing S2PKT01 requires S2PHT05/S2PIT04/S2PJT03 readiness, M1-M4 shared contract identity, template version 1.0.0, board differentiation, B4/B5/B6 cross-cutting boards, three reading layers, evidence labels, feedback actions, allowed no-send statuses, deterministic hashes, and all production/schema/email side-effect flags false.
- S2PKT01 does not change runtime mail templates/frontstage and does not claim `OWNER_EXPERIENCE_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source-adapter change, ranking change, or Email V1 runtime change.

## S2PKT02 M1 Mail Evidence

- `MOD-ADP-090` / `FORM-ADP-092` define local M1 science/theory frontier mail evidence built on the S2PKT01 `EMAIL_LEARNING_V1` contract.
- Passing S2PKT02 requires S2PKT01/S2PHT05/S2PIT04/S2PJT03 readiness, M1/B1 scope, B4/B5/B6 cross-cutting boards, scientific mechanism, evidence chain, counterevidence, personal value, action path, ledger-traceable content, S2PJT03-traceable 15m/2h action windows, deterministic M1 hash, and all production/schema/email side-effect flags false.
- S2PKT02 does not change runtime mail templates/frontstage and does not claim `OWNER_EXPERIENCE_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source-adapter change, ranking change, or Email V1 runtime change.

## S2PKT03 M2 Mail Evidence

- `MOD-ADP-091` / `FORM-ADP-093` define local M2 engineering, product, and industry frontier mail evidence built on the S2PKT01 `EMAIL_LEARNING_V1` contract.
- Passing S2PKT03 requires S2PKT01/S2PHT05/S2PIT04/S2PJT03 readiness, M2/B2 scope, B4/B5/B6 cross-cutting boards, engineering usability, reproducibility, product/industry value, limitations, action path, ledger-traceable content, S2PJT03-traceable 2h/7d action windows, deterministic M2 hash, and all production/schema/email side-effect flags false.
- S2PKT03 does not change runtime mail templates/frontstage and does not claim `OWNER_EXPERIENCE_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source-adapter change, ranking change, or Email V1 runtime change.

## S2PKT04 M3 Mail Evidence

- `MOD-ADP-092` / `FORM-ADP-094` define local M3 policy, capital, and geopolitical frontier mail evidence built on the S2PKT01 `EMAIL_LEARNING_V1` contract.
- Passing S2PKT04 requires S2PKT01/S2PHT05/S2PIT04/S2PJT03 readiness, M3/B3 scope, B4/B5/B6 cross-cutting boards, legal status, capital impact, geopolitical context, personal impact, action path, ledger-traceable content, S2PJT03-traceable 2h/30d action windows, deterministic M3 hash, and all production/schema/email side-effect flags false.
- S2PKT04 does not change runtime mail templates/frontstage and does not claim `OWNER_EXPERIENCE_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source-adapter change, ranking change, or Email V1 runtime change.

## S2PKT05 M4 Mail Orchestration Evidence

- `MOD-ADP-093` / `FORM-ADP-095` define local M4 cross-board 3+1 mail orchestration evidence built on the S2PKT01 `EMAIL_LEARNING_V1` contract and terminal S2PKT02/S2PKT03/S2PKT04 local reports.
- Passing S2PKT05 requires M4/B1-B6 scope, B4/B5/B6 cross-cutting boards, M1/M2/M3 pass-ready terminal inputs with matching hashes, Sydney 07:30/11:30/17:00/21:30 staggered windows, a cycle watermark waiting for M1/M2/M3, duplicate_count 0, silent_drop_count 0, legacy five-mail inactive state, cross_source_resonance/contradictions/era_mainline/personal_action_mix/review_reminders sections, S2PJT03-traceable actions, S2PJT02 due-queue-traceable review reminders, deterministic M4 hash, and all production/schema/email side-effect flags false.
- S2PKT05 does not change runtime mail templates/frontstage and does not claim `OWNER_EXPERIENCE_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source-adapter change, ranking change, production waterline/outbox readiness, or Email V1 runtime change.

## S2PMT01 Security And Evidence Boundary

- `MOD-ADP-094` / `FORM-ADP-096` define local security and evidence-boundary gates for S2PMT01.
- Passing S2PMT01 local validation requires source content to be labeled `UNTRUSTED_DATA`, safe public URL rendering, typed frontstage fact/inference/hypothesis/action statements, claim/evidence bindings for facts, premise/reasoning/confidence bindings for inferences, zero critical claim blocking, local supply-chain baseline controls, and no tool execution, secret access, email send, repository write, or production side effects.
- S2PMT01 local evidence does not install workflow enforcement, send email, enable scheduler, upload Release assets, migrate DB/public schema, change V7.1/V7.2 contracts, or claim inherited P0/P1 closure before independent review.

## S2PMT02 Atomic Storage And Recovery

- `MOD-ADP-095` / `FORM-ADP-097` define local atomic storage and recovery hardening evidence for S2PMT02.
- Passing S2PMT02 local validation requires staged writes with atomic replace, manifest hash verification, tamper detection, explicit restore drill into a caller-provided drill directory, staging cleanup, and all production restore/SMTP/scheduler/Release/schema/queue/DB side-effect flags false.
- S2PMT02 local evidence does not execute production restore, install scheduler, send email, upload Release assets, migrate DB/public schema, mutate queues, change source adapters, change V7.1/V7.2 contracts, or claim integrated production acceptance.

## S2PMT03 Lease Fencing And Transactional Outbox

- `MOD-ADP-096` / `FORM-ADP-098` define local lease fencing, state concurrency, transactional outbox, SMTP accept crash-window, and M4 watermark evidence for S2PMT03.
- Passing S2PMT03 local validation requires row_version compare-and-swap, unexpired foreign lease blocking, fencing-token stale writer rejection, state-history consistency, idempotent outbox Message-ID by content revision, SMTP accept crash-window blocking without durable provider refs, cycle-scoped M4 watermark readiness/degradation, exactly_once_claimed false, and all production side-effect flags false.
- S2PMT03 local evidence does not send SMTP, install scheduler, upload Release assets, run production restore, migrate DB/public schema, mutate production queues, change source adapters or ranking, change V7.1/V7.2 contracts, or claim integrated production acceptance.

## S2PMT04 Lifecycle And Cache Cleanup

- `MOD-ADP-097` / `FORM-ADP-099` define local lifecycle and cache-cleanup hardening evidence for S2PMT04.
- Passing S2PMT04 local validation requires disabled automatic wake dry-run, lifecycle drain/checkpoint/cleanup sequence, lifecycle interrupt matrix coverage for `SIGTERM` and `SIGINT`, startup reconciliation, startup convergence/count conservation, durable shutdown receipt, observable transaction completion receipts, low-disk cache degradation, safe cache cleanup, parseable disabled launchd plist generation, and all production side-effect flags false.
- Low-disk cache degradation must block new downloads and rebuildable cache writes, keep cleanup dry-run, preserve durable evidence, avoid delete application, and avoid queue mutation.
- S2PMT04 local evidence does not install or enable a scheduler, send SMTP, upload Release assets, run production restore, migrate DB/public schema, mutate production queues, change source adapters or ranking, change V7.1/V7.2 contracts, or claim integrated production acceptance.

## S2PMT05 Stress Fault Time And E2E

- `MOD-ADP-098` / `FORM-ADP-100` define local pressure, fault, time, and E2E hardening evidence for S2PMT05.
- Passing S2PMT05 local validation requires deterministic load/stress/spike profiles, accelerated local 24h soak coverage, multi-actor duplicate-trigger race protection with `mail_key`/`lease_owner`/`fencing_token` receipts and reason-coded blocked attempts, SMTP accepted-before-local-commit crash-window handling with outbox claim before SMTP acceptance, `ACCEPTED_PENDING_COMMIT`, stable idempotent `message_id`, provider accept ref finalization, blocked unsafe resend, and no real SMTP side effect, ENOSPC/read-only/SQLITE_BUSY/corrupt-artifact fault injection, Australia/Sydney DST and clock-skew policy, 35-day 3+1/weekly/monthly/review/action/ROI count conservation with an auditable run bundle and reachable review/action/ROI links, semantic/evidence-bound non-template result validity, 2x/5x priority-aware backpressure with high-priority SLO and low-priority delay/drop reason codes, deterministic isolation, required audit finding coverage, and all production side-effect flags false.
- B-007 duplicate-trigger evidence requires github_schedule/local_launchd/manual_retry/restart_catchup actor coverage, M1-M4 x 100 attempts, exactly one active revision per product and mail key, `MAIL_KEY_ALREADY_CLAIMED` reason codes for blocked duplicate attempts, active plus blocked count conservation, lease/fencing receipts, and no scheduler side effects.
- B-008 SMTP crash-window evidence requires outbox claim before SMTP acceptance, explicit `ACCEPTED_PENDING_COMMIT`, stable same-revision `message_id`, changed `message_id` when content revision changes, blocked resend without durable `provider_accept_ref`, local finalization with `smtp-accept://...` provider ref, and no real SMTP side effects.
- B-012 E2E evidence requires a local audit bundle with section artifacts, artifact index, link graph, deterministic bundle hash, daily 3+1 mail count conservation, weekly/monthly report coverage, and review/action/ROI link reachability.
- B-013 result validity requires semantic alignment scores, claim-ledger refs, evidence refs, specific mechanism/action summaries, non-template output variance, and unsupported P0 claim negative controls that block publication.
- B-014 backpressure requires 2x and 5x peak profiles, high-priority work within the configured SLO, low-priority delay/drop reason codes, durable evidence preservation, and rebuildable-only shedding.
- S2PMT05 local evidence does not execute a real 24h wall-clock production soak, install or enable a scheduler, send SMTP, upload Release assets, run production restore, migrate DB/public schema, mutate production queues, change source adapters or ranking, change V7.1/V7.2 contracts, close inherited P0/P1 before S2PMT07, or claim integrated production acceptance.

## S2PMT06 Owner UX And Safe Controls

- `MOD-ADP-099` / `FORM-ADP-101` define local Chinese owner UX, interaction feedback, navigation, safe controls, traceability, and accessibility evidence for S2PMT06.
- Passing S2PMT06 local validation requires a complete first-screen owner status, fixed top/bottom Chinese navigation, breadcrumbs, related links, source-to-ROI traceability, not-run/loading/no-update/partial-success/degraded/failed/stale status feedback, recoverable error cards, preview-to-rollback safe config changes, append-only revision ledger, queue search/filter/sort/export/drilldown, safe manual retry/cancel/requeue/skip/regenerate previews, visible feedback loops, accessibility/mail-client compatibility, C-001 through C-015 coverage, and all production side-effect flags false.
- S2PMT06 local evidence does not enable SMTP, install scheduler, upload Release assets, run production restore, migrate DB/public schema, mutate production queues, change source adapters or ranking, change CURRENT or V7.1/V7.2 contracts, close inherited P0/P1 before S2PMT07, or claim integrated production acceptance.

## S2PMT07 Final Gate Precheck

- `MOD-ADP-100` / `FORM-ADP-102` define the fail-closed final production gate precheck for S2PMT07.
- Passing S2PMT07 is not claimed by this run. The current precheck remains blocked because reviewer independence is not proven, inherited V7.1 P0=8 and P1=37 are open, S2PLT04 completion is missing, the final acceptance bundle is missing, the independent signoff is missing, and final required command execution by an independent reviewer is not proven.
- S2PMT07 precheck does not enable SMTP, install scheduler, upload Release assets, run production restore, migrate DB/public schema, mutate production queues, change source adapters or ranking, change CURRENT or V7.1/V7.2 contracts, close inherited P0/P1, enable DAILY_OPERATION, or claim integrated production acceptance.

## S2PLT01 Full Replay Entry Precheck

- `MOD-ADP-101` / `FORM-ADP-103` define the fail-closed entry precheck for S2PLT01 full-system 30 independent historical-day replay.
- The S2PLT01 replay evidence gate can now consume provided evidence records through a deterministic no-production payload contract with payload metadata, evidence mode, evidence refs, payload hash, 30 replay days, 120 M1-M4 `EMAIL_LEARNING_V1` no-send mail previews, and D1-D4 terminal source states. Passing S2PLT01 is not claimed by this run because the actual replay payload was not executed here and inherited V7.1 P0=8 and P1=37 remain open.
- S2PLT01 precheck does not execute replay, accept S2PLT01, complete S2PLT04, enable SMTP, install scheduler, upload Release assets, run production restore, migrate DB/public schema, mutate production queues, change source adapters or ranking, change CURRENT or V7.1/V7.2 contracts, close inherited P0/P1, enable DAILY_OPERATION, or claim integrated production acceptance.

## S2PBT05 D1 Qualification Receipt

- `MOD-ADP-102` / `FORM-ADP-104` define the D1 source-domain qualification receipt that turns completed `S2PBT01` / legacy `S2P1T01` bioRxiv and medRxiv evidence into a terminal D1 dependency for S2PLT01.
- The receipt relies on existing real no-send replay and shadow evidence: 30/30 historical dates, 30 real preprint source IDs, duplicate selected/canonical count 0, future leakage 0, queue continuity breaks 0, P0/P1 0, and shadow_hours 720.0.
- S2PBT05 does not enable formal bioRxiv/medRxiv production inclusion, live source fetch, SMTP, scheduler, Release, DB/public schema migration, production queue mutation, source adapter/ranking change, CURRENT or V7.1/V7.2 contract-file edits, DAILY_OPERATION, or integrated production acceptance.

## S2PLT02 Live 2D Precheck

- `MOD-ADP-104` / `FORM-ADP-106` define the fail-closed S2PLT02 two-day live-run readiness precheck.
- Passing S2PLT02 is not claimed by this run. The current precheck remains blocked because S2PLT01 acceptance is not proven, two consecutive real natural days are not proven, 8 real M1-M4 emails are not proven, real scheduler and SMTP proof are missing, M4 watermark correctness is not proven, and inherited V7.1 P0=8 and P1=37 remain open.
- S2PLT02 precheck does not start live operation, accept S2PLT02, enable SMTP, install scheduler, upload Release assets, execute production restore, migrate DB/public schema, mutate production queues, change source adapters or ranking, change CURRENT or V7.1/V7.2 contracts, close inherited P0/P1, enable DAILY_OPERATION, or claim integrated production acceptance.

## S2PLT04 Integration Candidate Precheck

- `MOD-ADP-103` / `FORM-ADP-105` define the fail-closed S2PLT04 integration candidate precheck.
- Passing S2PLT04 is not claimed by this run. The current precheck remains blocked because S2PLT01 acceptance is not proven, S2PLT02/S2PLT03 authoritative completion evidence is missing, the final acceptance bundle is missing, inherited V7.1 P0=8 and P1=37 remain open, and embedded S2PMT07 precheck is blocked.
- S2PLT04 precheck does not produce `S2_INTEGRATION_CANDIDATE_READY`, complete S2PLT04, enable SMTP, install scheduler, upload Release assets, execute production restore, migrate DB/public schema, mutate production queues, change source adapters or ranking, change CURRENT or V7.1/V7.2 contracts, close inherited P0/P1, enable DAILY_OPERATION, or claim integrated production acceptance.

## Owner Center Entry Rule

- `MOD-ADP-105` / `FORM-ADP-107` record the owner-facing entry rule for Stage 2 owner UX and mail-status work.
- GitHub-rendered Markdown is the primary owner-readable surface. A shallow `arxiv-daily-push/用户中心/README.md` entry plus adjacent status pages is the required target for owner status, mail, queue, review, action, and ROI summaries.
- Local `.adp` files, SMTP reports, run JSON, and candidate queue JSON remain valid evidence sources only. Owner pages must directly summarize sent, blocked/not sent, and queued states without requiring local absolute-path navigation.
- This rule does not migrate PR #240 owner pages by itself and does not replay email, enable SMTP/scheduler/Release, mutate queues, change public schema/DB, change source adapters or ranking, edit CURRENT/V7 baselines, close inherited P0/P1, accept S2PLT02, enable DAILY_OPERATION, or claim integrated production acceptance.
