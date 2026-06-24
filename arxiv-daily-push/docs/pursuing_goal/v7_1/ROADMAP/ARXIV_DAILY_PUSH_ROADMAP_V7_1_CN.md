# arXiv Daily Push Roadmap V7.1（中文完整执行版）

> 本 Roadmap 的最终生产验收已从 S2PL 移至 S2PMT07；S2PL 只形成集成候选。

## 全局 Gate

- Stage2 来源 Shadow 开发可并行继续。
- P0/P1 未清零时禁止真实 SMTP、真实恢复、自动调度安装和 DAILY_OPERATION。
- 唯一最终 Gate：`S2PMT07 → INTEGRATED_PRODUCTION_ACCEPTED → DAILY_OPERATION`。

# S1｜arXiv 单源纵向切片与生产基线

**状态：** `completed`  
**Pursuing Goal：** 证明多源智能系统的最小纵向切片：采集、证据、评分、报告、邮件和运行可形成可审计闭环。  
**Entry Gate：** V5 Stage 1 基线可读。  
**Stop Gate：** `ARXIV_PRODUCTION_ACCEPTED`  
**Stop Conditions：** R-CONFLICT；DATA-LOSS；EVIDENCE-FAIL；REPLAY-FAIL；LIVE-FAIL

## S1PA｜基线审计、治理校准与防漂移

**状态：** `completed`  
**Pursuing Goal：** 建立可追溯的 arXiv 单源项目事实图，并冻结 Stage 1 的唯一执行基线。  
**Entry Gate：** 仓库、V5 基线和现有治理文件可读。  
**Stop Gate：** `S1_BASELINE_LOCKED`  
**Stop Conditions：** R-CONFLICT；G-DRIFT；TRACE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S1PAT01` 最小范围只读审计 | `completed` | 建立代码、配置、治理、工作流、测试和数据流事实图。 | 无 | 审计清单、现状图、风险清单和真实路径齐全。 | `ACC-S1PAT01-AUDIT` |
| `S1PAT02` 治理事实源校准 | `completed` | 统一版本、状态、计划和项目注册事实。 | 无 | 版本、状态、计划、任务和模型一致。 | `ACC-S1PAT02-GOV` |
| `S1PAT03` 需求追踪与防漂移门禁 | `completed` | 建立 Requirement→Feature→Task→Config→Function→Test→Artifact→Evidence 追踪。 | 无 | 追踪覆盖完整并阻止范围回归。 | `ACC-S1PAT03-TRACE` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S1PB｜人工控制面与数据基础

**状态：** `completed`  
**Pursuing Goal：** 建立唯一控制配置、四个人类查看面和可回滚的数据存储基础。  
**Entry Gate：** S1PA 通过。  
**Stop Gate：** `S1_CONTROL_AND_DATA_READY`  
**Stop Conditions：** ACCEPTANCE-FAIL；DATA-LOSS；G-DRIFT

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S1PBT01` owner controls 与 Schema | `completed` | 建立唯一人工控制配置及校验。 | 无 | 权重、队列和板块配置可校验。 | `ACC-S1PBT01-CONFIG` |
| `S1PBT02` 四个人类查看文件生成器 | `completed` | 生成运行、来源、模型队列和内容账本视图。 | 无 | 视图由事实源生成且无漂移。 | `ACC-S1PBT02-HUMAN-VIEWS` |
| `S1PBT03` SQLite WAL + FTS5 统一模型与迁移 | `completed` | 实现文档、事件、Claim、队列、报告和邮件数据模型。 | 无 | 迁移可前进/回滚，事务和幂等通过。 | `ACC-S1PBT03-DATA` |
| `S1PBT04` 原始证据、哈希、备份恢复与旧数据 fixture | `completed` | 实现 RawRecord、内容哈希和恢复验证。 | 无 | 恢复后哈希一致且 fixture 无重复。 | `ACC-S1PBT04-RECOVERY` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S1PC｜arXiv 单源纵向切片核心

**状态：** `completed`  
**Pursuing Goal：** 证明 arXiv 从采集、规范化、证据、评分到队列的全链可重复、可解释、可审计。  
**Entry Gate：** S1PB 通过。  
**Stop Gate：** `S1_ARXIV_CORE_READY`  
**Stop Conditions：** SRC-POLICY；DET-FAIL；EVIDENCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S1PCT01` Source Registry 与 Connector Contract | `completed` | 定义来源 ID、限流、缓存、健康和许可字段。 | 无 | arXiv 可通过通用接口运行。 | `ACC-S1PCT01-SOURCE-CONTRACT` |
| `S1PCT02` arXiv Adapter 与小样本 fixture | `completed` | 实现官方入口优先与可测试回退。 | 无 | fixture 和小样本在线测试通过。 | `ACC-S1PCT02-ARXIV` |
| `S1PCT03` 规范化、去重、版本、事件与 Taxonomy | `completed` | 映射 CanonicalDocument/Version/Event。 | 无 | Canonical 重复为 0，版本和时间正确。 | `ACC-S1PCT03-CANONICAL` |
| `S1PCT04` 研究评分卡、贡献明细与队列 | `completed` | 实现可解释排序、排队和淘汰原因。 | 无 | 同输入同配置同顺序。 | `ACC-S1PCT04-RANKING` |
| `S1PCT05` EvidencePacket、两遍分析与 Claim Ledger | `completed` | 建立证据包、版本差分、反证和 Claim/Evidence 绑定。 | 无 | 关键 Claim 证据绑定 100%。 | `ACC-S1PCT05-EVIDENCE` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S1PD｜文本交付、邮件合同与本地运行

**状态：** `completed`  
**Pursuing Goal：** 形成高密度中文报告、邮件幂等和可恢复本地运行纵向切片。  
**Entry Gate：** S1PC 通过。  
**Stop Gate：** `S1_TEXT_DELIVERY_READY`  
**Stop Conditions：** CONTENT-QUALITY-FAIL；EMAIL-DUP；OPS-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S1PDT01` B1 高密度文本报告合同 | `completed` | 生成 Markdown/HTML/JSON 报告。 | 无 | 报告结构、引用和不确定性审计通过。 | `ACC-S1PDT01-REPORT` |
| `S1PDT02` 邮件预览、幂等和发送状态合同 | `completed` | 实现预览、哈希、重试和防重复。 | 无 | 同一 Run 不重复发送。 | `ACC-S1PDT02-EMAIL` |
| `S1PDT03` 本地调度、Watchdog、备份与迁移包 | `completed` | 实现锁、heartbeat、补跑、恢复和迁移 Runbook。 | 无 | 恢复和安装/卸载模拟通过。 | `ACC-S1PDT03-RUNTIME` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S1PE｜真实重放、运行证据与 Stage 1 验收

