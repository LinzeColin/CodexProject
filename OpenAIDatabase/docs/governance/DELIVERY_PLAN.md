# OpenAIDatabase Delivery Plan

task_count: 8

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
