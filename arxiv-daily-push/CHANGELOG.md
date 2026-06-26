# Changelog

## Unreleased - 2026-06-24

- Hardened the `S2PMT02` / Stage 1 runtime backup path for inherited A-014 by copying supporting files to source-hash-prefixed manifest paths so different directories with the same filename are preserved without silent overwrite; production backup/restore, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Hardened the `S2PMT02` / Stage 1 runtime restore path for inherited A-001/A-002 by rejecting manifest database paths outside the backup root and validating a temporary restored SQLite file before atomic target replacement; production restore, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Synced post-merge `S2PBT05` owner/status governance wording so `OWNER_STATUS`, `ASSURANCE_STATUS`, `delivery_tasks`, and `model_registry` no longer describe `S2PBT05` as missing after PR #224; remaining blockers stay inherited P0/P1, full replay, 120 mail previews, terminal source states, S2PLT04, S2PMT07, and integrated production acceptance.
- Completed `S2PBT05` D1 source-domain qualification receipt from completed `S2PBT01` / legacy `S2P1T01` bioRxiv and medRxiv real no-send replay/shadow evidence, removing only the `s2pbt05_missing` S2PLT01 blocker while keeping inherited V7.1 P0=8/P1=37, missing full replay execution, missing 120 mail-preview proof, missing terminal source-state proof, formal D1 production inclusion, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contract files, DAILY_OPERATION, Stage2 production acceptance, and integrated production acceptance unchanged.
- Recorded `S2PLT01` fail-closed full-system replay entry precheck with machine-verifiable blockers that originally included missing `S2PBT05`, inherited V7.1 P0=8/P1=37, missing full 30-day replay execution, missing 120 mail-preview proof, and missing terminal source-state proof while keeping replay execution, S2PLT01 acceptance, S2PLT04 completion, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contract files, inherited P0/P1 closure, DAILY_OPERATION, Stage2 production acceptance, and integrated production acceptance unchanged.
- Recorded `S2PMT07` fail-closed final gate precheck with machine-verifiable blockers for missing independent reviewer proof, inherited V7.1 P0=8/P1=37, missing S2PLT04 completion, missing final acceptance bundle, missing independent signoff, and missing independent final command execution while keeping SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contract files, inherited P0/P1 closure, DAILY_OPERATION, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PMT06` local Chinese owner UX and safe-control evidence with first-screen status, fixed top/bottom navigation, breadcrumbs, status feedback states, recoverable error cards, safe config-change flow, append-only revision ledger, queue search/filter/sort/export/drilldown, safe retry/cancel/requeue/skip/regenerate previews, feedback visibility, accessibility/mail-client compatibility, source-to-ROI traceability, and no-production side-effect gates while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contract files, inherited P0/P1 closure, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PMT05` local pressure/fault/time/E2E evidence with deterministic load/stress/spike profiles, accelerated local 24h soak coverage, dual scheduler race protection, SMTP accepted-before-local-commit crash-window handling, ENOSPC/read-only/SQLITE_BUSY/corrupt-artifact fault injection, Australia/Sydney DST and clock-skew policy, 35-day 3+1/weekly/monthly/review/action/ROI count conservation, backpressure/degradation gates, deterministic isolation, and no-production side-effect gates while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, V7.1/V7.2 contract files, Stage2 production acceptance, inherited P0/P1 closure, and integrated production acceptance unchanged.
- Completed `S2PMT04` local automatic lifecycle and cache-cleanup evidence with disabled dry-run launchd wake path, STOPPED/STARTING/RECOVERING/LEADER/RUNNING/DRAINING/CHECKPOINTING/CLEANING state sequence, startup reconciliation, durable shutdown receipts, whitelist/symlink guarded dry-run cache cleanup, parseable launchd plist generation, and no-production side-effect gates while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, V7.1/V7.2 contract files, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PJT05` local-only monthly cognitive delta, capability growth, economic conversion, and forecast review evidence with passing S2PJT04 weekly reports, month-start/month-end cognitive snapshots, changed viewpoints with evidence, capability growth traceability, at least one verifiable calculated conversion, forecast review, next-month focus, deterministic monthly report hash, and no-production side-effect gates while keeping SMTP, scheduler, Release, DB migration, public schema, queue mutation, ranking, source adapters, Email V1 runtime/frontstage, CURRENT, V7.1/V7.2 contract files, owner-experience final acceptance, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PJT02` local-only review schedule and due queue evidence with default `1/3/7/14/30/90` intervals, feedback-adjustment readiness, due-today/7-day/overdue/completed count recomputation, deterministic due queue hash, and no-scheduler/no-production side-effect gates while keeping SMTP, Release, DB migration, public schema, queue mutation, ranking, source adapters, Email V1 runtime/frontstage, CURRENT, V7.1/V7.2 contract files, owner-experience final acceptance, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PJT01` local-only lifecycle state evidence for review/action/asset/conversion/mastery states with append-only history, count conservation, ledger mapping, dry-run rollback migration proof, and no-production/no-schema/no-email-frontstage side-effect gates while keeping real DB migration, SMTP, scheduler, Release, queue mutation, ranking, source adapters, Email V1 runtime/frontstage, CURRENT, V7.1/V7.2 contract files, owner-experience final acceptance, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PIT02` local-only runtime dashboard evidence for the Chinese owner center by aggregating S2PIT01 user-center evidence, Stage 1 runtime audit, watchdog, read-only storage inspect, and explicit production-boundary state into a local dashboard report and `00_用户中心/01_当前状态.md` while keeping live service probes, SMTP, scheduler, Release, public schema, DB migration, queue mutation, ranking, source adapters, Email V1 runtime/frontstage, CURRENT, V7.1/V7.2 contract files, owner-experience final acceptance, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PIT01` metadata-only/local Chinese user-center and one-edit owner-control entry evidence with `00_用户中心`, `00_只改这里`, four separated control domains, two-click reachability, `config/owner_controls.yaml` as the only editable fact source, read-only SQLite inspect input, compatible config compilation, and no-production/no-schema/no-email-frontstage side-effect gates while keeping CURRENT, V7.1/V7.2 contract files, SMTP, scheduler, Release, DB migration, public schema, queue mutation, source adapters, Email V1 runtime, owner-experience final acceptance, Stage2 production acceptance, and integrated production acceptance unchanged.
- Completed `S2PET04` / legacy `S2P4T04` metadata-only D4 US-TP and D4 qualification evidence across OSTP, BIS, FTC, FCC, CISA, and CHIPS Program with required technology policy signals, upstream S2PET01-S2PET03 gates, D4 30-date replay, 2-day shadow, B4/B5/B6 routing, 35/15/30/20 budget explanations, official identity, traceability, and no-production/no-schema side-effect gates while keeping live source fetching, D4 production inclusion, SMTP, scheduler, Release, public schema, queue mutation, V7.1/V7.2 contracts, Email V1 runtime/frontstage, and integrated production acceptance unchanged.
- Completed `S2PET03` / legacy `S2P4T03` metadata-only D4 US-FM financial, market, and macro source backbone evidence across SEC/EDGAR, Federal Reserve, Treasury, CFTC, OCC, FDIC, and CFPB with SEC form classification, CIK and Accession identifiers, company/fund/asset relations, upstream S2PET02 gate, official identity, traceability, and no-production/no-schema/no-investment-advice/no-trading side-effect gates while keeping live source fetching, paid market data, D4 production inclusion, SMTP, scheduler, Release, public schema, queue mutation, V7.1/V7.2 contracts, Email V1 runtime/frontstage, and integrated production acceptance unchanged.
- Completed `S2PET02` / legacy `S2P4T02` metadata-only D4 US-LG cross-agency legal backbone evidence across Federal Register, Regulations.gov, GovInfo, and Congress.gov with Docket/FR/CFR/bill/report/public-law/certified-text relations, upstream S2PET01 gate, official identity, traceability, and no-production/no-schema/no-legal-advice side-effect gates while keeping live source fetching, PDF/full-text download, D4 production inclusion, SMTP, scheduler, Release, public schema, queue mutation, V7.1/V7.2 contracts, Email V1 runtime/frontstage, and integrated production acceptance unchanged.
- Completed `S2PET01` / legacy `S2P4T01` metadata-only D4 US-TA official technology-agency source foundation evidence across NSF, DARPA, DOE, NIH, NASA, NIST, USPTO, and FDA with required signal taxonomy, official identity, traceability, and no-production/no-schema/no-email-frontstage side-effect gates while keeping live source fetching, D4 production inclusion, SMTP, scheduler, Release, public schema, queue mutation, V7.1/V7.2 contracts, Email V1 runtime/frontstage, and integrated production acceptance unchanged.
- Repaired `S2PAT07` V7.2 Email V1 root-governance pointers after `S2PHT01V1.1-T01-T05` reached main: CURRENT, V7.2 root lock, product contract, roadmap, current pointer registry, migration matrix, handoff, README, validator, and hashes now agree that Email V1 is `EMAIL_LEARNING_V1_MERGED_TO_MAIN_NO_PRODUCTION_SIDE_EFFECTS` while `S2PCT02` remains the global current task and SMTP, scheduler, Release, runtime mail code, public schema, DB/migration, V7.1, and integrated production acceptance remain unchanged.
- Completed `S2PGT05` / legacy `S2P6T02` private cross-board calibration and explainable queue evidence with B1-B6 percentile calibration, D1-D4 source balance, waiting credit, selected/queued/deferred readable reasons, deterministic ordering, stable queue hashing, and no-production/no-schema/no-email-frontstage side-effect gates while keeping production ranking, real queue mutation, source-domain production inclusion, SMTP, scheduler, Release, V7.2 contracts, Email V1 frontstage/runtime, and integrated production acceptance unchanged.
- Completed `S2PGT04` private support/refute/frontier delta and signal-resonance evidence with route linkage, required delta-type coverage, supported/refuted evidence states, resonance groups, signal-strength, explanation, evidence-ref, and no-production/no-schema/no-email-frontstage side-effect gates while keeping public schema migration, production queues, SMTP, scheduler, Release, source-domain production inclusion, V7.2 contracts, Email V1 runtime/frontstage, and integrated production acceptance unchanged.
- Completed `S2PGT03` private D1-D4 to B1-B6 multi-label routing evidence with source-domain, B1-B3 primary board, B4-B6 cross-cutting board, reason-code, explanation, evidence-ref, source-domain mapping, and no-production/no-schema side-effect gates while keeping public schema migration, production queues, SMTP, scheduler, Release, source-domain production inclusion, V7.2 contracts, Email V1 runtime, and integrated production acceptance unchanged.
- Completed `S2PGT02` / legacy `S2P6T01` private cross-source identity-resolution and knowledge-graph relation spine evidence across DOI, PMID, arXiv, Chinese document number, Federal Register document number, and CIK identifiers with duplicate-canonical, relation-evidence, idempotency, and no-production/no-schema side-effect gates while keeping public schema migration, production queues, SMTP, scheduler, Release, source-domain production inclusion, V7.2 contracts, and integrated production acceptance unchanged.
- Completed `S2PGT01` EvidencePacket V2 compatibility evidence with private D1-D4 source-domain report gates, required packet fields, metadata/abstract/full-text/cross-source evidence-level labels, old arXiv compatibility proof, and no-production/no-schema side-effect gates while leaving D4 source adapters, public schema migration, SMTP, scheduler, Release, queue mutation, V7.2 contracts, and integrated production acceptance unchanged.
- Completed `S2PFT05` / legacy `S2P5T05` full D3 China official-source governance qualification with C0-C4 component coverage, quota roles, quota balance, health balance, elimination explanations, fallback route, 30-date replay, and metadata-only gates while keeping formal D3 production inclusion, Stage 2 production acceptance, integrated production acceptance, SMTP, Release, scheduler, queue/schema mutation, public schema migration, V7.2 contract files, mail runtime, and production side effects disabled.
- Completed `S2PFT04` / legacy `S2P5T04` China special-zone metadata-only discovery evidence with zone ID, zone type, authority role, policy focus area, parent-city mapping, health tier, authority, dedupe, and metadata-only gates while keeping D3 full acceptance, Stage 2 production acceptance, SMTP, Release, scheduler, queue/schema mutation, public schema migration, V7.2 contract, mail runtime, and production side effects disabled.
- Completed `S2PFT03` / legacy `S2P5T03` first 24 China key-city metadata-only coverage evidence with city ID, alias, local department role, region group, region weight, health tier, authority, and metadata-only gates while keeping D3 full acceptance, Stage 2 production acceptance, SMTP, Release, scheduler, queue/schema mutation, public schema migration, special-zone, V7.2 contract, and production email side effects disabled.
- Completed `S2PFT02` / legacy `S2P5T02` Hong Kong and Macau independent profile evidence with separate jurisdiction identity, language profile, legal-system state, government-structure, authority, metadata-only, and mainland-template reuse gates while keeping D3 full acceptance, Stage 2 production acceptance, SMTP, Release, scheduler, queue/schema mutation, public schema migration, city, special-zone, V7.2 contract, and production email side effects disabled.
- Recorded PR #152/#153 as merged to `main`, confirming audited M1-M4 mail paths use `EMAIL_LEARNING_V1` while SMTP, scheduler, Release, public schema, DB/migration, CURRENT, V7.1, and integrated production acceptance remain unchanged.
- Completed `S2PFT01` / legacy `S2P5T01` China mainland provincial template coverage evidence for 31 provincial-level IDs while keeping D3 full acceptance, Stage 2 production acceptance, SMTP, Release, scheduler, queue/schema mutation, public schema migration, HK/MO, city, special-zone, V7.2 contract, and production email side effects disabled.
- Implemented `S2PHT01V1.1-T02-T04` EMAIL_LEARNING_V1 M1-M4 renderer: shared content object, responsive HTML/plain text template, ChatGPT new-chat links, arXiv/PDF links, candidate queue summary compatibility, and forbidden visible marker gate.
- Routed audited daily delivery, Stage1 B1 report email, local runner previews, scheduled readiness checks, and Stage2 shadow previews through Email V1 while keeping SMTP transport, scheduler trigger/production enablement, Release upload, source adapters, ranking, queue algorithms, public schema, DB/migrations, CURRENT, and V7.1 unchanged.
- Completed `S2PDT04` / legacy `S2P3T04` China official D3 readiness review evidence without granting D3 source-domain production acceptance.
- Added `adp stage2-china-d3-readiness-review`, 30-date replay, 2-day shadow, authority, B2-B6 board-routing, metadata-only/no-production gates, model/formula/parameter governance registrations, V7.2 revalidation receipt, and S2PDT04 manifest/phase evidence while keeping D3 core acceptance, Stage 2 production acceptance, SMTP, Release, schedule, queue mutation, public schema migration, PDF/full-text download, paid API use, paywall bypass, V7.1 CURRENT switching, V7.2 mail/schema pre-run, and production inclusion disabled.
- Completed `S2PDT03` / legacy `S2P3T03` China legal metadata, version/effectivity, reprint relation, and old-conclusion update shadow evidence.
- Added `adp stage2-china-legal-metadata-relation-shadow`, legal status and relation fixtures, legal status taxonomy/version effectivity/reprint relation/forced update/metadata-only gates, model/formula/parameter governance registrations, and S2PDT03 manifest/phase evidence while keeping legal advice, D3 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, queue mutation, schema migration, PDF/full-text download, paid API use, paywall bypass, V7.1 CURRENT switching, V7.2 mail/schema pre-run, and production inclusion disabled.
- Advanced V7.1 root routing to `S2PDT04` / legacy `S2P3T04` China official D3 source-domain readiness review.
- Completed `S2PDT02` / legacy `S2P3T02` China C1 central department and key ministry metadata-only source map evidence.
- Added `adp stage2-china-c1-department-source-map`, C1 department fixtures, sector coverage/official identity/alias/industry route/board route/metadata-only gates, model/formula/parameter governance registrations, and S2PDT02 manifest/phase evidence while keeping D3 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, queue mutation, schema migration, PDF/full-text download, paid API use, paywall bypass, V7.1 CURRENT switching, V7.2 mail/schema pre-run, and production inclusion disabled.
- Advanced V7.1 root routing to `S2PDT03` / legacy `S2P3T03` China legal metadata, effectivity/version, and reprint relation shadow.
- Completed `S2PCT07` D2 source-domain qualification and cross-type calibration as qualification-ready no-production evidence.
- Added `adp stage2-d2-source-domain-qualification`, upstream/domain/replay/shadow/forced-event/queue/type calibration gates, model/formula/parameter governance registrations, and S2PCT07 manifest/phase evidence while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, queue mutation, schema migration, PDF/full-text download, paid API use, paywall bypass, marketing-material acceptance, and production inclusion disabled.
- Advanced V7.1 root routing to `S2PDT01` / legacy `S2P3T01` China C0 national authoritative backbone.
- Completed `S2PCT06` authoritative research institution, laboratory, industry technical report, and product technical note metadata-only no-send shadow evidence.
- Added `adp stage2-authoritative-reports-shadow`, authoritative technical report fixtures, publisher identity/interest relation/evidence level/traceability gates, model/formula/parameter governance registrations, and S2PCT06 manifest/phase evidence while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, video, PDF/full-text download, paid API use, paywall bypass, marketing-material acceptance, and production inclusion disabled.
- Advanced V7.1 root routing to `S2PCT07` D2 source-domain qualification and cross-type calibration.
- Completed `S2PCT05` engineering open-source, code, benchmark, model-card, release, and standards public-signal metadata-only no-send shadow evidence.
- Added `adp stage2-engineering-signals-shadow`, engineering signal fixtures, officiality/version/paper-relation/reproducibility gates, model/formula/parameter governance registrations, and S2PCT05 manifest/phase evidence while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, video, PDF/full-text download, paid API use, repository clone, and paywall bypass disabled.
- Advanced V7.1 root routing to `S2PCT06` authoritative research institution and industry technical report framework.
- Completed `S2PCT04` / legacy `S2P2T04` top-journal profile, publication relation, correction, and retraction metadata-only no-send shadow evidence across Nature, Science, and The Lancet shadow batches.
- Added profile taxonomy for research, review, editorial, news, correction, and retraction; relation edges for original publication, discusses, corrects, and retracts; and forced-event updates where correction requires revision and retraction invalidates prior conclusions.
- Added `adp stage2-top-journal-profile-shadow`, profile relation fixtures, prior state fixtures, model/formula/parameter governance registrations, and S2PCT04 manifest/phase evidence while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, video, PDF/full-text download, and paywall bypass disabled.
- Advanced V7.1 root routing to `S2PCT05` engineering open-source, code, benchmark, model-card, release, and standards public-signal framework.
- Completed `S2PCT03` / legacy `S2P2T03` The Lancet main-journal metadata-only no-send shadow evidence using official public Lancet Online First RSS and current issue RSS cross-checks.
- Added Lancet medical article-type gates, DOI-query-ready PubMed relation metadata, duplicate DOI/source handling, separate Lancet shadow queue/ledger/email preview persistence, and `adp stage2-lancet-shadow-daily`.
- Verified focused top-journal/stage2 tests, semantic governance preparation, and a live Lancet RSS no-send canary while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, video, PubMed full-record harvesting, PDF/full-text download, and paywall bypass disabled.
- Advanced V7.1 root routing to `S2PCT04` / legacy `S2P2T04` journal profile, publication relation, correction, and retraction modeling.
- Completed `S2PCT02` / legacy `S2P2T02` Science main-journal metadata-only no-send shadow evidence using the official public Science RSS feed.
- Added Science article-type gates for Research Article, Report, Review, and Perspective, duplicate DOI/source handling, separate Science shadow queue/ledger/email preview persistence, and `adp stage2-science-shadow-daily`.
- Verified focused top-journal/stage2 tests, semantic governance, and a live Science RSS no-send canary while keeping D2 source-domain acceptance, Stage 2 production acceptance, SMTP, Release, schedule, video, PDF/full-text download, and paywall bypass disabled.
- Advanced V7.1 root routing to `S2PCT03` / legacy `S2P2T03` The Lancet metadata-only shadow, and hardened dashboard generation so stale owner decisions do not override the next task after a task transition.
- Added `S2PCT01` / legacy `S2P2T01` V7.1 D2 top-journal shadow foundation using official public Nature RSS metadata, filtering to `s41586-*` main-journal research article links only.
- Added `adp fetch-top-journal-latest` and `adp stage2-top-journal-shadow-daily` with separate no-send queue, ledger, dry-run package, and email preview persistence; kept Stage 2 production acceptance, SMTP, Release, schedule, and video disabled.
- Verified a live Nature RSS no-send canary with 3 real `s41586` source IDs and local queue/ledger/email preview artifacts under `/tmp`.
- Implemented the `S2P1T01` bioRxiv/medRxiv source-promotion foundation: metadata-only preprint adapter, disabled Stage 2 source registry entries, promotion gate, separate shadow daily queue/ledger/email preview path, and fixture tests.
- Verified one live bioRxiv and one live medRxiv fixed-interval canary plus one no-send shadow daily canary; kept formal production inclusion blocked until 30-date terminal replay and 48h shadow evidence pass.
- Added `adp local-runner preflight|daily|launchd-package` for Stage 1 local Mac + Codex/local runner operation.
- Added local queue, local content ledger JSONL, per-run report, and plain/HTML email preview persistence under an owner-controlled state directory.
- Added a disabled launchd package draft and 2026-06-30 migration runbook without installing the scheduler, sending production SMTP, enabling GitHub cloud scheduled production, uploading Release artifacts, or generating video.
- Set the next executable roadmap task to `S2P1T01` after `ADP-S1P5T05` local production and migration prep.

## 0.23.1 - 2026-06-23

- Reopened strict Stage 1 acceptance for `S1P5T03-R REAL_ARXIV_30_DAY_BACKFILL_AND_LEDGER_RECONCILE`.
- Added cloud-runner real historical arXiv 30-day backfill workflow, replay CLI, tests, and persisted `CONTENT_LEDGER.csv` rows for 30 selected and 269 queued candidates.
- Recorded GitHub/cloud run `28027759062` artifact `7821452823` as the strict 30-day backfill proof; kept production scheduling, SMTP send, Release upload, Stage 2, and video generation disabled.
- Implemented `ADP-PHASE12-EMAIL-HUMAN-FORMAT-036`: Stage 1 owner email now renders as a Chinese teaching brief and hides ROI score, Release, video, delivery-policy, and backend wording from the frontstage.

## 0.23.0 - 2026-06-23

- Recorded PR #82 GitHub/cloud artifact `7818287996` as
  `ARXIV_PRODUCTION_ACCEPTED` for Stage 1 arXiv.
- Added project-root `功能清单`, `开发记录`, and `模型参数文件` human entry files,
  with the V6 roadmap rendered directly in `开发记录`.
- Hardened scheduled/trial workflows so all-arXiv fallback collection uses
  `ADP_ARXIV_MAX_RESULTS_PER_CATEGORY:-3`, matching accepted evidence volume.
- Kept production scheduling disabled and fail-closed until GitHub repo
  variables/secrets are explicitly verified or enabled.
- Added `adp build-stage1-accelerated-acceptance` for S1P5T04 accelerated real-arXiv acceptance evidence.
- Updated the live all-arXiv cloud dry-run workflow to collect up to 3 items per primary archive and build a 30-sample accelerated acceptance artifact on GitHub runner.
- Kept production scheduling disabled, sent no new email, and preserved Stage 1 text-only/no-video/no-Release requirements.

## 0.22.0 - 2026-06-23

- Converted S1-12 production enablement to Stage 1 text-only delivery: all-arXiv scan, candidate queue, ROI-ranked lead selection, Chinese teaching email, and GitHub Actions text artifacts.
- Removed video/MP4 and GitHub Release upload as production-readiness requirements for Stage 1; Gmail SMTP remains the only controlled frontstage side effect.
- Kept production scheduler and `ARXIV_PRODUCTION_ACCEPTED` disabled pending PR CI, manual controlled SMTP test evidence, and later acceptance gates.
- Imported the V6 task-numbering roadmap under `docs/pursuing_goal/`, locked current progress to `S1P5T04`, and recorded GitHub/cloud-runner manual Gmail SMTP run `28002478689` as the first controlled send evidence.

## 0.21.0 - 2026-06-23

- Added S1-11 historical B1/arXiv preview evidence generation via `adp historical-b1-previews`.
- Added deterministic 30-sample B1 report/email preview generation with unique source IDs, content hashes, email IDs, claim evidence audits, and content ledger rows.
- Kept live network fetch, production scheduler, real SMTP send, GitHub Release upload, video generation, and `ARXIV_PRODUCTION_ACCEPTED` disabled.

## 0.20.0 - 2026-06-23

- Added S1-10 post-migration bootstrap verification for the target machine or GitHub-hosted cloud runner.
- Added `adp post-migration-bootstrap` to verify Python, Git checkout, SSL context, SQLite/FTS5, runtime smoke, GitHub Actions runner env, workflow runner contract, and secret-name-only readiness.
- Added a GitHub-hosted Stage 1 bootstrap workflow that runs on `ubuntu-latest`, uploads JSON evidence, and keeps production schedule, SMTP send, Release upload, video, and large replay disabled.

## 0.19.0 - 2026-06-22

- Added S1-09 low-resource migration package export and verification via `adp migration export|verify`.
- Added package manifest hash verification, new-machine bootstrap checklist, secret-name checklist, restore drill, and low-resource smoke artifact generation.
- Kept production scheduling, real SMTP, Release upload, video generation, 30-day replay, and Stage 2 promotion disabled.

## 0.18.0 - 2026-06-22

- Added S1-08 local runtime recovery controls for `adp tick`, `adp watchdog`, `adp backup`, `adp restore`, `adp runtime-audit`, and `adp scheduler install|uninstall`.
- Added heartbeat/checkpoint state, stale-heartbeat watchdog checks, SHA256 SQLite backup/restore manifests, and scheduler dry-run template generation.
- Kept production scheduling, real SMTP, Release upload, video generation, and long-running local background execution disabled.

## 0.17.0 - 2026-06-22

- Added S1-07 B1/arXiv Chinese teaching report and email preview artifact generation.
- Added `adp build-b1-report-email` for text-first Markdown, HTML, plain-text email, HTML email, and audit JSON output.
- Added fail-closed validation for 100% critical-claim evidence coverage, Chinese-first email content, no real SMTP, no Release upload, and no video requirement.

## 0.16.0 - 2026-06-22

- Promoted the V5 two-stage text-delivery baseline for Stage 1 B1/arXiv and marked conflicting V4/media requirements as inactive for the current acceptance path.
- Added the V5 Stage 1 scoring, 10,000 queue, 365-day window, reason-code, and text-first content-ledger contract.
- Added `adp stage1-queue` JSON output plus deterministic tests for 10,001st-item eviction, 365-day boundary handling, soft quota borrowing, source-share cap enforcement, lifecycle reason codes, stable tie ordering, and canonical `CONTENT_LEDGER.csv` columns.
- Updated generated owner ledger columns to use the Stage 1 text content-ledger contract while keeping production acceptance, scheduler, SMTP, Release upload, video generation, and broad source expansion disabled.

## 0.15.0 - 2026-06-22

- Added the Review8 Stage 1 source registry and arXiv connector contract for `SRC-ARXIV` / `arxiv.atom.v1`.
- Added `adp source-registry validate` JSON output, source registry schema, offline fixture validation, and fail-closed connector contract tests.
- Lowered the Stage 1 Window A online arXiv metadata canary cap from 25 to 10 without enabling PDFs, bulk harvest, SMTP, Release upload, scheduler, or production acceptance.

## 0.14.1 - 2026-06-22

- Rebuilt the daily email as a responsive HTML plus concise Chinese plain-text decision brief based on the V2 mockup: exact `YYYYMMDD -- Project Name -- arXiv Group -- Theme` subject, read/skim/skip, evidence level, reading time, first-principles chain, decision mapping, key questions, evidence gaps, minimal experiment, optional `.mp4` video link, and feedback actions.
- Removed frontend numeric `x/5` score labels from the subject, plain-text body, and HTML body; ranking/ROI scores remain backend-only evidence.
- Added a human-frontstage lesson payload so backend Claim Ledger and ROI details remain auditable while user-visible email hides Claim Ledger IDs, visible ROI scores, delivery policy text, Release landing-page clutter, and irrelevant q-fin candidate pollution.
- Kept production schedule disabled; this change prepares the next PR CI and controlled manual Gmail SMTP plus GitHub Release rerun only.

## 0.14.0 - 2026-06-22

- Added the Review8 Stage 1 local SQLite/WAL/FTS5 document and event storage model.
- Added `adp storage migrate`, `adp storage inspect`, and `adp storage rollback` JSON CLI commands.
- Added deterministic migration, SourceItem persistence, full-text search, inspection, and rollback tests.
- Kept source fetching, PDF retention, SMTP, Release upload, scheduler enablement, and production acceptance unchanged.

## 0.13.1 - 2026-06-22

- Corrected the Phase 12 human front-stage after manual run `27934320671`: the email text is now the reading entry point, Release is backend evidence/download storage, and video is an optional file link.
- Removed backend ROI score exposure from the MP4 transcript.
- Kept production schedule disabled; this change prepares the next controlled manual Release plus Gmail SMTP rerun only.

## 0.13.0 - 2026-06-22

- Added `config/owner_controls.yaml` as the single owner-editable control file for Stage 1 Window A.
- Added `adp owner validate`, `adp owner preview-impact --days 30`, and `adp owner render-docs --write` to validate controls, preview impact, and generate four owner-readable files.
- Added generated `docs/owner/OWNER_CONSOLE.md`, `SOURCE_CATALOG.md`, `MODEL_AND_QUEUE.md`, and `CONTENT_LEDGER.csv` views from machine facts only.
- Kept production schedule, SMTP, Release upload, source ingestion expansion, and scoring runtime behavior unchanged.

## 0.12.5 - 2026-06-22

- Refined the daily email front-end format for human scanning, actionability, and information density.
- Changed the daily email subject to `YYYYMMDD -- arXiv <Project Group> -- <arXiv Group> -- <Theme>`.
- Removed front-end `project`, `date`, `recipient`, ROI score, and delivery policy lines from the daily email body while preserving ROI evidence in backend artifacts.
- Kept Release/video links, Chinese lesson text, concise evidence, candidate queue summary, and no video email attachment policy.
- Kept production schedule disabled; this change only prepares the next controlled manual email test.

## 0.12.4 - 2026-06-22

- Fixed GitHub Release delivery to deduplicate repeated identical asset paths before invoking `gh release create`.
- Added fail-closed blocking for distinct Release assets that would publish with the same filename.
- Recorded second manual delivery run `27927785092`, where workflow-level dedupe passed but the lower release delivery boundary still blocked before SMTP.
- Added bounded transient retry handling for live all-arXiv cloud dry-runs after PR CI run `27928505758` hit arXiv 429 limits while preserving the 20/20 archive pass requirement.
- Bound successful GitHub Actions manual delivery run `27932072771` as controlled Release/Gmail SMTP evidence while preserving the no-production-acceptance boundary.
- Locked the Review8 two-stage V4 pursuing-goal baseline under `docs/pursuing_goal/BASELINE_LOCK.md` and started Stage 1 Window A traceability without changing runtime behavior.
- Kept production schedule disabled and preserved no-secret/no-attachment Release-link delivery policy.

## 0.12.3 - 2026-06-22

- Fixed the manual GitHub Release plus Gmail SMTP test workflow to deduplicate Release assets by filename before invoking scheduled delivery.
- Preserved fail-closed behavior: if Release creation fails, the workflow still blocks SMTP instead of sending an email without a video/Release link.
- Kept scheduled production disabled and unchanged.

## 0.12.2 - 2026-06-22

- Added a default-branch-only manual GitHub Actions workflow for one controlled GitHub Release plus Gmail SMTP delivery test.
- The manual workflow scans all arXiv primary archive buckets, selects one ROI-ranked daily paper, renders a lightweight MP4, creates a Release with the MP4 and JSON artifacts, then sends one email to `linzezhang35@gmail.com` containing Chinese lesson text, Release link, video link, and candidate queue summary.
- Kept scheduled production disabled: the workflow has no `schedule:` trigger, does not read repository production enablement variables, and requires the exact `SEND_TEST_EMAIL_TO_LINZEZHANG35_GMAIL_COM` confirmation string before side effects.

## 0.12.1 - 2026-06-22

- Added Phase 12 cloud production-enablement workflow for GitHub-hosted live all-arXiv dry-run evidence across all 20 primary archive buckets.
- Added `adp run-live-all-arxiv-dry-run` and `adp render-lightweight-mp4` evidence paths that produce a live-selected sample daily input and a real lightweight `.mp4` artifact.
- Migrated arXiv Daily Push scheduled, trial-start, provisioning-audit, and production-trial workflows away from self-hosted runner targeting to GitHub-hosted `ubuntu-latest`.
- Tightened email video-link gating so JSON video manifests no longer satisfy production-ready email evidence; a GitHub Release `.mp4` asset link is required.
- Kept production schedule, SMTP sending, and Release uploading disabled by default pending cloud dry-run, Release, and manual Gmail SMTP evidence.

## 0.12.0 - 2026-06-22

- Added Phase 12 all-arXiv primary archive scanning via `adp plan-all-arxiv-scan` and `adp build-all-arxiv-daily-input`.
- Added persistent candidate queue behavior with ROI/learning-value ranking, one daily lead selection, high-value queue carry-forward, and queue fallback when no new high-value paper is available.
- Updated scheduled and trial-start workflows to remove the old `cat:cs.AI` production default and build Phase 12 all-arXiv daily input artifacts instead.
- Added Release-hosted video artifact link requirements before real SMTP can count as production-ready scheduled evidence.
- Updated runbook and config examples for all-arXiv scope, candidate queue state, GitHub Release artifact links, and fail-closed production enablement.

## 0.11.27 - 2026-06-22

- Added `adp run-two-day-simulation` for the updated Phase 11 two-day simulation acceptance path.
- The simulation runs two unique scheduled daily paths with mocked SMTP and Release boundaries, appends both days to trial evidence, and verifies no duplicate dates, source IDs, or publication IDs.
- Kept the simulation fail-closed and explicit: it does not fetch network data, send real SMTP mail, upload a real Release, read Codex auth, log secret values, retain media/cache artifacts, or claim production acceptance.

## 0.11.26 - 2026-06-22

- Added `adp review-provisioning-audit` to register a downloaded `adp-production-provisioning-audit` artifact before trial-start dispatch.
- The review gate requires a valid passing production refs report plus durable workflow run and artifact refs.
- Kept the review fail-closed and no-side-effect: it does not read secret values, Codex auth, dispatch workflows, send SMTP mail, upload Releases, or claim production acceptance.

## 0.11.25 - 2026-06-22

- Added a manual `arxiv-daily-push-provisioning-audit.yml` workflow that runs on `ubuntu-latest` before trial start and uploads `adp-production-provisioning-audit`.
- Reused `discover-production-refs` to validate runner label, required SMTP secret names, Release target variable, and workflow variables without occupying the private runner.
- Kept the audit fail-closed and no-secret: it does not read secret values, Codex auth, dispatch trial start, send SMTP, create Releases, or claim production acceptance.

## 0.11.24 - 2026-06-22

- Updated the default-branch trial-start workflow to run no-secret production refs discovery before any live source, SMTP, Release, or start-gate work.
- Added an in-workflow `plan-production-launch` readiness precheck that consumes the production refs artifact and fails closed before side effects.
- Added workflow contract checks and artifacts for `adp-trial-start-production-refs` and `adp-trial-start-launch-readiness` while keeping Phase 11 production acceptance blocked until real trial evidence exists.

## 0.11.23 - 2026-06-22

- Added `adp discover-production-refs` to use `gh api` on a provisioned runner and build a no-secret production refs report from GitHub Actions metadata.
- Added metadata discovery coverage for runner label, required SMTP secret names, Release target variable, and workflow variable names without printing `gh` stdout/stderr or secret values.
- Kept local execution fail-closed when `gh` is unavailable and kept production launch/30-day acceptance blocked until real external refs and trial evidence exist.

## 0.11.22 - 2026-06-22

- Added `adp print-production-refs-template` to emit a no-secret owner-fillable JSON template before `plan-production-refs`.
- Added a repository example production refs input template that defaults to blocked readiness and contains only secret/variable names plus empty refs.
- Kept production launch blocked until owner-provisioned durable refs, explicit confirmation, default-branch trial-start evidence, and 30-day production evidence exist.

## 0.11.21 - 2026-06-22

- Added machine-checked GitHub Actions `contents: write` permission requirements for controlled Release probes.
- Updated trial-start and scheduled production workflow contracts so real Release evidence can be created only after explicit enablement.
- Kept SMTP/Release side effects disabled by default and production acceptance blocked until external refs and 30-day evidence exist.

## 0.11.20 - 2026-06-22

- Added `adp plan-production-refs` and `adp-production-refs-v1` to collect external runner, SMTP secret-name, Release target, and workflow variable readiness refs without reading or logging secret values.
- Added fail-closed checks for required SMTP secret names, required workflow variable names, durable readiness refs, explicit ready flags, and suspicious secret-value input fields.
- Updated `adp plan-production-launch` so a passing production refs report can fill the external runner/SMTP/Release/workflow refs while keeping launch and 30-day production acceptance blocked until real external evidence exists.

## 0.11.19 - 2026-06-22

- Added `adp plan-production-launch` and `adp-production-launch-readiness-v1` to fail closed before default-branch trial start workflow dispatch.
- Added launch readiness validation for PR merged/non-draft state, expected head SHA binding, trial start workflow contract, private runner ref, SMTP secrets ref, Release target ref, workflow variable ref, and explicit launch confirmation.
- Added launch readiness schema and tests covering pass, current draft/unmerged PR blocking, head SHA mismatch blocking, and CLI JSON output.

## 0.11.18 - 2026-06-22

- Added `.github/workflows/arxiv-daily-push-trial-start.yml` to collect default-branch trial start evidence on the private runner.
- Added `adp plan-trial-start-workflow` and `adp-trial-start-workflow-v1` to validate manual dispatch, preflight-first ordering, live source and delivery probe ordering, artifact uploads, durable refs, and explicit SMTP/Release variable gates.
- Added workflow plan schema and tests covering manual-only behavior, required artifacts, side-effect gating, secret-name-only mapping, and CLI JSON output.

## 0.11.17 - 2026-06-22

- Added `adp plan-trial-start` and `adp-trial-start-v1` to build a fail-closed readiness report before starting the real 30-day production trial.
- Added start gating across passing production preflight, bootstrap workflow, scheduler contract, live arXiv source batch, real sent SMTP probe, real created Release probe, explicit confirmation, and durable GitHub/runner/state/start refs.
- Added trial start schema and tests covering pass, missing confirmation, missing durable refs, SMTP dry-run blocking, blocked preflight, and CLI JSON output.

## 0.11.16 - 2026-06-22

- Added `adp build-trial-resource-evidence` and `adp-trial-resource-v1` to verify 30-day resource telemetry from daily trial resource refs and passing production preflight reports.
- Tightened production preflight resource refs so passing preflight reports use timestamped `production-preflight://` refs instead of a static `current` ref.
- Added resource schema and tests covering pass, missing matching preflight blocking, blocked preflight blocking, missing durable resource ref blocking, and CLI JSON output.

