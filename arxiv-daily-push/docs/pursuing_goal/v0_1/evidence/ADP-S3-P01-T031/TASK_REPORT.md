# TASK_REPORT · ADP-S3-P01-T031｜实现最小 Official Connector Interface

## 唯一目标（达成）
为中国 A0 官方源试点实现**极简连接器内核**：只保留 discover/fetch/verify/normalize/attachments/cursor/health 必需能力，交付 **connector SDK、typed contract、adapter registry**；**无业务 UI/图谱/新平台耦合，一个 mock connector 全链路通过**。按 Owner 决策，**内核阶段就接真实 HTTP fetch**。

## 六个开始前问题（已回答）
1. **唯一目标**：7 能力的 Official Connector 接口 + typed contract + adapter registry；mock 全链路通过；内核接真实 fetch。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/official_connector.py, CONNECTOR_SDK_SPEC.md}` + 本证据包（real_fetch_smoke / test-results / 报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题动效、worker、生产 D1/R2、cron；不引入第三方/新平台/UI/图谱。NOT_DEPLOYED（SDK 未接 worker）。
4. **基线**：main `1e3b33e4`（T030 收尾 S2 已合入）。连接性实测：gov.cn/stats/ndrc/cac 可达 200，nda.gov.cn 193B（JS shell）。
5. **验收**：无业务 UI/图谱/新平台耦合；一个 mock connector 全链路通过。
6. **回滚**：`git revert <sha>`（纯 SDK，NOT_DEPLOYED，生产未变更）。

## 交付物
- `tools/official_connector.py` —— **stdlib-only** SDK：`OfficialConnector`(ABC，7 抽象能力) + typed dataclasses（DiscoverItem/FetchResult/Attachment/NormalizedDoc/VerifyResult/HealthResult/Cursor）+ **`HttpFetcher`（真实 urllib GET，UA/超时/大小上限/失败不崩）** + `AdapterRegistry`(source_id→connector，拒重复) + `run_chain`(全链路驱动)。
- `CONNECTOR_SDK_SPEC.md` —— 7 能力契约、SDK 组成、确定性与真实抓取边界。
- `evidence/.../real_fetch_smoke.json` —— 实抓 gov.cn 的 live 时点证据。

## 验收结果（实测，见 test-results/connector_tests.txt，ACCEPTANCE = PASS，exit 0）
- **一个 mock connector 全链路通过**：`MockOfficialConnector` 经 `run_chain` → health.ok=True、discover 2、每条 fetch→verify(**A0/官方域**)→normalize（doc1 **文号 国发〔2026〕1号 / 日期 2026-01-05 / 状态 现行有效 / 附件 1**；doc2 日期 2026-02-10）→attachments→**cursor 推进到最新日期 2026-02-10**。
- **无业务 UI/图谱/新平台耦合**：SDK 仅 stdlib；测试断言源码不含 `requests/flask/django/networkx/neo4j/fastapi`。
- **adapter registry**：注册/取用正常，**重复 source_id 报错**。
- **真实 HTTP GET（内核已接通）**：`HttpFetcher` 对**本地 loopback server** 实测 status 200、返回**逐字 payload + sha256 匹配**（确定性、CI 无外网）。
- **live A0 实抓（Owner 决策）**：经 SDK `HttpFetcher` 实抓 `www.gov.cn`（200/67662B/官方域/「中国政府网_中央人民政府门户网站」）与 `gov.cn/zhengce/`（200/39811B/「政策_中国政府网」）；记为 live 时点证据（不逐字复现，只存元数据+标题）。

## Data / Performance / Visual
Data = mock 全链路 trace + live 实抓元数据。无 UI 改动、无图谱、无新平台；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED，SDK 未接 worker）。

## Value / Cost（S3 China A0 Official Pilot）
- **Value**：所有 A0 政府适配器（T034+）插入的**统一最小接口 + 类型契约 + 注册表**——用 A0 官方原文替换 Board 3 新闻噪声的管道；真实 fetch 从内核起就接通，早暴露站点问题。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = SDK 未接 worker。经常性云成本 delta = $0/月。**注意**：live 实抓从**开发环境**跑（非 worker），故 0 云成本；一旦 T034+ 接进 worker cron，每次 fetch = Worker 子请求，须核 DIR-007 免费额度 + 每 run 抓取上限。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（真实适配器解析在 T034+）；live 实抓不逐字复现（契约测试用 mock+loopback）；worker 子请求成本待接线核算；nda.gov.cn 需浏览器；verify/normalize 真实规则在 T033/T034+；robots 未做。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = real_fetch_smoke.json。

## 完成声明
```text
Task: ADP-S3-P01-T031
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/official_connector.py + CONNECTOR_SDK_SPEC.md + T031 证据包（real_fetch_smoke/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: connector_tests.txt —— mock 全链路(health/discover2/fetch/verify A0/normalize 文号·日期·状态/attachments/cursor)+HttpFetcher 真实GET(loopback 逐字+sha256)+registry 拒重复+无平台耦合，ACCEPTANCE=PASS(exit 0)；live gov.cn 实抓 200 官方域(real_fetch_smoke.json)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 最小 Official Connector SDK（7 能力+typed contract+registry，真实 fetch 已接通）
Data/Performance/Visual: Data=mock trace + live 实抓元数据；无 UI/图谱/平台
Value: A0 政府适配器统一插座；A0 官方原文替换新闻噪声的管道
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0；live 实抓走开发环境(非worker)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（SDK 未接 worker/D1）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
