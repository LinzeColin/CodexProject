# PFI_OS Systems Workspace

This directory is the controlled landing zone for child systems that will be migrated into PFI_OS one at a time.

Current phase: staged source migration. Finance Ledger, Industry Research, and Policy Intelligence have moved past manifest-only into source/tests/docs migration.

Do not copy private runtime data into this directory. Source code, tests, docs, public-safe samples, and sanitized handoff artifacts are allowed. Raw bills, holdings, broker-adjacent files, SQLite runtime databases, cookies, API keys, Chrome profiles, screenshots, and local logs are excluded by default.

## Registered Systems

| System | Target directory | Current phase | Next migration step |
| --- | --- | --- | --- |
| Finance Ledger / Consumption Analysis | `systems/finance_ledger` | source/tests/docs migrated | add PFI_OS adapter and run macOS acceptance after unified UI Shell |
| Industry Research / Trading Strategy Advice | `systems/industry_research` | source/tests/docs migrated | add PFI_OS adapter and keep report generation fail-closed |
| Policy Intelligence | `systems/policy_intelligence` | source/tests/docs migrated | add PFI_OS adapter and restore private-runtime automation freshness |

Each system must keep a `SYSTEM_MANIFEST.json` aligned with `shared/schema/system_manifest.schema.json`.

`ResearchBus` consumes these manifests through `pfi_os.integrations.workspace_systems`.
The adapter publishes compact status only: system id, migration state, relative roots,
sample count, capped entrypoints/verifications/next actions, and data policy. It does
not publish legacy absolute roots or private runtime outputs.
