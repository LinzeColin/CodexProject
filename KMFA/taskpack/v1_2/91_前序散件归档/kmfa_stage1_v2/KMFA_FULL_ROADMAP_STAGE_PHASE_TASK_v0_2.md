# KMFA 经营分析系统｜Codex 全程开发 Roadmap v0.2

> 状态：ChatGPT 阶段一产物草案。用于讨论、收敛、评审后进入 Codex TaskPack。  
> 项目路径：`CodexProject/KMFA`  
> 产品形态：独立项目；后续通过入口、报告中心、共享 manifest 或统一 launcher 接入 OpMe。  
> 角色：CEO / CFO / CTO，其中 CTO = Chief Tax Officer。原 CMO 商务经营合并到 CEO；技术/项目治理分摊到 CEO、CFO、CTO、数据治理。  
> 行业：建工建安、机电机加工、水泥钢铁能源化工委外安装维修，核心为项目制工程经营。

---

## 0. 全局开发原则

1. **Stage / Phase / Task 三层结构**：给 Codex 的 Roadmap 必须使用 Stage → Phase → Task，不再只用 Phase / Task 两层。  
2. **每个 Stage 不超过 5 个 Phase；每个 Phase 不超过 5 个 Task。**  
3. **每个 Codex run 只处理一个项目、一个 Stage/Phase/Task、一个 Acceptance。**  
4. **先 READ-ONLY PLAN，再实现。** 实现前必须列出读取文件、修改文件、测试命令、风险、回滚方案、Stop Condition。  
5. **原始敏感数据不进入公开 GitHub。** `KMFA/metadata` 保存 manifest、hash、lineage、状态、证据索引和报告 manifest。  
6. **单账本，多视图 reconciliation。** 不设计内外账；在唯一合法账本基础上建立管理分析、项目真实、税务政策、董事层经营视图。  
7. **确定性计算优先。** 金额、比例、趋势、评分必须由程序和公式计算；LLM/文案层只做解释、摘要、风险提示和报告表达。  
8. **数据源门禁。** 缺关键数据时，不推进对应报告章节，不生成完整结论。  
9. **通知不等于外发报告。** 邮件只提醒查看，不发送完整财务、合同、税务、工资或银行明细。  
10. **未来 OpMe 集成不得污染 KMFA MVP 与 OpMe 当前业务代码。**

---

## Stage 1｜项目合同与治理底座

**Pursuing Goal**：把 KMFA 从想法锁定为可交给 Codex 执行的独立项目合同，包括角色、边界、数据源、metadata、UI/UX、报告、治理与安全规则。  
**Pass Gate**：`KMFA_SCOPE_LOCK.md`、`ROLE_MODEL.md`、`DATA_SOURCE_CONTRACT.md`、`METADATA_PROTOCOL.md`、`REPORT_MATRIX.md`、`UIUX_REQUIREMENTS.md`、`FORMULA_REGISTRY.yaml`、`ROADMAP.yaml/md` 全部通过人工评审。  
**Stop Condition**：要求保存明文账号密码、将未脱敏原始财务/合同/银行/税务数据提交公开 GitHub、未确认 CTO=税务、未建立数据门禁而继续报告实现。  
**Validation**：文档检查 + 人工评审 + metadata 目录结构检查 + no-secret scan。

### Phase 1.1｜Scope Lock

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S1P1T1 | 建立 `CodexProject/KMFA` 项目壳 | README、AGENTS、功能清单、开发记录、模型参数文件存在 | 文件存在性检查 | 未继承根 AGENTS 规则 |
| S1P1T2 | 锁定产品定位 | 明确 KMFA = 经营分析系统，独立项目，未来接 OpMe | 人工评审 | 继续把 KMFA 直接塞进 OpMe |
| S1P1T3 | 锁定行业范围 | 覆盖项目制工程、建工建安、机电机加工、能源化工维修 | 范围矩阵检查 | 套用互联网营销模型 |
| S1P1T4 | 锁定非目标 | 不自动付款、不自动报税、不外发完整报告、不保存明文凭证 | 非目标清单 | 任何高风险自动执行 |
| S1P1T5 | 锁定术语 | CEO/CFO/CTO，CTO=Chief Tax Officer | ROLE_MODEL 通过 | CTO 被误写成技术负责人 |

