# Risk Register

- R1: Path-only processed private refs cannot prove processed business values; mitigation is `NO_GO` until authorized fill supplies fingerprints.
- R2: Private fill request could disclose internal refs if committed; mitigation is ignored runtime and validator Git-boundary checks.
- R3: Raw-to-processed comparison could be claimed too early; mitigation is explicit comparison=false and consistency=false gates.
