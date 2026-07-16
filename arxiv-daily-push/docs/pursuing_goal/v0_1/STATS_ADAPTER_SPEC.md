# A0 Adapter Spec · 国家统计局 / 发改委（ADP-S3-P02-T035）

两个 A0 官方适配器（stats.gov.cn / ndrc.gov.cn）+ **统计 Claim 抽取器**。工具：`tools/adapter_stats_ndrc.py`，
基于 T031 SDK + T033 身份。**NOT_DEPLOYED**（真抓走开发环境）。核心：**统计事实只来自官方数字，不从媒体数字形成事实**。

## 统计 Claim（记录单位/期间/口径/修订）

`StatClaim{indicator, value, unit, period, basis(口径), revision, source_id, authority_level, is_fact}`。
`extract_stat_claims(text, source_id, authority_level, title)`：
- **indicator**（指标）：国内生产总值/GDP、CPI/PPI、规模以上工业增加值、社会消费品零售总额、固定资产投资、城镇调查失业率…
- **value + unit**（值+单位）：`亿元/万亿元/元/%/百分点/万人/万吨`。
- **period**（期间）：从标题/正文取 `2024年` / `2026年二季度` / `2024年6月`。
- **basis 口径**：`同比/环比/比上年同期/累计/当月/当季/不变价/现价/可比价/两年平均`（取值窗口内最近标记）。
- **revision 修订**：`初步核算/初步统计/最终核实/修订/初步预计`（真实数据存在初步核算→最终核实的修订）。

## 硬规则：不从媒体数字形成事实

`claims_to_facts(claims)` 只保留 `is_fact=True`；`is_fact = authority_level ∈ {A0, A1}`。媒体/搜索源的相同数字被**记录为 claim 但不晋升为 fact**。落实 T033（media/search discovery-only）+ T012 registry（media 不得 official_evidence）。

## 能力与来源

`OfficialStatConnector`（T031 SDK 7 能力）：discover（解析 `t{YYYYMMDD}_N.html` 发布列表 + 断点续爬）、fetch（真实 HttpFetcher）、verify（走 T033→A0）、normalize（标题 + 统计 claim 计数 + 修订）、attachments（pdf/doc/xls/csv 数据表）、cursor、health。`build_registry` 注册 **stats-gov（统计局）+ ndrc-gov（发改委）**；发改委同时覆盖政策文件/公告（元信息表同 gov.cn 模板）。

## 验收（`test-results/stats_tests.txt`，PASS）

- **统计 Claim 记录单位/期间/口径/修订**：官方发布 fixture → 5 条 claim，**每条都有 unit+period+revision**，增长率类带 口径（同比/比上年）；GDP 绝对值 1349084亿元 / 2024年 / 初步核算。
- **不从媒体数字形成事实**：同一文本 official→5 facts，**media→0，search→0**。
- **live 实测**：`real_stats_smoke.json` = 实测 stats.gov.cn 真实「上半年经济运行」发布 → **21 条 official claim → 21 facts；media→0 facts**（含 国内生产总值695704亿元/同比/初步核算）。

## 边界

抽取聚焦**叙述式**统计陈述（stats 发布正文的主要形式）；**表格数据**（单位在列头、值在单元格）非本任务抽取范围（见 known_gaps）。indicator 词表可扩展；fixtures 为贴合真实 stats 语言的结构化样本，2024 期镜像真实 GDP 口径。