## 0.11.15 - 2026-06-22

- Added `adp build-trial-recovery-evidence` and `adp-trial-recovery-v1` to build fail-closed recovery drill evidence from a failed/degraded scheduled daily-run and a recovered production-ready rerun.
- Added recovery validation requiring real sent failure/recovery notifications, production-ready recovery refs, matching daily dates when available, and durable failure/recovery evidence refs.
- Added recovery schema and tests covering pass, dry-run failure notification blocking, missing recovery ref blocking, non-production-ready recovery blocking, and CLI JSON output.

## 0.11.14 - 2026-06-22

- Added `adp build-trial-replay-evidence` and `adp-trial-replay-v1` to build fail-closed weekly/monthly replay evidence from the accumulated trial ledger.
- Added replay validation requiring production-ready daily refs, no duplicate dates/source/publication IDs, 7 consecutive days for weekly replay, 30 consecutive days for monthly replay, and a durable replay evidence ref.
- Added replay schema and tests covering weekly/monthly pass, monthly coverage blocking, missing durable ref blocking, duplicate-date blocking, and CLI JSON output.

## 0.11.13 - 2026-06-22

- Added `adp annotate-trial-ops-evidence` for fail-closed annotation of explicit weekly/monthly replay, recovery drill, scheduler, Release, SMTP, and resource evidence refs.
- Added `adp export-trial-ops-state` so a passing ops annotation can carry forward the updated `trial_evidence` JSON without hand-editing state.
- Added tests that block verified operational flags without refs and prove weekly/monthly plus recovery evidence can unlock the final trial validator when all daily evidence already exists.

