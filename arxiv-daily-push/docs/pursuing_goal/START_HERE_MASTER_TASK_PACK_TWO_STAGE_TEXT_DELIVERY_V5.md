# arXiv Daily Push 两阶段文本情报系统 Master Task Pack V5

> 文档版本：V5  
> 日期：2026-06-22  
> 目标仓库：`LinzeColin/CodexProject`  
> 目标目录：`arxiv-daily-push/`  
> 部署路线：2026-06-30 前低资源代码开发；迁移后在新电脑本地原生长期运行  
> 最终状态：`PRODUCTION_ACCEPTED → DAILY_OPERATION`

---

# 0. 使用方式与唯一生效基线

本压缩包只包含两份文件：

```text
START_HERE_MASTER_TASK_PACK_TWO_STAGE_TEXT_DELIVERY_V5.md
FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_TEXT_DELIVERY_V5.txt
```

执行顺序：

1. 将本 Master Task Pack 放入仓库 `arxiv-daily-push/docs/pursuing_goal/`；
2. 将完整 Prompt 原样发送给 Codex；
3. Codex 先进行最小范围只读审计，再按本文件的两个顶层阶段持续推进；
4. Stage 1 门禁通过前不得进入 Stage 2；
5. 最终生产完成条件不是代码存在，而是全系统历史重放、真实运行、邮件交付和人工审查面全部通过。

本 V5 是当前唯一生效基线。它已对照以下历史文件完成要求迁移：

```text
参考.rtf
SHA-256: ed983f72e6233b6c2d707e69d131be9416f894aa46d39e7d962dcf65c738f7e0

arxiv_daily_push_multisource_local_production_taskpack_v1(1).md
SHA-256: 2900f5c810ea4e87ea8a33b953551c4d822475e7063547e9cbc1627100f96bab
```

保留不变的核心基线：

- 四个内容板块与一个跨板块总览；
- 每天五份报告、五封独立邮件；
- 全部研究、顶刊、中国 C0—C4、美国官方来源范围；
- 免费优先、禁止付费数据 API、禁止付费云主机作为默认生产依赖；
- 本地数据库、不可变原始证据、版本关系图、Taxonomy、实体和主题聚类；
- 三套领域评分卡、跨板块排序、10,000 条活跃队列和 12 个月时间窗；
- 一个人工控制文件、四个人类查看文件；
- 开发记录、需求清单、任务目标、函数清单、模型参数和追踪矩阵；
- 每周诊断、每 14 天参数复审、人工合并；
- 30 个独立历史日期完整重放与连续 2 个真实自然日；
- 两阶段开发与 2026-06-30 新电脑迁移门禁。

当前产品唯一外发交付是：

```text
高密度文本报告
独立邮件
Markdown / HTML / JSON 审计产物
```

任何旧版非文本交付链路及其配置、任务、测试、调度、存储和验收项均不属于本 V5 范围。现有相关旧代码默认保持关闭，不得消耗本 Goal 的开发资源；除非它直接阻断文本主链，否则不在本 Goal 内重构。

发现本文件与仓库现状存在冲突时，不得自行折中。进入：

```text
BLOCKED_REQUIREMENT_CONFLICT
```

并输出：冲突位置、影响、A/B/C 最小决策选项、推荐项和等待人工确认的唯一问题。

---

# 1. 两个顶层阶段与总时间线

本项目只有两个顶层阶段。

| 阶段 | Goal | 完成状态 |
|---|---|---|
| Stage 1 | 完成 arXiv 单源完整纵向切片；迁移前完成低资源代码和测试，迁移后完成真实部署、30 日重放和 2 日真实运行 | `ARXIV_PRODUCTION_ACCEPTED` |
| Stage 2 | 在稳定 arXiv 生产基础上，逐来源、逐板块晋升，完成 B1—B5、五封邮件和全系统生产验收 | `PRODUCTION_ACCEPTED → DAILY_OPERATION` |

## 1.1 时间窗口

| 时间 | 可执行工作 | 禁止工作 |
|---|---|---|
| 2026-06-22 至 2026-06-29 | 治理、Schema、接口、数据库迁移代码、fixture、单元测试、小样本集成测试、安装脚本、迁移清单 | 30 日真实重放、大范围在线抓取、大批量附件下载、长期后台运行、大规模缓存、生产邮件 |
| 2026-06-30 起 | 新电脑 bootstrap、真实网络预检、完整 arXiv 重放、真实邮件、长期调度、Stage 2 晋升 | 未通过门禁就宣称生产完成 |

2026-06-30 是迁移目标日期，不是自动解锁条件。必须完成新电脑硬件、网络、磁盘、凭据和调度预检后才能执行重资源任务。

## 1.2 规划工期

| 里程碑 | 预计工期 | 说明 |
|---|---:|---|
| Stage 1 迁移前代码窗口 | 约 5—8 天 | 只完成低资源开发与 fixture 证据 |
| Stage 1 新电脑验收 | 约 6—12 个自然日 | 包括 30 日 arXiv 重放和连续 2 个真实自然日 |
| Stage 2 核心五封邮件 | Stage 1 后约 7—12 周 | B1、B2、B3 C0/C1、B4、B5 |
| Stage 2 完整 C0—C4 与最终验收 | Stage 1 后约 12—20 周 | 逐批接入全部省级、24 城市和 C4 |

工期是计划范围，不替代验收标准。任何阶段不得以“时间到了”代替证据门禁。

---

# 2. 最终产品与每日交付合同

## 2.1 五个报告板块

| 板块 ID | 名称 | 核心内容 |
|---|---|---|
| B1 | 研究前沿 | 预印本、医学索引、开放研究和早期技术信号 |
| B2 | 顶级期刊 | Nature、Science、The Lancet 主刊的高质量证据 |
| B3 | 中国政策法规 | C0—C4：全国、中央、省级、重点城市、特殊功能区及垂直机构 |
| B4 | 美国科技金融官方信号 | 科技创新和技术突破优先，同时覆盖科技政策、股票、基金、金融和宏观监管 |
| B5 | 跨板块总览 | 科研—顶刊—中国政策—美国官方信号之间的关系、机会、风险、矛盾和传导路径 |

## 2.2 正式生产每日交付

