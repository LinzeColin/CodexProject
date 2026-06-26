# Schema

## sources

来源主表。只保存来源信息，不保存政策正文。

关键字段：

- `source_id`：稳定来源 ID。
- `official_url`：来源官网或栏目 URL。
- `canonical_domain`：规范化域名。
- `source_type`：`government_portal`、`ministry`、`provincial_portal`、`think_tank` 等。
- `crawl_enabled`：爬虫是否可读取该来源。
- `review_status`：`unreviewed`、`system_scored`、`user_confirmed`、`rejected`、`needs_review`。

## source_evidence

来源证据表。

常见 `evidence_type`：

- `official_directory`
- `organization_page`
- `government_site_id`
- `icp_registration`
- `police_registration`
- `sponsor_unit`
- `supervisor_unit`
- `about_page`
- `manual_note`

## authority_scores

评分历史表。每个来源只有一条 `active=1` 的当前评分。

包含：

- `system_score`
- `final_score`
- `tier_system`
- `tier_final`
- 五项评分拆分
- `scoring_details_json`

## source_authority_current

当前权威性视图。爬虫和报告层优先读取这个视图。

## documents

政策文件和附件线索表。正文数据库保存原文 URL、来源快照、抓取快照路径和可用于分析的文本摘录。

关键字段：

- `document_type`：`webpage` 或 `attachment`。
- `snapshot_path`：本次抓取保存的 HTML、PDF、DOCX、XLSX 或二进制快照路径。
- `text_excerpt`：网页正文摘录；当 PDF/DOCX/XLSX/图片附件被抓取且可解析时，保存附件文本摘录。扫描版 PDF 和图片会尝试可选 OCR；若缺少 `PyMuPDF`、`Pillow`、`pytesseract` 或本机 Tesseract 语言包，运行日志会记录 `ocr_unavailable:*`，字段可能为空。旧版 DOC/XLS 仍可能为空。
- `content_hash`：抓取内容哈希，用于去重和历史追溯。
- `authority_tier_snapshot`、`authority_score_snapshot`：抓取当时的来源权威快照，避免后续改分影响历史报告。

## interpretation_sources

外部研究/解读资料来源表。它不保存政策原文，只定义如何为政策文件寻找补充解读资料。

关键字段：

- `interpretation_source_id`：稳定解读来源 ID。
- `platform`：平台，例如 `bilibili`、`gov.cn`、`people.cn`。
- `source_type`：`video_interpretation`、`official_interpretation`、`business_media_analysis` 等。
- `url_template`：报告中的可点击搜索入口。
- `api_url_template`：可选 API 入口；当前用于 B 站公开视频搜索。
- `collector_type`：`search_landing`、`bilibili_api`、`search_api_bing`、`search_api_google`、`search_api_serpapi`、`public_site_search`、`public_search_html` 或 `local_related_documents`。
- `max_results`：每个政策文件从该来源最多采集的结果数。
- `auth_required`：是否需要登录态。
- `validation_url`、`success_markers`、`login_required_markers`、`captcha_markers`：本地平台授权文件中的可选在线验证配置。在线验证只在用户显式执行 `platform-auth-validate --online` 时读取 cookie 访问验证 URL，并按标记判断登录态；报告和 dashboard 只展示是否配置、状态和错误类型，不展示 cookie、账号密码或完整本地路径。

## interpretation_items

外部研究/解读资料条目表。报告和分析会引用这些条目，但不会把它们与官方原文混为同一权威等级。

关键字段：

