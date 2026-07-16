# PFI v0.2.5 Stage 1 Phase 1.3 Risk and Rollback

## Verified isolated boundary

- The accepted App was an isolated disposable candidate. It was never promoted to a canonical entry.
- Applications, Desktop and Downloads retained the observed v0.2.3 canonical entries byte-for-byte. The only canonical install gate remains `S12-P2-T1`.
- The candidate used release-only identity and an empty data home. It did not read or change financial data, SQLite, model, formula or parameter behavior.
- The accepted runtime had one three-member process group and two exact loopback endpoints. Finalization stopped that group, released both endpoints, removed its LaunchServices registration and deleted the isolated root.

## Residual risks

- The actual local Streamlit runtime was 1.35.0 while the lock declares 1.54.0. Final rebuilt-environment and installed-runtime validation remains a Stage 12 obligation.
- Real history navigation observed `pageshow.persisted=false`. This is recorded as an observation, not presented as a bfcache hit.
- A rejected cleanup attempt showed that leaving the temporary Finder window open can republish a stale LaunchServices path after root deletion. The accepted rerun closed that window before finalization and independently proved final absence.
- Tracked evidence cannot contain its own future binding commit. The direct binding successor and three external reviews are therefore bound through an external post-commit attestation.

## Rollback

1. Revert the Phase 1.3 direct binding/evidence commit.
2. Revert release-content commit `128c6b889c91f5d7f64c7cd9635466fa2caf0275` with a new path-limited compensating commit if rollback is required.
3. Remove only the matching external attestation and review directory for the rejected binding candidate.

Rollback must not alter canonical Apps, user data, SQLite, existing ports 8501/8502, installed dependencies or remote refs. Stage 1 remains `in_progress`; Stage 2 is not started.
