# Changelog

## 0.1.0 - 2026-06-20

- Established CodexProject canonical governance baseline under `docs/governance/`.
- Separated product version `0.1.0` from legacy Task Pack label `v4.2.0`.
- Mapped legacy model, formula, parameter, task, acceptance, risk, and release-gate evidence into validator-readable governance files.
- Converted legacy governance Markdown entrypoints into compatibility indexes to prevent duplicate editable fact sources.
- No model runtime logic, business behavior, data generation, or product feature code changed.
- Added T1307/A209 4h operator soak evidence: 48/48 checkpoint windows PASS over 14400 seconds; A209 remains open until 24h operator soak evidence and CI validation exist.
- Repaired the T1301/A202 operator-source capture fixture hash after G2 PostgreSQL CI flagged `NVDA-ANCHOR-001 source_text_sha256 does not match text`; 24h soak remains a background evidence task and does not block this fixture/CI repair.
- Added a T1301/A202 fail-closed operator/legal review packet for selected live official-source evidence; it records seven required closure gates and keeps relationship publication and legal clearance disabled.
- Closed T1304/A206 scheduler functionality independently from A209 soak: lease, auto wake, idempotency, heartbeat, retry cap, dead-letter, graceful shutdown, outbox dispatch, Docker Compose worker binding and supervisor execution are treated as DONE while 24h soak remains A209-only.
- Added a T1301/A202 plus T1309/A210 signed release decision bundle contract; it enumerates the exact source-license, passage-level, owner, legal and brand signed inputs still required, while keeping `release_ready=false` until A209 24h soak and release-manager activation are separately satisfied.
- Added a T904/A026-A027 gold-quality evaluation contract; it reports precision, recall and source coverage, but keeps A026/A027 `IN_PROGRESS` until production human-labeled gold sets meet the 50/95% entity and 100/90% relationship gates.
- Added a T904/A026-A027 production gold-label intake template artifact and validator commands; the template is `TEMPLATE_ONLY` and keeps `release_gate_closure_allowed=false`.
- Added a T1309/A210 brand-clearance intake template and validator commands; the template covers CN/US/EU/UK/AU trademark knockout, company/domain/social/app-store/GitHub/npm/PyPI searches, phonetic/semantic review and legal/owner decision fields while keeping `release_gate_closure_allowed=false`.
- Added a T1301/A202 source-withdrawal and counter-evidence fail-closed publication rehearsal; disputed raw source snapshots, disputed evidence-chain rows and unreviewed evidence-chain counter-evidence now block reviewed relationship publication before relationship, fact-version or operation-log writes.
- Added a T1303/A204-A205 release-manager activation preflight; it aggregates A202 signed-decision, A026/A027 gold-quality, A209 soak and A210 brand-clearance evidence and fails closed while any external release gate is missing.
- Added a T905/A119-A120 release rehearsal: every PostgreSQL migration suffix now has a CI-bound rollback/re-upgrade integration test, and README clean-start commands are machine-checked against Makefile and EEI validation workflow bindings.
- Added a T1301/A202 candidate-source-anchor coverage contract for signed release decision bundles; passage-level reviews must cover `GV-SNAPSHOT-001..004` from `golden_vertical_fact_candidates.json`, while A202 remains blocked on real source/license/owner/legal evidence.
- Added a T1301/A202 release-decision intake template and validator path; the template covers source-license review, passage-level relationship review, production owner sign-off and legal release clearance fields while keeping `release_gate_closure_allowed=false`.
- Closed `GOV-SEMANTIC-EEI-001` machine semantic coverage for active parameters and formulas: motion parameters now extract from `config/ui/motion-tokens.json`, FORM-012 has machine implementation refs, and production release gates remain open.
- Added a T1301/A202 operator-review candidate queue: the packet now binds `GV-FACT-001..002` to required official-source anchors `GV-SNAPSHOT-001..004` for human/legal review, while publication, legal clearance and release readiness remain fail-closed.
- Added a T1307/A209 operator-soak progress monitor: the detached 24h soak now has a read-only status contract for PID, successful windows, remaining windows, resume command and `release_gate_closed_by_monitor=false`; A209 remains open until full 24h evidence validates.
- Added a T1307/A209 operator-soak supervisor: it observes the existing 24h PID without double-starting, dry-runs recovery by default, requires explicit `--auto-resume --execute` for paused-run recovery, and keeps `release_gate_closed_by_supervisor=false`.
- Bound the A209 supervisor into clean-room release packaging and governance evidence so `scripts/supervise_operator_soak.py` is included in release artifacts while A209 remains open.
- Added a T1307/A209 operator-soak watchdog: it can run detached in the background, checks every 300 seconds, resumes only paused successful checkpoints when explicitly launched with `--execute --auto-resume`, reports stale live PIDs without killing them, and keeps `release_gate_closed_by_watchdog=false`.
- Upgraded `scripts/apply_model_config.py` from dry-run-only preview to a fail-closed T1303/A204-A205 operator CLI: `--dry-run` remains hash-bound and non-writing, while explicit `--execute` requires PostgreSQL and delegates draft creation, transactional activation and score recompute enqueue to the existing repository transaction layer.
- Added a T1307/A209 background heartbeat artifact: `scripts/record_operator_soak_heartbeat.py` records the live operator/watchdog PIDs, current 24h window progress and non-closure semantics into `artifacts/tests/a209/t1307_operator_soak_background_progress.json`; current heartbeat shows `88/288` windows PASS and keeps A209 `IN_PROGRESS`.
- Synchronized A209 heartbeat governance for CI: registered operational parameters `PARAM-069` through `PARAM-071`, refreshed clean-room release evidence to `package_paths=418`, and kept `release_gate_closed_by_background_heartbeat=false`.
- Updated the T1303/A204-A205 release-manager activation validator so it accepts evidence-derived READY preflight states only when A202, A026/A027, A209 and A210 gate artifacts are all release-ready; the committed repository preflight remains `RELEASE_MANAGER_ACTIVATION_BLOCKED`.
- Bound A209 background heartbeat into the T1303/A204-A205 release-manager preflight as source-hashed non-closure context; current heartbeat shows `92/288` windows PASS, `0` failed and `counts_as_release_ready=false`.

## Legacy Task Pack v4.2.0 - 2026-06-19

- Historical EEI Task Pack and prototype governance snapshot preserved in Git history and legacy `data/*.csv` evidence inputs.
- Current counts and active governance facts must be read from `docs/governance/*`, not this changelog.
