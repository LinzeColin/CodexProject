# arXiv Daily Push 融合系统 Roadmap V7（中文人类可读版）

> 基线日期：2026-06-24；状态：**Owner 已确认，等待写入仓库并经 CI 锁定**。
> 本 Roadmap 取代 V6 的“来源即阅读板块、五封邮件”产品结构，但不改写既有历史事件和 Stage 1 验收证据。

## 0. 先看结论

- **Stage 2 不暂停**：现有 `S2P1T01` bioRxiv/medRxiv 线程继续，规范映射为 `S2PBT01`。
- 新增并行基础任务 `S2PAT01`：把本次全部 Owner 要求固化进 GitHub；它阻断“晋升/验收”，但不阻断已限定范围的连接器实现。
- 新产品结构：**4 个数据源域 D1–D4 → 3 个主阅读板块 B1–B3 + 3 个横切副板块 B4–B6 → 每日 3 封主邮件 + 1 封跨板块汇总邮件**。
- Stage 2 必须在最终验收前同时具备：深度理解、个人影响、中文人类界面、真实队列、复习、行动、ROI、周报、月报和 3+1 邮件。

## 1. Stop Gate 与 Stop Condition 的定义

- **Stop Gate**：某 Stage/Phase/Task 可以结束并解锁下一层级前，必须通过的完成门。
- **Stop Condition**：一旦触发必须立即停止、进入 BLOCKED/FAILED，并只提交证据、冲突或恢复方案。
- “代码已写”“单测通过”不能替代 Stop Gate；必须有运行、证据、追踪和中文人类视图。

## 2. Stage 总览

| Stage | Pursuing Goal | 状态 | Phase | 估算工时 | 占比 | Stop Gate | 关键 Stop Conditions |
|---|---|---|---:|---:|---:|---|---|
| `S1` arXiv 单源纵向切片与生产基线 | 证明多源智能系统的最小纵向切片：采集、证据、评分、报告、邮件和运行可形成可审计闭环。 | `completed` | 5 | 328h | 17.73% | `ARXIV_PRODUCTION_ACCEPTED` | R-CONFLICT；DATA-LOSS；EVIDENCE-FAIL；REPLAY-FAIL；LIVE-FAIL |
| `S2` 多源、深度理解、个人成长与 3+1 邮件融合开发 | 将四个数据源域、三个主阅读板块、三个横切副板块、深度理解、中文人类界面、复习、行动、ROI、周/月报告和每日 3+1 邮件融合为同一生产系统。 | `in_progress` | 12 | 1342h | 72.54% | `INTEGRATED_PRODUCTION_ACCEPTED → DAILY_OPERATION` | R-CONFLICT；CONTRACT-HASH-MISMATCH；SRC-POLICY；EVIDENCE-FAIL；CONTENT-QUALITY-FAIL；LANGUAGE-UX-FAIL；STATE-COUNT-FAIL；EMAIL-DUP；REPLAY-FAIL；LIVE-FAIL；P0/P1>0 |
| `S3` 真实运行、个人成长校准与持续认知复利 | 用真实 30 日运行、周/月报告、复习、行动和经济转化证据，证明系统能长期带来可验证成长而非只发送信息。 | `planned` | 3 | 180h | 9.73% | `COGNITIVE_COMPOUNDING_ACCEPTED → CONTINUOUS_OPERATION` | LIVE-FAIL；STATE-COUNT-FAIL；ROI-TRACE-FAIL；周/月报告缺失；合同漂移 |

总规划估算：**1850h**。这是治理所需的相对工程估算，不是日历承诺。

# S1：arXiv 单源纵向切片与生产基线

**Pursuing Goal：** 证明多源智能系统的最小纵向切片：采集、证据、评分、报告、邮件和运行可形成可审计闭环。

**Entry Gate：** V5 Stage 1 基线可读。

**Stop Gate：** `ARXIV_PRODUCTION_ACCEPTED`

**Stop Conditions：** R-CONFLICT；DATA-LOSS；EVIDENCE-FAIL；REPLAY-FAIL；LIVE-FAIL

## Phase 总览

| Phase | Pursuing Goal | 状态 | Task | 工时 | Entry Gate | Stop Gate | Stop Conditions |
|---|---|---|---:|---:|---|---|---|
| `S1PA` 基线审计、治理校准与防漂移（legacy `S1P1`） | 建立可追溯的 arXiv 单源项目事实图，并冻结 Stage 1 的唯一执行基线。 | `completed` | 3 | 34h | 仓库、V5 基线和现有治理文件可读。 | `S1_BASELINE_LOCKED` | R-CONFLICT；G-DRIFT；TRACE-FAIL |
| `S1PB` 人工控制面与数据基础（legacy `S1P2`） | 建立唯一控制配置、四个人类查看面和可回滚的数据存储基础。 | `completed` | 4 | 64h | S1PA 通过。 | `S1_CONTROL_AND_DATA_READY` | CFG-FAIL；DATA-LOSS；G-DRIFT |
| `S1PC` arXiv 单源纵向切片核心（legacy `S1P3`） | 证明 arXiv 从采集、规范化、证据、评分到队列的全链可重复、可解释、可审计。 | `completed` | 5 | 90h | S1PB 通过。 | `S1_ARXIV_CORE_READY` | SRC-POLICY；DET-FAIL；EVIDENCE-FAIL |
| `S1PD` 文本交付、邮件合同与本地运行（legacy `S1P4`） | 形成高密度中文报告、邮件幂等和可恢复本地运行纵向切片。 | `completed` | 3 | 54h | S1PC 通过。 | `S1_TEXT_DELIVERY_READY` | CONTENT-QUALITY-FAIL；EMAIL-DUP；OPS-FAIL |
| `S1PE` 真实重放、运行证据与 Stage 1 验收（legacy `S1P5`） | 以真实 arXiv 数据证明单源系统可达到生产验收基线。 | `completed` | 5 | 86h | S1PD 通过。 | `ARXIV_PRODUCTION_ACCEPTED` | REPLAY-FAIL；LIVE-FAIL；OPS-FAIL |

## S1PA：基线审计、治理校准与防漂移

**Pursuing Goal：** 建立可追溯的 arXiv 单源项目事实图，并冻结 Stage 1 的唯一执行基线。

**Entry Gate：** 仓库、V5 基线和现有治理文件可读。

**Stop Gate：** `S1_BASELINE_LOCKED`

