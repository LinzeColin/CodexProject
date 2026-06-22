# arXiv Daily Push

`arXiv 日报推送 / arXiv Daily Push` is a private, evidence-first daily learning
pipeline. The current implementation provides the local package, CLI contract,
governance records, configuration examples, generic schemas, runtime contract
validators, a deterministic `RunRecord` state machine, an arXiv Atom adapter,
deterministic ranking, Claim Ledger publication gate, evidence-linked lesson
generation, TTS dry-run narration planning, storyboard/video dry-run planning,
daily dry-run orchestration, runner/release/email dry-run handoff, final
acceptance/handoff readiness packaging, small-window live arXiv ingest, an
explicit SMTP delivery boundary, a fail-closed GitHub Release delivery
boundary, a scheduled production workflow gate, a controlled scheduled
execution driver, an all-arXiv Phase 12 scanner with candidate queue and ROI
ranking, a daily input builder from arXiv Atom source batches, an
incremental trial evidence ledger update bridge, cross-run ledger state
persistence, operational trial evidence annotation, weekly/monthly replay
evidence generation, recovery drill evidence generation, resource telemetry
evidence generation, a fail-closed 30-day trial start gate, a production launch
readiness gate, and tests.

The active pursuing-goal baseline is the Review8 two-stage V4 baseline locked
in `docs/pursuing_goal/BASELINE_LOCK.md`. The project is not production
accepted: the latest verified GitHub manual delivery run proves one controlled
Release plus Gmail SMTP test only, not the required 30-day trial or two live
production days.

## Current Scope

Implemented now:

- `adp version`
- `adp doctor`
- `adp render-email`
- `adp send-notification`
- `adp publish-release`
- `adp validate-record`
- `adp arxiv-url`
- `adp parse-arxiv-atom`
- `adp fetch-arxiv-latest`
- `adp source-registry`
- `adp plan-all-arxiv-scan`
- `adp build-all-arxiv-daily-input`
- `adp build-daily-input`
- `adp rank-candidates`
- `adp gate-publication`
- `adp generate-lesson`
- `adp generate-narration`
- `adp generate-storyboard`
- `adp run-daily-dry-run`
- `adp build-handoff`
- `adp build-acceptance`
- `adp evaluate-trial`
- `adp update-trial-ledger`
- `adp export-trial-ledger-state`
- `adp annotate-trial-ops-evidence`
- `adp export-trial-ops-state`
- `adp build-trial-replay-evidence`
- `adp build-trial-recovery-evidence`
- `adp build-trial-resource-evidence`
- `adp plan-trial-start`
- `adp plan-trial-start-workflow`
- `adp plan-production-launch`
- `adp preflight-production`
- `adp plan-trial-bootstrap`
- `adp plan-production-scheduler`
- `adp run-scheduled-production`
- dry-run email rendering for `linzezhang35@gmail.com`
- fail-closed SMTP notification delivery evidence; real sending requires explicit `--allow-send` and SMTP environment variables
- fail-closed GitHub Release delivery evidence; real Release creation requires explicit `--allow-upload`, `ADP_RELEASE_TARGET`, `gh`, and safe asset checks
- local resource and dependency readiness checks
- generic contracts for `SourceItem`, `EvidenceClaim`, `Lesson`, `Storyboard`, `Publication`, and `RunRecord`
- deterministic state transitions for local `RunRecord` validation
- arXiv Atom feed parsing into generic `SourceItem` records using local fixture tests
- Stage 1 source registry contract that keeps `config/owner_controls.yaml` as the single editable source list, enables only SRC-ARXIV/arxiv.atom.v1, and caps canaries at 10 metadata records
- small-window live arXiv Atom source ingestion with incremental duplicate filtering and fail-closed network/API behavior
- deterministic daily input builder that converts an arXiv `SourceBatch` into ranked daily pipeline input using only Atom `<summary>` claims
- Phase 12 all-arXiv primary archive scan plan and daily input builder that ranks candidates by relevance, learning value, economic conversion rate, ROI, cross-disciplinary value, and explainability
- persistent `adp-candidate-queue` behavior that stores high-value unselected papers and consumes the queue when no new high-value candidate is available
- scheduled email delivery package that requires a Chinese lesson, candidate queue summary, and a GitHub Release-hosted video artifact link before real SMTP can count as production evidence
- incremental trial evidence ledger updater that appends only production-ready scheduled daily-run reports and blocks duplicate or dry-run evidence
- trial ledger state exporter and scheduled artifact restoration so 30-day evidence can accumulate across GitHub Actions runs
- operational trial evidence annotator that merges explicit weekly/monthly replay, recovery drill, scheduler, Release, SMTP, and resource refs without hand-editing the ledger
- weekly/monthly replay evidence builder that validates production-ready daily refs, duplicate-free coverage, 7-day weekly coverage, 30-day monthly coverage, and a durable replay evidence ref before producing annotation hints
- recovery drill evidence builder that validates a failed or degraded scheduled daily-run plus a recovered production-ready rerun with real sent notifications and durable failure/recovery refs before producing annotation hints
- resource telemetry evidence builder that validates 30 unique daily resource refs against passing production preflight reports before producing annotation hints
- trial start readiness gate that requires passing preflight, bootstrap, scheduler, all-arXiv source input, real SMTP, real Release, durable refs, and explicit confirmation before a real 30-day trial is marked start-ready
- manual trial start evidence workflow that collects preflight, all-arXiv source input, Phase 12 artifacts, candidate queue, SMTP, Release, and start-gate artifacts on the private runner with explicit variable-gated side effects
- production launch readiness gate that blocks default-branch trial start workflow dispatch until the PR is merged and non-draft, expected head SHA matches, workflow contract is ready, runner/secrets/vars have durable refs, and launch is explicitly confirmed
- deterministic 100-point ranking with per-component audit output
- fail-closed candidate blocking for missing P0 evidence, metadata conflicts, and recent duplicate selections
- Claim Ledger construction from explicit evidence claims
- publication hard-block gate for unsupported P0 claims, metadata conflicts, and unsupported peer-review claims
- deterministic Chinese Lesson JSON generation from supported Claim Ledger evidence
- lesson validation that blocks unsupported or unknown claim references
- dry-run narration/TTS-ready JSON generation from Lesson objects
- TTS resource gate that blocks audio writes, model downloads, and real synthesis in Phase 7
- dry-run Storyboard generation from narration plans
- video media gate that blocks rendering, media writes, and asset downloads in Phase 8
- local daily dry-run pipeline across evidence, lesson, narration, storyboard, publication, and email preview
- runner/release/email dry-run handoff that keeps scheduler, Release upload, and real SMTP disabled
- final acceptance package that marks production acceptance blocked until real 30-day, scheduler, Release, SMTP, and resource evidence exists
- 30-day trial evidence validator that exports production acceptance evidence only after daily uniqueness, P0 traceability, scheduler, Release, SMTP, resource, weekly/monthly replay, and recovery gates pass
- production preflight gate that blocks scheduled execution unless runtime commands, secret env keys, disk, memory, Git artifact hygiene, and cache/staging directories are safe
- manual production trial bootstrap workflow/runbook that runs preflight before any trial work and keeps cron, Release upload, and SMTP sending disabled
- scheduled production workflow gate with `Australia/Sydney` 04:45 health check, 05:00 daily run, and 05:10 watchdog slots; default GitHub variables keep scheduled work and side effects disabled
- controlled scheduled execution driver that turns preflight, daily-run, and watchdog results into `adp-scheduled-execution` evidence while requiring real SMTP and Release refs before production evidence can count
- scheduled trial ledger update artifact that can accumulate daily evidence without claiming 30-day acceptance before the validator passes
- scheduled `adp-trial-evidence-ledger` state artifact that is restored on later runs when no explicit ledger path is configured
- SMTP delivery report schema that records message hashes and secret-key presence without logging SMTP secret values or email body
- GitHub Release delivery report schema that records asset hashes and command intent without logging Release notes, secrets, stdout, or stderr
- governance records required by `CodexProject`