### Phase 1.2｜Data Source Contract

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S1P2T1 | 建立数据源注册表 | 红圈、金蝶、WPS、银行、税务/数电票、合同、政策证据包全部登记 | schema lint | 缺 CFO/CTO 必要源 |
| S1P2T2 | 定义文件包清单 | 每个源列出 required/optional 文件、命名模式、频率 | CSV/YAML 检查 | 文件包无法映射报告章节 |
| S1P2T3 | 定义字段映射草案 | 每个源有 schema map 占位 | schema map 存在 | 直接把源表当 canonical facts |
| S1P2T4 | 定义数据新鲜度 | 周/月/季/半年/年 freshness 规则 | freshness test | 过期数据仍支撑实时结论 |
| S1P2T5 | 定义数据源门禁 | READY/PARTIAL/FAILED/OUTDATED/MANUAL_REVIEW 状态体系生效 | data readiness matrix | blocking/not_applicable 状态未合并 |

### Phase 1.3｜Metadata & Security Protocol

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S1P3T1 | 建立 `KMFA/metadata` 目录协议 | sources/imports/schema_maps/data_quality/lineage/reports/notifications/approvals 存在 | tree check | metadata 保存原始敏感数据 |
| S1P3T2 | 建立 credentials 占位规则 | 只有 example，不保存明文账号密码 | no-secret scan | 出现 password/token 明文 |
| S1P3T3 | 建立 evidence index 规则 | 保存 hash、来源、lineage，不保存合同/发票/银行原文 | hash manifest test | 原文进公开仓库 |
| S1P3T4 | 建立 report manifest | 每份报告记录 data batch、参数版本、导出格式、确认状态 | manifest schema test | 报告无 lineage |
| S1P3T5 | 建立 notification log | 只记录提醒事件，不保存完整报告正文 | notification schema test | email 发送敏感明细 |

### Phase 1.4｜UI/UX & Report Contract

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S1P4T1 | 首页 Dashboard 预览 | 商务风、人类可读、可二级导航 | 人工 UI 评审 | 明显 AI 工具感过重 |
| S1P4T2 | 报告预览 | Board Pack/CEO/CFO/CTO/Reconciliation/附录可评审 | 人工报告评审 | 报告没有表格和图形化表达 |
| S1P4T3 | 数据源检查板 UI | 行列交叉矩阵、状态颜色、文件包可见 | UI 交互检查 | 缺源/缺文件无法定位 |
| S1P4T4 | 周/月/季/半年/年报告矩阵 | 每周期报告形式、受众、门禁清晰 | report matrix lint | 只做月报 |
| S1P4T5 | 可读性标准 | 非专业摘要 + 专业附表双层表达 | checklist | 只给专业财务表或只给空泛摘要 |

### Phase 1.5｜Formula & Roadmap Contract

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S1P5T1 | 建立公式注册表 | 经营健康雷达、行动评分、reconciliation、数据门禁公式可见 | YAML lint | 权重/阈值隐藏在前端 |
| S1P5T2 | 建立参数版本管理 | 参数版本进入报告 manifest | unit test | 报告无法复现 |
| S1P5T3 | 建立 Codex Roadmap | Stage/Phase/Task 全程任务完整 | 人工评审 | Roadmap 缺 reconciliation |
| S1P5T4 | 建立风险等级 | money/tax/privacy/source side effects 为高风险 | risk matrix | 外部副作用无 gate |
| S1P5T5 | Stage 2 研究计划 | 官方政策、ERP/API、金蝶/WPS/红圈、工程行业模型研究列表 | research plan | 直接进入实现 |

---

## Stage 2｜基础工程骨架与本地运行

**Pursuing Goal**：创建可运行的 KMFA 独立项目骨架，前后端、metadata、样例数据、测试与静态预览都可在本地运行。  
**Pass Gate**：本地启动成功；Dashboard 与报告预览可访问；metadata 初始化；样例数据不含敏感信息；基础测试通过。  
**Stop Condition**：直接接真实账号、直接接生产数据、直接修改 OpMe 主业务代码。  
**Validation**：unit tests + smoke test + no-secret scan + sample data scan。

### Phase 2.1｜Project Skeleton

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S2P1T1 | 建立 backend/frontend/docs/metadata/samples/scripts | 目录结构符合 TaskPack | tree check | 无 docs 或 metadata |
| S2P1T2 | 建立 FastAPI 或等价后端壳 | health endpoint 可访问 | smoke test | 无后端入口 |
| S2P1T3 | 建立前端壳 | 首页、CEO、CFO、CTO、数据检查板、报告中心可导航 | UI smoke | 无二级导航 |
| S2P1T4 | 建立报告模板目录 | HTML/PDF/Markdown 模板占位 | template check | 报告逻辑写死在页面 |
| S2P1T5 | 建立配置加载 | formula_registry、data readiness、report config 可加载 | unit test | 参数硬编码 |

