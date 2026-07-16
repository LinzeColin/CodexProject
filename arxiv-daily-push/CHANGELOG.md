# Changelog

## 2026-07-16 Australia/Sydney - ADP V0.1 task ADP-S0-P01-T002 (archive old directions + conflict ledger)

- Second task of the ADP V0.1 FINAL EXECUTION program, one-task-per-run per the anti-black-hole protocol. Goal: keep every historical detail queryable but stop old UI, A3+, multitenancy, and TAM from re-entering the current scope. Doc-only, release_mode NOT_DEPLOYED, 0 recurring cloud cost; no worker/D1/R2/schema/CSP touched and the six themes + advanced motion are untouched. Two deliverables under arxiv-daily-push/docs/pursuing_goal/v0_1/: CONFLICT_LEDGER.csv (14 machine-readable rulings CL-001..CL-014, each with source / old_conclusion / new_ruling / ruling_status / reason / authority_ref; parses with csv.DictReader and every row has all four required fields) and ARCHIVED_NOT_CANONICAL.md (per-direction adjudication table + where the historical inputs physically live with sha256 fingerprints + a boundary statement). The 14 rulings supersede or reclassify: auth/multitenancy/enterprise-backend, TAM/pricing, replacement UI, multi-level A0-A4/B/C/D sources -> A0/A1/A2 only, 171 sources = seed cohorts, D1-stores-all-raw -> D1 hot metadata + R2 raw, 20TB/10M/30M = capacity envelope, Workflows mandatory -> candidate vs Cron+Queues, vector-DB-first -> deferred, competitor-parity -> equal-or-better user benefit, final-package = final execution baseline (not done until S8), out-of-scope security side-quests, motion-vs-performance = not-in-conflict, A3+ sources out of scope. Old material is downgraded, not deleted; the historical zips are NOT bulk-committed (low-token/no-redundant-binary contract) and stay referenced by sha256. Ends IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION (implementer does not self-sign PASS). Private Cloudflare facts FACT-011..015 remain UNVERIFIED and are the S0-P02 job.

## 2026-07-16 Australia/Sydney - Begin ADP V0.1 FINAL EXECUTION program: task ADP-S0-P01-T001 (freeze scope + owner directives)