每天生成并发送：

```text
5 份完整报告
5 封独立邮件
B1、B2、B3、B4、B5 各一封
```

邮件主题：

```text
[ADP][B1][YYYY-MM-DD] 研究前沿日报
[ADP][B2][YYYY-MM-DD] 顶级期刊日报
[ADP][B3][YYYY-MM-DD] 中国政策法规日报
[ADP][B4][YYYY-MM-DD] 美国科技金融官方信号日报
[ADP][B5][YYYY-MM-DD] 跨板块总览
```

B5 只有在 B1—B4 分别进入成功或明确降级终态后才可生成。缺失板块不得被静默忽略，必须在 B5 中明确说明来源、影响和不确定性。

## 2.3 历史与真实运行交付数量

最终全系统 30 日历史重放：

```text
150 份完整报告
150 份邮件渲染预览
历史邮件不得真实发送
```

最终连续 2 个真实自然日：

```text
10 份完整报告
10 封真实邮件
```

Stage 1 arXiv 单源历史验收：

```text
30 份 B1 报告
30 份 B1 邮件预览
2 个真实自然日各 1 份 B1 报告和 1 封真实邮件
```

## 2.4 文本质量原则

不设置会牺牲专业度、证据密度和准确性的固定字数上限。质量门禁基于：

- 关键事实可追溯；
- 证据与结论绑定；
- 研究方法、法律效力、版本状态和不确定性被正确解释；
- 同主题的支持、反证和矛盾结果同时呈现；
- 重复信息被压缩；
- 板块内有专业深度，B5 有跨板块关系；
- 结论、下一步和风险清晰；
- 读者无需打开代码即可理解选择、排序和淘汰原因。

---

# 3. 人工控制面：只改 1 个文件，只看 4 个文件

## 3.1 唯一人工控制文件

```text
config/owner_controls.yaml
```

可控制：

- 板块和来源启停；
- 来源、行业、主题、机构、公司和资产偏好；
- 三套评分卡和跨板块权重；
- 队列容量、时间窗、软配额和淘汰阈值；
- 来源采集频率、并发、限流和回退；
- 报告与邮件开关；
- 本机 CPU、内存、磁盘和缓存限制；
- 历史重放、Shadow、生产模式；
- 每周和每 14 天 Codex 迭代权限。

敏感信息不得提交 Git。邮件凭据、Codex 登录态和 Token 只能位于操作系统凭据库、受保护环境变量或本机秘密文件。

## 3.2 四个人类查看文件

| 文件 | 回答的问题 |
|---|---|
| `docs/owner/OWNER_CONSOLE.md` | 项目当前阶段、今日五封邮件、来源健康、资源压力、真正需要人工处理的事项 |
| `docs/owner/SOURCE_CATALOG.md` | 来源、板块、机构、行业、方式、频率、权重、许可和健康状态 |
| `docs/owner/MODEL_AND_QUEUE.md` | 三套评分卡、跨板块公式、队列规则、当前参数和参数变更影响 |
| `docs/owner/CONTENT_LEDGER.csv` | 已讲、简要提及、待讲、降级、淘汰、阻断、报告和邮件状态 |

这些文件均由事实源自动生成，不允许人工单独修改。

## 3.3 开发治理文件

保留并扩展现有治理体系：

```text
docs/governance/MODEL_SPEC.md
docs/governance/DEVELOPMENT_LEDGER.md
docs/governance/DELIVERY_PLAN.md
docs/governance/STATUS.md
docs/governance/OWNER_STATUS.md
docs/governance/TRACEABILITY_MATRIX.csv
docs/governance/model_registry.yaml
docs/governance/formula_registry.yaml
docs/governance/parameter_registry.csv
docs/governance/delivery_tasks.yaml
docs/governance/FUNCTION_CATALOG.generated.md
docs/governance/FEATURE_CATALOG.generated.md
docs/phase_records/
```

追踪链：

```text
Requirement ID
→ Feature ID
→ Task ID
→ Config Key
→ Function Symbol
→ Test ID
→ Artifact
→ Run Evidence
```

---

# 4. `owner_controls.yaml` 核心结构

Codex 必须生成正式文件、JSON Schema、注释示例、验证命令和 30 日影响预览。以下为冻结结构基线：

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
  paid_openai_api_allowed: false
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
  max_parallel_analysis_jobs: 1
  max_parallel_report_jobs: 1
  min_free_disk_gb: 60
  emergency_free_disk_gb: 15
  max_temp_cache_gb: 10

intelligence_provider:
  priority:
    - codex_cli_chatgpt_auth
    - local_model
    - deterministic_degraded
  fail_if_no_high_quality_provider: true
  local_model_optional: true
  max_context_tokens: auto
  chunk_and_retrieve_required: true

boards:
  B1: {enabled: true, name: "研究前沿"}
  B2: {enabled: true, name: "顶级期刊"}
  B3: {enabled: true, name: "中国政策法规"}
  B4: {enabled: true, name: "美国科技金融官方信号"}
  B5: {enabled: true, name: "跨板块总览"}

email:
  enabled: true
  recipients_from_secret: true
  split_mode: five_independent_messages
  send_order: [B1, B2, B3, B4, B5]
  historical_replay_send: false
  attach_markdown_report: true
  include_high_density_html: true
  require_message_hash: true
  retry_count: 3
  cross_board_waits_for: [B1, B2, B3, B4]

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

report_quality:
  critical_claim_traceability_required: true
  factual_claim_source_required: true
  contradiction_review_required: true
  uncertainty_section_required: true
  source_coverage_section_required: true
  queue_change_section_required: true
  no_fixed_word_limit: true
  editorial_compression_pass: true
  fail_closed_on_missing_critical_evidence: true

token_efficiency:
  deterministic_prefilter_required: true
  evidence_packet_cache: true
  reuse_analysis_by_content_hash: true
  analyze_version_delta_only_when_possible: true
  deduplicate_context: true
  full_text_only_for_selected_items: true
  persist_model_call_manifest: true
  hard_daily_token_cap: null
  soft_budget_requires_quality_override_reason: true

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

验证命令：

```bash
adp owner validate
adp owner preview-impact --days 30
adp owner render-docs
```