### Phase 2.2｜Metadata Runtime

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S2P2T1 | import_runs writer | 每次导入生成 run_id 与 manifest | unit test | 导入无记录 |
| S2P2T2 | file_fingerprint | 文件 hash、大小、行数、时间戳保存 | unit test | 不能追溯文件 |
| S2P2T3 | evidence_index | 指标、报告、数据源可关联 | unit test | 报告数字无来源 |
| S2P2T4 | report_manifest writer | 报告生成记录参数版本与数据批次 | unit test | 报告不可复现 |
| S2P2T5 | notification_log | 通知事件可记录 | unit test | 无通知审计 |

### Phase 2.3｜Sample Data & Fixtures

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S2P3T1 | 构造脱敏样例红圈数据 | 项目、合同、进度、人材机 | fixture test | 使用真实客户明细 |
| S2P3T2 | 构造脱敏金蝶数据 | 科目、凭证、利润、应收应付 | fixture test | 使用真实凭证 |
| S2P3T3 | 构造 WPS 台账样例 | 报价、采购、工时、研发辅助 | fixture test | 样例无法覆盖字段 |
| S2P3T4 | 构造银行/税务样例 | 流水、日余额、发票摘要 | fixture test | 包含完整账号/税号敏感明细 |
| S2P3T5 | 构造政策证据样例 | IP、研发、科技人员、高新收入 | fixture test | 诱导包装材料 |

### Phase 2.4｜Static UI Integration

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S2P4T1 | 导入 Dashboard v2 样式 | 首页专业商务风 | screenshot review | 保留明显 AI 痕迹 |
| S2P4T2 | 导入 Report Preview 样式 | 报告适配打印/PDF | print test | PDF 不可读 |
| S2P4T3 | 数据检查矩阵组件 | 横向滚动、颜色、状态 legend | component test | 看不到文件级状态 |
| S2P4T4 | period switch | 周/月/季/半年/年切换 | UI test | 周期状态混乱 |
| S2P4T5 | responsive layout | 管理层电脑/平板可读 | viewport test | 小屏不可用 |

### Phase 2.5｜Local Dev & CI

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S2P5T1 | smoke_test.sh | 一键检查后端/前端/metadata | shell test | 无验收命令 |
| S2P5T2 | unit test skeleton | formula/data/readiness/report 有测试壳 | pytest | 无测试目录 |
| S2P5T3 | lint/format | 基础 lint 通过 | CI | 大量未格式化代码 |
| S2P5T4 | no-secret scan | 检查常见 secret 模式 | CI | 出现明文 secret |
| S2P5T5 | changelog/dev log | 开发记录自动/手动可维护 | docs check | 无开发记录 |

---

## Stage 3｜数据导入、字段映射与检查板

**Pursuing Goal**：支持 Codex 端、网页端、自动/半自动导入，并统一进入 metadata、data quality、readiness gate。  
**Pass Gate**：红圈/金蝶/WPS/银行/税务/合同/政策证据包样例可导入，状态矩阵自动更新，缺数据能阻塞对应报告。  
**Stop Condition**：把导入逻辑与报告逻辑耦合、跳过 schema mapping、导入失败但状态仍显示 READY。  
**Validation**：integration tests + sample import tests + matrix state tests。

### Phase 3.1｜Universal Import Contract

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S3P1T1 | 定义 Import Contract | source_id/run_id/file_hash/schema/status 统一 | schema test | 各导入方式各走一套状态 |
| S3P1T2 | Codex CLI 导入 | 命令行可导入样例文件 | CLI test | CLI 导入不写 metadata |
| S3P1T3 | Web 上传导入 | 前端上传、后端保存 manifest | integration test | 上传后无 run_id |
| S3P1T4 | 自动导入占位 | schedule config 存在但默认关闭 | config test | Stage 3 直接连生产账号 |
| S3P1T5 | 导入幂等性 | 同文件重复导入不会重复污染 facts | idempotency test | 重复导入金额翻倍 |

### Phase 3.2｜Source Adapters v1

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S3P2T1 | 红圈导出文件 adapter | 项目/合同/成本样例可解析 | adapter test | API 未确认就强接 |
| S3P2T2 | 金蝶导出文件 adapter | 科目/凭证/应收应付样例可解析 | adapter test | 忽略辅助核算 |
| S3P2T3 | WPS 表格 adapter | 报价/采购/工时表可解析 | adapter test | 临时表无法映射 |
| S3P2T4 | 银行流水 adapter | 流水/日余额样例可解析 | adapter test | 无隐私脱敏 |
| S3P2T5 | 税务/发票 adapter | 销项/进项/税率样例可解析 | adapter test | 税率字段缺失仍 READY |

