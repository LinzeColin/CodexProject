# PHASE_S2PLT02_CONTROLLED_LAUNCHD_KICKSTART_TIMEOUT

- Task: `S2PLT02-CONTROLLED-LAUNCHD-KICKSTART-TIMEOUT`
- Parent gate: `S2PLT02`
- Acceptance id: `ACC-S2PLT02-2D`
- Generated at: `2026-07-01T11:06:10+10:00`
- Scope: record the owner-authorized controlled launchd kickstart attempt without SMTP send enabled.

## Result

| Field | Value |
| --- | --- |
| `launchctl kickstart` rc | `0` |
| Bounded wait | `180s` |
| Daily runner exit observed | `false` |
| Final process count | `0` |
| Final LaunchAgents disabled | `true` |
| SMTP send enabled | `false` |
| Scheduler proof ready | `false` |
| Counts toward S2PLT02 terminal proof | `false` |
| Post-closeout audit state hash | `86c26aed6038f185f993fc7e7bb3f3eb5a849fd9d6438a2fb6bcf2ddedcbdaa9` |

## Nonterminal Reasons

- The daily runner did not exit within the bounded 180 second window.
- The attempt started from a checkout that became stale against `origin/main` after the preceding evidence commit was pushed.
- No valid scheduler run manifest was produced.

## Safety Closeout

- The running ADP local-runner process was terminated.
- `ADP_ALLOW_SMTP_SEND=false` remained in the persistent env file.
- `com.linze.adp.local.daily`, `com.linze.adp.local.health`, and `com.linze.adp.local.watchdog` were disabled after the attempt.
- No SMTP send, terminal proof artifact, scheduler install, Release, restore, DAILY_OPERATION, Stage2/S3 acceptance, or integrated production acceptance was produced.

## Evidence

- Run manifest: [`ADP-S2PLT02-CONTROLLED-LAUNCHD-KICKSTART-TIMEOUT-20260701.json`](../../../governance/run_manifests/ADP-S2PLT02-CONTROLLED-LAUNCHD-KICKSTART-TIMEOUT-20260701.json)
- Local evidence directory: `/tmp/adp_s2plt02_scheduler_capture_yUlAB2`
- Prior canonical alignment: [`PHASE_S2PLT02_CANONICAL_LAUNCHAGENT_CHECKOUT_ALIGNMENT.md`](PHASE_S2PLT02_CANONICAL_LAUNCHAGENT_CHECKOUT_ALIGNMENT.md)

## Remaining Blockers

- Capture a valid real scheduler proof manifest from a current-main canonical checkout.
- Build, review, write, and validate `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json`.