## 0.11.12 - 2026-06-22

- Added `adp export-trial-ledger-state` to export the accumulated `trial_evidence` JSON from a passing ledger update report.
- Updated the scheduled workflow to restore the prior `adp-trial-evidence-ledger` artifact with `gh run download` and upload the new state after successful daily ledger append.
- Added tests and scheduler validation for cross-run trial ledger state persistence while keeping 30-day production acceptance blocked until the validator passes.

## 0.11.11 - 2026-06-21

- Added `adp update-trial-ledger` and `adp-trial-ledger-v1` to append production-ready scheduled daily-run evidence into the Phase 11 trial evidence package.
- Updated the scheduled workflow to upload an `adp-trial-ledger-update` artifact after daily-run evidence while preserving fail-closed behavior for duplicate days, dry-run side effects, and missing production refs.
- Added trial ledger schema and tests covering blocked non-production evidence, duplicate daily evidence, global evidence flag upgrades, CLI JSON output, and scheduled workflow wiring.

## 0.11.10 - 2026-06-21

- Added `adp build-daily-input` and `adp-daily-input-builder-v1` to convert live arXiv source batches into ranked daily pipeline inputs using only Atom summary claims.
- Updated scheduled daily-run workflow wiring to build and upload `adp-scheduled-source-batch` and `adp-scheduled-daily-input` artifacts when no override input path is configured.
- Added daily input schema and tests covering summary-derived P0 claims, missing-summary blocking, recent-selection blocking, CLI JSON output, and scheduled execution compatibility.

