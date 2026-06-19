# Automation Readiness

The automation entrypoint is:

```bash
cd systems/policy_intelligence/source
bash scripts/run_policy_report.sh
```

It is designed to be safe for unattended runs:

- Initializes and refreshes the source registry before each run.
- Uses a lock file at `data/pipeline.lock` so overlapping runs fail instead of corrupting state.
- Runs `automation-lock-clean` before the main pipeline. This removes only stale lock files whose recorded PID is no longer running; active locks and invalid lock contents are not deleted. When no active lock remains, it also marks orphaned `pipeline_runs.status='running'` rows as failed so monitoring does not show dead runs as active.
- Writes run records to `data/policy_documents.sqlite`.
- Writes step-level automation state to `data/automation/latest_run.json`.
- Writes machine-readable health status to `data/monitor/latest_status.json`.
- Writes snapshots under `data/snapshots/YYYYMMDD/`.
- Writes Chinese PDF reports under `reports/`.
- Uses Chrome as the default PDF engine so Chinese text renders consistently with the HTML sidecar. Set `POLICY_REPORT_FORCE_REPORTLAB_PDF=1` only when Chrome is unavailable and ReportLab fallback is acceptable.
- Uses concise report filenames that include the single analysis target, for example `20260603_农村集体土地留用地高效开发利用意见_研究报告.pdf`.
- Keeps same-name HTML and Markdown sidecar files under `reports/` for layout review and content traceability.
- Creates a same-name `_dashboard.html` sidecar with collection funnel, quality gate, platform coverage, queue distribution, timeline, and reference-model capability matrix.
- Can generate `reports/policy_ops_dashboard.html`, a cross-run operations dashboard for run status, report queue, external-reference gaps, quality gates, platform gaps, industry backlog, and reference-model capability targets.
- Can generate `reports/automation_run_dashboard.html`, a step-level automation run dashboard for init, seed, pipeline, dashboard generation, credential validation, report self-check, quality gates, and benchmark generation.
- Can generate `reports/automation_readiness_dashboard.html`, a concise readiness dashboard for twice-daily unattended automation: entrypoint, data directory, lock state, automation step state, completed report artifact, pending queue, quality gate, P0 credentials, schedule cadence, and runtime policy.
- Can generate `reports/platform_coverage_dashboard.html`, a platform coverage matrix for search APIs, Chinese search entries, core social/video/article platforms, public media sites, implemented parsers, authorization blockers, and compliance boundaries.
- Can generate `reports/platform_parser_dashboard.html`, a platform parser capability dashboard for Bilibili, Douyin, Kuaishou, Weibo, Zhihu, WeChat public accounts, Xiaohongshu, Toutiao, search APIs and public media sites. It separates current parser delivery from planned authorized parsers for video metadata, subtitles, comments, danmaku, author profiles and interaction metrics.
- Can generate `reports/platform_parser_validation_dashboard.html`, a parser acceptance-prerequisite dashboard that combines parser registry rows, search API key readiness and platform authorization availability. It tells whether the next step is to provide a search key, provide platform auth, implement a parser, or run sample acceptance.
- Can generate `reports/platform_parser_sample_dashboard.html`, a read-only sample acceptance dashboard that verifies whether collected interpretation rows actually contain report-usable article, video, author, interaction and failure-audit evidence.
- Can generate `reports/crawl_policy_dashboard.html`, a crawl policy and compliance boundary dashboard for source-registry entries, including robots/nofollow policy, rate limits, retry policy, timeout, snapshot retention, blocked-page handling, and robots URL.
- Automation keeps `crawl-policy` offline by default. Operators can explicitly add `--check-robots` to fetch `robots.txt` and verify whether the configured User-Agent can crawl each source homepage; failed or disallowed checks become evidence, not bypass attempts.
- If local certificate-chain validation fails during robots checks, operators can add `--allow-insecure-tls` for that robots.txt read only. It does not override robots disallow rules, login walls, paid access, captcha pages, or platform restrictions.
- Can generate `reports/attachment_parser_dashboard.html`, an attachment parser capability dashboard for PDF, DOCX, XLSX, OCR, Apache Tika and GROBID readiness. It shows parser status, covered formats, business value, next action and acceptance checks without printing document text or secrets.
- Can generate `reports/setup_wizard_dashboard.html`, a local onboarding wizard that connects template generation, local key/auth editing, readiness checks, platform coverage, gap review, and final pipeline commands.
- Can generate `reports/credential_doctor_dashboard.html`, a local credential doctor that checks file existence, format, empty/placeholder fields, cookie/session file presence, staleness, and permissions without printing secret values.
- Can generate `reports/search_secret_intake_dashboard.html`, a search API intake checklist with provider readiness, missing fields, safe import commands and validation commands.
- Can generate `reports/platform_auth_validation_dashboard.html`, a platform authorization validation view. Automation uses offline mode; the operator can explicitly run online validation for supported platforms.
- Can generate `reports/search_validation_dashboard.html`, a search API validation view for SerpAPI, Bing and Google CSE. Automation uses offline mode to avoid accidental quota consumption; the operator can run online validation manually.
- Can generate `reports/benchmark_dashboard.html`, an open-source/commercial reference-model benchmark dashboard driven by `config/benchmark_models.json`, including crawler, document parsing, PDF structure extraction, change monitoring, GRC workflow, regulatory-intelligence patterns, and per-model acceptance checks.
- Can generate `reports/quality_gates_dashboard.html`, a declarative quality-gate dashboard driven by `rules/quality_gates.json`.
- Can generate `reports/report_artifact_check_dashboard.html`, a generated-report artifact self-check dashboard.
- Creates an external-reference gap queue for missing API keys, authorization gaps, parser gaps, blocked pages, short excerpts, and failed requests.
- Keeps source authority snapshots on every document record.
- Adds clickable table of contents.
- Generates exactly one single-file research report per automation run.
- Records `report_queue` and `report_timeline` in `data/policy_documents.sqlite`.
- Shows the pending report queue in the automation JSON result and in the PDF report.
- Shows operational visualizations in the PDF/HTML report and in the standalone dashboard.
- Collects external public research/interpretation material, including Bilibili public video-search metadata and public site-search article excerpts when available.
- Uses external interpretation material as analysis context before writing the report.
- Fetches selected official PDF/DOCX/XLSX/image attachments and tries to extract text before analysis, including optional OCR for scanned PDFs and image notices when local OCR dependencies are available.
- Uses deterministic Chinese `template` analysis by default, so the job does not require API credentials.

