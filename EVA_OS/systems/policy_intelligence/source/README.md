# Source Authority Registry

独立来源注册库，用于收集政策信息来源、保存可追溯证据，并按 `A-E + 0-100` 规则计算权威性评分。

## 初始化

```bash
cd outputs/source-authority-registry
python3 -m source_registry --db data/source_registry.sqlite init
python3 -m source_registry --db data/source_registry.sqlite seed --seed-file config/seed_sources.json
python3 -m source_registry --db data/source_registry.sqlite list
```

如果没有安装为包，运行命令前使用：

```bash
export PYTHONPATH=src
```

## 常用命令

```bash
# 列出允许爬取的来源
python3 -m source_registry --db data/source_registry.sqlite list --crawl-enabled

# 查看单个来源
python3 -m source_registry --db data/source_registry.sqlite show <source_id> --json

# 人工确认最终分
python3 -m source_registry --db data/source_registry.sqlite review <source_id> \
  --final-score 96 \
  --status user_confirmed \
  --reviewer linze \
  --note "确认作为中央政府主发布源"

# 给正文库使用的来源快照
python3 -m source_registry --db data/source_registry.sqlite snapshot <source_id>

# 运行政策文件收集、分析和报告流水线
bash scripts/run_policy_report.sh

# 查看质量门槛、待生产队列和授权/API 缺口
python3 -m source_registry --db data/source_registry.sqlite status --json

# 查看外部参考缺口队列
python3 -m source_registry --db data/source_registry.sqlite gaps --limit 20

# 生成外部参考缺口可视化复核工作台
python3 -m source_registry --db data/source_registry.sqlite gap-dashboard

# 生成跨运行运营总览 dashboard
python3 -m source_registry --db data/source_registry.sqlite ops-dashboard

# 生成平台覆盖矩阵，检查搜索 API、中文搜索入口和平台授权/解析器状态
python3 -m source_registry --db data/source_registry.sqlite platform-coverage

# 生成平台解析器能力 dashboard，检查视频/文章/作者页/评论/弹幕/互动数据能力
python3 -m source_registry --db data/source_registry.sqlite platform-parsers

# 验收平台解析器前置条件，合并搜索 key、平台授权和 parser 台账
python3 -m source_registry --db data/source_registry.sqlite platform-parser-validate

# 生成抓取策略与合规边界 dashboard
python3 -m source_registry --db data/source_registry.sqlite crawl-policy

# 生成附件解析能力 dashboard，检查 PDF/DOCX/XLSX/OCR/Tika/GROBID 缺口
python3 -m source_registry --db data/source_registry.sqlite attachment-parsers

# 生成开源/商业模型对标 dashboard
python3 -m source_registry --db data/source_registry.sqlite benchmark-dashboard

# 生成规则化质量门槛 dashboard
python3 -m source_registry --db data/source_registry.sqlite quality-gates

# 检查最新 PDF/HTML/Markdown/dashboard 报告产物
python3 -m source_registry --db data/source_registry.sqlite report-check

# 检查搜索 API、中文搜索入口和平台授权 readiness
python3 -m source_registry --db data/source_registry.sqlite readiness --json

# 生成本地 secret/auth 模板，默认写到 ~/.policy-intelligence/
python3 -m source_registry --db data/source_registry.sqlite setup-config

# 生成本地接入验收向导
python3 -m source_registry --db data/source_registry.sqlite setup-wizard

# 汇总判断是否可以进入全网在线验收
python3 -m source_registry --db data/source_registry.sqlite access-readiness

# 生成本地 Data Trust 审计包：JSON/CSV/Markdown/PDF
python3 -m source_registry --db data/source_registry.sqlite data-trust-audit \
  --content-db data/policy_documents.sqlite \
  --report-dir reports \
  --output-dir reports/system_audit

# 一次性导入 SerpAPI/Bing/Google CSE 搜索凭据；输出不展示 key
python3 -m source_registry --db data/source_registry.sqlite search-secret-bulk-import \
  --source-file /path/to/search_api_bundle.json \
  --search-secrets-file ~/.policy-intelligence/policy-search-secrets.json

# search_api_bundle.json 支持顶层字段或 provider 分组字段，例如：
# {
#   "SERPAPI_API_KEY": "...",
#   "bing": {"api_key": "..."},
#   "google": {"api_key": "...", "cse_id": "..."}
# }

# 一次性导入多个平台 cookie 文件路径；输出不展示 cookie 或完整路径
python3 -m source_registry --db data/source_registry.sqlite platform-auth-bundle-import \
  --source-file /path/to/platform_auth_bundle.json \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json

# 只登记 Chrome/Playwright 会话文件或 Chrome profile 目录；输出不展示完整路径
python3 -m source_registry --db data/source_registry.sqlite platform-auth-session-import \
  --platform bilibili \
  --session-file /path/to/chrome_profile_or_storage_state \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json

# platform_auth_bundle.json 支持顶层平台字段或 platforms 分组字段，例如：
# {
#   "bilibili": {"cookie_file": "/local/path/bilibili_cookie.txt"},
#   "platforms": {"zhihu": "/local/path/zhihu_cookie.txt", "douyin": {"chrome_profile_dir": "/local/chrome/profile"}}
# }

# 体检本地 key/auth 文件，不输出 secret 内容
python3 -m source_registry --db data/source_registry.sqlite credential-doctor

# 验证平台授权文件连通性；默认离线，不读取远程平台
python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json

# 显式在线验证；目前只对 B站做最小公开登录态验证
python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json \
  --platform bilibili \
  --online

# 验证搜索 API 连通性；默认在线，会消耗少量 API 配额
python3 -m source_registry --db data/source_registry.sqlite search-validate \
  --search-secrets-file ~/.policy-intelligence/policy-search-secrets.json

# 只检查配置，不联网
python3 -m source_registry --db data/source_registry.sqlite search-validate --offline

# 标记单个缺口为已解决或忽略
python3 -m source_registry --db data/source_registry.sqlite gap-review <gap_id> \
  --status resolved \
  --reviewer linze \
  --note "已补充 Bing/Google/SerpAPI key"

# 批量复核缺口，建议先 dry-run
python3 -m source_registry --db data/source_registry.sqlite gap-bulk-review \
  --required-action provide_search_api_key \
  --status resolved \
  --reviewer linze \
  --note "搜索 API key 已补齐" \
  --dry-run

# 导入中国政府网“政府网站基本信息下载”的 CSV 或 ZIP
python3 -m source_registry --db data/source_registry.sqlite import-csv path/to/catalog.csv
```

