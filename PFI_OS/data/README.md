# Data Directory Boundary

This public repository includes only small continuity snapshots required for deterministic local development.

Included examples:

- `data/marketEvents`
- `data/dataLake`
- `data/replay`
- `data/entityRegistry`
- selected command-center JSON/CSV/MD summaries

Excluded local/private data:

- holdings books and imports,
- raw portfolio videos and extracted frames,
- local SQLite runtime databases,
- full report-decision queues containing local paths,
- system-audit files containing local user paths,
- PDFs generated from private runs,
- runtime logs, lock files, and process ids.

Recreate private/runtime data locally from trusted sources. Do not upload credentials, account exports, raw brokerage screenshots, or local report folders to this public repository.