## 0.11.9 - 2026-06-21

- Added `adp run-scheduled-production` and `adp-scheduled-execution-v1` as the controlled execution driver for scheduled health-check, daily-run, and watchdog modes.
- Updated the scheduled GitHub workflow to upload `adp-scheduled-execution` evidence after preflight while still failing closed when preflight, daily input, SMTP, or Release evidence is missing.
- Added scheduled execution schema and tests covering dry-run notification evidence, scheduled-run gating, degraded dry-run side effects, and mocked production-ready SMTP/Release evidence.

## 0.11.8 - 2026-06-21

- Added `.github/workflows/arxiv-daily-push-scheduled.yml` with `Australia/Sydney` 04:45 health-check, 05:00 daily-run, and 05:10 watchdog schedule slots.
- Added `adp plan-production-scheduler` and `adp-production-scheduler-v1` to validate the scheduled workflow gate without enabling production side effects.
- Added scheduler schema and tests covering timezone schedules, production variable gates, preflight-first ordering, and no SMTP/Release side effects.

## 0.11.7 - 2026-06-21

- Added `adp publish-release` for dry-run GitHub Release evidence and explicit Release creation.
- Added `adp-release-delivery-v1` with target gating, safe asset checks, no clobber upload, and no notes/stdout/stderr logging.
- Added Release delivery schema and tests covering dry-run, missing-target blocking, forbidden secret-like assets, mocked `gh release create`, and CLI JSON output.

