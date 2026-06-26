# PFI Data Boundaries

Version: PFI-001

PFI OS is local-first. The Git repository stores code, schemas, templates, and
small sanitized fixtures only. Runtime data lives outside the repository under
`$PFI_OS_DATA_HOME`.

## Data Domains

| Domain | Definition | Examples | Git policy |
| --- | --- | --- | --- |
| `PUBLIC_SHARED_RAW` | Public raw material without personal data | official API JSON, public HTML, public PDF, public CSV | Small sanitized fixtures only |
| `PUBLIC_SHARED_CANONICAL` | Standardized public facts | market bars, financial facts, macro series, policy facts | Schema and fixture only |
| `PRIVATE_USER` | User private source data | holdings, trades, private reports, notes, preferences | Never commit |
| `PRIVATE_DERIVED` | Outputs combining public and private data | portfolio risk, personalized recommendations, optimization | Never commit |
| `SECRET` | Credentials and access material | API keys, cookies, sessions, tokens, passwords | Never commit |
| `EPHEMERAL` | Rebuildable runtime state | cache, temp downloads, worker logs, generated runtime summaries | Never commit except explicit sanitized fixture |

## Default Data Home

```text
$PFI_OS_DATA_HOME/
├── shared/
│   ├── raw/
│   ├── canonical/
│   └── metadata/
├── private/
│   ├── operational/
│   │   └── pfi.sqlite
│   ├── portfolio/
│   ├── documents/
│   ├── notes/
│   ├── models/
│   └── derived/
├── cache/
├── jobs/
├── exports/
├── backups/
└── logs/
```

## Repository Rules

- Do not commit real holdings, real trades, account identifiers, private
  documents, SQLite runtime databases, local logs, screenshots, credentials, or
  generated private-derived outputs.
- Do not write private data into `shared/`.
- Shared-domain jobs must not read `private/` unless using an explicit read-only
  domain interface.
- Research and strategy tests use sanitized fixtures by default.
- Exports must label their data classification.
- CI or release checks must include secret scans and private path scans.

## Legacy Gap

The legacy repository currently contains tracked `data/**` runtime artifacts.
PFI-002 must remove active runtime artifacts from Git while preserving safe
schema, examples, `.gitkeep`, and documented migration notes.
