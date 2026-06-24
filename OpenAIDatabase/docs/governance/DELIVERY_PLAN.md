# OpenAIDatabase Delivery Plan

task_count: 11

## Phase A - Discovery and Baseline

### TASK-OAI-A-001

- task_id: TASK-OAI-A-001
- phase: A
- objective: Complete P10 read-only audit for OpenAIDatabase.
- scope: README, AGENTS, legacy governance files, config, model scripts, focused tests, scoped git log.
- non_scope: raw data, generated outputs, business code edits, dependency installation.
- status: completed
- dependencies: none
- required files: `MODEL_SPEC.md`, `model_registry.yaml`, `formula_registry.yaml`, `parameter_registry.csv`
- acceptance_ids: ACC-OAI-A-001
- test commands: targeted `rg`, scoped `git log --max-count=50 -- OpenAIDatabase`
- evidence: 10 active models and 82 active parameters identified from code/config/tests.
- risk: reading raw memory data would violate scope.
- rollback: no file changes were made during the read-only audit portion.
- target version: 0.1.0
- completed version: 0.1.0

### TASK-OAI-A-002

- task_id: TASK-OAI-A-002
- phase: A
- objective: Complete P11 migration to canonical governance files.
- scope: governance docs, registries, legacy index files, VERSION, CHANGELOG.
- non_scope: scripts, app code, raw data, generated outputs.
- status: completed
- dependencies: TASK-OAI-A-001
- required files: `docs/governance/*`, `VERSION`, `CHANGELOG.md`
- acceptance_ids: ACC-OAI-A-002
- test commands: `python scripts/validate_project_governance.py --project OpenAIDatabase`; `python3 -m py_compile ...`; focused unittest command
- evidence: project validator exit 0; py_compile exit 0; focused unittest exit 0 with 11 tests OK
- risk: declaring undocumented heuristic calibration as fact.
- rollback: remove OpenAIDatabase governance baseline and restore old entry files.
- target version: 0.1.0
- completed version: 0.1.0

### TASK-OAI-A-003

- task_id: TASK-OAI-A-003
- phase: A
- objective: Complete P12 verification for OpenAIDatabase governance.
- scope: validator, focused unit tests, diff check.
- non_scope: fixing business behavior.
- status: completed
- dependencies: TASK-OAI-A-002
- required files: `OpenAIDatabase/docs/governance/*`
- acceptance_ids: ACC-OAI-A-003
- test commands: project validator, focused unittest, `git diff --check`
- evidence: project validator exit 0; focused unittest exit 0; `git diff --check` exit 0
- risk: dependency or generated-data assumptions may block broader acceptance.
- rollback: return to TASK-OAI-A-002 for smallest repair.
- target version: 0.1.0
- completed version: 0.1.0

### TASK-OAI-A-004

- task_id: TASK-OAI-A-004
- phase: A
- objective: Complete P13 promotion from advisory to required after verification passes.
- scope: `governance/projects.yaml` OpenAIDatabase ci_mode only.
- non_scope: other projects and business logic.
- status: completed
- dependencies: TASK-OAI-A-003
- required files: `governance/projects.yaml`
- acceptance_ids: ACC-OAI-A-004
- test commands: project validator and global validator
- evidence: OpenAIDatabase project validator exit 0; global validator exit 0 with advisory warnings only for unmigrated projects; `governance/projects.yaml` marks OpenAIDatabase required
- risk: required mode will block CI on governance drift.
- rollback: set OpenAIDatabase ci_mode back to advisory.
- target version: 0.1.0
- completed version: 0.1.0

## Phase B - Model and Data Specification

### TASK-OAI-B-001

- task_id: TASK-OAI-B-001
- phase: B
- objective: Resolve UNKNOWN calibration evidence for heuristic weights and thresholds.
- scope: memory weight, ROI, activity score, Codex activity, topic/signal rules.
- non_scope: changing active constants without evidence.
- status: blocked
- dependencies: TASK-OAI-A-004
- required files: `parameter_registry.csv`, `formula_registry.yaml`, calibration evidence or explicit governance decision.
- acceptance_ids: ACC-OAI-B-001
- test commands:
- evidence: `parameter_registry.csv` rows with UNKNOWN calibration method reference this task.
- risk: undocumented tuning could be mistaken for empirically validated behavior.
- rollback: keep current heuristic constants and provisional status.
- target version: UNKNOWN (TASK-OAI-B-001)
- completed version:

## Phase C - Implementation

### TASK-OAI-C-001

