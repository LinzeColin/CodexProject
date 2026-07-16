# PFI v0.2.5 Stage 0 Current State Matrix

Evidence batch: `2026-07-12T01:09:30.659834+10:00`. Allowed status enum: `VERIFIED / CONFLICTED / BLOCKED / NOT_RUN / REFERENCE_ONLY`.

| surface | status | current truth | evidence |
|---|---|---|---|
| Git/repository | VERIFIED | Phase base is `ede905cd96c7b6682cf38971de54f4544f46251b`; initial advertised main is `a65f30c19241b14c4a895bc68dd4422b5a1e4a5c`; merge base is `3c7626008c25aeb6b71ddccc0eb9b999e5d3aedb`; no remote-only PFI drift was observed and no hydration was performed. | external guard `run_state.json`; Task 1 report |
| Formal UI source | VERIFIED | The formal homepage source exists at `PFI/web/app/pages/home.js` and is loaded by the Web shell and Streamlit asset path. The absent `PFI/web/app/home.js` is a non-designated legacy path and therefore a non-gap; this source fact alone does not establish rendered or production acceptance. | `CURRENT_WEB`; `P03_CORRECTION` |
| Release identity | CONFLICTED | VERSION, page, launcher, repository App, installed App and target v0.2.5 identity remain ununified. | `PFI/config/pfi_v025_active_requirements.json`; `CURRENT_OWNER`; `CURRENT_WEB`; `P03_TERM` |
| App identity | CONFLICTED | Repository App exists but strict codesign exits 1 and its executable does not match every existing user entry. No App mutation or reinstall was attempted. | guard `app_runtime_probe.json`; `P03_TERM` (`APP-001`) |
| Runtime listeners | CONFLICTED | Two healthy canonical-root listeners were observed on ports 8501 and 8502; a preferred single listener is not established. | guard `app_runtime_probe.json`; `P03_TERM` (`APP-001`) |
| Data roots | CONFLICTED | `PFI_DATA_HOME` is unset; working-tree `MetaDatabase/PFI` is absent while the Git object surface exists; repository-local and user-state roots are present. | guard `raw_data_probe.json`; `P03_TERM` (`DATA-001`) |
| Read model | BLOCKED | Four raw sources and 8,815 transaction records are readable through the immutable Git-object path, but net worth, cash balance and investment market value remain `source_missing`. | guard `raw_data_probe.json`; `P01_REPO` |
| Route/navigation | CONFLICTED | Static source exposes ten primary labels, but target routes and current aliases/compatibility inputs are not converged; rendered DOM, a11y, deep-link and history proof is absent. | `P02_ACTIVE`; `CURRENT_WEB`; `P03_TERM` |
| Owner views | CONFLICTED | Historical closeout and bare acceptance markers do not prove current v0.2.5 status; owner surfaces are not unified to this candidate. | `CURRENT_OWNER`; `PFI/config/pfi_v025_active_requirements.json`; `P03_TERM` |
| Privacy boundary | VERIFIED | Phase 0.1/0.2 evidence, current probes and the finalized exact-25 candidate emit no private rows, amounts, accounts, counterparties, credentials, raw filenames or absolute private database paths; the corrected final-tree privacy scan reported zero pattern, token and structured-key findings. | guard proof privacy fields; Task 2 report; external Task 7 final-gate outputs |
| Tests | NOT_RUN | The isolated parameter diagnostic is the expected 3-pass/5-fail baseline (exit 1) and collect-only found 795 tests (exit 0); full tests, browser/UAT and production gates were not run by this Phase contract. | `P03_TERM` (`TEST-001`, `TEST-002`, `P03-OUTCOMES`) |
| Phase 0.1 evidence | REFERENCE_ONLY | The Phase 0.1 baseline candidate is preserved as prior evidence; it does not prove current Stage acceptance. | `PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json` |
| Phase 0.2 evidence | REFERENCE_ONLY | The tracked Phase 0.2 candidate preserves precommit lifecycle; the immutable external attestation resolves its approved override only within Phase 0.2 scope. | `PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json`; `P02_ATTEST` |
| Phase 0.3 candidate evidence | VERIFIED | Original commit `31368570082c34eca50c72c7d7b2ef46b0e6854d` and its immutable attestation are preserved. Correction `PFI-V025-S0-P03-COMP-FND030` reclassifies FND-030 as non-applicable/non-gap; the compensating commit and external compensation attestation remain pending. | `PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json`; `P03_CORRECTION`; original immutable attestation SHA-256 `b439444de5a110f07f48fe0fa1d566624183a38e4d7270d0f0bc6fb2e6d696d6` |
| Stage 0 whole-stage acceptance | NOT_RUN | Whole-stage fresh review, remediation, re-review, Codex acceptance and explicit user acceptance have not started. | Phase 0.3 stop condition |
| Stage 1 | NOT_RUN | Stage 1 has not started and is not authorized by this run. | Phase 0.3 mandatory stop statement |

Stage 0 / Phase 0.3 candidate result only; Stage 0 whole-stage review and Stage 1 remain not_started in this run.
