# PFI v0.2.4 Stage 8 GitHub Main Upload Risk and Rollback

## Risk

- This gate pushes to GitHub `main`; final truth must be terminal verification that local `HEAD`, fresh `origin/main`, and remote `refs/heads/main` are identical.
- Evidence JSON cannot safely embed its own final commit hash. Use terminal `git rev-parse` and `git ls-remote` output after push as the final hash source.
- Stage 9 must not start until Stage 8 upload is verified.
- `/Applications/PFI.app` remains missing; this gate does not reinstall app bundles.

## Rollback

- If pre-push validation fails, do not push; fix within Stage 8 upload gate scope.
- If push fails, keep local commit and report the remote/auth failure.
- If a post-push mismatch appears, fetch remote state, compare local/remote hashes, and do not enter Stage 9 until the mismatch is resolved.
- This gate does not mutate business data, app bundles, launcher files, or user financial data.

## Stop Conditions

- Stop after `HEAD == origin/main == remote main` is verified.
- Do not execute Stage 9 in this gate.
- Do not reinstall app bundle.
- Do not write, clean, delete, synthesize, or backfill user financial data.
