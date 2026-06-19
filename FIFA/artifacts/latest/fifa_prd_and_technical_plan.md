# FIFA / 足球结果竞猜分析系统 PRD 与技术方案

## 需求访谈总结

原本需要确认的关键问题：

- 系统服务对象：待确认。默认 MVP 假设为个人分析使用。
- 第一目标：待确认。默认同时覆盖分析准确性、数据自动化基础、报告生成和 API 可视化文档。
- 赛事范围：待确认。默认支持国家队和俱乐部比赛，优先面向 2026 US Canada Mexico FIFA 相关赛事。
- 竞猜范围：待确认。默认先实现胜平负概率；比分、让球、大小球、角球、红黄牌、冠军预测保留扩展字段和后续模型方向。
- 是否涉及真实金钱下注：待确认。默认系统只做概率分析和决策支持，不执行下注。
- 数据源/API Key：待确认。默认无付费数据源、无 API Key，先支持手动 JSON/CSV 导入和合规公开源配置。
- 赔率数据：待确认。默认不抓取 TAB；仅保留合法授权数据接入位置。
- 新闻、社交、搜索趋势：待确认。默认以导入或合规公开 API 方式进入 `news_sentiment`、`trend_score`。
- 模型：默认先用可解释规则模型，后续可增加机器学习。
- 回测指标：默认胜平负准确率、分结果准确率、Brier Score、Log Loss。
- 前端：待确认。默认用 FastAPI OpenAPI 文档作为基础 Web/API 页面。
- 报告：默认实现 Markdown 赛前报告。
- 定时任务/通知：待确认。默认只设计，不在 MVP 中启用。
- 权限：默认本地单用户，无登录；表结构为后续权限预留。
- 数据更新频率：默认每半天，但 MVP 不启动后台定时抓取。

这些待确认项不会阻止 MVP 开发，因为当前版本将不确定业务项做成可配置、可导入、可扩展字段，并在输出中保留缺失数据告警。

## PRD

### 背景

围绕 2026 US Canada Mexico FIFA / 足球赛事，构建一个公开信息收集、数据清洗、赛前趋势分析、结果概率预测、历史回测和报告生成系统。

### 项目目标

- 统一管理球队、赛事、比赛、近期状态、新闻/趋势信号。
- 基于可解释规则模型输出主胜/平局/客胜概率。
- 保存每次预测，支持赛后回测。
- 生成带免责声明的赛前分析报告。
- 为后续赔率、伤停、阵容、舆情和搜索趋势接入预留接口。

### 非目标

- 不自动下注。
- 不保证收益。
- 不绕过验证码、登录、付费墙、IP 限制或平台风控。
- 不批量注册账号。
- 不做盘口操纵。
- 不实现未经授权的数据抓取。
- 不把 TAB 或任何平台数据作为唯一推荐依据。

### 用户角色

- 个人分析者：录入或导入比赛数据，查看概率和报告。
- 数据维护者：配置公开数据源，导入球队状态和比赛结果。
- 后续管理员：待确认，MVP 不实现登录。

### 使用场景

- 赛前录入比赛和球队状态，生成胜平负概率。
- 比赛结束后补充比分，运行回测。
- 生成每日/每周或单场 Markdown 报告。
- 配置公开数据源并记录抓取任务日志。

### 核心业务流程

1. 创建球队和赛事。
2. 创建比赛。
3. 导入近期球队状态、新闻情绪和趋势信号。
4. 调用预测 API。
5. 系统保存预测和影响因素。
6. 赛后更新比分和状态。
7. 运行回测并查看指标。
8. 生成报告。

### 功能列表

- 球队管理：创建、列表。
- 赛事管理：创建、列表。
- 比赛管理：创建、列表、详情、批量导入。
- 球队状态导入。
- 数据源配置和任务日志。
- 规则模型预测。
- 预测详情和解释因素。
- 回测指标计算。
- Markdown 报告生成。
- OpenAPI 文档。

### MVP 数据字段

| 表 | 字段 | 类型 | 必填 | 示例 | 业务含义 | 数据来源 | 更新时间 |
|---|---|---:|---|---|---|---|---|
| teams | id | integer | 是 | 1 | 球队 ID | 系统生成 | 创建时 |
| teams | name | text | 是 | Australia | 球队名 | 手动/API | 变更时 |
| teams | country | text | 否 | AU | 国家/地区 | 手动/API | 变更时 |
| teams | team_type | text | 是 | national | 国家队/俱乐部 | 手动 | 变更时 |
| teams | fifa_rank | integer | 否 | 25 | FIFA 或其他排名 | 手动/API | 排名更新时 |
| competitions | id/name/season/region | mixed | name 必填 | World Cup | 赛事信息 | 手动/API | 赛季更新 |
| matches | home_team_id/away_team_id | integer | 是 | 1/2 | 对阵双方 | 手动/API | 赛程更新 |
| matches | match_time | text | 是 | 2026-06-12T20:00:00Z | 比赛时间 | 手动/API | 赛程更新 |
| matches | status/home_score/away_score | mixed | 否 | finished/2/1 | 比赛结果 | 手动/API | 赛后 |
| team_stats | recent_points | integer | 是 | 10 | 近期积分 | 导入/计算 | 每半天或赛后 |
| team_stats | recent_goals_for/against | real | 是 | 9/4 | 近期进失球 | 导入/计算 | 每半天或赛后 |
| team_stats | injury_impact | real | 是 | 0.2 | 伤停影响 0-1 | 导入/人工 | 赛前 |
| team_stats | fatigue_index | real | 是 | 0.3 | 疲劳影响 0-1 | 赛程计算 | 每半天 |
| team_stats | news_sentiment/trend_score | real | 是 | 0.1 | 新闻/趋势 -1 到 1 | 导入/API | 每半天 |
| news_articles | title/url/source/sentiment | mixed | title 必填 | injury update | 新闻记录 | 合规公开源 | 抓取/导入 |
| predictions | probabilities/recommended_result | mixed | 是 | 0.55/home_win | 预测输出 | 模型生成 | 每次预测 |
| prediction_factors | name/formula/weight/value/effect | mixed | 是 | recent_form | 可解释因素 | 模型生成 | 每次预测 |
| model_versions | version/weights_json | text | 是 | rules-v1.0.0 | 模型版本 | 系统配置 | 模型变更 |
| crawl_sources | name/base_url/enabled | mixed | 是 | FIFA API | 数据源配置 | 手动 | 变更时 |
| crawl_jobs/logs | status/message | mixed | 是 | skipped | 任务审计 | 系统生成 | 每次任务 |
| reports | title/content_markdown | text | 是 | 赛前报告 | 报告内容 | 系统生成 | 每次报告 |