**状态：** `completed`  
**Pursuing Goal：** 以真实 arXiv 数据证明单源系统可达到生产验收基线。  
**Entry Gate：** S1PD 通过。  
**Stop Gate：** `ARXIV_PRODUCTION_ACCEPTED`  
**Stop Conditions：** REPLAY-FAIL；LIVE-FAIL；OPS-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S1PET01` 目标运行机 bootstrap 与预检 | `completed` | 验证 CPU、RAM、磁盘、网络、SMTP 和调度。 | 无 | 运行机预检有证据。 | `ACC-S1PET01-PREFLIGHT` |
| `S1PET02` 真实 arXiv 单日全链预检 | `completed` | 完成真实抓取到报告/邮件预览。 | 无 | 一次完整真实 Run 成功。 | `ACC-S1PET02-LIVE-CHAIN` |
| `S1PET03` 30 个独立历史日重放与账本闭环 | `completed` | 生成 30 个真实 as-of 日的报告和账本。 | 无 | 30/30 终态、未来泄漏 0、P0/P1=0。 | `ACC-S1PET03-REPLAY` |
| `S1PET04` 连续真实运行与 Stage 1 验收 | `completed` | 验证调度、恢复和受控邮件证据。 | 无 | ARXIV_PRODUCTION_ACCEPTED。 | `ACC-S1PET04-STAGE1` |
| `S1PET05` 本机生产运行与迁移准备 | `completed` | 完成 local runner、持久化和迁移准备。 | 无 | 本地运行准备完成，云端生产调度关闭。 | `ACC-S1PET05-LOCAL` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

# S2｜多源、深度理解、个人成长与 3+1 邮件融合开发

**状态：** `in_progress`  
**Pursuing Goal：** 将四个数据源域、三个主阅读板块、三个横切副板块、深度理解、中文人类界面、复习、行动、ROI、周/月报告和每日 3+1 邮件融合为同一生产系统。  
**Entry Gate：** ARXIV_PRODUCTION_ACCEPTED；当前 S2P1T01 可继续，但所有生产晋升必须读取 V7 合同。  
**Stop Gate：** `INTEGRATED_PRODUCTION_ACCEPTED → DAILY_OPERATION`  
**Stop Conditions：** R-CONFLICT；CONTRACT-HASH-MISMATCH；SRC-POLICY；EVIDENCE-FAIL；CONTENT-QUALITY-FAIL；LANGUAGE-UX-FAIL；STATE-COUNT-FAIL；EMAIL-DUP；REPLAY-FAIL；LIVE-FAIL；ACCEPTANCE-FAIL；SEC-TRUST-FAIL；ATOMICITY-FAIL；OUTBOX-FAIL；LOCK-LEASE-FAIL；SCHEDULER-FAIL；STRESS-FAIL；UI-FLOW-FAIL；HANDOFF-FAIL

## S2PA｜V7 产品契约、中文可读治理与任务兼容

**状态：** `in_progress`  
**Pursuing Goal：** 把本次 Owner 决策固化为唯一、中文、人类可读且机器可校验的 V7 基线，使所有 Stage 2 线程读取同一合同。  
**Entry Gate：** Stage 1 已验收；仓库当前 V5/V6 基线和三基文件可读。  
**Stop Gate：** `V7_PRODUCT_CONTRACT_LOCKED`  
**Stop Conditions：** R-CONFLICT；G-DRIFT；TRACE-FAIL；CONTRACT-HASH-MISMATCH

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PAT01` 只读冲突审计与 V6→V7 迁移矩阵 | `ready` | 核对 V5/V6、当前代码配置、三基文件和本任务包，列出冲突、旧名与迁移顺序。 | 无 | 冲突矩阵完整；未决冲突均有单一 Owner 决策入口。 | `ACC-S2PAT01-V7-AUDIT` |
| `S2PAT02` 锁定 V7 产品契约与关键决策记录 | `planned` | 建立 product_contract、decision_log、requirements 和基线锁，并记录 4 源/3 主/3 副/3+1 邮件。 | S2PAT01 | 所有关键 Owner 要求有稳定 ID、状态、来源和验收标准。 | `ACC-S2PAT02-CONTRACT` |
| `S2PAT03` 任务 ID 兼容、Roadmap V7 与 AGENTS/README 同步 | `planned` | 采用字母 Phase 规范并保留 V6 数字 ID alias；更新当前任务映射和唯一基线入口。 | S2PAT02 | 当前 S2P1T01 映射为 S2PBT01；历史事件不改写。 | `ACC-S2PAT03-ROADMAP` |
| `S2PAT04` 中文人类视图、合同哈希与 CI 防漂移门 | `planned` | 使三基文件、用户中心、PR/CI 摘要显示合同版本与哈希并中文优先。 | S2PAT03 | 英文-only 人类界面和合同哈希漂移能被 CI 阻断。 | `ACC-S2PAT04-CN-CI` |
| `S2PAT05` V7.1 并行审查落库、Stop Code 与追踪门修复 | `ready` | 把三轨发现、严重度/合并政策、显式依赖、可执行验证器和连续交接合同写入仓库。 | S2PAT02 | V7_1_AUDIT_CONTRACT_LOCKED | `ACC-S2PAT05-AUDIT-LOCK` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PB｜D1 研究、预印本与医学索引数据源域