### Phase 3.3｜Schema Mapping

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S3P3T1 | canonical schema | customer/contract/project/payment/invoice/cost/policy 等实体 | schema test | 无 canonical layer |
| S3P3T2 | 字段映射 UI/配置 | 用户可查看/调整映射 | UI test | 映射藏在代码里 |
| S3P3T3 | required/optional 字段 | 缺 required 进入 PARTIAL/FAILED | unit test | 缺关键字段仍 READY |
| S3P3T4 | 字段类型校验 | 日期/金额/税率/项目 ID 校验 | unit test | 金额当文本通过 |
| S3P3T5 | mapping version | 映射版本写入 import manifest | metadata test | 报告无法复现口径 |

### Phase 3.4｜Data Quality Engine

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S3P4T1 | 缺失值/重复值检查 | 输出 validation_results | unit test | 无数据质量报告 |
| S3P4T2 | 异常金额/日期检查 | 大额、负数、跨期、未来日期预警 | unit test | 异常无标记 |
| S3P4T3 | 跨源一致性检查 | 合同金额、开票、回款、项目成本核对 | integration test | Reconciliation 无法支撑 |
| S3P4T4 | freshness 检查 | 超期转 OUTDATED | unit test | 过期仍 READY |
| S3P4T5 | MANUAL_REVIEW 队列 | 复核事项写入 metadata | integration test | 人工复核无队列 |

### Phase 3.5｜Data Readiness Board

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S3P5T1 | 行列矩阵状态计算 | 每源每文件包状态可见 | component test | 只能看源不能看文件 |
| S3P5T2 | 报告章节阻塞关系 | 缺数据阻塞相应报告 | unit test | 缺数据仍生成完整报告 |
| S3P5T3 | 状态颜色规范 | green/yellow/red/black/purple | visual test | 色彩不一致 |
| S3P5T4 | 上传后自动打勾 | 成功导入更新 READY | integration test | 上传后状态不变 |
| S3P5T5 | 缺失报警 | 缺文件、过期、失败显示报警 | UI test | 用户不知道缺什么 |

---

## Stage 4｜项目制经营模型与 Reconciliation 引擎

**Pursuing Goal**：建立 KMFA 的核心行业模型：客户→机会/报价→合同→项目→成本→结算→开票→回款→质保→复盘，并实现单账本多视图 reconciliation。  
**Pass Gate**：可用样例数据生成项目真实利润、现金流、应收应付、税务口径、reconciliation bridge；每个关键数字有 lineage。  
**Stop Condition**：没有 reconciliation 就输出管理利润；LLM 直接算财务数字；把多视图误写成内外账。  
**Validation**：formula unit tests + reconciliation snapshot tests + lineage tests。

### Phase 4.1｜Canonical Business Entities

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S4P1T1 | Customer/Project/Contract | 核心实体 schema 完成 | schema test | 项目与合同无法关联 |
| S4P1T2 | Cost/Labor/Material/Subcontract | 人材机与外协成本实体完成 | schema test | 成本不能归项目 |
| S4P1T3 | Invoice/Payment/Receivable/Payable | 开票、收付、应收应付实体完成 | schema test | 现金与利润无法分离 |
| S4P1T4 | ChangeOrder/Settlement/Retention | 签证、结算、质保金实体完成 | schema test | 真实毛利缺关键项 |
| S4P1T5 | PolicyEvidence | 政策证据实体完成 | schema test | 政策报告无证据链 |

### Phase 4.2｜Project Profit Engine

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S4P2T1 | 合同毛利 | 合同金额、预估成本、报价毛利 | unit test | 报价漏项未标注 |
| S4P2T2 | 实际直接成本 | 人材机、外协、运输、差旅、返工归集 | unit test | 未归集成本不报警 |
| S4P2T3 | 结算毛利 | 签证/变更/结算金额纳入 | unit test | 变更无证据 |
| S4P2T4 | 现金毛利 | 回款、付款、质保金、垫资影响 | unit test | 利润与现金混淆 |
| S4P2T5 | 项目毛利 bridge | 合同毛利→管理真实毛利路径可视 | snapshot test | bridge 无来源 |

### Phase 4.3｜CFO Finance Engine

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S4P3T1 | P&L 摘要 | 收入、成本、费用、利润可计算 | unit test | 金额由文案生成 |
| S4P3T2 | 直接法现金流 | 期初、流入、流出、期末、runway | unit test | 无银行数据仍完整结论 |
| S4P3T3 | 应收应付账龄 | 账龄、超期、争议、优先级 | unit test | 应收不关联合同 |
| S4P3T4 | 费用结构 | 管理、销售/商务、研发/技术、税费等 | unit test | 分类缺失不提示 |
| S4P3T5 | 现金场景模拟 | 收入延迟、回款延迟、成本上涨 | unit test | 情景假设不记录 |

