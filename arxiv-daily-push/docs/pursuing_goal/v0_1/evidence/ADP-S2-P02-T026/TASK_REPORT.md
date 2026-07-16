# TASK_REPORT · ADP-S2-P02-T026｜实现版本 Diff、模板噪声过滤与 Replay 幂等

## 唯一目标（达成）
只对**实质变化**（正文/附件/状态）生成 DocumentVersion；**模板噪声**（页脚/导航/分享/计数/相对时间/cookie/广告/版权/ICP）变化不增版本；**任何任务可重放**（三次重放结果一致）。交付 diff engine、noise rules、replay CLI、fixtures。

## 六个开始前问题（已回答）
1. **唯一目标**：版本 Diff + 模板噪声过滤 + Replay 幂等，只对实质变化增版本、噪声不增、三次重放一致。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/version_engine.py, VERSION_ENGINE_SPEC.md, NOISE_RULES.md}` + 本证据包（fixtures.json / version_report.json / test-results / 报告）+ 治理同步（CHANGELOG / DEVELOPMENT_LEDGER / development_events.jsonl / dashboard-generated registers）。
3. **绝不能改变**：抓取行为、六主题高级动效、worker、生产 D1（adp-mirror）、R2、cron。纯规则/工具，NOT_DEPLOYED，未接写入路径。
4. **基线**：main `e69a0559`（T025 DocumentVersion schema 已合入）；建立在 T024 canonical_id + T025 版本链之上。
5. **验收**：正文/附件/状态实质变化增版本；页脚/导航变化不增；三次重放结果一致。
6. **回滚**：`git revert <sha>`（纯规则/工具，NOT_DEPLOYED，生产未变更）。

## 交付物
- `tools/version_engine.py` —— `strip_noise`（去模板噪声）+ `substantive_signature`（body_hash+附件哈希集+status）+ `content_hash` + `diff`（解释变化）+ `ingest`（append-only 版本决策、幂等）+ `replay`（N 次重放一致）+ CLI。
- `VERSION_ENGINE_SPEC.md` —— 版本触发签名、diff、append-only、replay 幂等、CLI 规范。
- `NOISE_RULES.md` —— 保守的模板噪声规则表（含 **CJK `\b` 陷阱**说明与修复）。
- `evidence/.../fixtures.json` + `version_report.json` —— 六条 fixture（v1/噪声/正文/附件/状态/重放）与 CLI 报告。

## 验收结果（实测，见 test-results/version_tests.txt，ACCEPTANCE = PASS，exit 0）
- **页脚/导航变化不增版本**：A→B 只加页脚/编辑署名/分享/阅读计数/"3 分钟前"/版权/ICP → `noise_only=True, substantive=False` → **不增版本**（B 判为 `skipped_no_change`）。
- **正文实质变化增版本**：B→C 样本量更正 → `body_changed=True, substantive=True` → 新版本。
- **附件实质变化增版本**：C→D 增补充材料 → `attachments_changed=True`、`body_changed=False`（隔离）→ 新版本。
- **状态实质变化增版本**：D→E active→withdrawn → `status_changed=True`、body/附件均 False（隔离）→ 新版本。
- **append-only 链**：序列 [A,B,C,D,E,F] → actions `[created_v1, skipped, new_version, new_version, new_version, skipped]` → 版本链 **v1..v4**（干净递增），4 个 content_hash 互异，历史不覆盖。
- **三次重放结果一致**：`replay(3x) identical=True`；重复注入当前 tip（E×3）→ 链保持 4（幂等）；CLI 连续两次 `--out` **字节一致**。
- **CLI/真数据形态**：6 items → 1 canonical document → 4 versions / 3 new / 2 skipped / replay_deterministic True。

## 实现中发现并修复的真实缺陷
噪声规则里 CJK 备选词后接 `\b`（如 `分享到|微信…\b`）在两个 CJK 字符间**永不触发**（CJK 全是 `\w`），导致 "分享到微信" 未被清除 → 一次纯噪声变化被误判为实质变化、多产生一个版本。**修复**：去掉 CJK 备选后的 `\b`，改用 `token + .*` 锚定；`NOISE_RULES.md` 记录该陷阱。修复后验收全绿。

## Data / Performance / Visual
N/A —— 纯规则/工具，无生产数据写入、无性能路径、无 UI 改动；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S2 Durable Evidence & Versioning）
- **Value**：版本链只反映**实质变化**——展示层噪声不再制造伪版本，历史干净可信；注入幂等使任何抓取/回填任务可安全重放不产生重复版本。为 T027+ 开放快照/恢复提供可信版本轴。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 新站点样板出现时扩 NOISE_RULES + fixture。经常性云成本 delta = $0/月。未接生产写入路径。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接 worker/D1 写入路径，归后续接线）；噪声规则非穷尽（保守偏多留版本）；doc_date 不入触发签名（可配置）；body 质量依赖上游抽取；附件与 R2 键强校验留待快照任务；status 枚举未强约束。

## 不适用证据项
`migration.sql/rollback.sql`（本任务无 schema 变更，沿用 T025）、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = fixtures.json + version_report.json。

## 完成声明
```text
Task: ADP-S2-P02-T026
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/version_engine.py + VERSION_ENGINE_SPEC.md + NOISE_RULES.md + 证据包（fixtures/version_report/test-results/TASK_REPORT/cost_value/known_gaps/commands.log/changed_files/git.diff）+ 治理同步（见 changed_files.txt）
Tests: version_tests.txt —— 噪声不增/正文增/附件增(隔离)/状态增(隔离)/append-only v1..4/三次重放一致/tip 重放幂等/CLI 字节一致 全通过，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 版本 Diff + 模板噪声过滤 + Replay 幂等（只对实质变化增版本）
Data/Performance/Visual: N/A（纯规则）
Value: 版本链只反映实质变化、历史干净、任务可安全重放
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0；未接生产写入路径
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯规则/工具）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
