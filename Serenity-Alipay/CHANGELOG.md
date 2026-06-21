# Changelog

## Unreleased - Review6 Semantic Extraction

- Added machine source selectors, extracted values, verification timestamps, and evidence hashes for 49 active Serenity parameters.
- Added AST implementation fingerprints for 12 active Serenity formulas.
- Recorded the FORM-008 post-renormalization cap caveat: final weights can exceed 0.30 for 1, 2, 3, and 4 candidate scenarios under the current algorithm, while existing target-weight tests cover only the 5-candidate scenario.

No scoring result, ranking result, gate logic, parameter value, data, or business behavior changed.

## 0.1.0 - Governance Baseline

- Added CodexProject governance baseline for Serenity-Alipay.
- Registered current scoring, ranking, hard-gate, MDD, recovery, Top5, comparison, discipline, and scheduler rules without changing runtime behavior.
- Added version separation in `docs/governance/VERSION_MATRIX.yaml`.
- Preserved legacy project files as compatibility indexes.

No scoring result, ranking result, gate logic, parameter value, data, or business behavior changed in this governance-only baseline.