## 评分规则

总分 100：

- 官方身份证据：30 分
- 机构层级与法定/行政职能：25 分
- 是否为原始发布源：20 分
- 可追溯证据完整度：15 分
- 稳定性与历史可靠性：10 分

等级：

- A：90-100
- B：75-89
- C：60-74
- D：40-59
- E：0-39

系统评分写入 `system_score`；人工确认写入 `final_score`。报告和正文快照使用 `final_score` 优先，否则使用 `system_score`。

## 与正文库集成

正文数据库不需要复制来源库，只保存以下快照字段：

```json
{
  "source_id": "...",
  "authority_tier_snapshot": "A",
  "authority_score_snapshot": 96,
  "source_name": "中国政府网",
  "source_url": "https://www.gov.cn/",
  "scoring_version": "authority-v1",
  "scored_at": "..."
}
```

这样后续来源评分被人工调整，也不会改变历史文件的报告追溯口径。

## 测试

```bash
cd outputs/source-authority-registry
PYTHONPATH=src python3 -m unittest discover -s tests
```

## 自动化入口

当前可交给 automation 的入口是：

```bash
cd systems/policy_intelligence/source
bash scripts/run_policy_report.sh
```

它会生成：

- `data/policy_documents.sqlite`
- `data/automation/latest_run.json`
- `data/monitor/latest_status.json`
- `reports/automation_run_dashboard.html`
- `reports/policy_ops_dashboard.html`
- `reports/platform_coverage_dashboard.html`
- `reports/platform_parser_dashboard.html`
- `reports/platform_parser_validation_dashboard.html`
- `reports/platform_parser_sample_dashboard.html`
- `reports/crawl_policy_dashboard.html`
- `reports/attachment_parser_dashboard.html`
- `reports/setup_wizard_dashboard.html`
- `reports/credential_doctor_dashboard.html`
- `reports/platform_auth_validation_dashboard.html`
- `reports/search_secret_intake_dashboard.html`
- `reports/search_validation_dashboard.html`
- `reports/automation_readiness_dashboard.html`
- `reports/benchmark_dashboard.html`
- `reports/quality_gates_dashboard.html`
- `reports/report_artifact_check_dashboard.html`
- `data/snapshots/YYYYMMDD/`
- `reports/YYYYMMDD_<分析对象>_研究报告.pdf`
- `reports/YYYYMMDD_<分析对象>_研究报告.html`
- `reports/YYYYMMDD_<分析对象>_研究报告.md`
- `reports/YYYYMMDD_<分析对象>_研究报告_dashboard.html`

详细说明见 [docs/automation.md](docs/automation.md)。

## 报告格式

报告已切换为全中文 PDF 交付。默认主产物是 `reports/YYYYMMDD_<分析对象>_研究报告.pdf`，文件名会体现本报告唯一研究对象并保持简短；同目录保留 HTML/Markdown 旁路产物，用于排版追溯和内容审查。PDF 默认使用 Chrome 按 HTML 版式打印，以保证中文显示兼容；如需强制使用 ReportLab 兜底引擎，可设置 `POLICY_REPORT_FORCE_REPORTLAB_PDF=1`。当前报告粒度为：

- 每份报告只研究 1 份政策文件。
- 每次自动化运行只生成 1 份单文件研究报告。
- 当前 automation 每天运行 2 次，因此正常情况下每天自动生成 2 份报告。

报告包含：

- 可点击目录和文内跳转
- 研究质量与交付状态：质量门槛、平台覆盖、外部参考缺口、待生产队列
- 外部采集健康度：展示外部解读尝试数、可计入参考、缺搜索 API key、需授权来源、请求失败和搜索入口数量
- 外部参考缺口队列：把未计入参考的搜索入口、缺 API key、需授权、待解析器、公开网页受限或抓取失败记录成可追踪待办
- 执行摘要
- 运行编号：`YYYYMMDDNN`，例如当天第 1 份报告为 `2026060301`
- 来源权威等级
- 官方附件解析：PDF/DOCX/XLSX/图片附件会在进入报告前尝试抽取文本摘录；扫描版 PDF 和图片可在本机具备 OCR 依赖时抽取文字，用于正文分析和行业分类
- 重要性评分
- 政策属性
- 行业与地区映射
- 核心要点
- 核心条款拆解
- 产业链影响
- 受益公司/标的候选
- 商业影响
- 交易观察价值
- 风险与不确定性
- 与历史政策或既有行研报告的关系
- 建议行动
- 可进入行研或交易系统的任务队列
- 外部研究与解读资料质量门槛：每份报告有效外部参考不少于 5 份，且至少覆盖 2 个外部平台
- Reference 区域采用紧凑排版，目标控制在 1 页内；控制的是展示长度，不减少参考数量
- 多平台资料池：B 站、抖音、快手、微博、知乎、微信公众号、小红书、今日头条、官方媒体、财经媒体等
- 待生产研究报告队列：按行业板块、时间、中央到地方排序
- 同名 dashboard sidecar：保留采集漏斗、运行复盘、benchmark、报告 timeline 等运维信息；正式 PDF 不展示最近运行明细

