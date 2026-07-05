# OpenAIDatabase Delivery Plan

task_count: 14

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
- objective: Run Memory Atlas main-branch release acceptance after data-guide rename, Codex auto-update scheduling, and deployment snapshot refresh.
- scope: main branch merge, redacted visualization snapshot, frontend build, release audit, visual acceptance, Memory Atlas acceptance, Cloudflare Pages + Access preflight, OpenAIDatabase unit tests.
- non_scope: live Cloudflare Pages upload without credentials, Cloudflare Access policy mutation, raw exports, plaintext secrets, production readiness promotion.
- status: completed
- dependencies: TASK-OAI-A-004
- required files: `apps/memory-atlas/src/App.tsx`, `scripts/install_codex_weekly_sync.py`, `scripts/run_codex_memory_auto_update.py`, `data/derived/visualization/memory_atlas.json`, `tests/test_memory_atlas_visual_acceptance.py`
- acceptance_ids: ACC-OAI-D-001
- test commands: snapshot build, `npm ci`, `npm run lint`, `npm run build`, release audit, visual acceptance, Memory Atlas acceptance, Cloudflare preflight, unittest discover, deploy dry-run, wrangler auth check.
- evidence: local gates passed; deploy dry-run command contract valid; live deploy blocked by missing Wrangler authentication and Cloudflare live env vars.
- risk: live Cloudflare upload and Access verification remain unproven.
- rollback: revert main merge/snapshot/test/governance commits and roll back Pages deployment if a live deploy later exists.
- target version: 0.2.0
- completed version: 0.2.0

### TASK-OAI-D-002

- task_id: TASK-OAI-D-002
- phase: D
- objective: Execute authorized Cloudflare Pages direct upload and verify Cloudflare Access protection for Memory Atlas.
- scope: Wrangler authentication, Cloudflare Pages direct upload, Access challenge verification, allowed-user app load, `/memory_atlas.json` live fetch, sanitized live evidence.
- non_scope: committing Cloudflare tokens, publishing raw exports, bypassing Access, adding finance/trading agent write permissions.
- status: blocked
- dependencies: TASK-OAI-D-001
- required files: `docs/MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md`, `config/cloudflare/live_deploy_evidence.template.json`
- acceptance_ids: ACC-OAI-D-002
- test commands: authorized deploy helper, `npx wrangler pages deployment list --project-name openai-memory-atlas`, strict goal-completion audit with sanitized live evidence.
- evidence: blocked because local wrangler is not authenticated and `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `MEMORY_ATLAS_ACCESS_HOSTNAME`, and `MEMORY_ATLAS_ALLOWED_EMAIL` are absent.
- risk: without live Access verification, deployment cannot be treated as protected or production-ready.
- rollback: do not execute live upload until auth/env exists; if a live deploy later fails, roll back to the previous Pages deployment version.
- target version: 0.2.0
- completed version:

### TASK-OAI-D-003

- task_id: TASK-OAI-D-003
- phase: D
- objective: Repair OpenAIDatabase CI evidence-schema compatibility and cross-platform deterministic script output.
- scope: legacy `sync_runs` compatibility, future sync log task-run schema, POSIX generated paths, `openssl` missing fail-closed handling, OpenAIDatabase CI tests.
- non_scope: raw exports, plaintext secrets, live Cloudflare deployment, Access mutation, model calibration, delivery readiness promotion.
- status: completed
- dependencies: TASK-OAI-D-001
- required files: `scripts/evaluate_personalization_context.py`, `scripts/sync_codex_memory_data.py`, `scripts/build_agent_context_pack.py`, `scripts/deploy_memory_atlas_cloudflare.py`, `skills/openai-memory-analysis/scripts/openai_memory_analysis.py`
- acceptance_ids: ACC-OAI-D-003
- test commands: OpenAIDatabase unittest discover, personalization export, startup route, evaluator, py_compile, changed-only governance validation.
- evidence: local OpenAIDatabase unittest discover ran 44 tests OK; export/route/evaluator/py_compile passed; governance changed-only rerun pending after this document sync.
- risk: historical sync rows remain legacy compatibility evidence; live Cloudflare delivery is still blocked.
- rollback: revert TASK-OAI-D-003 scripts and governance records.
- target version: 0.2.0
- completed version: 0.2.0

## Phase E - Delivery and Operation

### MACDATA-PROM2-SETUP-20260705

- task_id: MACDATA-PROM2-SETUP-20260705
- phase: MACDATA
- objective: Install proM2 MacData controlled archive workflow using the local Apple M2 Max MacBook Pro as device truth.
- scope: `OpenAIDatabase/macdata/proM2`, OpenAIDatabase governance records, GitHub archive branch `macdata-proM2`.
- non_scope: Time Machine, iCloud, API keys, tokens, passwords, cookies, sessions, Keychain, shell history, full environment dumps, `.env` raw content, and other macdata devices.
- status: in_progress
- dependencies: S5PBT03
- required files: `device_config.json`, `owner_confirmations.json`, `run_controlled_cycle.py`, `test_macdata_package.py`
- acceptance_ids: ACC-MACDATA-PROM2-SETUP-20260705
- test commands: `python3 -m unittest OpenAIDatabase/macdata/proM2/tests/test_macdata_package.py -q`; `python3 OpenAIDatabase/macdata/proM2/scripts/run_controlled_cycle.py --repo-root . --preflight-only`; full `--execute` archive cycle after setup push.
- evidence: local package tests and preflight pass on MacBook Pro / Mac14,5 / Apple M2 Max / 32GB; full archive branch verification is pending until setup is pushed.
- risk: Docker/Homebrew/system/project-cache cleanup must remain gated by remote hash verification and project-cache whitelist rules.
- rollback: revert setup commit; delete remote `macdata-proM2` only after confirming archive history is no longer needed.

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
