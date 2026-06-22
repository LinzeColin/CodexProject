# arXiv Daily Push 两阶段 Master Task Pack V4

> 文档版本：4.0  
> 日期：2026-06-22  
> 目标仓库：`LinzeColin/CodexProject`  
> 目标项目：`arxiv-daily-push/`  
> 新电脑迁移目标日期：2026-06-30  
> 顶层开发阶段：**仅两个**  
> 最终状态：`PRODUCTION_ACCEPTED → DAILY_OPERATION`

---

# 使用方式

你只需要把整个 ZIP 交给 Codex，并把 ZIP 内的 `FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_V4.txt` 作为持续 Prompt 发送给 Codex。

ZIP 内只保留四类内容：

```text
START_HERE_MASTER_TASK_PACK_TWO_STAGE_V4.md  本文件，包含全部要求、标准、权重、测试和时间线
FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_V4.txt   可直接发送给 Codex 的持续 Prompt
baseline/REFERENCE_OWNER_DECISIONS.rtf       人工决策只读基线
baseline/MULTISOURCE_LOCAL_PRODUCTION_TASKPACK_V1.md  完整产品与工程只读基线
```

本文件已经将原来分散的比较文件、Task Pack、Test Pack、迁移规则和 Prompt 合并。Codex 不得要求你再维护另一组平行文件。

---

# Part A｜基线锁、允许变化和两阶段总览

## A1. 两份只读基线

| 文件 | 作用 | SHA-256 |
|---|---|---|
| `baseline/REFERENCE_OWNER_DECISIONS.rtf` | 五封邮件、本地运行、1 改 4 看、资源与人工决策 | `ed983f72e6233b6c2d707e69d131be9416f894aa46d39e7d962dcf65c738f7e0` |
| `baseline/MULTISOURCE_LOCAL_PRODUCTION_TASKPACK_V1.md` | 完整产品范围、来源、模型、数据库、队列、报告、治理和验收 | `2900f5c810ea4e87ea8a33b953551c4d822475e7063547e9cbc1627100f96bab` |

Codex 必须在每个 Task、PR 和晋升门禁前校验哈希。两份基线不得修改、覆盖、删减、弱化或重新解释。

## A2. 本次唯一允许的变化

| Delta ID | 允许变化 |
|---|---|
| D-001 | 先完成 arXiv 单源完整纵向切片，再逐来源、逐板块晋升 |
| D-002 | 2026-06-30 作为新电脑迁移目标日期，但必须由人工确认解锁 |
| D-003 | 迁移前只做低资源代码工作；重放、批量媒体、大规模缓存和正式运行延后 |
| D-004 | 增加单源、来源级和板块级晋升门禁；最终全系统 30 日＋2 日标准不变 |

未列入 D-001—D-004 的任何范围缩小、删除、弱化、无限期延后或验收降低，均属于需求回归。

## A3. 只有两个顶层阶段

```text
Stage 1：arXiv 单源完整纵向切片与生产验收
Stage 2：逐来源、逐板块晋升与全系统生产验收
```

Stage 1 包含迁移前和迁移后两个执行窗口，但仍然只是一个阶段。Stage 2 包含多个来源 Wave，但仍然只是一个阶段。

## A4. 总时间线

| 时间/门禁 | 目标 | 资源规则 |
|---|---|---|
| 2026-06-22—2026-06-29 | Stage 1 迁移前代码窗口 | 仅低资源代码、fixture、最多 10 条 arXiv canary |
| 2026-06-30 起，人工确认新电脑后 | Stage 1 新电脑验收窗口 | 部署、arXiv 30 日重放、连续 2 日真实运行 |
| `ARXIV_PRODUCTION_ACCEPTED` 后 | Stage 2 | 逐来源、逐板块晋升；arXiv 稳定生产持续运行 |
| Stage 2 末尾 | 最终全系统验收 | 150 报告、150 邮件预览、150 视频＋2 日真实运行 |

工程估计：

```text
迁移前代码就绪：目标 2026-06-29 前
新电脑部署和 arXiv 生产验收：迁移后约 5—10 个自然日
Stage 2 完整开发和验收：约 12—18 周
保守区间：约 22 周，网站变更、反爬、许可和硬件问题可能延长
```

时间估计不得作为降低质量、跳过测试或伪造完成的理由。

## A5. 冲突处理

若发现基线之间、基线与仓库或需求与技术现实冲突，进入：

```text
BLOCKED_REQUIREMENT_CONFLICT
```

必须输出冲突双方文件和位置、影响、A/B/C 最小选项、推荐项。不得静默折中。

---

# Part B｜冻结的产品、来源、模型、数据与运营基线

> 本 Part 完整保留原产品和工程基线。后面的两阶段计划只改变执行顺序和重任务时点，不改变本 Part 的最终要求。

# 0. 结论与冻结决策

## 0.1 最终产品

系统从单一 arXiv 日报升级为四板块、多来源、证据可追溯的每日情报系统：

| 板块 ID | 板块 | 核心内容 |
|---|---|---|
| B1 | 研究前沿 | 预印本、医学索引、开放研究与早期技术信号 |
| B2 | 顶级期刊 | Nature、Science、The Lancet 主刊的高质量证据 |
| B3 | 中国政策法规 | C0—C4：全国、中央、省级、重点城市、特殊功能区及垂直机构 |
| B4 | 美国科技金融官方信号 | 科技创新与技术突破优先，同时覆盖科技政策、金融、股票、基金和宏观监管 |
| B5 | 跨板块总览 | 科研—顶刊—中国政策—美国官方信号之间的关系、机会、风险和矛盾 |

## 0.2 每日交付

每天发送 **5 封独立邮件**：

1. B1 研究前沿报告邮件；
2. B2 顶级期刊报告邮件；
3. B3 中国政策法规报告邮件；
4. B4 美国科技金融官方信号报告邮件；
5. B5 跨板块汇总报告邮件。

正式生产每天生成：

- 5 份完整报告；
- 5 封独立邮件；
- 4 个板块视频：B1、B2、B3、B4；
- B5 默认不生成日常视频；
- 每封邮件单独记录发送状态、消息哈希、报告版本、附件或视频链接状态。

30 天历史重放阶段为了压力测试，仍按已确认要求生成：

- 30 × 5 = **150 份报告**；
- 30 × 5 = **150 个视频**，包括历史 B5 跨板块视频；
- 30 × 5 = **150 份邮件渲染预览**；
- 历史重放邮件默认只渲染、不实际发送，避免产生 150 封历史邮件。

连续 2 个真实自然日生成并实际发送：

- 2 × 5 = **10 份报告**；
- 2 × 5 = **10 封真实邮件**；
- 2 × 4 = **8 个正式生产视频**。

最终验收至少包含：

- **160 份报告**；
- **158 个视频**；
- **160 份邮件渲染产物**；
- **10 次真实邮件发送记录**。

## 0.3 队列

```yaml
active_queue:
  max_items: 10000
  max_event_age_days: 365
  soft_quotas:
    B1_research_frontier: 3500
    B2_top_journals: 1500
    B3_china_policy: 3000
    B4_us_official: 2000
```

说明：

- 10,000 是活跃 `Event` 或 `ThemeCluster` 的上限，不是数据库历史上限；
- 超过 12 个月的事件退出活跃队列，但文档、版本、关系和证据不删除；
- 配额是可借用的软配额；
- 单一来源默认不得长期占据本板块活跃队列的 40% 以上；
- 任何淘汰、降级、合并、阻断都必须保留原因和历史记录，不能静默消失。

## 0.4 成本与 API

```yaml
cost_policy:
  paid_data_api_allowed: false
  undocumented_private_endpoint_allowed: false
  paywall_bypass_allowed: false
  paid_cloud_compute_allowed: false
  free_official_api_allowed: true
  preferred_access_order:
    - official_rss_atom
    - official_oai_pmh
    - official_html_archive
    - official_xml_csv_json_bulk
    - free_keyless_official_api
    - free_keyed_official_api
    - controlled_html_fetch
```

Codex 不得要求你逐个数据源手动配置 API。

只有在以下条件全部满足时，才允许要求一次性人工操作：

1. 官方 RSS、OAI、网页、批量文件均无法满足；
2. API 官方、免费且条款允许；
3. 密钥确实不可由 Codex 自动获取；
4. Codex 将所有此类密钥合并成一份一次性清单；
5. 未配置该密钥时，系统仍有明确降级路径，不得整体停摆。

---

# 1. 当前仓库基线与首要修复

当前仓库已经具备较完整的治理基础，包括：

- `docs/governance/MODEL_SPEC.md`
- `docs/governance/DEVELOPMENT_LEDGER.md`
- `docs/governance/DELIVERY_PLAN.md`
- `docs/governance/STATUS.md`
- `docs/governance/OWNER_STATUS.md`
- `docs/governance/TRACEABILITY_MATRIX.csv`
- `docs/governance/model_registry.yaml`
- `docs/governance/formula_registry.yaml`
- `docs/governance/parameter_registry.csv`
- `docs/governance/delivery_tasks.yaml`
- `docs/phase_records/`
- `docs/pursuing_goal/06_PURSUING_GOAL_READY_PROMPT.md`

现有实现已经包含 arXiv 适配、确定性评分、Claim Ledger、报告/TTS/视频 dry-run、SMTP 和 Release 边界、生产预检、计划任务、试运行证据等模块，但目前仍以 arXiv 为唯一实际内容源。

Codex 必须先完成以下治理校准，不得直接堆叠新爬虫：

1. 校准 `VERSION`、`pyproject.toml`、`CHANGELOG.md`、`STATUS.md`、`OWNER_STATUS.md` 和模型注册表；
2. 将旧的“Phase 1—11 仅 arXiv”目标迁移为本文件定义的多源目标；
3. 保留现有模型、公式、参数和开发记录，不覆盖历史；
4. 新需求必须使用新的稳定 Requirement ID、Feature ID、Task ID；
5. 现有 `PLANS.md` 若仍显示旧阶段，必须升级为当前多源路线；
6. 不允许创建第二套互相漂移的治理体系；
7. 生成的人类页面必须由事实源自动生成，CI 检查漂移。

---

# 2. 人类只需要编辑 1 个文件、查看 4 个文件

## 2.1 唯一人工控制文件

```text
arxiv-daily-push/config/owner_controls.yaml
```

你只需要通过这个文件修改：

- 板块启停；
- 来源启停和来源权重；
- 行业、主题、机构、公司、资产偏好；
- 三套领域评分权重；
- 跨板块排序权重；
- 队列容量、时间窗和软配额；
- 报告、邮件和视频开关；
- 来源采集频率；
- 本机资源上限；
- 历史重放和生产模式；
- Codex 每周、半月迭代权限。

敏感信息不得写入该文件。SMTP 密码、GitHub Token、Codex 登录态等只能保存在操作系统凭据库、受保护环境变量或本机秘密文件中。

## 2.2 四个人类查看文件

| 文件 | 用途 |
|---|---|
| `docs/owner/OWNER_CONSOLE.md` | 当前运行状态、今日五封邮件、阻断项、资源压力、需要人工处理的最少事项 |
| `docs/owner/SOURCE_CATALOG.md` | 全部来源、板块、机构、行业、采集方式、权重、频率、健康状态 |
| `docs/owner/MODEL_AND_QUEUE.md` | 三套评分卡、跨板块公式、队列规则、当前参数和参数变更影响 |
| `docs/owner/CONTENT_LEDGER.csv` | 已讲、简要提及、待讲、降级、淘汰、阻断、报告、视频和邮件状态 |

这些文件均由代码和配置自动生成，不直接手工修改。

## 2.3 你不需要日常查看的机器治理文件

现有 `docs/governance/` 文件继续作为审计和 Codex 开发事实源，由系统自动维护。你日常只看 `docs/owner/`。

---

# 3. `owner_controls.yaml` 建议结构

以下内容必须由 Codex生成可用版本，并配套 JSON Schema、注释、校验命令和影响预览。

