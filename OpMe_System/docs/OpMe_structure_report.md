# OpMe_System S4PCT01 Structure Report

Task: `S4PCT01`
Acceptance: `ACC-S4PCT01`
Date: 2026-06-25

## Scope

This report records the OpMe_System structure simplification for Other8 S4PC.
It separates active runtime source from historical backups and original
prototype work without changing backend, frontend, app launcher, API, UI, or
model behavior.

## Active Structure

| Purpose | Active path | Status |
|---|---|---|
| Backend runtime source | `OpMe_System/backend/**` | unchanged |
| Frontend runtime source | `OpMe_System/frontend/**` | unchanged |
| Delivery app build source | `OpMe_System/app_bundle/**` | unchanged |
| Runtime data and generated state | `OpMe_System/data/**`, `OpMe_System/reports/**` | unchanged/ignored runtime output |
| Demo upload samples | `OpMe_System/samples/**` | unchanged active demo input |
| Historical backups | `governance/archive/other8_wave1_pending/OpMe_System/backups/generated-artifacts/**` | archived |
| Original prototype work | `governance/archive/other8_wave1_pending/OpMe_System/work/original/**` | archived |

`app_bundle/native_launcher.c` and `app_bundle/assets/OpMeIcon.*` stay active
because `scripts/build_app_bundle.sh`, `scripts/install_app_entries.sh`, and
`scripts/generate_app_icon.py` use those paths as delivery build inputs. The
generated `.app` bundle and iconset remain ignored.

## OLD_TO_NEW_MAP

| Old path | New path | Status |
|---|---|---|
| `OpMe_System/backups/generated-artifacts/**` | `governance/archive/other8_wave1_pending/OpMe_System/backups/generated-artifacts/**` | archived |
| `OpMe_System/work/original/**` | `governance/archive/other8_wave1_pending/OpMe_System/work/original/**` | archived |

The exact 18 moved paths are bound in
`governance/run_manifests/GOV-OTHER8-S4PCT01-OPME-STRUCTURE-SIMPLIFICATION-20260625.json`
and trace back to `governance/stage_gates/s4pa/wave1_archive_manifest.json`.

## Preserved Paths

- `OpMe_System/backend/**` and `OpMe_System/frontend/**` are unchanged.
- `OpMe_System/app_bundle/**` remains active delivery-build source.
- `OpMe_System/samples/**` remains active demo input because the README exposes
  it as an upload path and the runtime may recreate `samples/`.
- `OpMe_System/data/**`, generated runtime reports, and local dependency caches
  remain governed by existing ignore/runtime rules.

## Stop Conditions Preserved

- Delivery package and runtime source responsibilities are separated: yes.
- Backend/frontend runtime behavior changed: no.
- Startup command changed without README sync: no.
- App bundle build source moved: no.
- Sample/demo input moved: no.

## Rollback

Rollback is a git revert of the S4PCT01 task commit. Manual rollback restores
each archived path from `governance/archive/other8_wave1_pending/OpMe_System/`
to the old `OpMe_System/` path according to `OLD_TO_NEW_MAP`, then verifies the
S4PAT02 checksums and the S4PCT01 run manifest.