每次修改必须输出：Schema、权重和、来源变化、队列变化、过去 30 天排名变化、报告覆盖变化、资源影响和回滚版本。

---

# 5. 功能清单

| Feature ID | 功能 | 完成定义 |
|---|---|---|
| F-001 | 治理一致性 | 版本、状态、需求、任务、模型、参数和生成页面无漂移 |
| F-002 | 人工控制面 | 一个 YAML 控制关键参数，四个人类文件自动生成 |
| F-003 | 全链追踪 | Requirement → Function → Test → Artifact 可验证 |
| F-010 | 来源注册表 | 稳定 ID、板块、机构、行业、方式、频率、权重和健康状态 |
| F-011 | 免费访问策略 | 禁止付费 API，优先 RSS/OAI/官方网页/批量文件 |
| F-012 | 来源健康 | 成功、无更新、降级、阻断和解析漂移均有记录 |
| F-013 | C0—C4 生成 | 省级、24 城市、特殊功能区和垂直机构模板化发现 |
| F-020 | Connector SDK | RSS、Atom、OAI、HTML、PDF、XML、CSV、JSON、免费官方接口 |
| F-021 | 限流与缓存 | 主机限流、ETag、Last-Modified、重试、断点续跑 |
| F-022 | 条款和许可治理 | robots、条款、全文范围、附件策略可审计 |
| F-030 | 本地数据库 | SQLite WAL + FTS5，支持文档、版本、事件、关系、队列和状态 |
| F-031 | 原始证据 | SHA256 内容寻址、压缩、不可变 RawRecord |
| F-032 | 统一模型 | Document、Version、Event、Entity、Relation 分离 |
| F-033 | 身份与去重 | DOI、PMID、arXiv ID、文号、FR Doc、CIK 等对齐 |
| F-034 | 版本关系图 | 修订、替代、撤回、发表、生效、废止、实施和解释 |
| F-035 | Taxonomy Bridge | 学科、MeSH、产业、政策、司法辖区和资产标签映射 |
| F-036 | 证据包缓存 | 按内容哈希复用解析、证据和分析，减少重复上下文 |
| F-040 | 三套评分卡 | 研究、中国政策、美国官方信号独立评分并可解释 |
| F-041 | 顶刊 Profile | 原始研究、综述、社论、新闻、更正、撤回分开处理 |
| F-042 | 跨板块排序 | 分位校准、关系、影响、紧迫性、置信度和多样性 |
| F-043 | 10,000 条队列 | 12 个月、软配额、淘汰、重激活和等待信用 |
| F-044 | 状态原因账本 | 已讲、未讲、降级、淘汰、阻断全部可追溯 |
| F-050 | Claim Ledger | 关键事实绑定证据、位置、置信度和事实类型 |
| F-051 | 五份报告 | 四板块详细报告 + B5 跨板块总览 |
| F-052 | 五封邮件 | 每个板块独立发送、幂等、重试和审计 |
| F-053 | 文本质量流水线 | 证据地图、矛盾审查、编辑压缩和密度优化 |
| F-060 | 本地计划任务 | 唤醒、错过补跑、单实例和固定工作目录 |
| F-061 | Watchdog | 心跳、锁、卡死检测、恢复和重试 |
| F-062 | 资源治理 | CPU、内存、磁盘、缓存和温度压力记录 |
| F-063 | 本地备份 | 数据库、配置、Manifest、报告索引备份恢复 |
| F-070 | 30 日历史重放 | 30 个独立 as-of 日，未来信息泄漏为 0 |
| F-071 | 2 日真实运行 | 两个真实自然日、10 份报告、10 封真实邮件 |
| F-072 | 生产验收 | 所有门禁通过后进入 DAILY_OPERATION |
| F-080 | 每周 Codex 诊断 | 一个问题、一个 PR、人工合并 |
| F-081 | 每 14 天参数复审 | 30 日 A/B 对比、展示排名变化、人工批准 |
| F-082 | 防需求漂移 | Codex 不得自行改变冻结范围和门禁 |

---

# 6. 来源清单、编号和采集优先级

## 6.1 统一来源字段

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

## 6.2 稳定编号

```text
RF-###              研究前沿
TJ-###              顶级期刊
CN-C0-###           全国权威主干
CN-C1-###           中央机关与重点职能部门
CN-C2-<REGION>-###  省级行政区域
CN-C3-<CITY>-###    重点城市
CN-C4-<AREA>-###    特殊功能区和垂直机构
US-TA-###           科技创新与技术突破
US-FM-###           金融、股票、基金和宏观
US-TP-###           科技政策和产业规则
US-LG-###           跨机构法律主干
```

编号一经分配不得复用。

## 6.3 免费采集优先级

```text
官方 RSS / Atom
→ 官方 OAI-PMH
→ 官方网页、档案页、政策库和公报
→ 官方 XML / CSV / JSON / Bulk / Sitemap
→ 免费无密钥官方 API
→ 免费需密钥官方 API
→ 受控低频 HTML
```

禁止：付费数据 API、未公开私有接口、绕过登录/验证码/订阅墙、把转载当原始源、静默省略失败来源、要求人工逐源配置。

---

# 7. B1 研究前沿

| ID | 来源 | 角色 | 优先方式 | 领域 |
|---|---|---|---|---|
| RF-001 | arXiv | 综合预印本、分类和版本源 | RSS、OAI-PMH、官方列表 | AI、计算机、数学、物理、量化金融 |
| RF-002 | TechRxiv | 工程和计算技术预印本 | RSS、官方列表 | 工程、通信、芯片、计算 |
| RF-003 | bioRxiv | 生命科学预印本 | RSS、免费官方接口 | 生物、基因、神经、药物 |
| RF-004 | medRxiv | 医学健康预印本 | RSS、免费官方接口 | 医学、临床、公共卫生 |
| RF-005 | ChemRxiv | 化学和材料预印本 | RSS、官方列表 | 化学、材料、能源 |
| RF-006 | SSRN | 社科、法律、金融和经济工作论文 | 官方提醒、低频官方页面 | 金融、法律、经济、商业 |
| RF-007 | EarthArXiv | 地球和环境科学预印本 | RSS、官方列表 | 气候、地学、环境、能源 |
| RF-008 | ChinaXiv | 中国预印本和中文研究成果 | 官方列表、检索页、公开 PDF | 中文科研、多学科 |
| RF-009 | PubMed | 生物医学权威索引 | 保存检索 RSS、免费 E-utilities | 医学、生物、药物 |
| RF-010 | Europe PMC | 生物医学索引、开放全文和资助关系 | 订阅、免费 REST、Bulk | 医学、生物、开放证据 |