同名 `_dashboard.html` 是面向运营和复盘的独立仪表盘页面，可直接查看本次运行的图表、队列积压、质量缺口和参考模型能力矩阵。正式研究报告按商务简洁原则只保留高价值研究内容，不把最近运行日志、采集漏斗或 benchmark 矩阵写入正文。参考模型来自 [docs/reference_benchmark.md](docs/reference_benchmark.md)，覆盖 PolicyInsight、GovReady-Q、CISO Assistant、OPA、Regology 和 Monity AI。

`reports/policy_ops_dashboard.html` 是跨运行运营总览 dashboard，按商务简洁原则只保留核心指标、质量门槛、下一步动作、待生产队列、外部参考缺口和全网覆盖入口。待生产队列表按当前 pending 报告重新编号为 `队列序`，行业优先级只用于排序，不作为报告编号；页面不再展示最近运行明细、模型对标明细或刷新命令，避免把运维日志和生产队列混在一起。

`历史成功公开参考复用` 是外部参考的稳定性补丁，只复用同一政策文件过去已经成功抓取正文、且可计入质量门槛的公开网页/平台参考。它排除搜索入口、登录受限页、抓取失败页、本地相关文件库条目，并按平台+标题去重；默认最多补 1 条，用于抵御微信公众号等公开链接临时失效，不用于注水参考数量。

`reports/automation_run_dashboard.html` 是自动化步骤状态 dashboard。`scripts/run_policy_report.sh` 每个阶段都会写入 `data/automation/latest_run.json`，记录步骤名、状态、耗时、退出码和错误摘要。它用于定位 unattended automation 是卡在采集、报告生成、dashboard 生成、质量门槛还是凭据验证阶段；不记录 API key、cookie、账号密码或 secret 文件内容。

`reports/automation_readiness_dashboard.html` 是每日两次自动化运行就绪 dashboard。它只回答是否适合放进 unattended automation：入口脚本、数据目录、pipeline lock、自动化步骤状态、最近成功运行新鲜度、完成报告产物、待生产队列、质量门槛、P0 搜索/API+B站授权、每日两次调度、调度持久化证据以及当前运行策略是否可用。运行策略面板会展示采集规模、请求超时、重试次数、限速和最大运行时长，并在无重试、无限速、超时异常或采集规模过低时给出 warning。调度持久化可通过 `data/automation/scheduler.json` 或 `--scheduler-file` 提供非敏感证据，例如 scheduler 类型、入口脚本和 `09:00/21:00` 运行时间；launchd `.plist` 会被结构化解析 `ProgramArguments` 和 `StartCalendarInterval`，时间不匹配不会误判通过。它不会保存账号、API key 或 cookie。该页面只展示状态、证据和下一步动作，不展示 secret，也不把步骤日志塞进运营总览。

`automation-scheduler-plan` 生成 macOS launchd 调度计划草案，不会安装或启用系统任务，也不会创建 `data/automation/scheduler.json`。它输出 `reports/com.source-registry.policy-report.plist`、`reports/scheduler_manifest.example.json`、`reports/automation_scheduler_plan.json` 和 `reports/automation_scheduler_plan.html`，用于人工确认安装步骤、回滚步骤和非敏感 evidence 格式。只有真实安装 launchd/cron/外部 automation 后，才应把 manifest 示例复制为 `data/automation/scheduler.json`，让 readiness 从 warning 变为 pass。

`automation-lock-clean` 是无人值守运行前的安全预检命令，只会删除 PID 已不存在的 `data/pipeline.lock`；如果锁文件对应进程仍在运行，或锁文件内容不是 PID，它不会删除。清理后若确认当前没有 active lock，它还会把正文库里遗留的 `pipeline_runs.status='running'` 标记为 failed，避免监控把中断运行误当成仍在执行。`scripts/run_policy_report.sh` 会在正式 pipeline 前自动执行该预检，减少 stale lock 阻塞每日两次运行。

`reports/platform_coverage_dashboard.html` 是平台覆盖矩阵，按搜索 API、中文搜索入口、B 站/抖音/快手/微博/知乎/微信公众号/小红书/头条和公开媒体站点列出：当前是否配置、授权是否可用、已实现解析能力、授权后允许能力、阻塞原因、下一步动作和合规边界。它用于判断“接近全网覆盖”还缺 key、cookie/session、平台解析器还是人工复核。

`reports/platform_parser_dashboard.html` 是平台解析器能力 dashboard。它从 `config/platform_parsers.json` 读取 B站、抖音、快手、微博、知乎、微信公众号、小红书、头条、搜索 API 和公开媒体站点的解析能力，展示公开搜索、文章正文、视频元数据、字幕、评论、弹幕、作者页和互动数据的 ready/partial/planned 状态、业务价值、下一步和验收标准。运营总览只保留该专项入口；具体平台解析状态集中在本页。

