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
- Added a T1301/A202 source-withdrawal and counter-evidence fail-closed publication rehearsal; disputed raw source snapshots, disputed evidence-chain rows and unreviewed evidence-chain counter-evidence now block reviewed relationship publication before relationship, fact-version or operation-log writes.
- Added a T1303/A204-A205 release-manager activation preflight; it aggregates A202 signed-decision, A026/A027 gold-quality, A209 soak and A210 brand-clearance evidence and fails closed while any external release gate is missing.
- Added a T905/A119-A120 release rehearsal: every PostgreSQL migration suffix now has a CI-bound rollback/re-upgrade integration test, and README clean-start commands are machine-checked against Makefile and EEI validation workflow bindings.
- Added a T1301/A202 candidate-source-anchor coverage contract for signed release decision bundles; passage-level reviews must cover `GV-SNAPSHOT-001..004` from `golden_vertical_fact_candidates.json`, while A202 remains blocked on real source/license/owner/legal evidence.

## Legacy Task Pack v4.2.0 - 2026-06-19

- Historical EEI Task Pack and prototype governance snapshot preserved in Git history and legacy `data/*.csv` evidence inputs.
- Current counts and active governance facts must be read from `docs/governance/*`, not this changelog.
