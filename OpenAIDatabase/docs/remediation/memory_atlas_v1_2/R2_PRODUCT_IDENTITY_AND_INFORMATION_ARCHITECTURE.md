# Memory Atlas v1.2 Remediation R2: Product Identity And Information Architecture

## Status

- Phase: `R2_PRODUCT_IDENTITY_AND_INFORMATION_ARCHITECTURE`
- Phase result: `R2_COMPLETE_LOCAL_ONLY`
- Release result: `FAIL_REMEDIATION_REQUIRED`
- Base commit: `27c316a685126dddf9690d6344de8e69592cdb62`
- Final fetched `origin/main`: `b864009c657c6a9cebbf451e30389c1aa5809700`
- Closeout divergence: local `main` is ahead 4 and behind 7; no merge or rebase was
  attempted because the incoming commits belong to a separate Cloudflare L2 delivery.
- Remote push: `false`
- App reinstall: `false`
- Cloudflare deployment: `false`
- Next phase: `R3_REAL_COMMAND_PALETTE_WORKFLOWS`

R2 establishes a real v1.2 product identity and question-led information architecture.
It does not make commands executable, apply proposals, run owner-daily, reconcile
snapshots or publish any local work.

## Product Changes

- Brand is `Memory Atlas`; product line is `记忆决策台 · v1.2`.
- Home is `发生了什么`, with the context `先看变化，再核对证据，最后决定下一步`.
- The ten existing routes remain intact and are grouped by three user questions:
  `判断`, `探索` and `复盘`.
- Snapshot/runtime metadata, shared-state signal/revision, command CLI/safety contracts
  and formula parameter/source paths are closed `<details>` disclosures by default.
- Home visualization headings, filter labels, category options, action priorities and
  arrival evidence are Chinese and decision-oriented instead of Stage/schema-oriented.
- Navigation buttons scroll fully into their desktop or mobile navigation viewport on
  keyboard focus.
- Command buttons still only select explanatory content or navigate to an existing
  view. No execution bridge was added in R2.

## Browser Acceptance

| Viewport | Topbar | Focus lens | Quick actions | Content | Result |
|---|---:|---:|---:|---:|---|
| 1470x661 | 56px | 45px | 119px | 345px | PASS |
| 1440x900 | 56px | 45px | 152px | 551px | PASS |
| 390x844 | 46px | 78px | 140px | 311px | PASS |

The final real-browser gate proves:

- exact v1.2 identity, active Home title and three navigation groups;
- zero visible matches for Stage/Phase labels, CLI, English safety internals,
  implementation visual names, source paths and arrival machine evidence;
- sidebar, focus, command and formula technical disclosures are closed by default;
- the command disclosure opens and closes from the keyboard and preserves its audit
  contract;
- primary focus order follows navigation, Help, search, focus actions, quick actions
  and Home evidence;
- mobile Tab activates all ten routes in order and Shift+Tab returns through all nine
  preceding routes to Home; every forward and reverse step stores geometry proving the
  complete button and focus ring are inside the navigation scrollport with `0px` clip;
- all five workspace regions have zero pairwise overlap, horizontal overflow and
  viewport escape;
- every viewport checks 27 Home targets and 70 nested children with zero clipping;
- all three behavior categories and nine Chinese summaries remain scroll-reachable;
- mobile renders all ten route icons, keeps the Home title on one line and leaves a
  311px content viewport;
- screenshots are nonblank and preview ports are released.

## Regression

- Focused Python contracts: `9 passed`.
- TypeScript lint: PASS.
- Production build: PASS.
- Chinese UX audit: PASS with `bad_items=[]`.
- Historical contracts: S10 Review PASS (45 checks), S11 Review PASS (55 checks)
  and S12 P1 PASS (46 checks).
- Stage 7 Galaxy: PASS with 67,161 lit pixel samples and 11,828 points.
- Stage 7 Memory River: PASS with 64 lifecycle/event markers and 48 density bands.
- Stage 7 navigation selectors now use stable `data-nav-view` route keys so future
  human-facing label changes do not invalidate the visual regression.
- Independent review finished with `0 Critical / 0 Important`. Its terminology concern
  was closed by exact Chinese product-copy assertions. Its keyboard concern first made
  the stronger gate catch a real 36px right clip at `obsidian`; `onFocus` scrolling and
  bidirectional full-containment evidence then closed the finding.

## Requirement Delta

R2 promotes only four requirements directly proven by rendered browser behavior:

- `S05-AC04`: `FAILED -> VERIFIED`.
- `S09-AC04`: `PARTIAL -> VERIFIED`.
- `S10-AC02`: `PARTIAL -> VERIFIED`.
- `S10-AC03`: `FAILED -> VERIFIED`.

`S03-AC05` remains `PARTIAL`: the product surface no longer exposes raw-manifest-like
details, but a real raw ledger still does not exist and must be proven in R7. The
58-row aggregate is therefore `VERIFIED 34 / PARTIAL 16 / FAILED 6 /
NOT_VERIFIED 2` after R2.

## Evidence

- `机器治理/证据与日志/remediation/v1_2_r2/status.json`
- `机器治理/证据与日志/remediation/v1_2_r2/requirements_gap_delta.csv`
- `机器治理/证据与日志/remediation/v1_2_r2/browser/before/`
- `机器治理/证据与日志/remediation/v1_2_r2/browser/after/`
- `机器治理/证据与日志/remediation/v1_2_r2/regression/stage7/`
- `docs/superpowers/specs/2026-07-10-memory-atlas-v1-2-r2-identity-ia-design.md`

## Rollback

Revert the local R2 implementation commit while retaining R0/R1. This restores the R1
shell and tests without touching raw data, credentials, installed apps, Cloudflare or
GitHub main.

## Stop Condition

Stop after the local R2 commit. Do not start R3, push, reinstall or deploy in this run.
The installed app and online website remain the prior release until R8 performs the
single final delivery. R8 must explicitly reconcile the Cloudflare L2 history now on
`origin/main`; it must not overwrite the remote HomeHub link or governance evidence.