## 0.11.6 - 2026-06-21

- Added `adp send-notification` for dry-run notification evidence and explicit SMTP delivery.
- Added `adp-smtp-delivery-v1` with fail-closed environment-key checks, TLS-required delivery, body hashing, and no secret/body logging.
- Added SMTP delivery schema and tests covering dry-run, missing-env blocking, and mocked real send.

## 0.11.5 - 2026-06-21

- Added `adp fetch-arxiv-latest` for small-window live arXiv Atom source ingestion.
- Added incremental duplicate filtering by prior `source_id` and a SourceBatch schema.
- Added fail-closed network/API/Atom parsing behavior with tests and current local SSL-blocker evidence.

## 0.11.4 - 2026-06-21

- Added a manual GitHub Actions production trial bootstrap workflow that runs production preflight before any trial work.
- Added `adp plan-trial-bootstrap` to validate the workflow/runbook contract without enabling cron, Release upload, or SMTP sending.
- Added a production trial runbook and trial bootstrap schema/tests.

## 0.11.3 - 2026-06-21

- Added `adp preflight-production` as a fail-closed gate before any scheduled production run.
- Preflight now checks production commands, required secret environment key presence without logging values, disk, memory, Git artifact hygiene, and local cache/staging directories.
- Added production preflight schema and tests covering blocked and passing reports.