`platform_text_parser` 是平台视频/互动文本的本地标准化模块，用于把 B站 JSON 字幕、SRT、WebVTT、评论列表和弹幕 XML 统一清洗为报告可用摘录。它只处理已公开或已授权取得的本地文本，不读取账号、cookie、API key，也不绕过平台访问控制。B站 collector 现在复用该模块生成字幕、评论和弹幕摘录；样本验收会继续指出哪些能力已有本地证据、哪些仍缺样本。

`platform_page_parser` 是授权公开搜索结果页的离线元数据抽取模块。它从已抓取 HTML 的 meta、JSON-LD、OpenGraph 和常见正文数字中提取标题、作者、作者页、发布时间、阅读/播放量和互动数；不联网、不执行脚本、不读取 secret。`authorized_public_search` 现在会把这些字段写入 interpretation item，用于提高微博、知乎、公众号、小红书、头条、抖音、快手等平台详情页的报告可用性。

`reports/platform_parser_validation_dashboard.html` 是平台解析器验收 dashboard。它把 `config/platform_parsers.json`、搜索 API key 状态和本地平台授权状态合并，判断每个 parser 当前是 `current_ready`、`current_partial`、`missing_search_key`、`missing_platform_auth` 还是 `implementation_pending`。该页用于决定下一步是补 key、补 cookie/session，还是实现平台详情解析器；不输出 API key、cookie、账号密码或完整本地路径。

`reports/platform_parser_sample_dashboard.html` 是平台解析样本验收 dashboard。它只读 `data/policy_documents.sqlite` 中已入库的外部解读样本，按 parser 判断是否已有可计入报告质量门槛的正文、视频、作者、互动和失败审计证据；`sample_passed` 才代表该 parser 已产生可用于报告的本地样本，`partial_sample` 代表只有线索或关键证据不足，`no_samples` 代表需要先补采集。该页不联网、不读取账号密码、不展示 API key/cookie/session。

`reports/crawl_policy_dashboard.html` 是抓取策略与合规边界 dashboard。它从 `config/crawl_policies.json` 读取默认策略和 profile，把来源库中的 `crawl_enabled=true` 来源映射到抓取策略，展示 robots/nofollow 策略、限速、重试、超时、快照保留、受限页面处理方式和 robots URL。该页面吸收 Heritrix3/Scrapy 的抓取治理思路，用于确保全网抓取不是无限制乱抓，而是按公开/授权/限速/失败记录/缺口队列执行。

`reports/attachment_parser_dashboard.html` 是附件解析能力与运行依赖 dashboard。它从 `config/attachment_parsers.json` 读取 PDF、DOCX、XLSX、PPTX、OCR、Apache Tika、GROBID 等解析能力，展示 ready/partial/planned 状态、格式覆盖、业务价值、下一步实施队列和验收标准；同时检查本机 `pypdf`、`PyMuPDF`、`Pillow`、`pytesseract`、系统 `tesseract`、`TIKA_SERVER_URL`、`GROBID_SERVER_URL` 是否具备。当前内置解析器已覆盖 DOCX 正文/页眉页脚/批注、XLSX sheet 名称和单元格值、PPTX slide 文本；Tika/GROBID 已接成可选外部服务，配置对应本地 URL 后可处理旧版 Office 和研究 PDF 结构化信息。运营总览只保留该专项入口；具体解析能力集中在本页，避免把低价值实现细节放进主 dashboard。

`crawl-policy` 默认只做离线准入检查，不联网。需要人工验证 robots.txt 时运行：

```bash
python3 -m source_registry --db data/source_registry.sqlite crawl-policy --check-robots
```

在线模式会读取各来源 `robots.txt` 并检查当前 User-Agent 是否允许抓取来源首页；失败、404、禁止抓取都会显示为状态证据，但不会尝试绕过限制。

如果本机 Python 证书链导致政府网站 robots 校验失败，可人工加 `--allow-insecure-tls` 只放宽 robots.txt 读取时的 TLS 校验：

```bash
python3 -m source_registry --db data/source_registry.sqlite crawl-policy --check-robots --allow-insecure-tls
```

该参数不改变验证码、登录、付费墙、robots 禁止抓取等访问边界；只用于区分“本地证书链失败”和“robots 明确禁止/站点不可达”。

`reports/benchmark_dashboard.html` 是开源/商业模型对标 dashboard。它从 `config/benchmark_models.json` 读取 PolicyInsight、GovReady-Q、CISO Assistant、Open Policy Agent、changedetection.io、Heritrix3、Scrapy、Apache Tika、GROBID、Huginn、Regology、Monity AI 的 GitHub/官网证据、能力标签、吸收能力、当前落地状态、下一步实施队列和验收标准。运营总览只保留该专项 dashboard 的入口；详细模型矩阵集中在本页面，避免主 dashboard 信息过载。

`reports/quality_gates_dashboard.html` 是规则化质量门槛 dashboard。它从 `rules/quality_gates.json` 读取硬门槛、合规护栏和运营目标，并用最近一次 monitor 状态评估当前是否满足：外部参考不少于 5 份、外部平台不少于 2 个、每份报告只研究 1 份文件、正式主产物必须是 PDF、主体分析固定 10 个深度章节、PDF 主体页数目标不少于 10 页、商务高价值信息密度不少于 95%。运营总览会展示全部硬门槛状态，避免关键质量规则被折叠隐藏；无法从当前运行证据验证的项目显示为 `not_checked`，不会冒充达标。

