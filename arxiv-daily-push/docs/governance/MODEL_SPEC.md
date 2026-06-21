# MODEL_SPEC

Project: `arxiv-daily-push`
Governance spec version: `1.0.0`

machine_summary:

- model_count: 3
- formula_count: 4
- parameter_count: 19

Fact levels follow `docs/governance/STANDARD.md`.

## A. Model Overview

| Model ID | Name | Kind | Purpose | Status | Version | Implementation reference |
|---|---|---|---|---|---|---|
| MOD-ADP-001 | Phase 1 readiness and notification dry-run gate | deterministic rule engine | Classify local readiness and render non-secret email notifications | active | adp-foundation-v1 | `src/arxiv_daily_push/doctor.py`, `src/arxiv_daily_push/notifications.py` |
| MOD-ADP-002 | 100-point arXiv selection score | deterministic scoring model | Select the daily learning item from eligible arXiv candidates | planned | adp-ranking-planned-v1 | planned Phase 4 |
| MOD-ADP-003 | Claim Ledger publication gate | deterministic evidence gate | Block publication when key claims lack source locators or metadata is conflicted | planned | adp-claim-gate-planned-v1 | planned Phase 5 |

## B. Assumptions

| Assumption ID | Statement | Evidence | Scope | Status |
|---|---|---|---|---|
| ASM-ADP-001 | Phase 1 must not implement ingest, ranking, TTS, video, GitHub runner, or real email send. | `README.md`, `AGENTS.md`, `docs/phase_records/PHASE_01.md` | Phase 1 | active |
| ASM-ADP-002 | Email is the notification channel and `linzezhang35@gmail.com` is the recipient. | `config.py`, `config/examples/notification.example.yaml` | all phases | active |
| ASM-ADP-003 | Phase 1-11 use arXiv first while preserving generic source boundaries for later sources. | `docs/pursuing_goal/06_PURSUING_GOAL_READY_PROMPT.md` | all phases | active |

## C. Functions and Formulas

The machine-readable source is `formula_registry.yaml`.

- FORM-ADP-001 classifies Phase 1 readiness as `blocked`, `warn`, or `pass`.
- FORM-ADP-002 renders dry-run email subject/body without secrets.
- FORM-ADP-003 preserves the planned 100-point selection scoring weights.
- FORM-ADP-004 preserves the planned Claim Ledger hard-block rules.

## D. Parameters

The canonical parameter catalog is `parameter_registry.csv`.

- Active Phase 1 parameters: PARAM-ADP-001 through PARAM-ADP-008.
- Planned ranking weights: PARAM-ADP-009 through PARAM-ADP-016.
- Planned evidence gate parameters: PARAM-ADP-017 through PARAM-ADP-019.

## E. Methodology

Phase 1 implements a deterministic foundation gate only. It checks command
availability and disk readiness, then reports warnings for later-phase runtime
dependencies without pretending TTS, video, GitHub automation, or SMTP transport
is ready.

The future ranking, evidence, TTS, video, and automation models are planned
from the pursuing goal baseline and remain unimplemented until their phases.

## F. Strategy Logic

- Required Phase 1 commands missing -> `blocked`.
- Later-phase commands missing or disk under the video/TTS threshold -> `warn`.
- Required commands present and later-phase resource gates satisfied -> `pass`.
- Email rendering is dry-run only and never reads SMTP secrets.

## G. Validation

Current focused validation:

- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`
- `python3 scripts/validate_project_governance.py --project arxiv-daily-push`
- `git diff --check`

Uncovered planned scenarios:

- arXiv ingest idempotency.
- 100-point ranking golden tests.
- Claim locator extraction.
- TTS/video sample gates.
- GitHub self-hosted runner and email transport health.

