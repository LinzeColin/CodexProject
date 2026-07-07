# Risk Register

- Risk: authorization intake is mistaken for owner-authorized anchor confirmation.
- Control: confirmation count remains zero and every downstream gate stays closed.
- Risk: private authorization queue leaks target-slot details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during preparation.
- Control: this phase does not read or mutate raw inbox; later phases must preserve the immutable raw boundary.
