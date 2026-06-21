# arXiv Daily Push

`arXiv 日报推送 / arXiv Daily Push` is a private, evidence-first daily learning
pipeline. The Phase 10 foundation provides the local package, CLI contract,
governance records, configuration examples, generic schemas, runtime contract
validators, a deterministic `RunRecord` state machine, an arXiv Atom adapter,
deterministic ranking, Claim Ledger publication gate, evidence-linked lesson
generation, TTS dry-run narration planning, storyboard/video dry-run planning,
daily dry-run orchestration, runner/release/email dry-run handoff, and tests.

## Current Scope

Implemented now:

- `adp version`
- `adp doctor`
- `adp render-email`
- `adp validate-record`
- `adp arxiv-url`
- `adp parse-arxiv-atom`
- `adp rank-candidates`
- `adp gate-publication`
- `adp generate-lesson`
- `adp generate-narration`
- `adp generate-storyboard`
- `adp run-daily-dry-run`
- `adp build-handoff`
- dry-run email rendering for `linzezhang35@gmail.com`
- local resource and dependency readiness checks
- generic contracts for `SourceItem`, `EvidenceClaim`, `Lesson`, `Storyboard`, `Publication`, and `RunRecord`
- deterministic state transitions for local `RunRecord` validation
- arXiv Atom feed parsing into generic `SourceItem` records using local fixture tests
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
- governance records required by `CodexProject`

Not implemented yet:

- scheduled or bulk arXiv ingestion
- TTS model download
- real TTS audio synthesis
- real video rendering
- enabled GitHub Actions runner setup
- real SMTP sending or scheduled runner execution

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
GitHub tokens, SMTP secrets, render cache, or dependency directories. Phase 1-10
must remain code, schema, fixture, governance, and dry-run JSON only unless a
later explicit resource and acceptance gate permits more.