```yaml
schema_version: 1

project:
  display_name: "Multi-Source Daily Intelligence Push"
  display_timezone: "Australia/Sydney"
  production_enabled: false
  production_auto_enable_after_acceptance: true

cost_policy:
  paid_data_api_allowed: false
  paid_cloud_compute_allowed: false
  free_official_api_allowed: true
  free_api_key_requires_owner_approval: true
  undocumented_endpoint_allowed: false
  paywall_bypass_allowed: false

runtime:
  deployment_mode: local_native
  scheduler_mode: os_native
  offline_policy: catch_up_on_next_start
  wake_from_sleep: true
  run_on_battery: false
  interactive_cpu_limit_percent: 50
  background_cpu_limit_percent: 80
  max_fetch_concurrency: 6
  max_browser_concurrency: 1
  browser_fetch_default: false
  min_free_disk_gb: 120
  emergency_free_disk_gb: 40
  max_temp_cache_gb: 20
  max_parallel_report_jobs: 1
  max_parallel_video_jobs: 1

intelligence_provider:
  paid_openai_api_allowed: false
  priority:
    - codex_cli_chatgpt_auth
    - local_model
    - deterministic_degraded
  fail_if_no_high_quality_provider: true
  local_model_autodetect: true
  unload_local_model_after_minutes: 5
  max_context_tokens: auto
  chunk_and_retrieve_required: true

boards:
  B1:
    enabled: true
    name: "研究前沿"
  B2:
    enabled: true
    name: "顶级期刊"
  B3:
    enabled: true
    name: "中国政策法规"
  B4:
    enabled: true
    name: "美国科技金融官方信号"
  B5:
    enabled: true
    name: "跨板块总览"

email:
  enabled: true
  recipients:
    - "linzezhang35@gmail.com"
  split_mode: five_independent_messages
  send_order:
    - B1
    - B2
    - B3
    - B4
    - B5
  historical_replay_send: false
  attach_markdown_report: true
  attach_mobile_video_when_size_allows: true
  max_attachment_mb: 20
  require_message_hash: true
  retry_count: 3
  cross_board_waits_for:
    - B1
    - B2
    - B3
    - B4

video:
  daily_enabled_boards:
    - B1
    - B2
    - B3
    - B4
  daily_cross_board_video: false
  historical_replay_video_boards:
    - B1
    - B2
    - B3
    - B4
    - B5
  keep_master_locally: true
  make_mobile_copy: true
  delete_intermediate_after_success: true

queue:
  max_active_items: 10000
  max_event_age_days: 365
  source_share_cap_per_board: 0.40
  soft_quotas:
    B1: 3500
    B2: 1500
    B3: 3000
    B4: 2000

scoring:
  research:
    relevance: 22
    novelty: 16
    evidence_quality: 16
    technical_breakthrough: 16
    conversion_economic_value: 14
    impact_scale: 8
    timeliness_version_change: 5
    diversity_coverage: 3

  china_policy:
    authority_legal_effect: 18
    policy_delta: 16
    technology_industry_relevance: 16
    economic_impact: 14
    scope: 10
    urgency: 10
    regional_relevance: 8
    actionability: 5
    completeness_confidence: 3

  us_official:
    innovation_breakthrough: 20
    regulatory_market_impact: 18
    authority_evidence: 14
    novelty_delta: 14
    entity_asset_scope: 12
    urgency: 10
    commercialization: 8
    actionability: 4

  cross_board:
    normalized_quality: 40
    cross_board_linkage: 20
    decision_impact: 15
    urgency: 10
    confidence: 10
    diversity: 5

  queue_priority:
    quality: 55
    event_delta: 15
    urgency: 10
    cross_board_linkage: 10
    waiting_credit: 5
    source_balance: 5

us_attention_budget:
  innovation_breakthrough: 35
  finance_market_macro: 30
  technology_policy_industry_rules: 20
  cross_agency_legal_backbone: 15

source_defaults:
  required_tier_weight: 1.00
  important_tier_weight: 0.90
  extended_tier_weight: 0.75
  max_host_requests_per_minute: 10
  request_timeout_seconds: 30
  max_retries: 3

source_overrides: {}

interest_profile:
  preferred_industries:
    - artificial_intelligence
    - semiconductors
    - biotechnology
    - healthcare
    - finance
    - capital_markets
    - funds
    - advanced_manufacturing
    - energy
    - digital_economy
  preferred_entities: []
  preferred_topics: []
  negative_keywords: []

iteration:
  weekly_diagnostic_enabled: true
  weekly_codex_pr_enabled: true
  biweekly_parameter_review_enabled: true
  auto_merge: false
  max_one_issue_per_pr: true
  historical_ab_test_days: 30
```

## 3.1 修改后的自动反馈

每次修改 `owner_controls.yaml`，CI 或本地命令必须输出：

- Schema 是否通过；
- 每组权重是否合计为 100；
- 哪些来源或板块状态变化；
- 过去 30 天重放中排名变化最大的项目；
- 新进入队列和退出队列的数量；
- 五封邮件内容覆盖的预期变化；
- 资源占用预估变化；
- 可回滚的配置版本号。

建议命令：

```bash
adp owner validate
adp owner preview-impact --days 30
adp owner render-docs
```

---

# 4. 功能清单

| Feature ID | 功能 | 完成定义 |
|---|---|---|
| F-001 | 治理一致性 | 版本、状态、任务、模型、参数和文档无漂移 |
| F-002 | 人工控制面 | 只编辑一个 YAML，自动生成四个人类查看文件 |
| F-003 | 需求追踪 | Requirement → Config → Function → Test → Artifact 全链追踪 |
| F-010 | 来源注册表 | 每个来源具备稳定 ID、板块、行业、方式、频率、权重和健康状态 |
| F-011 | 免费访问策略 | 禁止付费 API，优先 RSS/OAI/官方网页/批量文件 |
| F-012 | 来源健康检查 | 抓取成功、无更新、降级、阻断均有记录 |
| F-013 | C0—C4 来源生成 | 中央、省级、24 城市和特殊功能区自动生成和校验 |
| F-020 | 统一连接器 SDK | RSS、Atom、OAI、HTML、PDF、XML、CSV、JSON、免费 API |
| F-021 | 主机限流与缓存 | 按主机限流、ETag/Last-Modified、重试和断点续跑 |
| F-022 | 许可与 robots 治理 | 来源条款、许可、全文边界和抓取策略可审计 |
| F-030 | 本地数据库 | SQLite WAL + FTS5，支持文档、版本、事件、关系、队列和状态 |
| F-031 | 原始证据存储 | SHA256 内容寻址、压缩、不可变原始记录 |
| F-032 | 统一文档/事件模型 | Document、Version、Event、Entity、Relation 分离 |
| F-033 | 去重和身份解析 | DOI、PMID、arXiv ID、文号、FR Doc、CIK 等对齐 |
| F-034 | 版本关系图 | 修订、替代、撤回、发表、生效、废止、实施和解释 |
| F-035 | Taxonomy Bridge | 学科、MeSH、产业、政策、司法辖区和资产标签映射 |
| F-040 | 三套领域评分卡 | 研究、中国政策、美国官方信号独立评分并可解释 |
| F-041 | 顶刊 Profile | 原始研究、综述、社论、新闻、更正、撤回分开处理 |
| F-042 | 跨板块排序 | 分位数校准、跨板块关系、影响、紧迫性和多样性 |
| F-043 | 10,000 条队列 | 12 个月时间窗、软配额、淘汰、重激活和等待信用 |
| F-044 | 状态和原因账本 | 已讲、未讲、降级、淘汰、阻断均有原因和历史 |
| F-050 | Claim Ledger | 关键结论绑定原始证据、定位、置信度和事实类型 |
| F-051 | 五份报告 | 四板块详细报告 + 跨板块总览 |
| F-052 | 五封邮件 | 每个板块一封，跨板块一封，独立发送和重试 |
| F-053 | 四个日常视频 | B1—B4；历史重放阶段 B1—B5 全部视频 |
| F-054 | 文本优先降级 | 视频失败不阻断报告；邮件显示降级原因 |
| F-060 | 本地计划任务 | 电脑开机/唤醒后自动运行、错过任务补跑 |
| F-061 | Watchdog | 心跳、锁、卡死检测、恢复、单实例和重试 |
| F-062 | 资源治理 | CPU、RAM、显存、磁盘、缓存和温度压力记录 |
| F-063 | 本地备份 | 数据库、配置、Manifest 和报告索引备份 |
| F-070 | 30 天历史重放 | 30 个独立 as-of 日，禁止未来信息泄漏 |
| F-071 | 2 天真实运行 | 两个真实自然日、10 封真实邮件、8 个日常视频 |
| F-072 | 生产验收 | 所有门禁通过后自动进入 DAILY_OPERATION |
| F-080 | 每周 Codex 诊断 | 一个问题、一个 PR、人工合并 |
| F-081 | 半月参数复审 | 30 天 A/B 重放、展示排名变化、人工批准 |
| F-082 | 防需求漂移 | Codex 不得自行改变权重、来源、队列、成本和发布门禁 |

---

# 5. 来源清单与编号

## 5.1 统一来源字段

每个来源必须具备：

```yaml
source_id:
board_id:
source_group:
display_name:
official_organization:
jurisdiction:
source_type:
industries:
topics:
authority_tier:
source_weight:
access_methods:
primary_method:
fallback_methods:
api_cost:
api_key_required:
terms_status:
robots_status:
license_scope:
schedule:
historical_replay_method:
rate_limit:
health_status:
last_success_at:
last_change_at:
consecutive_failures:
parser_version:
owner_override:
```

## 5.2 稳定编号

```text
RF-###              研究前沿
TJ-###              顶级期刊

CN-C0-###           全国权威主干
CN-C1-###           中央机关与重点职能部门
CN-C2-<REGION>-###  省级行政区域
CN-C3-<CITY>-###    重点城市
CN-C4-<AREA>-###    自贸区、高新区、开发区、垂直机构

US-TA-###           科技创新与技术突破
US-FM-###           金融、股票、基金、宏观
US-TP-###           科技政策和产业规则
US-LG-###           跨机构法律主干
```

编号一经分配不得复用。

---

# 6. B1 研究前沿来源

| 初始 ID | 来源 | 角色 | 优先方式 | 行业/领域 |
|---|---|---|---|---|
| RF-001 | arXiv | 综合预印本、分类与版本源 | RSS、OAI-PMH、官方列表 | AI、计算机、数学、物理、量化金融 |
| RF-002 | TechRxiv | 工程、电气、电子和计算技术预印本 | RSS、官方列表 | 工程、通信、芯片、计算 |
| RF-003 | bioRxiv | 生命科学预印本 | RSS、免费官方接口 | 生物、基因、神经、药物 |
| RF-004 | medRxiv | 医学健康预印本 | RSS、免费官方接口 | 医学、临床、公共卫生 |
| RF-005 | ChemRxiv | 化学和材料预印本 | RSS、官方列表 | 化学、材料、能源 |
| RF-006 | SSRN | 社科、法律、金融和经济工作论文 | 官方提醒、低频官方页面 | 金融、法律、经济、商业 |
| RF-007 | EarthArXiv | 地球与环境科学预印本 | RSS、官方列表 | 气候、地学、环境、能源 |
| RF-008 | ChinaXiv | 中国预印本和中文研究成果 | 官方列表、检索页、公开 PDF | 中文科研、多学科 |
| RF-009 | PubMed | 生物医学权威索引 | 保存检索 RSS、免费 E-utilities | 医学、生物、药物 |
| RF-010 | Europe PMC | 生物医学索引、开放全文和资助关系 | 订阅、免费 REST、Bulk | 医学、生物、开放证据 |

规则：

- PubMed 和 Europe PMC 通常作为索引和增强源，不重复生成原始论文记录；
- DOI、PMID、arXiv ID、正式期刊发表关系进入同一 CanonicalDocument；
- SSRN 必须低频、缓存、条款检查，不得逆向私有接口；
- PDF 只在许可允许且确实需要证据提取时下载；
- OCR 只用于无文本层扫描件。

---

# 7. B2 顶级期刊来源

| 初始 ID | 来源 | 优先方式 | 重点类型 |
|---|---|---|---|
| TJ-001 | Nature 主刊 | 官方 RSS、文章列表、免费 DOI 元数据 | Article、Review、News、Editorial、Correction、Retraction |
| TJ-002 | Science 主刊 | 官方 RSS、内容页、免费 DOI 元数据 | Research Article、Report、Review、Perspective、Editorial、Correction |
| TJ-003 | The Lancet 主刊 | 官方 RSS、Online First、PubMed/Europe PMC | Article、Review、Commission、Editorial、Correspondence、Correction |

硬边界：

