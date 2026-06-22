# Phase 12 Email Human Format

Status: prepared; requires PR CI and a follow-up manual email test

## Goal

Improve the daily email front-end so the owner can scan it quickly, open the
12-second video, understand the article's practical value, and defer backend
ROI details to GitHub artifacts when needed.

## Changes

- Daily email subject now follows:
  `YYYYMMDD -- arXiv <Project Group> -- <arXiv Group> -- <Theme>`.
- Daily email body starts with human-facing sections instead of
  `project`, `date`, and `recipient` metadata lines.
- Daily email keeps Chinese layout and labels except for paper titles,
  arXiv category IDs, URLs, and other necessary technical terms.
- Daily email removes visible ROI score lines and delivery policy text.
- Daily email keeps Release URL, 12-second MP4 video URL, concise evidence,
  action-time guidance, and candidate queue summary.
- Backend artifacts still retain ranking and ROI evidence for audit.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_email_fmt_focus2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_global_scan.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_notifications.py -q`: 20 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_email_fmt_all PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 177 tests OK.

## Safety

- No production schedule enablement.
- No new SMTP send in this preparation commit.
- No direct Release upload in this preparation commit.
- No secret logging.
- No video email attachment.

## Rollback

Revert version `0.12.5` email format code, tests, and governance records, then
restore version `0.12.4`.
