# Changelog

## 0.2.0 - 2026-06-21

- Added the three-layer private context architecture for core profile, project memory, and behavior history.
- Added generated ChatGPT/Codex personalization exports, Codex config templates, resource routing, evaluation harness, and four redacted run-log categories.
- Wired Codex sync to regenerate personalization exports after derived data refresh.
- Added focused tests and governance records for `MOD-011`, `FORM-011`, and `PARAM-083` through `PARAM-092`.

## 0.1.0 - 2026-06-20

- Added the first OpenAIDatabase governance baseline for 10 deterministic models, 10 formulas, and 82 documented active parameters.
- Separated product version, model versions, parameter profile versions, data snapshot version, governance spec version, and current gate in `docs/governance/VERSION_MATRIX.yaml`.
- Kept runtime model behavior unchanged; this is a governance documentation and CI mode change only.
