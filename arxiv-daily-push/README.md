# arXiv Daily Push

`arXiv 日报推送 / arXiv Daily Push` is a private, evidence-first daily learning
pipeline. The Phase 11 foundation provides the local package, CLI contract,
governance records, configuration examples, generic schemas, runtime contract
validators, a deterministic `RunRecord` state machine, an arXiv Atom adapter,
deterministic ranking, Claim Ledger publication gate, evidence-linked lesson
generation, TTS dry-run narration planning, storyboard/video dry-run planning,
daily dry-run orchestration, runner/release/email dry-run handoff, final
acceptance/handoff readiness packaging, small-window live arXiv ingest, an
explicit SMTP delivery boundary, a fail-closed GitHub Release delivery
boundary, a scheduled production workflow gate, a controlled scheduled
execution driver, a daily input builder from arXiv Atom source batches, an
incremental trial evidence ledger update bridge, cross-run ledger state
persistence, operational trial evidence annotation, weekly/monthly replay
evidence generation, and tests.

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
- small-window live arXiv Atom source ingestion with incremental duplicate filtering and fail-closed network/API behavior
- deterministic daily input builder that converts an arXiv `SourceBatch` into ranked daily pipeline input using only Atom `<summary>` claims
- incremental trial evidence ledger updater that appends only production-ready scheduled daily-run reports and blocks duplicate or dry-run evidence
- trial ledger state exporter and scheduled artifact restoration so 30-day evidence can accumulate across GitHub Actions runs
- operational trial evidence annotator that merges explicit weekly/monthly replay, recovery drill, scheduler, Release, SMTP, and resource refs without hand-editing the ledger
- weekly/monthly replay evidence builder that validates production-ready daily refs, duplicate-free coverage, 7-day weekly coverage, 30-day monthly coverage, and a durable replay evidence ref before producing annotation hints
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

- bulk arXiv ingestion
- live source ingest pass on the current local machine; Python SSL certificate validation currently blocks this environment
- TTS model download
- real TTS audio synthesis
- real video rendering
- enabled GitHub Actions runner setup
- verified real SMTP delivery on a provisioned production runner
- verified private GitHub Release creation on a provisioned production runner
- enabled scheduled runner execution on the default branch
- actual weekly/monthly replay run archived with a durable production ref
- claimed scheduled 30-day trial start
- claimed 30-day operational acceptance

## Goal Baseline

The long-running `/goal` baseline is stored at:

```text
docs/pursuing_goal/06_PURSUING_GOAL_READY_PROMPT.md
```

Phase 1-11 use arXiv as the first source, while preserving generic
`SourceAdapter`, `SourceItem`, `EvidenceClaim`, `Lesson`, `Storyboard`,
`Publication`, and `RunRecord` boundaries for future data sources.

## Local Validation

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q
python3 scripts/validate_project_governance.py --project arxiv-daily-push
git diff --check
```

## Resource Policy

Do not commit media, model weights, voice samples, credentials, Codex auth,
GitHub tokens, SMTP secrets, render cache, or dependency directories. Phase 1-11
must remain code, schema, fixture, governance, and dry-run JSON only unless a
later explicit resource and acceptance gate permits more.
