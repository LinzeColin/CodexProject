
# 美国企业权力—资本—战略网络研究规格

**文件名**：US_Corporate_Power_Map_Research_Universe_Source_Metrics_Screening_v0.1_2026-06-19.md  
**规格版本**：v1.0（作为 Task Pack v2.0 的研究范围基线）  
**基准日期**：2026-06-19  
**状态**：实施基线；具体实体状态与关系仍需按来源逐条核验  
**用途**：确认研究公司池、来源体系、研究对象、关键指标、数据参数和筛选门槛；作为 Codex 的研究宇宙、来源、指标与筛选基线。

> **结论与默认建议**：采用“30 家 P0 深挖 + 50 家 P1 扩展 + 40 家 P2 观察”的 120 家美国研究宇宙，并保留 20 个全球关键外部节点。MVP 不应试图一次性把 120 家全部做成同等深度；应先把 P0 做成证据充分的关系图，再自动扩展 P1、事件触发 P2。

## 0. 审阅状态表
| 项目 | 默认方案 | 本稿是否已定义 | 实施动作 |
| --- | --- | --- | --- |
| 美国公司/组织池 | 120 个：P0 30、P1 50、P2 40 | 是 | 生成 seed_universe.csv 与研究队列 |
| 全球外部节点 | 20 个，仅在与美国核心节点存在实质关系时展开 | 是 | 生成 external_context.csv |
| 数据来源 | 一级监管/法律来源优先，官方自述次之，商业库可选 | 是 | 生成 source_registry.csv 与连接器计划 |
| 研究对象 | 实体、人员、证券、基金、合同、设施、事件和证据 | 是 | 冻结领域模型 |
| 关键指标 | 控制、资本、依赖、政策、网络和证据质量六大类 | 是 | 生成 metric_catalog.csv |
| 筛选门槛 | 公司纳入、关系入图、事件告警、证据展示四层门槛 | 是 | 写入规则引擎 |
| 预测边界 | 只输出证据、信号和可证伪假设；不声称看见隐藏真实资金流 | 是 | 写入产品和风控要求 |

## 1. 需求边界与研究目的

### 1.1 系统最终要回答的八个问题

1. **谁控制谁**：法律母子公司、投票权、经济权益、董事任命权、信托/基金会/PBC等特殊治理安排是什么？
2. **谁给谁提供资本**：股权、债务、可转债、信贷、基金、政府奖励和长期采购承诺分别来自哪里？
3. **资本被投向哪里**：研发、资本开支、数据中心、电力、并购、战略少数股权、回购和股息如何变化？
4. **谁依赖谁**：芯片、云、模型、数据、能源、客户、供应商、分发平台和政府采购的关键依赖是什么？
5. **哪些人和机构构成治理网络**：创始人、董事、高管、投资机构、银行、私募基金、政府机构之间如何连接？
6. **最近发生了什么变化**：控制权、融资、并购、合同、监管、董事、高管和资本开支的变化是否构成结构性事件？
7. **下一轮战略浪潮可能在哪里**：用可解释的资本配置、供应链、专利、合同和政策信号形成假设，而不是用单一价格指标猜测。
8. **结论有多可信**：每个节点、边、金额和判断必须显示来源、报告期、申报日、观察日、置信度和已知冲突。

### 1.2 明确不做的事情

- 不承诺揭示未披露、非法获得或真正“隐藏”的资金流。
- 不把 Form 13F 的季度持仓快照称为实时资金流。
- 不从新闻传闻推导精确持股比例、估值或控制权。
- 不将品牌、产品、法律实体、基金、管理人和受益所有人混为一个节点。
- 不直接输出“必涨/必跌”或个性化买卖指令；战略雷达只产生可验证、可回测、带不确定性的研究假设。
- 不在 MVP 阶段依赖付费数据库、绕过登录/付费墙或违反来源条款的抓取。

### 1.3 时间与深度边界

- **P0 深挖历史窗**：默认 5 年；公开公司至少覆盖最近 8 个季度、最近 2 份年报和最新 proxy。
- **P1 扩展历史窗**：默认 3 年；先完成身份、集团结构、主要资本和一跳关系。
- **P2 观察窗**：默认 18 个月；仅在重大事件触发时升级。
- **更新模型**：每日增量抓取 + 来源驱动更新；“实时”必须显示披露滞后，不能伪装成交易所级实时资本流。

## 2. 公司与组织研究宇宙

### 2.1 分层原则

- **P0：MVP 深挖对象**。必须形成公司档案、控制图、资本河流、战略雷达和证据时间线。
- **P1：首轮网络扩展**。必须建立完整实体身份与核心一跳关系；重大事件可升级到 P0 深度。
- **P2：观察/事件触发对象**。只维持身份、来源入口和事件监控，不在 MVP 中做全历史手工研究。
- **X：全球外部节点**。不是“美国公司池”的替代品；仅在供应链、资本、控制、政策或技术依赖与 P0/P1 发生实质连接时展开。

### 2.2 P0：30 家深挖对象
| ID | 公司/组织 | 权力系统 | 初始形态（入库时复核） | 首要研究焦点 |
| --- | --- | --- | --- | --- |
| P0-001 | Alphabet Inc. | 数字平台 / 云 / AI | 上市集团 | 母子公司与品牌分离；Google/Cloud/YouTube/Waymo；AI资本开支、并购、监管与数据依赖 |
| P0-002 | Microsoft Corporation | 云 / 企业软件 / AI | 上市集团 | Azure、OpenAI经济与治理关系、AI基础设施资本开支、企业分发渠道与监管 |
| P0-003 | Amazon.com, Inc. | 云 / 电商 / 物流 / AI | 上市集团 | AWS、Anthropic关系、物流网络、数据中心资本开支、供应链与政府合同 |
| P0-004 | Meta Platforms, Inc. | 社交平台 / 广告 / AI | 上市集团 | 创始人投票控制、平台矩阵、AI基础设施、战略投资、广告与监管 |
| P0-005 | Apple Inc. | 终端 / 平台 / 服务 | 上市集团 | 全球供应链、服务收入、回购、AI合作、应用分发权力与监管 |
| P0-006 | NVIDIA Corporation | AI计算 / 半导体 | 上市集团 | GPU生态、客户与代工依赖、战略投资、网络设备、资本回报与平台控制 |
| P0-007 | OpenAI Group PBC | 基础模型 / AI平台 | 私营PBC；结构需持续核验 | 与OpenAI Foundation分离建模；股东、算力、云、商业分发、治理权和融资事件 |
| P0-008 | Anthropic PBC | 基础模型 / AI平台 | 私营PBC | Long-Term Benefit Trust、Amazon/Google等资本与云关系、算力承诺、融资与治理 |
| P0-009 | Space Exploration Technologies Corp. (SpaceX) | 航天 / 卫星 / AI集团 | 上市集团 | SpaceX—xAI—X链条、Starlink、政府合同、双重股权、债务、资本开支与并购 |
| P0-010 | X.AI Holdings Corp. / xAI operating entities | 基础模型 / 社交数据 / AI基础设施 | SpaceX集团子层级；法律实体需解析 | 与SpaceX及X Holdings的有效日期关系、Colossus算力、融资、数据与产品分发 |
| P0-011 | X Holdings Corp. / X Corp. | 社交平台 / 数据分发 | SpaceX集团下属链条；法律实体需解析 | 债务、平台现金流、广告、数据授权、xAI集成、治理与关联交易 |
| P0-012 | Tesla, Inc. | 汽车 / 能源 / AI / 机器人 | 上市集团 | 创始人生态、关联方、AI与机器人资本开支、能源业务、供应链和交叉投资 |
| P0-013 | Oracle Corporation | 数据库 / 云 / AI基础设施 | 上市集团 | OCI数据中心、AI客户与伙伴、债务融资、收购整合、能源与芯片依赖 |
| P0-014 | Broadcom Inc. | 半导体 / 基础设施软件 | 上市集团 | VMware整合、AI网络、客户集中度、债务、并购和平台议价权 |
| P0-015 | Advanced Micro Devices, Inc. | CPU / GPU / AI计算 | 上市集团 | AI加速器、代工和封装依赖、客户结构、收购与战略投资 |
| P0-016 | Intel Corporation | 半导体 / 晶圆代工 | 上市集团 | Foundry资本开支、政府补助、制造节点、资产重组、客户与供应链 |
| P0-017 | CoreWeave, Inc. | GPU云 / AI基础设施 | 上市/融资密集型平台 | 客户集中、GPU担保与债务、数据中心租约、电力承诺、供应商依赖 |
| P0-018 | Palantir Technologies Inc. | 数据软件 / 国防AI | 上市集团 | 政府合同、商业扩张、创始人控制、合作网络与政策影响 |
| P0-019 | BlackRock, Inc. | 资产管理 / 基础设施资本 | 上市资产管理集团 | 管理人、基金和受益所有权分离；13F/N-PORT/Form ADV、投票权与私募资产 |
| P0-020 | The Vanguard Group, Inc. | 资产管理 | 私营资产管理集团 | 基金持股与管理人权力分离；共同持股、代理投票、产品流量与治理影响 |
| P0-021 | State Street Corporation | 托管 / 资产管理 / 银行 | 上市金融集团 | State Street Global Advisors、托管资产、基金持股、投票与银行体系关系 |
| P0-022 | Berkshire Hathaway Inc. | 多元化控股 / 保险 / 投资 | 上市控股集团 | 运营子公司与证券投资组合分离；保险浮存金、资本配置、能源和铁路 |
| P0-023 | JPMorgan Chase & Co. | 银行 / 投行 / 资产管理 | 上市银行控股集团 | 贷款、承销、M&A顾问、托管、资产管理、交易对手与集团结构 |
| P0-024 | The Goldman Sachs Group, Inc. | 投行 / 资管 / 私募资本 | 上市金融集团 | 融资、承销、顾问、私募基金、交易对手、董事网络与战略投资 |
| P0-025 | Morgan Stanley | 投行 / 财富管理 / 资管 | 上市金融集团 | 资本市场中介、财富管理资金、13F、承销和重大企业关系 |
| P0-026 | Blackstone Inc. | 私募股权 / 信贷 / 基础设施 | 上市另类资管集团 | GP—基金—SPV—被投企业分层；数据中心、能源、地产和信贷关系 |
| P0-027 | Apollo Global Management, Inc. | 私募股权 / 私募信贷 / 保险 | 上市另类资管集团 | Apollo—Athene体系、私募信贷、保险资金、基础设施和企业融资 |
| P0-028 | Lockheed Martin Corporation | 国防 / 航空航天 | 上市集团 | 政府合同、项目依赖、分包商网络、游说、技术投资与供应链 |
| P0-029 | Constellation Energy Corporation | 核电 / 电力供应 | 上市能源集团 | 数据中心电力协议、核电资产、并购、监管与AI电力需求信号 |
| P0-030 | NextEra Energy, Inc. | 公用事业 / 可再生能源 | 上市能源集团 | 公用事业与开发平台分离、电网和数据中心需求、资本开支、融资与监管 |

