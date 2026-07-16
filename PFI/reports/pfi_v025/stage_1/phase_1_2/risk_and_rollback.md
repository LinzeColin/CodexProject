# PFI v0.2.5 Stage 1 Phase 1.2 Risk and Rollback

## Residual risks

- Current runtime is Streamlit 1.35.0 while the lock declares 1.54.0. The wrapper has a compatibility guard, but Phase 1.3 must rerun actual HTTP/browser evidence after canonical environment installation.
- The strict HTTP policy patches Streamlit's Tornado `StaticFileHandler` before server construction. An incompatible signature or Starlette mode fails closed rather than starting without the cache contract.
- A legacy Service Worker controller can survive unregister until the current page closes/reloads. The current page remains blocked; automatic reload is intentionally avoided.
- Real headless Chromium navigation reported `back_forward` with `persisted=false`; deterministic Node and browser-dispatched persisted events cover the handler/mismatch path, but the report does not claim a real bfcache hit.
- The Streamlit cache adapter is installed at startup without editing `streamlit_app.py`; wrapper tests and real AppTest prove key/TTL behavior, but bypassing canonical launchers is unsupported and fails without `PFI_STREAMLIT_CACHE_KEY`.
- Browser trace ZIP members are rewritten only to replace the absolute home prefix with `$HOME`; ZIP integrity and decompressed-member privacy are both verified before binding.

## Rollback

1. Revert the Phase 1.2 binding/evidence commit.
2. Revert final remediation content commit `b3885f15cd2e983c0839be6a20d7e4a9391c6324`; the rejected `5edd3788` / `df7e2add` pair remains superseded history and is not an acceptance target.
3. Restore the Phase 1.1 manifest/embedded manifest values bound to `a9592b8ce457492fd0e6817f74388f146ca657c6`.

No data migration, SQLite change, installed App change, live-process stop, or remote push occurred, so no user-data/system rollback is required.

## Stop boundaries preserved

- Phase 1.3 install/Finder/new-profile work is not started.
- Existing ports 8501/8502 and fixed-port owner processes are not stopped or reused for evidence.
- Model, formula, parameter values, financial rows, FX rates, and private paths are not changed or included in evidence.
