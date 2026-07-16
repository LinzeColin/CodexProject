# TASK_REPORT · ADP-S6-P01-T070｜建立 Dataset Snapshot 与 observed_at 泄漏防线

## 唯一目标（达成）
**确保 2026 回填的旧文件不会假装在历史时点已知**：数据集快照**按 observed_at（非 doc_date）** 键控——文档的 doc_date（政策发布时点，可能 2016）与 observed_at（ADP 实际抓取/知道的时点，回填时可能 2026）分离。快照只含 `observed_at <= as_of` 的文档；**注入未来文档会使泄漏测试失败**；**任何预测可确定性重建其当时数据集**。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：as-of Dataset Snapshot（observed_at 键控）+ observed_at 泄漏防线（注入未来文档必失败）+ 预测可重建当时数据集。
2. **允许修改文件**：`tools/dataset_snapshot.py`（新）+ `evidence/ADP-S6-P01-T070/*` + 治理同步。**不改 worker/生产/registry/VERSION**。复用 T056 `coverage_asof._parse_date`。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。库层只读、**无时钟**（as_of 传入）。
4. **基线**：main `5e6a3b1e`（T069 已合入）；corpus 含 2016 回填(观测 2026)、2017/2019 文档、2018 预测。
5. **验收**：注入未来文档使测试失败（含 backfill/无 observed_at）；任何预测可重建其当时数据集（可复现、序无关）；observed_at 键控（backfill doc_date<as_of 仍被排除，非 doc_date）。
6. **回滚**：`git revert <sha>`（只读库，生产未变更）。

## 交付物
- `tools/dataset_snapshot.py` —— `snapshot(corpus, as_of)`（含 `observed_at<=as_of` 的文档[解析日期]，malformed/缺 observed_at 排除，确定性序 + 可复现 snapshot_id）+ `snapshot_id`（对含入文档的 canonical_id/observed_at/content_hash 哈希，序无关）+ `assert_no_leakage(dataset, as_of)`（任一文档 observed_at>as_of 或缺失 → **raise LeakageError**，泄漏 tripwire）+ `rebuild_for_prediction(corpus, prediction)`（按 origin_date 重建当时数据集，可复现）。
- `evidence/…/build_dataset_snapshot.py`（corpus：2017a/b + **2016 回填(观测 2026)** + 2019c；2018 预测）+ `dataset_snapshot_report.json` + `test-results/{t070_verify.py, dataset_snapshot_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/dataset_snapshot_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 注入未来文档会使测试失败**：干净 as-of 快照**通过** `assert_no_leakage`；**外部注入**未来观测文档（c 观测 2019 > 2018）→ **RAISE**；注入 **2016 回填文档**（观测 2026）→ **RAISE**；注入**无 observed_at** 文档 → **RAISE**（知晓时点不可验即泄漏）。**判别力**：干净通过、注入失败——guard 在**外部注入数据集**上测（非仅工具自过滤输出），非空跑。
- **observed_at 键控（非 doc_date）**：2016 回填文档 doc_date=2016-05-01（**< as_of 2018**）但 observed_at=2026-07-01 → **被 2018 快照排除**；2018 快照 = 恰 [a, b]（2017 观测）。若按 doc_date 则会误含——证明按 observed_at。
- **② 任何预测可重建其当时数据集**：`rebuild_for_prediction` snapshot_id == snapshot(2018) snapshot_id；**可复现**（两次重建同 id）；重建集自身通过其 origin 的泄漏 guard；**序无关**（打乱 corpus 同 id）；不同 as_of（2019-06）扩展为 [a,b,c] 且 id 不同。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 4 文档 corpus（含 2016 回填/observed 2026）+ 2018/2019 as-of。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S6 预测校准）
- **Value**：**回测无未来泄漏的地基**——快照按 observed_at 键控，2026 回填的历史文件绝不假装在历史时点已知；注入未来文档立即触发 tripwire；任何预测可确定性重建其当时数据集（可审计、可复现）。为 T071（基线）、T072（Rolling-origin Backtest）提供防泄漏数据集。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 快照/防线 + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：observed_at 由摄取管线提供（真实 observed_at = 抓取时间戳，回填文档观测时点为回填运行时点）；snapshot_id 为 canonical_id/observed_at/content 的确定性哈希（碰撞概率忽略）；真实 D1 快照物化由部署阶段负责。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = dataset_snapshot_report.json。`benchmarks` = N/A。

## 完成声明
```text
Task: ADP-S6-P01-T070
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/dataset_snapshot.py(新) + T070 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: dataset_snapshot_tests.txt —— 干净快照过泄漏guard;外部注入未来/2016回填/无observed_at文档全RAISE;observed_at键控(backfill doc_date<as_of仍排除);rebuild==snapshot可复现序无关;不同as_of扩展;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Dataset Snapshot(observed_at键控) + observed_at泄漏防线 + 预测可重建当时数据集
Data/Performance/Visual: Data=4文档含2016回填observed2026；Perf=实时无回归；Visual=六主题保留
Value: 回测无未来泄漏地基,2026回填不假装历史已知,注入未来文档立即触发tripwire
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