### 2.3 P1：50 家扩展对象

| ID | 公司/组织 | 权力系统 | 初始形态（入库时复核） | 首要研究焦点 |
| --- | --- | --- | --- | --- |
| P1-031 | International Business Machines Corporation | 企业软件 / 混合云 / AI | 上市集团 | 企业AI、云与咨询分发、收购和专利 |
| P1-032 | Salesforce, Inc. | 企业软件 / 数据 / AI | 上市集团 | 平台生态、AI并购、资本回报与客户网络 |
| P1-033 | ServiceNow, Inc. | 企业软件 / 工作流 / AI | 上市集团 | 企业入口、AI合作、战略投资和客户集中 |
| P1-034 | Adobe Inc. | 创意软件 / 文档 / AI | 上市集团 | 订阅平台、生成式AI、内容版权和并购监管 |
| P1-035 | Cisco Systems, Inc. | 网络设备 / 安全 | 上市集团 | AI网络、收购整合、客户与供应链 |
| P1-036 | Dell Technologies Inc. | 服务器 / 企业硬件 | 上市集团 | AI服务器、供应链、融资和渠道 |
| P1-037 | Hewlett Packard Enterprise Company | 服务器 / 网络 / 企业基础设施 | 上市集团 | AI系统、网络、政府与企业客户 |
| P1-038 | Arista Networks, Inc. | 云网络 / 数据中心 | 上市集团 | 超大规模客户集中、AI网络和供应链 |
| P1-039 | Cloudflare, Inc. | 边缘网络 / 安全 / 开发者平台 | 上市集团 | 网络分发、AI推理、客户与数据治理 |
| P1-040 | CrowdStrike Holdings, Inc. | 网络安全 | 上市集团 | 平台集中度、政府和企业合同、事件风险 |
| P1-041 | Palo Alto Networks, Inc. | 网络安全 | 上市集团 | 并购整合、平台化、政府与企业关系 |
| P1-042 | Snowflake Inc. | 数据云 / AI | 上市集团 | 云依赖、数据平台、AI合作与客户 |
| P1-043 | Databricks, Inc. | 数据 / AI平台 | 私营；法律状态需核验 | 融资、云合作、收购、企业分发 |
| P1-044 | Stripe, Inc. | 支付基础设施 | 私营；法律状态需核验 | 支付流、银行伙伴、融资、平台依赖 |
| P1-045 | Uber Technologies, Inc. | 移动平台 / 物流 | 上市集团 | 平台网络、自动驾驶投资、监管与资本配置 |
| P1-046 | QUALCOMM Incorporated | 无线芯片 / 许可 | 上市集团 | 专利许可、终端客户、AI边缘计算 |
| P1-047 | Micron Technology, Inc. | 存储半导体 | 上市集团 | HBM、制造资本开支、政府补助和周期 |
| P1-048 | Marvell Technology, Inc. | 数据中心芯片 / 网络 | 上市集团 | 定制硅、云客户、并购和供应链 |
| P1-049 | Applied Materials, Inc. | 半导体设备 | 上市集团 | 晶圆厂资本开支、客户集中和出口管制 |
| P1-050 | Lam Research Corporation | 半导体设备 | 上市集团 | 先进制程投资、客户与政策风险 |
| P1-051 | KLA Corporation | 半导体设备 / 检测 | 上市集团 | 制造节点、客户和技术瓶颈 |
| P1-052 | Texas Instruments Incorporated | 模拟半导体 | 上市集团 | 制造扩张、工业/汽车需求和资本回报 |
| P1-053 | Synopsys, Inc. | EDA / 芯片IP | 上市集团 | 设计工具控制点、并购与客户依赖 |
| P1-054 | Cadence Design Systems, Inc. | EDA / 系统设计 | 上市集团 | 设计工具生态、AI辅助设计和客户 |
| P1-055 | GlobalFoundries Inc. | 晶圆代工 | 上市集团 | 美国制造、长期供货协议、政府支持 |
| P1-056 | Bank of America Corporation | 银行 / 投行 | 上市银行控股集团 | 贷款、承销、财富管理和企业关系 |
| P1-057 | Citigroup Inc. | 全球银行 / 交易服务 | 上市银行控股集团 | 跨境资金、托管、交易服务和重组 |
| P1-058 | Wells Fargo & Company | 银行 / 商业信贷 | 上市银行控股集团 | 企业信贷、监管限制和客户网络 |
| P1-059 | Fidelity Investments | 资产管理 / 经纪 | 私营金融集团 | 基金持股、经纪流量、私募投资和治理 |
| P1-060 | Capital Group | 资产管理 | 私营资产管理集团 | 基金持股、长期资本和代理投票 |
| P1-061 | T. Rowe Price Group, Inc. | 资产管理 | 上市资管集团 | 基金持股、私募成长投资和资金流 |
| P1-062 | The Charles Schwab Corporation | 经纪 / 托管 / 银行 | 上市金融集团 | 客户现金、托管、ETF与经纪流量 |
| P1-063 | KKR & Co. Inc. | 私募股权 / 信贷 / 基础设施 | 上市另类资管集团 | 基金/SPV、数据中心、能源和信贷 |
| P1-064 | The Carlyle Group Inc. | 私募股权 / 国防 / 基础设施 | 上市另类资管集团 | 基金、政府网络、国防与企业控制 |
| P1-065 | Ares Management Corporation | 私募信贷 / 另类资产 | 上市另类资管集团 | 私募信贷、基础设施和企业融资 |
| P1-066 | RTX Corporation | 国防 / 航空航天 | 上市集团 | 政府合同、航空供应链和分包网络 |
| P1-067 | Northrop Grumman Corporation | 国防 / 航天 | 上市集团 | 政府项目、导弹/太空资产和供应商 |
| P1-068 | The Boeing Company | 航空 / 国防 / 航天 | 上市集团 | 商业航空、国防合同、供应链和监管 |
| P1-069 | General Dynamics Corporation | 国防 / 船舶 / IT | 上市集团 | 政府合同、船舶与信息系统 |
| P1-070 | L3Harris Technologies, Inc. | 国防电子 / 通信 | 上市集团 | 并购、政府合同和关键电子供应链 |
| P1-071 | Anduril Industries, Inc. | 国防科技 / AI | 私营；法律状态需核验 | 融资、政府合同、传感器与自主系统 |
| P1-072 | Blue Origin, LLC | 航天 / 发射 / 基础设施 | 私营；法律状态需核验 | 创始人资本、政府合同、发射与供应链 |
| P1-073 | Exxon Mobil Corporation | 油气 / 化工 / 能源 | 上市集团 | 资本开支、并购、能源转型、政策与游说 |
| P1-074 | Chevron Corporation | 油气 / 能源 | 上市集团 | 并购、资本配置、能源政策与供应链 |
| P1-075 | GE Vernova Inc. | 电力设备 / 电网 / 发电 | 上市集团 | 电网瓶颈、燃机、核电/风电供应链与AI用电 |
| P1-076 | Vistra Corp. | 发电 / 零售电力 | 上市集团 | 电力资产、数据中心合同、并购与资本回报 |
| P1-077 | Duke Energy Corporation | 公用事业 | 上市集团 | 电网资本开支、费率监管和数据中心负荷 |
| P1-078 | Comcast Corporation | 宽带 / 媒体 | 上市集团 | 宽带基础设施、NBCUniversal、资本配置与监管 |
| P1-079 | AT&T Inc. | 通信 / 光纤 / 无线 | 上市集团 | 网络资本开支、频谱、债务和政府关系 |
| P1-080 | Verizon Communications Inc. | 通信 / 无线 / 光纤 | 上市集团 | 频谱、网络资本开支、债务和企业客户 |

