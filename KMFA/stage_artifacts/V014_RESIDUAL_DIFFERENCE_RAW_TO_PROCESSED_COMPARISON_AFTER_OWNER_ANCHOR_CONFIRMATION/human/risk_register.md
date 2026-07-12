# Risk Register

- Risk: formal comparison attempt is mistaken for completed value consistency.
- Control: public evidence records zero exact matches, 72 blockers and keeps raw-to-processed value comparison performed=false.
- Risk: private blocker records leak target details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during comparison.
- Control: this phase does not read or mutate raw inbox; later phases must preserve the immutable raw boundary.