`reports/report_artifact_check_dashboard.html` 是报告产物自检 dashboard。它默认读取最近一次 pipeline 生成的 PDF，并检查 PDF 是否存在/非空、PDF 页数、PDF 可提取文字密度、HTML 可见文字密度、同名 HTML/Markdown/dashboard sidecar、报告是否单文件、10 个深度章节、可点击目录、规则化质量门槛面板、研究质量面板或 dashboard sidecar、Reference 区域是否存在、估算是否紧凑，以及商务高价值信息密度是否达到 95%。Reference 紧凑度只读取正文 `interpretations` 区块，不把目录或待生产队列误算进去；高价值密度会惩罚明显占位、重复、泛化和低价值段落。自检结果会被 `quality-gates` 用作生成后证据，减少不必要的 `not_checked`。

`reports/setup_wizard_dashboard.html` 是本地接入验收向导，把 `setup-config`、搜索 API 批量导入、平台 cookie 批量导入、`readiness`、`platform-coverage`、`platform-parsers`、`platform-parser-validate`、`crawl-policy`、`attachment-parsers`、`gap-dashboard` 和最终运行报告串成步骤矩阵与可复制命令。页面新增接入优先级矩阵，只保留会直接提升报告质量的输入、验收标准和业务价值：P0 为搜索 API 与 B 站，P1 为微信公众号/知乎/微博，P2 为抖音/快手/小红书/头条。页面只展示本地模板路径、命令和状态，不展示 API key、cookie、账号密码或本地文件内容。

`reports/access_readiness_dashboard.html` 是全网接入验收页。它把搜索 API、B站 P0 授权、百度/搜狗/360 中文公开入口、公众号/知乎/微博 P1 授权、短视频/社媒 P2 授权和平台解析器前置条件合并成一页，直接给出 `blocked`、`partial` 或可进入在线验收的状态。页面只展示脱敏状态、业务价值、下一步命令和合规边界，不展示 API key、cookie、session、账号密码、bundle 内容或完整敏感 cookie 路径。

`reports/system_audit/data_trust_audit_<date>.pdf` 是政策系统 Data Trust 正式审计报告。它只读取本地控制文件、配置、SQLite 来源库、内容库和报告目录，输出每条记录的可信状态、证据分类、结论等级、问题、下一步动作和稳定 hash。缺失 `AGENTS.md`、`PLANS.md`、`CODEX_TASK_PACK.md`、`CODEX_PROMPTS.md` 会被标记为 `NEEDS_REVIEW`；失败运行和拒绝来源会阻断对应结论。详细规则见 `docs/data_trust_layer.md`。

`reports/credential_doctor_dashboard.html` 是本地凭据体检 dashboard。它会检查搜索 key 文件、平台授权文件、cookie/session 文件存在性、权限、空值和过期状态，并新增 P0 接入门槛：至少 1 个搜索 API 可用且 B 站授权文件可用时，系统才视为具备高质量外部研究的最低接入条件；3 个搜索 API 与 B 站均可用时，P0 接入完整。体检页只显示状态、缺失字段名、业务价值和下一步动作，不显示真实 key、cookie、session 内容或完整敏感路径。

`reports/search_secret_intake_dashboard.html` 是搜索 API 接入清单。它按 SerpAPI、Bing、Google CSE 展示当前 ready 状态、缺失字段、业务价值、安全导入命令和离线/在线验收命令；同时提供 `search-secret-bulk-import`，可从一个本地 `search_api_bundle.json` 一次性导入多个 provider。Google CSE 必须同时具备 API key 和 CSE ID 才算 ready。页面不展示 API key 或完整敏感路径。

`reports/platform_auth_intake_dashboard.html` 是平台授权接入清单。它按 P0/P1/P2 展示 B站、微信公众号、知乎、微博、抖音、快手、小红书、头条的目标文件、接入方式、业务价值、授权能力和验收命令；同时提供 `platform-auth-bundle-import` 和 `platform-auth-session-import`。cookie 文件会复制到私有目录并可直接用于授权公开搜索；Chrome/Playwright 会话文件或 Chrome profile 目录只登记为 `session-only` 授权引用，用于后续在线验收或人工交接，不冒充可直接采集的 cookie 能力。页面不展示真实 cookie/session 内容、bundle 内容或完整本地路径。

`reports/credential_doctor_dashboard.html` 是本地凭据体检页面，用于检查 search/auth 文件是否存在、JSON/dotenv 格式是否有效、搜索 key 字段是否仍为空或占位符、平台 cookie/session 文件是否存在、是否为空、是否过旧，以及文件权限是否过宽。体检只输出状态，不输出 API key、cookie、session 内容或完整本地 cookie 路径。

`reports/platform_auth_validation_dashboard.html` 是平台授权连通性验证页。`platform-auth-validate` 默认离线，只检查 B 站、抖音、快手、微博、知乎、微信公众号、小红书、头条的本地授权配置和 cookie/session 文件可用性；加 `--online` 后才会运行合规的最小在线验证。B站使用专用公开登录态接口；其他平台如果在本地 `platform_auth` 文件中配置了 `validation_url`、`success_markers`、`login_required_markers`、`captcha_markers`，会用本地 cookie 访问该验证 URL 并按标记判断 `passed`、`login_expired`、`captcha_or_security_check` 或 `login_state_uncertain`。验证结果只显示平台、状态、授权方式、凭据类型、验证范围、允许能力和错误类型，不显示 cookie、session、账号密码或完整本地路径。

