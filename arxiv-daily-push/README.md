# arXiv Daily Push

`arXiv 日报推送 / arXiv Daily Push` is a private, evidence-first daily learning
pipeline. The Phase 1 repository foundation provides only the local package,
CLI contract, governance records, configuration examples, schemas, and tests.

## Phase 1 Scope

Implemented now:

- `adp version`
- `adp doctor`
- `adp render-email`
- dry-run email rendering for `linzezhang35@gmail.com`
- local resource and dependency readiness checks
- governance records required by `CodexProject`

Not implemented in Phase 1:

- arXiv ingestion
- ranking or queue selection
- Claim Ledger extraction
- TTS model download
- video rendering
- GitHub Actions runner setup
- real SMTP sending

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
GitHub tokens, SMTP secrets, render cache, or dependency directories. Phase 1-6
must remain text/code/schema only.