### 2.4 P2：40 家观察对象

| ID | 公司/组织 | 权力系统 | 初始形态（入库时复核） | 首要研究焦点 |
| --- | --- | --- | --- | --- |
| P2-081 | Netflix, Inc. | 流媒体 / 内容 | 上市集团 | 内容支出、广告、云与分发依赖 |
| P2-082 | The Walt Disney Company | 媒体 / 乐园 / 流媒体 | 上市集团 | 内容IP、平台、董事治理、资本配置 |
| P2-083 | Warner Bros. Discovery, Inc. | 媒体 / 流媒体 | 上市集团；结构变化需监控 | 债务、资产重组、内容与分发 |
| P2-084 | T-Mobile US, Inc. | 无线通信 | 上市集团 | 控制股东、频谱、并购与网络资本开支 |
| P2-085 | Charter Communications, Inc. | 宽带 / 有线电视 | 上市集团 | 债务、网络投资、分发与监管 |
| P2-086 | Fox Corporation | 新闻 / 体育 / 媒体 | 上市集团 | 家族控制、内容权利与政治影响 |
| P2-087 | Nasdaq, Inc. | 交易所 / 市场基础设施 | 上市集团 | 上市、数据、清算和指数基础设施 |
| P2-088 | Intercontinental Exchange, Inc. | 交易所 / 清算 / 数据 | 上市集团 | 交易与清算、NYSE、数据和抵押生态 |
| P2-089 | CME Group Inc. | 衍生品交易所 | 上市集团 | 期货清算、风险集中和市场数据 |
| P2-090 | Capital One Financial Corporation | 银行 / 信用卡 | 上市金融集团 | 消费信贷、并购、数据与支付 |
| P2-091 | UnitedHealth Group Incorporated | 医疗保险 / 医疗服务 | 上市集团 | 保险—服务垂直整合、并购与监管 |
| P2-092 | Eli Lilly and Company | 制药 | 上市集团 | 研发、产能、定价、并购与供应链 |
| P2-093 | Johnson & Johnson | 医药 / 医疗器械 | 上市集团 | 分拆后结构、研发、诉讼和并购 |
| P2-094 | Pfizer Inc. | 制药 | 上市集团 | 研发、专利悬崖、并购与资本配置 |
| P2-095 | Merck & Co., Inc. | 制药 | 上市集团 | 研发管线、并购与产品集中 |
| P2-096 | AbbVie Inc. | 制药 | 上市集团 | 产品集中、并购与研发 |
| P2-097 | Thermo Fisher Scientific Inc. | 生命科学工具 | 上市集团 | 科研供应链、并购与客户网络 |
| P2-098 | Danaher Corporation | 生命科学 / 工业科技 | 上市集团 | 并购型资本配置、运营子公司网络 |
| P2-099 | Walmart Inc. | 零售 / 物流 / 金融服务 | 上市集团 | 供应链、广告、支付、云合作与劳动力 |
| P2-100 | Costco Wholesale Corporation | 零售 / 会员制 | 上市集团 | 供应链、会员现金流和资本配置 |
| P2-101 | The Home Depot, Inc. | 零售 / 建材 | 上市集团 | 供应链、专业客户、并购与回购 |
| P2-102 | The Procter & Gamble Company | 消费品 | 上市集团 | 品牌组合、广告、供应链与资本回报 |
| P2-103 | The Coca-Cola Company | 饮料 / 品牌授权 | 上市集团 | 装瓶体系、品牌控制和全球分销 |
| P2-104 | McDonald's Corporation | 餐饮 / 特许经营 / 地产 | 上市集团 | 特许网络、地产和供应链 |
| P2-105 | Honeywell International Inc. | 工业 / 航空 / 自动化 | 上市集团 | 分拆/组合调整、航空与工业技术 |
| P2-106 | Caterpillar Inc. | 工程机械 | 上市集团 | 矿业/基建周期、经销商和融资 |
| P2-107 | Deere & Company | 农业机械 / 软件 | 上市集团 | 设备、经销商、农业数据和融资 |
| P2-108 | GE Aerospace | 航空发动机 | 上市集团 | 航空供应链、服务收入和国防关系 |
| P2-109 | United Parcel Service, Inc. | 物流 | 上市集团 | 网络资本开支、大客户和劳动力 |
| P2-110 | FedEx Corporation | 物流 | 上市集团 | 网络重组、航空资产和大客户 |
| P2-111 | Union Pacific Corporation | 铁路 | 上市集团 | 物流基础设施、资本开支和监管 |
| P2-112 | Rocket Lab USA, Inc. | 航天 / 卫星 | 上市集团 | 政府合同、发射与卫星系统 |
| P2-113 | Shield AI, Inc. | 国防AI / 自主系统 | 私营；法律状态需核验 | 融资、政府合同、无人系统 |
| P2-114 | Scale AI, Inc. | 数据 / AI基础设施 | 私营/控制关系需核验 | 股权变化、平台客户、数据与政府合同 |
| P2-115 | Cerebras Systems, Inc. | AI芯片 / 计算系统 | 私营/上市状态需核验 | 融资、客户、供应链和算力合同 |
| P2-116 | Groq, Inc. | AI推理芯片 / 云 | 私营；法律状态需核验 | 融资、推理基础设施和客户 |
| P2-117 | Crusoe Energy Systems LLC | AI数据中心 / 能源 | 私营；法律状态需核验 | 能源—数据中心耦合、融资和客户 |
| P2-118 | Lambda, Inc. | GPU云 / AI基础设施 | 私营/上市状态需核验 | GPU融资、数据中心、电力与客户 |
| P2-119 | Figure AI, Inc. | 人形机器人 / AI | 私营；法律状态需核验 | 融资、制造伙伴、模型与客户 |
| P2-120 | Perplexity AI, Inc. | AI搜索 / 分发 | 私营；法律状态需核验 | 融资、分发、内容授权和平台竞争 |

### 2.5 X：20 个全球关键外部节点

| ID | 外部节点 | 角色 | 仅在何种关系下展开 |
| --- | --- | --- | --- |
| X-001 | Taiwan Semiconductor Manufacturing Company Limited (TSMC) | 晶圆代工 | NVIDIA/AMD/Apple等制造瓶颈与美国建厂 |
| X-002 | ASML Holding N.V. | 光刻设备 | 先进制程核心设备与出口管制 |
| X-003 | Samsung Electronics Co., Ltd. | 存储 / 代工 / 终端 | HBM、代工、终端和美国投资 |
| X-004 | SK hynix Inc. | 存储半导体 | HBM供应与AI计算链 |
| X-005 | Arm Holdings plc | 芯片架构 / IP | CPU架构授权和软银控制关系 |
| X-006 | Hon Hai Precision Industry Co., Ltd. (Foxconn) | 电子制造服务 | Apple/服务器等制造网络 |
| X-007 | SoftBank Group Corp. | 科技投资 / 控股 | Arm及美国AI投资网络 |
| X-008 | Sony Group Corporation | 内容 / 传感器 / 游戏 | 图像传感器、内容和平台关系 |
| X-009 | Tencent Holdings Limited | 平台 / 游戏 / 投资 | 美国科技与游戏资产投资关系 |
| X-010 | Alibaba Group Holding Limited | 云 / 电商 | 跨境云、电商与资本市场关系 |
| X-011 | ByteDance Ltd. | 短视频 / AI平台 | TikTok美国业务、监管与数据治理 |
| X-012 | Huawei Technologies Co., Ltd. | 通信 / 芯片 / 云 | 美国供应链、出口管制和竞争关系 |
| X-013 | Public Investment Fund of Saudi Arabia (PIF) | 主权资本 | 美国科技、娱乐、体育与基础设施投资 |
| X-014 | MGX | 主权支持科技投资 | 美国AI融资和基础设施资本 |
| X-015 | Mubadala Investment Company | 主权资本 | 半导体、AI和私募资本关系 |
| X-016 | Qatar Investment Authority (QIA) | 主权资本 | 美国科技、地产和融资关系 |
| X-017 | GIC Private Limited | 主权资本 | 美国私募、科技和基础设施投资 |
| X-018 | Temasek Holdings | 主权资本 | 美国科技与金融资产关系 |
| X-019 | Brookfield Asset Management Ltd. | 基础设施 / 私募资本 | 数据中心、电力和美国资产 |
| X-020 | Schneider Electric SE | 电力设备 / 数据中心 | 数据中心配电、能效和供应链 |

