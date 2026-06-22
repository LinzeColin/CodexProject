# PHASE S1-08 Local Runtime Recovery

- task_id: `S1-08-LOCAL_RUNTIME_RECOVERY-001`
- date: `2026-06-22`
- status: `completed`
- production_acceptance_claimed: `false`
- production_schedule_enabled: `false`
- real_smtp_sent: `false`
- real_release_uploaded: `false`
- video_generated: `false`
- scheduler_installed: `false`

## Scope

Implemented the Stage 1 local runtime recovery control surface:

- `adp tick` writes explicit heartbeat and checkpoint state under an operator-supplied state directory;
- `adp watchdog` blocks missing heartbeat, stale heartbeat, and stale runtime locks;
- `adp backup` copies a passing SQLite database and small supporting files into a SHA256 manifest under the low-resource byte cap;
- `adp restore` requires explicit confirmation, blocks unsafe overwrite by default, verifies SHA256, and inspects the restored SQLite database;
- `adp runtime-audit` blocks enabled production side-effect flags before Stage 1 acceptance;
- `adp scheduler install` and `adp scheduler uninstall` emit macOS/Linux/Windows templates only and never apply OS scheduler changes.

## Verification

- focused runtime recovery and CLI tests: `13 tests OK`
- full arxiv-daily-push tests: `210 tests OK`
- semantic extractor: `43 active formulas and 308 active parameters checked`

## Boundary

S1-08 proves deterministic local recovery controls only. It does not install a
real scheduler, start a local background process, send Gmail SMTP, upload GitHub
Releases, generate video, run 30 historical previews, prove two live production
days, or claim `ARXIV_PRODUCTION_ACCEPTED`.
