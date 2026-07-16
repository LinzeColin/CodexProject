# Known gaps · ADP-S3-P02-T035

- **NOT_DEPLOYED（任务边界，非缺陷）**：适配器未接 worker cron / D1。真抓走**开发环境**（0 云成本）；接 worker 后每 fetch = Worker 子请求，须核 DIR-007。
- **抽取聚焦叙述式，不做表格抽取**：`extract_stat_claims` 抽取**叙述式**统计陈述（如「国内生产总值1349084亿元，同比增长5.0%」），这是 stats 发布正文主形式。**表格数据**（单位在列头、值在单元格，如 GDP 初步核算数据表）**不在本任务抽取范围**——实测真实 GDP 表格页抽取 0 条（表结构需专门的表抽取，属后续）。narrative 发布（经济运行）实测抽 21 条。
- **indicator 词表有限**：`INDICATORS` 覆盖 GDP/CPI/PPI/工业增加值/零售/投资/失业率等主指标；分产业增加值（第一产业增加值等）等未列入 → 跳过（不臆造）。可按需扩展词表。
- **口径/期间取最近标记**：basis 取值窗口内最近 口径 词，period 取标题/正文首个年份/季度/月份；复杂多期间同段落可能归并到同一 period（保守）。
- **发改委共用统计连接器**：ndrc-gov 用同一 `OfficialStatConnector`；发改委政策文件/公告的文号/日期若需，走 T034 的政策解析（同 gov.cn 模板），本任务聚焦统计 claim。
- **fixtures 为结构化样本**：stats/ndrc fixtures 贴合真实语言/模板；2024 期镜像真实 GDP 口径。真实各期差异由 T032 契约 + 后续 fixtures 兜底；live 实测不逐字复现。