**Stop Conditions：** R-CONFLICT；G-DRIFT；TRACE-FAIL

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S1PAT01` | `S1P1T01` | `completed` | 12h | **最小范围只读审计**：建立代码、配置、治理、工作流、测试和数据流事实图。 | V5 文件可读。 | 审计清单、现状图、风险清单和真实路径齐全。 | R-CONFLICT | `ACC-S1PAT01-AUDIT` |
| `S1PAT02` | `S1P1T02` | `completed` | 10h | **治理事实源校准**：统一版本、状态、计划和项目注册事实。 | S1PAT01 通过。 | 版本、状态、计划、任务和模型一致。 | G-DRIFT | `ACC-S1PAT02-GOV` |
| `S1PAT03` | `S1P1T03` | `completed` | 12h | **需求追踪与防漂移门禁**：建立 Requirement→Feature→Task→Config→Function→Test→Artifact→Evidence 追踪。 | S1PAT02 通过。 | 追踪覆盖完整并阻止范围回归。 | TRACE-FAIL | `ACC-S1PAT03-TRACE` |

## S1PB：人工控制面与数据基础

**Pursuing Goal：** 建立唯一控制配置、四个人类查看面和可回滚的数据存储基础。

**Entry Gate：** S1PA 通过。

**Stop Gate：** `S1_CONTROL_AND_DATA_READY`

**Stop Conditions：** CFG-FAIL；DATA-LOSS；G-DRIFT

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S1PBT01` | `S1P2T01` | `completed` | 14h | **owner controls 与 Schema**：建立唯一人工控制配置及校验。 | S1PA 通过。 | 权重、队列和板块配置可校验。 | CFG-FAIL | `ACC-S1PBT01-CONFIG` |
| `S1PBT02` | `S1P2T02` | `completed` | 14h | **四个人类查看文件生成器**：生成运行、来源、模型队列和内容账本视图。 | S1PBT01 通过。 | 视图由事实源生成且无漂移。 | G-DRIFT | `ACC-S1PBT02-HUMAN-VIEWS` |
| `S1PBT03` | `S1P2T03` | `completed` | 24h | **SQLite WAL + FTS5 统一模型与迁移**：实现文档、事件、Claim、队列、报告和邮件数据模型。 | S1PBT01 通过。 | 迁移可前进/回滚，事务和幂等通过。 | DATA-LOSS | `ACC-S1PBT03-DATA` |
| `S1PBT04` | `S1P2T04` | `completed` | 12h | **原始证据、哈希、备份恢复与旧数据 fixture**：实现 RawRecord、内容哈希和恢复验证。 | S1PBT03 通过。 | 恢复后哈希一致且 fixture 无重复。 | DATA-LOSS | `ACC-S1PBT04-RECOVERY` |

## S1PC：arXiv 单源纵向切片核心

**Pursuing Goal：** 证明 arXiv 从采集、规范化、证据、评分到队列的全链可重复、可解释、可审计。

**Entry Gate：** S1PB 通过。

**Stop Gate：** `S1_ARXIV_CORE_READY`

**Stop Conditions：** SRC-POLICY；DET-FAIL；EVIDENCE-FAIL

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S1PCT01` | `S1P3T01` | `completed` | 14h | **Source Registry 与 Connector Contract**：定义来源 ID、限流、缓存、健康和许可字段。 | S1PB 通过。 | arXiv 可通过通用接口运行。 | SRC-POLICY | `ACC-S1PCT01-SOURCE-CONTRACT` |
| `S1PCT02` | `S1P3T02` | `completed` | 18h | **arXiv Adapter 与小样本 fixture**：实现官方入口优先与可测试回退。 | S1PCT01 通过。 | fixture 和小样本在线测试通过。 | SRC-POLICY | `ACC-S1PCT02-ARXIV` |
| `S1PCT03` | `S1P3T03` | `completed` | 18h | **规范化、去重、版本、事件与 Taxonomy**：映射 CanonicalDocument/Version/Event。 | S1PCT02 通过。 | Canonical 重复为 0，版本和时间正确。 | DET-FAIL | `ACC-S1PCT03-CANONICAL` |
| `S1PCT04` | `S1P3T04` | `completed` | 16h | **研究评分卡、贡献明细与队列**：实现可解释排序、排队和淘汰原因。 | S1PCT03 通过。 | 同输入同配置同顺序。 | DET-FAIL | `ACC-S1PCT04-RANKING` |
| `S1PCT05` | `S1P3T05` | `completed` | 24h | **EvidencePacket、两遍分析与 Claim Ledger**：建立证据包、版本差分、反证和 Claim/Evidence 绑定。 | S1PCT03 与 S1PCT04 通过。 | 关键 Claim 证据绑定 100%。 | EVIDENCE-FAIL | `ACC-S1PCT05-EVIDENCE` |

## S1PD：文本交付、邮件合同与本地运行

**Pursuing Goal：** 形成高密度中文报告、邮件幂等和可恢复本地运行纵向切片。

**Entry Gate：** S1PC 通过。

**Stop Gate：** `S1_TEXT_DELIVERY_READY`

**Stop Conditions：** CONTENT-QUALITY-FAIL；EMAIL-DUP；OPS-FAIL

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S1PDT01` | `S1P4T01` | `completed` | 18h | **B1 高密度文本报告合同**：生成 Markdown/HTML/JSON 报告。 | S1PC 通过。 | 报告结构、引用和不确定性审计通过。 | CONTENT-QUALITY-FAIL | `ACC-S1PDT01-REPORT` |
| `S1PDT02` | `S1P4T02` | `completed` | 18h | **邮件预览、幂等和发送状态合同**：实现预览、哈希、重试和防重复。 | S1PDT01 通过。 | 同一 Run 不重复发送。 | EMAIL-DUP | `ACC-S1PDT02-EMAIL` |
| `S1PDT03` | `S1P4T03` | `completed` | 18h | **本地调度、Watchdog、备份与迁移包**：实现锁、heartbeat、补跑、恢复和迁移 Runbook。 | S1PDT02 通过。 | 恢复和安装/卸载模拟通过。 | OPS-FAIL | `ACC-S1PDT03-RUNTIME` |

## S1PE：真实重放、运行证据与 Stage 1 验收

**Pursuing Goal：** 以真实 arXiv 数据证明单源系统可达到生产验收基线。

**Entry Gate：** S1PD 通过。

**Stop Gate：** `ARXIV_PRODUCTION_ACCEPTED`