规则：

- PubMed、Europe PMC 主要作为索引和增强源，不重复生成原始论文；
- DOI、PMID、arXiv ID、正式发表关系进入同一 CanonicalDocument；
- SSRN 低频、缓存、条款检查，不逆向私有接口；
- 只在许可允许和证据确需时下载全文；
- OCR 只用于无文本层扫描件。

---

# 8. B2 顶级期刊

| ID | 来源 | 方式 | 重点类型 |
|---|---|---|---|
| TJ-001 | Nature 主刊 | 官方 RSS、文章列表、免费 DOI 元数据 | Article、Review、News、Editorial、Correction、Retraction |
| TJ-002 | Science 主刊 | 官方 RSS、内容页、免费 DOI 元数据 | Research Article、Report、Review、Perspective、Editorial、Correction |
| TJ-003 | The Lancet 主刊 | 官方 RSS、Online First、PubMed/Europe PMC | Article、Review、Commission、Editorial、Correspondence、Correction |

规则：

- 首期只启用主刊；
- 文章类型参与 Profile；
- 新闻和社论是趋势信号，不得冒充原始研究；
- 更正、撤回和表达关注属于强制事件；
- 不绕过订阅墙，不保存无许可全文。

---

# 9. B3 中国政策法规：C0—C4

## 9.1 C0 全国权威主干

- 国家法律法规数据库；
- 全国人大及其常委会法律、决定、草案和审议文件；
- 国务院政策文件库；
- 国务院公报；
- 中央公开党内法规和制度库；
- 最高人民法院；
- 最高人民检察院；
- 原始发文机关正式文件和附件。

## 9.2 C1 中央机关与重点职能部门

党务、治理和监督：

- 中共中央和中央办公厅公开文件；
- 中央纪委国家监委；
- 中央组织部；
- 中央宣传相关公开机构；
- 中央网信办；
- 中央政法委；
- 党内法规制度来源。

宏观、科技、产业、金融和市场：

- 国家发展改革委、科技部、工业和信息化部、财政部；
- 中国人民银行、国家金融监督管理总局、中国证监会、国家外汇管理局；
- 商务部、海关总署、国家税务总局、国家统计局；
- 市场监管总局、国家知识产权局、国务院国资委、国家数据局；
- 国家能源局、国家卫生健康委、国家药监局、生态环境部；
- 教育部、人力资源和社会保障部、自然资源部、住房城乡建设部；
- 交通运输部、农业农村部、应急管理部；
- 其他具有正式政策发布职责的国务院部门和直属机构。

## 9.3 C2 全部省级行政区域

直辖市：北京、天津、上海、重庆。  
省：河北、山西、辽宁、吉林、黑龙江、江苏、浙江、安徽、福建、江西、山东、河南、湖北、湖南、广东、海南、四川、贵州、云南、陕西、甘肃、青海。  
自治区：内蒙古、广西、西藏、宁夏、新疆。  
特别行政区：香港、澳门，使用独立法律和政府网站 Profile。  
台湾不作为本注册表中的中国政府部门来源自动纳入。

每个省级区域至少注册：党委和办公厅、纪委监委、人大、政府和公报、高级法院、检察院、发改、科技、工信、财政、商务、市场监管、金融监管、国资、税务、数据、网信、生态环境、卫健、药监、自然资源、应急和适用特殊区域。

## 9.4 C3 首批 24 个重点城市

```text
北京、上海、深圳、广州、天津、重庆、杭州、南京、苏州、合肥、
武汉、西安、成都、长沙、无锡、东莞、佛山、珠海、沈阳、
宁波、青岛、厦门、大连、郑州
```

每个城市强制注册：市委及办公厅、纪委监委、人大、政府和公报、法院、检察院、发改、科技、工信、财政、商务、市场监管、数据、金融监管、国资、网信、税务、生态环境、卫健、药监、规划自然资源、应急、适用高新区/自贸区/开发区、海关/港口/航运。

## 9.5 C4 特殊功能区与垂直机构

自动发现并注册：国家级新区、自贸试验区、国家级高新区、国家级经开区、综合保税区、重点产业园区、海关直属机构、税务局、人民银行分支、金融监管局、证监局、知识产权保护中心、药监分支和审评机构、港口航运机场管理机构及其他直接影响科技、产业、金融和市场的重要派出机构。

C4 不允许人工逐个设置。Codex 必须依据官方目录、父级门户和模板自动生成候选，再验证域名、权威性和可访问性。

政策文档必须保存：文号、发布机关、共同发布机关、效力等级、辖区、文件类型、发布日期、施行日、失效日、意见截止日、有效状态、原始 URL、附件、修改/废止/替代/解释/实施关系。

---

# 10. B4 美国科技金融官方信号

不启用 FINRA、MSRB 等 SRO。

## 10.1 US-TA 科技创新与技术突破：35%

NSF、DARPA、ARPA-E、ARPA-H、DOE Office of Science、国家实验室、NIH、NASA、NIST、USPTO、FDA、SBIR/STTR、IARPA。

重点：重大资助、项目、原型、技术突破、临床和监管里程碑、专利、商业化、国家实验室成果、关键标准。

## 10.2 US-FM 金融、股票、基金和宏观：30%

SEC/EDGAR、Federal Reserve、New York Fed、FRED、Treasury、Fiscal Data、OFAC、CFTC、OCC、FDIC、CFPB、OFR、FSOC、BEA、BLS、Census、EIA。

SEC 至少识别：8-K、10-K、10-Q、S-1、13D、13G、13F、Forms 3/4/5、N-PORT、N-CEN。

## 10.3 US-TP 科技政策和产业规则：20%

OSTP、NIST、BIS、FTC、FCC、CISA、Department of Commerce/CHIPS、DOE、FDA 指南及其他与 AI、芯片、网络安全、标准、频谱、竞争和出口管制直接相关的官方来源。

