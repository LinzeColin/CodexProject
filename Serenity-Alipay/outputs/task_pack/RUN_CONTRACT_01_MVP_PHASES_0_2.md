# Run Contract 01: MVP Phases 0-2

## Objective

Implement the first bounded MVP slice for Serenity Daily Analysis.

## Minimal Scope

- Python local package.
- Config.
- SQLite schema.
- CLI.
- Alipay CSV import.
- Manual candidate/fund rule loaders.
- Metrics and scoring.
- Hard risk gates.
- Markdown report draft.

## Files Likely To Create

```text
pyproject.toml or requirements.txt
app/
tests/
data/imports/
data/reports/
data/notifications/
```

## Commands To Validate

```bash
python -m app.cli doctor
python -m app.cli init-db
python -m app.cli import-alipay --csv data/imports/alipay_positions.csv
python -m app.cli run --slot R7 --dry-run
pytest -q
```

## Risks

- moomoo/OpenD may be unavailable.
- Current directory may not yet be a Python repo.
- Apple Mail send should remain disabled.
- External data quality may be insufficient.

## Stop Conditions

- Tests fail after 3 focused repair loops.
- Implementation requires credentials or platform login.
- Scope would require automatic trading.

