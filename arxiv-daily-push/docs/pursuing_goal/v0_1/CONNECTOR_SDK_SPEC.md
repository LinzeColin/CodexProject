# Official Connector SDK Spec · ADP-S3-P01-T031

中国 A0 中央国家级官方源的**极简连接器内核**：只保留试点必需的 7 项能力，**零第三方依赖（stdlib only）**、
**无业务 UI / 无知识图谱 / 无新平台耦合**。工具：`tools/official_connector.py`。**NOT_DEPLOYED**——这是 SDK，
尚未接入 worker/D1；真实 A0 适配器在 T034+。

## 七项能力（typed contract）

| 能力 | 签名 | 说明 |
|---|---|---|
| `discover(cursor)` | → `[DiscoverItem]` | 从官方列表/目录页发现文档入口（增量从 cursor 起） |
| `fetch(url, fetched_at)` | → `FetchResult` | **真实 HTTP GET**（`HttpFetcher`，stdlib urllib，带 UA/超时/大小上限）；返回 status/bytes/sha256/ok |
| `verify(item, fetched)` | → `VerifyResult` | 官方身份校验：官方域、主办单位、A0/A1/A2 分级、原因 |
| `normalize(item, fetched)` | → `NormalizedDoc` | 抽取标题/文号/成文日期/效力状态/正文/authority + canonical_hint（对接 T024 身份） |
| `attachments(fetched)` | → `[Attachment]` | 原文附件（PDF/doc）链接 + 可选 sha256 |
| `cursor(docs)` | → `Cursor` | 推进增量游标（last_id/last_date），支持去重与断点 |
| `health()` | → `HealthResult` | 源可达性/契约健康自检 |

数据类型全部是 stdlib `dataclass(frozen=True)`：`DiscoverItem / FetchResult / Attachment / NormalizedDoc /
VerifyResult / HealthResult / Cursor`。`schema_version = adp.official_connector.v0_1`。

## SDK 组成

- `OfficialConnector`（ABC）：每个 A0 适配器实现的**唯一接口**，恰好 7 个抽象方法，别无其他。
- `HttpFetcher`：**真实 GET**（urllib，无第三方），UA=`ADP-A0-connector/0.1 (+research; single-GET)`，超时 15s、大小上限 5MB，网络/SSL/超时失败返回 `ok=False` 而非崩溃。
- `AdapterRegistry`：`source_id → connector`，重复 id 报错；无动态 import 魔法。
- `run_chain(connector, cursor, fetched_at)`：一次驱动全链路 `health → discover →（fetch → verify → normalize → attachments）* → cursor`，返回结构化 trace；纯编排、自身无 I/O。

## 确定性与真实抓取（Owner 决策：内核阶段就接真实抓取）

- **契约测试确定性**：`run_chain` 全链路跑在 `MockOfficialConnector`（canned fixture）上；`HttpFetcher` 的真实 GET 在**本地 loopback HTTP server** 上验证字节/哈希——**CI 无外网**、可复现。
- **真实抓取已在内核接通**：`HttpFetcher` 是真 urllib GET；`evidence/…/real_fetch_smoke.json` 为**实抓 gov.cn 的 live 时点证据**（`www.gov.cn` 200/67KB「中国政府网」、`gov.cn/zhengce/` 200/40KB「政策_中国政府网」，官方域校验通过）。live 证据**不逐字可复现**（站点会变），只提交元数据 + 标题摘录，不提交整页 HTML。

## 边界（验收）

- **无业务 UI、无图谱、无新平台耦合**：SDK 仅 stdlib；测试断言源码不含 `requests/flask/django/networkx/neo4j/fastapi` 等。
- **一个 mock connector 全链路通过**：`MockOfficialConnector` 经 `run_chain` 全 7 能力通过（health/discover2/fetch/verify A0/normalize 含文号·日期·状态/attachments/cursor 推进到最新日期）。
- **NOT_DEPLOYED**：未接 worker/D1；真实适配器（国务院政策/法规、统计/发改委、网信办/国家数据局）在 T034–T036，接入 worker cron 后每次 fetch 记为 worker 子请求，须核 DIR-007 免费额度。
