# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:7ded278950b6c173d70973ec00eb0c80286b8ff28900e1ed583c31a93b4491f3`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:governance/run_manifests/GOV-REVIEW6-FINAL-PORTFOLIO-001.json`

## Current State

- Project: `OpenAIDatabase`
- Path: `OpenAIDatabase`
- Product version: `0.2.0`
- Phase/Gate: `B / GOV-SEMANTIC-OAIDB-in-progress`
- Models/Formulas/Parameters total: `11 / 11 / 94`
- Active formulas/parameters: `11 / 94`
- Machine checked formulas/parameters: `10 / 28`

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
- Release gate: `MEMORY-ATLAS-CLOUDFLARE-LIVE-AUTH-REQUIRED`
- Latest remediation task: `TASK-OAI-D-001` completed local Memory Atlas release/visual/acceptance/Cloudflare preflight evidence
- Next executable task: `TASK-OAI-D-002`
- Pending/stale events: `7`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `6`
- Unresolved fact IDs: `6`

## Latest Other8 Evidence

- `S3PDT01`: private import, redaction, Git leakage, and raw-source deletion recovery contracts passed focused local evidence.
- Evidence ref: `governance/stage_gates/s3pd/privacy_scan.log`.
- Boundary: synthetic private data only; no real raw exports, cookies, browser profiles, plaintext secrets, production private data, owner data ingestion, or delivery-readiness approval was used or implied.

## Latest Memory Atlas Deployment Evidence

- `TASK-OAI-D-001`: main-branch merge, data-guide UI contract, snapshot refresh, release audit, visual acceptance, app acceptance, Cloudflare Pages + Access preflight, and OpenAIDatabase unittest gates passed locally.
- Evidence refs: `OpenAIDatabase/scripts/audit_memory_atlas_visual_acceptance.py`, `OpenAIDatabase/scripts/preflight_cloudflare_pages_access.py`, `OpenAIDatabase/tests/test_memory_atlas_visual_acceptance.py`.
- Boundary: live Cloudflare Pages upload and Access verification did not run because local Wrangler is unauthenticated and live Cloudflare env vars are absent.