### Phase 4.4｜Reconciliation Engine

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S4P4T1 | 单账本多视图模型 | accounting/management/project/tax/board views | schema test | 被描述为内外账 |
| S4P4T2 | adjustment ledger | 每项调整有 reason/source/evidence/owner/status | unit test | 调整无证据 |
| S4P4T3 | profit bridge | 账面利润→管理真实利润 | snapshot test | bridge 不可复现 |
| S4P4T4 | tax timing/classification bridge | 税务口径差异可解释 | unit test | 税务建议无复核 |
| S4P4T5 | stakeholder view output | 不同 stakeholder 看到同一事实的不同分析视图 | integration test | 多视图数字互相矛盾无解释 |

### Phase 4.5｜Lineage & Evidence

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S4P5T1 | metric_lineage | 每个关键指标关联源、公式、参数版本 | unit test | 指标无 lineage |
| S4P5T2 | report_lineage | 报告章节关联数据批次 | unit test | 报告不可审计 |
| S4P5T3 | evidence drilldown | Dashboard 可看到来源摘要 | UI test | 用户无法追溯 |
| S4P5T4 | sensitive evidence policy | 原文不进公开仓库 | no-secret/data scan | 敏感数据泄露 |
| S4P5T5 | reconciliation audit trail | 调整与人工确认可审计 | integration test | 调整无法复盘 |

---

## Stage 5｜CEO / CFO / CTO 报告与 Dashboard

**Pursuing Goal**：生成周/月/季/半年/年报告，覆盖 CEO、CFO、CTO 和 Board Pack，支持 Dashboard、PDF、CSV/Excel 附表。  
**Pass Gate**：用样例数据生成完整报告包；缺数据时报告降级；PDF 可读；表格和可视化清晰；报告 manifest 完整。  
**Stop Condition**：报告出现空泛 AI 痕迹、无证据数字、缺数据仍输出肯定结论、不可打印或不可读。  
**Validation**：snapshot tests + PDF/print test + readability checklist + report manifest check。

### Phase 5.1｜Dashboard Pages

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S5P1T1 | 首页总览 | 经营健康、现金、毛利、回款、政策、数据门禁 | UI test | 首屏信息过载或空泛 |
| S5P1T2 | CEO page | 商务订单、项目组合、Board 决策 | UI test | CMO 未合并或广告化 |
| S5P1T3 | CFO page | 现金、利润、应收应付、reconciliation | UI test | 缺 reconciliation |
| S5P1T4 | CTO page | 税务、发票、政策资格、证据归集 | UI test | CTO 又变成技术 |
| S5P1T5 | 数据检查板 page | 行列矩阵、上传、状态、阻塞 | UI test | 缺文件级可见性 |

### Phase 5.2｜Report Templates

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S5P2T1 | Weekly report | 现金/回款/项目风险/数据缺口 | snapshot | 周报变成月报缩略版 |
| S5P2T2 | Monthly board pack | CEO/CFO/CTO/Reconciliation/附录 | snapshot | 缺角色章节 |
| S5P2T3 | Quarterly report | 战略复盘/预算/政策/组合 | snapshot | 只有财务表 |
| S5P2T4 | Half-year report | 政策证据、经营中盘、治理评估 | snapshot | 缺政策视角 |
| S5P2T5 | Yearly report | 年度经营、证据归档、预算、复盘 | snapshot | 无复盘与归档 |

### Phase 5.3｜Charts & Tables

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S5P3T1 | 经营健康雷达 | 根据 formula_registry 计算 | unit + UI | 前端硬编码 |
| S5P3T2 | 项目毛利 bridge | 可视化合同毛利到真实毛利 | snapshot | 无表格明细 |
| S5P3T3 | 现金曲线 | 4/8/12 周现金压力 | unit + UI | 缺银行数据仍展示确定曲线 |
| S5P3T4 | 政策 readiness | 科小/高新/专精特新/研发加计扣除 | unit + UI | 政策结论过度肯定 |
| S5P3T5 | 数据检查矩阵 | 状态颜色和阻塞关系 | UI test | 颜色/状态不统一 |

### Phase 5.4｜Export Layer

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S5P4T1 | HTML report | 可浏览、可打印 | browser test | 布局破碎 |
| S5P4T2 | PDF export | 页眉页脚、目录、表格可读 | PDF test | PDF 缺关键图表 |
| S5P4T3 | CSV export | 关键附表可下载 | CSV test | CSV 无字段说明 |
| S5P4T4 | Excel export | 可选附表 xlsx | xlsx test | 格式错乱 |
| S5P4T5 | report package manifest | 每次导出有 manifest | metadata test | 导出不可审计 |