- `document_id`：关联的政策文件。
- `platform`：资料平台。
- `item_type`：`video`、`article`、`search_result` 或 `search_entry`。
- `title`、`url`、`query`：资料标题、链接和检索词。
- `evidence_status`：`公开视频搜索结果`、`公开搜索入口`、`公开 API 未返回结果，保留搜索入口`、`需登录/反爬验证；未配置授权文件`、`授权文件可用；待接入平台解析器`、`bing公开搜索结果；正文已摘录`、`google公开搜索结果；正文受限`、`gov.cn公开站内搜索结果；正文已摘录`、`sogou公开搜索结果；正文已摘录` 等。
- `author_name`、`author_url`：作者、UP 主或账号信息。
- `published_at`：公开发布时间。
- `duration_seconds`：视频时长，非视频为空。
- `view_count`、`engagement_count`：播放/阅读和互动计数。
- `content_excerpt`：简介、标签、分区、搜索摘要或公开网页正文摘录；B 站公开视频如存在公开作者页、字幕、评论或弹幕，会追加对应摘录。搜索 API、公开站内搜索和中文公开搜索 HTML 结果开启正文抽取时，会优先保存公开 HTML 页面正文摘录。
- `relevance_score`：系统估算的 0-100 相关度。
- `raw_metadata_json`：原始公开元数据快照。B 站视频会尽量保存 `bvid`、`cid`、互动计数、公开作者页状态、作者公开认证/粉丝/简介摘录、字幕状态、字幕摘录、评论状态、评论摘录、弹幕状态和弹幕摘录。搜索 API、公开站内搜索和中文公开搜索 HTML 结果会保存 `article_fetch_status`、`article_content_type`、`article_fetched_url`、页面标题、搜索入口、搜索平台和结果状态。本地相关公开文件会保存 `related_document_id`、来源名称和权威快照。授权平台线索会保存脱敏后的 `platform_auth` 状态，例如是否已配置 cookie/session 文件、文件是否可用、允许能力清单和缺口说明；不会保存 cookie 内容、账号或密码。

## external_reference_gaps

外部参考缺口队列表。它把未计入 5 份有效参考 / 2 个外部平台质量门槛的外部线索转成可追踪待办，供 dashboard、monitor 和 automation 决定下一步补 API、补授权、接解析器或人工复核。

关键字段：

- `gap_id`：稳定缺口 ID，由政策文件、解读来源、URL 和缺口类型生成。
- `document_id`：关联的政策文件。
- `interpretation_source_id`：产生该缺口的解读来源。
- `platform`：平台或搜索入口。
- `gap_type`：机器可读缺口类型，例如 `missing_api_key`、`platform_auth_missing`、`platform_parser_pending`、`search_landing`、`public_site_no_result`、`public_article_blocked`、`public_article_failed`、`public_article_too_short`、`request_failed`、`low_relevance_candidate`。
- `required_action`：建议动作，例如 `provide_search_api_key`、`provide_platform_auth`、`implement_platform_parser`、`refine_public_site_search`、`review_candidate_url`、`retry_request`。
- `priority_score`：0-100 优先级。缺搜索 key、缺授权和待接解析器优先级最高。
- `status`：`pending`、`resolved`、`ignored`。
- `first_seen_run_id` / `last_seen_run_id`：首次和最近一次出现该缺口的运行编号。
- `reviewed_by` / `review_note` / `reviewed_at`：人工复核人、复核说明和复核时间。用于记录已解决、忽略或重新置为待处理的原因。
- `raw_metadata_json`：脱敏元数据，只保存公开抓取状态、公开作者/视频/article 状态和授权状态布尔值；不保存账号、密码、cookie 内容或本地敏感文件路径。

同一缺口重复出现时更新 `last_seen_run_id` 和优先级，不重复插入。已 `resolved` 的缺口如果后续再次出现，会重新变为 `pending`。

CLI 支持：

- `gaps`：列出缺口。
- `gap-review`：复核单个缺口。
- `gap-bulk-review`：按 `required_action`、`gap_type` 或 `platform` 批量复核缺口，建议先 `--dry-run`。
- `gap-dashboard`：生成外部参考缺口 HTML 可视化管理页，默认输出 `reports/external_reference_gap_dashboard.html`。

配置 readiness 不写入独立表，由 `readiness` 命令即时读取搜索 secret 文件、平台授权文件、解读来源配置和当前缺口汇总后输出脱敏状态。

本地配置模板也不写入数据库，由 `setup-config` 生成：

- `policy-search-secrets.json`：空的 SerpAPI/Bing/Google CSE key 字段。
- `policy-platform-auth.json`：各平台 cookie/session 文件路径和允许能力清单。
- `cookies/`：建议放置本地 cookie/session 文件的目录。命令只创建目录，不创建空 cookie 文件。

