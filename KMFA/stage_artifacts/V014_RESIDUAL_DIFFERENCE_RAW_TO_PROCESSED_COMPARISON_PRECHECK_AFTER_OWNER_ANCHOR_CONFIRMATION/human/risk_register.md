# Risk Register

- Risk: comparison precheck is mistaken for formal value comparison.
- Control: raw-to-processed comparison remains unperformed and downstream reconciliation gates stay closed.
- Risk: private comparison-ready handles leak target-slot details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during precheck.
- Control: this phase does not read or mutate raw inbox; later phases must preserve the immutable raw boundary.