**状态：** `in_progress`  
**Pursuing Goal：** 在不回归 arXiv 的前提下，逐源晋升研究/预印本/索引增强来源，并统一输出 EvidencePacket。  
**Entry Gate：** ARXIV_PRODUCTION_ACCEPTED；S2PAT02 的产品契约至少可读。  
**Stop Gate：** `D1_SOURCE_DOMAIN_ACCEPTED`  
**Stop Conditions：** SRC-POLICY；DET-FAIL；SCHEMA-BREAK；BOARD-MAP-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PBT01` bioRxiv 与 medRxiv 晋升 | `in_progress` | 接入生命科学和医学预印本，验证第二类来源及 D1→B1/B2/B4/B5/B6 路由。 | S2PAT02 | 各自 fixture、30 日终态、48h Shadow、身份/版本/许可门通过。 | `ACC-S2PBT01-BIORXIV-MEDRXIV` |
| `S2PBT02` PubMed 与 Europe PMC 增强源 | `planned` | 实现 PMID/DOI 对齐、开放全文和资助关系，不重复创建原始论文。 | S2PBT01 | 增强关系、许可和全文级别正确。 | `ACC-S2PBT02-PUBMED-EPMC` |
| `S2PBT03` TechRxiv、ChemRxiv、EarthArXiv 晋升 | `planned` | 扩展工程、化学、材料和地球环境预印本。 | S2PBT01 | 三个来源均可独立降级和回滚。 | `ACC-S2PBT03-PREPRINTS` |
| `S2PBT04` SSRN 与 ChinaXiv 高风险来源 | `planned` | 处理条款、低频网页、中文元数据和页面漂移。 | S2PBT01 | 条款可审计、中文字段完整、失败显式。 | `ACC-S2PBT04-SSRN-CHINAXIV` |
| `S2PBT05` D1 数据源域全量资格与 Stage 1 回归 | `planned` | 完成 D1 十来源重放、队列、EvidencePacket 和 arXiv 回归。 | S2PBT01, S2PBT02, S2PBT03, S2PBT04 | D1 30 日重放、2 日 Shadow、旧 arXiv 无回归。 | `ACC-S2PBT05-D1` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PC｜D2 权威发表、工程开源与产业技术报告数据源域

**状态：** `planned`  
**Pursuing Goal：** 建立从顶级期刊到工程实现、权威技术报告和产业落地信号的第二数据源域。  
**Entry Gate：** D1 通用来源框架稳定。  
**Stop Gate：** `D2_SOURCE_DOMAIN_ACCEPTED`  
**Stop Conditions：** SRC-POLICY；EVIDENCE-FAIL；ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PCT01` Nature 主刊晋升 | `planned` | 接入官方发现入口、文章类型、更正和 DOI。 | S2PAT02 | 来源级 replay/Shadow、许可和事件通过。 | `ACC-S2PCT01-NATURE` |
| `S2PCT02` Science 主刊晋升 | `planned` | 识别 Research/Report/Review/Perspective 等类型。 | S2PAT02 | 来源级门禁通过且不影响 D1。 | `ACC-S2PCT02-SCIENCE` |
| `S2PCT03` The Lancet 主刊晋升 | `planned` | 接入 Online First、PubMed 关系和医学文章类型。 | S2PAT02 | 索引对齐、许可和类型门通过。 | `ACC-S2PCT03-LANCET` |
| `S2PCT04` 顶刊 Profile、发表关系、更正撤回 | `planned` | 差异化建模研究、综述、社论、新闻、更正和撤回。 | S2PCT01, S2PCT02, S2PCT03 | 撤回/更正强制事件能更新旧结论。 | `ACC-S2PCT04-JOURNAL-PROFILE` |
| `S2PCT05` 工程开源、代码、基准和标准公开信号框架 | `planned` | 接入论文关联代码、官方发布、模型卡、基准和标准信号，形成 B2 工程证据。 | S2PAT02 | 官方性、版本、仓库/论文关系和复现状态可追溯。 | `ACC-S2PCT05-ENGINEERING-SIGNALS` |
| `S2PCT06` 权威研究机构与产业技术报告框架 | `planned` | 接入公开、可审计的研究机构、实验室和企业技术报告/产品技术说明。 | S2PAT02 | 报告类型、发布主体、利益关系和证据级别明确。 | `ACC-S2PCT06-REPORTS` |
| `S2PCT07` D2 数据源域资格与跨类型校准 | `planned` | 完成顶刊、工程、报告来源的 30 日重放和类型差异评分。 | S2PCT01, S2PCT02, S2PCT03, S2PCT04, S2PCT05, S2PCT06 | D2 30 日重放、2 日 Shadow、强制事件和队列解释通过。 | `ACC-S2PCT07-D2` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PD｜D3 中国官方核心数据源域

