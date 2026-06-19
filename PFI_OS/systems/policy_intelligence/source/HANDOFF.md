# Current Goal

Build a twice-daily policy intelligence pipeline that generates concise, business-grade single-file PDF policy research reports and operations dashboards.

# Current State

- Main operations dashboard now keeps only core metrics, quality gates, next actions, pending queue, external-reference gaps, and coverage links.
- Formal report body now uses `研究质量与交付状态` instead of embedding run-history, crawl-funnel, timeline, or benchmark detail.
- Detailed run, timeline, benchmark, parser, and coverage information remains in sidecar dashboards.
- Latest generated report: `reports/20260605_农村集体土地留用地高效开发利用意见_研究报告_4.pdf`.
- Latest run id: `2026060504`; status completed and quality gate passed with effective external references `5/5`, platforms `3/2`, PDF 18 pages and business-value density 100%.
- Authorized platform collection now has a conservative `authorized_public_search` bridge for Douyin, Kuaishou, Weibo, Zhihu, WeChat and Xiaohongshu: if a local cookie file is available, it can request the configured search page, parse public result links, extract accessible article text, and audit login/CAPTCHA/access-control blockers without storing secrets.
- Automation readiness now includes a runtime policy check and panel: source/page/link limits, interpretation-document limit, request timeout, retry count, request delay, and maximum running minutes.
- Automation readiness now also checks scheduler persistence evidence and latest successful run freshness. It can read a non-secret `data/automation/scheduler.json` or `--scheduler-file`; missing scheduler evidence is a warning because target times do not prove launchd/cron/external automation is installed.
- Added `automation-scheduler-plan` for macOS launchd planning. It generates a reviewable plist draft, scheduler manifest example, JSON plan and HTML dashboard under `reports/`, but does not install launchd and does not create `data/automation/scheduler.json`.
- Attachment parsing now has stronger built-in OOXML coverage: DOCX body/header/footer/comments, XLSX workbook sheet names plus cell values, and PPTX slide text extraction with slide sequence markers.
- Added `platform_text_parser` for local video/interaction text normalization: Bilibili subtitle JSON, SRT, WebVTT, comment reply lists and danmaku XML now produce compact report-ready excerpts with auditable empty/parse-failed states. Bilibili enrichment helpers now use this shared parser.
- Added `platform_page_parser` for authorized/public result-page metadata extraction. It reads already-fetched HTML only and extracts title, author, author URL, published time, view/read/play counts and engagement counts from meta tags, JSON-LD/OpenGraph and visible count text. `authorized_public_search` now writes those fields into interpretation items.
- Chinese public search parsing is stronger: Baidu/Sogou/360 result anchors now prefer real external `data-url`-style attributes, decode common redirect query keys such as `url`, `u`, `target`, `to` and `link`, and keep search-engine self pages out of valid candidates.
- `search-validate --offline` now includes a Baidu/Sogou/360 public HTML parser self-test in `reports/search_validation_dashboard.html`; current parser readiness is `3/3`, while API credentials remain missing.
- Xiaohongshu now uses `authorized_public_search` instead of landing-only config, so a local auth file can activate public result parsing and page metadata extraction.
- Toutiao now has dual channels: `public_search_html` for unauthenticated public coverage and `authorized_public_search` for user-authorized article/author/interaction enrichment. Parser validation now treats Toutiao full-web enrichment as blocked until local auth is provided.
- Platform coverage now maps `authorized_public_search` to concrete bridge capabilities: authorized public search, public article extraction, author profile, interaction metrics and failure audit. Authorized-only platforms remain blocked without auth; Toutiao remains partial because it also has a public search channel.
- Added `platform-auth-bulk-import` for multi-platform cookie intake. If the user exports local cookie text files into one directory named as `<platform>_cookie.txt` (for example `bilibili_cookie.txt`, `zhihu_cookie.txt`, `weibo_cookie.txt`, `toutiao_cookie.txt`), one command can copy them into the private cookie store, update `policy-platform-auth.json`, set private permissions, and output only sanitized status.
- `platform_auth_intake` and `setup_wizard` now include the bulk import command as the recommended lower-friction path while preserving single-platform import.
- Platform auth intake now also supports `platform-auth-bundle-import`: one local `platform_auth_bundle.json` can map platforms to exported cookie file paths. The command copies cookies into the private cookie store, updates `policy-platform-auth.json`, preserves private permissions, and prints only sanitized platform status.
- Search API intake now also has a lower-friction bulk import path: `search-secret-bulk-import` accepts one local `search_api_bundle.json` with SerpAPI/Bing/Google CSE fields, writes only to the private search secret file, and returns sanitized provider status without printing keys, bundle contents or full sensitive paths.
- Automation readiness now parses launchd `.plist` scheduler evidence structurally with `plistlib`: it verifies `ProgramArguments` includes `run_policy_report.sh` and `StartCalendarInterval` contains the expected schedule times. A wrong run time or planned-but-not-installed artifact no longer counts as valid scheduler persistence.
- Attachment parser dashboard now includes local runtime dependency readiness. It checks Python modules (`pypdf`, `fitz`/PyMuPDF, `PIL`, `pytesseract`), system `tesseract`, and external-service configuration entry points (`TIKA_SERVER_URL`, `GROBID_SERVER_URL`) without making network calls or printing environment values.
- Apache Tika bridge is now an executable optional path rather than a pure plan: DOC/XLS/PPT/RTF/ODT/ODS/EPUB attachments route to `PUT /tika` when `TIKA_SERVER_URL` is configured, and otherwise record `needs_dependency:tika_server:<format>` without network calls or fake extraction success.
- GROBID research PDF bridge is now an executable optional path: when `GROBID_SERVER_URL` is configured, PDFs first try `POST /api/processFulltextDocument`, parse TEI title/author/section/reference text, and fall back to normal PDF/OCR parsing with a `*_after_grobid_failure:*` status when GROBID fails.
- Added `access-readiness` as the consolidated go/no-go dashboard for near-full-web intake. It summarizes search API, Bilibili P0 auth, Baidu/Sogou/360 public Chinese entries, WeChat/Zhihu/Weibo P1 auth, short-video/social P2 auth, and parser prerequisites with sanitized commands and compliance boundaries. The latest real run is still `blocked`: search API ready `0/3`, platform auth available `0/8`, Bilibili missing, Chinese public entries `3/3`, pending gaps `143`.
- Platform auth intake now supports `platform-auth-session-import` for a local Chrome/Playwright session file or Chrome profile directory. Session/profile references are tracked as `session-only`: useful for authorization handoff and online validation planning, but not counted as direct collector-ready cookie input. `access-readiness` now shows Bilibili `ready`, `session_only`, or `missing` and surfaces `collector_ready=false` when a session reference exists without a cookie file.
- `setup-config` now also prepares P0 bulk-intake examples: `search_api_bundle.example.json` and `platform_auth_bundle.example.json` under the secure directory. They contain only empty key fields, placeholder values, and local cookie/session path hints, and are meant to be edited locally before running `search-secret-bulk-import`, `platform-auth-bundle-import`, or `platform-auth-session-import`.