### Phase 5.5｜Human Readability & Quality Density

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S5P5T1 | 非专业摘要 | 每章先结论与下一步 | readability checklist | 只有专业术语 |
| S5P5T2 | 专业附表 | 每个结论有表格、公式或证据 | evidence check | 只有空泛文案 |
| S5P5T3 | ROI first action list | 行动按影响/成本/风险排序 | unit + snapshot | 建议不可执行 |
| S5P5T4 | limitation disclosure | 缺数据、过期、复核事项清楚 | snapshot | 隐藏不确定性 |
| S5P5T5 | report red-team | 检查明显 AI 痕迹、幻觉、无证据结论 | review checklist | 报告像聊天稿 |

---

## Stage 6｜CTO 税务政策、合同风险与报价漏项

**Pursuing Goal**：支持税务政策 readiness、研发费用证据、科小/高新/专精特新/小巨人准备度、合同风险扫描、报价漏项检测。  
**Pass Gate**：政策模块输出的是“证据缺口与风险提示”，不是包装或最终申报承诺；15.7 合同风险与 15.8 报价漏项作为未来采纳功能进入实现；15.6 低营销费用行业 CMO 模型不采纳。  
**Stop Condition**：鼓励虚构材料、输出确定申报成功、忽略人工税务复核、合同/报价模块无证据。  
**Validation**：policy rule tests + evidence completeness tests + human review gate。

### Phase 6.1｜Policy Readiness Engine

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S6P1T1 | 科技型中小企业 readiness | 条件、材料、缺口、证据状态 | unit test | 无官方依据版本 |
| S6P1T2 | 高新技术企业 readiness | IP、科技人员、研发费用、高新收入、审计材料 | unit test | 过度承诺成功 |
| S6P1T3 | 专精特新/小巨人 readiness | 专业化、精细化、特色化、创新与产业链 | unit test | 忽略最新政策版本 |
| S6P1T4 | 研发加计扣除 readiness | 研发项目、费用归集、留存备查 | unit test | 非研发活动被纳入 |
| S6P1T5 | 地方政策扩展占位 | 可维护 policy_registry | config test | 政策写死 |

### Phase 6.2｜Tax & Invoice Engine

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S6P2T1 | 税率匹配 | 合同税率/开票税率/业务类型对照 | unit test | 税率缺失仍 READY |
| S6P2T2 | 进销项匹配 | 项目进项、销项、抵扣状态 | unit test | 进项缺口无提示 |
| S6P2T3 | 计税方式记录 | 一般/简易等口径可记录 | schema test | 计税口径空缺 |
| S6P2T4 | 税负分析 | 税负率与异常预警 | unit test | 输出税务处理建议无复核 |
| S6P2T5 | CTO signoff | 高风险税务结论需要人工确认 | integration test | 税务结论自动通过 |

### Phase 6.3｜Contract Risk Scanner（15.7 未来采纳）

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S6P3T1 | 合同字段结构化 | 付款、质保、税率、验收、违约、签证 | parser test | 合同全文泄露 |
| S6P3T2 | 风险规则库 | 红黄绿规则可配置 | unit test | 规则硬编码不可维护 |
| S6P3T3 | 风险摘要 | 给 CEO/CFO/CTO 不同视角 | snapshot | 只给法务语言 |
| S6P3T4 | 证据索引 | 风险条款可回溯到合同位置 | lineage test | 风险无证据 |
| S6P3T5 | 人工复核 | 合同风险需人工确认 | workflow test | 自动替代合同审查 |

### Phase 6.4｜Quotation Gap Detector（15.8 未来采纳）

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S6P4T1 | 历史项目成本基线 | 类似项目成本结构可对比 | unit test | 没有可比项目仍强判断 |
| S6P4T2 | 报价漏项规则 | 人材机、外协、运输、吊装、安全、税费、差旅 | unit test | 漏项规则不可解释 |
| S6P4T3 | 报价毛利预警 | 低于阈值转 PARTIAL/REVIEW | unit test | 低毛利无提示 |
| S6P4T4 | 报价建议 | 只给建议和风险，不自动改报价 | snapshot | 自动替用户定价 |
| S6P4T5 | 报价复盘 | 成交后对比实际成本并校准 | backtest | 无复盘闭环 |

### Phase 6.5｜Policy Evidence Governance

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S6P5T1 | evidence checklist | 每个政策有 required evidence | config test | 缺证据仍乐观 |
| S6P5T2 | evidence freshness | 年度/季度材料过期预警 | unit test | 旧材料支撑新报告 |
| S6P5T3 | anti-packaging note | 明确不虚构、不包装、不规避监管 | doc check | 输出违规建议 |
| S6P5T4 | CTO review queue | 待复核事项集中显示 | UI test | 复核分散不可追踪 |
| S6P5T5 | policy report appendix | 输出证据缺口附录 | snapshot | 政策报告无附录 |