- 首期只启用主刊，不自动扩展全部子刊；
- 文章类型必须参与评分 Profile；
- 新闻和社论可作为趋势信号，不能冒充原始研究；
- 更正、撤回和表达关注属于强制事件；
- 不绕过订阅墙，不批量保存无许可全文。

---

# 8. B3 中国政策法规来源：C0—C4

## 8.1 C0 全国权威主干

至少包括：

- 国家法律法规数据库；
- 全国人大及其常委会法律、决定、草案、审议文件；
- 国务院政策文件库；
- 国务院公报；
- 中央公开党内法规与党内制度库；
- 最高人民法院；
- 最高人民检察院；
- 原始发文机关正式文件和附件。

## 8.2 C1 中央机关与重点职能部门

必须覆盖：

### 党务、治理与监督

- 中共中央和中央办公厅公开文件；
- 中央纪委国家监委；
- 中央组织部；
- 中央宣传相关公开机构；
- 中央网信办；
- 中央政法委；
- 党内法规制度来源。

### 宏观、科技、产业、金融和市场

- 国家发展改革委；
- 科技部；
- 工业和信息化部；
- 财政部；
- 中国人民银行；
- 国家金融监督管理总局；
- 中国证监会；
- 国家外汇管理局；
- 商务部；
- 海关总署；
- 国家税务总局；
- 国家统计局；
- 市场监管总局；
- 国家知识产权局；
- 国务院国资委；
- 国家数据局；
- 国家能源局；
- 国家卫生健康委；
- 国家药监局；
- 生态环境部；
- 教育部；
- 人力资源和社会保障部；
- 自然资源部；
- 住房城乡建设部；
- 交通运输部；
- 农业农村部；
- 应急管理部；
- 其他具有正式政策发布职责的国务院部门和直属机构。

## 8.3 C2 全部省级行政区域

首期要求建立并启用：

### 直辖市

- 北京；
- 天津；
- 上海；
- 重庆。

### 省

- 河北、山西、辽宁、吉林、黑龙江；
- 江苏、浙江、安徽、福建、江西、山东；
- 河南、湖北、湖南、广东、海南；
- 四川、贵州、云南、陕西、甘肃、青海。

### 自治区

- 内蒙古；
- 广西；
- 西藏；
- 宁夏；
- 新疆。

### 特别行政区

- 香港；
- 澳门。

香港和澳门使用独立法律与政府网站 Profile。台湾不作为“中国政府部门来源”自动纳入本注册表。

每个省级行政区域至少注册：

- 党委和党委办公厅；
- 纪委监委；
- 人大及常委会；
- 政府、政府办公厅、政策库和政府公报；
- 高级人民法院；
- 检察院；
- 发改、科技、工信、财政、商务；
- 市场监管、金融监管、国资、税务；
- 数据管理、网信；
- 生态环境、卫健、药监、自然资源、应急；
- 自贸区、高新区和重点产业区。

## 8.4 C3 首批 24 个重点城市

```text
北京、上海、深圳、广州、
天津、重庆、
杭州、南京、苏州、合肥、
武汉、西安、成都、长沙、
无锡、东莞、佛山、珠海、沈阳、
宁波、青岛、厦门、大连、
郑州
```

每个城市强制注册以下来源族：

1. 市委及市委办公厅；
2. 市纪委监委；
3. 市人大及常委会；
4. 市政府、政府办公厅、政策库和政府公报；
5. 市级法院；
6. 市级检察院；
7. 发展改革；
8. 科技；
9. 工业和信息化；
10. 财政；
11. 商务；
12. 市场监管；
13. 数据管理或大数据部门；
14. 地方金融监管；
15. 国资监管；
16. 网信；
17. 税务；
18. 生态环境；
19. 卫生健康；
20. 药品监管相关机构；
21. 规划和自然资源；
22. 应急管理；
23. 高新区、自贸区、开发区；
24. 海关、港口、航运等适用机构。

## 8.5 C4 特殊功能区与垂直机构

围绕 C2 和 C3 自动发现并注册：

- 国家级新区；
- 自由贸易试验区；
- 国家级高新技术产业开发区；
- 国家级经济技术开发区；
- 综合保税区；
- 重点产业园区；
- 海关直属机构；
- 税务局；
- 中国人民银行分支机构；
- 国家金融监督管理总局地方监管局；
- 证监局；
- 知识产权保护中心；
- 药监分支和审评机构；
- 港口、航运和机场管理机构；
- 其他直接影响科技创新、产业、金融和市场的重要垂直派出机构。

C4 不允许人工逐个设置。Codex 必须通过官方目录、父级门户和结构化模板自动生成候选，再做域名、权威性和可访问性验证。

---

# 9. B4 美国科技金融官方信号来源

D2 的 FINRA、MSRB 等 SRO 不纳入启用来源。

## 9.1 US-TA：科技创新与技术突破，35%

- NSF；
- DARPA；
- ARPA-E；
- ARPA-H；
- DOE Office of Science；
- 美国国家实验室；
- NIH；
- NASA；
- NIST；
- USPTO；
- FDA；
- SBIR/STTR；
- IARPA。

重点事件：

- 新项目和重大资助；
- 技术突破和原型；
- 临床与监管里程碑；
- 专利和商业化；
- 国家实验室成果；
- 关键基础设施和前沿标准。

## 9.2 US-FM：金融、股票、基金和宏观，30%

- SEC / EDGAR；
- Federal Reserve；
- New York Fed；
- FRED；
- Treasury；
- Fiscal Data；
- OFAC；
- CFTC；
- OCC；
- FDIC；
- CFPB；
- OFR；
- FSOC；
- BEA；
- BLS；
- Census；
- EIA。

SEC 至少识别：

```text
8-K
10-K
10-Q
S-1
13D
13G
13F
Forms 3/4/5
N-PORT
N-CEN
```

## 9.3 US-TP：科技政策和产业规则，20%

- OSTP；
- NIST；
- BIS；
- FTC；
- FCC；
- CISA；
- Department of Commerce / CHIPS；
- DOE；
- FDA 指南；
- 其他与 AI、芯片、网络安全、标准、频谱、竞争和出口管制直接相关的官方来源。

## 9.4 US-LG：跨机构法律主干，15%

- Federal Register；
- Regulations.gov；
- GovInfo；
- Congress.gov；
- White House；
- OMB；
- GAO。

同一机构可能服务多个主题，但只能有一个连接器和一个原始记录，通过多标签映射到子板块，防止重复采集。

---

# 10. 数据库和统一文档/事件模型

## 10.1 本地存储默认方案

```text
data/
  adp.sqlite3
  raw/
    sha256/
  reports/
  media/
  manifests/
  backups/
  exports/
```

默认采用：

- SQLite 3；
- WAL 模式；
- FTS5 全文索引；
- 外键和事务；
- 内容寻址原始文件；
- JSON Schema；
- 可选 Parquet 分析快照；
- 不引入需要长期维护的 PostgreSQL，除非未来改成多机并发。

数据库、原始文档、邮件、报告和视频不得提交公共 Git。

## 10.2 核心对象

```text
SourceDefinition
FetchRun
RawRecord
CanonicalDocument
DocumentVersion
Event
Entity
Relation
ThemeCluster
Claim
EvidenceBinding
ScoreSnapshot
QueueEntry
ReportArtifact
EmailArtifact
MediaArtifact
RunManifest
DevelopmentIteration
```

## 10.3 关键区别

```text
Document = 长期内容身份
Version  = 某一不可变版本
Event    = 某一时间发生的发布、修改、生效、撤回等变化
Queue    = 对 Event 或 ThemeCluster 排序
Report   = 对选中主题进行证据化分析
Email    = 报告的发送与交付状态
```

## 10.4 必须保存的时间

```yaml
published_at:
updated_at:
effective_at:
expires_at:
deadline_at:
retrieved_at:
observed_at:
known_at:
as_of_at:
```

历史重放必须使用 `known_at` 和 `as_of_at`，禁止使用未来才出现的版本、发表关系、修订或执行结果。

---

# 11. 版本关系图

至少支持：

```text
VERSION_OF
REPLACES
SUPERSEDES
AMENDS
REPEALS
CORRECTS
WITHDRAWS
RETRACTS
PUBLISHED_AS
CITES
SUPPORTS
CONTRADICTS
FUNDED_BY
ASSOCIATED_TRIAL
ASSOCIATED_PATENT
COMMERCIALIZED_BY
IMPLEMENTS
INTERPRETS
ENFORCES
RESPONDS_TO
AFFECTS_ENTITY
AFFECTS_SECTOR
AFFECTS_ASSET
SAME_TOPIC_AS
DERIVED_FROM
```

关系触发行为：

- 预印本正式发表：重新评分并激活；
- 征求意见稿转正式文件：提升法律效力并激活；
- 政策出现实施细则：更新影响和地区；
- 文件修改、废止或失效：更新状态；
- 论文撤回或重大更正：阻断旧结论并生成更正任务；
- 研究与基金、专利、临床、监管形成链路：提高跨板块关联分。

---

# 12. 评分模型

## 12.1 研究证据卡

```text
相关性 22
前沿性/新颖性 16
证据质量 16
技术突破 16
转化和经济价值 14
影响规模 8
时效和版本变化 5
多样性和覆盖 3
合计 100
```

B1 和 B2 使用同一母卡，但采用不同 Profile：

- preprint；
- top_journal_original_research；
- review_meta_analysis；
- editorial_news；
- correction_retraction。

## 12.2 中国政策卡

```text
发布机关和法律效力 18
政策变化幅度 16
科技与产业相关性 16
经济影响 14
覆盖范围 10
生效、截止和执行紧迫性 10
区域相关性 8
可行动性 5
信息完整性和置信度 3
合计 100
```

## 12.3 美国官方信号卡

```text
技术突破和创新相关性 20
监管或市场影响 18
来源权威与证据质量 14
新颖性和变化幅度 14
公司、基金、资产和行业范围 12
时效、截止和执行窗口 10
商业化和经济转化 8
可行动性 4
合计 100
```

## 12.4 统一质量修正

```text
base_score
= Σ(weight_i × normalized_signal_i)

quality_score
= base_score
× confidence_factor
× completeness_factor
× source_health_factor
```

每个条目必须保存：

- 原始信号；
- 归一化信号；
- 权重；
- 每个维度贡献；
- 置信度修正；
- 完整性修正；
- 来源健康修正；
- 硬门禁；
- 最终分数；
- 参数版本；
- 模型版本；
- 代码 commit。

## 12.5 跨板块排序

```text
normalized_quality
= 0.60 × board_percentile
+ 0.40 × source_percentile
```

```text
portfolio_score
= 0.40 × normalized_quality
+ 0.20 × cross_board_linkage
+ 0.15 × decision_impact
+ 0.10 × urgency
+ 0.10 × confidence
+ 0.05 × diversity
```

约束：

- 四个板块有合格内容时，每个板块至少有一个主主题；
- B5 单一板块默认不超过 40%；
- 生效、截止、撤回等重大事件允许 override，但必须记录理由；
- 同一主题先聚类再排序；
- 反证、矛盾和负面结果不得被热度模型吞掉；
- 不设置固定“只讲前 N 篇”，深度主题进入正文，其余合格内容进入附录和队列。

---

# 13. 队列状态和“已讲/未讲”账本

## 13.1 生命周期

```text
DISCOVERED
NORMALIZED
LINKED
SCORED
ELIGIBLE
SELECTED_BOARD
SELECTED_CROSS_BOARD
GENERATING
GENERATED
EMAIL_PENDING
EMAILED
MONITORING
ARCHIVED
```

异常状态：

```text
NEEDS_REVIEW
DOWNGRADED
EVICTED_CAPACITY
EVICTED_AGE
MERGED_DUPLICATE
SUPERSEDED
RETRACTED
WITHDRAWN
BLOCKED_EVIDENCE
BLOCKED_LICENSE
BLOCKED_SOURCE
FAILED_RETRYABLE
FAILED_TERMINAL
```

## 13.2 人类可读状态

| 人类状态 | 机器状态 |
|---|---|
| 已深度讲解 | `EXPLAINED_FULL` |
| 已简要提及 | `MENTIONED` |
| 待讲 | `QUEUED` |
| 正在生成 | `SELECTED` / `GENERATING` |
| 已降级 | `DOWNGRADED` |
| 容量淘汰 | `EVICTED_CAPACITY` |
| 超期淘汰 | `EVICTED_AGE` |
| 重复合并 | `MERGED_DUPLICATE` |
| 被新版本替代 | `SUPERSEDED` |
| 被撤回 | `RETRACTED` |
| 证据不足 | `BLOCKED_EVIDENCE` |
| 许可阻断 | `BLOCKED_LICENSE` |
| 来源失败 | `BLOCKED_SOURCE` |
| 已归档 | `ARCHIVED` |

