# Changelog

## 0.1.0 - 2026-06-20

- Established CodexProject canonical governance baseline under `docs/governance/`.
- Separated product version `0.1.0` from legacy Task Pack label `v4.2.0`.
- Mapped legacy model, formula, parameter, task, acceptance, risk, and release-gate evidence into validator-readable governance files.
- Converted legacy governance Markdown entrypoints into compatibility indexes to prevent duplicate editable fact sources.
- No model runtime logic, business behavior, data generation, or product feature code changed.
- Added T1307/A209 4h operator soak evidence: 48/48 checkpoint windows PASS over 14400 seconds; A209/A206 remain open until 24h operator soak evidence and CI validation exist.

## Legacy Task Pack v4.2.0 - 2026-06-19

- Historical EEI Task Pack and prototype governance snapshot preserved in Git history and legacy `data/*.csv` evidence inputs.
- Current counts and active governance facts must be read from `docs/governance/*`, not this changelog.