## 0.11.2 - 2026-06-21

- Added a Phase 11 trial evidence validator for 30-day production evidence packages.
- Added `adp evaluate-trial` for validating daily run uniqueness, traceability, scheduler, Release, SMTP, resource, weekly/monthly replay, and recovery evidence.
- Hardened production acceptance so manual operational flags cannot pass unless they come from a validated trial evidence report.

## 0.11.1 - 2026-06-21

- Hardened Phase 11 production acceptance: every production pass requirement now needs both a true flag and a non-empty evidence reference.
- Added regression coverage that blocks boolean-only operational evidence from marking production acceptance as passed.

## 0.11.0 - 2026-06-21

- Added Phase 11 acceptance and handoff readiness package generation.
- Added `adp build-acceptance` for converting Phase 10 handoff JSON into a truthful acceptance package.
- Acceptance output blocks production acceptance unless explicit 30-day, scheduler, Release, SMTP, and resource evidence is provided.
- Added acceptance tests covering default blocked status, unsupported claim prevention, invalid handoff rejection, future evidence pass, and CLI output.

## 0.10.0 - 2026-06-21

- Added Phase 10 runner/release/email dry-run handoff.
- Added `adp build-handoff` for converting a completed dry-run pipeline payload into a handoff preview.
- Added fail-closed validation that keeps scheduler, GitHub Actions runner, Release upload, unattended execution, and real SMTP sending disabled.
- Added handoff tests covering completed RunRecord requirements, disabled external side effects, validation errors, and CLI output.

