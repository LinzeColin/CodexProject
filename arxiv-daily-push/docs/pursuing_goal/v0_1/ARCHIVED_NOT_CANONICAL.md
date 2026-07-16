# ADP V0.1 · ARCHIVED_NOT_CANONICAL（归档旧方向，保留但不执行）

> 任务 `ADP-S0-P01-T002` 交付物。目标：**保留全部历史细节，但阻止旧 UI、A3+、多租户、TAM 等重新成为当前需求。**
> 机器可读的逐条裁决见同目录 `CONFLICT_LEDGER.csv`；权威顺序见 `PRECEDENCE.md`；本轮范围见 `CURRENT_SCOPE.md`。

## 1. 本文件的效力

- 下列方向**全部已被本轮 `OWNER_DIRECTIVES.yaml` 与最终执行包降级**：历史材料可查阅、可回溯细节，但**不得**作为当前实现合同、不得进入 Roadmap、不得触发任何部署或采购。
- 任何后续任务/线程若从历史材料读到与此冲突的主张，一律以 `PRECEDENCE.md` 的权威顺序为准，并在 `CONFLICT_LEDGER.csv` 查到对应裁决。
- 历史材料**不得直接覆盖**本最终包（见 `historical_inputs/README.md`）。可吸收的证据链、版本、as-of、Golden Set、预测回测等细节，按需登记为 `UNKNOWN/CONFLICT` 后再纳入，**不整体照搬**。

## 2. 被归档方向逐条裁决（来源 / 旧结论 / 新裁决 / 理由）

| # | 方向 | 来源 | 旧结论 | 新裁决 | 理由 |
|---|---|---|---|---|---|
| CL-001 | 认证/多租户/企业后台 | 旧线程 `ADP_HANDOFF_SINGLE_PACKAGE_V7`、`adp_new_thread_handoff_v0_1` | 先做登录认证、多租户与企业后台 | **SUPERSEDED**：保留历史，不进 Roadmap | 本轮只解内容质量与事实漂移（DIR-001） |
| CL-002 | TAM/定价/商业套餐 | `ADP_V0.1_..._COMMERCIALIZATION_ADDENDUM` | 以 TAM/定价/套餐驱动优先级 | **SUPERSEDED**：从 ROI 输入中删除 | 收益成本用真实运行成本量化（DIR-001/DIR-005） |
| CL-003 | 替代式 UI 原型 | `ADP_V0.1_Unified_PRD_Rebuild`、`Frontier_Learning_OS_FINAL_HANDOFF` | 用新 UI 原型/导航重做替换现有视觉 | **SUPERSEDED**：只保留已上线六主题+高级动效 | 六主题/hero 视频/仪表盘/氛围层/自愈是不可破坏基线（DIR-003） |
| CL-004 | 中国来源多级体系 | 旧 A0–A4/B/C/D 或 T0–T5 体系 | 建多级来源体系并全部纳入 Registry | **收敛为 A0/A1/A2**；媒体/搜索仅 discovery | 覆盖中央/省级/重点城市/重要区（DIR-002） |
| CL-005 | 171 源立即全接入 | `21_SOURCE_ARCHIVE_INDEX`、PRD 源清单 | 立即接入全部 171 源 | **候选 Seed**，cohort 晋级 | 一次性接入属 big-bang（09_ANTI_BLACK_HOLE / S4） |
| CL-006 | D1 存全部原文 | 上一版架构包 | D1 保存全部文档原文 | **D1 热元数据，R2 原始对象/历史** | 分层存储控体积/延迟/成本（04_PRODUCT_CONTRACT） |
| CL-007 | 20TB/10M/30M 立即建设 | 容量架构压测包 | 立即按 20TB/10M 文档/30M 版本建设 | **容量压测包络**，按真实增长扩展 | 是压测包络不是采购指令（FACT-016） |
| CL-008 | Workflows 强制依赖 | 编排方案 | Workflows 作强制编排依赖 | **候选**，先比 Cron+Queues；注意 2026-08-10 后步骤计费 | 不默认引入新框架（09_ANTI_BLACK_HOLE） |
| CL-009 | 向量库先上 | 检索方案 | 先上向量检索作核心检索 | **延后**，精确/结构化/FTS 不足再基准 | 避免过早引入成本与复杂度（09_ANTI_BLACK_HOLE） |
| CL-010 | 竞品都有我也有 | 竞品对齐材料 | 复制竞品全部入口/页面/复杂度 | **对齐等价或更好用户收益**，映射少量核心对象 | 按收益缺口优先级（02_CANONICAL_SCOPE） |
| CL-011 | 最终交付=已完成 | 交接包命名语义 | “最终包”即产品已开发完成 | **最终执行基线**；完成须过 S8 | stage gates ≠ production acceptance（01_FINAL_READINESS） |
| CL-012 | 顺带修范围外安全/入口 | `15_CURRENT_WEB_AUDIT_REFERENCES` 旧审计 | 顺带处理公开入口安全/认证问题 1/4 | **OUT_OF_SCOPE**，显式禁止范围外扩张 | 任务合同禁止顺带重构与范围外安全（DIR-001） |
| CL-013 | 动效 vs 性能取舍 | 性能担忧材料 | 动效损害性能应削减/移除 | **不冲突**：保留视觉语义+离屏暂停/懒加载/自适应 | 同时满足 DIR-003 与 S7 性能门 |
| CL-014 | A3+ 来源纳入 | 扩展来源提案 | 本轮纳入 A3 及以上来源 | **OUT_OF_SCOPE**：仅 A0/A1/A2 | 层级收敛，A3+ 留后续（DIR-002/CURRENT_SCOPE） |