## Report Depth Requirements

Every automation run must evaluate the selected single-file policy report against this minimum depth standard:

- executive summary
- source authority tier
- policy attribute
- applicable industries and regions
- core clause breakdown
- industry-chain impact
- beneficiary company or security candidates
- business impact
- trading observation value
- risks and uncertainty
- relationship to historical policies or existing industry research
- task queue items that can enter the industry research or trading advice system

The automation output must explicitly report whether the generated report meets this depth standard. If it does not, the output must list the missing parts, keep the item in the pending queue when appropriate, or mark it for Codex deep interpretation or human review.

External interpretation material is supporting context only. Official text, attachments, issuing authority and source authority snapshots must remain the primary basis for conclusions.

## Runtime controls

Environment variables:

```bash
MAX_SOURCES=3
MAX_PAGES_PER_SOURCE=2
MAX_LINKS_PER_PAGE=20
MAX_ANALYZE=20
MAX_INTERPRETATION_DOCUMENTS=10
MIN_EXTERNAL_REFERENCES=5
MIN_EXTERNAL_PLATFORMS=2
QUALITY_RULES_FILE=rules/quality_gates.json
FETCH_INTERPRETATION_RESULTS=1
FETCH_SEARCH_RESULT_PAGES=1
INTERPRETATION_REQUEST_TIMEOUT=20
INTERPRETATION_REQUEST_RETRIES=1
INTERPRETATION_REQUEST_DELAY_SECONDS=0.2
BILIBILI_COOKIE_FILE=
SEARCH_SECRETS_FILE=
PLATFORM_AUTH_FILE=
MIN_AUTHORITY_SCORE=60
ANALYSIS_MODE=template
ALLOW_INSECURE_TLS=1
DOCUMENT_SINCE=2025-01-01
```

Set `ANALYSIS_MODE=codex` only after manually testing `codex exec` in this directory.

`ALLOW_INSECURE_TLS=1` is enabled by default because the local Python runtime currently fails certificate-chain validation for `www.gov.cn`. Set it to `0` after the Python trust store is fixed.

`FETCH_INTERPRETATION_RESULTS=1` is enabled by default in `scripts/run_policy_report.sh`. Bilibili public video search generally returns title, URL, UP 主、播放量、发布时间、简介、标签和相关度. The pipeline also attempts public video detail enrichment, public author profile enrichment, including visible account verification/follower/signature metadata, `cid`, interaction counters, public subtitle excerpts, public comment excerpts, and public danmaku excerpts when available. If Bilibili returns no public API result for a query, the pipeline preserves a clickable search entry instead of failing the run.

`FETCH_SEARCH_RESULT_PAGES=1` is enabled by default in `scripts/run_policy_report.sh`. When SerpAPI, Bing, or Google CSE returns public web results, the pipeline tries to fetch each public HTML page and extract a readable article/body excerpt. Login prompts, captcha pages, paywalls, and member-only pages are recorded as blocked and are not counted toward the 5-reference / 2-platform quality gate.

Public site-search collectors are enabled for directly readable sources such as gov.cn, people.cn, cctv.com, and yicai.com. They parse same-domain search result links and then run the same public article extractor. Search entries, blocked pages, JavaScript-only search pages, captcha pages, and paywalls remain leads and do not count toward the quality gate.

