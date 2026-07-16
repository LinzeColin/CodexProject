# PFI v0.2.5 Stage 1 Phase 1.1 Risk and Rollback

## Current result

`ACC-PFI-V025-S1-P11-RELEASE-IDENTITY` is a local candidate only. Stage 1 remains `in_progress`; identity-binding commit attestation and independent review must complete before Codex accepts this Phase. This is not whole-Stage, release, production, install, or final human acceptance.

## Risks and controls

- **Commit self-reference:** `release_manifest.json.git_commit` points to final immutable post-review content commit `a9592b8ce457492fd0e6817f74388f146ca657c6`; the later identity-binding commit is carried only by external attestation. Initial `65fe4633.../fc2630be...` and intermediate `71147c43.../9cc8e0f6...` pairs remain auditable superseded history.
- **Frontend hash cycle:** the composite hash covers all delivered local scripts/styles and a canonicalized `index.html` whose embedded manifest block is replaced with `{}`. Manifest contents are not part of their own hash.
- **Old UI exposure:** the shell is hidden before scripts execute. Missing, partial, invalid, unreachable, or mismatched identity keeps it hidden and shows a Chinese recovery surface.
- **App provenance:** the native launcher supplies its actual App path and the shared shell helper validates that bundle's plist before opening the URL. Historical dry-run output remains unchanged.
- **Runtime topology:** `/api/release-manifest` is served by the separate runtime API base URL. The Roadmap's illustrative Streamlit-port 8501 URL is not claimed in this Phase.
- **Manifest-response integrity:** the runtime endpoint returns the SHA-256 of the exact raw manifest in `X-PFI-Release-Manifest-SHA256`; launcher mode blocks when the header is missing, invalid, or different from the launcher query.
- **Legacy metadata overwrite:** `version.js` synchronously normalizes the existing v0.2.4 runtime-config identity from the embedded v0.2.5 manifest before `shell.js` consumes it.
- **Local-path disclosure:** missing, unreadable, invalid UTF-8, or invalid JSON manifest input raises one generic public error and does not expose the local manifest path.
- **Streamlit iframe topology:** the delivered shell is a same-origin `srcdoc` iframe. The gate checks local, accessible parent, and referrer launcher sources; any partial, duplicate, tampered, or conflicting seven-key identity remains blocked. This reuses the repository's existing parent/referrer topology pattern without editing out-of-scope Streamlit source.
- **Static opt-out:** `releaseManifestApi:false` suppresses only the network fetch; it still requires a complete valid embedded v0.2.5 manifest before revealing the shell.
- **Finder visibility:** identity-init, native spawn, or missing project binding invokes a fixed Chinese recovery dialog without an absolute path. Tests substitute only the dialog executable; no real dialog or App install is performed.
- **Independent-review history:** superseded binding `9cc8e0f6...` received `Critical=1 / Important=2 / Minor=0`. Those findings are resolved in `a9592b8c...`; a fresh independent re-review is still required before final attestation.
- **Historical regression noise:** the selected compatibility baseline was already `33 passed / 1 failed` at Phase entry. After the intentional v0.2.5 identity transition it is `26 passed / 8 failed`: one pre-existing v0.2.1 development-record failure plus seven obsolete tests hard-coded to v0.2.3/v0.2.4 identity. The Roadmap allows only new v0.2.5 Stage 1 tests in this Phase; historical-test retirement/redirection is routed to `S12-P1-T1` and remains a final-release blocker, not silently ignored.
- **Browser coverage:** a real isolated Chrome screenshot and Node VM behavior tests cover the mismatch gate. Playwright is not installed; full App/localhost trace remains Phase 1.3.
- **Scope:** no cache/Service Worker/bfcache, canonical install, Finder, push, financial-data, SQLite, model, formula, or parameter behavior work is included.

## Rollback

1. Before the final identity-binding commit, discard only its uncommitted manifest/evidence/governance paths; keep final content commit `a9592b8c...` only as an incomplete non-delivery checkpoint.
2. After the final identity-binding commit, revert that binding first and `a9592b8c...` second. Both superseded pairs remain historical; do not rewrite history. No push occurs in this Phase.
3. Remove only the Phase 1.1 external attestation after reverting its candidate commit.
4. Do not touch `/Applications`, Desktop, Downloads, user data, SQLite, or live PFI services during rollback.
5. On any identity mismatch, keep the conflict page fail closed; do not bypass the gate to recover the old shell.