**Stop Conditions：** REPLAY-FAIL；LIVE-FAIL；OPS-FAIL

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S1PET01` | `S1P5T01` | `completed` | 12h | **目标运行机 bootstrap 与预检**：验证 CPU、RAM、磁盘、网络、SMTP 和调度。 | S1PD 通过。 | 运行机预检有证据。 | OPS-FAIL | `ACC-S1PET01-PREFLIGHT` |
| `S1PET02` | `S1P5T02` | `completed` | 12h | **真实 arXiv 单日全链预检**：完成真实抓取到报告/邮件预览。 | S1PET01 通过。 | 一次完整真实 Run 成功。 | OPS-FAIL | `ACC-S1PET02-LIVE-CHAIN` |
| `S1PET03` | `S1P5T03-R` | `completed` | 28h | **30 个独立历史日重放与账本闭环**：生成 30 个真实 as-of 日的报告和账本。 | S1PET02 通过。 | 30/30 终态、未来泄漏 0、P0/P1=0。 | REPLAY-FAIL | `ACC-S1PET03-REPLAY` |
| `S1PET04` | `S1P5T04` | `completed` | 18h | **连续真实运行与 Stage 1 验收**：验证调度、恢复和受控邮件证据。 | S1PET03 通过。 | ARXIV_PRODUCTION_ACCEPTED。 | LIVE-FAIL；EMAIL-DUP | `ACC-S1PET04-STAGE1` |
| `S1PET05` | `ADP-S1P5T05` | `completed` | 16h | **本机生产运行与迁移准备**：完成 local runner、持久化和迁移准备。 | S1PET04 通过。 | 本地运行准备完成，云端生产调度关闭。 | OPS-FAIL | `ACC-S1PET05-LOCAL` |

# S2：多源、深度理解、个人成长与 3+1 邮件融合开发

**Pursuing Goal：** 将四个数据源域、三个主阅读板块、三个横切副板块、深度理解、中文人类界面、复习、行动、ROI、周/月报告和每日 3+1 邮件融合为同一生产系统。

**Entry Gate：** ARXIV_PRODUCTION_ACCEPTED；当前 S2P1T01 可继续，但所有生产晋升必须读取 V7 合同。

**Stop Gate：** `INTEGRATED_PRODUCTION_ACCEPTED → DAILY_OPERATION`

**Stop Conditions：** R-CONFLICT；CONTRACT-HASH-MISMATCH；SRC-POLICY；EVIDENCE-FAIL；CONTENT-QUALITY-FAIL；LANGUAGE-UX-FAIL；STATE-COUNT-FAIL；EMAIL-DUP；REPLAY-FAIL；LIVE-FAIL；P0/P1>0

## Phase 总览

| Phase | Pursuing Goal | 状态 | Task | 工时 | Entry Gate | Stop Gate | Stop Conditions |
|---|---|---|---:|---:|---|---|---|
| `S2PA` V7 产品契约、中文可读治理与任务兼容 | 把本次 Owner 决策固化为唯一、中文、人类可读且机器可校验的 V7 基线，使所有 Stage 2 线程读取同一合同。 | `in_progress` | 4 | 40h | Stage 1 已验收；仓库当前 V5/V6 基线和三基文件可读。 | `V7_PRODUCT_CONTRACT_LOCKED` | R-CONFLICT；G-DRIFT；TRACE-FAIL；CONTRACT-HASH-MISMATCH |
| `S2PB` D1 研究、预印本与医学索引数据源域（legacy `S2P1`） | 在不回归 arXiv 的前提下，逐源晋升研究/预印本/索引增强来源，并统一输出 EvidencePacket。 | `in_progress` | 5 | 124h | ARXIV_PRODUCTION_ACCEPTED；S2PAT02 的产品契约至少可读。 | `D1_SOURCE_DOMAIN_ACCEPTED` | SRC-POLICY；DET-FAIL；SCHEMA-BREAK；BOARD-MAP-FAIL |
| `S2PC` D2 权威发表、工程开源与产业技术报告数据源域（legacy `S2P2`） | 建立从顶级期刊到工程实现、权威技术报告和产业落地信号的第二数据源域。 | `planned` | 7 | 144h | D1 通用来源框架稳定。 | `D2_SOURCE_DOMAIN_ACCEPTED` | SRC-POLICY；EVIDENCE-FAIL；错误文章类型；营销材料冒充证据 |
| `S2PD` D3 中国官方核心数据源域（legacy `S2P3`） | 建立全国和中央官方政策、法律、产业、科技与经济信号的权威主干。 | `planned` | 4 | 104h | 通用政府来源连接器可用。 | `D3_CORE_SOURCE_DOMAIN_ACCEPTED` | SRC-POLICY；法律状态未知；转载冒充原始源 |
| `S2PE` D4 美国官方科技金融数据源域（legacy `S2P4`） | 建立美国科技创新、法律、金融、宏观和技术政策官方信号域。 | `planned` | 4 | 104h | 官方来源、实体和关系框架稳定。 | `D4_SOURCE_DOMAIN_ACCEPTED` | SRC-POLICY；表单/实体关系错误；非官方源冒充官方 |
| `S2PF` D3 中国地方与特殊区域全覆盖（legacy `S2P5`） | 在不淹没中央权威信号的前提下，扩展省级、港澳、重点城市和特殊功能区。 | `planned` | 5 | 120h | D3 核心稳定。 | `D3_FULL_SOURCE_DOMAIN_ACCEPTED` | 来源数量掩盖质量；官方域名验证失败；区域关系错误 |
| `S2PG` 统一证据骨干、知识图谱与 4 源→3 主/3 副路由（legacy `S2P6`） | 把来源、阅读板块和邮件产品彻底解耦，形成全系统共用的证据、关系、路由和排序骨干。 | `planned` | 5 | 128h | D1–D4 至少各有一个稳定来源；V7 契约已锁定。 | `UNIFIED_INTELLIGENCE_BACKBONE_READY` | SCHEMA-BREAK；EVIDENCE-FAIL；BOARD-MAP-FAIL；DET-FAIL |
| `S2PH` Stage 1+ 深度理解、个人情报与内容质量 | 让 arXiv 和所有 Stage 2 来源都达到“像直接向 ChatGPT 深问一样”的深度，同时保留证据、不确定性和个人价值。 | `planned` | 5 | 116h | S2PGT01 可用；Stage 1 报告链可回归测试。 | `DEEP_INTELLIGENCE_QUALITY_ACCEPTED` | CONTENT-QUALITY-FAIL；EVIDENCE-FAIL；模板化空泛；个人影响无依据 |
| `S2PI` 中文用户中心、一改四查三基与真实状态可视化 | 让用户无需进入 config/docs/governance 即可控制、检查和验收系统，且看到真实数量而非仅容量。 | `planned` | 5 | 124h | S2PAT04 中文规则可用；现有 owner_controls 和数据库可读。 | `OWNER_EXPERIENCE_ACCEPTED` | LANGUAGE-UX-FAIL；STATE-COUNT-FAIL；G-DRIFT；重复可编辑事实源 |
| `S2PJ` 复习、行动、能力资产、ROI 与周/月复利闭环 | 把“阅读完成”扩展为可复习、可行动、可形成资产、可记录经济转化的长期成长闭环。 | `planned` | 5 | 120h | S2PHT 深度内容结构和 S2PIT 状态面可用。 | `COGNITIVE_GROWTH_LOOP_READY` | REVIEW-FAIL；ROI-TRACE-FAIL；STATE-COUNT-FAIL；虚假精确收益 |
| `S2PK` 每日 3＋1 邮件、错峰生成与正向 UI/UX | 稳定生成三封主板块邮件和一封跨板块汇总邮件，兼顾信息效率、深度、反馈、ROI 和防重复。 | `planned` | 5 | 106h | S2PG–S2PJ 的必要接口可用。 | `FOUR_EMAIL_SYSTEM_READY` | EMAIL-DUP；EMAIL-WATERLINE-FAIL；CONTENT-QUALITY-FAIL；M4 提前生成 |
| `S2PL` 全系统重放、真实运行与集成生产验收（legacy `S2P7`） | 以完整证据证明四数据源域、六阅读板块、3+1 邮件、复习、行动、ROI、周报和月报可稳定运行。 | `planned` | 4 | 112h | S2PA–S2PK 全部门禁通过或有 Owner 批准的显式降级。 | `INTEGRATED_PRODUCTION_ACCEPTED` | REPLAY-FAIL；LIVE-FAIL；OPS-FAIL；STATE-COUNT-FAIL；P0/P1>0 |

## S2PA：V7 产品契约、中文可读治理与任务兼容

**Pursuing Goal：** 把本次 Owner 决策固化为唯一、中文、人类可读且机器可校验的 V7 基线，使所有 Stage 2 线程读取同一合同。

**Entry Gate：** Stage 1 已验收；仓库当前 V5/V6 基线和三基文件可读。

**Stop Gate：** `V7_PRODUCT_CONTRACT_LOCKED`

**Stop Conditions：** R-CONFLICT；G-DRIFT；TRACE-FAIL；CONTRACT-HASH-MISMATCH

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PAT01` | — | `ready` | 8h | **只读冲突审计与 V6→V7 迁移矩阵**：核对 V5/V6、当前代码配置、三基文件和本任务包，列出冲突、旧名与迁移顺序。 | 只读范围已声明。 | 冲突矩阵完整；未决冲突均有单一 Owner 决策入口。 | R-CONFLICT；越界扫描 | `ACC-S2PAT01-V7-AUDIT` |
| `S2PAT02` | — | `planned` | 10h | **锁定 V7 产品契约与关键决策记录**：建立 product_contract、decision_log、requirements 和基线锁，并记录 4 源/3 主/3 副/3+1 邮件。 | S2PAT01 通过。 | 所有关键 Owner 要求有稳定 ID、状态、来源和验收标准。 | TRACE-FAIL；G-DRIFT | `ACC-S2PAT02-CONTRACT` |
| `S2PAT03` | — | `planned` | 10h | **任务 ID 兼容、Roadmap V7 与 AGENTS/README 同步**：采用字母 Phase 规范并保留 V6 数字 ID alias；更新当前任务映射和唯一基线入口。 | S2PAT02 通过。 | 当前 S2P1T01 映射为 S2PBT01；历史事件不改写。 | G-DRIFT；历史证据被覆盖 | `ACC-S2PAT03-ROADMAP` |
| `S2PAT04` | — | `planned` | 12h | **中文人类视图、合同哈希与 CI 防漂移门**：使三基文件、用户中心、PR/CI 摘要显示合同版本与哈希并中文优先。 | S2PAT03 通过。 | 英文-only 人类界面和合同哈希漂移能被 CI 阻断。 | LANGUAGE-UX-FAIL；CONTRACT-HASH-MISMATCH | `ACC-S2PAT04-CN-CI` |