Chinese public-search collectors are enabled for Baidu, Sogou, 360 Search, and Toutiao search. They parse public result links and then fetch only publicly readable article pages. Search engine landing pages, image/search vertical pages, login/captcha/paywall pages, blocked pages, and unreadable pages remain leads and do not count. Countable references are attributed to the resolved article domain, not to the search engine itself.

Local related-document collectors are enabled for already indexed public documents. They search the content database for same-topic official Q&A, interpretations, plans, and related policies, then add them as context references without changing the single primary document studied by the report.

`INTERPRETATION_REQUEST_RETRIES` and `INTERPRETATION_REQUEST_DELAY_SECONDS` control reliability and politeness for public interpretation/search requests. The default automation delay is small enough for twice-daily runs but prevents bursty requests across many platforms.

`MIN_EXTERNAL_REFERENCES=5` and `MIN_EXTERNAL_PLATFORMS=2` are the report quality gates. Only usable references count toward this threshold: public video metadata, readable articles, public research/news results, or items with a usable excerpt. Pure search landings, login/captcha sources, and failed API fallbacks are kept as leads but do not count.

Run IDs use `YYYYMMDDNN`, where `NN` is the sequence number of reports generated that day. The report body target is at least 10 analysis pages. The external-reference section is compacted so the reference display targets one page without reducing the required count of references.

The current source pool includes Bilibili, Douyin, Kuaishou, Weibo, Zhihu, WeChat public-account search, Xiaohongshu, Toutiao, Baidu, Sogou, 360 Search, gov.cn, people.cn, xinhuanet.com, cctv.com, and yicai.com. Platforms that require login or captcha stay in the report as authorization leads until a safe logged-in session or approved API is connected.

The search API pool includes SerpAPI, Bing Web Search API, and Google Custom Search JSON API. Put keys in a local JSON or dotenv file outside the project and set `SEARCH_SECRETS_FILE=/secure/path/policy-search-secrets.json`. The supported secret names are `SERPAPI_API_KEY`, `BING_SEARCH_API_KEY`, `GOOGLE_SEARCH_API_KEY`, and `GOOGLE_CSE_ID`. The safer repeatable path is `search-secret-import`, which reads key values from local files or environment variables, writes the private JSON file with `0600` permissions, and prints only sanitized status. If keys are missing, the pipeline records the missing-key status as a lead and continues; those leads do not count toward the 5-reference / 2-platform quality gate.

Every report dashboard includes an external collection health panel. It separates successful countable references from missing API keys, authorization/captcha leads, public site-search results, public search HTML results, local related public documents, public article excerpts, public video details, public author profiles, public subtitles/comments/danmaku, blocked pages, failed requests, and search-only landings so the automation output can explain exactly why a report remains in `quality_gap`.

Every report dashboard also includes an `外部参考缺口队列` panel. It groups non-counted interpretation leads by required action:

- `provide_search_api_key`
- `provide_platform_auth`
- `implement_platform_parser`
- `refine_public_site_search`
- `review_candidate_url`
- `retry_request`

The same information is persisted in `data/policy_documents.sqlite.external_reference_gaps` and exposed through `data/monitor/latest_status.json.external_reference_gaps`. This queue is the operational bridge between “near full-web coverage” and the next manual/automation action: adding keys, adding local authorization files, implementing site-specific parsers, retrying temporary failures, or manually reviewing borderline URLs.

Manual/automation operators can inspect and review the queue with:

```bash
python3 -m source_registry --db data/source_registry.sqlite setup-config --dry-run
python3 -m source_registry --db data/source_registry.sqlite search-secret-import --provider bing --value-file /path/to/bing_search_api_key.txt
python3 -m source_registry --db data/source_registry.sqlite search-secret-import --provider google --value-file /path/to/google_search_api_key.txt --engine-id-file /path/to/google_cse_id.txt
python3 -m source_registry --db data/source_registry.sqlite search-secret-intake
python3 -m source_registry --db data/source_registry.sqlite setup-wizard
python3 -m source_registry --db data/source_registry.sqlite credential-doctor
python3 -m source_registry --db data/source_registry.sqlite platform-auth-import --platform bilibili --source-file /path/to/exported_bilibili_cookie.txt
python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate
python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate --platform bilibili --online
python3 -m source_registry --db data/source_registry.sqlite search-validate --offline
python3 -m source_registry --db data/source_registry.sqlite search-validate --search-secrets-file ~/.policy-intelligence/policy-search-secrets.json
python3 -m source_registry --db data/source_registry.sqlite readiness --json
python3 -m source_registry --db data/source_registry.sqlite automation-readiness --json
python3 -m source_registry --db data/source_registry.sqlite ops-dashboard
python3 -m source_registry --db data/source_registry.sqlite platform-coverage
python3 -m source_registry --db data/source_registry.sqlite platform-parsers
python3 -m source_registry --db data/source_registry.sqlite platform-parser-validate
python3 -m source_registry --db data/source_registry.sqlite attachment-parsers
python3 -m source_registry --db data/source_registry.sqlite benchmark-dashboard
python3 -m source_registry --db data/source_registry.sqlite quality-gates
python3 -m source_registry --db data/source_registry.sqlite report-check
python3 -m source_registry --db data/source_registry.sqlite gap-dashboard
python3 -m source_registry --db data/source_registry.sqlite gaps --status pending --json
python3 -m source_registry --db data/source_registry.sqlite gaps --required-action provide_platform_auth
python3 -m source_registry --db data/source_registry.sqlite gap-review <gap_id> --status resolved --reviewer linze --note "authorization file provided"
python3 -m source_registry --db data/source_registry.sqlite gap-review <gap_id> --status ignored --reviewer linze --note "low relevance candidate"
python3 -m source_registry --db data/source_registry.sqlite gap-bulk-review --required-action provide_search_api_key --status resolved --dry-run
```

