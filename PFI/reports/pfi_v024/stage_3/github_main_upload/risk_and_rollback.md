# Stage 3 GitHub Main Upload Risk And Rollback

## Scope

This gate uploads the reviewed Stage 3 package to GitHub `main`. It does not
start Stage 4, reinstall app bundles, mutate launcher files, or change
financial data logic.

## Risks

- Remote `main` can advance after local validation and before push.
- Push can fail because of SSH/auth or non-fast-forward protection.
- Upload status files can over-claim completion without remote verification.

## Controls

- Rebase on current `origin/main` before final validation.
- Run Stage 3 browser validation, v0.2.4 regression, v0.2.3 compatibility, JSON
  checks, and git diff checks before push.
- Verify remote `main` after push with `git ls-remote origin refs/heads/main`
  and a fresh `git fetch origin main`.

## Rollback

- If push fails before changing remote `main`, keep local branch intact and
  retry after resolving the remote delta.
- If a pushed commit must be reverted, create a forward revert on `main`; do not
  rewrite remote history unless the user explicitly requests it.
