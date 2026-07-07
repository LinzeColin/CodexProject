# Runbook

## Daily 11:30 Australia/Sydney run

The local scheduler uses Sydney local time. 11:30 Australia/Sydney is the operational replacement for the previous Beijing 09:30 wording during the current UTC+10 offset.

1. Confirm local repo is on `main` and clean enough to run.
2. Pull latest `origin/main` with fast-forward only.
3. Read `SKILL.md` and all references/templates.
4. Run `tools/check_source_readiness.py` as a fast preflight.
5. Continue only when readiness is `READY`.
6. Scan input directory recursively.
7. Build file manifest with SHA256 and size.
8. If the configured folder is missing, write `SOURCE_MISSING` plus private source candidates; do not silently fall back to zip/archive sources.
9. If the configured folder exists but contains unreadable/cloud-only files, write `SOURCE_UNREADABLE`; do not generate a partial Excel package.
10. If a private candidate is verified and the operator intends to populate the configured folder, run `tools/materialize_fund_source.py` first without `--apply`, inspect the manifest, then rerun with `--apply`.
11. Build evidence index for screenshots and finance files.
12. Write the `INDEXED_PENDING_EXTRACTION` no-hallucination output package first: current native Excel template copy, fact ledgers, exception tasks, cross-review JSON, audit log, and run summary.
13. Extract only real values with source trace. CSV files may be auto-extracted only when they contain the exact structured columns `date, company, bank, account_alias, liquidity_tier, inflow, outflow, ending_balance, flow_type`; those rows become `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW`, not management conclusions.
14. When structured CSV facts exist, patch the copied native `.xlsx` workbook with the same traced facts in homepage KPI cards, visible flow/risk/matrix sheets, and hidden `H01/H02/H03`; preserve native chart parts and keep all values pending review.
15. Put low-confidence OCR/vision rows into review queue.
16. Build funds ledger and net-flow ledger.
17. Apply internal-transfer pairing before management rollups.
18. Build daily balance continuity and company-bank matrix.
19. Build tax/loan/wealth-management/deposit risk tables.
20. Promote reviewed facts into Excel with exact sheet order and style spec.
21. Hide audit/review sheets.
22. Run validation checks.
23. Write run summary.
24. Commit/push skill or automation changes to GitHub main only after validation passes.

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