# Decisions

- Formal PDF/HTML reports prioritize high-value research content and exclude recent run logs.
- Dashboard sidecars remain the place for operations, benchmark, and audit details.
- Abnormal script exits now record the active step as failed and attempt safe stale-lock cleanup.
- Historical public-reference reuse is allowed only for the same policy document, only after a previous successful public article excerpt, and defaults to one deduped reused reference per run.
- `authorized_public_search` is a bridge, not full platform mastery: platform-specific video detail, comments, danmaku, author profile and interaction metrics remain separate parser work items.

# Files Changed

- `src/source_registry/reporting.py`
- `src/source_registry/report_artifacts.py`
- `src/source_registry/interpretation.py`
- `src/source_registry/ops_dashboard.py`
- `src/source_registry/automation_readiness.py`
- `src/source_registry/automation_scheduler.py`
- `src/source_registry/access_readiness.py`
- `src/source_registry/attachment_parser.py`
- `src/source_registry/platform_auth.py`
- `src/source_registry/platform_auth_import.py`
- `src/source_registry/platform_auth_intake.py`
- `src/source_registry/platform_auth_validation.py`
- `src/source_registry/platform_text_parser.py`
- `src/source_registry/platform_page_parser.py`
- `src/source_registry/interpretation.py`
- `src/source_registry/cli.py`
- `src/source_registry/config_setup.py`
- `config/interpretation_sources.json`
- `config/platform_parsers.json`
- `config/attachment_parsers.json`
- `scripts/run_policy_report.sh`
- `tests/test_pipeline.py`
- `tests/test_report_artifacts.py`
- `tests/test_monitor.py`
- `tests/test_public_site_search.py`
- `tests/test_search_article_enrichment.py`
- `tests/test_ops_dashboard.py`
- `tests/test_config_setup.py`
- `tests/test_platform_auth.py`
- `tests/test_automation_readiness.py`
- `tests/test_automation_scheduler.py`
- `tests/test_access_readiness.py`
- `tests/test_attachment_parser.py`
- `tests/test_platform_auth_import.py`
- `tests/test_platform_auth_intake.py`
- `tests/test_platform_auth_validation.py`
- `tests/test_platform_text_parser.py`
- `tests/test_platform_page_parser.py`
- `README.md`
- `docs/automation.md`
- `docs/full_web_coverage_requirements.md`
- `docs/schema.md`

