# 06 Implementation Phases

## Phase 0: Repo Bootstrap

Deliver:

- Python package skeleton.
- Config file.
- SQLite schema creation.
- CLI with `doctor`, `init-db`, `run --dry-run`.

Validation:

```bash
python -m app.cli doctor
python -m app.cli init-db
```

## Phase 1: Data Intake MVP

Deliver:

- Alipay CSV template and importer.
- Manual candidate universe CSV.
- Manual official fund rule snapshot loader.
- Source log persistence.

Validation:

```bash
python -m app.cli import-alipay --csv data/imports/alipay_positions.csv
python -m app.cli run --slot R7 --dry-run
```

## Phase 2: Metrics And Scoring

Deliver:

- Return windows: 1m, 3m, 10 trading days.
- Drawdown and recovery-time.
- Score model.
- Hard gate enforcement.
- Benchmark comparison.

Validation:

```bash
pytest tests/test_metrics.py tests/test_scoring.py -q
```

## Phase 3: Discipline And Comparison

Deliver:

- Top5 ranking.
- Target weight generator.
- Current vs target deviation.
- Same-day and historical comparisons.
- Rebalance trigger logic.

Validation:

```bash
pytest tests/test_discipline.py tests/test_comparison.py -q
```

## Phase 4: Reporting And Notification

Deliver:

- Markdown run report.
- Urgent/Info/Warn notification templates.
- Mac OS Mail draft or AppleScript-ready command.
- Local notification dry-run hook.

Validation:

```bash
python -m app.cli report --run-id <run_id>
python -m app.cli notify --run-id <run_id> --dry-run
```

## Phase 5: Scheduler Preparation

Deliver:

- launchd plist template.
- Manual scheduler runner.
- Slot mapping with Beijing and Australia/Sydney display.

Validation:

```bash
python -m app.cli run --slot R6 --dry-run
python -m app.cli run --slot R10 --dry-run
```

## First Run Contract

Implement Phases 0-2 only unless user approves expansion. This keeps the first coding run bounded and verifiable.
