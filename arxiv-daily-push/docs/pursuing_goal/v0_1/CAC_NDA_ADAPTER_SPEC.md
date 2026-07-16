# A0 Adapter Spec · 网信办 / 国家数据局（ADP-S3-P02-T036）

两个 A0 适配器（cac.gov.cn 网信办 / nda.gov.cn 国家数据局），覆盖 AI / 网络安全 / 数据治理 / 国家数据政策第一线内容。
工具：`tools/adapter_cac_nda.py`，基于 T031 SDK + T033 身份。**NOT_DEPLOYED**。核心：**文档类型分类器**，官方原文为 primary。

## 文档类型分类（四类可区分）

`classify_doc_type(title, url, text)` → `DocType{doc_type, is_primary, consultation_status, deadline}`：
- **consultation（征求意见）**：标题/URL 含 征求意见/公开征求/意见征集/征求意见稿。**is_primary=True**（征求意见稿本身是官方原件）；解析 `consultation_status`（open/closed）+ `deadline`（意见反馈截止日期）。
- **formal（正式文件）**：含 办法/规定/通知/公告/令/条例/决定/指南 且非新闻、非解读。**is_primary=True**（官方原文）。
- **interpretation（解读）**：含 解读/答记者问/图解/政策问答/一图读懂。**is_primary=False**（指向正式文件）。
- **news（新闻）**：考察/会见/座谈/会议/讲话/动态等。**is_primary=False**。

**官方原文为 primary**：consultation 与 formal 是 primary；解读/新闻是 secondary（回指官方原文）。

## 能力与来源

`CacNdaConnector`（T031 SDK 7 能力）：discover（`c_N.htm`/`content_N`/`t{YYYYMMDD}_N` 列表）、fetch（真实 HttpFetcher）、
verify（走 T033→A0）、normalize（标题 + doc_type + is_primary + consultation_status）、attachments（pdf/doc/wps/xls）、cursor、health。
`build_registry` 注册 **cac-gov + nda-gov**。

## 访问限制（如实记录，未伪造）

- `www.cac.gov.cn`：正常服务（首页 200；实测分类真实征求意见/新闻链接正确）。
- `www.nda.gov.cn`（国家数据局）：返回 JS shell（193B）且拒绝默认 TLS（`TLSV1_ALERT_PROTOCOL_VERSION`）——**纯 urllib 客户端 live fetch 被阻**。`nda-gov` 已注册但 `health().ok=False`，note 记「needs browser or RSS/API entry」。接该源需 `mcp__Claude_Browser` 或其 RSS/API，属后续；**不臆造该源内容**。

## 验收（`test-results/cac_tests.txt`，PASS）

- **四类可区分**：consultation/formal/interpretation/news 分类正确。
- **官方原文为 primary**：consultation+formal primary=True；解读+新闻 primary=False。
- **consultation status**：open + 截止 2026-08-10 解析正确。
- **live 实测**：`real_cac_smoke.json` = 实测 cac.gov.cn 首页链接分类（习近平考察=news、征求意见稿=consultation primary）。nda-gov health 如实 blocked。