## 0.9.0 - 2026-06-21

- Added Phase 9 local daily dry-run pipeline orchestration.
- Added `adp run-daily-dry-run` for local source/claim JSON pipeline execution.
- Added RunRecord state transitions through completed, publication gate, Lesson, Narration, Storyboard, and email preview output.
- Added pipeline fixture and tests covering successful completion, evidence blocking, email preview, and CLI output.

## 0.8.0 - 2026-06-21

- Added Phase 8 storyboard/video dry-run generation from narration JSON.
- Added `adp generate-storyboard` for local storyboard rendering.
- Added video media gate with rendering, media writes, and asset downloads blocked in Phase 8.
- Added video fixture and tests covering dry-run storyboard generation, real render blocking, media path rejection, claim subset validation, and CLI output.

## 0.7.0 - 2026-06-21

- Added Phase 7 dry-run narration/TTS plan generation from Lesson JSON.
- Added `adp generate-narration` for local narration plan rendering.
- Added TTS resource gate with real synthesis, audio writes, and model downloads blocked in Phase 7.
- Added narration schema, fixture, and tests covering dry-run boundaries, real TTS blocking, audio path rejection, CLI output, and runtime parameters.

## 0.6.0 - 2026-06-21

- Added Phase 6 deterministic Chinese Lesson JSON generation from supported Claim Ledger evidence.
- Added `adp generate-lesson` for local lesson rendering from source/claim JSON fixtures.
- Added lesson validation that blocks unsupported or unknown claim references and requires visible claim markers in section bodies.
- Added lesson fixture and tests covering supported-claim linkage, unverified claim exclusion, blocked ledger handling, validation failures, and CLI output.

