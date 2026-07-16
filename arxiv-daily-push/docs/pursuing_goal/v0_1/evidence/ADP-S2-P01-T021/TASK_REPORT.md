# TASK_REPORT · ADP-S2-P01-T021｜定义 R2 RawArtifact Key、Hash、压缩与元数据

## 唯一目标（达成）
为不可变原始 HTML/PDF/附件建立稳定对象合同 —— 交付 object key spec、sha256、mime、response metadata、compression policy。

## 六个开始前问题（已回答）
1. 唯一目标：定义 R2 RawArtifact 的 content-addressed 键 + hash + mime + 元数据 + 压缩合同（不写 R2、不需开 R2）。
2. 允许修改文件：`docs/pursuing_goal/v0_1/{schemas/r2_raw_artifact.schema.json, tools/r2_artifact_key.py, R2_RAWARTIFACT_CONTRACT.md}` + 本证据包 + 治理同步。
3. 绝不能改变：抓取行为、六主题、worker、D1；**不开 R2、不写对象**（NOT_DEPLOYED，纯合同）。
4. 基线：main `84e0c968`（T020 已合入，S1 全完）；R2 状态 NOT_ENABLED（FACT-012）。
5. 验收：同字节同 hash；不同 source/version 不覆盖；路径不含 secret/PII。
6. 回滚：`git revert <sha>`（纯 schema/工具/文档，NOT_DEPLOYED）。

## 交付物
- `tools/r2_artifact_key.py` —— object_key()（content-addressed 键）+ sha256 + mime 嗅探 + should_compress() + artifact_metadata()；纯计算，无 R2/网络 I/O。
- `schemas/r2_raw_artifact.schema.json` —— 元数据 schema（object_key/sha256/mime/content_length/compression/source_id/content_version/url/fetched_at/immutable）。
- `R2_RAWARTIFACT_CONTRACT.md` —— 键布局、不可变去重、hash/mime/元数据、压缩策略、无 secret/PII 规则。

## 验收结果（实测，见 test-results/r2_key_tests.txt）
- **同字节同 hash/键**：True（content-addressed 幂等）。
- **不同 source/version 不覆盖**：不同 source_id → 不同键（同字节也不同）；不同 content_version → 不同键。True。
- **路径无 secret/PII**：URL 带 `?token=SECRET123` 时，键**不含** token（token 仅留在元数据 `url`）；键检出 secret/PII 模式即抛错。True。
- **压缩策略**：PDF→application/pdf 不压缩；HTML→gzip。True。
- 总 **RESULT: PASS**。schema 解析 OK。

## Data / Performance / Visual
N/A —— 纯合同/计算，无数据/性能/UI；未写 R2/D1。

## Value / Cost（S2 = 不可变原始证据）
- **Value**：不可变原始证据的**稳定对象合同**——content-addressed 键保证同字节幂等、不同来源/版本不覆盖、路径无泄漏；为 T022 双写、T023 shadow 打底（先立合同再写字节）。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 0；R2 0（未写）；模型调用 0；人工维护 = 新 mime/压缩规则改合同。经常性云成本 0。

## Known gaps
见 known_gaps.md（本任务只定合同不写 R2；R2 NOT_ENABLED；T022 双写需 Owner 决定开 R2）。

## 不适用证据项
`migration.sql/rollback.sql`（无 D1 schema）、`screenshots-or-videos`、`benchmarks`、`data-samples`、`deployment_manifest.preview.json`(NOT_DEPLOYED) —— N/A。

## 完成声明
```text
Task: ADP-S2-P01-T021
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: r2_artifact_key.py + r2_raw_artifact.schema.json + R2_RAWARTIFACT_CONTRACT.md + 证据 + 治理同步（见 changed_files.txt）
Tests: r2_key_tests.txt —— 同字节同hash/不同source·version不覆盖/无secret·PII/压缩策略 全 PASS；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: R2 RawArtifact content-addressed 键+hash+mime+元数据+压缩 合同
Data/Performance/Visual: N/A（未写 R2/D1）
Value: 不可变原始证据稳定对象合同（T022/T023 打底）
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md（T022 双写需 Owner 决定开 R2）
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯合同/工具）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