**状态：** `planned`  
**Pursuing Goal：** 建立全国和中央官方政策、法律、产业、科技与经济信号的权威主干。  
**Entry Gate：** 通用政府来源连接器可用。  
**Stop Gate：** `D3_CORE_SOURCE_DOMAIN_ACCEPTED`  
**Stop Conditions：** SRC-POLICY；ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PDT01` 中国 C0 全国权威主干 | `planned` | 接入法律法规、人大、国务院、公报和两高。 | S2PAT02 | 机关、文号、附件和日期可追溯。 | `ACC-S2PDT01-C0` |
| `S2PDT02` 中国 C1 中央机关与重点部门 | `planned` | 覆盖宏观、科技、产业、金融、市场和重点行业部门。 | S2PAT02 | 机构模板、别名、行业映射和官方域名完整。 | `ACC-S2PDT02-C1` |
| `S2PDT03` 法律元数据、版本效力与转载关系 | `planned` | 实现草案/正式、修订/废止、实施/解释关系。 | S2PDT01, S2PDT02 | 法律状态变化能触发重评分和旧结论更新。 | `ACC-S2PDT03-LEGAL` |
| `S2PDT04` D3 核心资格与阅读板块路由 | `planned` | 完成 C0/C1 重放并路由到 B2/B3/B4/B5/B6。 | S2PDT01, S2PDT02, S2PDT03 | 30 日重放、2 日 Shadow、权威性和路由解释通过。 | `ACC-S2PDT04-D3-CORE` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PE｜D4 美国官方科技金融数据源域

**状态：** `planned`  
**Pursuing Goal：** 建立美国科技创新、法律、金融、宏观和技术政策官方信号域。  
**Entry Gate：** 官方来源、实体和关系框架稳定。  
**Stop Gate：** `D4_SOURCE_DOMAIN_ACCEPTED`  
**Stop Conditions：** SRC-POLICY；ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PET01` US-TA 科技创新与突破 | `planned` | 接入 NSF、DARPA、DOE、NIH、NASA、NIST、USPTO、FDA 等。 | S2PAT02 | 资助、专利、临床、标准关系可审计。 | `ACC-S2PET01-US-TA` |
| `S2PET02` US-LG 跨机构法律主干 | `planned` | 接入 Federal Register、Regulations.gov、GovInfo、Congress 等。 | S2PAT02 | Docket、FR、法案和认证文本关系正确。 | `ACC-S2PET02-US-LG` |
| `S2PET03` US-FM 金融、市场与宏观 | `planned` | 接入 SEC、Fed、Treasury、CFTC、OCC、FDIC、CFPB 等。 | S2PAT02 | 表单、CIK、Accession、基金/公司/资产关系通过。 | `ACC-S2PET03-US-FM` |
| `S2PET04` US-TP 技术政策与 D4 资格 | `planned` | 接入 OSTP、BIS、FTC、FCC、CISA、CHIPS 等并完成 D4。 | S2PET01, S2PET02, S2PET03 | D4 30 日重放、2 日 Shadow、板块路由和预算解释通过。 | `ACC-S2PET04-D4` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PF｜D3 中国地方与特殊区域全覆盖

