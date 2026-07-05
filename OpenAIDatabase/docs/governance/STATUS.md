# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:bbec5b8736622a8f1e07d68e21e6d78e4c05d1ac941d8664304a25c5fa98c84e`
- snapshot_event_time: `2026-06-26T21:56:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `OpenAIDatabase`
- Path: `OpenAIDatabase`
- Product version: `0.2.0`
- Phase/Gate: `D / S5PB-GATE-IN-PROGRESS; MEMORY-ATLAS-CLOUDFLARE-LIVE-AUTH-REQUIRED`
- Latest maintenance task: `TASK-OAI-D-003 / OpenAIDatabase CI evidence-schema repair`
- Latest controlled sub-workflow setup: `MACDATA-PROM2-SETUP-20260705 / proM2 MacData archive and cleanup automation`
- Models/Formulas/Parameters total: `12 / 12 / 98`
- Active formulas/parameters: `12 / 98`
- Machine checked formulas/parameters: `10 / 28`

## macdata proM2 Controlled Archive

- Status: `in_progress`
- Device truth: `MacBook Pro / Mac14,5 / Apple M2 Max / 32GB`
- Archive branch: `macdata-proM2`
- Cleanup gate: remote upload hash verification must pass before macdata retention cleanup or Docker/Homebrew/system/project cache cleanup runs.
- Secret boundary: API keys, tokens, passwords, cookies, sessions, Keychain, shell history, full environment dumps, and `.env` raw content are out of scope.

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `OpenAIDatabase/docs/governance/parameter_registry.csv, OpenAIDatabase/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `OpenAIDatabase/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `OpenAIDatabase/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `OpenAIDatabase/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `OpenAIDatabase/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `OpenAIDatabase/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `OpenAIDatabase/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `S5PB-GATE-IN-PROGRESS; MEMORY-ATLAS-CLOUDFLARE-LIVE-AUTH-REQUIRED`
- Next executable task: `TASK-OAI-B-001`; `TASK-OAI-D-003` is a completed CI repair and does not change delivery readiness.
- Pending/stale events: `9`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `6`
- Unresolved fact IDs: `7`
