# Production Intake Field Guide

## Alipay Positions

- `asset_code`: same code used in candidates and fund rules.
- `current_amount`: current holding market value from Alipay/fund platform.
- `current_weight`: portfolio weight as decimal or percent.
- `as_of`: source snapshot date, `YYYY-MM-DD`, no more than 2 days stale for production.
- `source_note`: must name real evidence and include a verifiable reference, for example `Alipay export 2026-06-12; evidence=/absolute/path/to/export.csv`; sample/demo/manual placeholder is blocked.

## Fund Rules

- Use Alipay fund detail/rule page or fund company official page.
- Required execution fields: subscription/redemption status, cutoff time, confirm/redeem lag, subscription/redemption/management/custody fees.
- `source_type` should be `alipay`, `official`, or `moomoo`; aggregated fallback cannot unlock execution rules.
- `source_priority` should be 1-3 for production.
- `url_or_path` must be a valid http(s) URL or an existing local evidence file path, not the production CSV itself.

## Candidate Universe

- Exclude bond, money-market, Yu'e Bao, conservative structured, and cash-management products.
- Non-excluded candidates need at least two official-grade sources for Action-Ready eligibility.
- Aggregated fallback can support research view only; it cannot upgrade a candidate to Action-Ready.
- `missing_nav_days` and `missing_holding_days` must be <= 2.
- `source_url` must be a valid http(s) URL or an existing local evidence file path.