### 2.6 必须单独建模的特殊结构

| 特殊结构 | 建模要求 | 当前基准说明 |
| --- | --- | --- |
| OpenAI | `OpenAI Foundation`、`OpenAI Group PBC`、董事会、股东和商业伙伴均为独立节点 | OpenAI 官方说明 Foundation 控制 Group PBC，并拥有特殊治理权；不得把“OpenAI”做成一个扁平公司节点。 |
| SpaceX—xAI—X | SpaceX、X.AI Holdings、xAI运营实体、X Holdings/X Corp、Starlink品牌/法律实体分层 | SEC 文件显示 X Holdings 于 2025-03-28 被 xAI 收购，X.AI Holdings 于 2026-02-02 被 SpaceX 收购；关系必须带有效日期，不能覆盖历史。 |
| Anthropic | Anthropic PBC、Long-Term Benefit Trust、董事和投资人分离 | Trust 是治理机制，不是普通股东；经济权益与治理权必须分列。 |
| 资产管理机构 | 管理人、基金、ETF/共同基金系列、托管人、受益所有人和投票代理分离 | 13F 报告管理人持仓；N-PORT报告基金组合；不能把所有基金持股直接归因母公司经济所有。 |
| 私募股权/信贷 | 上市管理公司、GP、基金、SPV、保险资金和被投企业分离 | “Blackstone/Apollo/KKR 持有某公司”必须解析到具体基金/SPV及权利类型。 |
| Berkshire Hathaway | 运营子公司、控股链和证券投资组合分离 | 全资控制与公开市场少数投资的权力含义完全不同。 |
| 品牌与法律实体 | Google/YouTube/AWS/Starlink/X等品牌不能直接替代法律主体 | 前端可展示品牌，但证据边必须落到可识别法律实体；无法解析时标记 `needs_resolution`。 |

## 3. 研究对象与关系分类

### 3.1 实体对象

| 对象类型 | 例子 | 必须回答的问题 |
| --- | --- | --- |
| 法律实体 | 母公司、子公司、合资公司、SPV | 成立法域、存续状态、直接/最终母公司、有效期 |
| 非营利/信托/PBC治理体 | OpenAI Foundation、Anthropic Trust | 有何任命权、否决权、受托义务和经济权益 |
| 品牌/产品/平台 | Google Cloud、AWS、Starlink、X | 对应哪些法律主体、收入/合同/用户归属何处 |
| 个人 | 创始人、董事、高管、关键投资人 | 职务、任期、持股、投票权、董事交叉任职、关联交易 |
| 投资管理人 | BlackRock、Vanguard、KKR管理公司 | 管理哪些资金、是否具有投资/投票裁量权 |
| 基金/ETF/SPV | 具体基金和并购车辆 | 谁管理、谁出资、持有何种证券、期限与权利 |
| 证券/工具 | 普通股、优先股、债券、可转债、认股权证 | 数量、价格、优先权、转换权、到期、担保和投票权 |
| 合同/政府奖励 | 云合同、采购承诺、联邦合同 | 当事方、金额类型、期限、义务、上限、已发生金额 |
| 设施/资产 | 晶圆厂、数据中心、电厂、卫星星座 | 所有者、运营者、容量、电力、融资与关键供应商 |
| 专利/技术簇 | GPU互连、模型训练、机器人 | assignee、发明人、技术分类、转让与许可 |
| 政府机构/监管体 | SEC、FTC、DOJ、FCC、DOE、DOD | 监管、合同、批准、处罚或政策关系 |
| 事件 | 融资、并购、董事变更、合同、诉讼 | 宣布、签署、批准、完成、终止等状态与时间 |
| 证据 | filing、合同、公告、数据记录 | 原始来源、定位、哈希、置信度、修订和冲突 |

### 3.2 关系对象

| 关系族 | 关系类型示例 | 关键属性 |
| --- | --- | --- |
| 所有权 | owns、beneficially_owns、economic_interest | 经济比例、证券类别、直接/间接、报告基数、日期 |
| 控制权 | controls、appoints_director、veto_right、governs | 投票比例、任命权、否决事项、有效期 |
| 资本 | invests_in、lends_to、underwrites、guarantees | 金额、工具、利率、期限、担保、交割状态 |
| 并购 | acquires、merges_with、divests、spins_off | 对价、状态、有效日期、监管条件 |
| 经营依赖 | supplies、buys_from、hosts_on、licenses_to | 金额/占比、独家性、期限、替代难度 |
| 战略合作 | partners_with、joint_venture、distribution | 权利义务、地域、产品、收入分成 |
| 人员治理 | director_of、executive_of、former_employee_of | 职务、任期、独立性、交叉任职 |
| 政府关系 | awarded_by、regulated_by、lobbies、investigated_by | agency、award/filing/case ID、金额、阶段 |
| 技术/IP | owns_patent、licenses_ip、depends_on_standard | 专利族、许可范围、技术簇和有效期 |
| 数据/平台 | provides_data_to、distributes_for、integrates_with | 数据种类、API/平台、排他性和撤销条件 |
| 证据关系 | supported_by、contradicted_by、superseded_by | 来源级别、证据定位、置信度和修订链 |

## 4. 数据来源列表与优先级

### 4.1 来源分级规则

- **A 级：监管、法律和政府原始数据**。可作为事实层主证据。
- **B 级：公司或交易对手官方披露**。可作为事实层证据，但涉及自身宣传时需交叉核验。
- **C 级：商业数据服务**。用于加速实体解析、估值和私募研究；必须遵守许可，不是开源 MVP 的硬依赖。
- **D 级：专业新闻和调查报道**。用于发现线索、补充背景和形成待验证假设；不单独支撑精确控制权数字。