## 13.3 CONTENT_LEDGER 字段

```text
item_id
document_id
event_id
theme_cluster_id
board_id
source_id
title
event_date
industry_tags
current_score
current_rank
previous_score
previous_rank
queue_state
explanation_state
reason_code
reason_detail
report_id
report_file_state
report_path
email_id
email_state
email_sent_at
video_id
video_file_state
video_path
model_version
parameter_version
source_registry_version
run_id
first_seen_at
last_updated_at
```

任何内容不得静默删除。所有状态变化追加写入：

```text
data/events/content_events.jsonl
```

---

# 14. 报告和五封邮件合同

## 14.1 四份板块报告

统一结构：

1. 结论和关键变化；
2. 来源覆盖和健康状态；
3. 本日重点事件和主题；
4. 深度专业解释；
5. 证据、反证和不确定性；
6. 版本与关系图；
7. 对项目、行业、公司、资产或政策的影响；
8. 行动建议和观察事项；
9. 队列新增、升级、降级和淘汰；
10. 引用、原始来源和运行证据。

## 14.2 跨板块报告

1. 四板块核心结论；
2. 跨来源主题聚类；
3. 科研到产业和商业化传导；
4. 顶刊验证、修正或否定；
5. 中国与美国政策趋同和分化；
6. 公司、基金、股票、行业和宏观影响；
7. 机会—风险矩阵；
8. 12 个月观察清单；
9. 未解决矛盾和待核实问题；
10. 四封板块邮件的报告 ID 和状态。

## 14.3 邮件主题

```text
[ADP][B1][YYYY-MM-DD] 研究前沿日报
[ADP][B2][YYYY-MM-DD] 顶级期刊日报
[ADP][B3][YYYY-MM-DD] 中国政策法规日报
[ADP][B4][YYYY-MM-DD] 美国科技金融官方信号日报
[ADP][B5][YYYY-MM-DD] 跨板块总览
```

## 14.4 邮件内容

每封邮件必须包括：

- 结论优先摘要；
- 完整报告正文或高密度 HTML；
- Markdown 报告附件；
- B1—B4 的视频访问方式；
- 来源覆盖和降级警告；
- 报告、模型、参数和 Run ID；
- “已讲/未讲/降级/淘汰”数量；
- 本机完整产物路径；
- 发送哈希和重试状态。

不限制报告字数和视频时长。质量门禁基于证据覆盖、逻辑完整、专业深度和不确定性，而不是长度。

邮件过大时：

1. 保留高密度 HTML 正文；
2. 附加完整 Markdown；
3. 视频生成 Master 和移动版；
4. 移动版小于配置上限时作为附件；
5. 超过上限时使用已配置的私有交付适配器；
6. 不得把私人视频默认发布到公共 GitHub Release。

---

# 15. 抓取频率与运行水位线

## 15.1 初始频率

| 来源族 | 初始频率 |
|---|---|
| 研究预印本 | 每 6 小时 |
| Nature、Science、Lancet | 每 6 小时 |
| 中国中央、省级、城市 | 10:30、17:30 Asia/Shanghai，21:00 补抓 |
| 美国法律主干 | 07:00 America/New_York |
| 美国科技、创新、金融 | 09:30、16:30、21:30 America/New_York |
| Watchdog | 每 30 分钟 |
| 资源和来源健康 | 每小时 |
| Codex 周诊断 | 每周一次 |
| Codex 参数复审 | 每 14 天一次 |

## 15.2 本地调度设计

操作系统只需要运行少量任务：

```text
adp tick            每 30 分钟
adp watchdog        每 30 分钟，错开 5 分钟
adp backup          每日一次
adp weekly-review   每周一次
adp biweekly-review 每 14 天一次
```

`adp tick` 根据 IANA 时区和来源计划决定哪些来源到期，不需要为每个来源建立一个操作系统任务。

## 15.3 水位线

某板块进入报告生成的条件：

- 必需来源均已产生成功、无更新、明确降级或明确阻断的终态记录；
- 解析、去重、版本、关系、评分和队列更新完成；
- 不等待永远失败的来源；
- 缺失来源必须在邮件中明确显示；
- 生成过程不使用固定总时长上限，但必须有 heartbeat、检查点和无进展超时；
- B5 必须等待 B1—B4 报告均进入成功或显式降级终态。

---

# 16. 本地长期自动运行方案

## 16.1 默认推荐：原生计划任务，而不是 Docker Desktop

理由：

- 无任务时几乎不占 RAM；
- 不需要常驻 Docker 虚拟机；
- 更容易唤醒、补跑和查看日志；
- 适合单机 SQLite；
- 避免 Docker Desktop 默认占用较多内存和磁盘；
- 当前项目本来就是 Python CLI 结构，适合 one-shot 任务。

## 16.2 Windows

Codex 必须自动创建并验证：

```text
ADP-Tick
ADP-Watchdog
ADP-Backup
ADP-Weekly-Codex
ADP-Biweekly-Codex
```

关键设置：

- 无论用户是否登录均可运行；
- 若错过计划，在下次开机或唤醒后尽快执行；
- 允许唤醒电脑；
- 同一任务已运行时不启动第二实例；
- 使用独立锁文件和数据库锁；
- 失败后按退避策略重试；
- 不在电池供电时执行重视频任务；
- 任务日志写入本机，不写秘密；
- 重启后自动恢复；
- 脚本路径和工作目录固定；
- 不依赖打开的终端窗口。

## 16.3 Linux

使用：

```text
systemd oneshot service
systemd timer
Persistent=true
```

在硬件支持时可使用 `WakeSystem=true`。任务错过后在开机时补跑。

## 16.4 macOS

使用 `launchd`，并提供错过任务补跑、单实例锁和恢复逻辑。需要定时从完全关机启动时，必须依赖系统电源计划或硬件能力。

## 16.5 电脑电源边界

- 电脑完全关机时，软件不能运行；
- 睡眠状态可尝试由系统计划任务唤醒；
- 若硬件或系统不允许唤醒，任务在下一次开机后补跑；
- 需要严格准点邮件时，电脑必须保持开机或睡眠可唤醒；
- 可选启用 BIOS/UEFI RTC 自动开机，但不作为软件默认假设。

## 16.6 GitHub 的职责

```text
GitHub-hosted Actions:
  - 单元测试
  - Schema 校验
  - 治理校验
  - PR 检查
  - 轻量静态分析

本地电脑:
  - 真实抓取
  - 数据库
  - 报告
  - 视频
  - SMTP
  - 私密日志和内容
  - 30 天重放
  - 2 天真实运行
```

不再要求本地生产必须依赖长期在线的 GitHub self-hosted runner。现有 self-hosted 工作流可以保留为可选兼容入口，但本地 OS 调度必须可以独立运行。

---

# 17. 本机资源占用与门禁

旧项目记录曾出现约 8 GiB RAM、约 25 GiB 可用磁盘的审计结果。该结果可能已经过期，Codex 必须重新检测，不能直接沿用。

## 17.1 资源阶段估算

| 阶段 | CPU | RAM | 显存 | 磁盘影响 |
|---|---:|---:|---:|---:|
| 空闲，原生计划任务 | 接近 0 | 接近 0—100 MB | 0 | 日志少量增长 |
| 抓取、解析、SQLite | 1—4 核 | 0.5—2 GB | 0 | 原始网页和附件增长 |
| 报告编排，远程 Codex 登录态 | 1—4 核 | 1—3 GB | 0 | 报告和中间 JSON |
| 本地轻量模型 | 4—12 核 | 8—24 GB | 5—16 GB 可选 | 模型常见数 GB 到数十 GB |
| 本地 TTS | 2—8 核 | 1—4 GB | 0—6 GB | 音频和模型缓存 |
| FFmpeg 视频 | 4—12 核 | 2—6 GB | 0—2 GB，可选硬件编码 | 视频和临时帧占主导 |
| 30 天历史重放 | 长时间高负载 | 峰值按上面阶段 | 取决于模型 | 最终视频和中间文件可能数十至数百 GB |

这些是工程预算，不是当前机器实测值。Codex 必须用实际 telemetry 覆盖估算。

## 17.2 推荐硬件档位

### 不使用本地大模型

最低建议：

```text
4 核 CPU
16 GB RAM
120 GB 可用 SSD
无需独立显卡
```

推荐：

```text
8 核 CPU
32 GB RAM
250 GB 可用 SSD
8 GB 显存可选
```

### 使用本地模型

建议至少：

```text
32 GB RAM
12 GB 显存
250 GB 可用 SSD
```

高质量大模型和长上下文通常需要更高显存或内存。系统必须使用分块、检索、摘要缓存和证据索引，不能把全部来源原文一次塞入超长上下文。

## 17.3 视频存储

150 个历史视频可能占用约 15—45 GB 的最终文件；渲染中间文件可能是最终文件的 2—5 倍。Codex 必须：

- 先检测可用磁盘；
- 设置临时缓存上限；
- 每个视频成功后删除中间帧；
- Master 与移动版分离；
- 为 30 天重放分批执行；
- 低于紧急磁盘阈值立即停止；
- 不把视频、音频、模型权重提交 Git。

如果实测仍只有 8 GB RAM 和 25 GB 可用磁盘，系统不得开始 150 视频的完整重放，必须给出最小 owner action，例如选择外置 SSD 或清理空间。

## 17.4 显存

- 使用 Codex CLI 的 ChatGPT 登录态进行远程推理时，本机 GPU 基本不参与模型推理；
- 本地模型会占用显存或系统内存；
- 量化 8B 模型本体通常约 5—8 GB，长上下文还会增加 KV cache；
- 本地模型必须在完成后卸载；
- 视频优先使用 FFmpeg CPU 或硬件编码，避免同时占用推理显存；
- 本地模型和视频渲染默认串行，防止显存峰值叠加。

## 17.5 资源保护

必须实现：

```yaml
resource_gates:
  max_cpu_percent_interactive: 50
  max_parallel_video_jobs: 1
  max_parallel_model_jobs: 1
  min_free_disk_gb: 120
  emergency_free_disk_gb: 40
  max_temp_cache_gb: 20
  stop_on_high_memory_pressure: true
  stop_on_thermal_pressure: true
  run_video_on_battery: false
```

---

---

# Part C｜两阶段开发计划、任务目的与晋升门禁

# Stage 1｜arXiv 单源完整纵向切片与生产验收

## Stage 1 Goal

建立一个真实、可迁移、可审计、可恢复的 arXiv 单源生产闭环：

```text
arXiv 发现
→ RawRecord
→ CanonicalDocument / DocumentVersion / Event
→ 去重和版本关系
→ 研究证据评分
→ 10,000 条队列逻辑
→ B1 报告
→ Claim Ledger
→ B1 邮件
→ B1 视频
→ CONTENT_LEDGER
→ RunManifest
→ 本地调度、备份和恢复
```

Stage 1 完成条件不是代码存在，而是：

```text
ARXIV_PRODUCTION_ACCEPTED
```

通过后，arXiv 单源必须进入稳定日常生产，并在 Stage 2 开发期间继续运行。

## Stage 1 迁移前代码窗口

### 资源硬门禁

当：

```yaml
migration:
  new_machine_ready: false
```

时，只允许：

```text
在线 arXiv 元数据最多 10 条
不下载全文 PDF
Raw 数据不超过 100 MB
临时数据不超过 2 GB
媒体 smoke 最长 30 秒、最高 480p
不下载大型本地模型或大型 TTS
不执行 30 日重放
不执行批量视频
不安装或启用正式生产 scheduler
不大规模抓取 B1 其他来源、B2、B3、B4
```

重测试只能标记：

```text
DEFERRED_UNTIL_NEW_MACHINE
```

不得标记 PASS。

### Stage 1 任务