## 10.4 US-LG 跨机构法律主干：15%

Federal Register、Regulations.gov、GovInfo、Congress.gov、White House、OMB、GAO。

同一机构只保留一个连接器和一个原始记录，通过多标签映射到多个主题，避免重复采集。

---

# 11. 数据库、统一模型与文本缓存

## 11.1 本地存储

```text
data/
  adp.sqlite3
  raw/sha256/
  evidence/
  reports/
  emails/
  manifests/
  backups/
  exports/
```

默认：SQLite 3、WAL、FTS5、外键、事务、内容寻址、JSON Schema、可选 Parquet 分析快照。数据库、原始文档、完整报告、邮件和秘密不得提交公共 Git。

## 11.2 核心对象

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
EvidencePacket
AnalysisSnapshot
Claim
EvidenceBinding
ScoreSnapshot
QueueEntry
ReportArtifact
EmailArtifact
RunManifest
DevelopmentIteration
```

区别：

```text
Document = 长期内容身份
Version = 某一不可变版本
Event = 某一时间发生的发布、修改、生效、撤回等变化
Queue = 对 Event 或 ThemeCluster 排序
EvidencePacket = 面向分析的可复用证据集合
AnalysisSnapshot = 某模型和参数版本下的结构化分析
Report = 对选中主题的证据化解释
Email = 报告交付状态
```

必须保存：`published_at`、`updated_at`、`effective_at`、`expires_at`、`deadline_at`、`retrieved_at`、`observed_at`、`known_at`、`as_of_at`。

历史重放必须使用 `known_at` 和 `as_of_at`，禁止未来信息泄漏。

## 11.3 Token 和上下文效率

- 原始内容按哈希去重；
- 解析、证据抽取和结构化分析按内容哈希缓存；
- 未变化版本不重复全量分析；
- 版本变化优先分析 delta；
- 确定性规则先做粗筛、去重和分类；
- 只有入选或高潜内容才进入深度模型分析；
- 同一主题构建一次 EvidencePacket，多份报告复用；
- 每次模型调用保存 provider、model、prompt hash、输入输出估算、缓存命中、用途和结果哈希；
- 不以降低证据质量换取节省；任何超预算必须记录质量理由。

---

# 12. 版本关系图

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

触发：预印本正式发表、草案转正式文件、实施细则、修订废止、撤回更正、基金/专利/试验/监管关系，均需重新评分、更新队列并记录原因。

---

# 13. 评分模型

## 13.1 研究证据卡

```text
相关性 22
前沿性与新颖性 16
证据质量 16
技术突破 16
转化和经济价值 14
影响规模 8
时效和版本变化 5
多样性和覆盖 3
合计 100
```

B1/B2 Profile：preprint、top_journal_original_research、review_meta_analysis、editorial_news、correction_retraction。

## 13.2 中国政策卡

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

## 13.3 美国官方信号卡

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

## 13.4 统一质量修正

```text
base_score = Σ(weight_i × normalized_signal_i)
quality_score = base_score × confidence_factor × completeness_factor × source_health_factor
```

每条必须保存：原始信号、归一化值、权重、维度贡献、修正因子、硬门禁、最终得分、参数版本、模型版本和 commit。

## 13.5 跨板块排序

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

约束：每个有合格内容的板块至少保留一个主主题；B5 单一板块默认不超过 40%；重大生效/截止/撤回允许 override 并记录理由；同主题先聚类；反证和矛盾不得被热度吞掉；不设固定“只讲前 N 篇”。

---

# 14. 10,000 条队列与内容账本

## 14.1 队列

```yaml
max_active_items: 10000
max_event_age_days: 365
soft_quotas:
  B1: 3500
  B2: 1500
  B3: 3000
  B4: 2000
source_share_cap_per_board: 0.40
```

历史库不受 10,000 限制。超过 12 个月的 Event 归档，不删除文档、版本、关系和证据。新版本、正式发表、实施、执法、专利、试验、资助、截止临近可重激活。

```text
queue_priority
= 0.55 × quality
+ 0.15 × event_delta
+ 0.10 × urgency
+ 0.10 × cross_board_linkage
+ 0.05 × waiting_credit
+ 0.05 × source_balance
```

## 14.2 生命周期

```text
DISCOVERED → NORMALIZED → LINKED → SCORED → ELIGIBLE
→ SELECTED_BOARD → SELECTED_CROSS_BOARD → GENERATING
→ GENERATED → EMAIL_PENDING → EMAILED → MONITORING → ARCHIVED
```

异常：`NEEDS_REVIEW`、`DOWNGRADED`、`EVICTED_CAPACITY`、`EVICTED_AGE`、`MERGED_DUPLICATE`、`SUPERSEDED`、`RETRACTED`、`WITHDRAWN`、`BLOCKED_EVIDENCE`、`BLOCKED_LICENSE`、`BLOCKED_SOURCE`、`FAILED_RETRYABLE`、`FAILED_TERMINAL`。

## 14.3 CONTENT_LEDGER

字段：

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
model_version
parameter_version
source_registry_version
run_id
first_seen_at
last_updated_at
```

任何内容不得静默消失。所有状态变化追加写入 `data/events/content_events.jsonl`。

---

# 15. 文本分析、报告和邮件流水线

## 15.1 流程

```text
抓取
→ 原始证据保存
→ 规范化与去重
→ 文档/版本/事件/关系
→ 确定性预筛
→ 领域评分与队列
→ 主题聚类
→ EvidencePacket
→ 第一遍分析：事实、机制、影响和不确定性
→ 第二遍审查：反证、矛盾、版本和法律状态
→ 报告编排
→ Claim/Evidence 审计
→ 编辑压缩：删除重复、提升密度、保留必要深度
→ HTML/Markdown/JSON
→ 独立邮件
→ Manifest 和 Content Ledger
```

## 15.2 四份板块报告

1. 结论和关键变化；
2. 来源覆盖和健康状态；
3. 本日重点事件和主题；
4. 技术、法律、产业或金融深度解释；
5. 证据、反证和不确定性；
6. 版本与关系图；
7. 对项目、行业、公司、资产或政策的影响；
8. 行动建议和观察事项；
9. 队列新增、升级、降级和淘汰；
10. 引用、原始来源、模型和运行证据。