## 0.5.0 - 2026-06-21

- Added Phase 5 Claim Ledger construction and publication hard-block gate.
- Added `adp gate-publication` for local source/claim JSON gate checks.
- Added fail-closed checks for missing P0 locators, unsupported P0 claims, metadata conflicts, and unsupported arXiv peer-review claims.
- Added Claim Ledger fixture and evidence gate tests.

## 0.4.0 - 2026-06-21

- Added Phase 4 deterministic 100-point ranking and queue audit.
- Added fail-closed gates for missing P0 evidence, unsupported P0 evidence, metadata conflicts, and recent duplicate selections.
- Added `adp rank-candidates` for local candidate ranking from JSON fixtures.
- Added ranking golden tests and a small queue fixture.

## 0.3.0 - 2026-06-21

- Added Phase 3 arXiv Atom source adapter.
- Added offline Atom fixture parsing into generic `SourceItem` records.
- Added arXiv query URL rendering without network fetch.
- Added source adapter tests using local fixtures only.

## 0.2.0 - 2026-06-21

- Added Phase 2 generic contracts for `SourceItem`, `EvidenceClaim`, `Lesson`, `Storyboard`, `Publication`, and `RunRecord`.
- Added dependency-free runtime validators and a deterministic `RunRecord` state machine.
- Added `adp validate-record` for local `RunRecord` validation.
- Kept Phase 2 offline-only: no network ingest, ranking, TTS, video, runner automation, or real SMTP sending.

## 0.1.0 - 2026-06-21

- Created Phase 1 repository foundation for `arXiv Daily Push`.
- Added CLI skeleton with `version`, `doctor`, and `render-email`.
- Added dry-run notification contract for `linzezhang35@gmail.com`.
- Added local resource and storage pressure guardrails.
- Added CodexProject governance records for Phase 1.

- Added S2PJT03 local action, capability asset, and expected/actual ROI ledger evidence without production side effects.

- Added S2PJT04 local weekly report and attention reallocation evidence without production side effects.

- Added S2PHT05 local semantic content quality gate evidence without mail production or other production side effects.

- Added S2PIT03 local source/model/parameter/queue view evidence without production side effects.

- Added S2PIT04 local content/mail/review/action/asset/ROI ledger reconciliation evidence without production side effects.
- Added S2PKT01 local M1-M4 EMAIL_LEARNING_V1 mail contract evidence without production side effects.
- Added S2PKT02 local M1 science/theory frontier mail evidence without production side effects.
- Added S2PKT03 local M2 engineering/product/industry frontier mail evidence without production side effects.
- Added S2PKT04 local M3 policy/capital/geopolitical frontier mail evidence without production side effects.
- Added S2PKT05 local M4 cross-board 3+1 mail orchestration evidence without production side effects.
- Added S2PMT01 local security and evidence-boundary gates without production side effects.
- Added S2PMT02 local atomic storage and recovery hardening evidence without production side effects.

- Added S2PMT03 local lease fencing, state concurrency, transactional outbox, SMTP crash-window, and M4 watermark evidence without production side effects.
