# Evidence Intake Guide

Use this guide when attaching real Alipay screenshots/exports, fund-rule pages, or candidate-source files to the intake pack.

## Recommended Local Layout

Create this folder when you have evidence files to attach:

```text
outputs/intake_pack/evidence/
```

Suggested filenames:

- `alipay_positions_YYYY-MM-DD.csv` or `alipay_positions_YYYY-MM-DD.png`
- `fund_rules_<asset_code>_YYYY-MM-DD.pdf` or `.png`
- `candidate_source_<asset_code>_YYYY-MM-DD.pdf` or `.png`

## CSV Reference Rules

Inside the intake pack, relative references are resolved from `outputs/intake_pack/`.

- In `01_alipay_positions_to_fill.csv`, set `source_note` like `Alipay current holdings; evidence=evidence/alipay_positions_YYYY-MM-DD.csv`.
- In `02_fund_rules_to_fill.csv`, set `url_or_path` to `evidence/fund_rules_<asset_code>_YYYY-MM-DD.pdf` or a current http(s) URL.
- In `03_candidates_to_fill.csv`, set `source_url` to `evidence/candidate_source_<asset_code>_YYYY-MM-DD.pdf` or a current http(s) URL.

## Verification Commands

```bash
python -m app.cli source-evidence-audit --pack-dir outputs/intake_pack --json
python -m app.cli promote-intake-pack --json
python -m app.cli promote-intake-pack --apply --json
python -m app.cli preflight --require-production --json
```

When `promote-intake-pack --apply` passes, files under `outputs/intake_pack/evidence/` are copied into the project-level `evidence/` directory so production CSV references like `evidence/...` remain verifiable after promotion.

Do not attach private evidence files to a delivery ZIP unless you intentionally want that private evidence packaged.
