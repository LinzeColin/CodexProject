# Stage 9 GitHub Main Upload Risk and Rollback

## Risks

- Remote `main` may advance before push. Mitigation: fetch immediately before commit and again before push; if behind, inspect PFI-path deltas before rebasing.
- Upload evidence contains a self-referential final commit hash problem. Mitigation: do not embed the final commit hash in evidence; use terminal `git rev-parse` and `git ls-remote` output after push as the authoritative remote proof.
- Upload gate might be mistaken for future-version start. Mitigation: contract and evidence explicitly keep `future_version_started=false`.

## Rollback

- If validation fails before push, do not push; fix within this upload gate or stop with the failing command.
- If push fails because remote advanced, fetch and inspect `origin/main` PFI-path changes before any rebase.
- If remote verification fails after push, stop and report the exact `HEAD`, `origin/main`, and `ls-remote` hashes; do not start future version work.

## Explicit Non-Goals

- No app bundle reinstall.
- No launcher C or Info.plist mutation.
- No real financial data mutation, deletion, cleanup, backfill, or synthesis.
- No mock/sample/demo/synthetic/fixture/fake financial data.
