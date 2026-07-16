# TASK_REPORT · ADP-S5-P02-T062｜实现版本、As-of 与新旧对照 API/视图

## 唯一目标（达成）
在版本链（T026 version_engine：实质变化判定 + 模板噪声过滤）与 as-of 解析器（T056 coverage_asof：解析日期、绝不返回未来版本）之上，实现**用户可见的读层**：版本时间线、可定位的新旧对照 diff、as-of 历史查询、旧版可回放。让用户看到**真正的变化、历史状态和原文位置**。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：version timeline / diff payload / as-of / replay 的只读 API——增删改可定位、模板噪声不显示、旧版可回放。
2. **允许修改文件**：`tools/version_asof_api.py`（新）+ `evidence/ADP-S5-P02-T062/*` + 治理同步。**不改 worker/生产/registry/VERSION**。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。API 为纯函数只读层。
4. **基线**：main `bb4c5e8a`（T061 已合入）；复用 T026 version_engine + T056 coverage_asof，不重复实现噪声规则/as-of 解析。
5. **验收**：增删改可定位；模板噪声不显示；旧版可回放（含负控制：噪声-only 变更 diff 必须为空且不加版本；as-of 绝不返回未来版本）。
6. **回滚**：`git revert <sha>`（只读 API 库，生产未变更）。

## 交付物
- `tools/version_asof_api.py` —— version_timeline（折叠为实质版本，噪声-only 不成版本，携带去噪正文快照）+ diff_payload（**行级可定位** add/delete/modify，各带行号与原文，基于去噪正文 → 噪声永不显示）+ as_of（复用 T056 解析器，绝不返回未来版本）+ replay_version / replay_is_idempotent（确定性重建旧版正文，3 次重放一致）。
- `evidence/…/build_version_asof.py` —— 确定性 fixtures（v1 / 实质 v2[一增一删一改] / 噪声-only 再渲染 + as-of 电池语料）+ 报告。
- `evidence/…/version_asof_report.json`、`evidence/…/test-results/{t062_verify.py, version_asof_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/version_asof_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 增删改可定位**：实质 v2 对 v1 的 diff = **恰好 {add:1, delete:1, modify:1}**；每条变更带**具体行号 + 原文**（add 定位到「第四条…」新行；delete 定位到被删的「第二条…」；modify 定位到「第一条…」旧→新，新文含「健全」旧文不含）。
- **② 模板噪声不显示**：噪声-only 再渲染（同实质 + 版权/责编/分享/阅读量/相对时间/ICP 六类 chrome）→ **diff.changed=False、line_changes 为空**；diff 与回放正文中**无任何噪声串**；**真实正文未被误删**（「第一条」「第三条」仍在回放正文）。**负控制（判别力）**：对**同一对**原始（未去噪）正文做 raw diff → **surface 6 条噪声行**；去噪 diff surface 0 → 证明去噪是 load-bearing，非空跑。**负控制**：噪声-only 再渲染**未产生多余版本**（timeline=1）。
- **③ 旧版可回放**：replay_version(1/2) **逐字节等于**去噪后的原 v1/v2 正文；同一版本重放 3 次哈希一致（幂等）。**as-of 绝不返回未来版本**：as_of(2026-02-01)=None（首版前）；as_of(2026-04-15)=**v1**（v2 尚属未来）；as_of(2026-07-01)=v2。**无未来泄漏电池**：8 文档 × 36 查询日 = **288 样本，future_leakage=0，与独立 oracle 分歧=0**。**负控制**：故意「永远返回最新版」的泄漏解析器被同一电池在 **70 样本**上抓出 → 电池非空跑。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040，见 realtime_check.txt）。

## Data / Performance / Visual
Data = 1 canonical 文档（v1/实质 v2/噪声再渲染）+ 8 文档 as-of 电池（288 样本）。Performance = 实时无回归。无 UI 改动；六主题保留（API 为库层，供未来视图消费）。

## Value / Cost（S5 多板块深度）
- **Value**：**用户可见的「真正变化 + 历史状态 + 原文位置」**——增删改逐行可定位、模板噪声不干扰、任一历史版本可 as-of 查询与逐字节回放；深且确定性，为后续 Watchlist/Change-only Digest（T066）与版本 UI 提供底座。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = API + fixtures + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：行级 diff 粒度（非字符级 intra-line）；difflib 对齐启发式的边界；as-of 依赖 observed_at 的解析日期；真实生产版本链接入由部署阶段门控。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema 变更）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层无 UI/部署）。`data-samples` = version_asof_report.json。`benchmarks` = N/A（非性能任务）。

## 完成声明
```text
Task: ADP-S5-P02-T062
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/version_asof_api.py(新) + T062 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: version_asof_tests.txt —— 增删改恰{add:1,delete:1,modify:1}逐行可定位;噪声-only diff空+回放无噪声+真实正文保留(raw diff surface 6噪声行判别);旧版逐字节回放+3次幂等;as-of 288样本0未来泄漏0 oracle分歧(泄漏解析器被抓70样本);实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 版本时间线 + 可定位新旧对照 diff + as-of 历史查询 + 旧版回放 API
Data/Performance/Visual: Data=1文档3渲染+8文档288 as-of样本；Perf=实时无回归；Visual=六主题保留
Value: 用户可见真正变化/历史状态/原文位置,深且确定性
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读 API 库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
