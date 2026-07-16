# PFI v0.2.5 Stage 1 Phase 1.2 Service Worker Audit

## Source state

- Repository production source has no current `serviceWorker.register(...)` path and no new `sw.js` is introduced.
- Absence of current source code does not prove a user's browser has no historical registration, controller, or CacheStorage entry; therefore Phase 1.2 uses explicit disablement and cleanup.

## Enforced policy

1. Before any manifest/cache-policy fetch, enumerate same-origin Service Worker registrations.
2. Require every `unregister()` result to be `true`.
3. Delete every CacheStorage name on the dedicated PFI origin and require every deletion result to be `true`.
4. If the current document still has a controller after cleanup, keep the PFI shell hidden and show Chinese restart/reinstall/cache-clearing recovery. Do not auto-reload or loop.
5. Only a subsequent uncontrolled document may fetch manifest/cache policy and become ready.

## Isolated Chromium evidence

- A legacy `/legacy-sw.js` registration and `pfi-v024-shell` cache were deliberately seeded on an ephemeral PFI-only loopback origin.
- The controlled gate page remained blocked, kept the shell hidden, performed zero manifest/cache-policy fetches, and removed the registration/cache.
- After reload, `navigator.serviceWorker.controller === null`, registrations=`0`, caches=`0`; manifest and cache policy then passed and the shell became ready.
- A deterministic persisted-event mismatch changed the process key, immediately hid the shell, and displayed the Chinese `版本冲突` recovery surface.
- Console errors=`0`; page errors=`0`.

Evidence: `browser_validation.json`, `bfcache_mismatch.png`, `playwright_trace.zip`.

## Boundary

The cleanup applies only to the dedicated current origin. It does not enumerate other origins, browser profiles, installed App copies, or live PFI ports. Phase 1.3 must repeat the check in the canonical installed App/new-profile acceptance path.