---

## Stage 7｜通知、权限、多角色与自动化连接器

**Pursuing Goal**：在不外发完整报告、不泄露敏感数据的前提下，建立通知、权限、三人多角色、自动/半自动连接器。  
**Pass Gate**：邮件提醒可用但内容安全；角色帽子记录完整；连接器默认只读且可关闭；失败自动进入检查板。  
**Stop Condition**：发送完整报告正文、保存明文凭证、自动外部写入、权限绕过。  
**Validation**：security tests + notification snapshot + permission tests + connector dry-run。

### Phase 7.1｜Roles & Permissions

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S7P1T1 | 三人多角色模型 | user + role_hat + action 记录 | unit test | 只按人不按角色 |
| S7P1T2 | CEO/CFO/CTO 权限 | 页面、报告、审批权限分明 | permission test | CFO 可绕过 CTO 税务复核 |
| S7P1T3 | board view | Board 只看摘要与必要附录 | UI test | Board 看到过多敏感明细 |
| S7P1T4 | human signoff | 高风险事项必须确认 | workflow test | 自动确认 |
| S7P1T5 | audit log | 谁以哪个角色确认什么 | audit test | 无审计轨迹 |

### Phase 7.2｜Notifications

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S7P2T1 | notification rules | report_ready/cash_risk/data_failed/tax_risk | unit test | 规则不可配置 |
| S7P2T2 | email adapter | 发送到 linzezhang35@gmail.com，默认仅提醒 | dry-run test | 邮件含完整报告正文 |
| S7P2T3 | alert severity | info/warn/critical | unit test | 所有提醒同级 |
| S7P2T4 | notification log | 记录发送时间、事件、报告 ID | metadata test | 无通知审计 |
| S7P2T5 | unsubscribe/pause config | 可关闭或静默通知 | config test | 生产扰民 |

### Phase 7.3｜Connector Research & Dry Run

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S7P3T1 | 红圈连接器研究 | API/导出/RPA 可行性文档 | research review | 未确认就连生产 |
| S7P3T2 | 金蝶连接器研究 | OpenAPI/导出/权限方案 | research review | 写入财务系统 |
| S7P3T3 | WPS 连接器研究 | API/手工上传/共享表方案 | research review | 直接抓私人文档 |
| S7P3T4 | 银行/税务导入研究 | 优先只读导出与人工上传 | security review | 自动登录网银/税务做危险操作 |
| S7P3T5 | connector dry-run | mock credentials + sample files | dry-run | 使用真实密码测试 |

### Phase 7.4｜Scheduled Jobs

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S7P4T1 | schedule config | 每源频率可配置，默认关闭自动外联 | config test | 默认自动跑生产同步 |
| S7P4T2 | retry/idempotency | 失败重试不污染数据 | unit test | 重试重复入账 |
| S7P4T3 | failure alerts | 自动更新检查板与通知 | integration test | 失败静默 |
| S7P4T4 | manual override | 用户可手工标记复核与阻塞 | UI test | 无人工 override |
| S7P4T5 | run history | 连接器运行历史可审计 | metadata test | 无运行日志 |

### Phase 7.5｜Security Hardening

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S7P5T1 | secret management | .env/example/secrets 文档 | security test | 明文 secret 进 repo |
| S7P5T2 | sensitive data scanner | 样例/metadata/报告扫描 | CI | 敏感数据泄露 |
| S7P5T3 | retention policy | 原始、脱敏、metadata 保留策略 | doc check | 无限保存敏感数据 |
| S7P5T4 | backup/restore | metadata 与配置可备份恢复 | restore test | 无恢复方案 |
| S7P5T5 | permission regression | 权限变更有回归测试 | test | 权限回归未发现 |

---

## Stage 8｜稳定化、验收、OpMe 集成准备

**Pursuing Goal**：完成系统级验收、长期维护、运行治理、性能、安全和未来 OpMe 集成边界。  
**Pass Gate**：全链路 smoke test 通过；报告可复现；数据门禁有效；文档齐全；OpMe 集成方案只读且不改主业务。  
**Stop Condition**：未稳定就接生产、未脱敏就交付、未通过门禁就接 OpMe。  
**Validation**：E2E tests + report reproducibility + governance CI + security review + UAT。

