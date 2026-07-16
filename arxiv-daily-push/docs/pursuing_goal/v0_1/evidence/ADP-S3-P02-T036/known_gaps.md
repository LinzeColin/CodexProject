# Known gaps · ADP-S3-P02-T036

- **NOT_DEPLOYED（任务边界，非缺陷）**：适配器未接 worker cron / D1。cac live 分类走**开发环境**（0 云成本）；接 worker 后每 fetch = Worker 子请求，须核 DIR-007。
- **nda.gov.cn（国家数据局）live fetch 被阻（如实记录，未伪造）**：返回 JS shell（193B）+ 拒绝默认 TLS（TLSV1_ALERT_PROTOCOL_VERSION）。`nda-gov` 已注册但 `health().ok=False`（note: needs browser or RSS/API entry）。真正接该源需 `mcp__Claude_Browser` 或其 RSS/API/放宽 TLS 上下文，属后续任务；**本任务不臆造该源内容**。
- **分类为标题/URL 关键词 + 文号启发**：`classify_doc_type` 靠关键词（征求意见/解读/办法·规定·令/考察·会议）+ 文号存在性；边缘标题（如「关于XX办法的解读」同含 formal+interp 词）优先 interpretation（解读优先，安全：不把解读当原文）。真实边缘样本由后续 fixtures 增补。
- **consultation status 简化**：open/closed + 截止日期正则；「已结束/征集结束」判 closed，「公开征求/欢迎反馈」判 open。复杂表述可能判 None（保守）。
- **fixtures 为结构化样本**：consultation/formal/interpretation/news fixtures 贴合真实 cac 语言；真实各栏目 DOM 差异由 T032 契约 + 后续 fixtures 兜底；live 不逐字复现。