| Task ID | 任务 | 目的 | 主要交付 | 验收门禁 |
|---|---|---|---|---|
| S1-01 | 最小范围只读审计 | 获取真实代码、治理、测试和风险图 | 文件图、功能图、数据流、测试图 | 不改代码；读取范围合规 |
| S1-02 | 治理校准与基线锁 | 消除 VERSION、状态、模型、参数和计划漂移 | 需求、功能、任务、测试、产物追踪 | 事实源一致；历史证据不覆盖 |
| S1-03 | 人工控制面 | 实现 1 改 4 看 | `owner_controls.yaml`、四个 owner 文件、Schema | 人工无需阅读 Python 即可控制核心参数 |
| S1-04 | 数据库与统一模型 | 建立可扩源的持久层 | SQLite WAL/FTS5、迁移、回滚、核心对象 | 幂等、唯一键、备份恢复、旧 arXiv 兼容 |
| S1-05 | Source Registry 与 arXiv Contract | 将 arXiv 从特例变为通用 Adapter | Registry、Connector 接口、fixture、bounded canary | 最多 10 条真实元数据；失败隔离 |
| S1-06 | 评分、队列与内容账本 | 配置化研究评分和 10,000 队列 | ScoreSnapshot、Queue、reason code、CONTENT_LEDGER | 确定性；第 10,001 条和 365 天边界通过 |
| S1-07 | 报告、Claim、邮件与媒体接口 | 完成 B1 交付代码边界 | B1 Markdown/HTML/JSON、Claim、邮件预览、媒体 smoke | 关键 Claim 绑定证据；低资源预算合规 |
| S1-08 | 调度、watchdog、备份与迁移代码 | 为新电脑准备长期运行 | scheduler 模板、锁、心跳、补跑、backup/restore、迁移脚本 | 旧电脑只 dry-run；安装/卸载可验证 |
| S1-09 | 低资源纵向集成 | 验证完整代码路径和迁移就绪 | 一次 bounded vertical slice、RunManifest、迁移包 | `VERTICAL_SLICE_CODE_READY` |

迁移前完成状态：

```text
VERTICAL_SLICE_CODE_READY
→ WAITING_FOR_NEW_MACHINE
```

此时必须停下重任务，输出：迁移清单、未执行测试、证据、资源风险、回滚和恢复步骤。

## Stage 1 新电脑验收窗口

只有人工设置：

```yaml
migration:
  new_machine_ready: true
```

且硬件审计通过后才解锁。日期到达本身不能自动解锁。

| Task ID | 任务 | 目的 | 验收门禁 |
|---|---|---|---|
| S1-10 | 新电脑 bootstrap | 检测 OS、CPU、RAM、GPU、显存、SSD、Python、Git、FFmpeg、TTS、Codex、浏览器、SMTP、SSL、电源和调度 | `NEW_MACHINE_BOOTSTRAPPED` |
| S1-11 | 本地生产部署 | 安装原生运行环境、秘密、路径、计划任务、备份和恢复 | 重启、补跑、单实例和卸载通过 |
| S1-12 | 迁移验证 | 迁移代码、配置、数据库和必要证据 | 哈希、迁移、回滚和数据完整性通过 |
| S1-13 | arXiv 30 日历史重放 | 用 30 个独立 as-of 日验证完整链路 | 30 报告、30 邮件预览、30 视频、未来泄漏 0 |
| S1-14 | arXiv 连续 2 日真实运行 | 验证真实网络、调度、SMTP 和视频 | 2 报告、2 真实邮件、2 视频 |
| S1-15 | arXiv 生产验收 | 建立稳定单源生产基线 | P0/P1=0，`ARXIV_PRODUCTION_ACCEPTED` |

Stage 1 完成后：

- arXiv 正式每日运行；
- Stage 2 使用独立 Feature Flag、分支或 worktree；
- 新来源失败不得停止 arXiv；
- 生产配置和开发配置隔离；
- 所有变更可一键回退到 arXiv-only profile。

# Stage 2｜逐来源、逐板块晋升与全系统生产验收

## Stage 2 Goal

在稳定 arXiv 生产之上，按来源和板块逐步完成全部 B1—B4，构建 B5、五封邮件、完整关系图、三套评分卡和最终全系统生产系统。

Stage 2 唯一入口：

```text
ARXIV_PRODUCTION_ACCEPTED
```

## 来源晋升状态机

```text
DISABLED
→ FIXTURE_READY
→ CONTRACT_TESTED
→ REPLAY_30_PASSED
→ SHADOW_48H_PASSED
→ BOARD_PRODUCTION
→ FULL_PRODUCTION
```

Shadow 期间可以真实抓取、保存、评分和模拟排名，但不得影响正式邮件、正式队列或正式视频。

每个来源或同构来源包必须具备：独立 Feature Flag、独立测试、独立回滚、独立来源健康和独立失败隔离。

## Stage 2 任务与 Wave

| Task ID | Wave | 范围 | 目的 | 晋升门禁 |
|---|---|---|---|---|
| S2-01 | 基础 | 来源晋升框架、生产隔离、跨源身份和关系 | 保证新增来源不破坏 arXiv | Feature Flag、Shadow、回滚和生产隔离通过 |
| S2-02 | 1A | bioRxiv、medRxiv、PubMed、Europe PMC | 建立生命医学多源和索引增强 | 每源 30 日＋48h Shadow |
| S2-03 | 1B | TechRxiv、ChemRxiv、EarthArXiv | 扩展工程、化学、地球科学 | 每源 30 日＋48h Shadow |
| S2-04 | 1C | SSRN、ChinaXiv | 接入高变化、高风险来源 | 条款、页面稳定性和明确降级终态；`B1_ACCEPTED` |
| S2-05 | 2 | Nature、Science、The Lancet | 建立顶刊证据层和文章 Profile | 30 日＋2 日板块验收；`B2_ACCEPTED` |
| S2-06 | 3 | 中国 C0、C1 | 建立全国与中央权威政策主干 | 法律状态、文号、原始机关和版本关系；`B3_C0_C1_ACCEPTED` |
| S2-07 | 4 | US-TA、US-LG、US-FM、US-TP | 科技创新优先并覆盖金融与法律 | 注意力预算和实体影响正确；`B4_ACCEPTED` |
| S2-08 | 核心交付 | B5、五封邮件、跨板块关系和水位线 | 形成核心五邮件生产版 | `CORE_FIVE_EMAIL_PRODUCTION_ACCEPTED` |
| S2-09 | 5 | 中国 C2、C3、C4 | 覆盖全部省级、24 城市和特殊功能区 | 模板化注册、自动发现和来源健康；`FULL_C0_C4_PRODUCTION_ACCEPTED` |
| S2-10 | 运营 | 备份、恢复、每周 PR、每 14 天参数 PR | 长期治理与低人工负担 | 自动诊断、人工合并、回滚通过 |
| S2-11 | Final-1 | 全系统 30 日历史重放 | 验证完整多源系统 | 150 报告、150 预览、150 视频 |
| S2-12 | Final-2 | 全系统连续 2 个真实日和生产切换 | 最终生产验收 | 10 报告、10 邮件、8 视频；`PRODUCTION_ACCEPTED` |

## 每个来源的统一门禁

```text
Connector Contract 通过
30 日来源级重放完成
48 小时真实 Shadow 完成
P0/P1 = 0
静默丢失 = 0
幂等 = 100%
关键 Claim 证据绑定 = 100%
条款、许可、robots、限流和历史可用性有记录
```

历史无法完整恢复时必须记录：

```yaml
as_of_fidelity: partial
backfill_reconstructed: true
reason: <明确原因>
```

不得用当前页面冒充历史状态。

## 每个板块的统一门禁

- 全来源均有成功、无更新、明确降级或明确阻断终态；
- 板块 30 日重放；
- 连续 2 个真实日；
- 报告、邮件、视频合同通过；
- 去重、关系、评分、队列和资源通过；
- owner 文件更新；
- 一键回退验证；
- 新板块失败不停止已稳定板块。

## 最终全系统门禁

历史 30 日：

```text
150 报告
150 邮件预览
150 视频
30 个独立 as_of_at
未来信息泄漏 0
重复发送 0
静默遗漏 0
关键 Claim 证据覆盖 100%
```

连续 2 个真实日：

```text
10 报告
10 封真实邮件
8 个正式日常视频
B5 水位线正确
全来源有明确终态
调度、恢复、备份、资源稳定
```

最终状态：

```text
PRODUCTION_ACCEPTED
→ DAILY_OPERATION
```

---

# Part D｜开发治理、自动迭代和禁止事项

## 每个 Task 的开发合同

每次只处理：

```text
一个 Task ID
一个主要目录范围
一个主要验收标准
一个 PR
```

Task 开始前必须输出：目标、非目标、读取文件、修改文件、测试命令、资源预算、风险、回滚、停止条件。

Task 完成后必须更新现有治理文件，记录真实命令、退出码、耗时、资源峰值、证据、Diff、风险、回滚和下一门禁。

## Codex 禁止自动修改

- 两份基线；
- 付费 API 与付费云禁令；
- 两阶段结构；
- 10,000 条和 365 天；
- 三套评分卡结构和冻结权重；
- 来源覆盖范围；
- C0—C4；
- 五份报告和五封邮件；
- 日常四视频、历史五视频；
- 收件人、秘密和权限；
- 生产门禁；
- 自动合并策略；
- 外部交易或执行行为。

## 公共仓库隐私

公共 Git 只保存：源码、配置模板、Schema、测试、脱敏状态、哈希和小型证据索引。

不得提交：SMTP 密码、GitHub Token、Codex auth、Cookie、声音样本、模型权重、数据库、完整私密报告、音频、视频或渲染缓存。

# 19. 每周和每半月 Codex 自动迭代

## 19.1 每周

```text
只读诊断
→ 来源健康
→ 解析器漂移
→ 抓取失败
→ 队列异常
→ 报告/邮件/视频缺失
→ 资源增长
→ 选择一个最高优先级问题
→ 创建一个 PR
→ 人工审查和合并
```

每周目录：

```text
artifacts/weekly/YYYY-Www/
  diagnostic.md
  source_health.csv
  parser_drift.csv
  scoring_distribution.csv
  queue_aging.csv
  resource_report.csv
  regression_report.json
  proposed_changes.yaml
  codex_task_prompt.md
  rollback_plan.md
```

## 19.2 每 14 天

```text
人工反馈
+ 过去 30 天排名
+ 已讲/未讲转化
+ 淘汰内容后续价值
+ 来源失败率
+ 板块覆盖
→ 新旧参数 30 天重放
→ 展示排名变化
→ 创建参数 PR
→ 人工批准后生效
```

## 19.3 Codex 禁止自动修改

- 付费 API 禁令；
- 10,000 条上限；
- 12 个月时间窗；
- C0—C4 覆盖目标；
- 五封邮件；
- 日常四视频、历史五视频；
- 三套评分卡结构；
- 生产发布门禁；
- 邮件收件人；
- 秘密和权限；
- 自动合并策略；
- 外部交易或执行行为。

---

# 20. Requirement ID 基线

| Requirement ID | 要求 |
|---|---|
| REQ-COST-001 | 禁止付费数据 API |
| REQ-COST-002 | 禁止付费云主机作为默认生产依赖 |
| REQ-SRC-001 | 四大板块和 B5 汇总 |
| REQ-SRC-002 | B1 十个研究来源 |
| REQ-SRC-003 | B2 三个顶刊主刊 |
| REQ-CN-001 | C0—C4 完整覆盖 |
| REQ-US-001 | 科技创新和技术突破优先 |
| REQ-US-002 | 删除 FINRA/MSRB 等 D2 SRO |
| REQ-DATA-001 | 本地数据库、原始证据、版本和关系图 |
| REQ-MODEL-001 | 三套领域评分卡 |
| REQ-RANK-001 | 跨板块排序和可解释贡献 |
| REQ-QUEUE-001 | 活跃队列最大 10,000 |
| REQ-QUEUE-002 | 活跃事件最大年龄 12 个月 |
| REQ-REPORT-001 | 每天五份完整报告 |
| REQ-EMAIL-001 | 每天五封独立邮件 |
| REQ-VIDEO-001 | 日常四视频、历史重放五视频 |
| REQ-TRACE-001 | 已讲/未讲/降级/淘汰全记录 |
| REQ-HUMAN-001 | 只编辑一个人工控制文件 |
| REQ-HUMAN-002 | 四个人类查看文件 |
| REQ-LOCAL-001 | 本地原生计划任务和补跑 |
| REQ-RESOURCE-001 | CPU/RAM/显存/磁盘/缓存保护 |
| REQ-REPLAY-001 | 30 个独立历史日完整流程 |
| REQ-LIVE-001 | 连续 2 个真实自然日 |
| REQ-CODEX-001 | 每周诊断 PR，人工合并 |
| REQ-CODEX-002 | 每半月参数 A/B PR |
| REQ-ACCEPT-001 | 通过后自动进入 DAILY_OPERATION |