### Phase 8.1｜End-to-End Acceptance

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S8P1T1 | 样例全链路 | 导入→检查板→指标→报告→通知 dry-run | E2E | 任一环节无 manifest |
| S8P1T2 | 缺数据链路 | 缺文件会阻塞报告章节 | E2E | 缺数据仍完整结论 |
| S8P1T3 | Reconciliation 链路 | 调整→bridge→报告→signoff | E2E | bridge 不可追溯 |
| S8P1T4 | 政策链路 | 证据→readiness→缺口→复核 | E2E | 政策结论过度肯定 |
| S8P1T5 | 导出链路 | dashboard/pdf/csv/xlsx manifest | E2E | 导出无记录 |

### Phase 8.2｜Performance & Reliability

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S8P2T1 | report generation performance | 样例规模内生成稳定 | performance test | 页面卡死 |
| S8P2T2 | import large files | 大 CSV/XLSX 处理可控 | load test | 内存暴涨 |
| S8P2T3 | caching strategy | 指标缓存与失效规则 | unit test | 缓存导致旧数据 |
| S8P2T4 | error handling | 用户可读错误提示 | UI test | 报错只有堆栈 |
| S8P2T5 | logging | 运行日志分级 | log check | 无日志定位问题 |

### Phase 8.3｜Governance CI

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S8P3T1 | docs governance | 三中文入口维护 | docs check | 入口文档过期 |
| S8P3T2 | formula governance | 参数变更有版本和 changelog | config test | 参数改了报告不知 |
| S8P3T3 | metadata governance | schema 版本化 | schema test | 旧 metadata 不兼容 |
| S8P3T4 | report governance | report manifest 必填 | CI | 报告无 manifest |
| S8P3T5 | evidence governance | evidence_refs 必填 | CI | 关键数字无来源 |

### Phase 8.4｜OpMe Integration Preparation

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S8P4T1 | 集成边界文档 | KMFA 独立核心，OpMe 只做入口/报告中心 | doc review | 直接混入 OpMe 数据域 |
| S8P4T2 | manifest contract | KMFA 报告可被 OpMe 读取摘要 | contract test | OpMe 需要读敏感原始数据 |
| S8P4T3 | launcher card | OpMe 可显示 KMFA 入口卡片方案 | UI mock | 修改 OpMe 核心逻辑 |
| S8P4T4 | shared auth 预案 | 后续 SSO/权限映射文档 | security review | 权限绕过 |
| S8P4T5 | rollback plan | 集成失败可独立回滚 | rollback test | 集成不可撤销 |

### Phase 8.5｜Release Package

| Task ID | Task | Acceptance Criteria | Validation | Stop Condition |
|---|---|---|---|---|
| S8P5T1 | release notes | 功能、限制、风险、迁移说明 | doc review | 无发布说明 |
| S8P5T2 | admin guide | 数据源、导入、报告、通知、权限 | doc review | 用户不会维护 |
| S8P5T3 | operator checklist | 周/月/季/半年/年运行检查 | checklist test | 无运行手册 |
| S8P5T4 | backup package | 配置、metadata、样例、文档可打包 | package test | 交付不完整 |
| S8P5T5 | UAT signoff | CEO/CFO/CTO 角色确认 | UAT | 未经人工验收上线 |

---

## Surprise Backlog 状态

| 编号 | 名称 | 状态 | 进入 Stage |
|---|---|---|---|
| 15.1 | CEO War Room | 采纳 | Stage 5 |
| 15.2 | 项目毛利 Bridge | 采纳 | Stage 4/5 |
| 15.3 | 回款优先级引擎 | 采纳 | Stage 4/5 |
| 15.4 | 税务政策资格雷达 | 采纳 | Stage 6 |
| 15.5 | 监管/管理视图差异图，改名 Reconciliation Bridge | 采纳并修正 | Stage 4/5 |
| 15.6 | 低营销费用行业 CMO 模型 | 不采纳 | 删除，商务并入 CEO |
| 15.7 | 合同风险扫描 | 未来采纳 | Stage 6.3 |
| 15.8 | 报价漏项检测 | 未来采纳 | Stage 6.4 |
| 15.9 | 委外供应商风险榜 | 候选 | Stage 6/后续 |
| 15.10 | 三人多角色驾驶舱 | 采纳 | Stage 7 |

---

## 当前 ChatGPT 阶段一仍未完成的讨论项

1. 报告预览与 Dashboard v2 的 UI/UX 是否符合“商务风、人类质感、少 AI 痕迹”。  
2. 经营健康雷达权重是否需要调整。  
3. 数据源检查矩阵的列是否需要按你们真实红圈/金蝶/WPS 导出文件名进一步细分。  
4. Reconciliation 的 adjustment 类型是否贴合你们真实账务处理复杂度。  
5. Stage 2 是否先做纯本地上传 MVP，还是先研究红圈/金蝶/WPS API。  