### 4.2 来源注册表
| 代码 | 来源 | 主要信息 | 限制/工程要求 | 阶段 | 官方入口 |
| --- | --- | --- | --- | --- | --- |
| A01 | SEC EDGAR Submissions API | 公司申报历史、表单、accession、CIK | 无需API key；声明User-Agent；限速不高于10 req/s | MVP必选 | https://www.sec.gov/search-filings/edgar-application-programming-interfaces |
| A02 | SEC Companyfacts / XBRL API | 标准化财务事实、期间值、单位与申报链接 | 概念映射不完整；必须保留原始tag和期间 | MVP必选 | https://data.sec.gov/ |
| A03 | EDGAR Full-Text / Latest Filings / RSS | 事件发现、全文检索、增量抓取 | 需去重、修订覆盖和表单分类 | MVP必选 | https://www.sec.gov/search-filings |
| A04 | 10-K / 10-Q / 8-K / 20-F / 6-K | 财务、风险、分部、重大事件、合同与承诺 | 披露口径与时间滞后不同 | MVP必选 | https://www.sec.gov/edgar/search/ |
| A05 | DEF 14A / 信息声明 | 董事、薪酬、关联交易、投票权、受益所有权 | 一年一度为主；需结合最新8-K | MVP必选 | https://www.sec.gov/edgar/search/ |
| A06 | S-1 / S-4 / 424B / 并购附件 | IPO、资本结构、风险、并购协议、子公司清单 | 交易状态须区分拟议/签署/完成 | MVP必选 | https://www.sec.gov/edgar/search/ |
| A07 | Schedules 13D / 13G | 超过5%的受益所有权与控制意图 | 不是完整股东名册；修订和衍生品需处理 | MVP必选 | https://www.sec.gov/resources-small-businesses/going-public/officers-directors-10-shareholders |
| A08 | Forms 3 / 4 / 5 | 董事、高管、10%股东交易和持仓 | Form 4通常在交易后两个工作日；代码需解释 | MVP必选 | https://www.sec.gov/files/forms-3-4-5.pdf |
| A09 | Form 13F Data / Filings | 机构管理人季度末披露持仓 | 最长可在季末后45天申报；只可称为持仓快照变化，不可称实时资金流 | MVP必选 | https://www.sec.gov/rules-regulations/staff-guidance/division-investment-management-frequently-asked-questions/frequently-asked-questions-about-form-13f |
| A10 | Form N-PORT Data Sets | 注册基金月度组合数据的公开部分 | 公开与申报节奏不同；基金、系列和管理人需分离 | Phase 1.5 | https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets |
| A11 | IAPD / Form ADV | 投资顾问的所有权、业务、客户、关联方、AUM与纪律事项 | 管理人和基金车辆不能混为一体 | Phase 1.5 | https://adviserinfo.sec.gov/ |
| A12 | Form D / D-A | 私募证券发行通知、发行规模、投资者数量等 | 不是完整融资闭环；金额可为计划值 | Phase 1.5 | https://www.sec.gov/edgar/search/ |
| A13 | USAspending API v2 | 联邦合同、补助、贷款、recipient、agency、obligation/outlay | award ceiling、obligation、outlay必须分开 | Phase 1.5 | https://api.usaspending.gov/ |
| A14 | SAM.gov Public Data / UEI | 政府供应商实体、UEI、排除和部分责任信息 | 只使用公开API/公开字段；遵守数据用途限制 | Phase 1.5 | https://sam.gov/entity-information |
| A15 | LDA.gov Lobbying Disclosure API | 注册、客户、议题、机构、游说支出和贡献报告 | 旧站点将在2026-06-30后下线；新实现使用LDA.gov | Phase 1.5 | https://lda.gov/ |
| A16 | OpenFEC API | PAC、委员会、候选人及政治捐款披露 | 公司、PAC、个人和高管贡献需分开；需API key | Phase 2 | https://api.open.fec.gov/developers/ |
| A17 | USPTO Open Data Portal | 专利申请、授权、assignee、文档和技术分类 | assignee实体解析和转让历史需要审阅 | Phase 1.5 | https://data.uspto.gov/ |
| A18 | FTC Competition Enforcement Database | 公开并购与非并购执法事件 | 只反映公开执法，不代表所有审查活动 | Phase 1.5 | https://www.ftc.gov/competition-enforcement-database |
| A19 | DOJ Antitrust Case Filings | 反垄断案件、诉状、和解、判决与行业分类 | 案件状态和救济结果需时间建模 | Phase 1.5 | https://www.justice.gov/atr/antitrust-case-filings |
| A20 | Federal Register API | 拟议规则、最终规则、行政通知和机构文件 | FederalRegister.gov展示版与正式PDF/法规文本需区分 | Phase 2 | https://www.federalregister.gov/developers/documentation/api/v1 |
| A21 | FCC ECFS / Public API | 通信监管案卷、许可与公开评论 | 案卷实体匹配和附件解析成本较高 | Phase 2 | https://www.fcc.gov/ecfs/help/public_api |
| A22 | EIA Open Data API | 电力、燃料、发电、价格、设施和能源趋势 | 多为行业/设施级，不直接等于公司合同流 | Phase 1.5 | https://www.eia.gov/opendata/ |
| A23 | IRS TEOS / Form 990 XML | 非营利实体状态、治理、财务与关联组织 | 年度滞后；适用于基金会与非营利控制节点 | Phase 1.5 | https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-bulk-data-downloads |
| A24 | GLEIF LEI API / Level 2 | 法律实体标识、直接/最终会计合并母公司、模糊匹配 | 覆盖并非完整；会计合并不等于所有控制关系 | Phase 1.5 | https://www.gleif.org/en/lei-data/gleif-api |
| A25 | FFIEC National Information Center / FR Y-9C | 银行控股结构和合并财务 | 专用于受监管金融机构；字段和报告口径专业 | Phase 1.5 | https://www.ffiec.gov/npw |
| A26 | FDIC BankFind API | 银行历史、并购、分支、财务和机构标识 | 银行子体与顶层控股公司需映射 | Phase 1.5 | https://api.fdic.gov/banks/docs |
| A27 | FINRA TRACE / Fixed Income Data | 公司债券参考数据、市场聚合和部分交易历史 | 部分数据需协议/认证或付费；不等同发行人现金流 | Phase 2 | https://www.finra.org/filing-reporting/trace |
| A28 | 州公司注册处 / UCC / 州级监管数据库 | 成立、存续、合并、担保权益和州级许可 | 各州格式、访问和许可差异大；先做人工研究队列 | Phase 2 | state-specific |
| B01 | 公司IR、官方新闻室、治理文件、投资者演示 | 战略、融资、合同、组织与产品发布 | 自述性来源，必须与监管/合同文件交叉核验 | MVP必选 | source-specific |
| B02 | 官方合作方公告与政府机构新闻稿 | 双边合作、合同、投资和审批 | 区分宣布、承诺、签署、交割和实际支出 | MVP必选 | source-specific |
| C01 | Bloomberg / LSEG / FactSet / S&P Capital IQ | 实体主数据、交易、资本结构、估值与市场数据 | 商业许可；不可成为开源MVP硬依赖 | 可选付费 | licensed |
| C02 | PitchBook / Preqin / Crunchbase | 私募融资、基金、投资人与交易线索 | 私营公司数据可能估算或不完整；需原始文件复核 | 可选付费 | licensed |
| C03 | AlphaSense / Tegus等研究平台 | 文件检索、电话会与研究工作流 | 许可和再分发限制；仅作分析辅助 | 可选付费 | licensed |
| D01 | Reuters / FT / WSJ / Bloomberg News / The Information | 事件发现、背景和未公开细节线索 | 不能单独支撑精确股权比例或法律事实；至少双源或回到原始文件 | 二级佐证 | publisher-specific |

### 4.3 来源使用的强制规则

1. 所有金额都要区分 **计划值、承诺值、签约值、已交割值、义务额、支出额和潜在上限**。
2. 所有存量数据必须带 `as_of_date`；所有期间数据必须带 `report_period_start/end`。
3. 13F 只能表述为“报告持仓/报告持仓变化”。SEC 规定相关管理人通常可在季度结束后 45 天内申报，因此它不是实时流量。
4. Form 4 多数交易在交易后两个工作日内申报；仍要区分交易日和申报日。
5. 超过 5% 的受益所有权通常触发 Schedule 13D/13G，但它不是完整股东名册，也不能覆盖所有衍生经济暴露。
6. 公司公告中的“投资、合作、价值、规模”必须拆成法律当事方、金额类型、签约状态和有效日期。
7. 若一级来源之间矛盾，记录冲突并保留两个版本；不得用“最后抓到的值”静默覆盖。
8. 禁止将新闻、社交媒体或搜索摘要直接写入事实层；它们只能进入 `research_queue`。

## 5. 关键指标目录

> 指标的目的不是堆数量，而是把“权力、资本、依赖、政策和战略信号”变成可解释、可追溯、可比较的结构化变量。

