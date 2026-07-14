# Memory Atlas v1.2 Remediation R1: Home Layout And Multi-Viewport Gate

## Status

- Phase: `R1_LAYOUT_AND_MULTIVIEWPORT_GATE`
- Phase result: `R1_COMPLETE_LOCAL_ONLY`
- Release result: `FAIL_REMEDIATION_REQUIRED`
- Base commit: `418a822333a798abc3951db66b965ca6029dc30e`
- Remote push: `false`
- App reinstall: `false`
- Cloudflare deployment: `false`
- Next phase: `R2_PRODUCT_IDENTITY_AND_INFORMATION_ARCHITECTURE`

R1 only fixes the home shell/Grid blocker and establishes real browser acceptance. It
does not make the six command buttons executable, remove Stage/CLI implementation
details, align online data, reinstall the local app, deploy Cloudflare Pages, or prove
the full v1.2 release.

## Root Cause

`App.tsx` renders five direct workspace children: topbar, controls, interaction lens,
command palette and content grid. The shared and mobile CSS still allocated four rows.
The command palette therefore collapsed to 26px and its 361-891px content overflowed
over the home content.

Two related mobile constraints were also invalid:

- the workspace used `height: calc(100dvh - 55px)` although the actual mobile header
  was about 85px high;
- the mobile wide content grid forced a 320px first row even when only about 128px of
  the workspace remained.

## Implementation

- Added a dedicated fifth workspace row for surfaces where Command Palette is visible.
- Kept four rows for visual-focus surfaces where Command Palette remains hidden.
- Bounded Command Palette height and made its own content scrollable.
- Restored Home Overview as an internal scroll container after the generic
  `.visual-workspace` rule.
- Let the mobile workspace consume the actual CSS Grid remainder instead of a hardcoded
  header subtraction.
- Removed the mobile 320px minimum row only for the home wide view.
- Added a Playwright/Chromium gate for `1470x661`, `1440x900` and `390x844`.

## Browser Acceptance

| Viewport | Before | Final | Command palette | Content viewport | Result |
|---|---|---|---:|---:|---|
| 1470x661 | palette 26px; overlaps content by 18px | five non-overlapping rows | 170px | 292px | PASS |
| 1440x900 | palette 26px; overlaps content by 18px | five non-overlapping rows | 232px | 469px | PASS |
| 390x844 | palette 26px; overlaps content by 18px; workspace escapes viewport | five contained rows | 158px | 126px scroll viewport | PASS |

The automated gate verifies:

- no pairwise overlap between the five workspace sections;
- no document or section horizontal overflow;
- workspace and sections remain inside the visible viewport;
- Command Palette heading, detail and final safety item are scroll-reachable;
- Home Overview first and final sections are scroll-reachable;
- the home child surface remains inside the content grid;
- 27 direct/key nested containers and 70 nested children have no horizontal clipping;
- all three S06 behavior categories and all 9 rendered Chinese summaries are
  scroll-reachable;
- screenshots are nonblank and the preview port is released.

## Verification

- `python3 -m pytest -q tests/test_memory_atlas_v1_2_home_layout_contract.py tests/test_memory_atlas_visual_acceptance.py` -> `6 passed`
- `npm run lint` -> PASS
- `npm run build` -> PASS
- `npm run validate:v1.2-home-multiviewport` -> PASS for all three viewports
- `npm run validate:stage7-visual` -> PASS for Galaxy and Memory River
- `node --check scripts/validate_memory_atlas_v1_2_home_multiviewport.cjs` -> PASS

The historical `validate:v1.2-s12-p1` scope guard was intentionally not used as an R1
acceptance result: while R1 files are uncommitted it rejects every non-S12 file as an
unrelated change. Its command-palette inventory contract remains unchanged and can be
rerun from the clean local commit.

## Requirement Delta

R1 promotes only the requirements directly proven by rendered browser behavior:

- `S06-AC02`: `PARTIAL -> VERIFIED` because the real browser gate finds all three
  behavior categories and proves all 9 rendered Chinese summaries are non-empty,
  Chinese-readable and individually scroll-reachable.
- `S10-AC01`: `FAILED -> VERIFIED` because the home arrival briefing is no longer
  covered and remains reachable at all target viewports.

`S12-AC01` remains `PARTIAL` because the buttons still only select explanatory text.
`S14-AC02` remains `FAILED` until the real browser gate is part of the final audit chain.
The 58-row aggregate is therefore `VERIFIED 30 / PARTIAL 18 / FAILED 8 /
NOT_VERIFIED 2` after R1.

## Evidence

- `机器治理/证据与日志/remediation/v1_2_r1/status.json`
- `机器治理/证据与日志/remediation/v1_2_r1/requirements_gap_delta.csv`
- `机器治理/证据与日志/remediation/v1_2_r1/browser/before/`
- `机器治理/证据与日志/remediation/v1_2_r1/browser/final/`
- `机器治理/证据与日志/remediation/v1_2_r1/regression/stage7/`

## Rollback

Revert the single local R1 commit. This removes the CSS changes, R1 validators, tests
and evidence without touching raw data, credentials, the installed app or Cloudflare.

## Stop Condition

Stop after the local R1 commit. Do not start R2 in this run and do not push, reinstall
or deploy. The currently installed app and online website remain the prior broken
release until R8 performs the single final delivery.