`reports/search_validation_dashboard.html` 是搜索 API 与中文公开入口验证页。`search-validate --offline` 只检查 SerpAPI/Bing/Google CSE 是否已配置，并对百度、搜狗、360 的公开 HTML 搜索结果解析器做离线样本自检，不联网、不消耗配额；不带 `--offline` 时会对每个已配置 API provider 发起一条最小公开搜索请求，验证 key、engine、配额、网络和 API 版本是否可用。验证结果只显示 provider 状态、结果数量、样例域名和错误类型，不显示 API key。

`data/monitor/latest_status.json` 是面向 automation 和运行监控的机器可读状态文件。它汇总最近一次运行、报告文件是否存在、质量门槛、外部采集健康度、待生产队列、近期 timeline 和最近运行日志错误。也可以随时手动刷新：

```bash
python3 -m source_registry --db data/source_registry.sqlite status --json
```

## 行业优先级与队列规则

行业优先级配置在 `config/industry_priorities.json`。当前采用你确认的 40 个行业顺序，队列排序为：

```text
行业序号 > 时间倒序 > 中央到地方层级 > 文件优先级
```

默认只把 `2025-01-01` 之后的文件纳入等待队列。每次运行都会重新抓取所有启用来源并刷新队列；如果自动收集过程中发现更高优先级行业有新文件，会先回到该行业处理，直到该行业 pending 队列清空后再继续后续行业。

## 深度解读标准

主体分析目标不少于 10 页。报告主体固定拆成 10 个深度章节：

1. 原文定位、权威性与研究边界
2. 政策背景、问题导向与出台动因
3. 文件属性、适用范围与约束强度
4. 核心条款与政策工具拆解
5. 产业链、供应链与商业模式影响
6. 区域、部门与实施主体影响
7. 企业机会、受益方向与交易观察价值
8. 历史政策、既有研究与外部解读对照
9. 风险、不确定性与反向验证
10. 后续任务队列、监测指标与结论

每份政策解读报告至少覆盖：执行摘要、来源权威等级、政策属性、适用行业和地区、核心条款拆解、产业链影响、受益公司/标的候选、商业影响、交易观察价值、风险和不确定性、与历史政策或既有行研报告的关系、可进入行研或交易系统的任务队列。

政策结论必须区分官方原文、主管部门解释、外部研究/媒体解读和自动化推论。外部解读可用于补充观点差异、传播热度和市场关注点，但不能替代官方原文或附件。

当报告无法满足上述深度标准时，automation 输出必须明确列出缺口，并把该文件保留在待生产队列或标记为需要 Codex 深度解读/人工复核。

最终交付前需要你补充的信息见 [docs/final_delivery_inputs.md](docs/final_delivery_inputs.md)。

## 解读资料来源

除官方原文来源库外，系统现在新增了解读资料来源配置：

- `config/interpretation_sources.json`
- B 站政策解读公开视频搜索
- 中国政府网政策解读搜索
- 人民网政策解读搜索
- 新华网政策解读搜索
- 央视网政策解读搜索
- 第一财经政策解读搜索
- 抖音政策解读视频搜索
- 快手政策解读视频搜索
- 微博政策讨论搜索
- 知乎政策解读搜索
- 微信公众号政策解读搜索
- 小红书政策讨论搜索
- 今日头条政策解读搜索
- SerpAPI / Bing / Google CSE 全网公开搜索 API
- 百度 / 搜狗 / 360 中文公开搜索入口和可读结果页正文抽取

B 站当前通过公开视频搜索 API 采集标题、链接、UP 主、播放量、发布时间、简介、标签和相关度；对搜索结果会进一步尝试读取公开视频详情、公开作者页/账号画像、互动统计、分 P `cid`、公开字幕摘录、公开评论摘录和公开弹幕摘录。作者页只保存公开可见的账号名称、认证说明、粉丝量、等级和简介摘录，用于评估外部解读材料背景，不把 UP 主视为政府原文权威来源。如果公开 API 没有结果，会自动保留可点击搜索入口。受登录态影响的页面、受限评论或更完整弹幕明细，不要在聊天里发送账号密码；应通过 Chrome 已登录会话或本地安全 cookie 文件授权。

抖音、快手、微博、知乎、微信公众号、小红书和头条当前支持 `authorized_public_search` 桥接能力：当本地平台授权 cookie 文件可用时，系统会用该 cookie 请求配置的搜索页，解析公开结果链接，并对可访问页面做正文抽取；如果遇到登录过期、验证码、安全验证、付费墙或访问控制，只记录受限状态，不计入有效参考。该桥接能力不输出 cookie、session、账号密码或完整本地路径；平台专用的视频详情、评论、弹幕、作者页和互动指标解析仍在 parser 队列中单独推进。

搜索 API 当前支持 SerpAPI、Bing Web Search API 和 Google Custom Search JSON API。它们用于扩展券商/律所/咨询机构/智库/媒体/平台公开解读，不替代官方原文。没有 key 时系统会记录 `missing_api_key:*` 缺口并继续生成报告，不会把缺口误计为有效参考。脚本默认会对搜索 API 返回的公开网页做二次正文抽取；如果遇到登录、验证码或付费墙，只记录受限状态，不绕过访问控制，也不把该页面计入有效参考。

公开站内搜索当前支持中国政府网、人民网、央视网和第一财经等可直接 HTTP 访问的搜索页。系统会先解析搜索结果链接，再抓取同域公开文章正文，形成 `公开站内搜索结果；正文已摘录`。如果站内搜索页没有可解析结果、文章正文太短、遇到登录/验证码/付费墙或搜索页依赖前端脚本，系统只保留入口或受限状态，不把它计入 5 份有效参考。