## S2PB：D1 研究、预印本与医学索引数据源域

**Pursuing Goal：** 在不回归 arXiv 的前提下，逐源晋升研究/预印本/索引增强来源，并统一输出 EvidencePacket。

**Entry Gate：** ARXIV_PRODUCTION_ACCEPTED；S2PAT02 的产品契约至少可读。

**Stop Gate：** `D1_SOURCE_DOMAIN_ACCEPTED`

**Stop Conditions：** SRC-POLICY；DET-FAIL；SCHEMA-BREAK；BOARD-MAP-FAIL

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PBT01` | `S2P1T01` | `in_progress` | 24h | **bioRxiv 与 medRxiv 晋升**：接入生命科学和医学预印本，验证第二类来源及 D1→B1/B2/B4/B5/B6 路由。 | Stage 1 通过；当前线程可继续，但生产晋升需 S2PAT02。 | 各自 fixture、30 日终态、48h Shadow、身份/版本/许可门通过。 | SRC-POLICY；重复论文；Shadow 影响正式邮件 | `ACC-S2PBT01-BIORXIV-MEDRXIV` |
| `S2PBT02` | `S2P1T02` | `planned` | 24h | **PubMed 与 Europe PMC 增强源**：实现 PMID/DOI 对齐、开放全文和资助关系，不重复创建原始论文。 | S2PBT01 或通用框架稳定。 | 增强关系、许可和全文级别正确。 | SRC-POLICY；重复 Canonical | `ACC-S2PBT02-PUBMED-EPMC` |
| `S2PBT03` | `S2P1T03` | `planned` | 24h | **TechRxiv、ChemRxiv、EarthArXiv 晋升**：扩展工程、化学、材料和地球环境预印本。 | D1 通用连接器稳定。 | 三个来源均可独立降级和回滚。 | SRC-POLICY；解析漂移静默 | `ACC-S2PBT03-PREPRINTS` |
| `S2PBT04` | `S2P1T04` | `planned` | 28h | **SSRN 与 ChinaXiv 高风险来源**：处理条款、低频网页、中文元数据和页面漂移。 | HTML/许可/健康框架通过。 | 条款可审计、中文字段完整、失败显式。 | SRC-POLICY；中文字段静默丢失 | `ACC-S2PBT04-SSRN-CHINAXIV` |
| `S2PBT05` | `S2P1T05` | `planned` | 24h | **D1 数据源域全量资格与 Stage 1 回归**：完成 D1 十来源重放、队列、EvidencePacket 和 arXiv 回归。 | S2PBT01–T04 通过或有批准降级。 | D1 30 日重放、2 日 Shadow、旧 arXiv 无回归。 | REPLAY-FAIL；BOARD-MAP-FAIL | `ACC-S2PBT05-D1` |

## S2PC：D2 权威发表、工程开源与产业技术报告数据源域

**Pursuing Goal：** 建立从顶级期刊到工程实现、权威技术报告和产业落地信号的第二数据源域。

**Entry Gate：** D1 通用来源框架稳定。

**Stop Gate：** `D2_SOURCE_DOMAIN_ACCEPTED`

**Stop Conditions：** SRC-POLICY；EVIDENCE-FAIL；错误文章类型；营销材料冒充证据

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PCT01` | `S2P2T01` | `planned` | 16h | **Nature 主刊晋升**：接入官方发现入口、文章类型、更正和 DOI。 | D1 框架稳定。 | 来源级 replay/Shadow、许可和事件通过。 | SRC-POLICY；订阅墙绕过 | `ACC-S2PCT01-NATURE` |
| `S2PCT02` | `S2P2T02` | `planned` | 16h | **Science 主刊晋升**：识别 Research/Report/Review/Perspective 等类型。 | S2PCT01 框架稳定。 | 来源级门禁通过且不影响 D1。 | 错误文章类型；重复 DOI | `ACC-S2PCT02-SCIENCE` |
| `S2PCT03` | `S2P2T03` | `planned` | 20h | **The Lancet 主刊晋升**：接入 Online First、PubMed 关系和医学文章类型。 | S2PCT02 框架稳定。 | 索引对齐、许可和类型门通过。 | Correspondence 冒充研究；许可不明 | `ACC-S2PCT03-LANCET` |
| `S2PCT04` | `S2P2T04` | `planned` | 20h | **顶刊 Profile、发表关系、更正撤回**：差异化建模研究、综述、社论、新闻、更正和撤回。 | S2PCT01–T03 通过。 | 撤回/更正强制事件能更新旧结论。 | EVIDENCE-FAIL；撤回未传播 | `ACC-S2PCT04-JOURNAL-PROFILE` |
| `S2PCT05` | — | `planned` | 24h | **工程开源、代码、基准和标准公开信号框架**：接入论文关联代码、官方发布、模型卡、基准和标准信号，形成 B2 工程证据。 | D2 Profile 可扩展。 | 官方性、版本、仓库/论文关系和复现状态可追溯。 | 非官方镜像冒充原始源；版本不可追溯 | `ACC-S2PCT05-ENGINEERING-SIGNALS` |
| `S2PCT06` | — | `planned` | 24h | **权威研究机构与产业技术报告框架**：接入公开、可审计的研究机构、实验室和企业技术报告/产品技术说明。 | S2PCT05 通过。 | 报告类型、发布主体、利益关系和证据级别明确。 | 营销材料冒充研究；来源身份错误 | `ACC-S2PCT06-REPORTS` |
| `S2PCT07` | — | `planned` | 24h | **D2 数据源域资格与跨类型校准**：完成顶刊、工程、报告来源的 30 日重放和类型差异评分。 | S2PCT01–T06 通过或批准降级。 | D2 30 日重放、2 日 Shadow、强制事件和队列解释通过。 | REPLAY-FAIL；类型权重失真 | `ACC-S2PCT07-D2` |

## S2PD：D3 中国官方核心数据源域

**Pursuing Goal：** 建立全国和中央官方政策、法律、产业、科技与经济信号的权威主干。

**Entry Gate：** 通用政府来源连接器可用。

**Stop Gate：** `D3_CORE_SOURCE_DOMAIN_ACCEPTED`

