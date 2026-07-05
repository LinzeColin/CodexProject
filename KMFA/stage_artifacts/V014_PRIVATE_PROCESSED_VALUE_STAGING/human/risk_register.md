# Risk Register

- risk: staged target slots are references only and do not contain processed value fingerprints.
- control: keep decision `NO_GO` until private value fingerprints are materialized and compared.
- risk: private staging could disclose internal refs if committed.
- control: private staging stays under ignored `.codex_private_runtime` and validator checks it is untracked.
