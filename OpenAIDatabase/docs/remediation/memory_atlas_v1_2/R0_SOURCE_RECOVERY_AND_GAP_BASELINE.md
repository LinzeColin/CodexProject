# Memory Atlas v1.2 Remediation R0

## 结论

R0 真源恢复通过，但 v1.2 发布验收失败并保持重新打开状态。此前的
`100% complete`、`Final Review PASS` 和
`COMPLETE_WITH_OPERATOR_EVIDENCE` 不能继续作为当前发布结论。

本轮只完成 R0：恢复原始输入、建立事实基线和差距矩阵。没有修复 UI、没有重装
app、没有重新部署、没有推送 GitHub。

## 真源恢复

| 输入 | 历史 SHA-256 | 当前结果 |
|---|---|---|
| Roadmap | `699a8fe5f99a5edc88fec1f8940c4339f7b9b291bd31830f946f521f80904a71` | Downloads 与 repo archive 均精确匹配 |
| TaskPack ZIP | `38e21ae3e94d860e6a40c70a629c8f7048f889164358df7b184bd8caf7bf2472` | Downloads 与 repo `.zip.part` 恢复结果均精确匹配 |

TaskPack 共 32 个文件；`PACK_MANIFEST.json` 覆盖的 30 个 payload 文件全部逐字节
匹配。Roadmap 与包内 `02_Stage_Phase_Task_Roadmap_含PursuingGoal.md` 相同。
包内 `ZIP_SHA256.txt` 的 `6b1951eb...` 与原 ZIP 实测值不一致，已降级为非权威
metadata。

## 当前运行事实

| 层 | 事实 |
|---|---|
| Git | R0 开始时 `HEAD == origin/main == 00f4187f...`，分支为 `main` |
| 线上 bundle | `index-Boo-hAit.js` + `index-SpnzXgRc.css` |
| 本地 bundle | 与线上文件名和内容版本一致 |
| 线上 snapshot | 278 memories / 340 nodes / 1,771 edges / 201 activities |
| 本地 snapshot | 278 memories / 403 nodes / 2,134 edges / 201 activities |
| 数据一致性 | FAIL：线上少 63 nodes、363 edges |
| 1470x661 | FAIL：command palette 高 26px，内容高 361px，与 content grid 重叠 |
| 1440x900 | FAIL：command palette 高 26px，内容高 380px，与 content grid 重叠 |
| 390x844 | FAIL：command palette 高 26px，内容高 891px，与 content grid 重叠 |

根因位于 `apps/memory-atlas/src/styles.css`：`.workspace` 仍只有四个 grid rows，
但 `App.tsx` 已渲染 topbar、controls、interaction lens、command palette、content grid
五个主子项。

## 58 条需求结论

| 状态 | 数量 | 含义 |
|---|---:|---|
| VERIFIED | 28 | 有当前直接证据，但多数属于文档、数据模型、回归测试或 CLI dry-run |
| PARTIAL | 19 | 存在部分实现，缺真实用户路径、线上一致性或多视口可用性 |
| FAILED | 9 | 当前证据直接反驳验收标准 |
| NOT_VERIFIED | 2 | 没有足够直接证据 |

完整逐项矩阵：
`机器治理/证据与日志/remediation/v1_2_r0/requirements_gap_matrix.csv`。

## 直接发布阻断项

1. 首页在全部三个目标视口发生重叠；核心首屏不可扫描。
2. 首屏暴露 `S12 P1`、CLI、English safety labels 和阶段内部状态。
3. Command Palette 按钮只切换说明，不执行同步、报告、proposal 或 deep explore。
4. Final audit 不运行 v1.2 首页多视口无重叠门禁；旧 visual audit 主要是源码字符串检查。
5. 线上与本地 snapshot 不一致。
6. `data/public_raw` 只有 README，raw append-only audit 以 0 文件、0 ledger entry 空通过。
7. S13 的 authorized apply/rollback 证据是 fixture dry-run，不是产品用户工作流。
8. S14 stage PASS 状态来自当前已证明覆盖不足的 validators，不能继续代表发布通过。

## 补救顺序

| Phase | 唯一目标 | 完成门禁 |
|---|---|---|
| R1 | 修复 app shell/Grid 和新增真实多视口布局 gate | 1470x661、1440x900、390x844 无重叠、无水平溢出、关键内容可见 |
| R2 | 建立 v1.2 产品身份和首屏信息架构 | 不再暴露 Stage/Phase/CLI 内部标签；首屏回答用户核心问题 |
| R3 | 让六个 Command Palette 命令成为真实受控用户路径 | 本地 app 可执行；线上只读环境给出明确可行动降级；无静默发送 |
| R4 | 完成 proposal 审批、apply、validation、rollback 用户闭环 | 未授权 fail-closed；授权操作和失败回滚均有真实 E2E 证据 |
| R5 | 提供 owner-daily 真实用户入口 | app 内可启动、查看结果和失败原因，不只是 CLI JSON 合同 |
| R6 | 补齐 P0 可视化、人类问题、过滤和交互证据 | source/time/project/task 过滤与关键图表 E2E 通过 |
| R7 | 解决 raw/source recovery 与线上/本地 snapshot parity | 非空 raw/manifest 恢复证明；同一 snapshot hash/count 进入 app 和 Pages candidate |
| R8 | 整体真实验收与一次性最终交付 | 全部 58 条 VERIFIED；多视口 E2E、恢复演练、安全、parity 通过后才 push/reinstall/deploy |

## R0 Pass Gate

- 原 Roadmap 与原 TaskPack 已按历史 SHA-256 精确恢复：PASS。
- 58 条原始 acceptance 已全部进入矩阵：PASS。
- 每项均包含实现、本地、线上、浏览器证据列或明确缺失原因：PASS。
- 旧完成结论已由新的 remediation status 明确 supersede：PASS。
- UI 修复、部署、app 重装、GitHub push 均未发生：PASS。

下一 run 只能执行 R1，不得同时进入 R2。