**Stop Conditions：** SRC-POLICY；法律状态未知；转载冒充原始源

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PDT01` | `S2P3T01` | `planned` | 24h | **中国 C0 全国权威主干**：接入法律法规、人大、国务院、公报和两高。 | 政府连接器可用。 | 机关、文号、附件和日期可追溯。 | 转载冒充原始源 | `ACC-S2PDT01-C0` |
| `S2PDT02` | `S2P3T02` | `planned` | 32h | **中国 C1 中央机关与重点部门**：覆盖宏观、科技、产业、金融、市场和重点行业部门。 | S2PDT01 通过。 | 机构模板、别名、行业映射和官方域名完整。 | 部门清单缩水；人工逐源硬编码 | `ACC-S2PDT02-C1` |
| `S2PDT03` | `S2P3T03` | `planned` | 24h | **法律元数据、版本效力与转载关系**：实现草案/正式、修订/废止、实施/解释关系。 | S2PDT01–T02 通过。 | 法律状态变化能触发重评分和旧结论更新。 | 法律状态未知；日期混淆 | `ACC-S2PDT03-LEGAL` |
| `S2PDT04` | `S2P3T04` | `planned` | 24h | **D3 核心资格与阅读板块路由**：完成 C0/C1 重放并路由到 B2/B3/B4/B5/B6。 | S2PDT01–T03 通过。 | 30 日重放、2 日 Shadow、权威性和路由解释通过。 | REPLAY-FAIL；BOARD-MAP-FAIL | `ACC-S2PDT04-D3-CORE` |

## S2PE：D4 美国官方科技金融数据源域

**Pursuing Goal：** 建立美国科技创新、法律、金融、宏观和技术政策官方信号域。

**Entry Gate：** 官方来源、实体和关系框架稳定。

**Stop Gate：** `D4_SOURCE_DOMAIN_ACCEPTED`

**Stop Conditions：** SRC-POLICY；表单/实体关系错误；非官方源冒充官方

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PET01` | `S2P4T01` | `planned` | 28h | **US-TA 科技创新与突破**：接入 NSF、DARPA、DOE、NIH、NASA、NIST、USPTO、FDA 等。 | 美国官方来源框架可用。 | 资助、专利、临床、标准关系可审计。 | 科技创新权重被稀释 | `ACC-S2PET01-US-TA` |
| `S2PET02` | `S2P4T02` | `planned` | 20h | **US-LG 跨机构法律主干**：接入 Federal Register、Regulations.gov、GovInfo、Congress 等。 | S2PET01 框架稳定。 | Docket、FR、法案和认证文本关系正确。 | 草案冒充最终文本 | `ACC-S2PET02-US-LG` |
| `S2PET03` | `S2P4T03` | `planned` | 28h | **US-FM 金融、市场与宏观**：接入 SEC、Fed、Treasury、CFTC、OCC、FDIC、CFPB 等。 | S2PET02 通过。 | 表单、CIK、Accession、基金/公司/资产关系通过。 | 表单分类错误；自动交易行为 | `ACC-S2PET03-US-FM` |
| `S2PET04` | `S2P4T04` | `planned` | 28h | **US-TP 技术政策与 D4 资格**：接入 OSTP、BIS、FTC、FCC、CISA、CHIPS 等并完成 D4。 | S2PET01–T03 通过。 | D4 30 日重放、2 日 Shadow、板块路由和预算解释通过。 | REPLAY-FAIL；BOARD-MAP-FAIL | `ACC-S2PET04-D4` |

## S2PF：D3 中国地方与特殊区域全覆盖

**Pursuing Goal：** 在不淹没中央权威信号的前提下，扩展省级、港澳、重点城市和特殊功能区。

**Entry Gate：** D3 核心稳定。

**Stop Gate：** `D3_FULL_SOURCE_DOMAIN_ACCEPTED`

**Stop Conditions：** 来源数量掩盖质量；官方域名验证失败；区域关系错误

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PFT01` | `S2P5T01` | `planned` | 32h | **全部省级模板与核心覆盖**：覆盖全部省级行政区域核心部门。 | D3 核心稳定。 | 省级清单和健康分层完整。 | 遗漏行政区域 | `ACC-S2PFT01-PROVINCES` |
| `S2PFT02` | `S2P5T02` | `planned` | 16h | **香港与澳门独立 Profile**：按独立法律和政府结构建模。 | S2PFT01 模板可扩展。 | 司法辖区、语言和法律状态独立正确。 | 套用内地模板 | `ACC-S2PFT02-HK-MO` |
| `S2PFT03` | `S2P5T03` | `planned` | 24h | **首批重点城市覆盖**：按部门模板覆盖重点城市并支持别名。 | S2PFT01 通过。 | 城市覆盖矩阵、区域权重和健康状态通过。 | 城市缺失；别名错误 | `ACC-S2PFT03-CITIES` |
| `S2PFT04` | `S2P5T04` | `planned` | 24h | **特殊功能区与垂直机构自动发现**：发现自贸区、高新区、海关、税务、金融监管等。 | S2PFT03 通过。 | 官方性验证、去重、父子关系和复审面通过。 | 非官方园区进入生产 | `ACC-S2PFT04-ZONES` |
| `S2PFT05` | `S2P5T05` | `planned` | 24h | **D3 全覆盖资格与地方来源治理**：完成 C0–C4 配额、健康、淘汰和回退机制。 | S2PFT01–T04 通过。 | D3 全量重放、来源平衡和淘汰解释通过。 | 低质量地方源淹没队列 | `ACC-S2PFT05-D3-FULL` |

## S2PG：统一证据骨干、知识图谱与 4 源→3 主/3 副路由

**Pursuing Goal：** 把来源、阅读板块和邮件产品彻底解耦，形成全系统共用的证据、关系、路由和排序骨干。

**Entry Gate：** D1–D4 至少各有一个稳定来源；V7 契约已锁定。

**Stop Gate：** `UNIFIED_INTELLIGENCE_BACKBONE_READY`

**Stop Conditions：** SCHEMA-BREAK；EVIDENCE-FAIL；BOARD-MAP-FAIL；DET-FAIL

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PGT01` | — | `planned` | 24h | **EvidencePacket V2 与证据级别**：统一元数据级、摘要级、全文级、跨源核验级证据字段。 | V7 契约锁定。 | 所有连接器可输出同一版本 EvidencePacket，旧 arXiv 兼容。 | SCHEMA-BREAK；证据级别缺失 | `ACC-S2PGT01-EVIDENCE-V2` |
| `S2PGT02` | `S2P6T01` | `planned` | 28h | **跨源身份解析与知识图谱**：整合 DOI/PMID/arXiv/文号/FR/CIK 等关系。 | S2PGT01 通过。 | 重复 Canonical 0，关系有证据且更新幂等。 | 错误实体合并 | `ACC-S2PGT02-KG` |
| `S2PGT03` | — | `planned` | 28h | **D1–D4 到 B1–B6 多标签路由**：实现 3 主板块和 3 横切副板块的多对多解释路由。 | S2PGT01 通过。 | 每条重要内容有来源域、主板块、横切板块和原因码。 | BOARD-MAP-FAIL | `ACC-S2PGT03-ROUTING` |
| `S2PGT04` | — | `planned` | 24h | **跨源支持、反驳、前沿变化量与信号共振**：识别支持/反驳/版本差分和多类信号共振。 | S2PGT02–T03 通过。 | 关系、前沿 Delta 和共振结论可追溯。 | EVIDENCE-FAIL；反证被过滤 | `ACC-S2PGT04-DELTA-RESONANCE` |
| `S2PGT05` | `S2P6T02` | `planned` | 24h | **跨板块校准、组合排序与可解释队列**：建立分位数校准、来源平衡、等待信用和队列原因。 | S2PGT03–T04 通过。 | 同输入同配置同顺序，队列和淘汰原因可读。 | DET-FAIL；单源淹没 | `ACC-S2PGT05-CALIBRATION` |

