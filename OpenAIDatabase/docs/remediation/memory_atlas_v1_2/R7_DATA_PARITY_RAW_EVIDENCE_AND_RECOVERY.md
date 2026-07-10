# Memory Atlas v1.2 Remediation R7: Data Parity, Raw Evidence And Recovery

## Status

- Phase: `R7_DATA_PARITY_RAW_EVIDENCE_AND_RECOVERY`
- Phase result: `R7_COMPLETE_LOCAL_ONLY`
- Release result: `FAIL_REMEDIATION_REQUIRED`
- R6 closeout base: `7412a5c2be2104ac28be9645855e104b6dcf7483`
- R7 design commits: `a8b4608806`, `bbf9b4f24d`
- Verified recovery candidate: `f65668b927522641f1a9d0e6fc5b77031908dd68`
- Evidence binder before this record: `210d0d32e4d15946dfbc030820bdd4939a97adeb`
- Final observed `origin/main`: `37d757be958e1546b5263e86d2193663b184bbe8`
- Pre-record divergence: local `main` ahead 52 / behind 17.
- Push, merge, rebase, app reinstall and Cloudflare deployment: `false`.
- Next phase: `R8_OVERALL_ACCEPTANCE_AND_SINGLE_FINAL_DELIVERY`.

R7 replaces the empty/vacuous raw and parity claims with real, sanitized public evidence,
one immutable release snapshot and a tracked-files-only recovery rehearsal. It does not
claim that GitHub remote, the installed app or the online site contains this candidate.

## Authorized Source Boundary

| Source | Frozen proof | Public result |
|---|---|---|
| ChatGPT official export | ZIP SHA-256 `52f204dd8d78b76a79c6fc37e3e09987d3ab682c87098da017b894dd88c3a868`; 1,473,421,021 bytes | 379 conversations / 3,433 messages |
| Codex point-in-time snapshot | inventory SHA-256 `a0fba71aaf3761a93abc4c8a802ba49ed8400e73cc4325c5e26f215bec06736d`; 128 files / 654,725,175 bytes | 128 sessions / 17,963 messages / 80,075 tool calls / 131 public chunks / 111 canonical facet sessions |
| Future-agent evidence | R6 review SHA-256 `4de0b032088e5183a570ef10f212b7020df341f67204829f5fb034e24c5ac79f` | 1 canonical reviewer event |

The two original v1.2 source packages remain tracked and hash-verified: Roadmap
`699a8fe5...04a71` and TaskPack `38e21ae3...2472`. Private source locations,
credentials, cookies, original binary attachment bodies and private export bytes are not
published. GitHub recovery covers sanitized transcript text, source-package bytes,
derived data, release data, code and governance evidence.

## Public Raw Integrity

- Final public raw candidate: 512 files / 452,781,632 bytes.
- Deterministic binary omission markers: 23,893.
- Encrypted-content omissions: 23,620.
- Boundary-free hook-shaped token candidate redactions: 2.
- Full audit: 0 credential/private-text files, 0 unmarked binary files, 0 invalid
  omission markers, 0 invalid JSON and 0 oversize files.
- Immutable manifest: 512 entries, SHA-256
  `1a4fa71303903ca896c82640f7b4550cee47f3cc8ec600f81d03f7603e120c96`.
- Hash ledger: 512 entries, 0 drift, 0 deletion and 0 new unledgered files.
- Four rejected materialization attempts remain in provenance; two rejected manifest
  artifacts are tracked, and neither is the accepted manifest.

## Immutable Release And Parity

- Release ID: `memory-atlas-v1-2-r7-20260710`.
- Snapshot SHA-256:
  `b608631fded9e116d350895be20e6e61be3c7e42ba651ccdf7fc52afd8fefcbc`.
- Snapshot size: 1,905,337 bytes.
- Release manifest SHA-256:
  `dcc1b2f71af18de82e0987fdf7becc451f82288ec90992d4931b18539ac3ac50`.
- Derived, immutable release, temporary local-runtime candidate and Pages build candidate
  all matched the exact snapshot hash and byte size.
- Canonical events: 491 = 379 ChatGPT + 111 Codex + 1 future-agent event.
- Snapshot: 278 active memories / 379 conversations / 128 Codex sessions / 435 nodes /
  2,325 edges.

## Tracked-Only Recovery

Recovery archived commit `f65668b927522641f1a9d0e6fc5b77031908dd68` using
`git archive`; 8,372 tracked files and 0 working-tree-only files were copied. In the
temporary recovered tree, both source packages were restored, the 512-file raw audit and
ledger passed, a fresh `npm ci --ignore-scripts` succeeded, the frontend built, and the
Pages candidate matched the immutable snapshot hash. Temporary recovery output and npm
cache were removed.

The recovery proof intentionally names a verified functional candidate rather than
claiming self-recovery of the later evidence record that describes that proof. Commit
`210d0d32` binds the evidence to the candidate. Exact recovery from the final pushed
remote HEAD remains an R8 gate; `remote_clone_verified=false` and
`r8_delivery_performed=false` are preserved.

## Requirement Delta

R7 promotes exactly five requirements:

| Requirement | Before | After |
|---|---:|---:|
| `S03-AC01` | FAILED | VERIFIED |
| `S03-AC02` | PARTIAL | VERIFIED |
| `S04-AC02` | NOT_VERIFIED | VERIFIED |
| `S04-AC03` | PARTIAL | VERIFIED |
| `S05-AC01` | PARTIAL | VERIFIED |

Aggregate after R7: `VERIFIED 53 / PARTIAL 2 / FAILED 3 / NOT_VERIFIED 0`.
The remaining five criteria are `S03-AC05`, `S04-AC04`, `S10-AC04`, `S14-AC02` and
`S14-AC05`; they remain R8 work.

## Verification And Review

- R7 raw/release/recovery unit suites: PASS.
- Workflow/runtime regression suite: 74 tests PASS.
- Visual/data unit regression: 4 tests PASS.
- Public raw audit, manifest/ledger audit, release verification and snapshot parity: PASS.
- `npm run lint` and production build: PASS; only the existing chunk-size warning remains.
- R6 visual workflows, R1 Home multi-viewport, R3 commands, R4 proposals, R5 Owner Daily,
  Stage 7 visual/full gates and privacy scan: PASS.
- Target viewports: `1470x661`, `1440x900`, `390x844`; rendered workflow gates report
  zero overlap, clipping and horizontal overflow.
- Independent review of `bbf9b4f2..210d0d32`: High 0 / Medium 0 / Low 1. The Low is
  the explicit functional-candidate/evidence-binder ordering documented above.

## Evidence

- `机器治理/证据与日志/remediation/v1_2_r7/status.json`
- `机器治理/证据与日志/remediation/v1_2_r7/browser_regression.json`
- `机器治理/证据与日志/remediation/v1_2_r7/source_provenance.json`
- `机器治理/证据与日志/remediation/v1_2_r7/release_verification.json`
- `机器治理/证据与日志/remediation/v1_2_r7/snapshot_parity.json`
- `机器治理/证据与日志/remediation/v1_2_r7/recovery/status.json`
- `机器治理/证据与日志/remediation/v1_2_r7/requirements_gap_delta.csv`
- `机器治理/证据与日志/remediation/v1_2_r7/independent_review.md`

## Stop Boundary

R7 stops here. Do not reconcile remote history, push, reinstall, deploy, change the
online snapshot or restore overall completion semantics in this phase. R8 must reconcile
both histories without force-push, run all 58 gates, make the single final GitHub main
delivery, recover from the pushed remote HEAD, reinstall/deploy that exact commit and
repeat the acceptance suite online before the goal can complete.