**状态：** `planned`  
**Pursuing Goal：** 在不淹没中央权威信号的前提下，扩展省级、港澳、重点城市和特殊功能区。  
**Entry Gate：** D3 核心稳定。  
**Stop Gate：** `D3_FULL_SOURCE_DOMAIN_ACCEPTED`  
**Stop Conditions：** ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PFT01` 全部省级模板与核心覆盖 | `planned` | 覆盖全部省级行政区域核心部门。 | S2PDT04 | 省级清单和健康分层完整。 | `ACC-S2PFT01-PROVINCES` |
| `S2PFT02` 香港与澳门独立 Profile | `planned` | 按独立法律和政府结构建模。 | S2PDT04 | 司法辖区、语言和法律状态独立正确。 | `ACC-S2PFT02-HK-MO` |
| `S2PFT03` 首批重点城市覆盖 | `planned` | 按部门模板覆盖重点城市并支持别名。 | S2PDT04 | 城市覆盖矩阵、区域权重和健康状态通过。 | `ACC-S2PFT03-CITIES` |
| `S2PFT04` 特殊功能区与垂直机构自动发现 | `planned` | 发现自贸区、高新区、海关、税务、金融监管等。 | S2PDT04 | 官方性验证、去重、父子关系和复审面通过。 | `ACC-S2PFT04-ZONES` |
| `S2PFT05` D3 全覆盖资格与地方来源治理 | `planned` | 完成 C0–C4 配额、健康、淘汰和回退机制。 | S2PFT01, S2PFT02, S2PFT03, S2PFT04 | D3 全量重放、来源平衡和淘汰解释通过。 | `ACC-S2PFT05-D3-FULL` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PG｜统一证据骨干、知识图谱与 4 源→3 主/3 副路由

**状态：** `planned`  
**Pursuing Goal：** 把来源、阅读板块和邮件产品彻底解耦，形成全系统共用的证据、关系、路由和排序骨干。  
**Entry Gate：** D1–D4 至少各有一个稳定来源；V7 契约已锁定。  
**Stop Gate：** `UNIFIED_INTELLIGENCE_BACKBONE_READY`  
**Stop Conditions：** SCHEMA-BREAK；EVIDENCE-FAIL；BOARD-MAP-FAIL；DET-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PGT01` EvidencePacket V2 与证据级别 | `planned` | 统一元数据级、摘要级、全文级、跨源核验级证据字段。 | S2PBT01, S2PAT02 | 所有连接器可输出同一版本 EvidencePacket，旧 arXiv 兼容。 | `ACC-S2PGT01-EVIDENCE-V2` |
| `S2PGT02` 跨源身份解析与知识图谱 | `planned` | 整合 DOI/PMID/arXiv/文号/FR/CIK 等关系。 | S2PGT01 | 重复 Canonical 0，关系有证据且更新幂等。 | `ACC-S2PGT02-KG` |
| `S2PGT03` D1–D4 到 B1–B6 多标签路由 | `planned` | 实现 3 主板块和 3 横切副板块的多对多解释路由。 | S2PGT01 | 每条重要内容有来源域、主板块、横切板块和原因码。 | `ACC-S2PGT03-ROUTING` |
| `S2PGT04` 跨源支持、反驳、前沿变化量与信号共振 | `planned` | 识别支持/反驳/版本差分和多类信号共振。 | S2PGT02, S2PGT03 | 关系、前沿 Delta 和共振结论可追溯。 | `ACC-S2PGT04-DELTA-RESONANCE` |
| `S2PGT05` 跨板块校准、组合排序与可解释队列 | `planned` | 建立分位数校准、来源平衡、等待信用和队列原因。 | S2PGT04 | 同输入同配置同顺序，队列和淘汰原因可读。 | `ACC-S2PGT05-CALIBRATION` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PH｜Stage 1+ 深度理解、个人情报与内容质量

**状态：** `planned`  
**Pursuing Goal：** 让 arXiv 和所有 Stage 2 来源都达到“像直接向 ChatGPT 深问一样”的深度，同时保留证据、不确定性和个人价值。  
**Entry Gate：** S2PGT01 可用；Stage 1 报告链可回归测试。  
**Stop Gate：** `DEEP_INTELLIGENCE_QUALITY_ACCEPTED`  
**Stop Conditions：** CONTENT-QUALITY-FAIL；EVIDENCE-FAIL；ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PHT01` 10 项差异化金标集与人工评分规程 | `planned` | 选择跨学科、不同证据级别的 10 项内容作为质量基准。 | S2PAT02 | 深度、清晰、相关、行动和反证五维评分规程锁定。 | `ACC-S2PHT01-GOLD-SET` |
| `S2PHT02` 摘要/全文/图表分层深度分析流水线 | `planned` | 回答问题、旧方法、新方法、机制、实验、结果、限制和适用条件。 | S2PHT01, S2PGT01 | 摘要级不冒充全文级；关键事实证据绑定 100%。 | `ACC-S2PHT02-DEEP-ANALYSIS` |
| `S2PHT03` 个人画像、项目、能力与目标映射 | `planned` | 将内容映射到用户项目、能力、时间、学习和经济路径。 | S2PHT01 | 个人影响有字段、理由、置信度和时间尺度。 | `ACC-S2PHT03-PERSONAL` |
| `S2PHT04` 时代影响、反炒作、失败条件与预测问题 | `planned` | 加入社会/时代影响、最强反对意见和可证伪预测。 | S2PHT02, S2PHT03 | 每项主讲包含最强反对意见和推翻条件。 | `ACC-S2PHT04-ANTI-HYPE` |
| `S2PHT05` 内容质量门与 Stage 1 arXiv 回灌 | `planned` | 将新分析合同应用到 arXiv 和所有来源，建立自动+人工质量门。 | S2PHT01, S2PHT02, S2PHT03, S2PHT04 | 10 项金标均达标，旧采集/证据/邮件链无回归。 | `ACC-S2PHT05-CONTENT-GATE` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PI｜中文用户中心、一改四查三基与真实状态可视化

**状态：** `planned`  
**Pursuing Goal：** 让用户无需进入 config/docs/governance 即可控制、检查和验收系统，且看到真实数量而非仅容量。  
**Entry Gate：** S2PAT04 中文规则可用；现有 owner_controls 和数据库可读。  
**Stop Gate：** `OWNER_EXPERIENCE_ACCEPTED`  
**Stop Conditions：** LANGUAGE-UX-FAIL；STATE-COUNT-FAIL；G-DRIFT；ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PIT01` 00_用户中心与“一改”控制入口 | `planned` | 建立一个编辑目录，分离画像、邮件复习、来源板块、预算调度。 | S2PAT04 | 用户常用控制在两次点击内，编译到兼容配置。 | `ACC-S2PIT01-USER-CENTER` |
| `S2PIT02` 运行任务与真实队列总控台 | `planned` | 显示实际排队、已讲解、已报告、已发送、失败和最老等待时间。 | S2PIT01 | 分项总数守恒，显示 generated_at/data_as_of 和过期警告。 | `ACC-S2PIT02-RUNTIME-DASHBOARD` |
| `S2PIT03` 数据源、阅读板块、模型参数与全量队列视图 | `planned` | 显示 D1–D4、B1–B6 健康、所有参数、来源和影响。 | S2PIT01 | 参数、代码、测试、默认值、范围和回滚值可读。 | `ACC-S2PIT03-SOURCE-MODEL` |
| `S2PIT04` 内容、邮件、复习、行动与 ROI 总账 | `planned` | 统一展示内容生命周期、邮件、复习、行动、能力资产和转化。 | S2PIT02, S2PIT03 | 每条记录可追溯到内容、证据、Run、邮件和反馈。 | `ACC-S2PIT04-LEDGER` |
| `S2PIT05` 三基文件全量中文渲染与 CodexProject 全局中文门 | `planned` | 更新功能清单、开发记录、模型参数文件，并将中文优先扩展到根 README、PR/CI 和所有项目人类界面。 | S2PIT01, S2PIT02, S2PIT03, S2PIT04 | 三基文件非跳转页，完整包含需求、Roadmap、参数、状态和验收。 | `ACC-S2PIT05-THREE-BASE` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PJ｜复习、行动、能力资产、ROI 与周/月复利闭环

