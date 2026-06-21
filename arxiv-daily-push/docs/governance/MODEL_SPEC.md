# MODEL_SPEC

Project: `arxiv-daily-push`
Governance spec version: `1.0.0`

machine_summary:

- model_count: 5
- formula_count: 7
- parameter_count: 34

Fact levels follow `docs/governance/STANDARD.md`.

## A. Model Overview

| Model ID | Name | Kind | Purpose | Status | Version | Implementation reference |
|---|---|---|---|---|---|---|
| MOD-ADP-001 | Phase 1 readiness and notification dry-run gate | deterministic rule engine | Classify local readiness and render non-secret email notifications | active | adp-foundation-v1 | `src/arxiv_daily_push/doctor.py`, `src/arxiv_daily_push/notifications.py` |
| MOD-ADP-004 | Generic data contract and RunRecord state gate | deterministic contract/state validator | Validate generic data boundaries and allowed run-state transitions without network or media work | active | adp-contracts-v1 | `src/arxiv_daily_push/contracts.py`, `src/arxiv_daily_push/state_machine.py` |
| MOD-ADP-005 | arXiv Atom source adapter | deterministic source adapter | Build bounded arXiv API URLs and map Atom entries into generic SourceItem records | active | adp-arxiv-adapter-v1 | `src/arxiv_daily_push/arxiv_adapter.py` |
| MOD-ADP-002 | 100-point arXiv selection score | deterministic scoring model | Select the daily learning item from eligible arXiv candidates | planned | adp-ranking-planned-v1 | planned Phase 4 |
| MOD-ADP-003 | Claim Ledger publication gate | deterministic evidence gate | Block publication when key claims lack source locators or metadata is conflicted | planned | adp-claim-gate-planned-v1 | planned Phase 5 |

## B. Assumptions

| Assumption ID | Statement | Evidence | Scope | Status |
|---|---|---|---|---|
| ASM-ADP-001 | Phase 1 must not implement ingest, ranking, TTS, video, GitHub runner, or real email send. | `README.md`, `AGENTS.md`, `docs/phase_records/PHASE_01.md` | Phase 1 | active |
| ASM-ADP-002 | Email is the notification channel and `linzezhang35@gmail.com` is the recipient. | `config.py`, `config/examples/notification.example.yaml` | all phases | active |
| ASM-ADP-003 | Phase 1-11 use arXiv first while preserving generic source boundaries for later sources. | `docs/pursuing_goal/06_PURSUING_GOAL_READY_PROMPT.md` | all phases | active |
| ASM-ADP-004 | Phase 2 is limited to offline generic contracts and state validation; it must not fetch sources or generate publishable content. | `docs/phase_records/PHASE_02.md`, `src/arxiv_daily_push/contracts.py`, `src/arxiv_daily_push/state_machine.py` | Phase 2 | active |
| ASM-ADP-005 | Phase 3 implements the first arXiv adapter but keeps tests offline and does not perform scheduled or bulk ingestion. | `docs/phase_records/PHASE_03.md`, `src/arxiv_daily_push/arxiv_adapter.py`, `tests/fixtures/arxiv_atom_sample.xml` | Phase 3 | active |

## C. Functions and Formulas

The machine-readable source is `formula_registry.yaml`.

- FORM-ADP-001 classifies Phase 1 readiness as `blocked`, `warn`, or `pass`.
- FORM-ADP-002 renders dry-run email subject/body without secrets.
- FORM-ADP-005 validates generic contract fields, enum sets, and P0 evidence locator requirements.
- FORM-ADP-006 validates allowed `RunRecord` transitions and terminal states.
- FORM-ADP-007 maps arXiv Atom metadata into generic `SourceItem` records with bounded query parameters.
- FORM-ADP-003 preserves the planned 100-point selection scoring weights.
- FORM-ADP-004 preserves the planned Claim Ledger hard-block rules.

## D. Parameters

The canonical parameter catalog is `parameter_registry.csv`.

- Active Phase 1 parameters: PARAM-ADP-001 through PARAM-ADP-008.
- Active Phase 2 contract/state parameters: PARAM-ADP-020 through PARAM-ADP-028.
- Active Phase 3 arXiv adapter parameters: PARAM-ADP-029 through PARAM-ADP-034.
- Planned ranking weights: PARAM-ADP-009 through PARAM-ADP-016.
- Planned evidence gate parameters: PARAM-ADP-017 through PARAM-ADP-019.

## E. Methodology

Phase 2 implements deterministic, dependency-free validation for the generic
objects required by the pursuing goal: `SourceItem`, `EvidenceClaim`, `Lesson`,
`Storyboard`, `Publication`, and `RunRecord`. The runtime validators intentionally
mirror the schema boundaries without introducing a JSON Schema dependency.

The `RunRecord` state machine is deliberately narrow: it accepts only explicit
forward transitions, blocks skipped evidence states, and treats `completed`,
`blocked`, and `failed` as terminal states. It does not imply that ingest,
ranking, evidence extraction, lesson generation, media generation, runner
automation, or SMTP transport is implemented.

Phase 3 adds the first concrete adapter for arXiv Atom responses. It uses the
official API shape documented by arXiv: query URLs are sent to `export.arxiv.org`
and results are Atom feeds. The adapter maps entries to generic `SourceItem`
objects and keeps arXiv-specific fields in `metadata.arxiv`.

## F. Strategy Logic

- Unrecognized source or claim enum -> validation error.
- P0 claim without a stable locator -> validation error.
- Skipped `RunRecord` transition -> validation error.
- Terminal `RunRecord` state with `running` status -> validation error.
- CLI `validate-record` returns exit 2 when validation errors are present.
- arXiv query `max_results` above the local Phase 3 cap -> validation error.
- arXiv API error Atom entry -> adapter error.
- Parsed arXiv entry -> `source_type=arxiv`, `source_adapter=arxiv.atom.v1`, arXiv fields under `metadata.arxiv`.

## G. Validation

Current focused validation:

- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`
- `python3 -m json.tool arxiv-daily-push/schemas/*.schema.json`
- `python3 scripts/validate_project_governance.py --project arxiv-daily-push`
- `python3 scripts/validate_project_governance.py --changed-only --enforce-sync`
- `git diff --check`

Uncovered planned scenarios:

- arXiv network ingest idempotency.
- 100-point ranking golden tests.
- Claim extraction from paper text/PDF.
- TTS/video sample gates.
- GitHub self-hosted runner and email transport health.
