# Runbook

## Daily 11:30 Australia/Sydney run

The local scheduler uses Sydney local time. 11:30 Australia/Sydney is the operational replacement for the previous Beijing 09:30 wording during the current UTC+10 offset.

1. Confirm local repo is on `main` and clean enough to run.
2. Pull latest `origin/main` with fast-forward only.
3. Read `SKILL.md` and all references/templates.
4. Scan input directory recursively.
5. Build file manifest with SHA256 and size.
6. If the configured folder is missing, write `SOURCE_MISSING` plus private source candidates; do not silently fall back to zip/archive sources.
7. If the configured folder exists but contains unreadable/cloud-only files, write `SOURCE_UNREADABLE`; do not generate a partial Excel package.
8. If a private candidate is verified and the operator intends to populate the configured folder, run `tools/materialize_fund_source.py` first without `--apply`, inspect the manifest, then rerun with `--apply`.
9. Build evidence index for screenshots and finance files.
10. Write the `INDEXED_PENDING_EXTRACTION` no-hallucination output package first: current native Excel template copy, empty fact ledgers, exception tasks, cross-review JSON, audit log, and run summary.
11. Extract only real values with source trace.
12. Put low-confidence OCR/vision rows into review queue.
13. Build funds ledger and net-flow ledger.
14. Apply internal-transfer pairing before management rollups.
15. Build daily balance continuity and company-bank matrix.
16. Build tax/loan/wealth-management/deposit risk tables.
17. Promote reviewed facts into Excel with exact sheet order and style spec.
18. Hide audit/review sheets.
19. Run validation checks.
20. Write run summary.
21. Commit/push skill or automation changes to GitHub main only after validation passes.

## Source materialization command

Dry-run:

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/materialize_fund_source.py \
  --repo-root /Users/linzezhang/CodexProject \
  --source-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Archive/付款请示群 \
  --target-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群
```

Apply after checking the dry-run manifest:

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/materialize_fund_source.py \
  --repo-root /Users/linzezhang/CodexProject \
  --source-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Archive/付款请示群 \
  --target-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群 \
  --apply
```

If dry-run returns `SOURCE_UNREADABLE`, do not apply. First make the OneDrive
source files available offline, then rerun dry-run and confirm
`unreadable_count=0`.

## Manual work expected from user

The user should only need to place files in the input folder and review high-risk exception tasks. The agent must not ask the user to manually rename files or hand-type data unless a blocking data ambiguity cannot be resolved from evidence.
