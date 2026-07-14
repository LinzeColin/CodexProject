# KM_IDSystem Model Specification

Project: `KM_IDSystem`
Governance spec version: `1.0.0`

- model_count: 9
- formula_count: 9
- parameter_count: 64
- active_model_count: 7
- active_formula_count: 7
- active_parameter_count: 49

## Canonical Sources

- `docs/governance/model_registry.yaml`
- `docs/governance/formula_registry.yaml`
- `docs/governance/parameter_registry.csv`
- `docs/governance/TRACEABILITY_MATRIX.csv`

## Model Overview

KM_IDSystem has active deterministic industrial rule models for dynamic kiln analysis, fault diagnosis, gear repair, machining advice, generic consulting, risk-level mapping, and an LLM provider router with offline fallback.

`MOD-008`, `FORM-008`, and `PARAM-050` through `PARAM-055` are planned,
non-production Stage039 control-policy registrations. They are included in the
total registry counts but excluded from the active counts until production
calibration and activation evidence exists.

`MOD-009`, `FORM-009`, and `PARAM-056` through `PARAM-064` are planned,
non-production Stage040 backpressure-policy registrations. They evaluate only
bounded control metadata and an actual project-filesystem free-space signal;
they do not activate a queue, worker, retry scheduler, persistent state, or
production admission path. Their proposed thresholds require production
calibration under `TASK-OPME-B-001` before activation.

Technology stack components such as FastAPI, React, SQLite, ECharts, and PDF generation are architecture/output components, not models.

## LLM Routing

`MOD-007` is not a provider name. It is a routing and fallback strategy: enabled provider configs with non-empty API key, base_url, and model are attempted in priority order; failures are logged; empty or failed provider sets return `offline_rules`. The prompt is referenced by file and line only and not copied into this governance file.

## Safety Boundary

All outputs are advisory engineering suggestions and report templates. They do not replace现场检测,施工审批,专业工程师签字,停机/焊接/热处理/起吊/设备改造 safety procedures.

## UNKNOWN Items

Threshold calibration source, field validation basis, provider operational policy, prompt governance version, and engineering signoff criteria are UNKNOWN and linked to `TASK-OPME-B-001`.