**状态：** `planned`  
**Pursuing Goal：** 把“阅读完成”扩展为可复习、可行动、可形成资产、可记录经济转化的长期成长闭环。  
**Entry Gate：** S2PHT 深度内容结构和 S2PIT 状态面可用。  
**Stop Gate：** `COGNITIVE_GROWTH_LOOP_READY`  
**Stop Conditions：** REVIEW-FAIL；ROI-TRACE-FAIL；STATE-COUNT-FAIL；ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PJT01` 内容学习生命周期与数据库迁移 | `planned` | 建立 REVIEW_DUE、ACTION、ASSET、CONVERSION、MASTERED 等状态。 | S2PHT02, S2PIT01 | 迁移可回滚，状态历史追加且守恒。 | `ACC-S2PJT01-LIFECYCLE` |
| `S2PJT02` 可配置复习调度与到期队列 | `planned` | 实现默认 1/3/7/14/30/90 天复习，并按反馈调整。 | S2PJT01 | 今日到期、7 日到期、逾期和已完成数量正确。 | `ACC-S2PJT02-REVIEW` |
| `S2PJT03` 行动、能力资产与预计/实际 ROI 账本 | `planned` | 记录 15 分钟/2 小时/7 天/30 天行动及实际收益。 | S2PJT01 | 预计值有假设和置信度；实际 ROI 仅在可核验成本/收益时计算。 | `ACC-S2PJT03-ROI` |
| `S2PJT04` 每周总结与注意力再分配 | `planned` | 生成周度主线、反证、复习、行动、资产和下周重点。 | S2PJT02, S2PJT03 | 周报可追溯到本周内容与实际状态。 | `ACC-S2PJT04-WEEKLY` |
| `S2PJT05` 每月认知差分、能力增长与经济转化总结 | `planned` | 生成月度时代主线、观点变化、能力资产、实际 ROI 和预测复盘。 | S2PJT04 | 月报包含月初/月底认知差分和可核验转化。 | `ACC-S2PJT05-MONTHLY` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PK｜每日 3＋1 邮件、错峰生成与正向 UI/UX

**状态：** `planned`  
**Pursuing Goal：** 稳定生成三封主板块邮件和一封跨板块汇总邮件，兼顾信息效率、深度、反馈、ROI 和防重复。  
**Entry Gate：** S2PG–S2PJ 的必要接口可用。  
**Stop Gate：** `FOUR_EMAIL_SYSTEM_READY`  
**Stop Conditions：** EMAIL-DUP；EMAIL-WATERLINE-FAIL；CONTENT-QUALITY-FAIL；ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PKT01` 统一邮件内容合同、状态与反馈组件 | `planned` | 定义三层阅读、证据标签、反馈按钮、哈希和状态。 | S2PHT05, S2PIT04, S2PJT03 | 四封邮件共享契约但保持板块差异。 | `ACC-S2PKT01-MAIL-CONTRACT` |
| `S2PKT02` M1 科学与理论前沿邮件 | `planned` | 生成 B1 主邮件并挂载 B4/B5/B6。 | S2PKT01 | 科学机制、证据、反证、个人价值和行动齐全。 | `ACC-S2PKT02-M1` |
| `S2PKT03` M2 工程、产品与产业前沿邮件 | `planned` | 生成合并后的 B2 主邮件并挂载 B4/B5/B6。 | S2PKT01 | 工程可用性、复现、产品/产业价值和限制齐全。 | `ACC-S2PKT03-M2` |
| `S2PKT04` M3 政策、资本与地缘前沿邮件 | `planned` | 生成 B3 主邮件并挂载 B4/B5/B6。 | S2PKT01 | 法律状态、资本影响、地缘背景和个人影响齐全。 | `ACC-S2PKT04-M3` |
| `S2PKT05` M4 跨板块总览、错峰编排与水位线 | `planned` | 在 M1–M3 明确终态后生成跨源共振、矛盾、时代主线、个人行动组合和复习提醒。 | S2PKT02, S2PKT03, S2PKT04 | 每日 3+1 互不替代、重复 0、无静默消失；默认错峰 07:30/11:30/17:00/21:30。 | `ACC-S2PKT05-M4` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PL｜全系统重放、真实运行与集成候选验收