---

# Part E｜集成测试与证据标准

# 集成测试与生产验收规范

> 本测试规范已经并入本 Master Task Pack，与两份只读基线共同生效。迁移前重测试可以延后，但不能删除、弱化或用 mock 标记为通过。

---

# 1. 测试层级

```text
T0 基线锁、治理和静态门禁
T1 配置、时间、状态单元测试
T2 Connector Contract
T3 数据库、迁移、备份和幂等
T4 评分、跨板块排序和队列
T5 报告、Claim、邮件和媒体
T6 调度、恢复和资源
T7 arXiv 30 日历史重放
T8 新来源 30 日重放＋48h Shadow
T9 板块级验收
T10 最终全系统 30 日＋2 日
```

测试模式：

| 模式 | 网络 | 重资源 | 生产影响 |
|---|---|---|---|
| fixture | 否 | 否 | 无 |
| bounded_canary | 最多 10 条元数据 | 否 | 无 |
| historical_replay | 是/缓存 | 是 | 历史邮件不发送 |
| shadow | 是 | 中 | 不影响正式排序/邮件 |
| live_acceptance | 是 | 是 | 真实发送 |
| daily_production | 是 | 是 | 正式运行 |

---

# 2. T0 基线和治理门禁

| Test ID | 测试 | 通过条件 |
|---|---|---|
| T-BASE-001 | 基线文件哈希 | 两份 SHA-256 与 `baseline_lock.yaml` 完全一致 |
| T-BASE-002 | 允许 Delta | 只有 D-001—D-004 被改变 |
| T-BASE-003 | 零回归矩阵 | 每个基线要求有 本文件位置、Task、Test、Artifact |
| T-BASE-004 | 执行顺序语义 | “迁移后执行”没有被解释成“取消” |
| T-BASE-005 | 最终验收语义 | 分阶段验收没有替代全系统 30＋2 |
| T-GOV-001 | 版本一致 | VERSION、pyproject、CHANGELOG、STATUS、OWNER_STATUS 一致 |
| T-GOV-002 | 需求追踪 | Requirement → Config → Function → Test → Artifact 100% |
| T-GOV-003 | 权重和 | 每组严格为 100 |
| T-GOV-004 | 成本禁令 | 无付费数据 API、付费云默认路径或付费 OpenAI API |
| T-GOV-005 | 未批准域名 | 新域名必须进入 Source Registry 和 PR |
| T-GOV-006 | 生成文档漂移 | 四个人工页面与事实源一致 |
| T-GOV-007 | 秘密扫描 | 无 SMTP 密码、Token、Cookie、Codex auth、私密数据库/报告/媒体 |
| T-GOV-008 | 迁移门禁 | `new_machine_ready=false` 时重任务无法启动 |
| T-GOV-009 | 资源门禁 | 迁移前预算不能通过 CLI 绕过 |
| T-GOV-010 | PR 边界 | 一个主要 Task ID、目录和验收标准 |

任一 T0 失败均阻断合并。

---

# 3. 迁移前资源预算测试

当 `new_machine_ready=false`：

```text
live_items <= 10
raw_storage <= 100 MB
temp_storage <= 2 GB
video_duration <= 30 seconds
video_height <= 480
no_full_pdf_download = true
no_large_model_download = true
no_30_day_replay = true
no_bulk_video = true
no_production_scheduler_install = true
no_mass_source_crawl = true
```

本应迁移后执行的测试必须标记：

```text
DEFERRED_UNTIL_NEW_MACHINE
```

不得标记 PASS。

---

# 4. 建议命令族

Codex 在只读审计后映射到仓库真实入口，不得虚构：

```bash
python -m pytest -q tests/governance tests/config
python -m pytest -q tests/unit
python -m pytest -q tests/connectors -k "arxiv or contract"
python -m pytest -q tests/data tests/migrations
python -m pytest -q tests/scoring tests/queue
python -m pytest -q tests/reporting tests/claims tests/email tests/media
python -m pytest -q tests/runtime tests/scheduler tests/resources
python -m pytest -q tests/integration -k "vertical_slice and low_resource"
python -m pytest -q tests/replay -k "as_of or no_future_leak or idempotent"
python -m pytest -q
```

真实命令、退出码、耗时和证据路径必须写入阶段记录。

---

# 5. T1 配置、时间和状态

## 配置

- 必填键缺失失败；
- 未知键失败；
- 权重越界或和不为 100 失败；
- 10,000/365/五封邮件/视频数量等冻结值变化必须人工批准；
- 敏感值不得写入 owner_controls；
- `new_machine_ready` 默认 false 且 Codex 不得自动改 true。

## 时间

- IANA 时区和 DST；
- published/updated/effective/expires/deadline/retrieved/observed/known/as_of 区分；
- 历史重放不能读取未来版本、正式发表、修订或执行结果；
- 365 天边界精确。

## 状态

每个状态有合法前驱、后继、事件、reason code 和人类说明；不得静默删除。

---

# 6. T2 Connector Contract

每个来源通过：

```text
discover 返回稳定 ID/cursor
fetch_metadata 保存原始响应和哈希
normalize 输出 Document/Version/Event
重复抓取幂等
限流、重试和超时可测
无更新是成功终态
parser 版本和 fixture 可追踪
条款、robots、许可存在
失败隔离单来源
外部提示注入被视为数据
```

arXiv 特定：ID/version、RSS/OAI 一致性、分类映射、修订关系、SSL/网络失败记录、canary 不超过 10 条。

---

# 7. T3 数据库和幂等

| Test ID | 测试 |
|---|---|
| T-DB-001 | 新库初始化 |
| T-DB-002 | Migration up/down |
| T-DB-003 | 旧 arXiv 数据兼容 |
| T-DB-004 | 外键和无孤儿记录 |
| T-DB-005 | 唯一键 |
| T-DB-006 | WAL 合法并发 |
| T-DB-007 | 事务失败无部分提交 |
| T-DB-008 | integrity_check |
| T-DB-009 | backup/restore 哈希一致 |
| T-DB-010 | Raw 内容寻址 |
| T-DB-011 | FTS 检索 |
| T-DB-012 | 同一 Run 重跑无重复 |

---

# 8. T4 模型、排序和 10,000 队列

评分：同输入同参数同分数；维度贡献可重算；来源权重不重复乘；缺失策略显式；硬门禁先于扣分；模型/参数/commit 可追溯。

队列：

| Test ID | 测试 |
|---|---|
| T-Q-001 | 10,000 条可表示 |
| T-Q-002 | 第 10,001 条确定性处理 |
| T-Q-003 | 365 天边界 |
| T-Q-004 | 3,500/1,500/3,000/2,000 软配额 |
| T-Q-005 | 空闲配额借用 |
| T-Q-006 | 单来源 40% 约束 |
| T-Q-007 | waiting credit |
| T-Q-008 | 新版本/正式发表重激活 |
| T-Q-009 | 撤回、替代和废止 |
| T-Q-010 | 所有淘汰有 reason code |
| T-Q-011 | CONTENT_LEDGER 可还原历史 |
| T-Q-012 | 同分稳定排序 |

最终阶段还需测试三套评分卡、顶刊 Profile、跨板块分位数和 B5 单板块 40% 约束。

---

# 9. T5 报告、Claim、五封邮件和视频

Claim 至少含：claim_id、report_id、文本、类型、证据、来源、定位、置信度、事实/推断、模型和 Run ID。

硬门禁：无原始源、法律状态不明、许可不清、解析过低、关键 Claim 无证据、原始哈希缺失时 fail closed。

报告：章节合同齐全；来源降级、队列变化、已讲/未讲可见；Markdown/HTML/JSON 一致；不因长度截断关键证据。

邮件：

- B1—B5 独立；
- B5 等待 B1—B4；
- Message-ID/业务哈希防重；
- 失败有状态和重试；
- 历史只渲染不发送；
- 真实两日发送 10 封；
- 收件人和秘密不进入 Git。

媒体：迁移前 stub/smoke；迁移后真实 TTS/视频、轨道/编码/时长、Master/移动版、中间文件清理、磁盘门禁、Claim 一致；视频失败不阻断文本邮件但必须降级可见。

---

# 10. T6 调度、恢复和资源

| Test ID | 测试 |
|---|---|
| T-RUN-001 | 单实例锁 |
| T-RUN-002 | 崩溃后锁恢复 |
| T-RUN-003 | heartbeat |
| T-RUN-004 | 无进展超时 |
| T-RUN-005 | 网络退避 |
| T-RUN-006 | 错过任务补跑 |
| T-RUN-007 | 重启恢复 |
| T-RUN-008 | 迁移前 scheduler dry-run |
| T-RUN-009 | 新电脑 scheduler 真实安装 |
| T-RUN-010 | uninstall/rollback |
| T-RES-001 | CPU 上限 |
| T-RES-002 | RAM 压力停止 |
| T-RES-003 | 磁盘最低阈值 |
| T-RES-004 | 临时缓存上限 |
| T-RES-005 | 视频并发为 1 |
| T-RES-006 | 模型与视频不叠加显存峰值 |
| T-RES-007 | 电池模式禁重视频 |
| T-RES-008 | 温度压力降级 |

资源不足必须 `BLOCKED_OWNER_ACTION`，不能自动删重要数据或降低质量。

---

# 11. T7 arXiv 30 日历史重放

每个日期产生：来源终态、Raw、Document/Version/Event、Score、Queue delta、B1 报告、Claim、邮件预览、视频、Manifest 和资源记录。

通过：

```text
30/30 日期有终态
未来信息泄漏 = 0
重复文档 = 0
无法解释的队列消失 = 0
关键 Claim 证据覆盖 = 100%
```

强制故障：网络、SSL、解析、视频、邮件渲染、进程重启、磁盘阈值、10,001、365 天。

---

# 12. T8 来源级 30 日＋48h Shadow

每个新来源在晋升前检查：真实发现量、失败和限流、解析漂移、重复率、版本关系、排名变化、队列影响、邮件模拟、资源增长、条款和密钥。

晋升门禁：

```text
P0/P1 = 0
静默丢失 = 0
幂等 = 100%
关键 Claim 证据绑定 = 100%
30 日来源重放完成
48 小时 Shadow 完成
```

历史不可恢复时必须明确 `as_of_fidelity: partial`，不得用当前页面冒充历史。

---

# 13. T9 板块级验收

每个板块完成后执行：

- 全来源终态；
- 板块 30 日重放；
- 连续 2 日生产；
- 报告、邮件、视频；
- 来源份额、去重、关系、队列和资源；
- 人工页面和回滚。

板块状态：B1_ACCEPTED、B2_ACCEPTED、B3_C0_C1_ACCEPTED、B4_ACCEPTED、B3_C2_C4_ACCEPTED。

---

# 14. T10 最终全系统验收

历史 30 日：150 报告、150 邮件预览、150 视频、30 独立 as_of_at、未来泄漏 0。

连续 2 日：10 报告、10 封真实邮件、8 视频、全来源终态、B5 水位线、资源和恢复证据。

完成状态：

```text
FULL_REPLAY_30_PASSED
FULL_LIVE_DAY_1_PASSED
FULL_LIVE_DAY_2_PASSED
PRODUCTION_ACCEPTED
DAILY_OPERATION
```

---

# 15. 缺陷等级和停止条件

| 等级 | 示例 | 行为 |
|---|---|---|
| P0 | 数据损坏、秘密泄漏、错误法律状态、重复真实发送 | 立即停止和回滚 |
| P1 | 静默漏抓、排序不确定、Claim 无证据、状态丢失 | 阻断晋升/发布 |
| P2 | 单来源失败且有明确降级、非关键媒体问题 | 隔离来源或文本优先 |
| P3 | UI/格式/性能优化 | 后续 PR |

停止：新电脑未准备、资源不足、需秘密/管理员、条款冲突、数据风险、必须付费、两日未完成或需求冲突。

---

# 16. 测试证据格式

