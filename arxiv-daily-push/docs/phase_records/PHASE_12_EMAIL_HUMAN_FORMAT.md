# Phase 12 Email Human Format

Status: implemented; requires PR CI before any follow-up controlled email test

## Goal

Improve the daily email front-end so the owner can scan it quickly, open the
message as a Chinese teaching brief, understand the article's practical value,
and keep backend ranking, Release, video, and delivery-policy details out of
the human-facing Stage 1 email.

## Changes

- Daily email subject now follows:
  `YYYYMMDD -- arXiv <Project Group> -- <arXiv Group> -- <Theme>`.
- Daily email body starts with human-facing sections instead of
  `project`, `date`, and `recipient` metadata lines.
- Daily email keeps Chinese layout and labels except for paper titles,
  arXiv category IDs, URLs, and other necessary technical terms.
- Daily email removes visible ROI score lines, delivery policy text, Release
  reading entries, video entries, and backend wording.
- Daily email now uses teaching-first sections: today’s core question, why it
  matters, first-principles chain, decision translation, questions, default
  action, candidate queue, and feedback.
- Backend artifacts still retain ranking and ROI evidence for audit.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_email_human_focus PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_global_scan.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_notifications.py -q`: 23 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_email_human_all PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 200 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_email_human_semantic PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_semantic_extractors.py arxiv-daily-push`: 48 formulas and 342 parameters checked.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_email_human_gov PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`: errors 0, warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_email_human_rootgov PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`: 154 tests OK.
- `git diff --check`: PASS.
- Cache hygiene check: no `__pycache__` or `.pyc` files under `arxiv-daily-push`, `tests`, or `scripts`.
- PR CI validation remains pending for this branch.

## Safety

- No production schedule enablement.
- No new SMTP send in this preparation commit.
- No direct Release upload in this preparation commit.
- No secret logging.
- No video requirement and no video email attachment.

## Rollback

Revert the `ADP-PHASE12-EMAIL-HUMAN-FORMAT-036` email renderer, tests, and
governance records.
