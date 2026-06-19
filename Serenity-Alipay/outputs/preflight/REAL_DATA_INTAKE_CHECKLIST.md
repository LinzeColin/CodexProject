# Real Data Intake Checklist

Use this checklist to replace sample data with verifiable production inputs.

## 1. Alipay Holdings

Target file:

```text
data/imports/alipay_positions.csv
```

Required columns:

```csv
asset_code,asset_name,platform,current_amount,current_weight,cost_basis,unrealized_pnl,as_of,source_note
```

Rules:

- `source_note` must describe the actual source, for example `Alipay export 2026-06-12`.
- Do not use sample/demo/manual-placeholder notes.
- Weights can be decimal or percent.
- Current production validation requires position `as_of` to be no more than 2 days stale.
- After replacement, run:

```bash
python -m app.cli import-alipay --csv data/imports/alipay_positions.csv
```

## 2. Fund Rules

Target file:

```text
data/manual/fund_rules.csv
```

Every candidate must include:

- subscription status
- redemption status
- cutoff time
- confirmation lag
- redeem lag
- subscription fee
- redemption fee
- management fee
- custody fee
- source name
- source type
- URL or local evidence path
- evidence level

Rules:

- Prefer Alipay fund page and fund company official pages.
- QDII confirmation/redemption lags must be product-specific.
- Any missing fee or redemption status blocks production.
- Aggregated/public fallback cannot unlock execution-critical fund rules.

## 3. Candidate Universe

Target file:

```text
data/manual/candidates.csv
```

Rules:

- Keep off-platform funds first.
- Exclude bond, money-market, Yu'e Bao, cash-management, and conservative structured products.
- Source URLs should point to MooMoo, Alipay, fund company, exchange filings, or official reports when available.
- Aggregated sources can fill the research view only; they cannot upgrade a candidate to Action-Ready by themselves.
- Current production gate requires at least two official-grade sources for Action-Ready eligibility.

## 4. MooMoo/OpenD

Expected result:

```bash
python -m app.cli moomoo-smoke --json
```

Must show:

```json
"production_ready_for_moomoo_data": true
```

Current local state:

- OpenD socket is reachable.
- Current interpreter imports `moomoo_api 10.6.6608`.
- OpenD was already running before the latest commands; `started_by_tool=false`, so the tool did not close it.
- `collect-moomoo` succeeded for `US.SPY` daily K-line collection.

Collection command:

```bash
python -m app.cli collect-moomoo --symbol US.SPY --start 2026-06-01 --end 2026-06-12 --require-success --json
```

If OpenD is unavailable:

- The tool may auto-start it from the discovered workbench when the socket is closed.
- If the tool starts OpenD itself, it cleans up the started process after the run unless `--keep-auto-started-opend` is used.
- If OpenD was already open, it is treated as user-managed and left running.

## 5. Benchmark Sources

Run:

```bash
python -m app.cli benchmark-smoke --require-production --json
```

Current local state:

- Benchmark smoke passes via exact Yahoo Finance chart fallback.
- Generated file: `data/manual/benchmark_price_history.csv`.
- Shanghai Composite `000001.SH`: 70 rows, 2026-03-02 to 2026-06-11.
- S&P 500 `SPX`: 73 rows, 2026-03-02 to 2026-06-12.
- Source priority is 5 public aggregation, so the system keeps a warning and still prefers MooMoo/official sources.
- Shanghai Composite exact MooMoo probe `SH.000001` fails because the account lacks CN market index quote permission.
- S&P 500 exact MooMoo probes fail; `US.SPY` and `US.VOO` ETF proxies pass but remain proxy-only.

Template:

```text
app/templates/benchmark_price_history_template.csv
```

## 6. Production Gate

Before editing production files, generate a fill-ready intake pack:

```bash
python -m app.cli production-intake-pack --scan-path ~/Downloads --scan-path ~/Documents --json
```

Review:

```text
outputs/intake_pack/README_PRODUCTION_DATA_INTAKE.md
outputs/intake_pack/FIELD_GUIDE.md
outputs/intake_pack/04_gap_actions.csv
```

After filling the pack, dry-run and then promote:

```bash
python -m app.cli promote-intake-pack --json
python -m app.cli promote-intake-pack --apply --json
```

The apply step blocks placeholders and backs up existing production files before copying.

Run:

```bash
python -m app.cli preflight --require-production --json
```

Only proceed to scheduled production after it returns:

```json
"production_ready": true
```

Current status: `production_ready=false`; production blockers are Alipay holdings, fund rules, and candidate universe.