```yaml
phase_id:
task_id:
git_commit:
baseline_hashes_verified:
config_version:
model_version:
source_registry_version:
commands:
  - command:
    exit_code:
    duration_seconds:
    result_artifact:
tests_passed:
tests_failed:
tests_deferred:
resource_peak:
  cpu_percent:
  ram_mb:
  vram_mb:
  temp_gb:
  disk_free_gb:
no_regression_matrix_updated:
known_risks:
rollback:
next_gate:
```

# Part F｜最终验收清单

# 22. 最终验收清单

- [ ] 现有治理无漂移；
- [ ] 一个 owner_controls.yaml 可控制全部关键参数；
- [ ] 四个人类查看文件自动生成；
- [ ] 四大来源板块和 B5 完整；
- [ ] B1 十个来源；
- [ ] B2 三个顶刊；
- [ ] B3 C0—C4；
- [ ] B4 科技创新优先且无 SRO；
- [ ] 免费来源策略；
- [ ] 本地 SQLite、原始证据和备份；
- [ ] 文档、版本、事件、关系图；
- [ ] 三套评分卡；
- [ ] 跨板块排序；
- [ ] 10,000 条、12 个月活跃队列；
- [ ] 已讲/未讲/降级/淘汰完整；
- [ ] 每天五份报告；
- [ ] 每天五封独立邮件；
- [ ] 每天四个视频；
- [ ] 30 天 150 报告、150 视频、150 邮件预览；
- [ ] 2 天 10 报告、10 封真实邮件、8 视频；
- [ ] 本地计划任务、唤醒、补跑、watchdog；
- [ ] CPU、RAM、显存、磁盘和缓存门禁；
- [ ] 每周 Codex PR；
- [ ] 每 14 天参数 PR；
- [ ] 人工合并；
- [ ] 生产自动切换；
- [ ] 最终状态 `PRODUCTION_ACCEPTED → DAILY_OPERATION`。

---

# Part G｜完整 Pursuing Goal Prompt

下面内容与 ZIP 内独立的 `FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_V4.txt` 完全一致。正常使用时直接发送独立 Prompt 文件即可。

```text
/goal

在 GitHub 仓库 `LinzeColin/CodexProject` 的 `arxiv-daily-push/` 项目中，读取我提供的压缩包，并以其中：

- `START_HERE_MASTER_TASK_PACK_TWO_STAGE_V4.md`
- `baseline/REFERENCE_OWNER_DECISIONS.rtf`
- `baseline/MULTISOURCE_LOCAL_PRODUCTION_TASKPACK_V1.md`

作为本次 Pursuing Goal 的完整需求、开发、测试和交付基线。

持续推进，直到最终状态：

```text
PRODUCTION_ACCEPTED
→ DAILY_OPERATION
```

本项目只有两个顶层阶段：

```text
Stage 1：arXiv 单源完整纵向切片与生产验收
Stage 2：逐来源、逐板块晋升与全系统生产验收
```

Stage 1 内部的“迁移前代码窗口”和“迁移后真实验收窗口”只是同一阶段的两个执行窗口，不得解释成第三阶段。Stage 2 内的 Wave 只是晋升批次，也不得解释成新的顶层阶段。

# 0. 基线锁与零回归

开始前必须校验两份只读基线：

```text
REFERENCE_OWNER_DECISIONS.rtf
SHA-256: ed983f72e6233b6c2d707e69d131be9416f894aa46d39e7d962dcf65c738f7e0

MULTISOURCE_LOCAL_PRODUCTION_TASKPACK_V1.md
SHA-256: 2900f5c810ea4e87ea8a33b953551c4d822475e7063547e9cbc1627100f96bab
```

两份基线不得修改、覆盖、删减、弱化或重新解释。

本次只允许四类变化：

```text
D-001 先完成 arXiv 完整纵向切片，再逐来源、逐板块晋升；
D-002 2026-06-30 为新电脑迁移目标日期；
D-003 迁移前只做低资源代码工作，重资源任务延后到新电脑；
D-004 增加 arXiv 单源、来源级、板块级晋升门禁，但最终全系统 30 日历史重放＋2 日真实运行不变。
```

除 D-001—D-004 外，原基线中的来源、板块、数据库、关系图、评分、权重、队列、报告、邮件、视频、人工控制、开发记录、测试和最终交付标准全部保留。

发现基线之间、基线与仓库、需求与技术现实存在冲突时，不得静默选择或自行折中。进入：

```text
BLOCKED_REQUIREMENT_CONFLICT
```

并输出：冲突双方文件和位置、影响、A/B/C 最小决策选项、推荐项和等待人工确认的唯一问题。

# 1. 首次读取和执行边界

首次只做最小范围只读审计，读取：

- 根 `AGENTS.md`；
- `arxiv-daily-push/AGENTS.md`；
- `README.md`、`PLANS.md`、`VERSION`、`CHANGELOG.md`、`pyproject.toml`；
- `config/`；
- `src/arxiv_daily_push/`；
- `tests/`；
- `docs/governance/`；
- `docs/phase_records/`；
- 既有 `docs/pursuing_goal/`；
- 仅与本项目直接相关的 `.github/workflows/`。

禁止第一次就全仓扫描、全仓重构或读取其他项目。禁止扫描虚拟环境、`node_modules`、媒体、缓存、模型权重、数据库、秘密、用户主目录和无关 Git 历史。

每次只推进一个 Task ID、一个主要目录范围、一个主要验收标准；Task 门禁通过后可以自动继续，不需要我逐 Task 输入。

每个 Task 开始前必须输出：

```text
Task ID
目标与非目标
将读取的文件
将修改的文件
测试命令
资源预算
风险
回滚方案
停止条件
```

每个 Task 结束后必须输出并写入治理记录：

```text
状态
Diff summary
真实测试命令、退出码、耗时和证据路径
需求追踪结果
基线哈希与零回归结果
CPU/RAM/显存/磁盘/缓存峰值
剩余风险
回滚方法
下一门禁是否解锁
```

不得只写“测试通过”。

# 2. 冻结产品要求

最终产品必须实现：

```text
B1 研究前沿
B2 顶级期刊
B3 中国政策法规
B4 美国科技金融官方信号
B5 跨板块总览
```

正式生产每天：

```text
5 份完整报告
5 封独立邮件：B1、B2、B3、B4、B5 各一封
4 个日常视频：B1—B4
B5 日常默认不生成视频
```

B5 只有在 B1—B4 分别进入成功或明确降级终态后才可生成。

最终 30 日历史重放：

```text
150 份报告
150 份邮件渲染预览
150 个视频，历史 B1—B5 每日各一个
历史邮件不得真实发送
```

最终连续 2 个真实自然日：

```text
10 份报告
10 封真实邮件
8 个正式日常视频
```

报告和视频不设置会牺牲深度、专业度、证据密度和准确性的固定字数或固定时长上限；但所有 Worker 必须具备 heartbeat、无进展超时、检查点、断点续跑和恢复。

# 3. 来源与成本冻结要求

禁止：

- 付费数据 API；
- 付费云主机作为默认生产依赖；
- OpenAI Platform 付费 API 和自动创建付费 API Key；
- 未公开私有接口；
- 绕过订阅墙、登录、验证码、robots 或许可；
- 要求我逐个来源手工配置 API。

采集优先级：

```text
官方 RSS/Atom
→ 官方 OAI-PMH
→ 官方网页、档案页、政策库和公报
→ 官方 XML/CSV/JSON/Bulk/Sitemap
→ 免费无密钥官方 API
→ 免费需密钥官方 API
→ 受控低频 HTML
```

确实需要免费密钥时，必须一次性汇总为最少人工动作，并提供未配置密钥时的明确降级路径。

B1 必须包含：

```text
arXiv
TechRxiv
bioRxiv
medRxiv
ChemRxiv
SSRN
EarthArXiv
ChinaXiv
PubMed
Europe PMC
```

B2 必须包含主刊：

```text
Nature
Science
The Lancet
```

B3 必须完整覆盖：

```text
C0 全国权威主干
C1 中央机关与重点职能部门
C2 全部省级行政区域
C3 首批 24 个重点城市
C4 自贸区、高新区、开发区、特殊功能区和垂直派出机构
```

C3 的 24 城市：

```text
北京、上海、深圳、广州、天津、重庆、杭州、南京、苏州、合肥、
武汉、西安、成都、长沙、无锡、东莞、佛山、珠海、沈阳、
宁波、青岛、厦门、大连、郑州
```

B4 删除 FINRA、MSRB 等 SRO 启用项，并冻结注意力预算：

```text
科技创新与技术突破 35
金融、股票、基金和宏观 30
科技政策与产业规则 20
跨机构法律主干 15
```

完整机构、部门、地区、行业、方式、频率和回退路径以 Master Task Pack 为准，不得缩减。

# 4. 人工控制和治理冻结要求

人工日常只编辑：

```text
config/owner_controls.yaml
```

人工日常只需要查看：

```text
docs/owner/OWNER_CONSOLE.md
docs/owner/SOURCE_CATALOG.md
docs/owner/MODEL_AND_QUEUE.md
docs/owner/CONTENT_LEDGER.csv
```

人工无需阅读 Python 即可看到和控制：

- 来源、板块、平台、机构、地区、行业、采集方式、权重、频率和健康；
- 三套评分卡、公式、参数、每维贡献和参数版本；
- 活跃队列、排名、历史排名、进入、降级、淘汰和重新激活；
- 已深度讲解、简要提及、待讲、生成中、阻断和归档；
- 报告、邮件、视频、Run ID、模型版本、配置版本和文件状态；
- 当前开发阶段、Task、风险、资源、回滚和真正需要人工处理的最少事项。

必须扩展现有治理体系，不创建平行且会漂移的第二套体系。持续维护：

```text
MODEL_SPEC
DEVELOPMENT_LEDGER
DELIVERY_PLAN / delivery_tasks
STATUS
OWNER_STATUS
TRACEABILITY_MATRIX
model_registry
formula_registry
parameter_registry
phase_records
PLANS
CHANGELOG
VERSION
pyproject 版本
开发事件和历史证据
```

每个 Requirement 必须追踪到：

```text
Requirement → Config → Function → Test → Artifact
```

每周只读诊断并创建一个问题范围的 PR，人工合并；每 14 天执行 30 日参数 A/B 对比并创建参数 PR。禁止自动合并和自动修改冻结需求。

# 5. 数据、关系、模型和队列冻结要求

实现本地 SQLite WAL + FTS5，以及：

```text
SourceDefinition
FetchRun
RawRecord
CanonicalDocument
DocumentVersion
Event
Entity
Relation
ThemeCluster
Claim
EvidenceBinding
ScoreSnapshot
QueueEntry
ReportArtifact
EmailArtifact
MediaArtifact
RunManifest
DevelopmentIteration
```

保存：

```text
published_at
updated_at
effective_at
expires_at
deadline_at
retrieved_at
observed_at
known_at
as_of_at
```

实现完整版本和关系图，包括但不限于：

```text
VERSION_OF、REPLACES、SUPERSEDES、AMENDS、REPEALS、CORRECTS、
WITHDRAWS、RETRACTS、PUBLISHED_AS、CITES、SUPPORTS、CONTRADICTS、
FUNDED_BY、ASSOCIATED_TRIAL、ASSOCIATED_PATENT、COMMERCIALIZED_BY、
IMPLEMENTS、INTERPRETS、ENFORCES、RESPONDS_TO、AFFECTS_ENTITY、
AFFECTS_SECTOR、AFFECTS_ASSET、SAME_TOPIC_AS、DERIVED_FROM
```

三套评分卡权重冻结为：

```text
研究证据：相关性 22；新颖性 16；证据质量 16；技术突破 16；
转化和经济价值 14；影响规模 8；时效和版本变化 5；多样性 3。

中国政策：发布机关和法律效力 18；政策变化幅度 16；科技产业相关性 16；
经济影响 14；覆盖范围 10；紧迫性 10；区域相关性 8；可行动性 5；
完整性和置信度 3。

美国官方：创新和技术突破 20；监管或市场影响 18；权威和证据 14；
新颖性和变化 14；公司基金资产行业范围 12；紧迫性 10；
商业化和经济转化 8；可行动性 4。
```

跨板块排序：

```text
normalized_quality
= 0.60 × board_percentile
+ 0.40 × source_percentile