## S2PH：Stage 1+ 深度理解、个人情报与内容质量

**Pursuing Goal：** 让 arXiv 和所有 Stage 2 来源都达到“像直接向 ChatGPT 深问一样”的深度，同时保留证据、不确定性和个人价值。

**Entry Gate：** S2PGT01 可用；Stage 1 报告链可回归测试。

**Stop Gate：** `DEEP_INTELLIGENCE_QUALITY_ACCEPTED`

**Stop Conditions：** CONTENT-QUALITY-FAIL；EVIDENCE-FAIL；模板化空泛；个人影响无依据

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PHT01` | — | `planned` | 16h | **10 项差异化金标集与人工评分规程**：选择跨学科、不同证据级别的 10 项内容作为质量基准。 | V7 内容合同可读。 | 深度、清晰、相关、行动和反证五维评分规程锁定。 | 金标集不具代表性 | `ACC-S2PHT01-GOLD-SET` |
| `S2PHT02` | — | `planned` | 28h | **摘要/全文/图表分层深度分析流水线**：回答问题、旧方法、新方法、机制、实验、结果、限制和适用条件。 | S2PHT01 通过。 | 摘要级不冒充全文级；关键事实证据绑定 100%。 | EVIDENCE-FAIL；全文不可用仍声称已读 | `ACC-S2PHT02-DEEP-ANALYSIS` |
| `S2PHT03` | — | `planned` | 24h | **个人画像、项目、能力与目标映射**：将内容映射到用户项目、能力、时间、学习和经济路径。 | S2PHT02 结构稳定。 | 个人影响有字段、理由、置信度和时间尺度。 | 个人影响无依据 | `ACC-S2PHT03-PERSONAL` |
| `S2PHT04` | — | `planned` | 24h | **时代影响、反炒作、失败条件与预测问题**：加入社会/时代影响、最强反对意见和可证伪预测。 | S2PHT02 通过。 | 每项主讲包含最强反对意见和推翻条件。 | 反证被过滤；营销性结论 | `ACC-S2PHT04-ANTI-HYPE` |
| `S2PHT05` | — | `planned` | 24h | **内容质量门与 Stage 1 arXiv 回灌**：将新分析合同应用到 arXiv 和所有来源，建立自动+人工质量门。 | S2PHT01–T04 通过。 | 10 项金标均达标，旧采集/证据/邮件链无回归。 | CONTENT-QUALITY-FAIL；Stage 1 回归 | `ACC-S2PHT05-CONTENT-GATE` |

## S2PI：中文用户中心、一改四查三基与真实状态可视化

**Pursuing Goal：** 让用户无需进入 config/docs/governance 即可控制、检查和验收系统，且看到真实数量而非仅容量。

**Entry Gate：** S2PAT04 中文规则可用；现有 owner_controls 和数据库可读。

**Stop Gate：** `OWNER_EXPERIENCE_ACCEPTED`

**Stop Conditions：** LANGUAGE-UX-FAIL；STATE-COUNT-FAIL；G-DRIFT；重复可编辑事实源

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PIT01` | — | `planned` | 24h | **00_用户中心与“一改”控制入口**：建立一个编辑目录，分离画像、邮件复习、来源板块、预算调度。 | S2PAT04 通过。 | 用户常用控制在两次点击内，编译到兼容配置。 | 重复可编辑事实源 | `ACC-S2PIT01-USER-CENTER` |
| `S2PIT02` | — | `planned` | 24h | **运行任务与真实队列总控台**：显示实际排队、已讲解、已报告、已发送、失败和最老等待时间。 | SQLite 状态可查询。 | 分项总数守恒，显示 generated_at/data_as_of 和过期警告。 | STATE-COUNT-FAIL | `ACC-S2PIT02-RUNTIME-DASHBOARD` |
| `S2PIT03` | — | `planned` | 24h | **数据源、阅读板块、模型参数与全量队列视图**：显示 D1–D4、B1–B6 健康、所有参数、来源和影响。 | S2PGT03–T05 可用。 | 参数、代码、测试、默认值、范围和回滚值可读。 | LANGUAGE-UX-FAIL；参数遗漏 | `ACC-S2PIT03-SOURCE-MODEL` |
| `S2PIT04` | — | `planned` | 24h | **内容、邮件、复习、行动与 ROI 总账**：统一展示内容生命周期、邮件、复习、行动、能力资产和转化。 | 状态模型字段冻结。 | 每条记录可追溯到内容、证据、Run、邮件和反馈。 | STATE-COUNT-FAIL；ROI-TRACE-FAIL | `ACC-S2PIT04-LEDGER` |
| `S2PIT05` | — | `planned` | 28h | **三基文件全量中文渲染与 CodexProject 全局中文门**：更新功能清单、开发记录、模型参数文件，并将中文优先扩展到根 README、PR/CI 和所有项目人类界面。 | S2PIT01–T04 通过。 | 三基文件非跳转页，完整包含需求、Roadmap、参数、状态和验收。 | LANGUAGE-UX-FAIL；G-DRIFT | `ACC-S2PIT05-THREE-BASE` |

## S2PJ：复习、行动、能力资产、ROI 与周/月复利闭环

**Pursuing Goal：** 把“阅读完成”扩展为可复习、可行动、可形成资产、可记录经济转化的长期成长闭环。

**Entry Gate：** S2PHT 深度内容结构和 S2PIT 状态面可用。

**Stop Gate：** `COGNITIVE_GROWTH_LOOP_READY`

