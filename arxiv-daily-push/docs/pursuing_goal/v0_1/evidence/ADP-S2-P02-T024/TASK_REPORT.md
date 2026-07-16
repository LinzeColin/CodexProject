# TASK_REPORT · ADP-S2-P02-T024｜定义 CanonicalDocument 身份、转载归并和去重规则

## 唯一目标（达成）
区分同一文档、转载、附件、修订和完全不同事件 —— 交付 identity spec、canonicalization fixtures、collision report。

## 六个开始前问题（已回答）
1. 唯一目标：定义 CanonicalDocument 确定性身份 + 转载归并 + 去重，artifact 保留、碰撞可解释。
2. 允许修改文件：`docs/pursuing_goal/v0_1/{tools/canonicalize.py, schemas/canonical_document.schema.json, CANONICAL_DOCUMENT_SPEC.md, canonical_doc_index_500.json}` + 本证据包 + 治理同步。
3. 绝不能改变：抓取行为、六主题、worker、D1、R2（NOT_DEPLOYED，只读规则）。
4. 基线：main `66d13ffe`（S2-P01 全完）；样本 500 items + factsheets。
5. 验收：同文重跑不增 document；转载归并但 artifact 保留；碰撞可解释。
6. 回滚：`git revert <sha>`（纯规则/工具，NOT_DEPLOYED）。

## 交付物
- `tools/canonicalize.py` —— identity（doi:/ttl:）+ 五类区分 + 转载归并（artifact 保留）+ 碰撞检测。
- `CANONICAL_DOCUMENT_SPEC.md` + `schemas/canonical_document.schema.json` —— 规则与结构。
- `canonical_doc_index_500.json` —— 真实 500 items 的 canonical 文档索引 + collision report。

## 验收结果（实测，见 test-results/canonical_tests.txt）
- **同文重跑不增 document**：fixture 同 DOI 两条 → 1 canonical document（收拢 1）；**真实 500 items → 498 canonical documents（2 重复收拢、0 碰撞）**。
- **转载归并但 artifact 保留**：fixture nature+chinanews 同 DOI → 1 document（is_repost_merged=True，sources[nature,chinanews]），**artifact_keys 保留两份（[x,y]）**。
- **修订**：同 DOI vN → 1 document，revisions[v2]。
- **完全不同事件**：不同标题 → 2 documents。
- **碰撞可解释**：ttl 同哈希异标题 → 记 collision（reason+resolution 回退 DOI/内容 hash）；真实 500 = 0 碰撞。

## Data / Performance / Visual
N/A —— 纯规则/工具，无数据写入/性能/UI；未碰运行时。

## Value / Cost（S2）
- **Value**：文档身份单一真相——同文去重、转载归并且不丢原文 artifact、修订成链、碰撞可解释可解决；为版本链（T025/T026）与开放快照打底。
- **Cost（逐项）**：新增请求 0；D1 0；R2 0；模型 0；人工维护 = 新身份规则改 spec+工具。经常性云成本 0。

## Known gaps
见 known_gaps.md（附件多文件挂载待 R2 键接入；ttl 身份对超短/泛标题较弱，DOI 优先）。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples`=canonical_doc_index_500.json。

## 完成声明
```text
Task: ADP-S2-P02-T024
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: canonicalize.py + canonical_document.schema.json + CANONICAL_DOCUMENT_SPEC.md + canonical_doc_index_500.json + 证据 + 治理同步（见 changed_files.txt）
Tests: canonical_tests.txt —— 同文重跑不增/转载归并保留artifact/修订成链/异事件区分/碰撞可解释 全通过；真实500=498doc/2收拢/0碰撞；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: CanonicalDocument 身份+转载归并+去重规则（artifact 保留、碰撞可解释）
Data/Performance/Visual: N/A（纯规则）
Value: 文档身份单一真相（版本链/快照打底）
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯规则/工具）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
