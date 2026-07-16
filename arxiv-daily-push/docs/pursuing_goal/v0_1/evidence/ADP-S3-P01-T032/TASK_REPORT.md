# TASK_REPORT · ADP-S3-P01-T032｜建立 Fixture 与 Contract Test Harness

## 唯一目标（达成）
冻结官方页快照为 fixture + 对比 golden expected JSON，使政府网站**模板变化在 CI 被发现，而不是上线后静默错抓**。交付 normal/attachment/pagination/changed fixtures + expected normalized JSON。

## 六个开始前问题（已回答）
1. **唯一目标**：连接器契约测试骨架；任一字段漂移/附件丢失/分页断裂使相应 connector test 失败。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/connector_contract.py, CONTRACT_TEST_SPEC.md}` + 本证据包（fixtures/expected/contract_report/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题动效、worker、生产 D1/R2、cron；不引入第三方/新平台。NOT_DEPLOYED。
4. **基线**：main `2c885fb7`（T031 连接器 SDK 已合入）；建立在 SDK 7 能力接口之上。
5. **验收**：任一字段漂移、附件丢失或分页断裂会使相应 connector test 失败。
6. **回滚**：`git revert <sha>`（纯离线测试骨架，生产未变更）。

## 交付物
- `tools/connector_contract.py` —— `ReferenceOfficialConnector`（stdlib，class 锚定解析定义好的官方文件模板，实现 SDK 7 能力）+ `run_contract`/`check_doc`/`check_pagination`（解析 vs golden 逐字段 diff）。
- `evidence/.../fixtures/` —— `normal.html`（标准）、`attachment.html`（2 附件）、`pagination.html`+`pagination_p2.html`（分页）、`changed.html`（模板改名，用于证明漂移被抓）。
- `evidence/.../expected/` —— `normal.json`/`attachment.json`/`pagination.json`（golden 冻结值）。

## 验收结果（实测，见 test-results/contract_tests.txt，ACCEPTANCE = PASS，exit 0）
- **正例全过**：normal/attachment/pagination 解析**逐字段等于 golden**（all_passed=True）；pagination 跨 2 页发现 3 项。
- **字段漂移被抓**：`changed.html` 把文号 class `doc-number`→`wenhao` → `doc_number` 解析为 **None** → 与 normal golden diff **FAIL**（`doc_number: expected 国发〔2026〕5号 got None`）。
- **附件丢失被抓**：从 `attachment.html` 删 `政策解读.docx` → attachments 从 2 降到 1 → diff **FAIL**。
- **分页断裂被抓**：删 `pagination.html` 的 `a.next` → 第 2 页不爬 → discover 从 3 降到 **2** → **FAIL**。
- 三类漂移（验收明列）**全部被相应 test 抓到**。

## Data / Performance / Visual
Data = 4 fixture + 3 golden JSON + 契约报告。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED，离线测试）。

## Value / Cost（S3 China A0 Official Pilot）
- **Value**：政府站改版时**CI 立即失败**而非上线后静默错抓——让 A0 官方适配器（T034+）可被信任的安全网；字段/附件/分页三类最常见漂移都被覆盖。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 站点合法改版时重抓 fixture + 更新 golden。经常性云成本 delta = $0/月。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接项目 CI 流水线）；参考连接器为通用模板（真实各站 DOM 在 T034+）；golden 需人工同步；fixtures 为构造样本非实抓整页；未覆盖编码/反爬/软404 等漂移（后续适配器补）。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = fixtures/ + expected/ + contract_report.json。

## 完成声明
```text
Task: ADP-S3-P01-T032
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/connector_contract.py + CONTRACT_TEST_SPEC.md + T032 证据包（fixtures/expected/contract_report/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: contract_tests.txt —— 正例3/3过 golden；字段漂移(changed.html 文号 None)/附件丢失(2→1)/分页断裂(3→2)各自 FAIL，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Fixture + Contract Test Harness（模板漂移在 CI 被发现）
Data/Performance/Visual: Data=fixtures+golden+契约报告；无性能/UI
Value: 政府站改版 CI 立即失败，非上线后静默错抓
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（离线契约测试）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
