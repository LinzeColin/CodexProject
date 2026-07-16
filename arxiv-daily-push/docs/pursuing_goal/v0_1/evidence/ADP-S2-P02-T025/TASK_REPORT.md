# TASK_REPORT · ADP-S2-P02-T025｜实施 DocumentVersion Schema、迁移与回滚

## 唯一目标（达成）
为 CanonicalDocument（T024）实现 **append-only 的 DocumentVersion 版本链 schema、迁移与回滚** —— 不覆盖历史，记录内容、附件、状态和日期的变化。交付 `migration.sql`、`rollback.sql`、indexes、schema version，并做迁移前后行数/关系校验与隔离副本回滚。

## 六个开始前问题（已回答）
1. **唯一目标**：DocumentVersion schema + 迁移 + 回滚，append-only 不覆盖历史，含 indexes 与 schema version 标识；迁移前后行数/关系校验，回滚在隔离副本成功。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/schemas/{document_version.migration.sql, document_version.rollback.sql}` + 本证据包（含隔离验证脚本）+ 治理同步（CHANGELOG / DEVELOPMENT_LEDGER / development_events.jsonl / STATUS_GENERATED 等 registers）。
3. **绝不能改变**：抓取行为、六主题高级动效、worker、**生产 D1（adp-mirror）**、R2、cron。迁移**不应用到生产**（NOT_DEPLOYED），仅在隔离内存副本上验证。
4. **基线**：main `1f3902d0`（T024 CanonicalDocument 身份已合入）；schema 建立在 T024 canonical_id 之上。
5. **验收**：迁移前后行数/关系校验（1 doc + 2 versions，0 孤儿，历史保留，UNIQUE 强制）；回滚在隔离副本成功（迁移对象移除、既有 cn_meta 保留、schema_version 键移除）。
6. **回滚**：`git revert <sha>` 回退规则文件；生产从未变更，故无数据回滚（`rollback.sql` 仅供隔离副本/未来落库时按 feature-flag 使用）。

## 交付物
- `schemas/document_version.migration.sql` —— `cn_documents`（canonical_id PK、title_norm、sources_json、current_version_no、created_at、first_seen_at）+ `cn_document_versions`（version_id PK、canonical_id、**version_no append-only**、content_hash、status、doc_date、artifact_keys_json、created_at、`UNIQUE(canonical_id,version_no)`）+ 3 个索引（canonical / content_hash / status）+ `cn_meta` 写入 `document_version_schema = adp.document_version.v0_1`。全部 `IF NOT EXISTS` / `INSERT OR IGNORE`，**幂等**。
- `schemas/document_version.rollback.sql` —— 逆序 DROP INDEX/TABLE + **仅删** `document_version_schema` 这一 `cn_meta` 键（scoped，不清空既有 cn_meta）。
- `evidence/.../test-results/t025_verify.py` + `migration_test.txt` —— 隔离内存 SQLite 验证脚本与输出。

## 验收结果（实测，见 test-results/migration_test.txt，ACCEPTANCE = PASS，exit 0）
- **生产式前置**：隔离库先建 `cn_meta` 并写入无关行 `cn_schema=adp.v03`，模拟已有生产表。PRE tables=`[cn_meta]`。
- **迁移前后行数/关系校验**：迁移后 tables=`[cn_document_versions, cn_documents, cn_meta]`、indexes=`[idx_docver_canonical, idx_docver_contenthash, idx_docver_status]`；插入 1 canonical doc + 2 版本 → **docs=1 / versions=2**，**孤儿版本(关系完整性)=0**（LEFT JOIN 检查），**历史保留=True**（v1 内容 hash 未被 v2 覆盖）。
- **append-only 约束**：`UNIQUE(canonical_id,version_no)` **强制=YES**（重复 version_no 插入被 IntegrityError 阻止）。
- **schema version**：`cn_meta.document_version_schema = adp.document_version.v0_1`。
- **幂等**：`migration.sql` 连跑两次不报错、不重复建对象。
- **回滚在隔离副本成功**：回滚后 tables=`[cn_meta]`、indexes=`[]`；**迁移对象全部移除=True**、**既有 cn_meta 保留=True**（`cn_schema` 仍在）、**schema_version 键移除=True**。

## Data / Performance / Visual
N/A —— 纯 schema/迁移 DDL，无生产数据写入、无性能路径、无 UI 改动；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S2 Durable Evidence & Versioning）
- **Value**：append-only 版本链使**历史永不被覆盖**——内容/状态/日期/附件的每次变化都成为新版本，配合 T022/T023 已保留的 R2 原文，得到**可恢复的内容历史**与每版本到原始 artifact 的链接；为 T026 版本 Diff 与 T027+ 开放快照打底。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 增列时改 migration/rollback + spec。经常性云成本 delta = $0/月。迁移**尚未应用到生产 D1**。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（仅隔离副本验证）；写入路径与「只对实质变化增版本」由 T026 接线；content_hash 规范化口径待 T026 固定；artifact_keys 与 R2 键强一致留待快照任务；遵循现有 schema 风格不声明数据库级 FK。

## 不适用证据项
`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（无 UI / 无部署 / 无运行时性能）。`data-samples` = 隔离验证的内联 fixture（脚本内）。

## 完成声明
```text
Task: ADP-S2-P02-T025
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: schemas/document_version.migration.sql + schemas/document_version.rollback.sql + 证据包（migration.sql/rollback.sql/test-results/TASK_REPORT/cost_value/known_gaps/commands.log/changed_files/git.diff）+ 治理同步（见 changed_files.txt）
Tests: migration_test.txt —— 迁移前后行数/关系(docs=1/versions=2/0孤儿/历史保留)、UNIQUE 强制、幂等双跑、隔离回滚(对象移除+cn_meta保留+schema键移除) 全通过，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: append-only DocumentVersion 版本链 schema + 迁移 + 回滚（不覆盖历史）
Data/Performance/Visual: N/A（纯 schema DDL，未触生产/UI）
Value: 历史永不覆盖，可恢复内容历史 + 每版本链接 R2 原文（版本 Diff/快照打底）
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0；迁移未落生产
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（迁移仅隔离副本验证）
Rollback: git revert <sha>（规则文件）；生产未变更
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