`gap-review` updates only the queue status and audit fields. It does not delete rows, does not write credentials, and does not mark report quality as passed by itself. The next pipeline run must still collect usable references.

`readiness` checks the local configuration surface without exposing secrets:

- Search APIs: SerpAPI, Bing, Google CSE key/engine presence.
- Chinese search entries: Baidu, Sogou, 360 enabled in interpretation source config with public result-page extraction when accessible.
- Platform authorization: Bilibili, Douyin, Kuaishou, Weibo, Zhihu, WeChat, Xiaohongshu, Toutiao configured and available.
- External reference gaps: current pending count and action distribution.

`setup-config` creates local template files for the operator:

```bash
python3 -m source_registry --db data/source_registry.sqlite setup-config
```

Default generated paths:

- `~/.policy-intelligence/policy-search-secrets.json`
- `~/.policy-intelligence/policy-platform-auth.json`
- `~/.policy-intelligence/search_api_bundle.example.json`
- `~/.policy-intelligence/platform_auth_bundle.example.json`
- `~/.policy-intelligence/cookies/`

The generated search template contains empty fields for SerpAPI, Bing, Google API key and Google CSE id. The generated platform auth template contains cookie file paths for Bilibili, Douyin, Kuaishou, Weibo, Zhihu, WeChat, Xiaohongshu and Toutiao. The two `.example.json` bundle files are editable local handoff files for `search-secret-bulk-import`, `platform-auth-bundle-import`, and `platform-auth-session-import`. It does not create empty cookie files, because an empty readable cookie file could make readiness look available even though the platform session is unusable.

After editing the local templates, validate with:

```bash
python3 -m source_registry --db data/source_registry.sqlite readiness \
  --search-secrets-file ~/.policy-intelligence/policy-search-secrets.json \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json
```

For safer search-key setup, import local key files instead of pasting key values into commands or chat:

```bash
python3 -m source_registry --db data/source_registry.sqlite search-secret-import \
  --provider bing \
  --value-file /path/to/bing_search_api_key.txt \
  --search-secrets-file ~/.policy-intelligence/policy-search-secrets.json

python3 -m source_registry --db data/source_registry.sqlite search-secret-import \
  --provider google \
  --value-file /path/to/google_search_api_key.txt \
  --engine-id-file /path/to/google_cse_id.txt \
  --search-secrets-file ~/.policy-intelligence/policy-search-secrets.json
```

When using `gap-bulk-review`, always run `--dry-run` first and inspect the listed `gap_id` values. Bulk review should be used for administrative state cleanup after you have actually supplied keys/auth files or intentionally ignored a class of low-relevance candidates.

`gap-dashboard` writes `reports/external_reference_gap_dashboard.html` by default. It is the visual operations page for external-reference gaps: action distribution, platform distribution, status distribution, top-priority gaps and an interactive review workbench. The workbench supports action/platform/status/text filters, selecting the current filtered rows, clearing selection, generating a filtered `gap-bulk-review --dry-run` command, and generating one-by-one `gap-review` command text for selected gaps. Automation reports should include this path when gap count is non-zero.

`ops-dashboard` writes `reports/policy_ops_dashboard.html` by default. It is the cross-run operations page for the whole policy-intelligence system. By design it keeps a business-briefing layout: quality gate, directly actionable blockers, pending production queue, external-reference gaps, and links to the specialized dashboards. Recent run logs, refresh commands and detailed benchmark/parser matrices stay in their dedicated pages, so the main dashboard does not mix delivery decisions with low-value operational detail. It only reads SQLite and monitor data; it does not mutate queue or gap state.

The dashboard must show all hard quality gates, including the 95% business-value-density gate. Queue rows are numbered by the current pending production order. If industry rank 1 has no pending rows because all matching rows are already generated or skipped, the first visible row should start at queue sequence 1 while retaining its actual industry priority value.

`automation-readiness` writes `reports/automation_readiness_dashboard.html` by default. It is the go/no-go page for putting the pipeline into twice-daily automation. It checks `bash scripts/run_policy_report.sh`, `data/`, `data/pipeline.lock`, step state, latest successful run freshness, completed report artifact, pending queue, quality gate, P0 credentials, schedule times, scheduler persistence evidence, and runtime policy. Runtime policy is read from the current environment or script defaults: source/page/link limits, interpretation-document limit, request timeout, retry count, request delay, and maximum running minutes. It warns when unattended runs have no retry, no practical request delay, abnormal timeout, too-small collection scope, or too-short maximum runtime. Scheduler evidence can be a JSON manifest or launchd `.plist`; plist evidence is parsed structurally from `ProgramArguments` and `StartCalendarInterval`, so a planned-but-not-installed file or a wrong run time does not count as proof. For a twice-daily schedule, the latest successful `pipeline_runs.status='completed'` row is considered fresh for 18 hours. A blocked P0 credential state means at least one search API key and the local Bilibili authorization file are still missing. It reports status, evidence and next actions only; it never prints API key, cookie, session, account or password values.

To prove that scheduling has actually been installed, create a non-secret scheduler evidence file at `data/automation/scheduler.json` or pass `--scheduler-file`:

```json
{
  "enabled": true,
  "scheduler_type": "launchd",
  "entrypoint": "bash scripts/run_policy_report.sh",
  "schedule_times": ["09:00", "21:00"],
  "timezone": "Australia/Sydney"
}
```

This file is only an audit manifest. It does not store credentials and does not install launchd or cron by itself. The readiness dashboard treats missing or incomplete scheduler evidence as a warning because target times alone do not prove unattended execution is persisted.

Generate a reviewable macOS launchd plan before installing anything:

```bash
python3 -m source_registry --db data/source_registry.sqlite automation-scheduler-plan \
  --workspace . \
  --output-dir reports \
  --schedule-time 09:00 \
  --schedule-time 21:00 \
  --json
```

This writes:

- `reports/com.source-registry.policy-report.plist`
- `reports/scheduler_manifest.example.json`
- `reports/automation_scheduler_plan.json`
- `reports/automation_scheduler_plan.html`

`automation-scheduler-plan` is intentionally non-mutating outside the workspace. It does not call `launchctl`, does not write `~/Library/LaunchAgents`, and does not create `data/automation/scheduler.json`. After the operator installs the plist and verifies `launchctl print`, copy the manifest example to `data/automation/scheduler.json` so `automation-readiness` can prove scheduler persistence. The generated dashboard includes rollback commands for unloading the plist and removing the scheduler evidence.

`automation-lock-clean` is the safe stale-lock cleanup command. It inspects `data/pipeline.lock`, reads the recorded PID, and deletes the file only when that PID is no longer running. If no active lock remains, it also reconciles orphaned running rows in `data/policy_documents.sqlite` by marking them failed with an audit reason. It is safe to run before every unattended execution and is now part of `scripts/run_policy_report.sh`.

`platform-coverage` writes `reports/platform_coverage_dashboard.html` by default. It is the full-web readiness matrix for SerpAPI, Bing, Google CSE, Baidu, Sogou, 360, Bilibili, Douyin, Kuaishou, Weibo, Zhihu, WeChat public accounts, Xiaohongshu, Toutiao and configured public media/government interpretation sites. For each row it shows configured state, local authorization availability, implemented parser capabilities, allowed capabilities after authorization, blocker, next action, and the compliance boundary. It only prints booleans and action labels; it does not print secret values, cookie contents, or local secret paths.

`platform-parsers` writes `reports/platform_parser_dashboard.html` by default. It reads `config/platform_parsers.json` and shows parser capability by platform: public search, article body, video metadata, subtitles, comments, danmaku, author profiles and interaction metrics. Planned authorized parsers are not treated as current delivery capability; they define the next implementation slice and acceptance check after local cookie/session authorization is available.

`platform_text_parser` provides the local normalization contract for video and interaction text. It supports Bilibili JSON subtitle payloads, SRT, WebVTT, comment reply lists and danmaku XML, then returns compact report-ready excerpts and auditable empty/parse-failed states. The Bilibili collector uses this module for subtitle, comment and danmaku excerpts. It does not fetch network content by itself and does not read or print secret values.

`platform_page_parser` provides the local metadata extraction contract for authorized public result pages. It reads already-fetched HTML only, then extracts title, author, author URL, published time, view/read/play counts and engagement counts from meta tags, JSON-LD/OpenGraph and visible count text. `authorized_public_search` uses it after a result page is fetched, so platform samples can carry author/profile/interaction evidence without executing scripts or exposing cookie/session data.

`platform-parser-validate` writes `reports/platform_parser_validation_dashboard.html` by default. It reads `config/platform_parsers.json`, the optional search secret file and the optional platform auth file, then classifies every platform parser as `current_ready`, `current_partial`, `missing_search_key`, `missing_platform_auth`, `implementation_pending`, or `implementation_pending_auth_ready`. This is the go/no-go page before online sample acceptance: it does not fetch platform content, does not print secret values, and does not change gap state.

`platform-parser-samples` writes `reports/platform_parser_sample_dashboard.html` by default. It reads local `interpretation_items` from `data/policy_documents.sqlite` and classifies parser output as `sample_passed`, `partial_sample`, `no_samples`, or `secret_leak`. It is the business acceptance page for external interpretation quality because it separates usable report references from search landings, missing-key rows and login-blocked clues.

`attachment-parsers` writes `reports/attachment_parser_dashboard.html` by default. It reads `config/attachment_parsers.json` and shows ready, partial and planned parser capability for official attachments and external research files: PDF text layer, DOCX/XLSX/PPTX OOXML, scan/image OCR, Apache Tika for legacy Office/complex formats, and GROBID for research PDF structure and references. It also performs a local dependency readiness check for Python modules, the system `tesseract` binary, `TIKA_SERVER_URL`, and `GROBID_SERVER_URL`; external service URLs are treated as configured-not-checked and are not called during dashboard generation. Current built-in OOXML extraction includes DOCX body/header/footer/comments, XLSX workbook sheet names and cell values, and PPTX slide text. Tika/GROBID are optional external-service bridges: configured services can be used by the parser, while missing services remain visible as dependency gaps rather than false success.

`benchmark-dashboard` writes `reports/benchmark_dashboard.html` by default. It reads `config/benchmark_models.json` and shows the evidence matrix, source-family distribution, capability-target coverage, adoption queue and compliance guardrails for PolicyInsight, GovReady-Q, CISO Assistant, Open Policy Agent, changedetection.io, Huginn, Regology and Monity AI. This is the control surface for turning external reference products into implementable local features without copying proprietary data or weakening the access-control boundary.

`quality-gates` writes `reports/quality_gates_dashboard.html` by default. It reads `rules/quality_gates.json`, refreshes monitor status, and evaluates current evidence against hard gates: 5 external references, 2 external platforms, one policy file per report, PDF primary output, 10 deep analysis chapters, 10-page PDF body target, and 95% business-value density. Compliance guardrails are also listed explicitly: no CAPTCHA bypass, no paywall bypass, no access-control bypass, no prohibited platform interfaces, and no secret output. Gates without current evidence are marked `not_checked`, not passed.

The external reference collector may use `历史成功公开参考复用` for the same policy document when a public page that previously yielded an article excerpt is temporarily unavailable. This cache excludes search landing pages, blocked pages, failed pages and local related-document rows, dedupes by platform and title, and defaults to one reused public reference per run.

Authorized platforms with `collector_type=authorized_public_search` use a conservative bridge collector. When a local cookie file is available, the collector requests the configured search page, parses public result links, and extracts article text from pages that remain accessible. Login-required, CAPTCHA/security-check, paywall or access-controlled pages are audit leads only and do not count as report references. The collector stores only sanitized auth metadata such as configured/available booleans and capability names; it never stores cookie values, session values, passwords or full cookie paths.

`report-check` writes `reports/report_artifact_check_dashboard.html` by default. It inspects the latest generated PDF report unless `--report-path` is provided. It checks PDF existence, non-blank size, PDF page count, extractable PDF text density, HTML visible-text density, HTML/Markdown/dashboard sidecars, single-document scope, deep chapter count, clickable table of contents, rule-panel presence, research-quality panel or dashboard sidecar presence, reference-section presence, and estimated reference-section compactness. Reference compactness is measured from the report body `interpretations` section rather than the table of contents. Its metrics feed `quality-gates`, so PDF page count, blank-risk and deep chapter gates can be verified from generated artifacts instead of staying `not_checked`.

`setup-wizard` writes `reports/setup_wizard_dashboard.html` by default. It is the local onboarding surface for the user/operator: step matrix, readiness summary, local template paths, command matrix with copy buttons, and next actions. It now includes search API bulk import, platform cookie bundle/directory bulk import, platform-parser registry validation, crawl-policy and attachment-parser checks before gap review and final pipeline execution. It is intentionally read-only. It does not create key values, does not create cookie files, does not print account credentials, and does not change gap status.

`access-readiness` writes `reports/access_readiness_dashboard.html` by default. It is the consolidated go/no-go page for near-full-web intake: search API, Bilibili P0 auth, Baidu/Sogou/360 public Chinese search entries, WeChat/Zhihu/Weibo P1 auth, short-video/social P2 auth, and platform parser prerequisites. It only prints sanitized status, business value, next commands, and compliance boundaries. It does not print API keys, cookies, sessions, account credentials, bundle contents, or full sensitive cookie paths.

`credential-doctor` writes `reports/credential_doctor_dashboard.html` by default. It should be run after editing the local search/auth files and before running unattended automation. It checks whether the search secret file exists, whether values are empty/placeholders, whether the platform auth JSON is valid, whether referenced cookie/session files exist and are non-empty, whether files are older than the default staleness threshold, and whether file permissions are too open. It does not validate the actual key against remote providers unless future explicit validation is added, and it never prints secret values.

`search-secret-intake` writes `reports/search_secret_intake_dashboard.html` by default. It is the operator checklist for SerpAPI, Bing and Google CSE: provider readiness, missing fields, business value, `search-secret-import` / `search-secret-bulk-import` commands, and offline/online validation commands. Google CSE is only ready when both the API key and CSE ID exist. It never prints API key values or full sensitive paths.

`platform-auth-intake` writes `reports/platform_auth_intake_dashboard.html` by default. It is the operator checklist for Bilibili, Douyin, Kuaishou, Weibo, Zhihu, WeChat public accounts, Xiaohongshu and Toutiao authorization. It supports single-cookie import, directory bulk import, `platform-auth-bundle-import` from one local JSON file, and `platform-auth-session-import` for a Chrome/Playwright session file or Chrome profile directory. Cookie files can become direct collector inputs; Chrome/session references are shown as `session-only` until a platform-specific validator or cookie extraction path makes them collector-ready. It never prints cookie/session values, account credentials, bundle contents, or full sensitive paths.

`platform-auth-validate` writes `reports/platform_auth_validation_dashboard.html` by default. In offline mode it checks whether Bilibili, Douyin, Kuaishou, Weibo, Zhihu, WeChat, Xiaohongshu and Toutiao authorization files are configured and locally available. With `--online`, Bilibili uses one minimal public login-state request. Other platforms can use a configured `validation_url` plus `success_markers`, `login_required_markers`, and `captcha_markers` in the local platform auth JSON. Missing markers or session-only credentials remain `online_validator_pending`; login pages, captcha/security pages, request failures, and uncertain marker results do not count as usable authorization. It never prints cookie/session values or full local cookie paths.

`search-validate` writes `reports/search_validation_dashboard.html` by default. In `--offline` mode it checks API configuration and runs a local parser self-test for Baidu, Sogou and 360 public HTML search entries. In online mode it sends one minimal public query to each configured API provider and reports whether the provider passed, failed, or returned no results. It reports result count, sample result domain and error class only; it never prints API key values. Use online mode intentionally because it may consume a small amount of API quota.

The lightweight monitor command is:

```bash
python3 -m source_registry --db data/source_registry.sqlite status --json
```

It refreshes `data/monitor/latest_status.json` and reports:

- latest run status and report file existence
- 5-reference / 2-platform quality gate
- external collection health, including missing API keys and platform authorization gaps
- external reference gap queue, including pending count, grouped actions, and top priority URLs
- pending queue count, active industry, and early-production candidates
- recent report timeline
- recent run-log errors

The step-level automation command is:

```bash
python3 -m source_registry --db data/source_registry.sqlite automation-dashboard --json
```

It reads `data/automation/latest_run.json` and writes `reports/automation_run_dashboard.html`. `scripts/run_policy_report.sh` updates this file before and after each automation stage. On failure, the failed step records a non-zero exit code and an error summary, then refreshes the dashboard before exiting.

The automation go/no-go command is:

```bash
python3 -m source_registry --db data/source_registry.sqlite automation-readiness \
  --content-db data/policy_documents.sqlite \
  --data-dir data \
  --search-secrets-file ~/.policy-intelligence/policy-search-secrets.json \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json \
  --scheduler-file data/automation/scheduler.json \
  --schedule-time 09:00 \
  --schedule-time 21:00 \
  --json
```

Use it before enabling or changing the external automation schedule. `ready` means the unattended surface is clean; `attention` means it can run but needs follow-up; `blocked` means the automation should not be treated as production-ready.

For stronger Bilibili access, put a cookie string in a local file outside version control and set:

```bash
BILIBILI_COOKIE_FILE=/secure/path/bilibili_cookie.txt bash scripts/run_policy_report.sh
```

The safer repeatable path is to import an exported browser cookie file into the private auth store:

```bash
python3 -m source_registry --db data/source_registry.sqlite platform-auth-import \
  --platform bilibili \
  --source-file /path/to/exported_bilibili_cookie.txt \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json
```

This command copies the cookie into `~/.policy-intelligence/cookies/`, sets private file permissions, updates `policy-platform-auth.json`, and prints only sanitized status, marker and validation commands.

For multi-platform setup, put exported cookie text files in one local directory and name them `<platform>_cookie.txt`, for example `bilibili_cookie.txt`, `zhihu_cookie.txt`, `weibo_cookie.txt`, `toutiao_cookie.txt`. Then run:

```bash
python3 -m source_registry --db data/source_registry.sqlite platform-auth-bulk-import \
  --source-dir /path/to/exported_cookie_dir \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json
```

The bulk importer uses the same private target directory and sanitized output rules as the single-platform importer.

Do not put Bilibili username/password in the project, automation prompt, database, or chat transcript.

For multi-platform authorization readiness, copy `config/platform_auth.example.json` to a secure path outside this project and set:

```bash
PLATFORM_AUTH_FILE=/secure/path/policy-platform-auth.json bash scripts/run_policy_report.sh
```

The file should only contain local cookie/session file paths and allowed capabilities. The pipeline checks whether those files exist and records sanitized status only:

- `auth_not_configured`
- `auth_cookie_file_missing`
- `auth_cookie_file_available`
- `auth_session_file_missing`
- `auth_session_file_available`

Having a valid cookie/session file does not mean the platform is fully integrated. Until a specific parser is implemented, the report marks the source as `授权文件可用；待接入平台解析器` and does not count it toward the 5-reference / 2-platform quality gate.

## Codex Automation

Created automation:

- ID: `automation`
- Name: `中国政策文件监测报告`
- Status: `PAUSED`
- Workspace: `systems/policy_intelligence/source`

The automation prompt is:

```text
Run the policy intelligence pipeline by executing `bash scripts/run_policy_report.sh` from the source-authority-registry deliverable directory. Each run must generate at most one single-file policy research report. Report the generated PDF report path, report artifacts, run stats, effective external reference count, current pending queue preview, recent report timeline, and any errors. Check whether the report includes executive summary, source authority tier, policy attribute, applicable industries and regions, core clause breakdown, industry-chain impact, beneficiary company or security candidates, business impact, trading observation value, risks and uncertainty, relationship to historical policies or existing industry research, and task queue items for the industry research or trading advice system. If any depth requirement is missing, list the gap and mark the report for Codex deep interpretation or human review. If the command exits non-zero, inspect `data/run_logs/` and summarize the failure. Do not change source code during this automation run.
```

The current cadence is Sydney 10:00 and 22:00, which maps to Beijing 08:00 and 20:00 for the current June timezone offset.

Because each run now generates one report for one policy file, the twice-daily schedule produces two single-file research reports per day. The automation output must include:

- generated report path
- PDF path must be the primary report path
- HTML/Markdown sidecar paths when available
- `data/monitor/latest_status.json` path and alerts when available
- `data/automation/latest_run.json` path and step failure summary when available
- run stats
- current pending queue preview
- external reference gap queue and required actions
- external reference gap dashboard path when generated
- readiness status for search API keys, Chinese search entries, and platform authorization files
- platform authorization validation dashboard path
- benchmark dashboard path and reference-model implementation gaps
- quality gate rules path, failed gates, and not_checked gates
- report artifact self-check dashboard path and failed/warning artifact checks
- recent report timeline
- whether any queued reports should be produced early
- whether the report meets the policy depth standard
- missing depth requirements, if any
- whether the report should enter Codex deep interpretation or human review

The queue is governed by `config/industry_priorities.json`. The automation must not skip from an earlier industry rank to a later industry rank while earlier-rank pending reports remain. If an earlier industry lacks the required 5 effective external references, report the deficit and required authorization instead of silently moving to a later industry.

Keep it paused until you are ready for unattended runs. Enable it from the Codex App automation pane after reviewing the first few manual reports.

## Current gaps before production use

- Gmail API push is not wired yet.
- Template analysis is automation-safe and now more detailed, but it is still not a full Codex deep-read analysis.
- Attachment parsing now extracts DOCX/XLSX with built-in XML parsing, extracts PDF text when `pypdf` or `PyMuPDF` is available, and attempts optional OCR for scanned PDFs/images when `PyMuPDF`, `Pillow`, `pytesseract`, and local Tesseract language data are available. Legacy DOC/XLS is still pending.
- Bilibili public video metadata, author profile metadata, detail counters, public subtitle excerpts, public comment excerpts, and public danmaku excerpts are collected when configured endpoints return results. Restricted comments, fuller danmaku history, Douyin/Kuaishou/Weibo/Zhihu/WeChat/Xiaohongshu page details, and other pages requiring login still need authorized Chrome/cookie/API access.
- Public article/body extraction is wired for search API results, directly readable public site-search results, and Chinese public-search HTML results, but it is generic HTML extraction. Site-specific extraction rules for major research/media platforms can improve precision later.
- External reference gaps are persisted, visible in monitor/dashboard, reviewable through CLI, and now exposed through an interactive HTML gap-management workbench. Direct in-browser database mutation is still intentionally not enabled; the page generates commands for terminal execution after review.
- Multi-platform authorization readiness is wired through `PLATFORM_AUTH_FILE`, but platform-specific parsers for Douyin/Kuaishou/Weibo/Zhihu/WeChat/Xiaohongshu/Toutiao are still pending.
- Final delivery inputs are listed in `docs/final_delivery_inputs.md`.