### 权限规则

MVP 本地单用户，不启用登录。后续可增加 `users`、`roles`、`audit_logs` 并将写操作限制为管理员。

### 异常场景

- 缺少球队状态：预测继续执行，返回 `home_team_stats_missing` 或 `away_team_stats_missing`。
- 缺少排名：使用中性值，返回 `fifa_ranking_missing`。
- 无完赛样本：回测返回空样本提示。
- 非授权抓取：任务记录为 skipped，不执行绕过式抓取。

### 数据源规则与爬虫合规

- 优先官方 API、授权 API、公开下载、手动 CSV/JSON。
- 配置源前需确认条款。
- 不绕过验证码、登录、付费墙、IP 限制或反爬机制。
- TAB 等赔率源仅在合法授权和条款允许时接入。

### 预测展示规则

- 展示主胜/平局/客胜概率，三者和为 1。
- 推荐倾向为最高概率结果。
- 置信度：最高概率与第二高概率差值大于等于 0.20 为 high，大于等于 0.10 为 medium，否则 low。
- 必须展示关键因素、缺失数据告警、模型版本、生成时间和免责声明。

### 回测规则

- 保存每次预测。
- 比赛结束后用真实比分计算实际结果。
- 指标：胜平负准确率、主胜预测准确率、平局预测准确率、客胜预测准确率、Top prediction accuracy、Brier Score、Log Loss、预测数量、样本时间范围、模型版本。
- 如后续涉及赔率收益测算，公式为：收益率 = 总收益 / 总投入；预测正确收益 = 投入金额 × 赔率 - 投入金额；预测错误收益 = -投入金额。

### 验收标准

- 能启动 API 并访问 `/docs`。
- 能创建球队、赛事、比赛。
- 能导入球队状态。
- 能生成并保存预测。
- 预测输出包含概率、推荐倾向、置信度、因素、缺失告警、免责声明。
- 能对完赛比赛运行回测。
- 能生成 Markdown 报告。
- 核心测试通过。

## 技术方案

### 技术栈

- Backend/API: FastAPI
- DB: SQLite
- Config: `.env` / environment variables
- Tests: Python `unittest`
- Docs: README + Markdown PRD

### 前端页面

MVP 使用 FastAPI `/docs` 作为基础 Web 操作页面。后续可加 React/Vue 看板。

### 后端 API

已实现核心和扩展 MVP API，详见项目 README。

### 数据库表

已实现：`teams`、`competitions`、`matches`、`team_stats`、`news_articles`、`model_versions`、`predictions`、`prediction_factors`、`prediction_results`、`crawl_sources`、`crawl_jobs`、`crawl_logs`、`reports`。

### 文件结构

```text
work/fifa-analysis-system/
  app/
    config.py
    constants.py
    database.py
    main.py
    models.py
    services.py
  tests/
    test_services.py
  .env.example
  README.md
  requirements.txt
```

### 模型设计

规则模型将近期状态、进攻、防守、排名、主场、伤停、疲劳、新闻、趋势加权为三个结果分数，再用 softmax 转换为概率。缺失数据使用中性默认值并输出 warning。

### 定时任务方案

MVP 不启动后台定时任务。建议后续用 cron、APScheduler 或队列按每半天触发导入和报告任务。

### 日志和监控

MVP 记录 `crawl_jobs` 和 `crawl_logs`。后续增加结构化应用日志、错误率、任务耗时和数据质量指标。

### 部署方案

本地运行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 安全和合规

- 敏感配置只走环境变量。
- 不硬编码 API Key。
- 不实现下注和绕过式抓取。
- 预测和报告固定输出免责声明。

### 可回滚设计

- MVP 是独立目录，不影响其他项目。
- SQLite 数据文件可备份/删除。
- 回滚代码可删除 `work/fifa-analysis-system`。

## 待确认项

- 真实使用的数据源和授权方式。
- TAB 数据是否有合法 API 或许可。
- 是否需要真实前端看板。
- 是否需要 PDF、Notion、邮件或通知。
- 比分、让球、大小球、角球、红黄牌和冠军预测的详细业务规则。
- 机器学习模型是否进入下一阶段。
- 多用户权限和部署环境。