百度、搜狗、360 作为中文公开搜索入口启用 `public_search_html`。系统会尝试解析公开结果页链接，优先使用 `data-url` 等真实外部地址，并解码常见 `url/u/target/to/link` 跳转参数，再抓取可公开访问的文章正文；搜索入口、搜索引擎自身页面、图片/微信搜索页、验证码、登录、付费墙和不可读页面都不计入有效参考。成功解析到的公开文章按最终文章域名计入外部平台。

已入库相关公开文件源启用 `local_related_documents`。它从当前内容库中查找同主题官方文件、答记者问、官方解读和相关政策，作为上下文参考进入报告；它不会把这些参考变成本报告主研究对象，也不会替代每份报告只研究一份文件的约束。计入参考前必须通过强主题匹配：短词如“药品”“医药”“实施细则”不能单独证明相关，必须命中“药品零售”“零售许可”“许可验收”“人工智能”等明确主题词；省政府公报、政策首页、政策库、宽泛规划等索引或泛相关页面不计入有效参考。

为提升公开搜索命中率，系统会清洗政策标题中的站点后缀、重复“政策解读”和征求意见类噪音，例如把“关于公开征求《某某细则》（征求意见稿）意见 省政府门户网站”压缩为“某某细则 政策解读”。搜索结果 URL 会修复常见 HTML 实体误解析，例如 `&timestamp` 被解析为 `×tamp` 的情况。若同一文件、同一来源、同一缺口类型因查询词优化产生新 URL，旧 pending 缺口会自动标记为 `ignored`，避免运营 dashboard 被过期搜索入口污染。

外部采集默认带轻量重试和限速，适合 unattended automation。可通过环境变量调整：

```bash
INTERPRETATION_REQUEST_RETRIES=2
INTERPRETATION_REQUEST_DELAY_SECONDS=0.5
FETCH_SEARCH_RESULT_PAGES=1
bash scripts/run_policy_report.sh
```

报告 dashboard 会把外部采集状态拆成缺 key、需授权、已配置授权、平台解析器待接入、公开站内搜索、公开网页正文摘录、受限页面、请求失败和搜索入口，便于决定下一步应该补 API key、接 Chrome 登录态，还是修复网络/接口。

外部参考缺口会写入正文库的 `external_reference_gaps` 表。它只保存脱敏后的缺口类型、平台、URL、状态、建议动作和优先级，不保存账号、密码、cookie 内容或本地敏感文件路径。常见建议动作包括：

- `provide_search_api_key`：补 SerpAPI/Bing/Google CSE 等搜索 key。
- `provide_platform_auth`：提供本地 Chrome/cookie/session 授权文件。
- `implement_platform_parser`：已有授权线索，但该平台详情解析器尚未接入。
- `refine_public_site_search`：公开站内搜索没有返回可用文章，需要调整关键词或站点规则。
- `review_candidate_url`：候选网页过短、受限或需要人工判断是否可计入。
- `retry_request`：网络、TLS、限速或站点临时失败，适合稍后重试。

缺口队列可通过 CLI 查询和复核：

```bash
python3 -m source_registry --db data/source_registry.sqlite gap-dashboard
python3 -m source_registry --db data/source_registry.sqlite gaps --status pending --json
python3 -m source_registry --db data/source_registry.sqlite gaps --required-action provide_search_api_key
python3 -m source_registry --db data/source_registry.sqlite gap-review gap_xxx --status ignored --reviewer linze --note "低相关候选链接"
python3 -m source_registry --db data/source_registry.sqlite gap-bulk-review --required-action review_candidate_url --status ignored --dry-run
```

`gap-review` 只改变缺口状态，不会删除历史记录。下一次运行如果同一已解决缺口再次出现，会重新置为 `pending`，保证真实阻塞不会被永久隐藏。

`gap-dashboard` 默认生成 `reports/external_reference_gap_dashboard.html`。页面包含按建议动作、平台、状态分布的条形图、最高优先级缺口表和交互式缺口复核工作台。工作台支持按动作、平台、状态和关键词筛选，勾选当前筛选结果，生成 `gap-bulk-review --dry-run` 批量预演命令，或为已勾选 gap 生成单条 `gap-review` 命令文本。页面只展示缺口元数据，不展示 API key、cookie 或账号密码；批量状态变更仍需要先 dry-run 并由你确认。

配置 readiness 可随时检查：

```bash
python3 -m source_registry --db data/source_registry.sqlite setup-config --dry-run
python3 -m source_registry --db data/source_registry.sqlite readiness \
  --search-secrets-file /secure/path/policy-search-secrets.json \
  --platform-auth-file /secure/path/policy-platform-auth.json
```

该命令只显示 key 是否存在、平台授权文件是否配置/可读、中文搜索入口是否在配置中启用，以及当前缺口动作分布；不会打印 API key、cookie 内容、session 内容或本地 cookie 文件路径。

本地配置模板可由 `setup-config` 生成：

```bash
python3 -m source_registry --db data/source_registry.sqlite setup-config
```

默认生成：

- `~/.policy-intelligence/policy-search-secrets.json`
- `~/.policy-intelligence/policy-platform-auth.json`
- `~/.policy-intelligence/search_api_bundle.example.json`
- `~/.policy-intelligence/platform_auth_bundle.example.json`
- `~/.policy-intelligence/cookies/`

