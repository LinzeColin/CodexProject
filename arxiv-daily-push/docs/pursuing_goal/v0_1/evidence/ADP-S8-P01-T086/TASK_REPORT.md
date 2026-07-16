# TASK_REPORT · ADP-S8-P01-T086｜生产回滚与灾难恢复演练

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S8-P01-T086（Stage S8 / S8-P01，size M；Release, Soak & Final Handoff）
- **release_mode**: NOT_DEPLOYED（隔离演练 + 新工具/证据，不发起真实回滚、不碰生产；live 仍 `b189d3cc0703`）
- **Depends**: ADP-S8-P01-T085

## 6 个前置问题
1. **唯一目标？** — 隔离演练**生产回滚 + 灾难恢复**：证 Worker/D1/R2/Registry/内容 bundle/预测 6 组件均可回到已知点；交付 rollback drill + restore drill + RTO/RPO actuals + evidence hashes；任何不可恢复项=release blocker。
2. **允许改的文件？** — 仅新增：`tools/disaster_recovery_drill.py`、`evidence/ADP-S8-P01-T086/**`；治理走 gov 脚本。不改 worker/schema/source_registry/生产。
3. **绝不能改的行为？** — live 仍 `b189d3cc0703`（NOT_DEPLOYED）；**不发起真实回滚**（演练隔离，证「可恢复性」而非执行 live rollback）；已提交证据只读；无生产 D1/R2 写；恢复进 tmp/内存。
4. **基线 build+data？** — worker 自哈希 `452f7c5de919`(源)/live `b189d3cc0703`(T040 回滚目标)；D1 从 T027 快照恢复(498/500)；registry_hash `d63cf6bd`；R2 内容寻址不可变；retention matrix(T029) 3 PERMANENT + 3 REGENERABLE。
5. **验收命令？** — `python3 test-results/t086_verify.py` → ACCEPTANCE=PASS，exit 0（6 组件隔离恢复至一致已知点、各 recovered_hash==known_point、报 RTO/RPO、0 release blocker；负控制:破坏恢复→recoverable False→release blocker）。
6. **NOT_DEPLOYED？** — 纯 docs/tool 新增；rollback=revert commit；未部署、未碰生产数据。

## 交付物
- **工具** `tools/disaster_recovery_drill.py`：对 6 组件逐一在**隔离沙箱**（tmp/内存 SQLite）执行恢复、测 RTO/RPO + evidence hash、分类 release blocker。复用既有工具（T029 restore_drill / T021 r2_artifact_key / T014 compile_registry / T018 render / T071 baselines）+ T085 已提交锚点。
- **dr_drill_report.json**（6 组件 rollback/restore drill + RTO/RPO + evidence hashes + retention class + is_release_blocker）。
- **recovery_known_points.json**（冻结的已提交已知点:content_bundle render hash / r2 内容寻址 key / d1 per-month / registry hash / worker build_id——每组件恢复的比对基准，漂移即判不可恢复）。
- **rto_rpo_actuals.json**（RTO 实测秒 + RPO 定性 + evidence hashes 汇总）。
- **验证器** `test-results/t086_verify.py`（2 载重负控制）+ `dr_drill_tests.txt`（PASS）+ `realtime_check.txt`。

## 6 组件恢复矩阵（隔离演练，全 recoverable，0 blocker）
| 组件 | retention | 已知点 | 恢复机制 | RPO | recoverable |
|---|---|---|---|---|---|
| **worker** | REGENERABLE(git 无状态码) | 源 build_id `452f7c5de919`/live `b189d3cc0703`(T040) | `wrangler versions deploy <build_id>`；自哈希证完整性 | 0 | ✔(自哈希复现) |
| **d1** | PERMANENT(append-only 版本)+REGENERABLE(镜像) | T027 开放月快照(498/500) | 从开放快照恢复到隔离内存 SQLite(T029) | 0(永久记录) | ✔(counts_consistent/0 孤儿/329 版本) |
| **r2** | PERMANENT(内容寻址原文,永不删) | 内容寻址 object key | 相同字节再导出=相同 key(不可变) | 0(不可变) | ✔(key 确定+可区分) |
| **source_registry** | REGENERABLE(git 编译) | registry_hash `d63cf6bd` | recompile source_registry(git revert 已知点) | 0(git) | ✔(recompile==d63cf6bd) |
| **content_bundle** | REGENERABLE(L0-L3 从 raw+code) | 确定性 render hash | 从永久 raw items 重导出(T018) | 0(可再生) | ✔(两次导出同 hash) |
| **prediction** | REGENERABLE(baselines)+PERMANENT(append-only 台账 T073) | 已提交 baselines 报告 | re-benchmark；forecast 台账 append-only | 0 | ✔(re-benchmark 复现) |

## 验收（PASS，verifier 独立重放，exit 0）
证据：`test-results/dr_drill_tests.txt`（ACCEPTANCE = PASS）。

1. **隔离演练完成且结果一致** — 6/6 组件在隔离沙箱恢复至一致已知点（worker 自哈希 `452f7c5de919`、registry `d63cf6bd`、D1 counts_consistent 329 版本、R2 内容寻址、content/prediction 确定性）；worker/registry 源文件演练前后 sha256 字节不变（只读、无 live rollback）。
2. **任何不可恢复项成为 release blocker** — `is_release_blocker = not recoverable`；真实 6 组件 **0 blocker**。**★每组件 recoverable 都比对 COMMITTED 已知点（非同run自比）★**:worker 自哈希==声明 build_id、registry recompile==`d63cf6bd`、prediction==已提交 baselines、**content_bundle==已提交 render hash `b70fe73e`（`recovery_known_points.json`）**、**r2==已提交内容寻址 key**、d1 per-month==已提交 T029。**3 载重负控制**:①翻转 source `enabled`→registry `c5db032a`≠`d63cf6bd`→blocker；②content 输入漂移→`129f0ab2`≠`b70fe73e`→blocker；③r2 不同内容→key≠已提交→blocker（分类载重、非空跑）。
3. **RTO/RPO actuals + evidence hashes** — `rto_rpo_actuals.json` 逐组件 RTO 实测秒 + RPO 定性 + evidence hash。

> **复核记录**：初版 content_bundle/r2 的 recoverable 是**同 run 自比**（h1==h2 确定性重言式），4-lens 对抗复核（blocker-classification lens）判 **HOLE_FOUND**（漂移不会被判 blocker，违验收②）。**已修**：新增 `recovery_known_points.json` 冻结各组件已知点，recoverable 改为比对**已提交锚点**→ 漂移即翻 False（NC2/NC3 证实）。

## 实时未回归
NOT_DEPLOYED：隔离演练，不发起真实回滚。live `/build.json`=`b189d3cc0703`（六主题+动效不变）。1 次只读 GET。

## 成本（unknown 不填 0）
生产 new_requests 0 / D1 行读写 0 / R2 字节·操作 0 / model_calls 0 / 经常性云 0（NOT_DEPLOYED，全本地 tmp/内存）。只读 GET 1；人工=DR 演练工具 + 验证器 + 负控制 + 证据。

## 独立验证
实现者**不自签 PASS**。交独立 Agent 复核（见 adversarial_review.md）。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