| 代码 | 指标 | 定义/公式 | 主要来源 | 回答的问题 |
| --- | --- | --- | --- | --- |
| C-01 | 经济所有权比例 | 持有人经济权益 / 对应证券完全稀释基数 | 13D/G、proxy、S-1/S-4、公司公告 | 控制者实际经济暴露 |
| C-02 | 投票权比例 | 可控制票数 / 总投票权 | proxy、章程、并购文件 | 控制权而非单纯持股 |
| C-03 | 控制权楔子 | 投票权% - 经济所有权% | C-01、C-02 | 识别双重股权和少量资本高控制 |
| C-04 | 5%受益所有权事件 | 跨越/跌破5%及13D/G修订 | 13D/G | 重要股东与控制意图变化 |
| C-05 | 内部人持股比例 | 董事、高管及10%持有人持仓 / 基数 | proxy、Forms 3/4/5 | 内部人利益绑定 |
| C-06 | 前十大机构持股比例 | 前10名报告机构持仓合计 / 流通基数 | 13F、N-PORT、公司披露 | 机构集中度；注意时滞 |
| C-07 | 所有权HHI | Σ(持有人比例²) | 13F、13D/G、proxy | 所有权集中程度 |
| C-08 | 董事席位控制 | 被特定股东/基金/创始人提名或控制的席位数 | proxy、投资协议、章程 | 治理权的直接表现 |
| C-09 | 董事交叉任职数 | 同一人在两个实体的同期董事/高管连接数 | proxy、官方履历 | 集团间软控制与信息通道 |
| C-10 | 关联交易强度 | 关联交易金额 / 收入或资产 | proxy、10-K、8-K | 内部资本转移与利益冲突 |
| F-01 | 股权融资额 | 期间内已交割股权/可转证券融资总额 | S-1、8-K、Form D、官方公告 | 外部资本输入 |
| F-02 | 债务发行额 | 期间内新发债券、贷款和信贷工具本金 | 10-K/Q、8-K、债券文件 | 杠杆扩张 |
| F-03 | 债务偿还额 | 期间内到期、回购或提前偿还本金 | 现金流量表、债务注释 | 去杠杆和再融资 |
| F-04 | 净外部融资 | 股权融资 + 债务发行 - 债务偿还 - 回购 - 股息 | F-01至F-03、财务报表 | 集团净吸收/返还资本 |
| F-05 | 股票回购 | 期间回购现金支出及授权余额 | 10-Q/K、8-K | 资本返还与每股收益工程 |
| F-06 | 股息支出 | 现金股息与特别股息 | 现金流量表、公告 | 资本返还 |
| F-07 | 并购资本部署 | 已完成交易对价；现金/股票/债务分拆 | S-4、8-K、10-K、官方公告 | 外部扩张方向 |
| F-08 | 战略少数股权投资 | 非控制投资金额与权利 | 10-K、8-K、Form D、公告 | 联盟、供应保障和未来控制期权 |
| F-09 | 资本开支 | 购置物业设备及资本化项目支出 | 现金流量表、XBRL、指引 | 真实资源投入 |
| F-10 | 研发支出 | 期间研发费用 | 10-K/Q、XBRL | 技术投资强度 |
| F-11 | 资本开支强度 | 资本开支 / 收入 | F-09、收入 | 基础设施扩张速度 |
| F-12 | 研发强度 | 研发 / 收入 | F-10、收入 | 技术路线下注 |
| F-13 | 自由现金流 | 经营现金流 - 资本开支；保留公司自定义口径 | 财务报表 | 内部融资能力 |
| F-14 | 13F持仓变化 | 本季报告股数/价值 - 上季报告股数/价值 | 13F | 仅表示报告持仓变化，不等同买入卖出现金流 |
| F-15 | 内部人净交易 | 公开市场购买金额 - 公开市场出售金额；排除授予/税款扣缴后另列 | Form 4 | 内部人行为信号 |
| D-01 | 客户集中度 | 最大客户或前N客户收入占比 | 10-K、招股书 | 议价与需求依赖 |
| D-02 | 供应商集中度 | 关键供应商、代工、GPU/云/能源依赖比例或等级 | 10-K、合同、公告 | 供应瓶颈和议价风险 |
| D-03 | 云/算力依赖指数 | 按计算、托管、芯片、云承诺加权的供应商集中度 | 合同、10-K、合作公告 | AI公司的真实基础设施依赖 |
| D-04 | 数据中心/电力承诺 | 已披露MW、长期购电、租赁和最低采购承诺 | 合同、10-K、能源公告 | 未来AI基础设施扩张 |
| D-05 | 采购义务 | 不可取消采购和服务承诺 | 10-K/Q注释 | 未来现金流锁定 |
| D-06 | 积压订单/合同收入 | backlog、remaining performance obligations、政府合同积压 | 10-K/Q、投资者材料 | 未来收入可见度 |
| S-01 | 专利簇增长 | 技术分类簇近3年授权/申请增长率 | USPTO | 研发方向而非单纯专利数量 |
| S-02 | 高价值专利信号 | 被引、家族规模、权利要求和关键技术簇综合分 | USPTO、商业专利库 | 技术壁垒 |
| S-03 | 招聘/组织扩张代理 | 官方职位、员工数和职能分布变化 | 10-K、官方招聘；低置信度 | 资源投入的辅助信号 |
| G-01 | 联邦合同义务额 | obligation按recipient和agency汇总 | USAspending | 政府需求和政策关系 |
| G-02 | 联邦合同潜在上限 | current/potential award amount，单独展示 | USAspending、合同文件 | 不能与已发生支出混同 |
| G-03 | 游说支出 | 按客户、议题、季度/年度汇总 | LDA | 政策影响投入 |
| G-04 | 政治资金暴露 | 企业PAC、高管和关联委员会分层汇总 | FEC | 政治关系；不得把个人捐款直接归因公司 |
| G-05 | 监管/执法严重度 | 调查、投诉、诉讼、和解、禁令、罚款按阶段加权 | FTC、DOJ、SEC、FCC等 | 法律与政策约束 |
| G-06 | 反垄断交易状态 | 未申报/申报/二次请求/起诉/和解/放弃/完成 | FTC、DOJ、公司文件 | 并购完成概率与结构性约束 |
| N-01 | 加权度中心性 | 节点所有入边/出边权重之和 | 证据图 | 直接关系密度 |
| N-02 | 介数中心性 | 最短路径中经过节点的比例 | 证据图 | 中介与瓶颈权力 |
| N-03 | PageRank / 特征向量中心性 | 由高影响节点连接加权 | 证据图 | 网络声望与系统重要性 |
| N-04 | 共同所有权重叠 | 两个公司共享机构持有人权重的Jaccard/余弦相似度 | 13F、N-PORT | 资本共同控制环境 |
| N-05 | 依赖集中度 | 客户、供应商、云、能源等边权HHI | 证据图 | 单点依赖风险 |
| N-06 | 社群/集团归属 | Louvain/Leiden社群 + 法律集团标签 | 证据图 | 发现隐性联盟和产业集群 |
| N-07 | 到核心节点最短路径 | 目标到P0节点的最短可信路径 | 证据图 | 一家公司进入权力网络的路径 |
| Q-01 | 事件速度 | 30/90日内新增重大事件数与加权分 | 事件表 | 战略变化加速 |
| Q-02 | 战略信号分 | 资本开支、并购、融资、专利、招聘、合同和监管的可解释加权分 | 多源 | 用于假设排序，不作为价格预测结论 |
| Q-03 | 证据置信度 | 来源级别、直接性、时效、交叉验证和解析质量综合0-100 | provenance | 区分事实、推断和线索 |
| Q-04 | 新鲜度年龄 | 当前时间 - observed_at/filing_at | 所有来源 | 提示数据过期 |
| Q-05 | 披露滞后 | filed_at - report_period_end / event_effective_at | 所有来源 | 避免把迟报信息当实时 |
| Q-06 | 冲突计数 | 同一事实存在的未解决矛盾数 | provenance | 暴露不确定性 |
| Q-07 | 证据覆盖率 | 有一级证据的关键字段 / 应有关键字段 | provenance | 衡量研究完整性 |

### 5.1 战略信号分的默认构成（0–100，不用于直接给出买卖结论）

| 维度 | 权重 | 正向/变化信号示例 | 反向或风险信号示例 |
| --- | ---: | --- | --- |
| 资本配置 | 25 | 资本开支、研发、并购、战略投资持续加速 | 依赖高杠杆、回购挤压研发、项目取消 |
| 供应链与基础设施 | 20 | 算力、电力、晶圆、网络和产能获得长期保障 | 单一供应商、能源瓶颈、关键合同终止 |
| 市场与商业依赖 | 15 | 客户多元化、积压订单、长期合同增加 | 单一客户占比高、平台被替代、价格压力 |
| 技术与人才 | 15 | 高价值专利簇、关键团队和产品节奏增强 | 关键人员流失、技术路线受限 |
| 政府与政策 | 10 | 获得重大合同、许可、补助或政策支持 | 反垄断诉讼、出口限制、重大罚款 |
| 网络位置 | 10 | 介数/PageRank上升、成为跨行业枢纽 | 关键连接断裂、社群边缘化 |
| 证据质量 | 5 | 多个一级来源一致、时效高 | 主要依赖传闻或冲突未解决 |

**解释要求**：任何总分都必须同时展示分项、原始事件、来源和反例。不得只显示一个“神秘综合分”。

## 6. 关键参数与数据字典