`setup-config` 会给出 `SEARCH_SECRETS_FILE` 和 `PLATFORM_AUTH_FILE` 的 export 命令，并生成两个可编辑的 bundle 示例文件。它只写空 key 字段、占位 bundle 值和 cookie/session 路径，不创建空 cookie 文件；否则 readiness 可能把空文件误判为可用授权。你需要在浏览器或平台工具里导出 cookie/session 后，把真实文件放到对应路径。

有效参考的计数规则：

- 计入：公开视频结果、可读取文章/研究/新闻结果、具备可读摘要或摘录的公开资料。
- 不计入：单纯搜索入口、需登录/验证码来源、付费墙/会员专享页面、公开 API 未返回结果时保留的入口。
- 默认最低要求：`MIN_EXTERNAL_REFERENCES=5`。
- 默认最低平台要求：`MIN_EXTERNAL_PLATFORMS=2`。
- 报告顶部会显示 `有效参考 X/5`、`外部平台 Y/2` 和达标状态。

可选登录态配置：

```bash
export BILIBILI_COOKIE_FILE=/path/to/bilibili_cookie.txt
FETCH_INTERPRETATION_RESULTS=1 bash scripts/run_policy_report.sh
```

多平台授权状态配置：

```bash
cp config/platform_auth.example.json /secure/path/policy-platform-auth.json
# 修改 /secure/path/policy-platform-auth.json 内各平台 cookie_file 路径。
# 不要把真实 cookie、账号、密码写入项目或聊天。
PLATFORM_AUTH_FILE=/secure/path/policy-platform-auth.json \
FETCH_INTERPRETATION_RESULTS=1 \
bash scripts/run_policy_report.sh
```

更推荐的接入方式是先把浏览器导出的 cookie 文本保存到一个本地临时文件，再交给安全导入命令处理；该命令会复制到 `~/.policy-intelligence/cookies/`、设置私有权限、更新 `policy-platform-auth.json`，并只输出脱敏状态：

```bash
PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-import \
  --platform bilibili \
  --source-file /path/to/exported_bilibili_cookie.txt \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json

PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite credential-doctor \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json
```

如果一次导出多个平台 cookie，把文件放到同一目录并命名为 `<platform>_cookie.txt`，例如 `bilibili_cookie.txt`、`zhihu_cookie.txt`、`weibo_cookie.txt`、`toutiao_cookie.txt`，再批量导入：

```bash
PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-bulk-import \
  --source-dir /path/to/exported_cookie_dir \
  --platform-auth-file ~/.policy-intelligence/policy-platform-auth.json
```

当前系统会读取授权配置并在报告中标记：

- `未配置授权文件`：该平台只能保留搜索入口或公开 API 结果。
- `授权文件不存在或不可读`：路径已配置，但当前机器无法读取。
- `授权文件可用；待接入平台解析器`：本地授权文件存在，但该平台的正文/评论/作者页解析器还未接入，不能计入有效参考。
- `授权文件已配置；公开 API 未返回结果`：授权存在，但公开视频搜索仍未返回可用资料。

授权状态只保存布尔状态、能力清单和缺口说明；不会把 cookie 内容写入报告、日志或数据库。

可选搜索 API key 配置：

```bash
cp config/secrets.example.json /secure/path/policy-search-secrets.json
# 填入 SERPAPI_API_KEY / BING_SEARCH_API_KEY / GOOGLE_SEARCH_API_KEY / GOOGLE_CSE_ID
SEARCH_SECRETS_FILE=/secure/path/policy-search-secrets.json bash scripts/run_policy_report.sh
```

更推荐的方式是把 key 保存到本地临时文件，再用安全导入命令写入 `~/.policy-intelligence/policy-search-secrets.json`；命令输出不会展示 key：

```bash
PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-import \
  --provider bing \
  --value-file /path/to/bing_search_api_key.txt \
  --search-secrets-file ~/.policy-intelligence/policy-search-secrets.json

PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-import \
  --provider google \
  --value-file /path/to/google_search_api_key.txt \
  --engine-id-file /path/to/google_cse_id.txt \
  --search-secrets-file ~/.policy-intelligence/policy-search-secrets.json
```

也可以直接使用环境变量：`SERPAPI_API_KEY`、`BING_SEARCH_API_KEY`、`GOOGLE_SEARCH_API_KEY`、`GOOGLE_CSE_ID`。cookie 和 API key 文件只应放在项目外或受控 secret 路径，不要提交到版本库。

## 已知限制

- 目前不自动绕过验证码、登录、付费墙或访问控制；B 站公开 API 或搜索 API 失败时会回退到搜索入口/缺口线索。
- “政府网站基本信息下载”支持导入用户下载的 CSV/ZIP；未内置隐藏下载接口探测。
- 智库、蓝皮书、官方媒体会被标记为非政府原文来源，即使评分较高也需要在报告中单独说明。
- DOCX/XLSX 使用内置 XML 解析；PDF 文本层依赖本机可用的 `pypdf` 或 `PyMuPDF`。扫描版 PDF 和图片附件会尝试可选 OCR，依赖 `PyMuPDF`、`Pillow`、`pytesseract` 和本机 Tesseract 语言包；依赖缺失时会记录 `ocr_unavailable:*`，不会把空结果当作成功解析。旧版 DOC/XLS/PPT/RTF/ODT/ODS/EPUB 可在配置 `TIKA_SERVER_URL` 后走 Apache Tika；研究 PDF 可在配置 `GROBID_SERVER_URL` 后抽取标题、作者、章节和参考文献。未配置外部服务时只记录缺口，不承诺成功解析。
