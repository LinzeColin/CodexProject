# Stage 5 GitHub Main Upload Risk and Rollback

- Risk: upload gate evidence cannot embed the final self-referential commit hash; terminal `git rev-parse` and `git ls-remote` are the authority after push.
- Risk: remote `origin/main` can move before upload; stop and re-check the remote delta if `git fetch origin main` shows any new commit, especially any change under `PFI/`.
- Rollback: revert the Stage 5 upload commit and, if needed, revert the Stage 5 phase/review commits from GitHub main; no user financial data or app bundle state is modified by this gate.
- Stop condition: any Stage 5 regression fails, remote main changes again before push, or terminal remote hash verification does not prove `HEAD == origin/main == remote main`.