portfolio_score
= 0.40 × normalized_quality
+ 0.20 × cross_board_linkage
+ 0.15 × decision_impact
+ 0.10 × urgency
+ 0.10 × confidence
+ 0.05 × diversity
```

队列优先级：

```text
quality 55
event_delta 15
urgency 10
cross_board_linkage 10
waiting_credit 5
source_balance 5
```

活跃队列冻结：

```text
最大 10,000 条
事件最大年龄 365 天
B1 3500
B2 1500
B3 3000
B4 2000
单一来源默认不长期超过本板块 40%
```

任何内容不得静默消失。第 10,001 条、365 天边界、同分排序、等待信用、配额借用、撤回、替代、重复和重新激活必须确定且可解释。

所有关键事实必须进入 Claim Ledger。缺少原始来源、哈希、检索时间、法律状态、许可、解析置信度或关键证据时必须 fail closed。

# Stage 1｜arXiv 单源完整纵向切片与生产验收

## Stage 1 Goal

建立一个真实、可迁移、可审计、可恢复的 arXiv 单源生产闭环：

```text
arXiv 发现
→ 原始证据保存
→ 规范化
→ 去重与版本
→ 事件与关系
→ 研究评分
→ 10,000 队列逻辑
→ B1 报告
→ Claim Ledger
→ B1 邮件
→ B1 视频
→ CONTENT_LEDGER
→ RunManifest
→ 本地计划任务与恢复
```

Stage 1 完成状态必须是：

```text
ARXIV_PRODUCTION_ACCEPTED
```

完成 Stage 1 后，arXiv 单源正式每日运行必须持续，不因 Stage 2 的新来源开发而中断。

## Stage 1 执行窗口 A：2026-06-30 前的低资源代码工作

当前旧电脑内存、显存、缓存和存储不足。2026-06-30 只是迁移目标日期，不是自动解锁条件。

只有人工在 `config/owner_controls.yaml` 设置：

```yaml
migration:
  new_machine_ready: true
```

且新电脑硬件审计通过，才允许重任务。Codex 不得自行设置该字段。

当 `new_machine_ready=false` 时，只允许：

```text
在线 arXiv 元数据最多 10 条
不下载全文 PDF
Raw 数据不超过 100 MB
临时数据不超过 2 GB
媒体 smoke 最长 30 秒、最高 480p
不下载大型本地模型或大型 TTS
不执行 30 日重放
不执行批量视频
不安装或启用正式生产 scheduler
不大规模抓取其他来源或板块
```

本窗口 Task 顺序：

```text
S1-01 最小范围只读审计和治理校准
S1-02 基线锁、需求/功能/任务/测试追踪
S1-03 owner_controls.yaml 和四个人工查看文件
S1-04 SQLite、统一文档/事件模型、迁移和回滚
S1-05 Source Registry、Connector Contract 和 arXiv 适配
S1-06 研究评分、10,000 队列和 CONTENT_LEDGER
S1-07 B1 报告、Claim、邮件预览和媒体接口
S1-08 scheduler、watchdog、backup、restore 和迁移脚本
S1-09 低资源纵向集成、迁移包和新电脑安装清单
```

本窗口验收：

```text
现有治理事实源一致
所有冻结 Requirement 有 Task/Test/Artifact
配置和权重 Schema 通过
数据库迁移和回滚通过
arXiv fixture 与最多 10 条真实 canary 通过
完整代码路径可执行
一份 B1 报告与邮件预览通过
媒体仅在资源允许时执行 30 秒以内 smoke
资源禁令无绕过路径
所有重测试标记 DEFERRED_UNTIL_NEW_MACHINE，而不是 PASS
形成可验证迁移包
```

达到：

```text
VERTICAL_SLICE_CODE_READY
→ WAITING_FOR_NEW_MACHINE
```

后必须暂停重任务，输出最小迁移操作清单、未执行测试、证据、风险、回滚和恢复步骤。

## Stage 1 执行窗口 B：新电脑上的真实 arXiv 验收

人工确认新电脑就绪后：

```text
S1-10 新电脑硬件、软件、秘密、路径和调度审计
S1-11 安装本地原生运行环境和 OS 计划任务
S1-12 迁移配置、代码、数据库和必要证据并验证哈希
S1-13 arXiv 30 个独立历史日期完整重放
S1-14 arXiv 连续 2 个真实自然日运行
S1-15 arXiv 生产验收与稳定生产隔离
```

arXiv 30 日重放必须产生：

```text
30 份 B1 报告
30 份 B1 邮件预览
30 个 B1 视频
30 个独立 as_of_at
30 份来源终态、Queue delta、Claim Ledger、Manifest 和资源记录
```

必须测试：

```text
未来信息泄漏 = 0
重复文档 = 0
无法解释的队列消失 = 0
关键 Claim 证据绑定 = 100%
同输入同配置同排序
重跑幂等
网络、SSL、解析、视频、重启、恢复、10,001、365 天和磁盘门禁
```

连续 2 个真实日必须每天产生：

```text
1 份真实 B1 arXiv 报告
1 封真实 B1 arXiv 邮件
1 个真实 B1 arXiv 视频
```

只有 P0/P1 缺陷为 0、资源稳定、调度和恢复通过，才可设置：

```text
ARXIV_PRODUCTION_ACCEPTED
```

这也是进入 Stage 2 的唯一门禁。

# Stage 2｜逐来源、逐板块晋升与全系统生产验收

## Stage 2 Goal

在不破坏 arXiv 稳定生产的前提下，按来源和板块逐步接入全部 B1—B4，完成 B5、五封邮件、完整关系图、三套评分卡和最终全系统 30＋2 验收。

Stage 2 只能在 `ARXIV_PRODUCTION_ACCEPTED` 后开始。

新来源状态机：

```text
DISABLED
→ FIXTURE_READY
→ CONTRACT_TESTED
→ REPLAY_30_PASSED
→ SHADOW_48H_PASSED
→ BOARD_PRODUCTION
→ FULL_PRODUCTION
```

Shadow 阶段可以真实抓取、保存、评分和模拟排名，但不得影响正式邮件、正式队列或正式视频。

每个来源或同构来源包必须是一个受控 Task/PR，具备独立 Feature Flag、测试、回滚和失败隔离。新来源失败只能回退自身；已经稳定的 arXiv 和已晋升来源继续生产。

## Stage 2 晋升顺序

```text
Wave 1A：bioRxiv、medRxiv、PubMed、Europe PMC
Wave 1B：TechRxiv、ChemRxiv、EarthArXiv
Wave 1C：SSRN、ChinaXiv
→ B1_ACCEPTED

Wave 2：Nature、Science、The Lancet
→ B2_ACCEPTED

Wave 3：中国 C0、C1
→ B3_C0_C1_ACCEPTED

Wave 4：美国 US-TA、US-LG、US-FM、US-TP
→ B4_ACCEPTED
→ CORE_FIVE_EMAIL_PRODUCTION_ACCEPTED

Wave 5：中国 C2、C3、C4
→ FULL_C0_C4_PRODUCTION_ACCEPTED

Final：全系统 30 个历史日＋连续 2 个真实日
→ PRODUCTION_ACCEPTED
→ DAILY_OPERATION
```

每个新来源晋升前至少通过：

```text
Connector Contract
30 日来源级历史重放
48 小时真实 Shadow
P0/P1 = 0
静默丢失 = 0
幂等 = 100%
关键 Claim 证据绑定 = 100%
条款、许可、robots、限流和历史可用性有明确记录
```

历史无法完整恢复时必须标记：

```text
as_of_fidelity: partial
backfill_reconstructed: true
```

不得用当前页面冒充历史状态。

每个板块晋升前必须通过板块级：

```text
30 日重放
连续 2 个真实日
来源终态完整
报告、邮件、视频合同
去重、关系、评分、队列和资源门禁
OWNER_CONSOLE、SOURCE_CATALOG、MODEL_AND_QUEUE、CONTENT_LEDGER 更新
一键回退验证
```

## Stage 2 最终验收

最终全系统 30 日历史重放必须执行完整链路：

```text
所有来源抓取或历史恢复
Raw 保存
规范化
跨源去重
Document/Version/Event/Entity/Relation
ThemeCluster
三套评分
跨板块排序
10,000 条队列
B1—B5 五份报告
Claim Ledger
五份邮件预览
B1—B5 五个历史视频
Manifest、状态和资源记录
```

通过条件：

```text
150 份历史报告
150 份历史邮件预览
150 个历史视频
30 个独立 as_of_at
未来信息泄漏 = 0
重复发送 = 0
静默遗漏 = 0
无法解释的状态消失 = 0
关键 Claim 证据覆盖 = 100%
```

最终连续 2 个真实日：

```text
每天 5 份报告
每天 5 封真实邮件
每天 B1—B4 四个正式视频
两日共 10 报告、10 邮件、8 视频
B5 水位线正确
全来源有成功、无更新、降级或阻断终态
调度、恢复、备份和资源稳定
```

通过后才可设置：

```text
PRODUCTION_ACCEPTED
→ DAILY_OPERATION
```

# 6. 本地运行与资源要求

默认使用本地原生 Python 和操作系统计划任务，不默认依赖 Docker Desktop、付费云主机或长期 GitHub self-hosted runner。

最终实现：

```text
adp tick
adp watchdog
adp backup
adp restore
adp runtime-audit
adp scheduler install
adp scheduler uninstall
adp migration export
adp migration verify
adp weekly-review
adp biweekly-review
```

支持：单实例锁、heartbeat、无进展超时、错过任务补跑、重启恢复、检查点、睡眠唤醒、资源门禁、备份、恢复和卸载。

新电脑必须重新实测 CPU、RAM、GPU、显存、SSD、FFmpeg、TTS、Codex、浏览器、SMTP、SSL、计划任务和电源能力。资源不足时进入 `BLOCKED_OWNER_ACTION`，只给出最小操作，不伪造通过、不自动删除重要数据、不降低报告质量。

# 7. 缺陷等级与停止条件

```text
P0：数据损坏、秘密泄漏、错误法律状态、重复真实发送
→ 立即停止、回滚

P1：静默漏抓、排序不确定、关键 Claim 无证据、状态丢失
→ 阻断晋升和发布

P2：单来源失败且有显式降级、非关键媒体问题
→ 隔离来源或文本优先

P3：格式、UI、非关键性能优化
→ 后续单问题 PR
```

停止条件包括：新电脑未准备、资源不足、需要秘密或管理员操作、来源条款冲突、必须付费、数据风险、需求冲突、真实两日未完成。

# 8. 完成声明与当前第一步

不得在以下状态宣布完成：

```text
只有代码
只有单元测试
只有 fixture 或 mock
只有 arXiv 抓取
没有真实报告/邮件/视频
没有历史重放
没有连续 2 个真实自然日
没有人工控制和内容账本
```

状态必须依次推进：

```text
STAGE1_CODE_ONLY
→ VERTICAL_SLICE_CODE_READY
→ WAITING_FOR_NEW_MACHINE
→ NEW_MACHINE_BOOTSTRAPPED
→ ARXIV_REPLAY_30_PASSED
→ ARXIV_LIVE_DAY_1_PASSED
→ ARXIV_LIVE_DAY_2_PASSED
→ ARXIV_PRODUCTION_ACCEPTED
→ STAGE2_SOURCE_PROMOTION
→ B1_ACCEPTED
→ B2_ACCEPTED
→ B3_C0_C1_ACCEPTED
→ B4_ACCEPTED
→ CORE_FIVE_EMAIL_PRODUCTION_ACCEPTED
→ FULL_C0_C4_PRODUCTION_ACCEPTED
→ FULL_REPLAY_30_PASSED
→ FULL_LIVE_DAY_1_PASSED
→ FULL_LIVE_DAY_2_PASSED
→ PRODUCTION_ACCEPTED
→ DAILY_OPERATION
```

现在只执行 `S1-01`：

```text
校验压缩包和两份基线哈希
进行最小范围只读审计
输出 Stage 1 的真实文件映射、任务计划、测试命令、资源预算、风险和回滚
不修改代码
不全仓扫描
不执行重任务
```
```

---

# Part H｜最终结论

本 V4 不是缩减版。它是：

```text
两份完整只读基线
＋全部冻结产品和工程要求
＋仅两个顶层阶段
＋2026-06-30 新电脑迁移门禁
＋迁移前低资源开发
＋迁移后 arXiv 单源验收
＋逐来源、逐板块晋升
＋最终全系统 30 日＋2 日验收
```

任何“暂缓”都只表示等待新电脑，不表示取消。任何分阶段验收都不能替代最终全系统验收。