**Stop Conditions：** REVIEW-FAIL；ROI-TRACE-FAIL；STATE-COUNT-FAIL；虚假精确收益

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PJT01` | — | `planned` | 24h | **内容学习生命周期与数据库迁移**：建立 REVIEW_DUE、ACTION、ASSET、CONVERSION、MASTERED 等状态。 | 统一内容 ID 和数据库迁移接口可用。 | 迁移可回滚，状态历史追加且守恒。 | DATA-LOSS；STATE-COUNT-FAIL | `ACC-S2PJT01-LIFECYCLE` |
| `S2PJT02` | — | `planned` | 24h | **可配置复习调度与到期队列**：实现默认 1/3/7/14/30/90 天复习，并按反馈调整。 | S2PJT01 通过。 | 今日到期、7 日到期、逾期和已完成数量正确。 | REVIEW-FAIL | `ACC-S2PJT02-REVIEW` |
| `S2PJT03` | — | `planned` | 28h | **行动、能力资产与预计/实际 ROI 账本**：记录 15 分钟/2 小时/7 天/30 天行动及实际收益。 | S2PJT01 通过。 | 预计值有假设和置信度；实际 ROI 仅在可核验成本/收益时计算。 | ROI-TRACE-FAIL；虚假精确收益 | `ACC-S2PJT03-ROI` |
| `S2PJT04` | — | `planned` | 20h | **每周总结与注意力再分配**：生成周度主线、反证、复习、行动、资产和下周重点。 | 复习与行动账本可用。 | 周报可追溯到本周内容与实际状态。 | 内容重复堆砌 | `ACC-S2PJT04-WEEKLY` |
| `S2PJT05` | — | `planned` | 24h | **每月认知差分、能力增长与经济转化总结**：生成月度时代主线、观点变化、能力资产、实际 ROI 和预测复盘。 | S2PJT03–T04 通过。 | 月报包含月初/月底认知差分和可核验转化。 | ROI-TRACE-FAIL；无证据成长率 | `ACC-S2PJT05-MONTHLY` |

## S2PK：每日 3＋1 邮件、错峰生成与正向 UI/UX

**Pursuing Goal：** 稳定生成三封主板块邮件和一封跨板块汇总邮件，兼顾信息效率、深度、反馈、ROI 和防重复。

**Entry Gate：** S2PG–S2PJ 的必要接口可用。

**Stop Gate：** `FOUR_EMAIL_SYSTEM_READY`

**Stop Conditions：** EMAIL-DUP；EMAIL-WATERLINE-FAIL；CONTENT-QUALITY-FAIL；M4 提前生成

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PKT01` | — | `planned` | 20h | **统一邮件内容合同、状态与反馈组件**：定义三层阅读、证据标签、反馈按钮、哈希和状态。 | 内容质量合同通过。 | 四封邮件共享契约但保持板块差异。 | CONTENT-QUALITY-FAIL | `ACC-S2PKT01-MAIL-CONTRACT` |
| `S2PKT02` | — | `planned` | 18h | **M1 科学与理论前沿邮件**：生成 B1 主邮件并挂载 B4/B5/B6。 | S2PKT01 通过。 | 科学机制、证据、反证、个人价值和行动齐全。 | EVIDENCE-FAIL | `ACC-S2PKT02-M1` |
| `S2PKT03` | — | `planned` | 20h | **M2 工程、产品与产业前沿邮件**：生成合并后的 B2 主邮件并挂载 B4/B5/B6。 | S2PKT01 通过。 | 工程可用性、复现、产品/产业价值和限制齐全。 | 工程与营销信号混淆 | `ACC-S2PKT03-M2` |
| `S2PKT04` | — | `planned` | 20h | **M3 政策、资本与地缘前沿邮件**：生成 B3 主邮件并挂载 B4/B5/B6。 | S2PKT01 通过。 | 法律状态、资本影响、地缘背景和个人影响齐全。 | 法律状态未知仍发布 | `ACC-S2PKT04-M3` |
| `S2PKT05` | `S2P6T03` | `planned` | 28h | **M4 跨板块总览、错峰编排与水位线**：在 M1–M3 明确终态后生成跨源共振、矛盾、时代主线、个人行动组合和复习提醒。 | S2PKT02–T04 通过。 | 每日 3+1 互不替代、重复 0、无静默消失；默认错峰 07:30/11:30/17:00/21:30。 | EMAIL-DUP；EMAIL-WATERLINE-FAIL；M4 提前生成 | `ACC-S2PKT05-M4` |

## S2PL：全系统重放、真实运行与集成生产验收

**Pursuing Goal：** 以完整证据证明四数据源域、六阅读板块、3+1 邮件、复习、行动、ROI、周报和月报可稳定运行。

**Entry Gate：** S2PA–S2PK 全部门禁通过或有 Owner 批准的显式降级。

**Stop Gate：** `INTEGRATED_PRODUCTION_ACCEPTED`

**Stop Conditions：** REPLAY-FAIL；LIVE-FAIL；OPS-FAIL；STATE-COUNT-FAIL；P0/P1>0

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S2PLT01` | `S2P7T01` | `planned` | 40h | **全系统 30 个独立历史日重放**：运行 4 源→6 板块→每日 4 邮件全流程，生成 120 份报告/预览及完整账本。 | S2PA–S2PK 通过。 | 30/30 独立 as-of、未来泄漏 0、全来源终态、P0/P1=0。 | REPLAY-FAIL | `ACC-S2PLT01-30D` |
| `S2PLT02` | `S2P7T02` | `planned` | 24h | **连续 2 个真实自然日与 8 封邮件**：在真实调度、网络和 SMTP 下每天发送 3+1。 | S2PLT01 通过。 | 两日 8 封邮件完整、无重复、M4 水位线正确。 | LIVE-FAIL；EMAIL-DUP | `ACC-S2PLT02-2D` |
| `S2PLT03` | `S2P7T03` | `planned` | 32h | **韧性、容量、回滚和状态一致性演练**：验证限流、解析漂移、重启、磁盘、备份、回滚和状态计数。 | S2PLT02 通过。 | 故障演练有证据，恢复点可执行，账本总数守恒。 | OPS-FAIL；DATA-LOSS；STATE-COUNT-FAIL | `ACC-S2PLT03-RESILIENCE` |
| `S2PLT04` | `S2P7T04` | `planned` | 16h | **最终集成验收与 DAILY_OPERATION 切换**：审计追踪、中文人类视图、调度、复习、ROI、周/月报告和 Owner 操作面。 | S2PLT01–T03 通过。 | INTEGRATED_PRODUCTION_ACCEPTED → DAILY_OPERATION。 | 任何 Gate 未闭合；用代码存在代替运行证据 | `ACC-S2PLT04-PRODUCTION` |

# S3：真实运行、个人成长校准与持续认知复利

**Pursuing Goal：** 用真实 30 日运行、周/月报告、复习、行动和经济转化证据，证明系统能长期带来可验证成长而非只发送信息。

**Entry Gate：** INTEGRATED_PRODUCTION_ACCEPTED。

**Stop Gate：** `COGNITIVE_COMPOUNDING_ACCEPTED → CONTINUOUS_OPERATION`

**Stop Conditions：** LIVE-FAIL；STATE-COUNT-FAIL；ROI-TRACE-FAIL；周/月报告缺失；合同漂移

## Phase 总览

| Phase | Pursuing Goal | 状态 | Task | 工时 | Entry Gate | Stop Gate | Stop Conditions |
|---|---|---|---:|---:|---|---|---|
| `S3PA` 30 个真实自然日运行与日周月证据 | 证明系统不仅能通过重放，还能在真实时间中持续产生稳定、高质量、可复习和可行动的情报。 | `planned` | 4 | 68h | INTEGRATED_PRODUCTION_ACCEPTED。 | `THIRTY_DAY_OPERATION_EVIDENCED` | LIVE-FAIL；EMAIL-DUP；STATE-COUNT-FAIL；周/月报告缺失 |
| `S3PB` 个人成长、内容质量与 ROI 校准 | 用真实反馈和行动结果校准内容、复习、个人价值和经济转化模型。 | `planned` | 4 | 68h | S3PA 通过。 | `PERSONAL_GROWTH_MODEL_CALIBRATED` | 无真实反馈却改模型；自动修改冻结参数；未来信息泄漏 |
| `S3PC` 预测账本、来源治理与持续认知复利 | 建立可证伪预测、来源准入/淘汰和持续改善机制，使系统长期提高而不漂移。 | `planned` | 4 | 44h | S3PB 通过。 | `COGNITIVE_COMPOUNDING_ACCEPTED` | 预测无期限；来源越级生产；自动合并关键变更；合同漂移 |

## S3PA：30 个真实自然日运行与日周月证据

**Pursuing Goal：** 证明系统不仅能通过重放，还能在真实时间中持续产生稳定、高质量、可复习和可行动的情报。

**Entry Gate：** INTEGRATED_PRODUCTION_ACCEPTED。

**Stop Gate：** `THIRTY_DAY_OPERATION_EVIDENCED`

**Stop Conditions：** LIVE-FAIL；EMAIL-DUP；STATE-COUNT-FAIL；周/月报告缺失

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S3PAT01` | — | `planned` | 24h | **30 日每日 3+1 真实运行**：完成 30 个自然日、120 封日邮件和每日账本。 | Stage 2 生产验收通过。 | 120 封邮件均有唯一 Run、哈希和状态。 | LIVE-FAIL；EMAIL-DUP | `ACC-S3PAT01-30D-LIVE` |
| `S3PAT02` | — | `planned` | 12h | **4 份每周总结**：生成并发送至少 4 份周报。 | S3PAT01 运行中。 | 周报覆盖认知、复习、行动、风险和下周重点。 | 周报缺失 | `ACC-S3PAT02-WEEKLY-LIVE` |
| `S3PAT03` | — | `planned` | 16h | **1 份完整月度总结**：生成月度认知差分、能力资产和经济转化报告。 | 完成一个自然月或等价完整周期。 | 月报证据可追溯且 Owner 可读。 | 月报缺失；ROI-TRACE-FAIL | `ACC-S3PAT03-MONTHLY-LIVE` |
| `S3PAT04` | — | `planned` | 16h | **队列、复习、行动、ROI 总账对账**：核对所有状态、数量和转化记录。 | S3PAT01–T03 有数据。 | 分项与总数守恒，孤儿记录为 0。 | STATE-COUNT-FAIL | `ACC-S3PAT04-RECONCILIATION` |