## data/automation/latest_run.json

自动化步骤级运行状态文件。它不是 SQLite 表，而是 `scripts/run_policy_report.sh` 每个阶段更新的机器可读 JSON，用于无人值守运行失败定位。

关键字段：

- `run_id`：自动化运行编号，默认由脚本启动时间生成。
- `status`：`running`、`completed` 或 `failed`。
- `started_at` / `updated_at`：UTC 时间戳。
- `summary`：步骤总数、完成数、失败数、运行中数、跳过数和累计耗时秒。
- `steps[]`：步骤明细。
- `steps[].step_key`：稳定步骤 ID，例如 `pipeline_run`、`quality_gates`、`platform_auth_validate`。
- `steps[].label`：中文步骤名。
- `steps[].status`：`running`、`completed`、`failed` 或 `skipped`。
- `steps[].exit_code`：命令退出码。
- `steps[].duration_seconds`：步骤耗时。
- `steps[].error_summary`：失败摘要。只记录短文本，不记录 API key、cookie、账号密码或 secret 文件内容。

可视化输出：

- `reports/automation_run_dashboard.html`：步骤状态 dashboard。

## report artifact check JSON

`report-check --json` 输出的是生成后报告产物自检结果，不写入 SQLite。它用于发现 PDF 空白、HTML 空白、Reference 过长、目录缺失和 dashboard 缺失等问题。

关键字段：

- `report_path`、`html_path`、`markdown_path`、`dashboard_path`：PDF 主产物和同名辅助产物路径。
- `pdf_size_bytes`、`pdf_page_count`、`pdf_text_char_count`：PDF 文件大小、页数和可提取文字字符数。`pdf_text_char_count` 用于识别“文件存在但内容空白”的风险。
- `html_size_bytes`、`html_visible_text_char_count`：HTML 文件大小和去除脚本/CSS/标签后的可见文字字符数。
- `report_document_count`：报告研究文件数，必须为 1。
- `deep_chapter_count`：主体深度章节数，目标不少于 10。
- `toc_present`、`toc_anchor_count`：可点击目录状态。
- `reference_section_char_count`、`reference_section_estimated_pages`、`reference_section_compact`：Reference 正文区块长度和 1 页内估算。计算优先读取 `section#interpretations`，并在 `#queue` 或 `#timeline` 前停止，避免把目录或等待队列误算进 Reference。
- `blank_risk`：综合 PDF 大小、PDF 可提取文字和 HTML 可见文字后的空白风险布尔值。
- `checks[]`、`summary`：每项自检结果和通过/失败/警告汇总。

## report_queue

单文件研究报告队列表。每份报告只对应 1 个 `document_id`。

关键字段：

- `document_id`：待生成报告的政策文件。
- `analysis_mode`：分析模式版本。
- `status`：`pending`、`generated`、`skipped`。
- `primary_industry` / `industry_bucket`：行业板块，用于队列排序。
- `industry_rank`：用户确认的行业优先级序号，1 为最高优先级，未命中为 999。
- `sort_time`：排序时间，优先使用发布日期，其次发现时间。
- `administrative_level` / `level_rank`：中央到地方排序字段。
- `priority_score`：系统估算优先级。
- `generated_report_path`：已生成报告路径。

排序口径：行业序号、时间、中央到地方、优先级。默认只纳入 `2025-01-01` 之后的文件；如果前序行业出现新文件，会自动回到前序行业，直到该行业 pending 队列清空后再进入后序行业。

## report_timeline

报告生成时间线，用于运营审计、同名 dashboard sidecar 和 automation 状态追溯；正式 PDF 正文默认不展示最近运行明细。

关键字段：

- `run_id`：生成该报告的 pipeline run。
- `document_id`：对应政策文件。
- `event_type`：当前主要为 `generated`。
- `report_path`：生成的单文件研究报告。
- `primary_industry`、`administrative_level`：用于回看报告覆盖节奏。
- `details_json`：标题、来源、有效外部参考数量等快照。
