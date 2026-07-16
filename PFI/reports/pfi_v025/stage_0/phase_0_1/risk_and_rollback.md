# PFI v0.2.5 Stage 0 Phase 0.1 — Risks and Rollback

## Decision boundary

- Acceptance target: `ACC-PFI-V025-S0-P01-BASELINE`.
- Current result: `candidate_pass`, pending independent Phase review and explicit user acceptance.
- This is a current-fact baseline only. It is not Stage 0 completion, production acceptance, or authorization to upload or reinstall the App.

## Confirmed carry-forward fact

- v0.2.4 product commit `17b9f59794740f927c5f531ba1aa334621a832e5` is the direct parent of evidence commit `5e48e739774575f4d198d6268271e557de434897`.
- The evidence commit is in `origin/main` history, and the PFI subtree did not change between that commit and audited remote main `3c7626008c25aeb6b71ddccc0eb9b999e5d3aedb`.
- The old live verifier is `not_replayable_after_unrelated_main_advance`; this Phase records remote ancestry and subtree equality instead of claiming a new v0.2.4 closeout transaction.

## Unresolved current facts

- Release identity is mixed: `PFI/VERSION` reports v0.2.1, web and App sources report 0.2.3, target/build markers report v0.2.4, and this evidence contract is v0.2.5.
- `PFI/web/app/home.js` is absent. The Task 2 grouped hash command therefore exited 1; this failure is retained and was not repaired.
- The repository App bundle emits `code has no resources but signature indicates they must be present`. Per-bundle numeric codesign exits were not exposed by the original exact loop and remain `null` where unavailable.
- The repository App executable hash differs from the installed, Downloads, and Desktop-resolved copies even though their plist hashes match.
- Two existing canonical PFI Streamlit services were observed on ports 8501 and 8502. Both were healthy and had canonical cwd; neither was designated preferred.
- `PFI_DATA_HOME` is unset. The working-tree `MetaDatabase/PFI` path is sparse-absent, while aggregate Git-tree evidence exists; `PFI/MetaDatabase` and `~/.pfi` each contained one file at capture time.
- Core read-model metrics for net worth, cash balance, and investment market value remain blocked by missing sources.
- `read_model_hash` is time-sensitive across calls because `generated_at_utc` enters the scan and the scan enters the hash at `PFI/src/pfi_os/application/read_model_status.py:153,165`. The captured snapshot is retained; a fresh replay proved all other safe fields equal.
- Pytest performed collection only: 795 tests were discovered and zero tests were executed. Full tests and browser UAT remain not run.

## Commands that failed or were not run

- Failed as observed inventory evidence: the Task 2 grouped frontend hash command exited 1 because `PFI/web/app/home.js` was missing.
- Failed as observed inventory evidence: strict codesign verification for the repository App emitted the missing-resources diagnostic.
- Not run by design: full test execution, browser UAT, App or launcher execution, service restart, data import or mutation, database write or migration, GitHub push, and App reinstall.

## Explicit non-goals

- Phase 0.2, Phase 0.3, whole-Stage review, Stage 1 or any later Stage.
- Business code, formulas, model parameters, schema, UI, launcher, App bundle, real-data, database, governance, release, or production changes.
- GitHub upload or final App installation.

## Rollback

- Before commit: delete only the seven paths listed in `changed_files.txt`.
- After commit: revert only the local Phase 0.1 commit; do not rewrite unrelated history.
- No private values, database writes, App changes, service changes, data mutations, or uploads occurred in this Phase.
