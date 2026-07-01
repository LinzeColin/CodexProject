# Stage 4 GitHub Main Upload Risk and Rollback

- Risk: upload gate evidence cannot embed the final self-referential commit hash; terminal `git rev-parse` and `git ls-remote` are the authority after push.
- Risk: remote `origin/main` moved before upload; this gate rebased Stage 4 on top of `d520e748` and verified the remote delta did not touch `PFI/`.
- Rollback: revert the Stage 4 upload commit and, if needed, revert the Stage 4 phase/review commits from GitHub main; no user financial data or app bundle state is modified by this gate.
- Stop condition: any Stage 4 regression fails, remote main changes again before push, or terminal remote hash verification does not prove `HEAD == origin/main == remote main`.