- The Owner set a new /goal and supplied ADP_V0.1_FINAL_EXECUTION_TASK_PACKAGE_2026-07-15 (90 atomic tasks across 9 stages S0-S8, with an anti-black-hole execution protocol: one Stage active, one task per run, no big-bang, independent verification). The live MVP, all six themes, and the advanced motion just shipped are an explicit protected baseline. Executed exactly the mandated first task, ADP-S0-P01-T001 (freeze the Owner's latest directives and authority order), release_mode NOT_DEPLOYED, 0 recurring cloud cost. New canonical baseline under arxiv-daily-push/docs/pursuing_goal/v0_1/: CURRENT_SCOPE.md (in/out scope, simplicity invariants, protected baseline, guardrails), OWNER_DIRECTIVES.yaml (machine-readable DIR-001..006, hard constraints, owner gates, out-of-scope, assumptions; YAML validated), and PRECEDENCE.md (six-level authority order and ten fixed conflict rulings), plus an evidence bundle answering the task's six start-questions. Nothing deployed; no worker, D1, R2, schema, or CSP touched; the site is unchanged. Ends IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION (implementer does not self-sign PASS). Private Cloudflare facts stay UNVERIFIED and are the S0-P02 task.

## 2026-07-15 Australia/Sydney - Self-hosted the hero videos (removed the external CloudFront dependency)

- The hero videos were still loading from an external CloudFront that is decaying (one clip already dead). The Owner authorized fixing this but does not want to touch the dashboard, and Cloudflare R2 (the v1.1 recommendation) needs a one-time dashboard enable that is a billing/terms action, so it was not taken on the Owner's behalf. Instead the three still-live clips were self-hosted on the Worker via Cloudflare static assets: downloaded and compressed with ffmpeg (obtained through the pip package imageio-ffmpeg, no system install) to 1280x720 H.264 no-audio loops (62MB down to 7MB total, also far lighter on mobile), stored under deploy/cloudflare/assets/media, served same-origin at /media/*.mp4 via a wrangler assets binding. HERO_VIDEO now points at /media/*.mp4 and the CSP media-src is back to 'self' with CloudFront removed entirely, so the site has zero external media dependency and the videos are durable with the deployment. The mp4 files were force-added past the repo's media/ gitignore because durability requires them versioned. Live-verified: all three /media clips serve 200 video/mp4 same-origin and the hero video plays. cosmos keeps its dashboard (its own source clip was already dead).

## 2026-07-15 Australia/Sydney - Restored the today-page hero first-screen (the original theme motion)

- The Owner supplied the actual v1.1 design package and pointed out the ORIGINAL theme motion was still missing after many changes. Reading the spec made the miss obvious: the signature motion was never the ambient background layer, it is the today-page HERO first-screen, which the cloud port had dropped entirely. Restored it in deploy/cloudflare/worker_cloud.js per the v1.1 first-screen contract. minimal, techno and forest now open with the original full-screen hero VIDEO (the three live CloudFront reference clips) showing an eyebrow, a giant serif title (today's pick, per-character blur-in for techno), a subtitle and a glass CTA over a per-theme gradient mask. cosmos gets the knowledge-vitals DASHBOARD: an SVG ring gauge that counts up to today's selection score out of 104, a STREAK / RETENTION / REVIEW-DEBT grid, and a 7-pick sparkline, all over the galaxy (its own NOVA video URL is dead). warm and fresh stay clean by design. Video handling follows the v1.1 red-lines (src assigned by JS, explicit muted/loop booleans, play plus a canplay handler so it never freezes on a first frame); the CSP gains a media-src entry for the video host. Live-verified per theme in a fresh no-cache tab: the minimal, techno and forest videos actually play, and the cosmos gauge animated to 094. Note: the reference videos are external and one is already dead, so they should be moved to owner storage (R2) for durability.

## 2026-07-15 Australia/Sydney - Made theme motion boldly visible + fixed the cache hiding every deploy

- After the previous change the Owner still saw no motion on both computer and phone, even on a fresh URL. Two root causes, both fixed in deploy/cloudflare/worker_cloud.js. (1) Cache: DOM inspection proved the browser was serving a fully cached page (computed card background still 0.58 and band animation 90s -- the OLD css) despite cache-control: no-cache; these browsers store no-cache responses and skip revalidation, so the Owner had not actually received any recent deploy. Changed the HTML cache-control from no-cache to no-store, must-revalidate so browsers always refetch (confirmed live). This is the main reason updates were invisible. (2) Visibility: the ambient effects were technically rendering but far too faint (1px stars, off-screen nebulae) because the original design leaned on full-screen hero videos that were not ported. Amplified the self-contained CSS: cosmos now has on-screen nebula-glow backgrounds, a conic aurora sweep, brighter and denser twinkling stars, and a 6-second glowing meteor, with cosmos cards made translucent (0.40) so the galaxy shows through; techno clouds are larger and brighter; minimal gains a moving light shaft; forest slopes are taller with a slow sway. Verified in a fresh no-cache browser tab: the cosmos galaxy and techno clouds are now clearly visible.

## 2026-07-15 Australia/Sydney - Restored the six-theme ambient motion layers

- Owner: "the 6 themes just change one color now, the original motion/animation design is all gone -- don't fix A and lose B." Correct: the Stage 2 six-theme port into deploy/cloudflare/worker_cloud.js had copied only the colour tokens and layout and dropped every per-theme animated layer that the local design source src/adp/templates/base.html defines. Restored them faithfully as pure CSS/SVG (no external dependency, CSP-safe), driven by a THEME_FX map and a data-fx attribute (set in the no-flash head-init and applyTheme, validated and self-healing like the theme guard): cosmos regains the galaxy layer (a slowly drifting light band, three nebula glows, two twinkling star fields, and an 11-second shooting meteor); techno regains three drifting white fluid clouds; minimal regains the ocean top-light and deep radial vignette; forest regains the layered hill-slope SVG and the water band; plus a gentle card fade-in entrance and a prefers-reduced-motion guard that disables the motion. warm and fresh stay clean (no fx) exactly as the original design intends. The external CloudFront hero videos from base.html were intentionally not ported (CSP and dependency fragility; the CSS ambient layers carry the motion). Content stays above the layers via z-index (fx at z-index 0, pointer-events none). Live-verified per theme on adp.linzezhang.com at both desktop and phone width, with the ChatGPT deep-dive button and the theme self-heal intact.

## 2026-07-15 Australia/Sydney - Theme-selector self-heal hotfix

- Owner reported the webpage's 6 themes were gone and would not come back. Reproduced in-browser: the six-theme picker read the stored theme from localStorage and applied it without validating, so a stale/invalid stored value (from an earlier build) or an Object.prototype key such as 'constructor'/'__proto__'/'toString' set an invalid data-theme (no matching CSS -> page fell back to the default warm palette) and left the native <select> at selectedIndex -1 (blank switcher). To the Owner this looked exactly like all 6 themes had vanished and their chosen theme was not restored. Fix (deploy/cloudflare/worker_cloud.js): the no-flash head-init and the theme script now validate the stored value with Object.prototype.hasOwnProperty.call(THEMES, s) (an isTheme() helper) and fall back to 'warm' unless it is one of the six, and applyTheme rewrites the corrected value so a bad entry self-heals on first load. Live-verified on adp.linzezhang.com: stored 'aurora' and 'constructor' both self-heal to warm (switcher shows 暖纸学习), and picking 森林河流 persists across page navigation.

## 2026-07-15 Australia/Sydney - ChatGPT deep-dive button + local cleanup

- Owner: "delete useless local info; add a jump to ChatGPT so it can traverse the whole web, think and search deeply, give me some surprises, and explain the corresponding content in a detailed, professional, comprehensive, deep way." Feature (deploy/cloudflare/worker_cloud.js): every daily pick, item-detail page, and review card now shows a "让 ChatGPT 全网深度追问" button that opens ChatGPT (chatgpt.com/?hints=search&q=) with a prompt pre-filled from that item's title, authors, categories, original link, and abstract, instructing ChatGPT to do a live deep web search (cross-checked with citable sources), reason deeply about the problem/method/assumptions/innovation/limits, give a detailed and professional and comprehensive and deep explanation for someone who wants to truly learn it, surface some surprises (unexpected links, counter-intuitive conclusions, overlooked angles), and end with a "what to read/do next" list; the search page also gets a topic deep-dive button. The rendered href is escaped (encodeURIComponent leaves only the literal & to become &amp;), so there is no injection surface. Live-verified on adp.linzezhang.com across today/item/review/search with the decoded prompt correct. Local cleanup (no tracked-file change): the retired mirror/tunnel architecture no longer backs adp.linzezhang.com, so the dormant com.linze.adp.web (uvicorn 8787) and com.linze.adp.tunnel (cloudflared) LaunchAgents were unloaded and their installed plists, the cloudflared connector token, the 38MB local cloudflared binary, and dead logs removed; the reinstall templates stay under deploy/cloudflare/launchd/, and the site still serves 200 on every route afterward, confirming the local residue was unused.

## 2026-07-15 Australia/Sydney - Cloud-native rebuild Stage 3: cut adp.linzezhang.com over to the cloud system + commercial feature/polish pass

- The Owner confirmed they check adp.linzezhang.com itself and asked to keep enriching it toward commercial quality. Stage 3 cutover: the custom domain adp.linzezhang.com was detached from the old adp-mirror worker and bound to the cloud-native adp-cloud worker; every route (today/review/radar/system/history/search/board) verified 200 on the real domain, independent of the Mac. The old adp-mirror worker and the local tunnel/web LaunchAgents no longer back any hostname (left dormant for the Owner to delete). Commercial feature + polish pass (all in deploy/cloudflare/worker_cloud.js): a learning-stats dashboard (streak, due, mastered, learning, recall-hit-rate) with a "start review" CTA; a guided review session /review (most-due card → reveal lesson → 4-grade → auto-advance) with the full queue below; board browsing /board/:id with pagination; full-text-ish search /search?q= over the candidate library; a past-picks archive /history; item detail pages /item/:id; and "study any item" (POST /api/study/:id) so any item from any board or search can be added to the spaced-repetition queue — not just the daily pick. Polish: meta description + Open Graph, per-theme theme-color, an emoji favicon (data URI), security headers (CSP, X-Content-Type-Options, Referrer-Policy), no-store on APIs, themed 404 and error pages, robots.txt, and aria labels. Live-verified end to end including study→review flow on adp.linzezhang.com.

## 2026-07-15 Australia/Sydney - Cloud-native rebuild Stage 2: six-theme interface, working board-3 source, per-board rotation

- Stage 2 of the cloud rebuild, all in `deploy/cloudflare/worker_cloud.js`: (1) ported the six-theme design language from base.html into the cloud worker — warm/minimal/fresh/techno/cosmos/forest token groups plus three nav layouts (sidebar/topbar/dock via body[data-nav]) and a theme dropdown persisted in localStorage; live-verified switching (warm sidebar ↔ cosmos dock) renders correctly. (2) Board 3 (China policy) — Google News is blocked from datacenter IPs, so it was replaced with Chinese-media RSS that fetches fine from Cloudflare (people.com.cn politics/finance, chinanews scroll, sina China focus); live-verified 75 clean (non-garbled) policy/government items. (3) Feed rotation changed from day-of-year to per-board staleness (fetch the 4 least-recently-fetched feeds of each board every run) so every board — including board 3 — refreshes each run and stays within the free-tier subrequest budget. (4) Added charset-aware feed fetch (gb2312/gbk→gb18030 via TextDecoder) to prevent future mojibake, and orphan-source cleanup so removed sources (the old Google News rows) don't linger. Fixed a sidebar CSS selector bug (the nav element is `<nav class="nav-side">` but the CSS targeted `aside.nav-side`, so the sidebar leaked to the top). Per-board item counts after the run: board1 270, board2 121, board3 75, board4 140. Still a separate adp-cloud worker; adp.linzezhang.com untouched until Stage 3.

## 2026-07-15 Australia/Sydney - Cloud-native rebuild Stage 1: the whole system now runs on Cloudflare (Workers + D1 + Cron), no Mac

- Owner directives: arXiv should cover all of arXiv (not just cs/stat); the bioRxiv shadow becomes normal ingestion; the web should be the real system (not a mirror of the Mac) — the current local-first/mirror model is "wrong"; and all boards must enter the daily selection. The Owner chose the free rebuild path (Cloudflare Workers + D1 + Cron). Stage 1 lands a self-sufficient cloud system in `deploy/cloudflare/worker_cloud.js` + `wrangler_cloud.jsonc` + `schema_cloud.sql`: one Worker + one D1 running all five stages (fetch → select → lesson → recall → FSRS) with a daily cron; pages read/write D1 directly and recall grades update FSRS immediately (no write-back queue — the cloud is the source of truth). Ingestion covers all of arXiv across every field (OAI-PMH), bioRxiv as normal ingestion, and all board feeds; selection scores candidates across ALL boards (8 weighted features, abstain 59.6). bioRxiv was also promoted to normal ingestion in the live local system per the same directive. Live-verified on adp-cloud.linzezhang35.workers.dev: arXiv 220 (incl. econ/stat/cs), bioRxiv 30, 217+ candidates, selected an economics paper, lesson rendered, a recall grade scheduled the next review (2026-07-18, 3-day interval) in D1. Free-tier subrequest cap (~50/invocation) handled by batching all D1 writes and rotating board feeds. Known gap: board 3's Google News feeds are blocked from datacenter IPs (degrade honestly; fixed in Stage 2). Deployed as a separate adp-cloud worker so the live adp.linzezhang.com is untouched until the Stage 3 cutover.

## 2026-07-15 Australia/Sydney - Expand board data sources to 44 feeds; return home.linzezhang.com to the Owner's own homepage

- Owner directives: (1) the four boards were incomplete — expand the data sources; (2) home.linzezhang.com is the Owner's personal homepage — give it back. Source expansion (registry boards-v03-2): board 2 now carries 23 top-journal official RSS feeds (Nature + Nature Medicine/Biotech/Machine Intelligence/Communications/Neuroscience/Methods/ML-subject, Science + Advances + News, Cell + Neuron/Immunity/Systems, PNAS, Lancet, NEJM, JAMA, BMJ, PLOS Biology/Comp-Biol, eLife, IEEE Spectrum); board 3 has 5 Google-News ministry/topic streams (State Council/MIIT/NDRC, MOST/CAC, PBoC/CSRC, AI governance, NMPA) plus the preserved RSSHub route; board 4 has 11 (Fed press/monetary/speeches, SEC press/statements, FTC press/consumer-protection, NIST, White House presidential actions, plus two Google-News aggregates); board 1 gains arXiv cs.CL/cs.CV and medRxiv browse streams. Every feed_url was live-probed; the first real fetch pulled 43/44 sources (1050 items; the RSSHub public instance stays rate-limited and auto-disabled). Boards 2-4 remain radar browse streams outside the daily selection pool. Homepage: home.linzezhang.com was mistakenly occupied by this project's worker; its custom domain has been returned to the Owner's own `linze-home-hub` worker (untouched), the stray `home` worker deleted, and deploy/cloudflare/home/ removed from the repo.

## 2026-07-15 Australia/Sydney - Boards 2-5 go live with transparent data sources; homepage hub at home.linzezhang.com; tunnel direct path verified end to end

- Owner directives: (1) the remaining four boards go online with per-board data-source visibility; (2) home.linzezhang.com must work. Boards 2 (Nature/Science/Cell official RSS), 3 (Google News policy aggregation + a preserved RSSHub route that honestly reports the public instance's rate-limit degradation) and 4 (Federal Reserve / SEC official RSS) are now live as radar feed streams: `config/boards_v0_3.yaml` is the single source of truth (PARAM-ADP-1123), `adp.boards` fetches via feedparser into the new `board_items` table with per-source health accounting (3 consecutive failures auto-disable), and the radar page shows every board's sources (name / platform / website / subscription method / official-vs-aggregator / health / item counts / last fetch) plus latest items; board 5 auto-aggregates. Real fetch: 6/7 sources OK, 138 items cumulative in board_items (idempotent re-runs give new=0; report in data/boards_fetch_report.json); the RSSHub public-instance route hit repeated 403s and auto-disabled (kill switch now actually skips disabled sources). External links are restricted to http/https (no javascript:/data: injection on the radar page), future-dated items are dropped so they cannot pin to the top, source ids must be globally unique, and network I/O no longer runs inside the SQLite write transaction. Boundary kept honest: boards 2-4 do NOT enter the daily selection pool - pool integration and the diversity 10->17 change remain a separate proposal path, and bioRxiv promotion stays an Owner-only radar button (an unauthorized test-promotion found in the local DB was reverted back to shadow with a receipt). Separately, the Owner authorized the cloudflared login, the adp-origin DNS record was created, and the full-system direct path is now live end to end (183ms, remote guard 403 verified through the real tunnel); a minimal static homepage worker now serves home.linzezhang.com with links to ADP and the five boards.

## 2026-07-15 Australia/Sydney - Serve the full system at adp.linzezhang.com via Cloudflare Tunnel (mirror becomes automatic fallback)

- Owner directive (migrate everything to the cloud; phone must open the identical full system): the worker now reverse-proxies adp.linzezhang.com to a remotely-managed Cloudflare Tunnel (`adp`, connector + local web resident via LaunchAgents `com.linze.adp.web` / `com.linze.adp.tunnel`) reaching the local FastAPI six-theme system on 127.0.0.1:8787; when the Mac is asleep or the tunnel is down the worker automatically falls back to the D1 read-only mirror plus the /grade write-back queue (verified live). Because the entry has no login, the local webapp gains a `remote_guard` middleware: tunneled requests (identified by edge-set CF headers) may browse and submit active-recall grades only, while owner-decision writes (promote/pilot/state/undo/corrections/transfer) return 403 and stay local-only (protection test added). The tunnel connector token lives at `~/.cloudflared/adp-tunnel-token` (0600, not committed). The `adp-origin.linzezhang.com` DNS origin record awaits the Owner naming it in chat before the direct connection goes live end to end. Review-round fixes: grade endpoints and the mirror pull now reject fabricated lesson ids (no junk FSRS rows from the public entry), the frontend `post()` helper surfaces 403/503 bodies instead of rendering them as fake success receipts, the worker falls back on 502/503/504 as well (connector up but local web down) and answers full-system-only paths with an honest 503 note page, and cloudflared runs with `--no-autoupdate`.

## 2026-07-15 Australia/Sydney - Return home.linzezhang.com to the homepage; ADP moves to adp.linzezhang.com

- The task pack named home.linzezhang.com but the Owner clarified it is the homepage domain: the worker custom domain was detached (verified no longer resolving) and ADP now serves at adp.linzezhang.com (verified 200). The R6 README explains the mirror's role (local-first architecture) and documents the optional Cloudflare Tunnel upgrade that serves the full local system at the same URL.

## 2026-07-15 Australia/Sydney - Remove cloud mirror key login per Owner directive

- home.linzezhang.com now opens directly with no key (Owner directive); pages are publicly readable and the tradeoff plus the recommended Cloudflare Access private-mode upgrade are disclosed in deploy/cloudflare/README.md. The /grade endpoint keeps its one-entry-per-lesson-per-day cap and the local pull keeps Sydney-day dedup. Receipt recorded in config_changes; the key scheme remains recoverable from git history (a0a79743).

## 2026-07-15 Australia/Sydney - v1.1 six-theme frontend, R5 bioRxiv shadow source, R6 Cloudflare hybrid mirror

- Rebuilt the six-theme frontend per the v1.1 supplement pack: per-theme design languages with structural switches (three full-bleed video heroes with JS-property-only media control, a zero-radius cosmic vitals dashboard fed by real run data, sidebar/topbar/dock navigation, effects layers, reduced-motion support); verified per theme in a browser with zero console errors.
- R5: bioRxiv shadow source using the stage-2-accepted preprint adapter — zero-ingestion shadow evaluation through the same gates/features, a real 14-day shadow report (420 candidates, 0 fetch errors), a one-page enable proposal, and an Owner-only promotion click with receipted config change and 3-failure auto-disable.
- R6: Cloudflare hybrid mirror deployed live at home.linzezhang.com (Worker + D1 one-way mirror + recall write-back queue + daily cron); no-key/incognito access returns 401; a cloud grade round-trips into local FSRS with same-Sydney-day dedup; local loop unaffected when offline. R2 weekly snapshots degrade to local until the Owner enables R2; the owner-key uses a rotatable D1-hash scheme (secret-store write was denied by local policy — disclosed in deploy/cloudflare/README.md).
- Production boundary unchanged: no SMTP send, no scheduler install, no Release, no restore, DAILY_OPERATION disabled.

## 2026-07-15 Australia/Sydney - Readable HTML email preview beside MIME .eml

- `deliver_lesson` now writes a browser-openable `.html` preview next to the MIME `.eml` outbox artifact (the wire format reads as encoded text when opened directly, which the Owner perceived as garbled); existing previews backfilled and the Friday checklist documents the distinction. No behavior change to authorization, idempotency, or learning-state separation.

## 2026-07-14 Australia/Sydney - V0.3 rebuild R0: decision freeze and drift repair

- Imported the Owner-accepted V0.3 rebuild task pack as the active development contract at `docs/v03/` (PRD, architecture, delivery roadmap R0-R6, <110 KB total); V7.2 remains the frozen fail-closed machine lock for the legacy runtime.
- Registered the 38-parameter thresholds registry as the single parameter truth at `config/thresholds_v0_3.yaml` (Owner-decided weights: knowledge_gap 20, evidence_quality 5, diversity 17 with single-board cap 10; abstain threshold 55 is a placeholder until the R1-3 replay recalibration).
- Cleared legacy config residues: `production_auto_enable_after_acceptance` is now false and the five-message email split is demoted to a template capability (`split_mode: single_lesson_mirror`).
- Aligned three version pointers (CURRENT.yaml `rebuild_v03`, `docs/v03/STATUS.yaml`, HANDOFF/01 top section) and froze the giant governance documents in place with banners plus `archive/README.md` registry (reading surface 8.1 MB -> ~115 KB).
- No production side effects: DAILY_OPERATION, SMTP, scheduler, Release, and restore all remain disabled.

## 2026-07-10 21:50:12 Australia/Sydney - Persistent DAILY_OPERATION authorization prerequisite fail-closed hardening

- Fixed `build_daily_operation_persistent_enablement_authorization_state` so a valid live authorization artifact cannot override failed owner-decision or controlled-run prerequisites.
- Added `blocked_persistent_daily_operation_authorization_prerequisites_failed` and made all three authorization/enablement flags true only when every check passes.
- Normalized missing prerequisite JSON mappings to fail-closed empty mappings instead of raising `AttributeError`, and made the validator independently reject PASS plus failed checks or a missing/extra prerequisite check key.
- Added direct and temporary-root readiness/preflight regressions; temporary authorization fixtures stay outside the repository and failed prerequisites require exit 2.
- Updated `MOD-ADP-100` / `FORM-ADP-102` governance without changing model IDs, parameter profiles, runtime version `0.23.0`, provisional governance version `0.23.1`, CURRENT, V7, or any production state.
- The real `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json` remains absent; DAILY_OPERATION, SMTP, scheduler/LaunchAgents, Release, and restore remain disabled.

## 2026-07-01 20:39:16 Australia/Sydney - S2PMT07 daily operation secret and artifact preflight repair

- Added reviewed local-runner SMTP secret key-presence metadata support for production preflight without logging secret values.
- Scoped production git artifact hygiene to `arxiv-daily-push` for DAILY_OPERATION authorization preflight, so ADP is not blocked by unrelated cross-project OpenAIDatabase archives.
- Reran the DAILY_OPERATION authorization preflight: `status=blocked_owner_daily_operation_authorization_required`, `preflight_checks_passed=true`, `failed_checks=[]`, `production_preflight_status=pass`, `state_hash=a856ee3d1532d8973e11bb502f76f7320f9816904b52aab64975112c764de55e`.
- Kept operation disabled: `daily_operation_enabled=false`, `real_smtp_send_enabled=false`, `scheduler_install_enabled=false`, `release_packaging_enabled=false`, and `production_restore_enabled=false`.
- Evidence: `governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-SECRET-ARTIFACT-REPAIR-20260701.json` and `arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_DAILY_OPERATION_SECRET_ARTIFACT_REPAIR.md`.

## 2026-07-01 20:12:13 Australia/Sydney - S2PMT07 daily operation gh equivalent repair

- Added a reviewed `github_open_pr_count_zero_api_v1` equivalent for the production preflight `gh` CLI command gate.
- Wired DAILY_OPERATION authorization preflight to pass the reviewed GitHub open PR count equivalent when `open_pr_count=0`.
- Reran the DAILY_OPERATION authorization preflight: `status=blocked`, `state_hash=2b8bd06a85516fc1608996a335a579153cd6db1a64eb090691b776f8ea03f361`.
- Cleared the original missing `gh` CLI blocker; remaining blockers are missing SMTP secret env names and existing `OpenAIDatabase/session_history` archive git artifact hygiene violations.
- Kept operation disabled: `daily_operation_enabled=false`, `real_smtp_send_enabled=false`, `scheduler_install_enabled=false`, `release_packaging_enabled=false`, and `production_restore_enabled=false`.
- Evidence: `governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-GH-EQUIVALENT-REPAIR-20260701.json` and `arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_DAILY_OPERATION_GH_EQUIVALENT_REPAIR.md`.

## 2026-07-01 19:43:41 Australia/Sydney - S2PMT07 daily operation authorization preflight

- Added `S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT` builder/validator/CLI and wrote the blocked preflight manifest.
- Preserved Stage 2 accepted evidence while keeping operation disabled: `daily_operation_enabled=false`, `real_smtp_send_enabled=false`, `scheduler_install_enabled=false`, `release_packaging_enabled=false`, and `production_restore_enabled=false`.
- Recorded blockers: missing `gh` CLI, missing SMTP secret env names, and existing `OpenAIDatabase/session_history` archive git artifact hygiene violations.
- Updated CURRENT, dynamic governance status, owner-facing docs, three-base files, traceability matrix, delivery ledger, run manifest, and regression tests.
- Evidence: `governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT-20260701.json` and `arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_DAILY_OPERATION_AUTHORIZATION_PREFLIGHT.md`.

## 2026-07-01 19:04:10 Australia/Sydney - S2PMT07 integrated production acceptance evidence

- Wrote and validated `FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json` with `integrated_production_accepted=true`, `stage2_integrated_production_accepted=true`, and `production_acceptance_claimed=true`.
- Kept operation disabled: `daily_operation_enabled=false`, persistent `ADP_ALLOW_SMTP_SEND=false`, LaunchAgents disabled, and no SMTP/scheduler/Release/restore was enabled.
- Updated CURRENT, dynamic governance dashboard, root acceptance tools, owner-facing docs, three-base files, delivery ledger, run manifest, and regression tests for `INTEGRATED_PRODUCTION_ACCEPTED_NO_DAILY_OPERATION`.
- Evidence: `governance/run_manifests/ADP-S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-EVIDENCE-20260701.json` and `arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_INTEGRATED_PRODUCTION_ACCEPTANCE_EVIDENCE_WRITE.md`.

## 2026-07-01 14:49:29 Australia/Sydney - S2PMT07 post-final-bundle current-state sync

- Synchronized dynamic governance, owner-facing docs, dashboard routing, and regression tests after `FINAL_ACCEPTANCE_BUNDLE/manifest.json` validated `status=pass` with `missing_items=[]`.
- Current next task is `S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT`; it is not another S2PLT04/final-bundle artifact build.
- Production remains disabled: `integrated_production_accepted=false`, `daily_operation_enabled=false`, persistent `ADP_ALLOW_SMTP_SEND=false`, LaunchAgents disabled, and no SMTP/scheduler/Release/restore was enabled.
- Evidence: `governance/run_manifests/ADP-S2PMT07-POST-FINAL-BUNDLE-CURRENT-STATE-SYNC-20260701.json`, `arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_POST_FINAL_BUNDLE_CURRENT_STATE_SYNC.md`, and `FINAL_ACCEPTANCE_BUNDLE/manifest.json`.

## 2026-07-01 08:37:20 Australia/Sydney - S2PLT02 terminal scheduler blocker sync

- S2PLT02 current terminal inventory now confirms `observed_real_delivery_days=2/2` and `observed_real_email_count=8/8`; `SECOND_REAL_DELIVERY_DAY` and `EIGHT_REAL_EMAILS` are ready inputs.
- Current remaining blockers are `REAL_SCHEDULER_PROOF` and `S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT`; no SMTP send, scheduler, Release, restore, DAILY_OPERATION, or production acceptance was enabled in this sync.
- Evidence: `governance/run_manifests/ADP-S2PLT02-TERMINAL-SCHEDULER-BLOCKER-SYNC-20260701.json` and `arxiv-daily-push/docs/phase_records/PHASE_S2PLT02_TERMINAL_SCHEDULER_BLOCKER_SYNC.md`.

## 2026-07-01 07:43:35 Australia/Sydney - S2PLT02 controlled real second-day capture

- Recorded one owner-authorized foreground real SMTP catch-up for service date `2026-06-29` without launchd kickstart.
- M1/M2/M3/M4 sent once; S2PLT02 observed real evidence is now `2/2` real delivery days and `8/8` real emails.
- Remaining blockers are `REAL_SCHEDULER_PROOF` and `S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT`; no scheduler, Release, restore, DAILY_OPERATION, or production acceptance was enabled.
- Evidence: `governance/run_manifests/ADP-S2PLT02-CONTROLLED-REAL-SECOND-DAY-CAPTURE-20260630.json`, `governance/run_manifests/ADP-LOCAL-DAILY-M1-M4-CONTROLLED-REAL-CATCHUP-20260629.json`, `governance/run_manifests/ADP-S2PLT02-NORMALIZED-REAL-DELIVERY-MANIFEST-20260629.json`, `governance/run_manifests/ADP-S2PLT02-M4-WATERMARK-PROOF-RECORD-20260629.json`, and `arxiv-daily-push/docs/phase_records/PHASE_LOCAL_DAILY_M1_M4_CONTROLLED_REAL_CATCHUP_20260629.md`.


## 2026-07-01 05:42:34 Australia/Sydney - S2PLT02 terminal capture readonly command executability sync

- Updated `capture_wait_state_guard.allowed_readonly_commands` so every listed readonly command is parser-executable and returns blocked JSON.
- Added `--generated-at 2026-07-01T05:42:34+10:00` to `adp audit-s2plt02-terminal-proof-evidence-inventory` in the wait guard command list.
- Added CLI regression coverage that executes every allowed readonly command through the parser.
- Current live CLIs remain blocked with capture plan `aafb8d5147d8c7849a2489bfb4991376e978d646b5e149156cbba58ae513aff1`, wait guard `502a892c3a207233c0d9ea985685c5064e2aaa279ca9010a490b30190aefecfe`, inventory command `26207ef1ba63b2fe56d7904e141cf20dbd49268d98407a45a73dbf2fcfd0ed4c`, prerequisite plan `94fbe44f8211dff645ad5939696843122191b5b10ed939a1e04105c5e312c6b9`, and final readiness `6ae337c9dd434e0f43909cf2ddc13f3d0de3a1bb5beb919ac2323ee61b8ef48f`.
- No S2PLT02/S2PLT03 terminal proof artifact, S2PLT04 completion report, final-bundle manifest/handoff/signoff/final-command proof, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-07-01 05:17:15 Australia/Sydney - S2PLT02 terminal capture inventory summary sync

- Added `terminal_delivery_input_inventory_summary` and `terminal_delivery_artifact_validation_summary` to `plan-s2plt02-terminal-delivery-proof-capture`.
- Carried both summaries into `plan-final-bundle-prerequisites` and `validate-final-acceptance-bundle` under `s2plt02_terminal_delivery_capture_plan_summary`.
- Current live CLIs remain blocked with capture plan `cba2fb5be5cc1a7dc098b28fe0b0bd137fb43d18e4f077d755571313bcee03e4`, input summary `4df922bd5dc56541cbd76380adc6897fb779c929afa1c37e7f1d2eab236e8e5b`, artifact summary `3fbde96111dd78d3ffe4474e012fa5d86de76a24e6fa7640d0310c178003e1db`, prerequisite plan `bcb40505ad7244626589c24991dcf05fe775268ce44b5eab3b68444f38cded6e`, and final readiness `23c5a2f6beed34c440ee8f3de870ca71a2c2deb1d44cbd67623a3c7aa7fc510c`.
- No S2PLT02/S2PLT03 terminal proof artifact, S2PLT04 completion report, final-bundle manifest/handoff/signoff/final-command proof, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-07-01 04:57:53 Australia/Sydney - S2PMT07 final bundle zero-proof request consumption sync

- 任务：`S2PMT07-FINAL-BUNDLE-ZERO-PROOF-REQUEST-CONSUMPTION-SYNC`。
- 结果：`blocked_final_bundle_zero_proof_request_consumed_no_production`。
- 已验证输入：`FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json`，zero-proof artifact validation `state_hash=bf966c244f9f7c52b75ae7d56ff8f8c0fbda498cd678f4003ee3ed2c40961786`。
- 当前 readiness：assignment request `state_hash=8a4596dbb16f55932e36b256fc22852e1f8ca52da22bdd85d6d1c79d23b61c1b`，closure decision request `state_hash=afc1155fafad8c460db5e09eb9890e7408a1e28dd0bf155121bf1a0308529e34`，final readiness `state_hash=cf9a46ccbdfd35b01bd579511ed7ae1cdfcac411e00d8f610c80625f596e1094`。
- request 状态现在显示 `zero_proof_artifact_present=true`、`p0_zero_proven=true`、`p1_zero_proven=true`，并移除 stale `p0_p1_zero_proof_artifact_missing`；这只表示 artifact 被 request 状态消费，不表示 P0/P1 closure。
- 边界：No P0/P1 closure, S2PLT02/S2PLT03 terminal proof, S2PLT04 completion report, final bundle manifest, handoff, signoff, final command proof, SMTP send, scheduler enable/install/kickstart, Release, restore, CURRENT/V7 change, public schema/DB/source/ranking/queue mutation, DAILY_OPERATION, Stage2/S3 production acceptance, or production side effect is introduced.
- 证据：`governance/run_manifests/ADP-S2PMT07-FINAL-BUNDLE-ZERO-PROOF-REQUEST-CONSUMPTION-SYNC-20260701.json`；`arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_FINAL_BUNDLE_ZERO_PROOF_REQUEST_CONSUMPTION_SYNC.md`。

## 2026-07-01 04:34:08 Australia/Sydney - S2PMT07 final reviewer assignment consumption sync

- 任务：`S2PMT07-FINAL-BUNDLE-REVIEWER-ASSIGNMENT-CONSUMPTION-SYNC`。
- 结果：`blocked_final_bundle_reviewer_assignment_consumed_no_production`。
- 已验证输入：`FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json`，assignment validation `state_hash=b5b117307bd61f168ae6a422b24c865227f4824191348b851081af66730ed2c2`。
- 当前 readiness：assignment request `state_hash=7f59ff864ad3a43f24e3b105f13a5aed8802729e8c18482483db8ed78c2921ad`，closure decision request `state_hash=246a736255b77c3a40f74fbdc4431f52367e3d474d4d13156a19ec9b6e7feddf`，final readiness `state_hash=be9cd3bb14da9d57dcaee0168bae396ed95049bf6c261515a5d39959cf3ad461`。
- 边界：No P0/P1 closure, S2PLT02/S2PLT03 terminal proof, S2PLT04 completion report, final bundle manifest, handoff, signoff, final command proof, SMTP send, scheduler enable/install/kickstart, Release, restore, CURRENT/V7 change, public schema/DB/source/ranking/queue mutation, DAILY_OPERATION, Stage2/S3 production acceptance, or production side effect is introduced.
- 证据：`governance/run_manifests/ADP-S2PMT07-FINAL-BUNDLE-REVIEWER-ASSIGNMENT-CONSUMPTION-SYNC-20260701.json`；`arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_FINAL_BUNDLE_REVIEWER_ASSIGNMENT_CONSUMPTION_SYNC.md`。


## 2026-07-01 04:05:59 Australia/Sydney - S2PMT07 final bundle no-write flags outermost sync

- Added outermost final-bundle no-write/no-enable/no-acceptance flags to `plan-final-bundle-prerequisites` and `validate-final-acceptance-bundle`.
- Live CLIs remain blocked with capture plan `12b564610114a7278b9566255085d5308984c28e433965581bcbde630e9bf9aa`, prerequisite plan `67fd78529ab74d520477820d588053c5796db88322a6affa111f278a203d5232`, final readiness `cfcd3d70c0cca7f0a5a8bc3804f599001e585a65dc80fed0cecc75996c6798ee`, and wait guard `581fe9f53d82db88959196f874d312e50b1739a839158f7bf2d38cc186c03506`.
- No S2PLT02/S2PLT03 terminal proof, S2PLT04 completion report, final-bundle manifest/handoff/signoff/final-command proof, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-07-01 03:46:29 Australia/Sydney - S2PLT02 terminal capture no-write flags top-level sync

- Added top-level S2PLT02 no-write/no-enable/no-acceptance flags to capture-plan and final-bundle summaries.
- Live CLIs remain blocked with capture plan `12b564610114a7278b9566255085d5308984c28e433965581bcbde630e9bf9aa`, prerequisite plan `d95f0afad934a6692635960d48cda963074840c0615f9bafe1fb023ff9c4f612`, and final validator `0c032d9c804410f2b4ffe11cb52b00e91500fd7790d1eac533154650625b3c6e`; wait guard remains `581fe9f53d82db88959196f874d312e50b1739a839158f7bf2d38cc186c03506`.
- No S2PLT02/S2PLT03 terminal proof, S2PLT04 completion report, final-bundle manifest/handoff/signoff/final-command proof, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-07-01 00:13:52 Australia/Sydney - S2PMT07 final bundle S2PLT02 terminal count split

- Added explicit S2PLT02 count-split fields so final-bundle summaries distinguish existing real SMTP evidence from current capture-window additions.
- Current terminal proof count remains `1/2` real delivery days and `4/8` real emails; the 2026-06-29/2026-06-30 capture window adds `0` real days and `0` real emails, with `8` dry-run emails rejected for terminal proof.
- Live prerequisite, final validator, and capture-plan CLIs remain blocked with hashes `fb04c0b2582c24bdecf9d6d33658f25139ab8cf656cd6e22c69f01e5a3e1c419`, `7527930ba22a849c42ff55a0e65ea3c4b242e6c629f51db671468b63a1925a2b`, and `e7c9834eca19f665f1b57566f47cbd03ecaaf95fa9eb538187af3c3f7e1aa7f1`.
- No S2PLT02/S2PLT03 terminal proof artifact, S2PLT04 completion report, final-bundle manifest/handoff/signoff/final-command proof, SMTP send, scheduler enable/install/kickstart, Release, restore, CURRENT/V7 change, public schema/DB/source/ranking/queue mutation, P0/P1 closure claim, S2PLT02/S2PLT03/S2PLT04/S2PMT07 acceptance, DAILY_OPERATION, Stage2/S3 production acceptance, or production side effect is introduced.

## 2026-06-30 23:50:28 Australia/Sydney - S2PMT07 final bundle S2PLT02 capture-window summary

- Added `terminal_capture_window_audit_summary` to S2PLT02 capture-plan summaries exposed by `plan-final-bundle-prerequisites` and `validate-final-acceptance-bundle`.
- The summary records 2026-06-29/2026-06-30 as dry-run service dates only: `dry_run_email_count=8`, `real_sent_candidate_email_count=0`, `terminal_delivery_credit=false`, and `counts_toward_s2plt02_terminal_proof=false`.
- Live capture-window audit remains blocked with `state_hash=ab1ef6efbca6e019569e65849cd66dbb4cca336fca4bd95314252603db65a151` and scheduler status `launchagents_loaded_but_disabled_not_terminal_scheduler_proof`.
- No S2PLT02/S2PLT03 terminal proof, S2PLT04 completion report, final-bundle manifest/handoff/signoff/final-command proof, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-30 22:46:02 Australia/Sydney - S2PMT07 final bundle P0/P1 zero-proof status summary

- Added top-level `s2plt04_completion_evidence_audit_summary` to `plan-final-bundle-prerequisites` and `validate-final-acceptance-bundle` while keeping S2PLT04 completion report blocked and unwritten.
- Added top-level `p0_p1_zero_proof_status_summary` to `plan-final-bundle-prerequisites` and `validate-final-acceptance-bundle`.
- The summary separates immutable V7.1 inherited baseline counts `P0=8;P1=37` from the current valid zero-proof artifact `current_zero_proof_counts=P0=0;P1=0`.
- Current live CLIs remain blocked / exit 2 for final-bundle prerequisites and final bundle validation; `validate-p0-p1-zero-proof --json` passes with state hash `bf966c244f9f7c52b75ae7d56ff8f8c0fbda498cd678f4003ee3ed2c40961786`.
- No S2PLT02/S2PLT03 terminal proof, S2PLT04 completion report, final-bundle manifest/handoff/signoff/final-command proof, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-30 11:45:16 Australia/Sydney - S2PLT02 real delivery manifest normalization

- Added `build-s2plt02-normalized-delivery-manifest`, a no-write builder that converts the historical 2026-06-28 real M1-M4 manifest into a strict normalized S2PLT02 input.
- The normalized manifest binds raw hash `a795bd90778b5a0bbbd217d286f696936954af47a1a547ed689f907b677d9fa2`, validates with `normalized_manifest_ready=true`, `manifest_validation_state_hash=91bf1a4477c621a75fceed90efecdb620341cfc97d5a751c127cc5ffbd6a0d99`, and `state_hash=c56a7a1a5e9cb8a81ba0b05aa848c05e1577ce7558bae1700ea4563652c2d93c`.
- Direct strict validation of the raw historical manifest remains `blocked_missing_explicit_no_production_flags`; future terminal proof assembly must consume complete normalized manifests.
- No second real SMTP day, live terminal proof artifact, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-30 11:05:56 Australia/Sydney - S2PLT02 real delivery manifest input validator

- Added `validate-s2plt02-real-delivery-manifest`, a no-write validator for one complete real M1-M4 delivery manifest before S2PLT02 terminal proof assembly.
- Normalized first-day evidence validates with `delivery_manifest_ready=true`, `service_date=2026-06-28`, `observed_email_count=4`, `sent_mail_products=M1,M2,M3,M4`, `artifact_written=false`, `real_smtp_send_enabled=false`, `scheduler_install_enabled=false`, `daily_operation_enabled=false`, and state hash `8e345486be00628254e15147aec0495c924a3e9b7f5a22eda2583b7c74bddb24`.
- Direct strict validation of the historical committed 2026-06-28 manifest returns blocked / exit 2 because it predates explicit no-production fields. This preserves fail-closed terminal proof input handling.
- No second real SMTP day, live terminal proof artifact, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-30 10:41:36 Australia/Sydney - S2PLT02 terminal delivery proof capture plan

- Added `plan-s2plt02-terminal-delivery-proof-capture`, a no-write ordered capture plan for the future S2PLT02 terminal delivery proof.
- Current plan returns blocked / exit 2 with `next_executable_step=CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY`; missing inputs remain `SECOND_REAL_DELIVERY_DAY`, `EIGHT_REAL_EMAILS`, `REAL_SCHEDULER_PROOF`, and `S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT`.
- The plan lists the six required steps from second real M1-M4 SMTP day capture through independent review, live artifact write, and `validate-s2plt02-terminal-delivery-proof --repo-root . --json`; state hash `81d89c0b03458d4b5cc569ae1d994b7d02ef36dfa89377516f7968619d03e878`.
- No live terminal proof artifact, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-30 10:12:54 Australia/Sydney - S2PLT02 terminal delivery input inventory

- Added `audit-s2plt02-terminal-delivery-inputs`, a no-write inventory of current S2PLT02 terminal delivery proof inputs.
- Current inventory returns blocked / exit 2 with ready inputs `S2PLT01_TERMINAL_ACCEPTANCE`, `FIRST_REAL_DELIVERY_DAY`, `NO_DUPLICATE_EMAILS`, `M4_WATERMARK_PROOF`, `REAL_SMTP_PROOF`, and `P0_P1_ZERO_PROOF`; missing inputs remain `SECOND_REAL_DELIVERY_DAY`, `EIGHT_REAL_EMAILS`, `REAL_SCHEDULER_PROOF`, and `S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT`.
- Current observed real delivery remains `1/2` day and `4/8` emails; `artifact_written=false`, `real_smtp_send_enabled=false`, `scheduler_install_enabled=false`, `daily_operation_enabled=false`, and state hash `5976272c0102361222027116f94f5a73cc53e87fa18d1b0e9a5d82208e7c4444`.
- No live terminal proof artifact, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-30 09:48:07 Australia/Sydney - S2PLT02 real scheduler proof input validator

- Added `validate-s2plt02-real-scheduler-proof`, a no-write validator for the future real launchd scheduler proof manifest consumed by the S2PLT02 terminal proof draft builder.
- Sample fixture output validates with `scheduler_proof_ready=true`, `artifact_written=false`, `scheduler_install_enabled=false`, `daily_operation_enabled=false`, and state hash `5e1157dc9c710501cb2bf2e5dcdd3cc09afb40ee68164ff32d844e993843fb80`.
- No current runtime scheduler proof, live terminal proof artifact, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-30 09:19:10 Australia/Sydney - S2PLT02 terminal delivery proof artifact draft builder

- Added `build-s2plt02-terminal-delivery-proof-artifact-draft`, a stdout-only builder for future `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json` candidates.
- Sample fixture output self-validates with `artifact_written=false`, `artifact_validation_errors=[]`, state hash `beb8f19417b694428749bef5eb01de375ce2321f209c9086dfe4862bf48c2a8b`, and acceptance hash `5aa91771f2900db713fb865a12cb69f5c09bd6b03761083337c2d58af13a3b96`.
- No live terminal proof artifact, SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-30 08:01:19 Australia/Sydney - S2PLT02 live authorization

- Added and validated live no-production `FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json`.
- Updated final-bundle prerequisite routing so the next executable task is now `S2PLT02_TERMINAL_DELIVERY_PROOF` while S2PLT04/final bundle/production acceptance remain blocked.
- No SMTP, scheduler, Release, restore, CURRENT/V7, public schema, DB, source, ranking, queue, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-29 23:21:34 Australia/Sydney - S2PMT07 final bundle manifest template

- Added template-only `FINAL_ACCEPTANCE_BUNDLE/templates/manifest.template.json` for the future live final bundle manifest.
- Kept live `FINAL_ACCEPTANCE_BUNDLE/manifest.json` missing and final bundle readiness blocked.
- No SMTP, scheduler, Release, restore, CURRENT/V7, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-29 23:05:25 Australia/Sydney - S2PLT02 authorization template

- Added owner-fillable `s2plt02_real_proof_capture_authorization.template.json` under final bundle templates.
- Kept live `FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json` missing and S2PLT02/S2PMT07 blocked.
- No SMTP, scheduler, Release, restore, CURRENT/V7, DAILY_OPERATION, or production acceptance was enabled.

## 2026-06-29 22:44:04 Australia/Sydney - S2PLT02-REAL-PROOF-CAPTURE-READINESS-RUNTIME-STATE-SYNC

- Updated `audit-s2plt02-real-proof-capture-readiness --json` to include `launchctl print` runtime state for daily/health/watchdog LaunchAgents in addition to disabled-state parsing.
- Current readiness remains blocked / exit 2 with `all_required_launchagents_disabled=true`, `all_required_launchagents_loaded=true`, `all_required_launchagents_not_running=true`, `all_required_launchagents_have_calendar_triggers=true`, `launchagents_loaded_but_disabled=true`, `scheduler_runtime_evidence_status=launchagents_loaded_but_disabled_not_terminal_scheduler_proof`, and state hash `79ac4987239ecad8d4eee82de0157901b59259100e6d738bd1b15d17a37dc76e`.
- Re-ran the stdout-only S2PLT02 authorization draft CLI against the new readiness hash; draft state hash `03f6910d79ca02f6447ebdb3409892008841a1a9752d59d29e9bc38dd1fdea83`, draft authorization hash `sha256:a2262579bac6f9d4594a46d06424eb40f7c953de246a9ffc7e9ae3f4389db1a2`, live authorization artifact still missing, and final-bundle prerequisite plan hash `f05b64685d487f28c9ddabb1216e5c67c5c4391ba86e5d5d5341aa398fa9a3a4`.
- This does not create `FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json`, authorize real proof capture, send SMTP, enable scheduler, upload Release assets, restore production, change CURRENT/V7, mutate public schema/DB/source/ranking/queue, enable DAILY_OPERATION, or claim Stage2/S3 production acceptance.

## 2026-06-29 21:49:37 Australia/Sydney - S2PMT07-FINAL-BUNDLE-AUTH-DRAFT-LIVE-GUARD

- Updated `plan-final-bundle-prerequisites --json` so the blocked prerequisite plan exposes the current distinction between a passing S2PLT02 authorization draft CLI dry-run and the missing live authorization artifact.
- Current guard fields are `next_executable_command_dry_run_status=pass`, `next_executable_command_dry_run_wrote_artifact=false`, `draft_authorization_is_live_authorization=false`, `live_authorization_artifact_status=missing`, `live_authorization_validation_errors=["s2plt02_real_proof_capture_authorization_missing"]`, and state hash `6c452e9e59c107f99c0b881fec64da2df9b7fa0d7428f69218dc22bd83f03eb1`.
- This does not create `FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json`, authorize real proof capture, send SMTP, enable scheduler, upload Release assets, restore production, change CURRENT/V7, mutate public schema/DB/source/ranking/queue, enable DAILY_OPERATION, or claim Stage2/S3 production acceptance.

## 2026-06-29 21:20:40 Australia/Sydney - S2PMT07-FINAL-BUNDLE-NEXT-EXECUTABLE-COMMAND-SYNC

- Updated `plan-final-bundle-prerequisites --json` so the blocked prerequisite plan exposes `next_executable_command=build-s2plt02-real-proof-capture-authorization-artifact-draft`, owner input argument names, validation command, and evidence refs when `next_executable_task=S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION`.
- Current plan remains blocked / exit 2 with `next_required_step=S2PLT04_COMPLETION_REPORT`, `next_required_step_is_actionable=false`, `next_executable_command_writes_artifact=false`, `next_executable_command_satisfies_gate=false`, and state hash `dd5fc312ae8ce8f70dbdc291d55dfd987686de3c5de0daa4bd1b57f1857c92db`.
- This does not create `FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json`, authorize real proof capture, send SMTP, enable scheduler, upload Release assets, restore production, change CURRENT/V7, mutate public schema/DB/source/ranking/queue, enable DAILY_OPERATION, or claim Stage2/S3 production acceptance.

## 2026-06-29 17:41:57 Australia/Sydney - S2PLT02-REAL-PROOF-CAPTURE-READINESS

- Added `audit-s2plt02-real-proof-capture-readiness --json` and fail-closed readiness logic before any real S2PLT02 SMTP/scheduler proof capture can be treated as terminal evidence.
- Current readiness is blocked / exit 2 with `safe_to_collect_terminal_proof=false`, `real_proof_capture_authorized=false`, `all_required_launchagents_disabled=true`, `second_real_delivery_day_present=false`, `terminal_delivery_proof_artifact_present=false`, `real_scheduler_proven=false`, and state hash `819b1c3911892ce861fd5ba5bdde0dc381e303076beea684f35eb94c75975463`.
- Remaining blockers are `real_proof_capture_authorization_missing;required_launchagents_disabled;second_real_delivery_day_missing;dry_run_second_day_not_terminal;s2plt02_terminal_delivery_proof_artifact_missing;real_scheduler_not_proven`. S2PLT01 terminal acceptance and P0/P1 zero-proof are validated inputs, but S2PLT02/S2PLT03/S2PLT04/S2PMT07 acceptance and integrated production acceptance remain false.
- No SMTP, scheduler, Release, production restore, CURRENT/V7 contract, public schema, DB migration, source adapter, ranking, or production queue behavior was enabled or changed.

## 2026-06-29 16:33:19 Australia/Sydney - S2PLT02-DRY-RUN-SECOND-DAY-AUDIT

- Added `audit-s2plt02-dry-run-second-day --json` and fail-closed S2PLT02 dry-run audit logic so the 2026-06-29 local M1-M4 dry-run trace is visible but cannot be counted as the second real delivery day.
- Current audit result is blocked / exit 2 with `dry_run_mail_count=4`, `real_sent_mail_count=0`, `observed_natural_days_credit=0`, `observed_email_count_credit=0`, `counts_toward_s2plt02_terminal_proof=false`, and state hash `9fbd118380da579c2cd47a92e6fe3e54fc89ffd9b76dddb8d3a7199e5821e965`.
- Remaining S2PLT02 blockers are still `dry_run_evidence_only_not_real_smtp`, `real_scheduler_not_proven`, `two_consecutive_real_days_not_proven`, and `eight_real_emails_not_proven`; S2PLT02/S2PLT03/S2PLT04/S2PMT07 acceptance and integrated production acceptance remain false.
- No SMTP, scheduler, Release, production restore, CURRENT/V7 contract, public schema, DB migration, source adapter, ranking, or production queue behavior was enabled or changed.

## 2026-06-29 15:59:53 Australia/Sydney - S2PMT07-S2PLT02-TERMINAL-DELIVERY-PROOF-VALIDATOR

- Added `validate-s2plt02-terminal-delivery-proof` and a strict validator for future `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json`.
- Current validation remains blocked / exit 2 because the live terminal delivery proof artifact is missing: `artifact_present=false`, `terminal_delivery_proof_ready=false`, `s2plt02_accepted_by_artifact=false`, validation state hash `3fbde96111dd78d3ffe4474e012fa5d86de76a24e6fa7640d0310c178003e1db`, S2PLT02 readiness hash `faedeea7dcc41d0122044cbdd07c1901f01fa6a7ca39f0d580f9f6844fc3f9b2`, and precheck hash `94bd3841adf70c44e10963ad94da2dd3b57b68152882639ca2637997bdbf1ca1`.
- No S2PLT02/S2PLT03/S2PLT04/S2PMT07 acceptance, S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 14:51:01 Australia/Sydney - S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-CONSUMPTION

- Created `FINAL_ACCEPTANCE_BUNDLE/s2plt01_terminal_acceptance.json` after independent reviewer PASS; `validate-s2plt01-terminal-acceptance --json` and `audit-s2plt01-terminal-acceptance --json` now pass with acceptance hash `510ffaf0c3b9de5cb2398cc9cb2c1ffa652ffe6f7a4026abe3c0484275b5d615`.
- Updated S2PLT02/S2PLT04 final-gate logic so downstream gates consume `S2PLT01_ACCEPTED=true`; S2PLT04 audit now remains blocked only by `s2plt02_live_2d_terminal_proof_missing` and `s2plt03_resilience_terminal_proof_missing`.
- No S2PLT02/S2PLT03/S2PLT04/S2PMT07 acceptance, S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 14:25:47 Australia/Sydney - S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-ARTIFACT-VALIDATOR

- Added `validate-s2plt01-terminal-acceptance` and a strict validator for future `FINAL_ACCEPTANCE_BUNDLE/s2plt01_terminal_acceptance.json`.
- Current validation remains blocked / exit 2 because the live artifact is missing: `artifact_present=false`, `s2plt01_accepted_by_artifact=false`, validation state hash `fcd71fb7e6c8f9956edd7fc3e33deadeeb4349183daf0f3950f10df6d8d03431`, and terminal audit state hash `6461557654b36bb383b91eb98bc610c1cf497de8563f7f0aa897db08fc26d315`.
- No S2PLT01/S2PLT04 acceptance, S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 13:58:47 Australia/Sydney - S2PMT07-S2PLT04-COMPLETION-EVIDENCE-LATEST-SYNC

- Updated `audit-s2plt04-completion-evidence` so S2PLT04 completion evidence audit consumes the latest nonterminal S2PLT02 terminal-readiness zero-proof sync and S2PLT03 audit-blocker zero-proof sync evidence.
- Current S2PLT04 audit remains blocked / exit 2, with `completion_report_ready=false`, `s2plt04_completion_report_written=false`, state hash `717822760035bbebe20c429cd2db4e11501e9ebecc2bbc633a04f72de9914c58`, S2PLT02 terminal-readiness state hash `b318db2e8f90efc9a09bdaea6ee75e6da87d929f844bc9c4a53816dd2b648d0c`, and S2PLT03 latest audit report hash `3483d4a8c4248d3a41cfae5db4febbe7c9d42368ae6ae9311d0c5a9819d13466`.
- Remaining blockers are `s2plt01_not_accepted`, `s2plt02_live_2d_terminal_proof_missing`, and `s2plt03_resilience_terminal_proof_missing`; no S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 13:34:38 Australia/Sydney - S2PLT03-AUDIT-BLOCKER-ZERO-PROOF-SYNC

- Updated `audit-s2plt03-resilience-readiness` so S2PLT03 `audit_blockers` derives P0/P1 zero state from the committed `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` artifact validation.
- Current S2PLT03 audit remains blocked / exit 2, but now reports `audit_blockers.status=pass`, `audit_blockers.checks.P0_zero=true`, `audit_blockers.checks.P1_zero=true`, inherited audit-blocker counts `P0=0` / `P1=0`, and report hash `3483d4a8c4248d3a41cfae5db4febbe7c9d42368ae6ae9311d0c5a9819d13466`, superseding `d8cdd55b7848c6b7745a0707522f0277c7b7ef2f82e2ca2a0152e5c520211333`.
- Remaining blocker is `s2plt02_not_accepted`; no S2PLT03 acceptance, S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 13:10:37 Australia/Sydney - S2PMT07-S2PLT01-ENTRY-PRECHECK-ZERO-PROOF-SYNC

- Updated `audit-s2plt01-terminal-acceptance` to expose `current_entry_precheck_zero_proof_readiness.status=pass` from committed replay evidence plus committed P0/P1 zero-proof artifact validation.
- Current S2PLT01 audit remains blocked, but now reports `entry_precheck_passed=true`, `entry_precheck_report_hash=b7c0b96f4cdc570a935680f52dd3804b262ef4898630df8cfadc9ce2796eb55b`, `observed_replay_days=30`, `observed_mail_previews=120`, `source_terminal_states_proven=true`, `future_leakage_count=0`, and `p0_p1_blocker_count=0`.
- The historical no-production replay execution hash remains `47394faede126c943dc46b3ca2ae0c8680d5ef32f1f26f4618e3064fcbc28171`; no S2PLT01 acceptance is claimed, and no S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 12:42:41 Australia/Sydney - S2PMT07-S2PLT01-REPLAY-PAYLOAD-READINESS-SYNC

- Updated `audit-s2plt01-terminal-acceptance` to verify the existing no-production S2PLT01 replay payload execution package and bind its execution hash.
- Current S2PLT01 audit remains blocked, but now reports `replay_payload_execution_package_validation.status=pass`, `observed_replay_days=30`, `observed_mail_previews=120`, `source_terminal_states_proven=true`, and remaining blockers `review_receipt_is_nonterminal`, `s2plt01_not_accepted`.
- No S2PLT01 acceptance is claimed; no S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 12:23:25 Australia/Sydney - S2PMT07-S2PLT01-ZERO-PROOF-READINESS-SYNC

- Updated `audit-s2plt01-terminal-acceptance` to consume the committed `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` artifact.
- Current S2PLT01 audit remains blocked, but now reports `inherited_p0_zero=true` and `inherited_p1_zero=true`; remaining blockers are `full_replay_not_executed`, `review_receipt_is_nonterminal`, and `s2plt01_not_accepted`.
- No S2PLT01 acceptance is claimed; no S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 12:01:17 Australia/Sydney - S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-DEPENDENCY-ORDER

- Fixed the S2PLT01 terminal acceptance audit dependency order so S2PLT01 readiness no longer depends on later S2PLT04 completion or S2PMT07 final signoff.
- Current S2PLT01 audit remains blocked: `full_replay_executed=false`, `S2PLT01_ACCEPTED=false`, inherited P0/P1 are still open, and the existing independent replay review receipt remains nonterminal.
- No S2PLT01 acceptance is claimed; no S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 12:12:00 Australia/Sydney - S2PLT03-ZERO-PROOF-RESILIENCE-SYNC

- Added `audit-s2plt03-resilience-readiness` CLI and updated S2PLT03 resilience precheck to consume the committed `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` artifact.
- Current S2PLT03 readiness remains blocked, but now reports `p0_zero=true` and `p1_zero=true`; the only current S2PLT03 readiness blocker is `s2plt02_not_accepted`.
- Updated S2PLT04 completion evidence audit to include the new S2PLT03 zero-proof readiness sync manifest as nonterminal evidence; no S2PLT03 acceptance, S2PLT04 completion report, final command execution, next-agent handoff, independent signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 change, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 11:06:42 Australia/Sydney - S2PLT02-ZERO-PROOF-READINESS-SYNC

- Updated the S2PLT02 terminal-readiness audit to consume the committed `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` artifact, so current readiness now reports `P0_ZERO=true` and `P1_ZERO=true`.
- Updated the S2PLT04 completion evidence audit so S2PLT02 remaining blockers no longer include inherited P0/P1 after zero-proof validation; the remaining S2PLT02 blockers are S2PLT01 acceptance, a second consecutive real natural day, eight total real emails, and real scheduler proof.
- This is still a blocked readiness sync only: no S2PLT02 acceptance, S2PLT04 completion report, final command execution, next-agent handoff, independent signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 change, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 10:35:11 Australia/Sydney - S2PLT02-TERMINAL-READINESS-AUDIT

- Added `audit-s2plt02-terminal-readiness` CLI so owner/coordinator and future reviewers can see the current S2PLT02 terminal-readiness state without treating partial evidence as acceptance.
- Current audit result is blocked: M4 watermark proof is ready, one natural day and four real emails are recorded, and real SMTP evidence is present, but S2PLT01 acceptance, a second real natural day, eight total real emails, real scheduler proof, and inherited P0/P1 top-level stop gates remain missing.
- The S2PLT04 completion evidence audit now references this S2PLT02 nonterminal readiness manifest; no S2PLT02 acceptance, S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 10:12:17 Australia/Sydney - S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-AUDIT

- Added `audit-s2plt01-terminal-acceptance` CLI so owner/coordinator and future reviewers can see that the existing S2PLT01 independent replay review receipt is nonterminal evidence only.
- Current audit result is blocked: review receipt is present and review package passed, but `full_replay_executed=false`, `S2PLT01_ACCEPTED=false`, `S2PLT04_COMPLETED=false`, `S2PMT07_FINAL_SIGNOFF=false`, and inherited V7.1 P0/P1 production stop gates remain open.
- No S2PLT01 acceptance is claimed; no S2PLT04 completion report, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, or integrated production acceptance is created or enabled.

## 2026-06-29 09:41:06 Australia/Sydney - S2PMT07-S2PLT04-COMPLETION-EVIDENCE-AUDIT

- Added `audit-s2plt04-completion-evidence` CLI so owner/coordinator and future reviewers can see the exact terminal evidence gaps before any S2PLT04 completion report is written.
- Current audit result is blocked: `S2PLT01_REPLAY_REVIEW` is nonterminal because `S2PLT01_ACCEPTED=false`, `S2PLT02_LIVE_2D_PROOF` terminal proof is missing, and `S2PLT03_RESILIENCE_PROOF` terminal proof is missing; committed `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` remains pass for zero-proof artifact validation only.
- No `FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json` is created; S2PLT04, final command execution, handoff, signoff, final manifest, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, and integrated production acceptance remain blocked or false.

## 2026-06-29 09:09:03 Australia/Sydney - S2PMT07-S2PLT04-COMPLETION-REPORT-DEPENDENCY-ORDER

- Fixed the S2PLT04 completion report validator/template ordering so the report no longer requires later final-bundle manifest evidence (`FINAL_BUNDLE_MANIFEST` / `FINAL_ACCEPTANCE_BUNDLE_PRESENT`) as a prerequisite.
- The real `FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json` is still missing and S2PLT01/S2PLT02/S2PLT03 terminal acceptance is still not proven by this change.
- S2PLT04 completion report, final command execution, handoff, signoff, final manifest, P0/P1 top-level closure, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, and integrated production acceptance remain blocked or false.

## 2026-06-29 08:46:12 Australia/Sydney - S2PMT07-CLI-MODULE-ENTRYPOINT

- Added the missing `__main__` module entrypoint so `python3 -B -m arxiv_daily_push.cli plan-final-bundle-prerequisites --json` dispatches to the same CLI path as direct `main([...])` calls.
- The module command now returns blocked JSON with `next_required_step=S2PLT04_COMPLETION_REPORT` and exit code `2`; this is a proof-chain executability fix only.
- S2PLT04 completion report, final command execution, handoff, signoff, final manifest, P0/P1 top-level closure, SMTP, scheduler, Release, restore, CURRENT/V7 changes, DAILY_OPERATION, and integrated production acceptance remain blocked or false.

## 2026-06-29 00:40:23 Australia/Sydney - S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-DRAFT-CLI

- Added `build-final-reviewer-assignment-artifact-draft` CLI to produce a stdout-only, ordered JSON draft for the future independent final reviewer assignment artifact from explicit owner/coordinator inputs.
- The draft command computes `assignment_hash=sha256:1b31de0eae2283814fa5e458d69700774f2ae8441187a3e8f0fd3a03740c2dec` and validates with no errors, but writes no live artifact, assigns no reviewer, satisfies no assignment gate, closes no P0/P1 findings, completes no S2PLT04 step, executes no final commands, and accepts no production.
- SMTP, scheduler, Release, restore, public schema, DB migration, production queue, source adapter, ranking, CURRENT/V7, V7.1 baseline, V7.2 contract, DAILY_OPERATION, and integrated production acceptance remain unchanged.

## 2026-06-29 00:14:34 Australia/Sydney - S2PMT07-FINAL-BUNDLE-PREREQUISITE-PLAN-CLI

- Expose `adp plan-final-bundle-prerequisites --json` as a blocked, no-production S2PMT07 prerequisite plan CLI.
- The plan consumes committed `FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json` as `NO_PRODUCTION_SIDE_EFFECT_ATTESTATION=pass` while keeping reviewer assignment, P0/P1 zero proof, S2PLT04 report, final command execution, handoff, signoff, manifest, final bundle, P0/P1 closure, and production acceptance blocked.
- 2026-06-28 23:58:57 Australia/Sydney: Added remaining S2PMT07 final-bundle artifact CLI validators for manifest, S2PLT04 completion report, no-production attestation, and next-agent handoff; manifest/report/handoff remain blocked when missing, committed no-production attestation validates pass, and no final-bundle artifact, P0/P1 closure, S2PLT04 completion, SMTP, scheduler, Release, restore, DAILY_OPERATION, or integrated production acceptance is claimed.
- 2026-06-28 23:41:05 Australia/Sydney: Added `validate-final-command-execution` CLI validation for future `FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json`; missing artifact returns blocked/exit 2 with `final_command_execution_missing`, and final command execution, reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 23:23:48 Australia/Sydney: Added `validate-p0-p1-zero-proof` CLI validation for future `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json`; missing artifact returns blocked/exit 2 with `p0_p1_zero_proof_artifact_missing`, and P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 23:04:29 Australia/Sydney: Added `build-final-closure-decision-owner-packet` CLI output for the existing S2PMT07 independent final closure decision owner/reviewer packet; the command exposes the future closure-decision artifact ref and required owner actions while reviewer assignment, closure decision, P0/P1 zero proof, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 22:44:37 Australia/Sydney: Added `validate-final-acceptance-bundle` CLI readiness precheck for S2PMT07 final acceptance bundle artifacts; command returns blocked/exit 2 with missing real artifact list while `FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json` remains recognized as present, and reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 22:23:15 Australia/Sydney: Hardened all S2PMT07 final-bundle artifact validators with recursive template placeholder rejection, so copied template values containing `REPLACE_WITH` or `RECOMPUTE_WITH` cannot pass even if the relevant artifact hash is recomputed; the real assignment artifact, reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 22:03:08 Australia/Sydney: Hardened S2PMT07 independent final reviewer assignment artifact validation so copied template placeholders such as `REPLACE_WITH_REAL_TIMESTAMP_AUSTRALIA_SYDNEY` and `REPLACE_WITH_REAL_INDEPENDENT_REVIEWER_ID` are rejected even if `assignment_hash` is recomputed; the real assignment artifact, reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 21:37:18 Australia/Sydney: Added `build-final-reviewer-assignment-owner-packet` CLI output for the existing S2PMT07 independent final reviewer assignment owner/coordinator packet; the command exposes required owner actions and review refs while assignment artifact, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 21:07:59 Australia/Sydney: Added `validate-final-reviewer-assignment` CLI validation for future `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json`; missing artifact returns blocked, valid temporary artifact can pass schema/hash/no-production checks, and reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 20:43:00 Australia/Sydney: Promoted `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` into the formal S2PMT07 final bundle required item list and directory-level artifact validation keys; the real assignment artifact remains missing, so final bundle, P0/P1 closure, S2PLT04, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 20:10:59 Australia/Sydney: Hardened S2PMT07 final bundle readiness so `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` validation is a hard prerequisite for top-level final bundle readiness even when directory-level final bundle artifact validation passes; the assignment artifact remains missing, and reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 19:40:00 Australia/Sydney: Wired S2PMT07 final bundle readiness to consume a future `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` artifact; the current artifact remains missing, and reviewer assignment, P0/P1 closure, S2PLT04, final bundle, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 19:05:22 Australia/Sydney: Added template-only S2PMT07 final bundle artifact skeletons under `FINAL_ACCEPTANCE_BUNDLE/templates/`; these templates do not satisfy readiness, and manifest, P0/P1 zero proof, S2PLT04 completion report, independent signoff, final command execution, next-agent handoff, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 17:32:43 Australia/Sydney: Synced S2PMT07 final bundle readiness with the committed no-production side-effect attestation artifact; readiness now consumes `FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json` while final bundle manifest, P0/P1 zero proof, S2PLT04 completion, independent signoff, final command execution, next-agent handoff, scheduler, SMTP, Release, restore, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 16:32:45 Australia/Sydney: Added S2PMT07 local runtime no-production gate; local ADP daily/health/watchdog LaunchAgents are disabled/not running and `ADP_ALLOW_SMTP_SEND=false`, while no SMTP, scheduler, Release, restore, P0/P1 closure, S2PLT04 completion, final bundle, DAILY_OPERATION, or integrated production acceptance is claimed.
- 2026-06-28 16:01:08 Australia/Sydney: Restored A-005 trust-boundary parameter selector coverage for `PARAM-ADP-955..959`; implementation congruence now verifies 1050/1050 active parameters while S2PMT07 independent final reviewer assignment, P0/P1 zero proof, S2PLT04, final bundle, and all production gates remain blocked.
- 2026-06-28 15:26:22 Australia/Sydney: Added S2PMT07 independent final closure decision owner/reviewer packet; it exposes required owner/reviewer actions, zero-proof decision location, assignment prerequisite, review refs, and no-production flags while the actual reviewer assignment, closure decision, P0/P1 zero proof, final bundle, S2PLT04, and all production gates remain blocked.
- 2026-06-28 14:11:24 Australia/Sydney: Added S2PMT07 remaining blocker matrix; current seven final-gate blockers are mapped to required future evidence and owner actions while P0/P1 closure, S2PLT04, final bundle, SMTP/scheduler/Release/restore, CURRENT/V7, DAILY_OPERATION, and integrated production acceptance remain blocked.
- 2026-06-28 13:12:48 Australia/Sydney: Added S2PLT02 explicit M4 watermark proof validator; current service date 2026-06-28 remains blocked because no explicit proof record exists, while S2PLT02 acceptance and all production gates remain false.
- 2026-06-28 12:47:11 Australia/Sydney: Added S2PLT02 delivery evidence ledger over committed M1-M4 real-delivery manifests; current state remains partial at 1/2 natural days and 4/8 emails with duplicate counts zero, while S2PLT02 acceptance and all production gates remain blocked.
- 2026-06-28 10:26:53 Australia/Sydney: Added local daily M1-M4 send orchestration; runner now builds four Email V1 products, records per-product SMTP evidence, syncs actual sent count to user center, and skips already-sent same-day products during catch-up.
- 2026-06-28 11:28:25 Australia/Sydney: Recorded real 2026-06-28 M1-M4 resend execution evidence; M1 was treated as historical sent and M2-M4 were sent by SMTP, updating GitHub user center to 4 / 4 without claiming Stage 2 production acceptance.
- 2026-06-28 10:08:17 Australia/Sydney: Added S2PMT07 mainline attestation state; target S2PMT07 evidence commit is contained in origin/main with open PR count 0 and ADP/arxiv/s2p remote branch count 0, while P0/P1 closure, final bundle, S2PLT04, and all production gates remain blocked.
- 2026-06-28 08:48:03 Australia/Sydney: Added S2PMT07 independent final reviewer assignment request state; reviewer assignment, closure decision, zero-proof artifact, P0/P1 closure, S2PLT04, final bundle, and production gates remain blocked.
- 2026-06-28 08:21:10 Australia/Sydney: Added S2PMT07 independent final closure decision request state; reviewer assignment, closure decision, zero-proof artifact, P0/P1 closure, S2PLT04, final bundle, and production gates remain blocked.
- 2026-06-28 07:56:58 Australia/Sydney: Added S2PMT07 P0/P1 zero-proof assembly state; candidate inputs are visible but independent final closure decision, zero-proof artifact, P0/P1 closure, S2PLT04, final bundle, and production gates remain blocked.
- 2026-06-28 07:41:22 Australia/Sydney: Added S2PMT07 final bundle prerequisite plan; current final bundle artifacts remain missing and no production gates changed.
- 2026-06-28 07:13:17 Australia/Sydney: Added S2PMT07 next-agent handoff artifact validator; current handoff remains missing and no production gates changed.
- 2026-06-28 06:48:44 Australia/Sydney: Added S2PMT07 no-production side-effect attestation artifact validator; current attestation remains missing and no production gates changed.
- 2026-06-28 06:18:50 Australia/Sydney: Added S2PMT07 independent review signoff artifact validator; current signoff remains missing and no production gates changed.
- 2026-06-28 05:57:25 Australia/Sydney: Added S2PMT07 final command execution artifact validator; current artifact remains missing and no production gates changed.
- Added `S2PMT07-FINAL-BUNDLE-MANIFEST-VALIDATOR` so any future `FINAL_ACCEPTANCE_BUNDLE/manifest.json` must pass strict schema version, exact manifest decision, bundle item hashes, artifact validation statuses, closure-state proof, no-production flags, and manifest-hash validation; current state remains blocked with the manifest and final bundle missing, inherited P0=8/P1=37, no S2PLT04 completion, no SMTP/scheduler/Release/restore, no schema/DB/queue/source/ranking/CURRENT/V7 changes, no P0/P1 closure, and no integrated production acceptance.
- Added `S2PMT07-P0-P1-ZERO-PROOF-VALIDATOR` so any future `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` must pass strict schema version, candidate evidence refs, zero P0/P1 counts, final bundle refs, no-production flags, and decision-hash validation; current state remains blocked with the artifact missing, inherited P0=8/P1=37, no final bundle, no S2PLT04 completion, no SMTP/scheduler/Release/restore, no schema/DB/queue/source/ranking/CURRENT/V7 changes, no P0/P1 closure, and no integrated production acceptance.
- Added `S2PMT07-P0-P1-ZERO-PROOF-READINESS` so future P0/P1 closure must provide `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` with required fields, independent final closure decision, zero open P0/P1 counts, and no-production attestation; current state remains blocked with the artifact missing, inherited P0=8/P1=37, no final bundle, no S2PLT04 completion, no SMTP/scheduler/Release/restore, no schema/DB/queue/source/ranking/CURRENT/V7 changes, no P0/P1 closure, and no integrated production acceptance.
- Added `S2PMT07-P0-P1-TECHNICAL-CANDIDATE-READINESS` so existing 8 P0 and 37 P1 finding-level technical closure candidates are visible to S2PMT07 final acceptance bundle readiness as prebundle evidence only; this does not create P0/P1 zero proof, close inherited P0/P1, complete S2PLT04, create the final bundle, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Synced `S2PLT04-FINAL-BUNDLE-READINESS-SYNC` so the S2PLT04 integration-candidate precheck now embeds final acceptance bundle readiness detail and required missing items; this does not create the final acceptance bundle, complete S2PLT04, close P0/P1, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Synced `S2PLT04-STATE-CONTENT-EVIDENCE-BUNDLE-SYNC` so the S2PLT04 integration-candidate precheck now binds local state-consistency and content evidence to deterministic no-production bundles with source tasks, evidence refs, and hashes; this does not complete S2PLT04, create the final acceptance bundle, close P0/P1, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Synced `S2PLT04-S2PLT01-REPLAY-REVIEW-EVIDENCE-SYNC` so the S2PLT04 integration-candidate precheck now consumes the existing S2PLT01 independent replay review receipt as non-terminal local evidence; this does not satisfy S2PLT01 authoritative acceptance, complete S2PLT04, create the final acceptance bundle, close P0/P1, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Synced `S2PLT04-S2PLT02-PRECHECK-EVIDENCE-SYNC` so the S2PLT04 integration-candidate precheck now consumes the existing S2PLT02 live two-day readiness precheck as non-terminal local evidence; this does not satisfy S2PLT02 authoritative completion, prove the real two-day run, complete S2PLT04, create the final acceptance bundle, close P0/P1, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Synced `S2PLT04-LOCAL-DRILL-EVIDENCE-SYNC` so the S2PLT04 integration-candidate precheck now consumes the existing S2PLT03 local no-production resilience drill bundle as non-terminal local evidence; this does not satisfy S2PLT03 authoritative completion, complete S2PLT04, create the final acceptance bundle, close P0/P1, enable SMTP/scheduler/Release/restore, mutate schema/DB/queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, or claim integrated production acceptance.
- Recorded `S2PLT03` as a deterministic fail-closed resilience, capacity, rollback, and state-count precheck with explicit blockers for missing S2PLT02 acceptance, missing rate-limit/parser-drift/restart/disk drills, missing backup restore-point, missing executable rollback, missing ledger count conservation, and inherited P0/P1 open findings; this does not accept S2PLT03, run live drills, execute production restore, send SMTP, enable scheduler, upload Release, mutate schema/DB/queues, change source adapters/ranking/CURRENT/V7 contracts, close P0/P1, enable daily operation, or claim integrated production acceptance.
- Synced `S2PLT01-REPLAY-REVIEW-STATUS-SYNC` so current replay-chain records recognize the existing local no-production S2PLT01 replay payload execution and independent replay review receipts, while leaving S2PLT01 acceptance, S2PLT04, S2PMT07, P0/P1 closure, SMTP, scheduler, Release, CURRENT/V7 contracts, daily operation, and integrated production acceptance blocked.
- Recorded `S2PMT07-P1-C002-TECHNICAL-REVIEW` with verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making C-002 owner-status runtime-state evidence a finding-level technical closure candidate after empty/delayed/failed states were added to the S2PIT02 gate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW` with verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making B-008 fake SMTP crash-window evidence a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW` with verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making B-007 multiprocess race evidence a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW` with verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making A-005 trust-boundary evidence a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW` with verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making A-004 typed frontstage evidence a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.

- Added `S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE` so the B-008 P0 receipt now includes a local fake SMTP accept-after-kill runner-boundary proof with restart reconciliation blocked without `provider_accept_ref`, durable fake provider ref finalization to `SENT`, stable `mail_key`/`message_id`, no duplicate resend, and no real SMTP side effects; this is evidence routing only and leaves independent signoff, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE` so the B-007 P0 receipt now includes a local multiprocess runner-boundary proof with 4 worker processes, 400 observed M1-M4 attempts, 4 active revisions, 396 blocked duplicates, and all worker exit codes equal to zero; this is evidence routing only and leaves independent signoff, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Fixed A-003 transactional outbox retry safety so `ACCEPTED_PENDING_COMMIT` cannot be claimed before provider reconciliation and `BLOCKED`/`SENT` rows with `retry_safe=false` cannot be reclaimed after lease expiry; recorded `S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW` with reviewer verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making A-003 a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW` with a read-only reviewer verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making A-002 a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, production restore, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW` with a read-only reviewer verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making A-001 a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, production restore, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded `S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW` with a read-only reviewer verdict `PASS_WITH_NO_PRODUCTION_ACCEPTANCE`, making B-001 a finding-level technical closure candidate while leaving P0/P1 counters, S2PMT07 final pass, S2PLT04, final bundle, final commands, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance unchanged.
- Recorded B-001 isolated launchd proof reconciliation in GitHub evidence surfaces so the previous missing isolated install-run-uninstall proof is now reviewable by S2PMT07 independent review; P0/P1 counters, SMTP, scheduler, Release, CURRENT, V7 contracts, daily operation, and integrated production acceptance remain unchanged.
## Unreleased - 2026-06-24

- Added `S2PMT04-INSTALL-LIFECYCLE-B001` dedicated local evidence and refreshed `S2PMT07-P0-REVIEW-RECEIPT-REFRESH-B001` so P0 receipt row B-001 points to controlled install/status/trigger-probe/uninstall lifecycle proof instead of older aggregate lifecycle/cache evidence; the real isolated install-run-uninstall proof remains missing and blocked, and this leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, launchd bootstrap, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT03-OUTBOX-DELIVERY-A003` dedicated local evidence and refreshed `S2PMT07-P0-REVIEW-RECEIPT-REFRESH-A003` so P0 receipt row A-003 points to transactional outbox Message-ID stability, changed-revision rekeying, 100-claim contention, SMTP accepted-before-commit fail-closed handling, provider-ref finalization, and at-least-once/no-exactly-once proof instead of aggregate lease-fencing evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002` dedicated local evidence and refreshed `S2PMT07-P0-REVIEW-RECEIPT-REFRESH-A002` so P0 receipt row A-002 points to real Stage 1 backup/restore probes for new-target restore, overwrite restore with previous-target backup preservation, invalid overwrite target preservation, and temporary-file cleanup instead of aggregate atomic recovery evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, production restore, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT02-RESTORE-PATH-SAFETY-A001` dedicated local evidence and refreshed `S2PMT07-P0-REVIEW-RECEIPT-REFRESH-A001` so P0 receipt row A-001 points to real Stage 1 restore probes for relative path traversal, absolute path escape, symlink escape, and invalid overwrite target preservation instead of aggregate atomic recovery evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, production restore, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PAT05-TRACEABILITY-CHAIN-C010` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C010` so P1 receipt row C-010 points to a 247-row clickable feature/task/test/run-evidence chain in the shallow GitHub user center instead of aggregate traceability surfaces; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PIT05-FOUR-CHECK-FRESHNESS-C003` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C003` so P1 receipt row C-003 points to four-check freshness, fact-source, drift-state, CI alarm, and page alarm proof instead of aggregate owner UX evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT06-SAFE-MANUAL-ACTION-C012` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C012` so P1 receipt row C-012 points to safe retry/cancel/requeue/skip/regenerate action proof instead of aggregate owner UX evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PIT02-OWNER-STATUS-C002` dedicated shallow GitHub mail/queue status evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C002` so P1 receipt row C-002 points to owner-visible `2 / 4` mail count, `299 = 30 + 269` candidate-pool conservation, sent/blocked/queued state coverage, and explicit `pending_daily_snapshot` review/action/asset/ROI fields instead of older deep owner-doc runtime dashboard evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PIT01-SHALLOW-USER-CENTER-C001` dedicated shallow GitHub user-center evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C001` so P1 receipt row C-001 points to `用户中心/README.md` and `用户中心/一看三查.md` path-gate proof instead of older deep owner-doc evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT04-PROCESS-LIFECYCLE-B002` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-B002` so P1 receipt row B-002 points to process-lifecycle SIGTERM/SIGINT matrix proof instead of older aggregate lifecycle/cache evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT01-ZERO-CRITICAL-CLAIM-A019` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-A019` so P1 receipt row A-019 points to the Stage 1 B1 zero-critical-claim gate proof instead of older aggregate security-boundary evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-FUTURE-HEARTBEAT-A015` dedicated local evidence and refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-A015` so P1 receipt row A-015 points to the future-heartbeat/DST/clock-skew phase record and manifest instead of the older aggregate S2PMT05 stress-E2E surface; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-A010-A016` so P1 receipt rows A-010, A-011, A-013, A-014, and A-016 point to their dedicated artifact atomic-publish, artifact SHA-256, scheduler-template, supporting-file-collision, and lesson-revision evidence records instead of older aggregate S2PMT02/S2PMT03/S2PMT04 surfaces; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH-A006-A009` so P1 receipt rows A-006 through A-009 point to their dedicated S2PMT03 runtime-lock, state-history, state-consistency, and optimistic-fencing phase records/manifests instead of the older aggregate `S2PMT03_LEASE_FENCING` evidence; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Refreshed `S2PMT07-P1-REVIEW-RECEIPT-REFRESH` so 16 P1 independent-review receipt rows point to their dedicated current phase records and run manifests, including corrected B-013 routing to `S2PMT05-RESULT-VALIDITY-B013`; this is evidence routing only and leaves independent signoff, final command execution, P0/P1 closure, S2PLT04, final bundle, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Synced `S2PMT07-FINAL-COMMAND-BLOCKER-SYNC` so the S2PMT07 fail-closed machine report, phase record, manifest, semantic parameters, and regression tests explicitly include `independent_final_command_execution_missing`; this aligns machine blockers with the V7.2/formula contract while keeping independent signoff, P0/P1 closure, S2PLT04, final bundle creation, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Refreshed `S2PMT07-P0-REVIEW-RECEIPT-REFRESH-B007-B008` so the P0 independent-review receipt points B-007 and B-008 to their dedicated 20260627 phase records and run manifests instead of the older S2PMT05 stress-E2E summary; added a final-gate regression test while keeping independent signoff, P0/P1 closure, S2PLT04, SMTP, scheduler, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-SMTP-CRASH-WINDOW-B008` local SMTP accepted-before-local-commit crash-window evidence so S2PMT05 now requires outbox claim before SMTP acceptance, explicit `ACCEPTED_PENDING_COMMIT`, stable idempotent `message_id`, blocked resend without durable provider accept ref, local finalization with `smtp-accept://...` provider ref, and no real SMTP side effects while keeping SMTP production enablement, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-DUPLICATE-TRIGGER-B007` local duplicate-trigger race evidence so S2PMT05 now requires github_schedule/local_launchd/manual_retry/restart_catchup actor coverage, M1-M4 x 100 repeated trigger attempts, `mail_key`/`lease_owner`/`fencing_token` receipts, exactly one active revision per product, reason-coded `MAIL_KEY_ALREADY_CLAIMED` blocked attempts, and no scheduler side effects while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-TIME-POLICY-B010` local structured time-policy evidence so S2PMT05 now requires Australia/Sydney 05:00 schedule, 3600-second misfire grace, one-cycle catch-up bound, DST fold/gap cases, 8h sleep recovery, NTP backward/forward clock-jump cases, local business-date cycle IDs plus UTC watermarks, and no duplicate M4 watermark while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-E2E-B012` local 35-day E2E audit-bundle evidence so S2PMT05 now requires daily 3+1, weekly, monthly, review, action, and ROI count conservation, section artifacts, artifact index, link graph, deterministic bundle hash, and reachable review/action/ROI links while keeping real 35-day production replay, SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-FAULT-INJECTION-B009` local systematic fault-injection evidence so S2PMT05 now requires ENOSPC, read-only target, SQLITE_BUSY, corrupt JSON cache, corrupt PDF artifact, corrupt backup manifest, backup path collision, explicit recovery states, no partial artifact commits, durable evidence preservation, and fail-closed recovery actions while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-CAPACITY-BASELINE-B006` local formal capacity baseline evidence so S2PMT05 now requires load/stress/spike/soak rows, 1x/2x/5x multipliers, throughput/latency/queue/memory/disk/error metrics, bounded recoverable queue age, accelerated local 24h soak, and rebuildable-only spike shedding while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-BACKPRESSURE-B014` local backpressure priority evidence so S2PMT05 now requires 2x/5x peak profiles, high-priority SLO protection, explicit low-priority delay/drop reason codes, durable evidence preservation, and rebuildable-only shedding while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT05-RESULT-VALIDITY-B013` local result-validity evidence so S2PMT05 now requires semantic alignment, Claim Ledger references, evidence references, mechanism/action specificity, non-template variance, and unsupported P0 negative-control blocking while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added `S2PMT04-CACHE-LOW-DISK-B005` local cache low-disk degradation evidence so low disk pressure blocks new downloads and rebuildable cache writes, preserves durable evidence, keeps cleanup dry-run, and avoids queue/delete side effects while keeping SMTP, scheduler installation, Release, public schema, DB migration, production queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance unchanged.
- Added a local runner GitHub user-center sync gate so daily pass and real SMTP attempts require the shallow `用户中心/复习行动与收益.md` learning snapshot to be updated from S2PJT02/S2PJT03 reports; missing reports, failed sync, or remaining `待今日运行快照写入` fields now block readiness while SMTP enablement, scheduler, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Added the root governance rule that development runs must not leave open PRs as delivery state; created or inherited PRs must be merged or closed before closeout, and any still-needed stale/conflicting/draft work must be re-cut from current `main` as a clean branch rather than left open.
- Added `S2PLT04` integration candidate precheck so current Stage 2 evidence can be summarized into a blocked no-production report covering S2PLT01 review evidence, missing S2PLT02/S2PLT03 completion, local state/content evidence, inherited P0/P1 blockers, missing final bundle, and blocked S2PMT07; S2PLT04 completion, `S2_INTEGRATION_CANDIDATE_READY`, SMTP, scheduler, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Added `S2PLT01-INDEPENDENT-REPLAY-REVIEW` so the S2PLT01 replay payload execution package can be independently reviewed with reviewer identity, reviewer role, independence flag, CI/evidence refs, execution-report validation, retained inherited P0/P1 blockers, and deterministic `review_hash`; S2PLT01 acceptance, production replay, S2PMT07 final signoff, SMTP, scheduler, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Added `S2PLT01-REPLAY-PAYLOAD-EXECUTION` so explicit 30-day replay records, 120 M1-M4 `EMAIL_LEARNING_V1` no-send mail previews, and D1-D4 terminal source states can be packaged into a validated no-production replay payload execution report with entry precheck binding and deterministic `execution_hash`; S2PLT01 acceptance, production replay, SMTP, scheduler, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Hardened the `S2PMT04` / Stage 1 scheduler dry-run macOS launchd template for inherited A-013 by replacing handwritten plist XML and `/bin/sh -lc` command strings with `plistlib` generated structured `ProgramArguments`, `WorkingDirectory`, and `EnvironmentVariables`; real scheduler install, launchd bootstrap, SMTP, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Added `S2PLT01-REPLAY-EVIDENCE-GATE` so the S2PLT01 precheck can validate provided 30-day replay records, 120 M1-M4 `EMAIL_LEARNING_V1` no-send mail previews, D1-D4 terminal source states, zero leakage/P0P1 counters, and evidence refs without executing replay or claiming S2PLT01 acceptance; inherited P0/P1, S2PLT04, S2PMT07, SMTP, scheduler, Release, public schema, DB migration, production queue, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Hardened the `S2PMT02` / Stage 1 B1 report artifact publishing path for inherited A-010 by validating the package before any formal artifact write, staging all files under `.b1_staging`, publishing a complete package directory only after staged byte-hash verification, and cleaning staging on publish failure; production email, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
- Hardened the `S2PMT02` / Stage 1 B1 report artifact manifest for inherited A-011 by making `artifact_files.sha256` equal the written file byte SHA-256 while preserving the prior canonical content hash as `content_hash`; production email, SMTP, scheduler, Release, public schema, DB migration, queue mutation, source adapters, ranking, CURRENT, V7.1/V7.2 contracts, inherited P0/P1 closure, DAILY_OPERATION, and integrated production acceptance remain unchanged.
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
- Added S2PLT01 replay payload contract evidence without replay execution or production side effects.
- Added S2PMT03 A-016 lesson revision identity hardening with stable `lesson_key`, immutable content/evidence-sensitive `lesson_revision_id`, and no production side effects.
- Added S2PMT03 B-003 local watchdog stale-lock recovery gate that blocks live-owner takeover and only permits expired dead-owner recovery through row-version and fencing-token claim semantics, with no production side effects.
- Added S2PMT03 B-011 local M4 watermark hardening for M2 failure, M3 timeout, late terminal data, rerun idempotence, and cross-cycle leakage without production side effects.
- Added S2PMT04 B-004 local startup convergence gate for persistent-state count conservation without production side effects.
- Added S2PMT04 B-015 local transaction completion gate for shutdown save/cleanup recovery receipts without production side effects.
- Added S2PLT02 fail-closed live 2-day readiness precheck for the 2 natural day / 8 M1-M4 real-email requirement without starting live operation, SMTP, scheduler, Release, schema, DB, queue, source adapter, ranking, CURRENT, or V7 contract side effects.
- Added owner-center entry governance rule requiring shallow GitHub-rendered `用户中心` pages as the primary owner-readable surface, with local `.adp` runtime files treated as evidence only.
- Added shallow GitHub user-center total candidate pool disclosure: 299 total candidates, 30 report/mail-preview index entries, 269 pending candidates, public ranking formula/weights, and regression tests; no production side effects.
- Added S2PMT01 A-020 local supply-chain machine gate for workflow permissions, GitHub Action references, and high/critical vulnerability exception approvals without production side effects.
- Added S2PMT01/S2PMT07 A-020 SBOM and CI enforcement refresh: deterministic local SBOM summary, project-governance A-020 security-boundary test gate, and finding-level technical review candidate evidence without closing P1/P0 or enabling production.
- Added S2PMT06 C-005 dedicated recoverable-error evidence and S2PMT07 P1 receipt refresh without closing P1 or enabling production side effects.
- Added S2PMT06 C-006/C-007 dedicated safe-config and append-only audit evidence with S2PMT07 P1 receipt refresh, without closing P1 or enabling production side effects.
- Recorded `S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE` to aggregate all eight inherited P0 finding-level technical review receipts while preserving P0=8/P1=37, final S2PMT07 blockers, and all no-production boundaries.
- Recorded `S2PMT07-P1-A006-A009-TECHNICAL-REVIEW` to mark A-006/A-007/A-008/A-009 as finding-level technical closure candidates while preserving P0=8/P1=37 and all no-production boundaries.
- Added `S2PMT07-FINAL-ACCEPTANCE-BUNDLE-READINESS` as a fail-closed final acceptance bundle readiness sub-gate that lists required final bundle evidence while preserving P0=8/P1=37, no final bundle, no production side effects, and no integrated production acceptance.
- Added S2PLT03 local no-production resilience drill bundle evidence while preserving S2PLT02/P0/P1/S2PLT04/S2PMT07 blockers and all production stop gates.
- Added S2PMT07 S2PLT04 completion report validator for future `FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json` payloads while preserving missing-report, missing-final-bundle, P0=8/P1=37, no-production, and no-integrated-acceptance blockers.
- Added S2PMT07 independent final reviewer assignment artifact validator for future `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` payloads while preserving missing-artifact, missing-reviewer, P0=8/P1=37, no-production, and no-integrated-acceptance blockers.
- Added local daily resend recovery support for `--daily-input-report`, allowing M1-M4 catch-up to reuse an existing same-day `adp-daily-input-report.json` without live arXiv fetch, with date-mismatch blocking and no production acceptance claim.
- Added S2PMT07 directory-level final bundle artifact validation while preserving missing-final-bundle, P0=8/P1=37, no-production, and no-integrated-acceptance blockers.
- Added S2PLT02 partial real delivery evidence binding for the recorded 2026-06-28 M1-M4 resend: one observed real natural day and four observed emails now feed the two-day precheck, while S2PLT02 acceptance and production gates remain blocked.
- Added S2PMT07 independent final reviewer assignment owner packet while preserving missing assignment artifact, P0=8/P1=37, no-production, and no-integrated-acceptance blockers.
- Added S2PMT07 final bundle committed artifact consumption so readiness consumes committed final-bundle artifacts through nested validators while preserving missing-final-bundle, P0=8/P1=37, no-production, and no-integrated-acceptance blockers.
- Added S2PLT02 real-proof capture authorization artifact gate and owner packet validation while preserving missing-authorization, no SMTP/scheduler, no Release/restore, no CURRENT/V7 change, and no integrated production acceptance blockers.
- Fixed S2PMT07 final bundle readiness to consume the committed valid P0/P1 zero-proof artifact in embedded zero-proof readiness, removing stale zero-proof missing/open blockers while keeping S2PLT02, S2PLT04, final bundle, SMTP/scheduler/Release/restore, CURRENT/V7, and integrated production acceptance blocked.
- Fixed S2PMT07 final bundle prerequisite plan to stop repeating inherited P0/P1 blockers after committed zero-proof artifact validation passes, while keeping S2PLT04, final command execution, handoff, signoff, manifest, and all production acceptance gates blocked.
- Fixed S2PMT07 S2PLT04 completion evidence audit refs to remove a nonexistent S2PLT02 manifest, list only existing S2PLT02 nonterminal refs, and expose the blocked S2PLT02 real-proof capture authorization state without enabling production.

- Record S2PLT02 terminal capture window audit: live authorization is valid, but current 2026-06-29/2026-06-30 dry-run evidence and disabled launchd state do not satisfy terminal delivery proof.