## 15.3 B5 跨板块报告

1. 四板块核心结论；
2. 跨来源主题聚类；
3. 科研到产业和商业化传导；
4. 顶刊验证、修正或否定；
5. 中国与美国政策趋同和分化；
6. 公司、基金、股票、行业和宏观影响；
7. 机会—风险矩阵；
8. 12 个月观察清单；
9. 未解决矛盾和待核实问题；
10. B1—B4 报告 ID、覆盖状态和降级说明。

## 15.4 邮件

每封邮件包括：结论优先摘要、高密度 HTML 正文、完整 Markdown 附件、来源覆盖与降级警告、报告/模型/参数/Run ID、已讲/未讲/降级/淘汰数量、本机产物路径、消息哈希和重试状态。

邮件发送必须幂等。相同 `report_id + recipient + content_hash` 不得重复发送；重试必须保留原始失败和最终结果。

---

# 16. 采集频率、水位线与本地运行

## 16.1 初始频率

| 来源族 | 频率 |
|---|---|
| 研究预印本 | 每 6 小时 |
| Nature、Science、Lancet | 每 6 小时 |
| 中国中央、省级、城市 | 10:30、17:30 Asia/Shanghai；21:00 补抓 |
| 美国法律主干 | 07:00 America/New_York |
| 美国科技、创新、金融 | 09:30、16:30、21:30 America/New_York |
| Watchdog | 每 30 分钟 |
| 资源和来源健康 | 每小时 |
| Codex 周诊断 | 每周一次 |
| 参数复审 | 每 14 天一次 |

## 16.2 OS 原生任务

```text
adp tick            每 30 分钟
adp watchdog        每 30 分钟，错开 5 分钟
adp backup          每日一次
adp weekly-review   每周一次
adp biweekly-review 每 14 天一次
```

`adp tick` 根据 IANA 时区和 Source Registry 只运行到期来源，不为每个来源建立单独 OS 任务。

Windows 使用 Task Scheduler；Linux 使用 systemd oneshot + timer + `Persistent=true`；macOS 使用 launchd。必须支持单实例、唤醒、错过补跑、固定工作目录、退避重试、锁、heartbeat 和重启恢复。

电脑完全关机时无法运行；下次开机自动补跑。需要准点邮件时，电脑应开机或处于可唤醒状态。

## 16.3 水位线

板块报告生成前：所有必需来源必须有成功、无更新、明确降级或明确阻断的终态；解析、去重、关系、评分和队列已完成；不得无限等待失败来源；缺失必须写进报告。B5 等待 B1—B4 成功或明确降级终态。

所有长任务必须有 heartbeat、检查点、无进展超时和断点续跑，但不得用固定总时长牺牲文本质量。

---

# 17. 本机资源与迁移门禁

## 17.1 当前电脑：2026-06-30 前

冻结为低资源代码窗口：

```text
不执行 30 日真实重放
不启动长期生产调度
不下载大型本地模型
不做大范围在线抓取
不批量下载附件
不构建大缓存
不真实群发邮件
```

允许：fixture、小样本、mock 邮件、临时 SQLite、Schema、接口、单元测试、安装脚本、迁移清单。

建议上限：单次测试数据 ≤ 100 MB；临时文件 ≤ 2 GB；分析并发 1；浏览器并发 0 或 1；出现内存压力立即停止。

## 17.2 新电脑：2026-06-30 起

Bootstrap 必须实测：OS、CPU、内存、SSD 可用空间、Python、Git、Codex、浏览器、SMTP、SSL、计划任务、电源策略和网络。硬件加速不是验收要求。

文本系统建议：

```text
最低建议：4 核 CPU、16 GB RAM、60 GB 可用 SSD
推荐：8 核 CPU、32 GB RAM、120 GB 以上可用 SSD
```

本地模型是可选降级路径，不得成为生产必需依赖。若使用，必须单独记录模型、资源和质量表现。

资源门禁：

```yaml
max_parallel_analysis_jobs: 1
max_parallel_report_jobs: 1
min_free_disk_gb: 60
emergency_free_disk_gb: 15
max_temp_cache_gb: 10
stop_on_high_memory_pressure: true
stop_on_thermal_pressure: true
run_heavy_jobs_on_battery: false
```

低于紧急阈值时 fail closed，不自动删除原始证据和重要报告。

---

# 18. Stage 1：arXiv 单源完整纵向切片

## 18.1 Stage 1 Goal

完成以下真实纵向链：

```text
arXiv
→ 抓取
→ RawRecord
→ CanonicalDocument / Version / Event
→ 分类与评分
→ 10,000 队列机制
→ EvidencePacket
→ B1 报告
→ Claim Ledger
→ B1 邮件
→ OWNER_CONSOLE / MODEL_AND_QUEUE / CONTENT_LEDGER
→ 本地计划任务、恢复和备份
```

## 18.2 迁移前任务

| Task ID | 目标 | 主要产物 | 门禁 |
|---|---|---|---|
| S1-01 | 最小只读审计和治理校准 | 现状图、漂移清单、追踪矩阵 | 版本、状态、任务和模型一致 |
| S1-02 | 人工控制面 | owner_controls、Schema、四个人类文件生成器 | 一改四看可用 |
| S1-03 | SQLite 与统一模型 | migration、仓储接口、幂等键 | fixture 重跑无重复 |
| S1-04 | Source Registry 和 Connector Contract | 注册表、接口、限流、缓存、健康模型 | arXiv 可按统一接口运行 |
| S1-05 | arXiv Adapter | RSS/OAI/官方列表、版本和 taxonomy | fixture 与小样本通过 |
| S1-06 | 研究评分和队列 | 研究卡、贡献明细、10,001/365 天测试 | 确定性和原因码通过 |
| S1-07 | 文本质量流水线 | EvidencePacket、两遍分析、Claim、B1 模板 | 关键 Claim 证据覆盖 100% |
| S1-08 | 邮件合同 | HTML/Markdown、幂等、mock SMTP | 不重复发送，失败可追踪 |
| S1-09 | 调度、watchdog、备份 | OS 安装脚本、锁、heartbeat、restore | 小样本恢复演练通过 |
| S1-10 | 新电脑迁移包 | bootstrap、secret 清单、迁移 Runbook | 不含秘密和大数据 |

