# OpenAIDatabase Governance Model Specification

task_id: TASK-OAI-C-002
evidence_level: EXTRACTED unless marked otherwise
governance_spec_version: 1.0.0
model_count: 12
formula_count: 12
parameter_count: 99
task_count: 16

## A. Model Overview

This file is the human-readable governance companion for the machine registries
in this directory. The machine facts are authoritative for model, formula,
parameter, task, version, and traceability counts.

| Model ID | Name | Kind | Status | Version | Implementation |
| --- | --- | --- | --- | --- | --- |
| MOD-001 | Memory candidate classification and tiering | deterministic_rule_engine | active | memory-candidate-v0 | `skills/openai-memory-analysis/scripts/openai_memory_analysis.py:512` |
| MOD-002 | Secret redaction and sensitivity policy | risk_model | active | redaction-policy-v0 | `skills/openai-memory-analysis/scripts/openai_memory_analysis.py:51` |
| MOD-003 | Active memory promotion and retrieval weight | deterministic_rule_engine | active | active-memory-v0 | `skills/openai-memory-analysis/scripts/openai_memory_analysis.py:1701` |
| MOD-004 | Read-only SQLite search and fetch | retrieval_model | active | read-only-retrieval-v0 | `skills/openai-memory-analysis/scripts/openai_memory_analysis.py:2055` |
| MOD-005 | Memory Atlas weight score | scoring_model | active | atlas-weight-v0 | `scripts/build_memory_atlas_data.py:380` |
| MOD-006 | ROI leverage and staleness score | scoring_model | active | roi-leverage-v0 | `scripts/build_memory_atlas_data.py:387` |
| MOD-007 | Contribution activity score | business_calculation_model | active | activity-score-v2 | `scripts/build_memory_atlas_data.py:462` |
| MOD-008 | Codex local behavior summary | heuristic_algorithm | active | codex-sync-v0 | `scripts/sync_codex_memory_data.py:279` |
| MOD-009 | Data source registry and public snapshot gate | deterministic_rule_engine | active | source-registry-v0 | `scripts/audit_memory_atlas_acceptance.py:86` |
| MOD-010 | Writeback proposal version chain | deterministic_workflow_model | active | writeback-proposal-v0 | `apps/memory-atlas/src/App.tsx:2328` |
| MOD-011 | Personalization export and resource routing | deterministic_workflow_model | active | personalization-routing-v0 | `scripts/build_personalization_exports.py:1` |
| MOD-MACDATA-PROM2-001 | Device preflight and archive cleanup policy | deterministic_workflow_model | active | macdata-prom2-v1 | `macdata/proM2/scripts/run_controlled_cycle.py:1` |

Non-use cases:

- Technology names such as React, Three.js, SQLite, Vite, and Cloudflare Pages are not models by themselves.
- Planned emotion or friction scoring is not active. The old parameter note calls it current未实现, so it remains outside the active registry.
- Provider names are not business models unless a routing/fallback rule changes behavior.

## B. Assumptions

| Assumption ID | Fact Level | Statement | Validation or Falsification |
| --- | --- | --- | --- |
| ASM-001 | EXTRACTED | The repository is local-first and review-gated. Raw exports, plaintext secrets, cookies, sessions, browser profiles, and saved-memory writes are outside allowed behavior. | Try to trace any active path that commits raw exports or direct saved-memory writes; current hard boundaries reject it. |
| ASM-002 | EXTRACTED | Active models are deterministic scripts or frontend rules, not trained ML models. | Search for training, fitted weights, model artifacts, or calibration datasets; no evidence found in scoped files. |
| ASM-003 | EXTRACTED | Memory Atlas public snapshot is redacted and read-only. Frontend writeback is proposal-only. | `audit_memory_atlas_release.py` fails if the contract is violated. |
| ASM-004 | EXTRACTED | Codex local sync emits redacted summaries only, without raw transcripts, plaintext secrets, or local absolute paths. | `tests/test_codex_memory_sync.py` asserts redaction. |
| ASM-005 | EXTRACTED | Planned data sources must be registered and must not create fake activity. | `audit_memory_atlas_acceptance.py` checks planned source status and selector visibility. |
| ASM-006 | UNKNOWN | Weight and threshold calibration is not evidenced by labeled data or out-of-sample experiments. | Resolve under `TASK-OAI-B-001` with calibration evidence or explicit decision to keep heuristic constants. |
| ASM-007 | EXTRACTED | Future agents need deterministic routing from redacted memory sources into ChatGPT/Codex personalization exports and must update profile, preference, taste, history, and pattern files together when those concepts change. | `evaluate_personalization_context.py` checks required files, sections, sync targets, and log categories. |

## C. Functions and Formulas

The exact expressions, variables, units, domains, missing policies, constraints,
fallback behavior, implementation refs, and test refs are maintained in
`formula_registry.yaml`.

Summary:

- FORM-001: Candidate category, importance, validity, confidence, tier, dedupe, and pending status.
- FORM-002: Secret and PII redaction, sensitivity assignment, secret_ref, and credential policy.
- FORM-003: Active memory tier normalization, retrieval weight, curation override, and use constraints.
- FORM-004: Read-only search/fetch SQL index, query filtering, secret exclusion, and fetch errors.
- FORM-005: Memory Atlas weight score and visual mappings.
- FORM-006: ROI leverage score, staleness status, and recommended action.
- FORM-007: Contribution activity score and 0-5 level normalization.
- FORM-008: Codex redacted session activity and recommendation summaries.
- FORM-009: Data source registry, homepage source gate, and static summary privacy policy.
- FORM-010: Writeback proposal revision, diff, rollback, and controlled apply gate.
- FORM-011: Three-layer context to ChatGPT/Codex personalization export, route selection, evaluation, and run logging.
- FORM-MACDATA-PROM2-001: proM2 MacData preflight, GitHub archive verification, and post-upload cleanup gate.

## D. Parameters

`parameter_registry.csv` is the canonical parameter ledger. Defaults,
initial/prior values, active values, weights, ranges, source/rationale,
calibration method, sensitivity, code refs, config refs, and test refs are
stored per `PARAM-xxx`.

Important distinctions:

- Default values are code or config fallback values.
- Initial/prior values are marked `NOT_APPLICABLE` where the model has no
  training or fitting phase.
- Active values are current constants or config values.
- Calibration is `UNKNOWN` where the repository has no empirical calibration
  evidence; those rows link to `TASK-OAI-B-001`.

## E. Methodology

The current methodology is deterministic local processing:

- Use regex and rule maps for memory candidate extraction and classification.
- Use explicit redaction and fail-closed secret policies before persistence.
- Use SQLite only as a read-only index over redacted active and pending memory.
- Use fixed scoring formulas for Atlas node weight, ROI leverage, and activity heat.
- Use source registry gates before adding new platform sources.
- Use frontend proposal JSON for writeback requests and require controlled agent/human apply before memory mutation.
- Use a three-layer context source and deterministic resource routes before
  broad search.
- Generate ChatGPT and Codex personalization exports from redacted derived
  memory after every meaningful sync.
- Verify personalization exports with the evaluation harness and preserve four
  redacted run-log categories.

Alternative methods not currently evidenced:

- Labeled supervised classification.
- Embedding/vector similarity scoring.
- Empirical A/B calibration of memory weight or ROI coefficients.
- Sentiment/emotion scoring.

## F. Strategy Logic

Signal formation:

- Candidate signals come from trigger regex categories.
- Atlas signals come from memory tier, importance, confidence, category, date, and source registry metadata.
- Codex behavior signals come from redacted local session metadata, tool counts, topic rules, and preference signal rules.
- Personalization export signals come from Core Profile, active memory,
  Codex recommendations, behavior snapshots, and resource-route config.

Gates:

- Raw exports and plaintext secrets are excluded from committed outputs.
- `review_status=pending` blocks treating generated candidates as accepted memories.
- `source_contract.mode=public_redacted_read_only_visualization` blocks raw public snapshots.
- Writeback proposals remain `draft_pending_agent_apply`.
- Future agents must update mapped source files before regenerating
  personalization exports when profile, preference, taste, history, or pattern
  facts change.

Fallback:

- Unknown memory tier, importance, or confidence uses numeric fallback scores.
- Missing search index triggers local rebuild from redacted JSONL.
- Missing Codex fields become empty, redacted, or hashed labels.
- Missing route intent returns a fail result with valid intents; missing
  required export sections fails evaluation.

Stop conditions:

- Raw unredacted data entering GitHub.
- Direct frontend mutation of active memory.
- Planned data sources producing fake records.
- Secret data returned through search/fetch.

## G. Validation

Current focused validation commands for this baseline:

- `python scripts/validate_project_governance.py --project OpenAIDatabase`
- `python scripts/validate_project_governance.py --all`
- `python3 -m unittest tests.test_openai_memory_analysis tests.test_memory_atlas_data tests.test_codex_memory_sync tests.test_memory_atlas_release_audit -q`
- `python3 -m unittest tests.test_personalization_architecture -q`
- `python3 scripts/build_personalization_exports.py --database-dir .`
- `python3 scripts/route_agent_resources.py --database-dir . --intent startup`
- `python3 scripts/evaluate_personalization_context.py --database-dir .`
- `git diff --check`

Release gate for this governance baseline:

- Governance validator passes with zero errors.
- Focused deterministic tests pass or any environment-only blocker is recorded.
- No OpenAIDatabase business logic diff is present.
- `governance/projects.yaml` marks OpenAIDatabase `required` only after validation.

Uncovered or unresolved:

- `TASK-OAI-B-001`: calibration evidence for heuristic weights and thresholds.
- `TASK-OAI-D-002`: authorized Cloudflare Pages live upload and Access verification after credentials/env are available.
- `TASK-OAI-D-003`: completed CI evidence-schema and cross-platform path repair; it does not change delivery readiness.