**状态：** `planned`  
**Pursuing Goal：** 形成可供安全/并发/生命周期最终硬化的完整集成候选，不在 P0/P1 清零前宣称生产验收。  
**Entry Gate：** S2PA–S2PK 全部门禁通过或有 Owner 批准的显式降级。  
**Stop Gate：** `S2_INTEGRATION_CANDIDATE_READY`  
**Stop Conditions：** REPLAY-FAIL；LIVE-FAIL；OPS-FAIL；STATE-COUNT-FAIL；ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PLT01` 全系统 30 个独立历史日重放 | `planned` | 运行 4 源→6 板块→每日 4 邮件全流程，生成 120 份报告/预览及完整账本。 | S2PBT05, S2PCT07, S2PDT04, S2PET04, S2PFT05, S2PKT05 | 30/30 独立 as-of、未来泄漏 0、全来源终态、P0/P1=0。 | `ACC-S2PLT01-30D` |
| `S2PLT02` 连续 2 个真实自然日与 8 封邮件 | `planned` | 在真实调度、网络和 SMTP 下每天发送 3+1。 | S2PLT01 | 两日 8 封邮件完整、无重复、M4 水位线正确。 | `ACC-S2PLT02-2D` |
| `S2PLT03` 韧性、容量、回滚和状态一致性演练 | `planned` | 验证限流、解析漂移、重启、磁盘、备份、回滚和状态计数。 | S2PLT02 | 故障演练有证据，恢复点可执行，账本总数守恒。 | `ACC-S2PLT03-RESILIENCE` |
| `S2PLT04` 集成候选验收（非生产切换） | `planned` | 汇总重放、真实运行、状态和内容证据，形成 S2_INTEGRATION_CANDIDATE_READY。 | S2PLT03 | S2_INTEGRATION_CANDIDATE_READY | `ACC-S2PLT04-INTEGRATION-CANDIDATE` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S2PM｜安全、并发、自动生命周期、压力与 UI 最终硬化

**状态：** `ready`  
**Pursuing Goal：** 关闭三轨审查的 P0/P1，证明系统在安全、并发、自动运行、故障恢复、压力和人机交互上可持续交接与生产运行。  
**Entry Gate：** S2PAT05 通过；可与来源 Shadow 开发并行。最终 T07 还要求 S2_INTEGRATION_CANDIDATE_READY。  
**Stop Gate：** `INTEGRATED_PRODUCTION_ACCEPTED → DAILY_OPERATION`  
**Stop Conditions：** SEC-TRUST-FAIL；PATH-ESCAPE；ATOMICITY-FAIL；OUTBOX-FAIL；LOCK-LEASE-FAIL；SCHEDULER-FAIL；BACKGROUND-LIFECYCLE-FAIL；STRESS-FAIL；CHAOS-FAIL；CLOCK-TIMEZONE-FAIL；UI-FLOW-FAIL；HANDOFF-FAIL；ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S2PMT01` 安全威胁模型、不可信内容与证据发布边界 | `ready` | 关闭 A-004/A-005/A-012/A-019/A-020，建立来源、模型、工具、URL、依赖和证据边界。 | S2PAT05 | SECURITY_AND_EVIDENCE_BOUNDARY_READY | `ACC-S2PMT01-SECURITY` |
| `S2PMT02` 原子文件发布、备份与安全恢复 | `planned` | 关闭 A-001/A-002/A-010/A-011/A-014，所有持久化和恢复 fail-closed、原子、可验证。 | S2PMT01 | ATOMIC_STORAGE_AND_RECOVERY_READY | `ACC-S2PMT02-ATOMIC-RECOVERY` |
| `S2PMT03` lease/fencing、并发状态、M4 水位线与事务发件箱 | `planned` | 关闭 A-003/A-006～A-009/A-016/A-017、B-003/B-007/B-008/B-011。 | S2PMT02 | CONCURRENT_SIDE_EFFECTS_READY | `ACC-S2PMT03-CONCURRENCY-OUTBOX` |
| `S2PMT04` 自动唤醒、运行、drain、关闭、缓存清理与恢复 | `planned` | 关闭 A-013、B-001～B-005/B-015，形成跨平台可安装且可卸载的完整生命周期。 | S2PMT03 | AUTONOMOUS_LIFECYCLE_READY | `ACC-S2PMT04-LIFECYCLE` |
| `S2PMT05` 负载、压力、浸泡、故障、DST 与全流程有效性测试 | `planned` | 关闭 B-006～B-014/B-016，并验证 3+1、周/月、复习、行动、ROI 全链。 | S2PMT04, S2PLT04 | STRESS_CHAOS_TIME_E2E_READY | `ACC-S2PMT05-STRESS-E2E` |
| `S2PMT06` 中文 UI、交互反馈、导航与安全操作完整性 | `planned` | 关闭 C-001～C-015，保证 Owner 旅程、状态反馈、配置修改、追踪和可访问性。 | S2PIT05, S2PMT03 | OWNER_UX_AND_SAFE_CONTROLS_READY | `ACC-S2PMT06-UX` |
| `S2PMT07` 独立复审、证据封包、连续交接与生产 Gate | `planned` | 由未参与实现的审查者复跑 P0/P1、全量测试、证据与交接门，决定是否进入 DAILY_OPERATION。 | S2PMT01, S2PMT02, S2PMT03, S2PMT04, S2PMT05, S2PMT06, S2PLT04 | INTEGRATED_PRODUCTION_ACCEPTED → DAILY_OPERATION | `ACC-S2PMT07-FINAL-REVIEW` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

# S3｜真实运行、个人成长校准与持续认知复利

