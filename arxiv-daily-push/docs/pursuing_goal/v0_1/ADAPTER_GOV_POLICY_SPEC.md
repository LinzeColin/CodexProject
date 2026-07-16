# A0 Adapter Spec · 国务院政策文件 / 国家法律法规（ADP-S3-P02-T034）

首个真实 A0 官方适配器：把 gov.cn 政策文件库（`/zhengce/content/*.htm`）与法规入口解析成 A0 样板——
原文标题、发文字号、发文机关、**类型化日期（成文日期 vs 发布日期，保持不混淆）**、效力状态、附件。
工具：`tools/adapter_gov_policy.py`，基于 T031 SDK、T033 身份、T032 契约。**NOT_DEPLOYED**（真抓走开发环境；未接 worker）。

## 真实 DOM（实测 gov.cn 政策页）

政策页含一张元信息表：`<b>发文字号：</b></td> <td>国办发〔2020〕50号</td>`，字段包括
发文机关 / 发文字号 / 成文日期 / 发布日期 / 主题分类 / 有效性。`_meta(html, 标签)` 逐字段抽取。
实测多样文种均可解析：通知（国办发〔2020〕50号）、国务院令（国令第711号）、国办函（国办函〔2021〕132号）。

## 类型化日期（核心：不混淆）

- **成文日期（written）** 与 **发布日期（published）** 是**两个不同字段**，解析后分别存于 `dates.{written, published}`，**绝不合并**。
- 真实存在跨年差异：国办函〔2021〕132号 成文 **2021-12-22**、发布 **2022-01-04**——若混淆会把年份归错。
- SDK `NormalizedDoc.doc_date` = **发布日期**（canonical publish）；成文日期在 `parse_policy` 中完整保留。
- 中文/ISO 日期归一化 `norm_date`：`2020年12月07日` → `2020-12-07`；无法解析返回 `None`（不臆造）。

## 能力（T031 SDK 7 项）

`discover`（解析政策列表 content 链接 + URL 内日期；按 `cursor.last_date` 断点续爬）、`fetch`（真实
HttpFetcher / 测试用 FixtureFetcher）、`verify`（走 T033 official_identity → A0）、`normalize`（→ NormalizedDoc，
doc_date=发布）、`parse_policy`（完整 A0 模板含类型化日期）、`attachments`（pdf/doc/docx/wps/xls）、
`cursor`（推进到最新发布日期）、`health`。`build_registry` 注册 **gov-cn-policy（政策）+ gov-cn-fagui（法规）** 两源共用一套解析。

## 验收（`test-results/adapter_tests.txt`，PASS）

- **官方原文和附件可回放**：2016/2020/2024/current 四期 fixture 解析 == golden，二次解析**逐字一致**，附件（0/0/1/2）可回放。
- **日期类型不混淆**：四期 written==成文、published==发布、doc_date==发布，**从不交换/合并**。
- **历史游标可恢复**：discover 全量 4 项；`cursor(last_date=2020-12-21)` 只返回其后 `[2024-03-01, 2026-07-10]`；cursor 推进到最新 `2026-07-10`。
- **live 实抓**：`real_parse_smoke.json` = 实测 3 篇真实 gov.cn 文件（通知/国令/国办函）解析，日期类型全部 distinct（含 2021→2022 跨年）。

## 边界

fixtures 为**贴合真实模板的结构化样本**（title + 元信息表 + 附件；正文从略以不复制版权原文）；2020 期镜像真实文件字段。
真实各年模板细节差异由契约 harness（T032）+ 后续 fixtures 兜底。真抓走开发环境（0 云成本）；接 worker cron 属后续，届时核 DIR-007 子请求预算。
