# Runbook

## Daily 11:30 Australia/Sydney run

The local scheduler uses Sydney local time. 11:30 Australia/Sydney is the operational replacement for the previous Beijing 09:30 wording during the current UTC+10 offset.

1. Confirm local repo is on `main` and clean enough to run.
2. Pull latest `origin/main` with fast-forward only.
3. Read `SKILL.md` and all references/templates.
4. Scan input directory recursively.
5. Build file manifest with SHA256 and size.
6. If the configured folder is missing, write `SOURCE_MISSING` plus private source candidates; do not silently fall back to zip/archive sources.
7. Build evidence index for screenshots and finance files.
8. Write the `INDEXED_PENDING_EXTRACTION` no-hallucination output package first: current native Excel template copy, empty fact ledgers, exception tasks, cross-review JSON, audit log, and run summary.
9. Extract only real values with source trace.
10. Put low-confidence OCR/vision rows into review queue.
11. Build funds ledger and net-flow ledger.
12. Apply internal-transfer pairing before management rollups.
13. Build daily balance continuity and company-bank matrix.
14. Build tax/loan/wealth-management/deposit risk tables.
15. Promote reviewed facts into Excel with exact sheet order and style spec.
16. Hide audit/review sheets.
17. Run validation checks.
18. Write run summary.
19. Commit/push skill or automation changes to GitHub main only after validation passes.

## Manual work expected from user

The user should only need to place files in the input folder and review high-risk exception tasks. The agent must not ask the user to manually rename files or hand-type data unless a blocking data ambiguity cannot be resolved from evidence.