迁移前不得执行 S1-11 以后任务。

## 18.3 新电脑验收任务

| Task ID | 目标 | 验收 |
|---|---|---|
| S1-11 | 新电脑 bootstrap | 硬件、网络、SSL、SMTP、Codex、浏览器、调度全部有实测记录 |
| S1-12 | 真实 arXiv 预检 | 抓取、解析、Raw、数据库、评分、报告和邮件预览全链通过 |
| S1-13 | 30 日 arXiv 历史重放 | 30 独立 as-of 日、30 报告、30 邮件预览、未来泄漏 0 |
| S1-14 | 连续 2 个真实自然日 | 2 报告、2 封真实邮件、真实调度和恢复证据 |
| S1-15 | Stage 1 验收 | `ARXIV_PRODUCTION_ACCEPTED`，开始稳定发送 B1 arXiv 邮件 |

## 18.4 Stage 1 晋升标准

必须同时满足：

- 30/30 历史日期有终态；
- 同输入、同参数、同 commit 得到相同顺序；
- 重跑无重复文档、事件、队列和邮件；
- 关键 Claim 证据绑定 100%；
- 静默丢失 0；
- 第 10,001 条和 365 天边界确定；
- 网络、SSL、解析、进程重启、邮件失败、磁盘阈值和恢复演练通过；
- P0/P1 缺陷为 0；
- 四个人类查看文件可解释当天结果；
- 本地计划任务启用；
- 连续 2 日真实邮件成功。

未满足不得进入 Stage 2。

---

# 19. Stage 2：逐来源、逐板块晋升

## 19.1 Stage 2 Goal

在不破坏 arXiv 已上线生产的前提下，采用 feature flag、独立配置、fixture、历史重放和 Shadow 逐来源晋升，最终形成 B1—B5 五封邮件系统。

来源状态机：

```text
DISABLED
→ TEST
→ REPLAY_PASSED
→ SHADOW
→ BOARD_PRODUCTION
→ FULL_PRODUCTION
```

Shadow 可以真实抓取、保存、评分和模拟排名，但不得影响正式队列和正式邮件。

## 19.2 晋升 Wave

| Wave | 范围 | 目的 |
|---|---|---|
| S2-W1 | bioRxiv、medRxiv、PubMed、Europe PMC | 验证第二类来源、索引增强和身份对齐 |
| S2-W2 | TechRxiv、ChemRxiv、EarthArXiv | 扩展工程、化学、地学预印本 |
| S2-W3 | SSRN、ChinaXiv | 处理条款、页面稳定性和中文来源 |
| S2-W4 | Nature、Science、The Lancet | 完成 B2、文章类型、发表关系和更正撤回 |
| S2-W5 | 中国 C0、C1 | 完成全国与中央权威政策法律主干 |
| S2-W6 | 美国 US-TA、US-LG、US-FM、US-TP | 科技创新优先，完成 B4 |
| S2-W7 | 中国 C2 全部省级 | 省级公报、政策库和核心部门 |
| S2-W8 | 中国 C3 24 城市 | 重点城市模板和部门覆盖 |
| S2-W9 | 中国 C4 | 特殊功能区和垂直机构自动发现 |
| S2-W10 | B5 与最终组合 | 跨板块图谱、五封邮件、全系统验收 |

Wave 内来源可并行 Shadow，但每次 Codex 开发仍遵循一个 issue、一个主要目录、一个主要验收标准、一个 PR。

## 19.3 单来源门禁

- Connector contract 和 fixture 通过；
- 30 个历史日期有成功、无更新、降级或阻断终态；
- 48 小时真实 Shadow；
- 幂等、去重、版本和许可通过；
- 成功或无更新率目标 ≥95%；
- 静默丢失 0；
- 关键字段完整；
- 来源失败不影响其他来源；
- 人工可见晋升记录；
- P0/P1 缺陷 0。

## 19.4 单板块门禁

- 所有必需来源已晋升或有人工批准降级；
- 板块级 30 日重放；
- 连续 2 日 Shadow 或生产候选运行；
- 报告、Claim、邮件合同通过；
- 来源覆盖、排名、队列和淘汰可解释；
- 旧生产板块无回归。

B1、B2、B3、B4 分别通过后才能启用对应正式邮件。B5 只有 B1—B4 全部通过后启用。

## 19.5 最终门禁

全系统 30 日历史重放：

- 30 个独立 `as_of_at`；
- 150 份报告；
- 150 份邮件预览；
- 全来源终态；
- 未来信息泄漏 0；
- 幂等、确定性、10,001、365 天、限流、解析漂移、重启、恢复和磁盘阈值通过。

连续 2 个真实自然日：

- 10 份报告；
- 10 封真实邮件；
- B5 水位线正确；
- 单来源失败隔离；
- 人工控制和查看文件完整；
- P0/P1 缺陷 0。

完成后：

```text
PRODUCTION_ACCEPTED
→ DAILY_OPERATION
```

---

# 20. 测试体系与质量门禁

## 20.1 测试层级

| 层级 | 范围 |
|---|---|
| T0 | 治理、Schema、追踪和秘密扫描 |
| T1 | 配置、时间、状态、原因码 |
| T2 | Connector Contract、限流、缓存、许可 |
| T3 | 数据库、迁移、幂等、身份和关系 |
| T4 | 三套模型、排序、10,000 队列 |
| T5 | EvidencePacket、Claim、报告和五封邮件 |
| T6 | 调度、锁、watchdog、恢复、备份和资源 |
| T7 | Stage 1 arXiv 30 日重放与 2 日真实运行 |
| T8 | 来源级 30 日 + 48 小时 Shadow |
| T9 | 板块级重放和邮件验收 |
| T10 | 全系统 30 日 + 2 日最终验收 |

## 20.2 强制质量指标

