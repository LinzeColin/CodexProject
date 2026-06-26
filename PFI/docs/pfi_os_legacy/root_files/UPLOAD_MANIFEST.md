# PFI_OS GitHub Upload Manifest

Target repository: `LinzeColin/PFI_OS`

This folder is a public-safe code snapshot for continuing development.
It intentionally excludes `.env`, `HANDOFF_PRIVATE_LOCAL.md`, runtime SQLite files, generated reports, raw/private data, holdings books, screenshots, imports, caches, and chat inbox files.

Runtime ResearchBus state is excluded from the public repository. Keep real `data/researchBus/ResearchBusSnapshot.json` local/private; use `data/researchBus/ResearchBusSnapshot.example.json` for public tests and documentation.

Recommended first commands:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[app,test,data]"
pytest -q
```

Environment variables for the integrated workspace:

```bash
export PFI_WORKSPACE_ROOT="$HOME/Documents/PFI_OS_Workspace"
export PFI_SYSTEMS_ROOT="$PFI_WORKSPACE_ROOT/systems"
export PFI_REPORT_ROOT="$PFI_WORKSPACE_ROOT/reports"
export PFI_OS_HOME="$PFI_SYSTEMS_ROOT/pfi_os"
export PFI_AI_RESEARCH_ROOT="$PFI_SYSTEMS_ROOT/industry_research"
export PFI_GOVERNMENT_POLICY_ROOT="$PFI_SYSTEMS_ROOT/policy_intelligence"
export PFI_INDUSTRY_REPORT_DIR="$PFI_REPORT_ROOT/industry_research"
```

Execution safety: orchestration defaults to dry-run. Real child-system execution requires explicit local approval via `PFI_ORCHESTRATOR_EXECUTE_ALLOWED=1`; set `PFI_ORCHESTRATOR_APPROVAL_TOKEN` when a stricter token gate is required.

Unified workspace baseline:

```text
systems/finance_ledger/SYSTEM_MANIFEST.json
systems/industry_research/SYSTEM_MANIFEST.json
systems/policy_intelligence/SYSTEM_MANIFEST.json
shared/security/system_permissions.json
shared/schema/system_manifest.schema.json
shared/schema/research_event.schema.json
.github/workflows/smoke.yml
scripts/ciSmoke.sh
```

Finance ledger migration now includes public-safe source assets:

```text
systems/finance_ledger/source/
systems/finance_ledger/samples/
systems/finance_ledger/README.md
```

Industry research migration now includes public-safe source assets:

```text
systems/industry_research/source/
systems/industry_research/source/data/sample/
systems/industry_research/README.md
```

Child-system migration rule: import one system at a time, beginning with source/tests/docs only. Never copy raw bills, holdings, broker-adjacent files, cookies, API keys, Chrome profiles, SQLite runtime databases, generated reports, local outputs, or local logs into the public repo.
