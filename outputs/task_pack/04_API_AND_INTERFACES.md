# 04 API And Interfaces

## CLI Interface

Recommended commands:

```bash
python -m app.cli init-db
python -m app.cli import-alipay --csv data/imports/alipay_positions.csv
python -m app.cli run --slot R7 --dry-run
python -m app.cli run --at "2026-06-15T14:30:00+08:00" --dry-run
python -m app.cli report --run-id <run_id>
python -m app.cli notify --run-id <run_id> --dry-run
python -m app.cli mail-smoke --json
python -m app.cli doctor
```

## Adapter Contracts

### Market Data Adapter

```python
class MarketDataAdapter:
    name: str
    priority: int

    def healthcheck(self) -> dict: ...
    def fetch_kline(self, asset_code: str, start: str, end: str, interval: str) -> list[dict]: ...
    def fetch_quote(self, asset_code: str) -> dict: ...
    def fetch_index_returns(self, index_code: str, windows: list[str]) -> dict: ...
```

MVP behavior:

- moomoo adapter is preferred.
- If moomoo/OpenD is unavailable, mark source unavailable and continue only if fallback is enabled.
- Fallback cannot create Action-Ready recommendations by itself.

### Alipay Importer

```python
class AlipayImporter:
    def import_positions_csv(self, path: str, run_id: str) -> list[dict]: ...
    def validate_positions(self, rows: list[dict]) -> list[dict]: ...
```

MVP behavior:

- CSV/template import only.
- Browser-assisted extraction is V2.

### Fund Rule Adapter

```python
class FundRuleAdapter:
    def load_manual_snapshot(self, path_or_url: str) -> dict: ...
    def normalize_fee_schedule(self, raw: dict) -> dict: ...
    def normalize_trade_rule(self, raw: dict) -> dict: ...
```

MVP behavior:

- Accept manual official-source snapshots and structured YAML/CSV.
- Store source chain.

### Notifier

```python
class Notifier:
    def render_mail(self, run_id: str, severity: str) -> str: ...
    def create_mail_draft(self, title: str, body: str, recipient: str) -> dict: ...
    def run_mail_smoke(self, send: bool = False, confirm_real_send: str = "") -> dict: ...
    def send_local_notification(self, title: str, body: str) -> dict: ...
```

MVP behavior:

- Generate mail body files.
- Generate AppleScript command or `.eml` draft.
- `mail-smoke` writes a draft and audit artifact by default.
- Real sending requires both `SERENITY_MAIL_SEND_ENABLED=true` and explicit `--send --confirm-real-send SEND`.

## Output Interface

Every run writes:

```text
data/reports/<run_id>_report.md
data/notifications/<run_id>_<severity>.md
data/exports/<run_id>_top5.csv
data/exports/<run_id>_recommendations.csv
```
