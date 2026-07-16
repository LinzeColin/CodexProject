# TASK_REPORT · ADP-S8-P01-T085｜全链路迁移与数据一致性彩排

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S8-P01-T085（Stage S8 / S8-P01，size L，**S8 首任务**；Release, Soak & Final Handoff）
- **release_mode**: NOT_DEPLOYED（纯隔离彩排 + 新工具/证据，不改 worker/schema/registry，不碰生产；live 仍 `b189d3cc0703`）
- **Depends**: T020;T029;T040;T056;T068;T076;T084（各 Stage 终点）

## 6 个前置问题
1. **唯一目标？** — 在隔离环境**重放**从 source registry 到发布/历史/预测的全链路，交付 rehearsal manifest + row/hash counts + diff report，证明关键计数/关系一致、无未解释数据丢失、不碰生产。
2. **允许改的文件？** — 仅新增：`tools/full_chain_rehearsal.py`、`evidence/ADP-S8-P01-T085/**`（含把 `items_500.json`+`fs_500.json` 提交为可复现输入 fixture）；治理文件走 gov 脚本。**不**改 worker/schema/source_registry/生产。
3. **绝不能改的行为？** — live 仍 `b189d3cc0703`（NOT_DEPLOYED）；已提交的 T024/T027/T029/T071 输出**只读**（彩排读它们、在 tmp 重算、绝不覆盖）；无生产 D1/R2 写；被调用的既有流水线工具**只读不改**。
4. **基线 build+data？** — live `b189d3cc0703`；已提交锚点：registry_hash `d63cf6bd…`、canonical 500→498、snapshot_id `sha256:61de7073…`(498 docs/500 versions/92 partitions)、restore counts_consistent。输入 fixture items_500(500 行)+fs_500。
5. **验收命令？** — `python3 test-results/t085_verify.py` → ACCEPTANCE=PASS，exit 0（在 tmp 重放整链，断言每阶段复现已提交锚点 + 无未解释丢失 + 证据字节不可变 + 负控制触发）。
6. **NOT_DEPLOYED？** — 纯 docs/evidence/tool 新增；rollback=revert 该 commit；未部署、未触生产数据。

## 关键发现（诚实）
- **原始 500 行 cn_items 输入此前未被提交**（只在 session scratchpad）；已提交的 `golden_set_500.json` 仅 P0 存在性视图（无 title/url/date），无法重建原始输入。故 canonicalize→version→snapshot 此前**只能靠已提交输出交叉核对，不能从已提交 fixture 重放**。本任务把真实 500 行输入 `items_500.json`（+由它确定性再导出、逐字节等于既有 `fs_500.json`）提交为**可复现锚点**，使全链真正可重放。（已扫描 items_500：纯公开 feed 元数据，0 email/0 私密路径/0 凭证。）
- **预测阶段（baselines）与文档链解耦**：T071 baselines 读 build_baselines.py 内嵌的 G0/G1/G2 fixture，不消费快照——如实标注 `decoupled`，仅验证其确定性可复现（G1/G2 有可复现基线）。

## 交付物
- **工具** `tools/full_chain_rehearsal.py`：在隔离 tmp work_dir 用**既有已提交工具黑盒重放** 8 阶段（compile_registry T014→extract_factsheet T016→build_render_payload T018→canonicalize T024→version_engine T026→snapshot_writer T027→restore_drill T029→baselines T071），逐阶段对已提交锚点比对；`assess_row_ledger()` 判无未解释数据丢失。
- **rehearsal_manifest.json**（每阶段 in/out row 计数 + key hash + matches_committed + 确定性 + row_ledger）。
- **diff_report.json**（replayed vs committed，逐阶段 + 锚点 + 负控制结果）。
- **验证器** `test-results/t085_verify.py`（3 载重负控制）+ `rehearsal_tests.txt`（ACCEPTANCE=PASS）+ `realtime_check.txt`。

## 验收（PASS，verifier 独立重放，exit 0）
证据：`test-results/rehearsal_tests.txt`（ACCEPTANCE = PASS）。

1. **关键计数/关系一致** — 8 阶段全复现已提交锚点：registry_hash `d63cf6bd`(且二次编译字节稳定)、factsheet `909a07fd`(由 items 再导出=既有 fs_500)、canonical **500→498**(dup=2/collisions=0/canonical_id 集合逐一相等)、version **500**、snapshot_id **`61de7073`**(498/500/92 + 逐分区 logical_hash 集合相等)、restore(3 月 329 版本，counts_consistent=True/0 孤儿/0 永久删除)、prediction(G1/G2 可复现基线)。
2. **无未解释数据丢失** — row_ledger 每条 delta 有编码原因：items→docs −2(duplicate_items_collapsed)、docs→versions +2(多 item 文档第 2 版)、docs/versions→snapshot 行数**守恒**(仅按月重分区)。**负控制**:poisoned ledger(未解释 −100 + 声称 preserved 却掉行)被 `assess_row_ledger` 判 not-ok。
3. **不碰生产** — 全部写只在 tmp work_dir；**已提交源真相 5 个锚点文件彩排前后 sha256 逐字节不变**(彩排只读不覆盖)；live `/build.json` 仍 `b189d3cc0703`(realtime_check.txt，NOT_DEPLOYED)。**负控制**:丢 1 行输入(500→499)使 canonical 与 snapshot 阶段 matches_committed 双双翻 False(证复现检查非空跑)；伪 live build 使 production_untouched 翻 False。

## 实时未回归
NOT_DEPLOYED：纯隔离彩排 + 新工具/证据。live `/build.json`=`b189d3cc0703`（六主题+动效不变）。1 次只读 GET。

## 成本（unknown 不填 0）
生产 new_requests 0 / D1 行读写 0 / R2 字节·操作 0 / model_calls 0 / 经常性云 0（NOT_DEPLOYED，全在本地 tmp）。只读 GET 1；人工=彩排工具 + 验证器 + 负控制 + 输入 fixture 提交 + 证据。

## 独立验证
实现者**不自签 PASS**。交独立 Agent 复核（见 adversarial_review.md）。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
