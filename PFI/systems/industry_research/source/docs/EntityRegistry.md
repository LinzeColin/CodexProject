# AI-Research-System Entity Registry / Alias Map

## Purpose

Entity Registry unifies the objects used by AI-Research-System so that reports, holdings, validation tasks, policy events, PFIOS results, and manual-review items can refer to stable IDs instead of fragile names.

It answers:

> Are “农业ETF天弘”, `512620`, `SH.512620`, policy-related symbols, validation tasks, reports, and review items mapped into a traceable entity system?

The registry is read-only. It does not refresh market data, open moomoo, parse new Alipay uploads, submit ResearchBus requests, edit reports, or execute trades.

## Command

```bash
python3 -m src.cli entity-registry-audit --date 2026-06-06
python3 -m src.cli entity-registry-audit --date 2026-06-06 --json
```

Recommended run order:

```bash
python3 -m src.cli data-trust-audit --date 2026-06-06
python3 -m src.cli reconciliation-audit --date 2026-06-06
python3 -m src.cli manual-review-audit --date 2026-06-06
python3 -m src.cli entity-registry-audit --date 2026-06-06
```

## Outputs

Outputs are written to:

```text
data/report_artifacts/system_audit/
```

Files:

- `entity_registry_YYYY-MM-DD.json`
- `entity_registry_YYYY-MM-DD.csv`
- `alias_map_YYYY-MM-DD.csv`
- `entity_registry_YYYY-MM-DD.md`
- `entity_registry_YYYY-MM-DD.pdf`

The PDF is the formal audit report. JSON and CSV are machine-readable inputs for dashboards, ResearchBus integration, and later evidence matrix layers.

## Entity Types

Current v1 emits:

- `FinancialInstrument`
- `Report`
- `DataSource`
- `PolicyDocument`
- `Account`
- `System`
- `Strategy`
- `ValidationTask`
- `ValidationRun`
- `ReviewItem`
- `SystemArtifact`

## Alias Types

Alias Map may include:

- `canonical_name`
- `symbol`
- `code`
- `quote_code`
- `english_name`
- `chinese_name`
- `research_group`
- `source_url`
- `holding_id`
- `run_id`
- `result_id`
- `task_id`
- `file_name`
- `week_folder`
- `priority`
- `status`

## Alias Scope

Alias hardening v1 adds `alias_scope`.

The same text can legitimately mean different things in different entity types. Example: `Alipay` can be a system/account source while `alipay` can also appear as a PFIOS strategy id. Those rows should not become a false conflict merely because the normalized text is identical.

Scope rules:

- Non-financial entities use their `entity_type` as alias scope.
- Financial instruments use `FinancialInstrument:<market>` as alias scope.
- ResearchBus rows with `market=CN` are normalized with local watchlist market hints when the same symbol already exists as `SSE` or `SZSE`.

This preserves real conflicts inside the same scope while avoiding false conflicts across unrelated types or market vocabularies.

## Normalization

Aliases are normalized by:

- Unicode NFKC normalization
- casefold
- whitespace removal
- common punctuation removal

Example:

| Raw Alias | Normalized |
| --- | --- |
| `SH.512620` | `sh512620` |
| `农业 ETF 天弘` | `农业etf天弘` |
| `RunMetadata7_04062026` | `runmetadata704062026` |

## Conflict Rule

If the same `alias_scope + normalized_alias` maps to more than one `entity_id`, the alias is marked `Conflict`.

Conflict does not auto-merge entities. It is a review signal because automatic merging can corrupt evidence chains.

2026-06-06 hardening result:

- Previous false conflicts: `18`
- Current conflicts after scope and market normalization: `0`
- Entity Registry status: `Pass`

## Validation

Recommended validation:

```bash
PYTHONPATH=. python3 -m pytest tests/test_entity_registry.py -q
PYTHONPATH=. python3 -m pytest tests/test_entity_registry.py tests/test_manual_review.py tests/test_reconciliation.py tests/test_data_trust.py tests/test_research_bus_bridge.py -q
python3 -m src.cli entity-registry-audit --date 2026-06-06 --json
```

Use the Codex bundled Python runtime for tests when system Python lacks `pytest`. Use system Python for CLI generation if bundled Python lacks `certifi`.