# Verification

- `PYTHONPATH=src python3 -m unittest discover tests`: 198 tests passed.
- `PYTHONPATH=src python3 -m unittest discover tests`: 200 tests passed.
- `PYTHONPATH=src python3 -m unittest tests.test_public_site_search tests.test_search_validation`: 19 tests passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-validate --offline --json`: refreshed `reports/search_validation_dashboard.html`; API configured `0/3`, public entrance parser readiness `3/3`.
- `PYTHONPATH=src python3 -m unittest tests.test_interpretation_sources_config tests.test_platform_coverage tests.test_platform_auth tests.test_platform_parser_validation`: 16 tests passed.
- `PYTHONPATH=src python3 -m unittest discover tests`: 203 tests passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-coverage --content-db data/policy_documents.sqlite --json`: refreshed `reports/platform_coverage_dashboard.html`; total 21, partial 7, lead_only 5, blocked 9, search API ready 0, platform auth available 0.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-parser-validate --json`: refreshed `reports/platform_parser_validation_dashboard.html`; parser count 10, current partial 2, missing search key 1, missing platform auth 7.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate --json`: refreshed `reports/platform_auth_validation_dashboard.html`; 8/8 platform auth missing.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite setup-wizard --json`: refreshed `reports/setup_wizard_dashboard.html`; platform coverage total 21, blocked 9, pending gaps 142.
- `bash -n scripts/run_policy_report.sh`: passed.
- `PYTHONPATH=src python3 -m unittest tests.test_platform_auth_import tests.test_platform_auth_intake tests.test_setup_wizard`: 16 tests passed.
- `PYTHONPATH=src python3 -m unittest discover tests`: 206 tests passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-intake --json`: refreshed `reports/platform_auth_intake_dashboard.html`; bulk import command present; 8 configured, 0 available, 8 missing files.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite setup-wizard --json`: refreshed `reports/setup_wizard_dashboard.html`; command matrix includes `platform-auth-bulk-import`.
- `PYTHONPATH=src python3 -m unittest tests.test_automation_readiness tests.test_automation_scheduler`: 18 tests passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite automation-scheduler-plan --workspace . --output-dir reports --schedule-time 09:00 --schedule-time 21:00 --json`: refreshed scheduler plan artifacts; status remains `planned_not_installed`.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite automation-readiness --content-db data/policy_documents.sqlite --data-dir data --schedule-time 09:00 --schedule-time 21:00 --json`: refreshed `reports/automation_readiness_dashboard.html`; overall blocked by P0 credentials, scheduler persistence still warn because no installed scheduler evidence exists.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite automation-readiness --content-db data/policy_documents.sqlite --data-dir data --schedule-time 09:00 --schedule-time 21:00 --scheduler-file reports/com.source-registry.policy-report.plist --output /private/tmp/scheduler_plist_readiness.html --json`: structural plist validation passed with launchd evidence and `09:00/21:00`.
- `PYTHONPATH=src python3 -m unittest discover tests`: 208 tests passed.
- `PYTHONPATH=src python3 -m unittest tests.test_attachment_parser tests.test_attachment_parser_registry`: 12 tests passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite attachment-parsers --json`: refreshed `reports/attachment_parser_dashboard.html`; parser count 8, ready 4, partial 2, planned 2; dependency ready 3, missing 4, configured external services 0. Missing: `pytesseract`, system `tesseract`, `TIKA_SERVER_URL`, `GROBID_SERVER_URL`.
- `PYTHONPATH=src python3 -m unittest discover tests`: 210 tests passed.
- `PYTHONPATH=src python3 -m unittest tests.test_attachment_parser tests.test_attachment_parser_registry`: 14 tests passed.
- `python3 -m compileall -q src tests`: passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite attachment-parsers --json`: refreshed `reports/attachment_parser_dashboard.html`; parser count 8, ready 4, partial 3, planned 1; dependency ready 3, missing 4, configured external services 0. Tika bridge is partial because `TIKA_SERVER_URL` is not configured.
- `PYTHONPATH=src python3 -m unittest discover tests`: 212 tests passed.
- `bash -n scripts/run_policy_report.sh`: passed.
- `PYTHONPATH=src python3 -m unittest tests.test_attachment_parser tests.test_attachment_parser_registry`: 16 tests passed.
- `python3 -m compileall -q src tests`: passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite attachment-parsers --json`: refreshed `reports/attachment_parser_dashboard.html`; parser count 8, ready 4, partial 4, planned 0; dependency ready 3, missing 4, configured external services 0. Tika and GROBID are partial because local service URLs are not configured.
- `PYTHONPATH=src python3 -m unittest discover tests`: 214 tests passed.
- `bash -n scripts/run_policy_report.sh`: passed.
- `PYTHONPATH=src python3 -m unittest tests.test_search_secret_import tests.test_search_secret_intake tests.test_setup_wizard`: 16 tests passed.
- `python3 -m compileall -q src tests`: passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-intake --json`: refreshed `reports/search_secret_intake_dashboard.html`; search API ready `0/3`, bulk import command present, no key values printed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite setup-wizard --json`: refreshed `reports/setup_wizard_dashboard.html`; search API ready `0/3`, platform auth available `0/8`, pending gaps `143`, command matrix includes `search-secret-bulk-import`.
- `bash -n scripts/run_policy_report.sh`: passed.
- `PYTHONPATH=src python3 -m unittest discover tests`: 216 tests passed.
- `PYTHONPATH=src python3 -m unittest tests.test_platform_auth_import tests.test_platform_auth_intake tests.test_setup_wizard`: 18 tests passed.
- `python3 -m compileall -q src tests`: passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-intake --json`: refreshed `reports/platform_auth_intake_dashboard.html`; platform auth configured `8/8`, available `0/8`, missing files `8/8`, `platform-auth-bundle-import` present.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite setup-wizard --json`: refreshed `reports/setup_wizard_dashboard.html`; command matrix includes `platform-auth-bundle-import`.
- `PYTHONPATH=src python3 -m unittest discover tests`: 218 tests passed.
- `bash -n scripts/run_policy_report.sh`: passed.
- `PYTHONPATH=src python3 -m unittest tests.test_access_readiness tests.test_setup_wizard tests.test_ops_dashboard`: 13 tests passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite access-readiness --content-db data/policy_documents.sqlite --json`: refreshed `reports/access_readiness_dashboard.html`; status `blocked`, P0 `p0_blocked`, search ready `0/3`, platform available `0/8`, Bilibili missing, Chinese public search entries `3/3`.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite setup-wizard --content-db data/policy_documents.sqlite --json`: refreshed `reports/setup_wizard_dashboard.html`; command matrix includes `access-readiness`, search API ready `0/3`, platform auth available `0/8`, pending gaps `143`.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite ops-dashboard --content-db data/policy_documents.sqlite --json`: refreshed `reports/policy_ops_dashboard.html`; pending queue `14`, pending gaps `143`, quality gate not met.
- `python3 -m compileall -q src tests`: passed.
- `PYTHONPATH=src python3 -m unittest discover tests`: 223 tests passed.
- `bash -n scripts/run_policy_report.sh`: passed.
- `PYTHONPATH=src python3 -m unittest tests.test_access_readiness tests.test_platform_auth tests.test_platform_auth_import tests.test_platform_auth_intake tests.test_setup_wizard`: 33 tests passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-intake --json`: refreshed `reports/platform_auth_intake_dashboard.html`; `platform-auth-session-import` present, configured `8/8`, available `0/8`, collector-ready `0/8`, session-only `0/8`, missing files `8/8`.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite setup-wizard --content-db data/policy_documents.sqlite --json`: refreshed `reports/setup_wizard_dashboard.html`; command matrix includes `platform-auth-session-import`, search API ready `0/3`, platform auth available `0/8`, pending gaps `143`.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite access-readiness --content-db data/policy_documents.sqlite --json`: refreshed `reports/access_readiness_dashboard.html`; status `blocked`, P0 `p0_blocked`, search ready `0/3`, platform available `0/8`, Bilibili missing, Chinese public entries `3/3`, Bilibili evidence `collector_ready=false`.
- `PYTHONPATH=src python3 -m unittest tests.test_access_readiness tests.test_platform_auth tests.test_platform_auth_import tests.test_platform_auth_intake tests.test_platform_auth_validation tests.test_setup_wizard`: 44 tests passed.
- `python3 -m compileall -q src tests`: passed.
- `PYTHONPATH=src python3 -m unittest discover tests`: 230 tests passed.
- `bash -n scripts/run_policy_report.sh`: passed.
- `PYTHONPATH=src python3 -m unittest tests.test_config_setup tests.test_setup_wizard tests.test_search_secret_import tests.test_platform_auth_import`: 28 tests passed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite setup-config --dry-run --json`: verified default P0 bundle example paths; existing main secret/auth files would be skipped, bundle example files would be created; no template bodies or secret values printed.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite setup-wizard --content-db data/policy_documents.sqlite --json`: refreshed `reports/setup_wizard_dashboard.html`; setup paths now include `~/.policy-intelligence/search_api_bundle.example.json` and `~/.policy-intelligence/platform_auth_bundle.example.json`; P0 still blocked.
- `PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite access-readiness --content-db data/policy_documents.sqlite --json`: refreshed `reports/access_readiness_dashboard.html`; status remains `blocked`, search API ready `0/3`, platform auth available `0/8`, Bilibili missing, Chinese public entries `3/3`.
- `python3 -m compileall -q src tests`: passed.
- `PYTHONPATH=src python3 -m unittest discover tests`: 230 tests passed.
- `bash -n scripts/run_policy_report.sh`: passed.
- `PYTHONPATH=src python3 -m unittest tests.test_platform_page_parser tests.test_platform_auth tests.test_platform_parser_samples`: 10 tests passed.
- `PYTHONPATH=src python3 -m unittest tests.test_platform_text_parser tests.test_bilibili_enrichment tests.test_platform_parser_samples`: 12 tests passed.
- `PYTHONPATH=src python3 -m unittest tests.test_attachment_parser tests.test_attachment_parser_registry`: 10 tests passed.
- `PYTHONPATH=src python3 -m unittest tests.test_automation_scheduler tests.test_automation_readiness`: 16 tests passed.
- `PYTHONPATH=src python3 -m unittest tests.test_automation_readiness`: 13 tests passed.
- `bash -n scripts/run_policy_report.sh`: passed.
- `python3 -m compileall -q src tests`: passed.
- Generated scheduler plan artifacts: `reports/com.source-registry.policy-report.plist`, `reports/scheduler_manifest.example.json`, `reports/automation_scheduler_plan.json`, `reports/automation_scheduler_plan.html`.
- Scheduler plan dashboard and JSON explicitly show `planned_not_installed`; no `data/automation/scheduler.json` was created by the planner.
- Refreshed dashboards: `reports/platform_parser_dashboard.html`, `reports/platform_parser_validation_dashboard.html`, `reports/policy_ops_dashboard.html`, `reports/setup_wizard_dashboard.html`.
- Refreshed `reports/attachment_parser_dashboard.html`; parser registry now shows 8 parsers, 4 ready, 2 partial, 2 planned, with PPTX OOXML ready.
- Refreshed `reports/platform_parser_dashboard.html` and `reports/platform_parser_sample_dashboard.html`; sample dashboard shows Bilibili has video metadata/comment/danmaku/author/interaction samples but still lacks subtitle samples.
- Refreshed `reports/platform_parser_validation_dashboard.html`; platform auth remains missing for Douyin/Kuaishou/Weibo/Zhihu/WeChat/Xiaohongshu, and search key remains missing.
- Refreshed `reports/automation_readiness_dashboard.html`; runtime policy is pass with timeout 20s, retries 1, delay 0.20s, max runtime 180min; latest successful run freshness is pass; scheduler persistence is warn because no scheduler evidence file or known launchd plist was found.
- Latest report artifact check: 16/16 passed; PDF 18 pages; business value density 100.00%; reference section 0.28 estimated pages.
- `data/pipeline.lock`: absent.
- `pipeline_runs`: 60 completed, 13 failed, 0 running; no active source_registry pipeline detected.

# Open Issues

- Automation readiness remains blocked by P0 missing search API and local platform authorization: setup wizard shows search API ready `0/3`, platform auth available `0/8`.
- `access-readiness` confirms the same P0 blocker in one place: no real search API key, no usable Bilibili cookie/session file, and no usable P1/P2 platform auth yet.
- Search API import friction is reduced, but no real search API key is present yet; `reports/search_secret_intake_dashboard.html` still shows SerpAPI/Bing/Google CSE missing.
- P0 bundle examples now reduce input friction, but the real values/files still need to be supplied locally; example files alone do not make readiness pass.
- Runtime policy itself is not blocking; the current blocker is still P0 credentials.
- Scheduler persistence is not proven yet. Add a real launchd/cron/external automation and record it in `data/automation/scheduler.json` or pass `--scheduler-file`; do not create the evidence file until the scheduler is actually installed.
- Authorized bridge behavior is unit-tested with mocked pages; real platform output still requires user-provided local cookie files and online validation.
- Platform auth import friction is reduced through directory and JSON-bundle import, but no real platform cookie/session file is present yet; `reports/platform_auth_intake_dashboard.html` still shows `available 0/8`.
- Chrome/session reference import is now supported, but real collector-ready status still requires cookie files or future platform-specific session validators. Do not count `session-only` as a report reference source.
- Tika bridge behavior is unit-tested with a mocked local service; real legacy Office extraction still requires a configured local/controlled Apache Tika server via `TIKA_SERVER_URL`.
- GROBID bridge behavior is unit-tested with a mocked local service; real research PDF structure extraction still requires a configured local/controlled GROBID server via `GROBID_SERVER_URL`.
- In-app browser verification was unavailable because Browser plugin returned `iab` unavailable; local HTML checks passed.

# Next Steps

- Provide at least one search API key file and Bilibili local authorization file path.
- Add P1 local cookie files for WeChat/Zhihu/Weibo to activate `authorized_public_search`.
- Re-run `credential-doctor`, `platform-auth-validate --online`, `search-validate`, `platform-parser-validate`, then `bash scripts/run_policy_report.sh`.

# System Coordination ACK 2026-06-05

- Government policy system remains scoped to policy original-source crawling, policy evidence chains, policy PDF reports, source/platform authority readiness, and platform authorization readiness. It should not own industry daily reports, PFIOS backtests, or consumer-analysis workflows.
- Current P0 blocker remains unchanged: search API ready `0/3`, platform auth available `0/8`, Bilibili auth missing, and `access-readiness` status `blocked`.
- Sync interface to PFIOS/industry systems should be policy evidence only: `document_id`, policy title/date/source, `source_id`, authority tier/score snapshot, policy-industry tags, evidence URLs, external-reference quality status, and report artifact path. Downstream systems can consume this evidence but should not duplicate policy crawling.
- Pause low-value expansion until P0 inputs are supplied: more parser/UI/dashboard expansion, new platform-specific enrichers, and scheduler installation. Highest next priority is making P0 access-readiness usable with at least one search API key and Bilibili local auth, then validating online.

# Chrome/Bilibili Authorization ACK 2026-06-05

- User authorized local Chrome cookies/history inspection for Bilibili. Chrome Default profile was registered as Bilibili `session_only`; it proves local authorization exists but is not direct collector-ready cookie input.
- Added `chrome-bilibili-discovery` to inspect authorized local Chrome History/Cookies SQLite status, output sanitized Bilibili policy/industry candidate URLs, dedupe low-value entries, and avoid printing cookie names, cookie values, passwords, or full Chrome paths.
- Latest sanitized discovery dashboard: `reports/chrome_bilibili_discovery_dashboard.html`; History readable, Bilibili history count `200`, Bilibili cookie row count `40`, policy/industry candidate count `2`.
- Current P0 status: still blocked until at least one search API key is provided; Bilibili remains `session_only` unless a controlled local cookie export or session-based collector is implemented.
- Verification: `PYTHONPATH=src python3 -m unittest discover tests` passed `235` tests; `python3 -m compileall -q src tests` passed; `bash -n scripts/run_policy_report.sh` passed.

# Search API ACK 2026-06-05

- SerpAPI key was imported into the private local search secret file; key value is not stored in repo, reports, dashboards, or HANDOFF.
- `search-validate --allow-insecure-tls` passed for SerpAPI with sample domain `www.ndrc.gov.cn`; local Python TLS without the flag returned `URLError`, so production runs should keep the existing `ALLOW_INSECURE_TLS=1` path or fix the local trust store before removing it.
- `access-readiness` improved to `overall_status=partial`, `p0_status=p0_minimum_ready`, `search_ready=1`, `missing_search_key=0`; Bilibili is still `session_only`, and 7 P1/P2 platform auth files are still missing.
- `platform-parser-validate` now marks the search API article parser `current_ready` with ready provider `serpapi`.
- Third-party package decision: do not install `daman87/douyin-api` because it points to executable/zip artifacts with weak source and license clarity; do not add `bilibili-api-python` as a main dependency now because it is GPLv3, crawler-oriented, adds many dependencies, and current Bilibili public collector already covers the near-term need.
- Cleaned stale `data/pipeline.lock`, reconciled orphaned run `2026060512`, and marked stale latest automation step `ai_research_policy_20260605_122125/pipeline_run` as failed for auditability. Automation readiness remains `blocked` by latest failed automation record and `warn` on scheduler persistence/quality gate until a new successful run or scheduler evidence is recorded.
- Verification: focused search/access/platform tests passed; full `PYTHONPATH=src python3 -m unittest discover tests` passed `235` tests; `python3 -m compileall -q src tests` passed; `bash -n scripts/run_policy_report.sh` passed.

# Reference Quality ACK 2026-06-05

- Tightened effective-reference logic after a low-value Bilibili trading video was found in a prior successful private-fund report: short-term trading, exam/recruiting, game/mod and generic entertainment videos no longer count unless they carry strong policy/research context.
- Added agriculture/land/natural-resource subject terms so high-quality land policy articles such as耕地保护专项规划、永久基本农田、粮食安全、国土空间、自然资源 and集体土地 can count when relevant.
- Effective references are now deduped by normalized URL and title, preventing historical reuse and current search hits from occupying duplicate reference slots.
- Latest successful run: `2026060516`, report `reports/20260605_农村集体土地留用地高效开发利用意见_研究报告_5.pdf`; quality gates passed with effective references `7/5`, platforms `2/2`, PDF `19` pages, single document, 10 deep chapters, reference section about `0.35` pages, business-value density `100%`.
- Prior fixed report also passed after the same rules: `reports/20260605_广州首部区级耕地保护专项规划印发_研究报告_6.pdf`; effective references `7/5`, platforms `3/2`, PDF `13` pages.
- Automation readiness is now `attention`: 11 pass, 1 warning, 0 fail. Remaining warning is scheduler persistence evidence; no launchd/cron/external scheduler manifest is installed or recorded yet.
- Verification: `PYTHONPATH=src python3 -m unittest tests.test_search_article_enrichment tests.test_pipeline tests.test_quality_gates` passed 28 tests; `python3 -m compileall -q src tests` passed; `report-check` passed 16/16; `quality-gates` passed 7/7; explicit user-provided key-value scan returned no matches in repo/report/data outputs.

# Automation Scheduler ACK 2026-06-06

- Existing Codex app cron automation `automation` / `中国政策文件监测报告` was updated from `PAUSED` to `ACTIVE`.
- Schedule is now daily at `09:00` and `21:00` Australia/Sydney via RRULE `BYDAY=SU,MO,TU,WE,TH,FR,SA;BYHOUR=9,21;BYMINUTE=0`.
- Automation prompt now runs the exact command with private local config paths: `SEARCH_SECRETS_FILE=$HOME/.policy-intelligence/policy-search-secrets.json PLATFORM_AUTH_FILE=$HOME/.policy-intelligence/policy-platform-auth.json ALLOW_INSECURE_TLS=1 bash scripts/run_policy_report.sh`; no secret values are stored in repo or HANDOFF.
- Added non-secret scheduler evidence `data/automation/scheduler.json` with scheduler type `codex_app_cron`, automation id, entrypoint, schedule times, timezone, and workspace.
- `automation-readiness` is now `ready`: 12 pass, 0 warnings, 0 failures; scheduler persistence status is `pass`.
- Remaining full-web gaps are not scheduler-related: SerpAPI is ready but Bing/Google CSE are missing; Bilibili is session/profile available but not direct collector-cookie ready; Douyin/Kuaishou/Weibo/Zhihu/WeChat/Xiaohongshu/Toutiao local cookie/session files are still missing.

# Local App Entry ACK 2026-06-06

- Built macOS app entry `中国政策研究系统.app` with a custom `policy_research.icns` icon: document + shield + chart + soft sparkles, intended to match a professional but friendly local-system style.
- Installed app copies at `/Applications/中国政策研究系统.app`, `~/Desktop/中国政策研究系统.app`, and `~/Downloads/中国政策研究系统.app`.
- Launcher starts or reuses a local static dashboard server on `127.0.0.1:8787` and opens `reports/policy_ops_dashboard.html`; if HTTP startup fails, it falls back to the local file URL.
- Verification: `Info.plist` passed `plutil -lint`; launcher passed `bash -n`; `POLICY_APP_NO_OPEN=1 /Applications/中国政策研究系统.app/Contents/MacOS/launcher` returned `http://127.0.0.1:8787/reports/policy_ops_dashboard.html`; `curl` confirmed the dashboard HTML is reachable.

# Local App Click Fix ACK 2026-06-06

- User reported `中国政策研究系统.app` click had no visible response. Root cause was the hand-built shell `.app` being brittle under macOS LaunchServices/signing and Desktop/iCloud extended attributes.
- Rebuilt the entry as an AppleScript applet via `osacompile`; it opens `reports/policy_ops_dashboard.html` directly in Google Chrome and writes launch evidence to `data/app_launcher/policy_app_launcher.log`.
- `/Applications/中国政策研究系统.app` is now the signed canonical app. `~/Desktop/中国政策研究系统.app` and `~/Downloads/中国政策研究系统.app` are symlinks to the Applications app to avoid Desktop/FileProvider xattrs corrupting the app signature.
- Verification: canonical app passed `codesign --verify --deep --strict`; `osascript build/macos_app/policy_app_launcher.applescript` logged launch/open; `open -n /Applications/中国政策研究系统.app` logged launch/open; `open -n ~/Desktop/中国政策研究系统.app` logged launch/open.