**状态：** `planned`  
**Pursuing Goal：** 用真实 30 日运行、周/月报告、复习、行动和经济转化证据，证明系统能长期带来可验证成长而非只发送信息。  
**Entry Gate：** INTEGRATED_PRODUCTION_ACCEPTED。  
**Stop Gate：** `COGNITIVE_COMPOUNDING_ACCEPTED → CONTINUOUS_OPERATION`  
**Stop Conditions：** LIVE-FAIL；STATE-COUNT-FAIL；ROI-TRACE-FAIL；ACCEPTANCE-FAIL

## S3PA｜30 个真实自然日运行与日周月证据

**状态：** `planned`  
**Pursuing Goal：** 证明系统不仅能通过重放，还能在真实时间中持续产生稳定、高质量、可复习和可行动的情报。  
**Entry Gate：** INTEGRATED_PRODUCTION_ACCEPTED。  
**Stop Gate：** `THIRTY_DAY_OPERATION_EVIDENCED`  
**Stop Conditions：** LIVE-FAIL；EMAIL-DUP；STATE-COUNT-FAIL；ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S3PAT01` 30 日每日 3+1 真实运行 | `planned` | 完成 30 个自然日、120 封日邮件和每日账本。 | 无 | 120 封邮件均有唯一 Run、哈希和状态。 | `ACC-S3PAT01-30D-LIVE` |
| `S3PAT02` 4 份每周总结 | `planned` | 生成并发送至少 4 份周报。 | 无 | 周报覆盖认知、复习、行动、风险和下周重点。 | `ACC-S3PAT02-WEEKLY-LIVE` |
| `S3PAT03` 1 份完整月度总结 | `planned` | 生成月度认知差分、能力资产和经济转化报告。 | 无 | 月报证据可追溯且 Owner 可读。 | `ACC-S3PAT03-MONTHLY-LIVE` |
| `S3PAT04` 队列、复习、行动、ROI 总账对账 | `planned` | 核对所有状态、数量和转化记录。 | 无 | 分项与总数守恒，孤儿记录为 0。 | `ACC-S3PAT04-RECONCILIATION` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S3PB｜个人成长、内容质量与 ROI 校准

**状态：** `planned`  
**Pursuing Goal：** 用真实反馈和行动结果校准内容、复习、个人价值和经济转化模型。  
**Entry Gate：** S3PA 通过。  
**Stop Gate：** `PERSONAL_GROWTH_MODEL_CALIBRATED`  
**Stop Conditions：** ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S3PBT01` 人工质量评分与失败样本复盘 | `planned` | 抽样评估深度、清晰、相关、行动和反证。 | 无 | 低分样本有根因和修复任务。 | `ACC-S3PBT01-HUMAN-QA` |
| `S3PBT02` 预计 ROI 与实际转化偏差校准 | `planned` | 比较时间、成本、收益、机会和能力资产。 | 无 | 偏差可解释，无法量化时保持 not_calculable。 | `ACC-S3PBT02-ROI-CAL` |
| `S3PBT03` 复习间隔与掌握率校准 | `planned` | 根据忘记/模糊/掌握/应用反馈调整间隔。 | 无 | 调整有对照和回滚，不自动污染历史。 | `ACC-S3PBT03-REVIEW-CAL` |
| `S3PBT04` 权重和阈值 A/B 影响预览 | `planned` | 生成 30 日离线影响预览，Owner 决定是否应用。 | 无 | 不自动合并、不自动改收件人/来源/冻结参数。 | `ACC-S3PBT04-AB` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

## S3PC｜预测账本、来源治理与持续认知复利

**状态：** `planned`  
**Pursuing Goal：** 建立可证伪预测、来源准入/淘汰和持续改善机制，使系统长期提高而不漂移。  
**Entry Gate：** S3PB 通过。  
**Stop Gate：** `COGNITIVE_COMPOUNDING_ACCEPTED`  
**Stop Conditions：** ACCEPTANCE-FAIL

| Task | 状态 | Pursuing Goal / Objective | Dependencies | Stop Gate | Acceptance |
|---|---|---|---|---|---|
| `S3PCT01` 预测账本与准确率复盘 | `planned` | 为高价值信号记录期限、预期证据和推翻条件。 | 无 | 到期预测自动进入复盘且保留错误记录。 | `ACC-S3PCT01-PREDICTIONS` |
| `S3PCT02` 来源准入、降级、淘汰与恢复制度 | `planned` | 以质量、健康、价值和成本管理来源生命周期。 | 无 | 新增来源不越级，淘汰有证据和回滚。 | `ACC-S3PCT02-SOURCE-GOV` |
| `S3PCT03` 月度 Owner 决策评审与合同版本治理 | `planned` | 审查需求、参数、板块、邮件和新增能力。 | 无 | 每次重大改变产生决策事件和新合同哈希。 | `ACC-S3PCT03-OWNER-REVIEW` |
| `S3PCT04` 持续运行最终验收 | `planned` | 确认系统达到长期认知、能力、行动和经济转化目标。 | 无 | COGNITIVE_COMPOUNDING_ACCEPTED → CONTINUOUS_OPERATION。 | `ACC-S3PCT04-COMPOUNDING` |

### Phase 结束条件

- 只有 Stop Gate 和 Required Evidence 同时满足，Phase 才能结束。
- 任一 Stop Condition 触发时状态必须为 BLOCKED/FAILED，并写入开发记录和交接。

