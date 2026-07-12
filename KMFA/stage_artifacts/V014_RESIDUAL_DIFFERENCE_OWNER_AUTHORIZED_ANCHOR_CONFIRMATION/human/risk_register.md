# Risk Register

- Risk: private anchor confirmation is mistaken for formal value comparison.
- Control: raw-to-processed comparison remains unperformed and every downstream reconciliation gate stays closed.
- Risk: private anchor handles leak target-slot details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during confirmation.
- Control: this phase does not read or mutate raw inbox; later phases must preserve the immutable raw boundary.