## 3. 历史材料实际存放位置（可查、非权威）

历史输入以只读归档形态完整保留（sha256 见包内 `historical_inputs/ARCHIVE_INDEX.csv`），**全部低于本最终包的权威级**：

| 归档文件 | sha256（前 12） | 状态 |
|---|---|---|
| `ADP_HANDOFF_SINGLE_PACKAGE_V7_2026-07-10.zip` | d373928d366a | HISTORICAL_NON_CANONICAL |
| `adp_new_thread_handoff_v0_1.zip` | 49fe7c2f05b9 | HISTORICAL_NON_CANONICAL |
| `ADP_V0_1_Thread_Handoff_Pack.zip` | 91f35713f499 | HISTORICAL_NON_CANONICAL |
| `Frontier_Learning_OS_FINAL_HANDOFF_PACK.zip` | 0107a2ecf71f | HISTORICAL_NON_CANONICAL |
| `ADP_V0.1_Unified_PRD_Rebuild_Foundation_2026-07-10.zip` | 6b63ee333b88 | HISTORICAL_NON_CANONICAL |
| `ADP_PRD_REBUILD_V0.1_INTEGRATED_PACKAGE_2026-07-10.zip` | 4434df270d08 | HISTORICAL_NON_CANONICAL |
| `ADP_V0.1_CHINA_OFFICIAL_SOURCE_AND_COMMERCIALIZATION_ADDENDUM_2026-07-15.zip` | 254598915143 | HISTORICAL_NON_CANONICAL |
| `ADP_V0.1_COMPLETE_HANDOFF_2026-07-15.zip` | 85b361b523df | HISTORICAL_NON_CANONICAL |
| `ADP_V0.1_RECONCILED_DATA_PERFORMANCE_COMPETITOR_PACKAGE_2026-07-15.zip` | c15da7b25ea9 | CANONICAL_INPUT_SUPERSEDED_BY_FINAL |
| `另一个线程的回复(2).rtf` | 5524c4bf62c9 | HISTORICAL_NON_CANONICAL |
| `codex adp outputs(1).zip` | 0036e493aa85 | HISTORICAL_NON_CANONICAL |

- **物理留存**：以上历史输入随 `ADP_V0.1_FINAL_EXECUTION_TASK_PACKAGE_2026-07-15/historical_inputs/` 保存于 Owner 侧；agent 历史与会话数据另存 `LinzeColin/AgentDatabase`（私有 Release 附件）。为遵守低 token/无冗余二进制契约，**不把这些历史 zip 整包提交进本仓库**；需要细节时按需解压查阅并按上表裁决。
- 唯一可执行事实源仍是 `docs/governance/{project.yaml,roadmap.yaml,events.jsonl}` + 本 `docs/pursuing_goal/v0_1/` 基线。

## 4. 边界（本文件不做什么）

- 不删除、不改写任何历史材料（只降级其效力）。
- 不触碰线上 MVP、六主题、高级动效、D1/R2/CSP（NOT_DEPLOYED，0 云成本）。
- 不新增来源、不接入 171 源、不建向量库/Workflows —— 这些均须各自的后续任务与 Gate。
