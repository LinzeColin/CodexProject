# Production Data Request Contract

Generated context: Serenity Daily Analysis baseline-first workflow.

Current state: the production baseline can be generated without current Alipay holdings. The required production data path is candidate evidence, fund execution rules, benchmark windows, and mail/runtime verification. Current Alipay holdings are optional overlay data for a later personal-position view.

Safety boundary: this workflow does not place trades, does not submit fund orders, and does not enable recurring real email sending by default.

## Required Inputs For Baseline

| Input | Target file | Minimum required content | Evidence requirement | Production effect |
|---|---|---|---|---|
| Serenity baseline candidate universe | `outputs/intake_pack/03_candidates_to_fill.csv` | Candidate code/name/market/type/theme, source names, source priorities, source URLs/evidence, official source count, conservative exclusion flag | Global source priority: MooMoo > Alipay > official platform > trade snapshot > public aggregation | Supports all-market mixed Top5 ranking |
| Fund execution rules | `outputs/intake_pack/02_fund_rules_to_fill.csv` | Subscription/redemption status, cutoff time, confirmation/redeem lag, subscription/redemption/management/custody/sales-service fees, min purchase, source priority, `as_of` | Prefer MooMoo, Alipay, and fund-company official pages; QDII/global/HK/US funds need product-specific rule proof | Supports fee/status/execution feasibility checks |
| Benchmark history | `data/manual/benchmark_price_history.csv` | Shanghai Composite and S&P 500 1m/3m/recent 10 trading-day comparison data | Prefer MooMoo or official index/exchange source; public aggregation is warning-level fallback | Supports benchmark comparison gate |

## Optional Overlay

| Input | Target file | Use | Evidence requirement |
|---|---|---|---|
| Current Alipay holdings | `outputs/intake_pack/01_alipay_positions_to_fill.csv` | Optional personal-position comparison only; not required for Serenity baseline | Current Alipay page/export/OCR evidence, with `source_note` containing `evidence=...` |

## Acceptance Gates

- Baseline candidates must exclude bond, money-market, Yuebao/cash-like, capital-preservation, and other conservative structures.
- Fund fee/status/cutoff/lag fields cannot be blank for production candidates.
- Official-grade source count should be at least 2 for Action-Ready candidates; otherwise the item stays Watch or Manual Review.
- Risk gate remains strict: MDD at or above 40% or recovery-to-origin time at or above 365 days creates Block or clear-reduction labels.
- Benchmark comparison must cover 1 month, 3 months, and recent 10 trading days versus Shanghai Composite and S&P 500. The system may target outperformance, but it must not guarantee future outperformance.
- Real mail sending remains an explicit runtime choice and is not enabled by this contract.

## Fastest Safe Workflow

```bash
python -m app.cli normalize-intake-bundle \
  --fund-rules-csv <current_fund_rules.csv> \
  --candidates-csv <current_candidates.csv> \
  --as-of YYYY-MM-DD \
  --write-pack \
  --json

python -m app.cli source-evidence-audit --pack-dir outputs/intake_pack --require-pass --json
python -m app.cli production-unlock-check --json
SERENITY_MAIL_SEND_ENABLED=true python -m app.cli preflight --json
SERENITY_MAIL_SEND_ENABLED=true python -m app.cli completion-audit --json
```

## Current Recommended Next Input

No current Alipay holding file is required for the baseline. The next useful production improvement is upgrading exact benchmark evidence from public aggregation fallback to MooMoo or official index/exchange evidence when available.
