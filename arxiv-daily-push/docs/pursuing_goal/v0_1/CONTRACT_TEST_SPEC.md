# Connector Contract-Test Spec · ADP-S3-P01-T032

**冻结官方页快照为 fixture + 对比 golden expected JSON**，使政府网站**模板变化在 CI 被发现**，而不是上线后
静默错抓。工具：`tools/connector_contract.py`。**NOT_DEPLOYED**（离线契约测试；无网络）。

## Fixtures（冻结快照）

`evidence/ADP-S3-P01-T032/fixtures/`：
- `normal.html` —— 标准官方文件页（标题/文号/日期/状态/正文/1 附件）。
- `attachment.html` —— 带 2 个附件（原文 + 解读）。
- `pagination.html` + `pagination_p2.html` —— 分页列表（第 1 页有「下一页」→ 第 2 页）。
- `changed.html` —— **模板已变**（文号 span 的 class 由 `doc-number` 改名为 `wenhao`），用于证明漂移会被抓到。

## Golden expected JSON

`evidence/ADP-S3-P01-T032/expected/`：`normal.json` / `attachment.json`（normalized doc）+ `pagination.json`
（discover items 列表）。golden = 参考连接器对 fixture 的确定性解析冻结值。

## Reference connector

`ReferenceOfficialConnector`（stdlib，class 锚定字段解析）实现 SDK（T031）7 能力，解析定义好的官方文件模板：
标题 `h1.doc-title`、文号 `span.doc-number`、日期 `span.doc-date`、状态 `span.doc-status`、正文 `div.doc-body`、
附件 `a.doc-att`、分页 `a.doc-link` + `a.next`。真实 A0 适配器（T034+）按各站替换选择器，但保持此**契约形状**。

## 契约与漂移检测（验收）

`run_contract(fixtures, expected)` 对每个 case 解析并与 golden 逐字段 diff。**任一以下漂移使相应 test 失败**：
- **字段漂移**：`changed.html`（文号 class 改名）→ `doc_number` 解析为 `None` → 与 normal expected diff 失败（`doc_number: expected 国发〔2026〕5号 got None`）。
- **附件丢失**：从 `attachment.html` 删一个 `a.doc-att` → attachments 列表短一项 → 失败。
- **分页断裂**：删 `pagination.html` 的 `a.next` → 第 2 页不再爬取 → discover 从 3 项降到 2 项 → 失败。

实测（`test-results/contract_tests.txt`，ACCEPTANCE = PASS）：3 个正例全过；3 类漂移全部被抓（各自 FAIL）。

## 如何应对真实模板变化

真实站点改版时：重新抓取该页→替换 fixture→跑契约。若 golden 未同步更新，diff 会**在 CI 失败**（提示人工确认是站点合法改版还是错抓），修复解析或更新 golden 后再合入。→ **CI 发现，而非上线后静默错抓**。
