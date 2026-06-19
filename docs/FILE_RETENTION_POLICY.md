# File Retention Policy

Updated: 2026-06-13

## Keep In GitHub

- Source code under `tab-research-pipeline/`.
- Tests and runner scripts.
- Config files.
- README, RUNBOOK, AGENTS, handoff, and development status.
- Public-safe latest artifacts under `artifacts/latest/`.
- Local cleanup audit reports under `ops/`.

## Keep Locally

- Active working source directory.
- Current Downloads app and HTML entry.
- Private My Bets authorized profile, if still needed by the user.
- Current public latest artifacts required by the running local app.
- Minimal reports needed for current review.

## Back Up To GitHub Then Remove Locally

- Old public report iterations when not needed for current UI.
- Reproducible QA screenshots.
- Reproducible generated previews.
- Historical diagnostics once summarized in manifests.

## Delete Without GitHub Backup

These are reproducible or unsafe to publish:

- `__pycache__/`
- `.pytest_cache/`
- virtual environments such as `.venv/`
- Chrome cache directories inside private profiles
- `.DS_Store`
- transient lock files

## Never Upload To GitHub

- TAB credentials.
- OTP or session secrets.
- Chrome cookies/profile databases.
- My Bets raw text.
- Account identifiers.
- Private stake-level detail.
- Raw private logs with sensitive paths or account information.
- Third-party scraped JS/HTML bundles unless separately reviewed for license and necessity.

## Current Slimming Principle

The GitHub repository is the durable development and public-safe artifact backup.
The local workspace should retain only files needed to run the current app, reproduce the current status, or continue implementation.

