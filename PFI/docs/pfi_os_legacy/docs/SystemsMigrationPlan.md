# PFI_OS Systems Migration Plan

Last updated: 2026-06-16 Australia/Sydney

## Goal

Move PFI_OS from a single PFIOS-centered workspace toward a product-grade research operating system with child systems registered under `systems/`, shared permission rules under `shared/security`, and common schemas under `shared/schema`.

This plan intentionally migrates one system at a time. The first phase registered manifests and CI smoke gates. The second phase has migrated `finance_ledger`, `industry_research`, and `policy_intelligence` source packages. It does not copy private ledgers, holdings, SQLite runtime databases, cookies, API keys, or raw logs.

Update 2026-06-16: the three migrated systems now have a low-token workspace manifest adapter. `ResearchBus` can register `finance_ledger`, `industry_research`, and `policy_intelligence` as canonical workspace systems without reading private runtime data.

## Current Phase

| System | Target | Phase | Source of truth before migration |
| --- | --- | --- | --- |
| Finance Ledger / Consumption Analysis | `systems/finance_ledger` | source/tests/docs migrated | `/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-20250604` |
| Industry Research / Trading Strategy Advice | `systems/industry_research` | source/tests/docs migrated | `/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-codex/outputs/AI-Research-System` |
| Policy Intelligence / Government Document Interpretation | `systems/policy_intelligence` | source/tests/docs migrated | `/Users/linzezhang/Documents/Codex/2026-06-03/sop-skill-pursuing-goal-diff-step/outputs/source-authority-registry` |

## Shared Contracts

- Permission matrix: `shared/security/system_permissions.json`
- System manifest schema: `shared/schema/system_manifest.schema.json`
- Research event schema: `shared/schema/research_event.schema.json`
- Smoke workflow: `.github/workflows/smoke.yml`
- Local smoke command: `scripts/ciSmoke.sh`
- Source-thread routing manifest: `docs/ThreadHandshakeManifest.md`

## Migration Order

1. `finance_ledger`
   - Status: source/tests/docs/configs/assets migrated under `systems/finance_ledger/source`.
   - Excluded all raw bills, ledger SQLite, transaction-detail HTML, private review data, generated outputs, and runtime work directories.
   - First acceptance gate: source imports cleanly and tests run against synthetic or sanitized fixtures.
   - Current evidence: `scripts/ciSmoke.sh` includes finance ledger compile and parser/classifier/reconciliation smoke tests.
   - Next acceptance gate: add an PFI_OS adapter that publishes summarized ledger metrics to ResearchBus without raw transaction rows.

2. `industry_research`
   - Status: source/tests/docs/configs/prompts/templates/scripts and sanitized samples migrated under `systems/industry_research/source`.
   - Excluded Alipay/private holdings, moomoo local database, cookies, API keys, real account data, report artifacts, generated PDFs, and runtime logs.
   - First acceptance gate: full migrated test suite passed locally with `198 passed, 9 subtests passed`.
   - Current evidence: `scripts/ciSmoke.sh` includes industry compile, focused tests, and CLI help.
   - Next acceptance gate: add an PFI_OS adapter that publishes summarized report readiness and validation tasks to ResearchBus without raw account artifacts.

3. `policy_intelligence`
   - Status: source/tests/docs/config/rules/scripts and sanitized sample fixtures migrated under `systems/policy_intelligence/source`.
   - Excluded `~/.policy-intelligence`, Chrome profile state, cookies, platform auth, API keys, raw HTML dumps, local logs, SQLite runtime databases, snapshots, reports, and automation run state.
   - First acceptance gate: compile, script syntax, focused tests, and CLI help are covered by `scripts/ciSmoke.sh`.
   - Next acceptance gate: add an PFI_OS adapter that publishes policy readiness, queue, external-reference-gap, and quality-gate summaries to ResearchBus without raw document text or auth paths.

## Public Repository Boundary

Allowed:

- Source code, tests, docs, public-safe configs, schemas, manifests, sanitized samples, and public-safe handoff summaries.

Denied by default:

- `*.sqlite`, `*.db`, raw bills, holdings, screenshots, cookies, API keys, Chrome profiles, local logs, broker-adjacent state, and app bundles that embed private absolute paths.

## MacOS Acceptance Target

Final macOS acceptance is not achieved until all of these are verified on this Mac:

1. `/Applications/PFI_OS.app`, `~/Desktop/PFI_OS.app`, and `~/Downloads/PFI_OS.app` launch the current PFI_OS workspace.
2. UI shell opens without stale paths and clearly shows child-system readiness.
3. Start, stop, cache cleanup, auto wake/run/shutdown, and smoke tests work from the app or documented scripts.
4. All child systems have fail-closed permissions and public/private data boundaries.
5. GitHub contains enough source, docs, schemas, and handoff state for a new agent to continue without local chat history.