| 指标 | 标准 |
|---|---:|
| 关键 Claim 证据绑定 | 100% |
| 重要事实来源追踪 | 100% |
| 必需来源终态覆盖 | 100% |
| 相同输入确定性 | 100% |
| 重跑幂等 | 100% |
| 静默丢失 | 0 |
| Canonical 重复 | 0 |
| 未来信息泄漏 | 0 |
| 缺失必需报告章节 | 0 |
| 重复邮件 | 0 |
| P0/P1 缺陷 | 0 |

## 20.3 缺陷等级

- P0：数据损坏、秘密泄漏、错误生产发送、未来信息泄漏、法律状态严重错误；立即停止。
- P1：关键来源/报告缺失、排序不可复现、证据链断裂、队列错误；阻止晋升。
- P2：单来源失败且有明确降级、非关键字段缺失；隔离修复，不隐瞒。
- P3：文案、显示和低风险改善；进入周迭代。

## 20.4 每个 Task 的开发合同

开始前：Task ID、目标/非目标、读取文件、修改文件、测试命令、资源预算、风险、回滚、停止条件。  
结束后：状态、Diff summary、真实命令/退出码/耗时/证据路径、需求追踪、资源峰值、剩余风险、回滚、下一门禁。

不得只写“测试通过”。

---

# 21. 每周和每 14 天 Codex 迭代

## 21.1 每周

```text
只读诊断
→ 来源健康
→ 解析漂移
→ 抓取失败
→ 队列异常
→ 报告/邮件缺失
→ 证据覆盖和重复上下文
→ 资源增长
→ 选择一个最高优先级问题
→ 创建一个 PR
→ 人工审查和合并
```

产物：`diagnostic.md`、`source_health.csv`、`parser_drift.csv`、`scoring_distribution.csv`、`queue_aging.csv`、`token_efficiency.csv`、`resource_report.csv`、`regression_report.json`、`proposed_changes.yaml`、`codex_task_prompt.md`、`rollback_plan.md`。

## 21.2 每 14 天

基于过去 14 天人工反馈和过去 30 天排名、已讲/未讲转化、淘汰内容后续价值、来源失败率、板块覆盖和模型调用效率，进行新旧参数 30 日 A/B 重放，展示排名和报告覆盖变化，创建参数 PR，人工批准后生效。

## 21.3 禁止自动修改

- 付费 API/付费云禁令；
- 来源覆盖范围；
- 10,000 条和 12 个月；
- 五封邮件；
- 三套评分卡结构；
- C0—C4；
- B4 注意力预算；
- 生产发布门禁；
- 收件人和秘密；
- 自动合并策略；
- 外部交易或执行行为。

---

# 22. Requirement ID 基线

| Requirement ID | 要求 |
|---|---|
| REQ-COST-001 | 禁止付费数据 API |
| REQ-COST-002 | 禁止付费云主机作为默认生产依赖 |
| REQ-SRC-001 | B1—B4 与 B5 总览 |
| REQ-SRC-002 | B1 十个研究来源 |
| REQ-SRC-003 | B2 三个顶刊主刊 |
| REQ-CN-001 | 中国 C0—C4 完整覆盖 |
| REQ-US-001 | 美国科技创新和技术突破优先 |
| REQ-US-002 | 不启用 FINRA/MSRB 等 SRO |
| REQ-DATA-001 | 本地数据库、原始证据、版本和关系图 |
| REQ-TEXT-001 | 文本证据包、分析缓存和高密度报告流水线 |
| REQ-MODEL-001 | 三套领域评分卡 |
| REQ-RANK-001 | 跨板块排序和可解释贡献 |
| REQ-QUEUE-001 | 活跃队列最大 10,000 |
| REQ-QUEUE-002 | 活跃事件最大年龄 12 个月 |
| REQ-REPORT-001 | 每天五份完整报告 |
| REQ-EMAIL-001 | 每天五封独立邮件 |
| REQ-TRACE-001 | 已讲/未讲/降级/淘汰全记录 |
| REQ-HUMAN-001 | 只编辑一个人工控制文件 |
| REQ-HUMAN-002 | 四个人类查看文件 |
| REQ-LOCAL-001 | 本地原生计划任务、唤醒和补跑 |
| REQ-RESOURCE-001 | CPU、内存、磁盘和缓存保护 |
| REQ-STAGE-001 | 只有 Stage 1 和 Stage 2 |
| REQ-MIGRATE-001 | 2026-06-30 前低资源开发，迁移后真实验收 |
| REQ-REPLAY-001 | 30 个独立历史日完整流程 |
| REQ-LIVE-001 | 连续 2 个真实自然日 |
| REQ-CODEX-001 | 每周诊断 PR，人工合并 |
| REQ-CODEX-002 | 每 14 天参数 A/B PR |
| REQ-ACCEPT-001 | 通过后自动进入 DAILY_OPERATION |

---

# 23. 最终验收清单

- [ ] V5 为唯一生效基线，旧非文本交付链路不进入当前范围；
- [ ] 治理无漂移；
- [ ] 一个 `owner_controls.yaml` 控制关键参数；
- [ ] 四个人类查看文件自动生成；
- [ ] 函数、功能、任务、需求、模型和参数全链追踪；
- [ ] B1 十个来源；
- [ ] B2 三个顶刊；
- [ ] B3 C0—C4；
- [ ] B4 科技创新优先且不启用 SRO；
- [ ] 免费来源策略；
- [ ] SQLite、Raw、EvidencePacket、版本和关系图；
- [ ] 三套评分卡和跨板块排序；
- [ ] 10,000 条、12 个月队列；
- [ ] 已讲、未讲、降级、淘汰完整；
- [ ] 每天五份报告；
- [ ] 每天五封独立邮件；
- [ ] Stage 1：30 报告、30 邮件预览、2 个真实日和 2 封真实邮件；
- [ ] Stage 2：150 报告、150 邮件预览、2 个真实日和 10 封真实邮件；
- [ ] 本地计划任务、唤醒、补跑、watchdog；
- [ ] CPU、内存、磁盘和缓存门禁；
- [ ] 每周 Codex PR；
- [ ] 每 14 天参数 PR；
- [ ] 人工合并；
- [ ] `ARXIV_PRODUCTION_ACCEPTED` 后才进入 Stage 2；
- [ ] 最终 `PRODUCTION_ACCEPTED → DAILY_OPERATION`。