## S3PB：个人成长、内容质量与 ROI 校准

**Pursuing Goal：** 用真实反馈和行动结果校准内容、复习、个人价值和经济转化模型。

**Entry Gate：** S3PA 通过。

**Stop Gate：** `PERSONAL_GROWTH_MODEL_CALIBRATED`

**Stop Conditions：** 无真实反馈却改模型；自动修改冻结参数；未来信息泄漏

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S3PBT01` | — | `planned` | 16h | **人工质量评分与失败样本复盘**：抽样评估深度、清晰、相关、行动和反证。 | S3PA 通过。 | 低分样本有根因和修复任务。 | 样本选择偏差 | `ACC-S3PBT01-HUMAN-QA` |
| `S3PBT02` | — | `planned` | 20h | **预计 ROI 与实际转化偏差校准**：比较时间、成本、收益、机会和能力资产。 | 实际转化账本有数据。 | 偏差可解释，无法量化时保持 not_calculable。 | ROI-TRACE-FAIL；虚假精确收益 | `ACC-S3PBT02-ROI-CAL` |
| `S3PBT03` | — | `planned` | 16h | **复习间隔与掌握率校准**：根据忘记/模糊/掌握/应用反馈调整间隔。 | 至少两轮复习数据。 | 调整有对照和回滚，不自动污染历史。 | REVIEW-FAIL | `ACC-S3PBT03-REVIEW-CAL` |
| `S3PBT04` | — | `planned` | 16h | **权重和阈值 A/B 影响预览**：生成 30 日离线影响预览，Owner 决定是否应用。 | S3PBT01–T03 通过。 | 不自动合并、不自动改收件人/来源/冻结参数。 | 未来信息泄漏；自动改冻结参数 | `ACC-S3PBT04-AB` |

## S3PC：预测账本、来源治理与持续认知复利

**Pursuing Goal：** 建立可证伪预测、来源准入/淘汰和持续改善机制，使系统长期提高而不漂移。

**Entry Gate：** S3PB 通过。

**Stop Gate：** `COGNITIVE_COMPOUNDING_ACCEPTED`

**Stop Conditions：** 预测无期限；来源越级生产；自动合并关键变更；合同漂移

| Task ID | Legacy Alias | 状态 | 工时 | 任务 / 主要交付 | Entry Gate | Stop Gate | Stop Conditions | Acceptance |
|---|---|---|---:|---|---|---|---|---|
| `S3PCT01` | — | `planned` | 12h | **预测账本与准确率复盘**：为高价值信号记录期限、预期证据和推翻条件。 | S2PHT04 已实现预测问题。 | 到期预测自动进入复盘且保留错误记录。 | 预测无期限；改写历史预测 | `ACC-S3PCT01-PREDICTIONS` |
| `S3PCT02` | — | `planned` | 16h | **来源准入、降级、淘汰与恢复制度**：以质量、健康、价值和成本管理来源生命周期。 | 真实来源健康数据可用。 | 新增来源不越级，淘汰有证据和回滚。 | 来源越级生产 | `ACC-S3PCT02-SOURCE-GOV` |
| `S3PCT03` | — | `planned` | 8h | **月度 Owner 决策评审与合同版本治理**：审查需求、参数、板块、邮件和新增能力。 | S3PCT01–T02 通过。 | 每次重大改变产生决策事件和新合同哈希。 | CONTRACT-HASH-MISMATCH | `ACC-S3PCT03-OWNER-REVIEW` |
| `S3PCT04` | — | `planned` | 8h | **持续运行最终验收**：确认系统达到长期认知、能力、行动和经济转化目标。 | S3PA–S3PC 证据完整。 | COGNITIVE_COMPOUNDING_ACCEPTED → CONTINUOUS_OPERATION。 | 任何核心证据缺失 | `ACC-S3PCT04-COMPOUNDING` |

# 3. 当前并行执行顺序

```text
治理/产品线程：S2PAT01 → S2PAT02 → S2PAT03 → S2PAT04
来源线程：      S2PBT01（legacy S2P1T01）继续限定范围实现
合并约束：      S2PBT01 可以开发和测试，但来源晋升/生产 Gate 必须等待 S2PAT02
随后并行：      D1/D2/D3/D4 来源开发 + S2PG/S2PH/S2PI/S2PJ 公共能力开发
集成顺序：      S2PG → S2PH/S2PI/S2PJ → S2PK → S2PL → S3
```

# 4. V6 到 V7 的关键映射

| V6 概念 | V7 处理 |
|---|---|
| B1 研究来源板块 | 拆分为数据源域 D1；内容按 B1/B2/B4/B5/B6 多标签阅读 |
| B2 顶刊板块 | 数据源域 D2，并扩展工程开源与权威技术报告 |
| B3 中国政策板块 | 数据源域 D3，主要支撑 B3，同时可进入 B2/B4/B5/B6 |
| B4 美国官方板块 | 数据源域 D4，主要支撑 B3/B2，并可进入 B1/B4/B5/B6 |
| B5 跨板块报告 | 改为 M4 跨板块邮件；横切分析拆为 B4/B5/B6 |
| 五封邮件 | 改为 M1/M2/M3/M4，每日 3+1 |
| S2P1T01 | canonical alias：S2PBT01，历史 ID 保留 |
| V6 S2P7 最终验收 | 迁移至 V7 S2PL，历史规划记录不覆盖 |

# 5. 最终验收总标准

1. 四数据源域均通过来源级门禁，未晋升来源有明确降级状态。
2. 三主板块和三横切副板块映射可解释，来源域不再等于阅读板块。
3. 每日 3+1 邮件错峰生成，M4 等待 M1–M3 明确终态，重复邮件为 0。
4. 10 项金标内容通过深度、证据、反证、个人价值和行动性人工验收。
5. 用户中心、一改四查三基和 CodexProject 全局中文门通过。
6. 总控台显示真实排队、已讲解、已发送、复习到期、行动和转化数量，分项总数守恒。
7. 每周和每月报告可追溯；预计 ROI 与实际 ROI 明确区分。
8. 全系统 30 日重放、2 日真实运行、恢复/回滚演练和 P0/P1=0。