| 字段 | 类型 | 要求 | 规则 |
| --- | --- | --- | --- |
| entity_id | UUID/稳定键 | 必填 | 内部稳定主键；不得用ticker作主键 |
| canonical_name | text | 必填 | 法律/规范名称 |
| entity_type | enum | 必填 | legal_entity / brand / fund / person / agency / security / facility / nonprofit / trust |
| parent_entity_id | UUID | 条件必填 | 仅表达已证实的直接法律/会计父级；复杂关系用edge |
| cik | string | 可选 | SEC中央索引键，左侧补零保存 |
| lei | string | 可选 | 法律实体识别码 |
| ein | string | 受限可选 | 仅来自公开合规来源 |
| ticker_exchange | object | 可选 | ticker、exchange、valid_from/to；支持历史变更 |
| uei | string | 可选 | SAM.gov Unique Entity ID |
| jurisdiction | string | 必填 | 成立法域，不等于总部 |
| legal_status | enum | 必填 | active / dissolved / merged / acquired / unknown |
| source_entity_id | UUID | 关系必填 | 边的起点 |
| target_entity_id | UUID | 关系必填 | 边的终点 |
| relationship_type | enum | 关系必填 | owns / controls / invests / lends / supplies / buys_from / partners / appoints / regulates / contracts_with 等 |
| relationship_subtype | string | 可选 | 例如economic_ownership、voting_control、cloud_dependency |
| directness | enum | 必填 | direct / indirect / look-through / inferred |
| economic_ownership_pct | decimal | 可选 | 必须同时记录basis和as_of_date |
| voting_power_pct | decimal | 可选 | 与经济所有权分开 |
| board_seats | integer | 可选 | 已控制/提名席位 |
| amount_original | decimal | 可选 | 原始金额 |
| currency_original | string | 可选 | ISO货币 |
| amount_usd | decimal | 可选 | 使用指定汇率日换算 |
| instrument_type | enum | 可选 | common / preferred / convertible / debt / warrant / option / contract / grant |
| transaction_status | enum | 必填 | rumor不入事实层；proposed / announced / signed / approved / closed / terminated |
| report_period_start/end | date | 条件必填 | 期间型数据 |
| as_of_date | date | 条件必填 | 存量/比例/持仓快照 |
| announced_at | datetime | 可选 | 对外宣布时间 |
| effective_at | datetime | 可选 | 法律/交易生效时间 |
| filed_at | datetime | 可选 | 监管申报时间 |
| observed_at | datetime | 必填 | 来源页面/数据所代表的观察时间 |
| ingested_at | datetime | 必填 | 系统抓取时间 |
| source_tier | enum | 必填 | A监管/法律、B官方自述、C商业数据、D新闻佐证 |
| source_url | text | 必填 | 可复核原始链接 |
| accession_or_document_id | string | 优先必填 | SEC accession、award ID、filing UUID等 |
| source_locator | string | 优先必填 | 页码、章节、表格或XBRL fact定位 |
| evidence_excerpt_hash | string | 建议必填 | 证据片段哈希，避免全文版权复制 |
| confidence_score | integer 0-100 | 必填 | 机器+规则初分，人工可覆盖并留日志 |
| review_status | enum | 必填 | unreviewed / machine_verified / human_verified / disputed |
| supersedes_record_id | UUID | 可选 | 修订、重述和更正链 |
| stale_after_days | integer | 必填 | 按来源类型配置 |
| last_verified_at | datetime | 必填 | 最近一次复核 |
| contradiction_flag | boolean | 必填 | 存在冲突时不得静默覆盖 |
| notes | text | 可选 | 仅记录结构化字段无法表达的限定 |

### 6.1 时间字段的最低要求

一个“融资/持股/并购/合同”事实至少要区分：

- `report_period_end`：数据代表的报告期末。
- `transaction_date`：交易发生日。
- `announced_at`：对外宣布日。
- `filed_at`：监管申报日。
- `effective_at`：法律生效或交割日。
- `observed_at`：来源数据的观察时点。
- `ingested_at`：系统抓取时点。

这些字段不能合并为一个 `date`。否则系统会把历史持仓、迟报文件和即时事件混成“今天发生的资金流”。

### 6.2 置信度分层

| 分数 | 显示策略 | 含义 |
| ---: | --- | --- |
| 90–100 | 可作为“已证实事实”展示 | 直接一级来源，实体和时间明确，已交叉校验或人工复核 |
| 80–89 | 可展示，标注来源和限制 | 单一强一级来源或两个一致二级来源 |
| 60–79 | 只以“推断/待核验”展示 | 间接证据、实体解析或金额状态仍有不确定性 |
| 40–59 | 仅进入研究队列 | 有线索但不足以入图作为事实 |
| 0–39 | 默认丢弃或隔离 | 传闻、无法定位、来源冲突严重或违反合规要求 |

## 7. 筛选门槛

### 7.1 公司/组织纳入门槛

实体满足“相关性评分”并至少命中一个规模或结构条件。所有阈值均应配置化，不写死在代码中。

#### A. 上市公司默认门槛：命中任一项

- 最新可得市值 **≥ 500 亿美元**；或
- 年收入 **≥ 250 亿美元**；或
- 金融机构总资产 **≥ 2,500 亿美元**；或
- 传统资产管理 AUM **≥ 5,000 亿美元**；另类资管 AUM **≥ 1,000 亿美元**；或
- 最近年度研发 + 资本开支 **≥ 50 亿美元**；或
- 近三年联邦奖励义务额 **≥ 10 亿美元**；或
- 属于某关键系统的前五名控制点；或
- 存在双重股权、创始人控制、非营利/PBC/信托控制、复杂集团或国家安全等结构性覆盖理由。

#### B. 私营公司默认门槛：命中任一项

- 最新可靠披露估值 **≥ 200 亿美元**；或
- 累计公开融资 **≥ 30 亿美元**；或
- 年收入/合同规模 **≥ 50 亿美元**；或
- 近三年联邦奖励义务额 **≥ 5 亿美元**；或
- 与至少 **2 个 P0 节点**存在已证实的股权、控制、算力、云、供应、政府合同或关键分发关系；或
- 在AI模型、芯片、数据中心、电力、国防、支付或通信中构成不可替代控制点。

#### C. 子公司/品牌展开门槛：命中任一项

- 独立 SEC 申报人、独立债务发行人或受单独监管；
- 收入、资产、资本开支或合同规模达到集团 **5%**；
- 拥有关键牌照、核心IP、数据、客户、供应或政府合同；
- 发生控制权、融资、诉讼、分拆或出售事件；
- 用户需要追踪的核心品牌，但必须映射到法律实体。

### 7.2 相关性评分（0–100）

| 维度 | 权重 | 评分依据 |
| --- | ---: | --- |
| 经济规模 | 20 | 市值、收入、资产、AUM、估值、合同规模 |
| 控制复杂度 | 20 | 双重股权、创始人、信托/PBC/非营利、层级数量、关联交易 |
| 资本流强度 | 20 | 融资、并购、资本开支、研发、私募信贷和回购 |
| 网络中心性 | 15 | 跨行业边数、关键客户/供应商、共同所有权和政府连接 |
| 战略信号密度 | 15 | AI、芯片、能源、云、国防、通信和平台控制点 |
| 数据可得性 | 10 | SEC/政府/官方资料覆盖度、实体解析和历史可比性 |

- **P0**：≥ 75 分，或用户指定/结构性强制纳入。
- **P1**：60–74 分。
- **P2**：45–59 分，或与 P0 存在高重要性一跳关系。
- **低于 45 分**：默认不进入公司池，只作为事件或供应链节点存在。

### 7.3 关系入图门槛

| 关系 | 原始层 | 默认前端显示门槛 | 强制覆盖例外 |
| --- | --- | --- | --- |
| 所有权 | 尽可能保存公开可得全部记录 | ≥5%受益所有权；或P0公司前20机构持有人；或≥1%且金额显著 | 任命权、否决权、董事席位、创始人/内部人，不受比例门槛限制 |
| 私募融资/少数投资 | 保存所有有一级证据的轮次 | 一般 ≥5亿美元；前沿私营公司 ≥1亿美元 | 带独家、优先购买、董事席位、云/算力/供应权时全部显示 |
| 并购 | 保存所有已证实交易 | ≥5亿美元或≥收购方企业价值/收入1% | 任何控制权变化、核心IP/数据/分发收购全部显示 |
| 债务/信贷 | 保存主要工具 | ≥10亿美元或≥总债务5% | 可转债、担保、GPU/资产抵押、关联方贷款全部显示 |
| 客户/供应商 | 保存披露关系 | 单一客户≥收入10%，或关键供应商/sole-source | 云、GPU、晶圆、能源、数据、政府关键依赖全部显示 |
| 资本开支/采购承诺 | 保存披露值 | ≥10亿美元或≥年度资本开支10% | 数据中心、电力、晶圆、网络和国防产能合同全部显示 |
| 政府奖励 | 保存 award 级记录 | 单笔≥1亿美元或近3年义务额≥5亿美元 | 国家安全、关键基础设施、AI模型或发射合同全部显示 |
| 游说 | 保存P0/P1相关申报 | 年度≥500万美元或行业前10% | 反垄断、AI、芯片、能源、通信、国防等关键议题全部显示 |
| 内部人交易 | 保存全部Form 4原始记录 | 单笔≥100万美元或30日持仓变化≥10% | 公开市场买入、控制人交易和异常集中交易全部显示 |
| 13F变化 | 保存快照 | 持仓≥5亿美元；或管理人前20大持仓；或股数QoQ变化≥25%且价值≥1亿美元 | 控制/维权意图必须回到13D/G，不用13F替代 |
| 监管/诉讼 | 保存案件状态 | 正式投诉、禁令、和解、并购挑战；罚款≥1,000万美元 | 影响控制权、业务许可或核心产品的案件全部显示 |

### 7.4 重大事件告警门槛

以下任一事件触发 P0/P1 高优先级研究任务：