- task_id: TASK-OAI-C-001
- phase: C
- objective: Future implementation task for controlled agent apply of writeback proposals.
- scope: backend or CLI apply layer, conflict checks, proposal history, rollback point.
- non_scope: direct frontend mutation of active memory.
- status: planned
- dependencies: TASK-OAI-B-001
- required files:
- acceptance_ids: ACC-OAI-C-001
- test commands:
- evidence:
- risk: writeback without conflict checks could corrupt active memory.
- rollback: keep proposal-only frontend contract.
- target version: UNKNOWN (TASK-OAI-B-001)
- completed version:

### TASK-OAI-C-002

- task_id: TASK-OAI-C-002
- phase: C
- objective: Add private three-layer context source, ChatGPT/Codex personalization exports, Codex config, on-demand resource routing, evaluation harness, and four run-log categories.
- scope: `config/context_sources`, `config/codex`, `config/evaluation`, `docs/PERSONAL_CONTEXT_ARCHITECTURE.md`, `context/`, `data/derived/personalization`, `data/run_logs`, scripts, focused tests, governance registries.
- non_scope: raw exports, plaintext secrets, business runtime behavior outside personalization sync, other projects.
- status: completed
- dependencies: TASK-OAI-A-004
- required files: `config/context_sources/three_layer_context.json`, `config/context_sources/resource_routes.json`, `config/codex/config.template.toml`, `config/codex/project.config.toml`, `config/evaluation/personalization_harness.json`, `data/derived/personalization/*`, `data/run_logs/*`
- acceptance_ids: ACC-OAI-C-002
- test commands: `python3 scripts/build_personalization_exports.py --database-dir .`; `python3 scripts/route_agent_resources.py --database-dir . --intent startup`; `python3 scripts/evaluate_personalization_context.py --database-dir .`; `python3 -m unittest tests.test_personalization_architecture -q`
- evidence: personalization export PASS, startup route PASS, evaluation harness PASS with no failures, focused unittest added.
- risk: generated export is redacted derived context but pattern scan is not a full secret scanner.
- rollback: remove `TASK-OAI-C-002` files and revert VERSION, CHANGELOG, and governance entries to 0.1.0.
- target version: 0.2.0
- completed version: 0.2.0

### S3PDT01

- task_id: S3PDT01
- phase: S3PD
- objective: Verify OpenAIDatabase private import, redaction, Git leakage, and deletion-recovery contracts with synthetic private data.
- scope: `scripts/privacy_guard.py`, `.gitignore`, focused unittest, privacy scan evidence, governance records.
- non_scope: real raw exports, cookies, browser profiles, plaintext secrets, production private data, delivery readiness approval.
- status: completed
- dependencies: S2PCT03
- required files: `scripts/privacy_guard.py`, `tests/test_s3pdt01_privacy.py`, `governance/stage_gates/s3pd/privacy_scan.log`
- acceptance_ids: ACC-S3PDT01
- test commands: bundled-python focused unittest; bundled-python privacy scan; `git ls-files` raw/private check; `git check-ignore` raw/private patterns.
- evidence: focused unittest ran 3 tests OK; privacy scan PASS with no tracked raw private files and no high-risk secret hits; raw/private paths are gitignored.
- risk: synthetic privacy proof does not approve real raw export ingestion or production memory safety.
- rollback: remove privacy guard, S3PDT01 tests/evidence, governance records, and `.gitignore` additions.
- target version: 0.2.0
- completed version: 0.2.0

## Phase D - Verification and Hardening

### TASK-OAI-D-001

- task_id: TASK-OAI-D-001
- phase: D
- objective: Run full app, local launcher, Cloudflare, and visual acceptance gates after governance baseline.
- scope: Memory Atlas build, release audit, visual acceptance, app runtime, Cloudflare preflight.
- non_scope: installing dependencies in this baseline run.
- status: planned
- dependencies: TASK-OAI-A-004
- required files:
- acceptance_ids: ACC-OAI-D-001
- test commands:
- evidence:
- risk: focused tests are not full release readiness.
- rollback: keep required governance gate but do not claim full release.
- target version: 0.1.0
- completed version:

## Phase E - Delivery and Operation

### TASK-OAI-E-001

- task_id: TASK-OAI-E-001
- phase: E
- objective: Maintain governance drift checks for OpenAIDatabase in required mode.
- scope: governance validator and model behavior globs.
- non_scope: unrelated project migration.
- status: planned
- dependencies: TASK-OAI-A-004
- required files: `governance/projects.yaml`, `.github/workflows/project-governance.yml`
- acceptance_ids: ACC-OAI-E-001
- test commands:
- evidence:
- risk: changing model behavior without registry updates must fail validation in CI.
- rollback: only downgrade to advisory with explicit governance decision.
- target version: 0.1.0
- completed version:
