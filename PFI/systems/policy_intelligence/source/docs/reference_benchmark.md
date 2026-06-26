# Reference Benchmark for Policy Intelligence

This benchmark converts `~/Downloads/policy_agent_research.pdf` and follow-up web research into implementation targets for this project.

Last refreshed: 2026-06-04. The referenced PDF was not available at its previous local path during this refresh, so GitHub/open web sources listed below were rechecked directly.

## Sources Reviewed

- [PolicyInsight](https://github.com/Kishorevb/policyinsight): dynamic government policy monitoring, real-time document monitoring, adaptive policy data model, NLP/LLM insights, responsive UI, alerts, scalability.
- [GovReady-Q](https://github.com/GovReady/govready-q): open-source self-service GRC, compliance-as-code, reusable compliance content, automated assessments, documentation workflows.
- [CISO Assistant](https://github.com/intuitem/ciso-assistant-community): open-source GRC hub, risk/compliance/audit workflows, API-first design, object linking, import/export, reporting.
- [Open Policy Agent](https://github.com/open-policy-agent/opa): policy-as-code engine, Rego rules, policy decision and enforcement separation, REST/SDK integration.
- [changedetection.io](https://github.com/dgtlmoon/changedetection.io): open-source website change detection, web page monitoring, notifications, browser-backed fetching, JSON/RSS-oriented monitoring.
- [Heritrix3](https://github.com/internetarchive/heritrix3): Internet Archive open-source, extensible, web-scale, archival-quality crawler; useful for crawl policy, robots-aware boundaries, snapshots, and long-term preservation.
- [Scrapy](https://github.com/scrapy/scrapy): Python high-level crawling and scraping framework; useful for source adapters, request middleware, rate limits, retry policy, deduplication, and parser contracts.
- [Apache Tika](https://github.com/apache/tika): detects and extracts metadata/text from many file types including PDF, Office, spreadsheets and presentations; useful for a unified attachment parser registry.
- [GROBID](https://github.com/grobidOrg/grobid): ML-based extraction and restructuring of raw PDFs into structured XML/TEI, useful for white papers, blue books and research-report citation chains.
- [Huginn](https://github.com/huginn/huginn): open-source self-hosted agents that monitor sources, emit events, and trigger actions.
- [Regology](https://www.regology.com/): regulatory intelligence platform, AI agents, regulatory change, research workflows, global source coverage, industry-agnostic impact assessment.
- [Monity AI](https://monity.ai/): AI website change monitoring, natural-language monitors, visual/PDF/document diffs, authenticated monitoring, Slack/Teams/Discord/webhook alerts.

## Capability Targets

| Capability | Borrowed From | Current Status | Next Implementation |
| --- | --- | --- | --- |
| Continuous policy monitoring | PolicyInsight, changedetection.io, Monity | Scheduled crawler and queue exist | Add source-level diff history and stale/offline state |
| Dynamic policy data model | PolicyInsight | SQLite schemas exist | Add relationship/version graph fields |
| NLP/LLM analysis | PolicyInsight | Template and Codex modes exist | Add structured eval checklist and knowledge-graph prompts |
| Dashboard and charts | PolicyInsight, CISO Assistant | Added per-report dashboard HTML and cross-run `policy_ops_dashboard.html` with run, queue, gap, quality and benchmark charts | Add deeper drill-down, persisted filters, and PDF export for operations review |
| Compliance-as-code | GovReady-Q, OPA | Quality gates are coded in Python | Add declarative rules file for report gates and source inclusion |
| Audit trail | GovReady-Q, CISO Assistant | `report_timeline` exists | Add reviewer actions, owner, decision reason, rollback marker |
| External reference gap workflow | GovReady-Q, CISO Assistant, Monity | `external_reference_gaps` stores blocked/missing-key/auth/parser leads; CLI can list, single-review, bulk-review, run readiness checks, generate local secret/auth templates, and render an interactive HTML gap dashboard with filters, row selection, and command generation | Add platform-specific remediation actions and a backend management API |
| Alert routing | PolicyInsight, changedetection.io, Huginn, Monity | Timeline records only | Add local webhook/Slack/Teams/email adapters after user supplies targets |
| Full-web authorized sources | Monity, Regology | Bilibili public API, platform search entries and `config/platform_parsers.json` parser capability registry exist | Add search API keys, Chrome session/cookie authorization, and platform detail collectors for planned parser rows |
| Visual/text/element diff | changedetection.io, Monity | Snapshots exist | Add normalized text diff and visual thumbnail diff for watched pages |
| Archival crawler policy | Heritrix3 | Snapshots exist, but crawl policy is implicit | Add crawl policy registry with robots status, user-agent/contact, rate limits, retry policy and retention |
| Modular crawler framework | Scrapy | Collector logic exists as Python functions | Add source adapter/spider contract covering URL normalization, dedupe, throttling, retry and parser tests |
| General attachment parsing | Apache Tika | `config/attachment_parsers.json` and `reports/attachment_parser_dashboard.html` track PDF/DOCX/XLSX/OCR ready/partial capability plus optional Tika bridge for legacy Office/complex formats | Add Tika health check, text-volume metrics, fixture corpus and concurrency limits |
| PDF structure and citation extraction | GROBID | Optional GROBID bridge can extract title, author, section and reference text from TEI when `GROBID_SERVER_URL` is configured | Add reference dedupe, author/organization normalization and source-authority linking |
| Global/regional source coverage | Regology | China-first source registry exists | Add source registry import workflow for other countries and authorities |
| Job orchestration | Huginn | Shell + Python CLI orchestration exists | Add job registry, retry state, and per-step status dashboard |

## First Delivery Slice

The first delivery slice focuses on report and operations visibility:

- Every generated report includes a visual dashboard section.
- Every generated report creates a same-name `_dashboard.html` sidecar.
- The system can also generate `reports/policy_ops_dashboard.html`, a cross-run operations dashboard for automation readiness and backlog review.
- Dashboard panels include collection funnel, quality gates, platform coverage, queue distribution, timeline events, and the benchmark capability matrix.
- `config/benchmark_models.json` is now the source of truth for the reference-model evidence matrix.
- `reports/benchmark_dashboard.html` shows source evidence, capability-target coverage, adoption queue, and compliance guardrails.
- Charts are inline HTML/CSS and do not require remote JavaScript.
- The benchmark dashboard now includes explicit acceptance checks, so each reference model maps to a verifiable implementation slice rather than a generic inspiration note.
- `reports/platform_parser_dashboard.html` now separates current Bilibili/search/public-site parser delivery from planned Douyin/Kuaishou/Weibo/Zhihu/WeChat/Xiaohongshu authorized parser work.
- `reports/platform_parser_validation_dashboard.html` now combines parser registry rows with search key and platform authorization prerequisites, turning parser plans into executable acceptance gates.
- `reports/platform_parser_sample_dashboard.html` now verifies local collected interpretation samples, separating report-usable evidence from search landings, login-blocked clues and missing-key rows.
- `reports/attachment_parser_dashboard.html` now separates built-in parser capability from optional Tika/GROBID service dependencies, so the main operations dashboard can stay concise while parser readiness remains auditable.

## Remaining User Inputs Needed

- Search API keys and preferred provider order: Bing, Google Programmable Search, SerpAPI, Baidu/Sogou/360 equivalents.
- Platform authorization method: Chrome logged-in session, local cookie file, OAuth/API credentials, or manual export.
- Alert routing targets: Slack webhook, Teams webhook, email SMTP, Discord webhook, local file only.
- Deployment target: current Mac only, always-on Mac, or cloud server.