1. 控制人、投票权、董事任命或 5%受益所有权跨越。
2. 新融资、债务、担保、资本承诺或并购对价 ≥ 10 亿美元。
3. 资本开支或研发同比变化 ≥ 20%，且绝对变化 ≥ 10 亿美元。
4. 新增/终止关键云、芯片、能源、数据、政府或分发合同。
5. 单一客户/供应商依赖跨越 10% 或出现重大中断。
6. 正式反垄断投诉、第二次请求、禁令、重大和解、出口限制或牌照变化。
7. CEO/CFO/关键技术负责人、董事长或多数董事发生变化。
8. 重大分拆、私有化、IPO、破产、债务重组或资产出售。
9. 30 日内多个中等事件形成“事件簇”，即使单项未过金额门槛。

### 7.5 事实展示门槛

- 精确持股比例必须同时有：**来源、证券类别、基数、直接/间接、as_of_date**。
- 精确金额必须同时有：**金额类型、币种、状态、宣布/交割时间**。
- “控制”必须有投票权、任命权、合同权、会计合并或其他明确依据。
- “资金流向”必须说明是现金流、融资、投资、持仓变化、采购承诺还是政府义务额。
- 推断关系必须以虚线/标签展示，并提供反对证据和失效条件。
- 低于 60 分置信度不得进入面向用户的事实图层。

## 8. MVP 数据覆盖与验收标准

### 8.1 P0 覆盖标准

每个 P0 实体至少满足：

- 规范名称、别名、CIK/LEI/UEI等可得标识和法律状态完整。
- 公开公司：最近 2 份年报、最近 8 个季度、最新 proxy、重大 8-K、13D/G、Forms 3/4/5 已索引。
- 私营/PBC/非营利：最近 5 年重大融资、治理、官方结构、政府合同和关键商业关系已形成证据队列。
- 至少 10 条可验证的高价值关系；不足时明确显示“公开资料不足”，不能用推断补足数量。
- 每个核心关系至少 1 个原始来源定位；控制和重大资本关系优先双源核验。
- 公司档案能回答第 1.1 节八个问题中的至少 6 个。

### 8.2 P1 覆盖标准

- 完成实体解析、集团父级、主要业务、最新监管/官方来源入口。
- 至少 5 条高价值一跳关系。
- 重大事件自动升级研究深度。

### 8.3 P2 覆盖标准

- 完成实体身份、来源入口和关键词/表单监控。
- 默认不做全量历史回填。
- 命中事件门槛或相关性分升至 60 后升级 P1。

### 8.4 整体数据质量验收

| 验收项 | 最低标准 |
| --- | ---: |
| P0 身份解析完整率 | 100% |
| P0 关键关系一级来源覆盖率 | ≥90% |
| P0 所有数值带时间和单位 | 100% |
| 13F 被误标为实时流量 | 0 次 |
| 品牌直接作为法律股权当事方 | 0 次，除非明确标记 unresolved |
| 重大冲突被静默覆盖 | 0 次 |
| 前端可点击到原始证据 | ≥95%高价值边 |
| 更新任务幂等性 | 重跑不产生重复事实 |
| 修订/重述链 | 可追踪，不删除旧版本 |

## 9. 关键盲点与反直觉问题

### 9.1 公开持股不等于实际控制

大量机构持股可能是被动基金或客户资产。真正的影响要结合投票政策、管理人裁量权、基金结构、董事权和治理协议。把 BlackRock/Vanguard 的所有 13F 持仓直接画成“母公司拥有”会严重误导。

### 9.2 资金方向不只在现金流量表

下一轮产业浪潮常先出现在：长期采购义务、GPU抵押贷款、电力协议、数据中心租约、设备订单、政府合同、专利簇和关键人员迁移。单看股票交易和并购会遗漏基础设施锁定。

### 9.3 大额承诺不等于已投入现金

融资“目标规模”、基金承诺、合同潜在上限、云额度和政府 award ceiling 常被媒体写成已发生金额。系统必须拆开状态，否则资本河流会被系统性放大。

### 9.4 共同所有权不自动等于协同行动

共享机构投资人可以形成治理环境和激励相似性，但不能直接推断串谋或一致行动。网络图应显示“共同持有暴露”，不显示未经证实的“共同控制”。

### 9.5 最有价值的信号可能是约束而不是投入

电力、晶圆、出口许可、反垄断救济、债务契约和监管牌照可能比融资额更能决定战略上限。因此战略雷达要同时显示“能力”和“约束”。

## 10. 审批选择矩阵

只需回复类似 `1A 2A 3B 4A 5A 6A`，无需写长说明。

| 编号 | 决策 | A（默认推荐） | B | C |
| --- | --- | --- | --- | --- |
| 1 | 公司池规模 | 120 美国 + 20 外部 | 80 美国 + 15 外部 | 200 美国 + 30 外部 |
| 2 | MVP 深挖数量 | P0 30 家 | P0 20 家，更快 | P0 40 家，更重 |
| 3 | 研究权重 | 均衡权力网络 | AI/科技占 60% | 金融/资本占 60% |
| 4 | 数据预算 | 只用开放/官方源 | 允许一个商业库 | 允许多商业库 |
| 5 | 推断政策 | 保守：事实与推断严格分层 | 探索：允许更多低置信度候选边 | 极保守：只显示一级来源事实 |
| 6 | 投资研究输出 | 战略信号与假设，不给直接买卖结论 | 加入可回测评分与观察清单 | 只做企业权力研究，不做投资层 |

### 默认审批值

`1A 2A 3A 4A 5A 6A`

## 11. 审批后写入最终 Task Pack 的文件

- `data/seed_universe.csv`：120 个美国实体与 20 个外部节点。
- `data/source_registry.csv`：本稿来源注册表、访问要求和阶段。
- `data/metric_catalog.csv`：指标定义、公式、来源和展示规则。
- `data/screening_rules.yaml`：公司、关系、事件和事实展示门槛。
- `data/research_object_taxonomy.csv`：实体和关系分类。
- `docs/RESEARCH_UNIVERSE_AND_DATA_POLICY.md`：本稿的正式版。
- `specs/provenance_schema.json`：时间、证据、修订和置信度字段。
- `prompts/00_UNIVERSE_APPROVAL_GATE.md`：Codex 在实现前强制读取并验证公司池。

## 12. 官方依据与参考入口

1. SEC EDGAR APIs：<https://www.sec.gov/search-filings/edgar-application-programming-interfaces>
2. SEC EDGAR Fair Access（当前最大请求速率 10 req/s，并要求声明 User-Agent）：<https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data>
3. SEC Form 13F FAQ（季度末后 45 天申报规则）：<https://www.sec.gov/rules-regulations/staff-guidance/division-investment-management-frequently-asked-questions/frequently-asked-questions-about-form-13f>
4. SEC Forms 3/4/5 说明（Form 4通常为交易后两个工作日）：<https://www.sec.gov/files/forms-3-4-5.pdf>
5. SEC 受益所有权与 5%门槛说明：<https://www.sec.gov/resources-small-businesses/going-public/officers-directors-10-shareholders>
6. SEC IAPD / Form ADV：<https://adviserinfo.sec.gov/>
7. SEC Form N-PORT 数据集：<https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets>
8. USAspending API v2：<https://api.usaspending.gov/>
9. OpenFEC API：<https://api.open.fec.gov/developers/>
10. LDA.gov：<https://lda.gov/>
11. USPTO Open Data Portal：<https://data.uspto.gov/>
12. IRS Tax Exempt Organization bulk data：<https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-bulk-data-downloads>
13. GLEIF API：<https://www.gleif.org/en/lei-data/gleif-api>
14. FTC Competition Enforcement Database：<https://www.ftc.gov/competition-enforcement-database>
15. DOJ Antitrust Case Filings：<https://www.justice.gov/atr/antitrust-case-filings>
16. FCC ECFS Public API：<https://www.fcc.gov/ecfs/help/public_api>
17. EIA Open Data：<https://www.eia.gov/opendata/>
18. Federal Register API：<https://www.federalregister.gov/developers/documentation/api/v1>
19. FFIEC National Information Center：<https://www.ffiec.gov/npw>
20. FDIC BankFind API：<https://api.fdic.gov/banks/docs>
21. FINRA TRACE：<https://www.finra.org/filing-reporting/trace>
22. OpenAI 官方结构说明：<https://openai.com/our-structure/>
23. SpaceX/xAI/X 有效关系的 SEC 文件：<https://www.sec.gov/Archives/edgar/data/1181412/000162828026040610/spacexfwp.htm>
24. Anthropic Long-Term Benefit Trust：<https://www.anthropic.com/news/the-long-term-benefit-trust>

---

**审阅结论模板**：`批准默认方案 1A 2A 3A 4A 5A 6A`，或仅替换需要调整的选项。审批前不应重新生成最终压缩包。