Not implemented yet:

- bulk arXiv ingestion beyond the bounded per-archive latest window
- live source ingest pass on the current local machine; Python SSL certificate validation currently blocks this environment
- TTS model download
- real TTS audio synthesis
- real video rendering
- enabled GitHub Actions runner setup
- verified real SMTP delivery on a provisioned production runner
- verified private GitHub Release creation on a provisioned production runner
- enabled scheduled runner execution on the default branch
- actual weekly/monthly replay run archived with a durable production ref
- actual recovery drill run archived with a durable production ref
- actual 30-day resource telemetry run archived with a durable production ref
- claimed scheduled 30-day trial start from current live GitHub runner evidence
- claimed production launch readiness from complete external refs and explicit owner confirmation
- claimed 30-day operational acceptance
- Stage 1 V4 owner-control surface: `config/owner_controls.yaml`
- Stage 1 V4 owner views: `docs/owner/OWNER_CONSOLE.md`,
  `docs/owner/SOURCE_CATALOG.md`, `docs/owner/MODEL_AND_QUEUE.md`,
  `docs/owner/CONTENT_LEDGER.csv`
- Stage 1 V4 unified SQLite/WAL/FTS5 document and event model
- Stage 1 V4 local runtime commands: `adp tick`, `adp watchdog`,
  `adp backup`, `adp restore`, `adp runtime-audit`, and scheduler
  install/uninstall helpers

## Goal Baseline

The current long-running `/goal` baseline is locked at:

```text
docs/pursuing_goal/BASELINE_LOCK.md
docs/pursuing_goal/FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_V4.txt
```

The legacy Phase 1-11 baseline remains at
`docs/pursuing_goal/06_PURSUING_GOAL_READY_PROMPT.md` for history only. Stage 1
uses arXiv as the first source, while preserving generic
`SourceAdapter`, `SourceItem`, `EvidenceClaim`, `Lesson`, `Storyboard`,
`Publication`, and `RunRecord` boundaries for future data sources.

Current V4 task sequence:

- `S1-02-BASELINE-LOCK-TRACEABILITY-001`: baseline lock and traceability.
- `S1-03-OWNER-CONTROLS-001`: owner controls and owner-readable views.
- `S1-04-SQLITE-DATA-MODEL-001`: unified local document/event store.
- `S1-05-ARXIV-CONNECTOR-CONTRACT-001`: arXiv source registry contract. Completed.
- `S1-06-SCORING-QUEUE-LEDGER-001`: research scoring, queue, and content ledger. Next ready task.
- `S1-07-B1_REPORT_EMAIL_MEDIA-001`: B1 report, claims, email preview, and media interface.
- `S1-08-LOCAL_RUNTIME_RECOVERY-001`: scheduler, watchdog, backup, and restore.
- `S1-09-MIGRATION_PACKAGE-001`: low-resource integration and migration package.

## Local Validation

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q
python3 scripts/validate_project_governance.py --project arxiv-daily-push
git diff --check
```

## Resource Policy

Do not commit media, model weights, voice samples, credentials, Codex auth,
GitHub tokens, SMTP secrets, render cache, or dependency directories. Stage 1
Window A remains low-resource until migration readiness is explicitly proven:
no PDF bulk downloads, no large model/TTS downloads, no full 30-day replay, and
no broad non-arXiv source expansion.
