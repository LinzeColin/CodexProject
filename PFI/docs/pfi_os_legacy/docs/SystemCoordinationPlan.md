# PFIOS 总系统协调计划

生成日期：2026-06-05

适用范围：PFIOS、AI-Research-System、消费分析系统、独立验证系统、政府政策系统，以及相关 Codex 对话框和 automation。

## 1. 当前判断

PFIOS 暂定为母系统和研究指挥中心。

理由：

- PFIOS 当前保存统一 ResearchBus 主库、schema、互通审计和桌面入口。
- PFIOS 已经能读取行研报告、消费行为状态、持仓主数据、独立验证运行状态和回测结果。
- PFIOS 的定位是研究验证、策略变更确认、报告中心和个人日常工作台，适合作为用户操作入口。

子系统保持独立运行，不合并成单一代码库。

原则：

- 母系统负责协调、schema、审计、入口和排期。
- 子系统负责各自专业能力。
- 任意子系统仍可单独启动、单独运行、单独维护。
- 所有跨系统数据通过 ResearchBus、outbox、manifest、schema 和明确 ACK 互通。

## 2. 已完成握手动作

已向以下线程发送总系统协调握手指令：

| 系统 | 线程 | 指令目标 |
| --- | --- | --- |
| AI-Research-System | 行研报告与交易策略建议系统 | 暂停非必要扩张，输出当前 goal、阻塞、ResearchBus 合并事项 |
| 消费分析系统 | 消费分析原版 | 暂停新 UI/重复打包，输出验收状态和消费状态同步需求 |
| 独立验证系统 | 独立验证系统 | 暂停新长跑和 OpenD 抓取，等待 PFIOS ACK |
| 政府政策系统 | 政府文件解读系统 | 暂停解析器/UI 堆叠，优先 P0 access-readiness |

当前状态：握手指令已发出，并已收到 AI-Research-System、消费分析系统、独立验证系统和政府政策系统的阶段性 ACK。各系统后续仍以用户在对应线程的最新指令为最高优先级；若用户在子系统线程继续下达新需求，该线程可能继续执行，但应把非必要扩张降级。

## 3. 系统职责

| 系统 | 主导职责 | 不应主导 |
| --- | --- | --- |
| PFIOS | ResearchBus、统一 schema、主工作台、持仓主数据、回测验证、策略变更确认、报告中心、总协调看板 | 行研报告正文生成、政策原文爬虫、消费账单分类、大规模 worker 长跑 |
| AI-Research-System | 日报/周报/K线报告、报告质量门、行研判断、automation、证据链引用 | ResearchBus 主 schema、PFIOS 策略库写入、消费账单分类 |
| 消费分析系统 | 支付宝/账单入库、经济放血分类、消费周期报告、行为状态输出、用户验收工作台 | 投资建议、回测、行研报告生成、政策采集 |
| 独立验证系统 | 大规模策略验证、manifest/campaign、worker、长跑产物、外部证据包 | PFIOS 数据库写入、策略变更确认、用户界面主入口 |
| 政府政策系统 | 政策原文抓取、政策证据链、政策报告、平台授权 readiness | 行研日报编排、PFIOS 回测、消费分析 |

## 4. 当前 active goal 汇总

| 系统 | 当前 goal | 当前状态 | 主要阻塞 |
| --- | --- | --- | --- |
| PFIOS | 个人量化研究、回测、持仓、报告、ResearchBus 总工作台 | 互通审计 15/15 Pass；盘感训练已增强 | 需要把独立验证 ACK、总协调看板和开发排期产品化 |
| AI-Research-System | 自动化行研报告、仓位操作研究、报告质量门 | 报告生成和 ResearchBus bridge 已具备 | 新鲜行情、OpenD 覆盖、支付宝当日更新、政策桥状态仍可能 fail-closed |
| 消费分析系统 | 经济放血账单分析软件工程交付 | 工程门禁通过，ZIP 已生成 | 等用户 A/B/C 验收和 ChatGPT 对照文件 |
| 独立验证系统 | PFIOS 外部策略验证层 | QBVS 侧协议和证据包就绪 | PFIOS 真实 ACK 缺失；OpenD 额度和 200 标的真实验证未完成 |
| 政府政策系统 | 每日两次政策原文抓取和政策研究报告 | 系统能力丰富，access-readiness 已有 | 搜索 API 0/3、平台授权 0/8、scheduler 安装证据缺失 |

## 5. 立即暂停事项

这些事项暂停，直到总协调 ACK 完成或用户单独指定：

- AI-Research-System：暂停新增低价值报告模板、重复 UI 扩张、无新数据支撑的历史报告重生成。
- 消费分析系统：暂停继续打包、多版本报告扩张、大型 UI 新增；先等用户验收和 ChatGPT 对照。
- 独立验证系统：暂停新一轮 OpenD 抓取、重复长跑、继续扩充策略目录数量；先完成 PFIOS ACK 和额度友好计划。
- 政府政策系统：暂停继续堆解析器和 dashboard；优先补搜索 API / 平台授权 / scheduler 证据。
- PFIOS：暂停非关键页面美化和新模块扩张；优先完成总协调、ACK、schema 治理和任务看板。

## 6. 最高优先级

P0，必须先做：

1. PFIOS 读取 QBVS 握手请求并生成真实 `pfi_os_handshake_ack.json`。
2. 建立 `SystemCoordinationPlan` 和 `SystemCoordinationStatus`，统一显示每个系统当前状态、阻塞、下一步。
3. 固化 ResearchBus schema version、请求类型和字段变更流程。
4. 把各系统 ACK 汇总到 PFIOS 总协调看板。
5. 所有系统进入“冻结非必要功能 + 只做指定高价值任务”的节奏。

P1，随后做：

1. 行研系统只保留报告质量门、automation、政策/PFIOS/持仓引用链路的修复。
2. 消费系统只输出消费状态、行为画像和验收结论给 ResearchBus。
3. 独立验证系统只输出 evidence bundle、campaign 状态、worker readiness，不写 PFIOS。
4. 政策系统只补 P0 凭据和 scheduler 证据，不继续扩张解析器。

P2，稳定后做：

1. PFIOS 首页新增总系统状态板块。
2. 新增跨系统任务队列：需求、owner、状态、阻塞、验收命令、回滚方式。
3. 报告中心纳入所有系统正式 PDF 和关键 JSON/CSV manifest。
4. 建立每周一次总系统审计 PDF。

P3，公开研究驱动升级：

1. 固化 `docs/PublicResearchUpgradePlan.md` 的证据门、来源日志和 ROI 评分。
2. 只吸收成熟开源和竞品机制，不盲目重写系统。
3. 新功能必须标注预期价值、执行难度、风险、所需输入、验证方式和失效条件。
4. 无公开、授权或用户提供的信息来源时，结论必须降级为 `无法访问 / 需要授权 / 需要用户手动导出`。

## 7. 时间线

时间估算基于当前代码和本地证据，不包含外部 API key、平台 cookie、OpenD 额度不可用导致的等待时间。

| 阶段 | 时间 | 目标 | 验收 |
| --- | --- | --- | --- |
| Phase 0：协调冻结 | 0.5 天 | 向所有线程发握手指令，形成总协调计划 | 本文件存在；各线程收到指令 |
| Phase 1：ACK 和 schema 治理 | 1 天 | PFIOS 生成 QBVS ACK；ResearchBus schema/version/request registry 固化 | ACK valid；互通审计仍 Pass |
| Phase 2：总状态看板 | 1-2 天 | PFIOS 显示各系统 goal、阻塞、下一步、暂停项 | 页面/CLI 均可查看；不打开子系统也能判断状态 |
| Phase 3：子系统接口收口 | 2-3 天 | 行研、消费、政策、独立验证只保留明确输入/输出/状态接口 | 每个系统有 ACK、manifest、最新状态 JSON |
| Phase 4：自动化治理 | 2-4 天 | automation 只触发成熟任务；缺数据 fail-closed；避免重复长跑 | automation readiness 和 report quality gate 可审计 |
| Phase 5：总系统成品化 | 3-5 天 | 总工作台、报告中心、任务队列、周审计报告成熟 | 一键同步、一键审计、一份周度总报告 |

预计总剩余：约 7-12 个有效工作日；如果外部凭据和 OpenD 额度及时补齐，可缩短到 4-7 个有效工作日。

## 8. 合并与整合顺序

不做代码库硬合并，采用“协议先行、证据包合并、界面聚合”的顺序。

1. schema 合并：统一 ResearchBus schema、字段命名、request types。
2. 状态合并：每个子系统只上报 status、blockers、latest artifacts、next action。
3. 证据合并：PDF/CSV/JSON/SQLite/manifest 进入统一 report index。
4. 任务合并：由 PFIOS 维护跨系统 task queue。
5. UI 合并：PFIOS 只聚合入口和摘要，不复制子系统全部页面。
6. automation 合并：由 automation 调用各系统稳定 CLI，不互相改源码。

## 9. ResearchBus 必备字段

所有跨系统消息至少包含：

- `run_id`
- `source_system`
- `target_system`
- `request_type`
- `status`
- `created_at`
- `updated_at`
- `schema_version`
- `source_path`
- `artifact_path`
- `evidence_level`
- `data_quality`
- `blocking_reason`
- `next_action`
- `owner_system`

金融、投资、回测相关额外包含：

- `market`
- `symbol`
- `sample_window`
- `data_provider`
- `cost_assumptions`
- `risk_gate_status`
- `decision_quality_status`
- `not_live_trading = true`

## 10. 验收门禁

总系统不能仅凭“文件存在”判断完成。必须同时满足：

1. 各系统 ACK 已返回或明确标记 blocked。
2. ResearchBus 互通审计 Pass，且 schema 版本一致。
3. PFIOS 能看到每个子系统的 latest status。
4. 子系统可单独运行，不依赖 PFIOS 启动。
5. 母系统能触发子系统稳定入口，但不吞并其代码。
6. 报告、回测、消费、政策结论均保留 source log / audit log / missing data log。
7. 任何缺数据、缺权限、缺用户验收、缺行情的任务必须 fail-closed。

## 11. 当前风险

- 多个线程仍在 active 或 in-progress；如果不冻结，会继续产生范围漂移。
- 旧路径较多，必须以当前 HANDOFF 和真实文件为准。
- AI-Research-System 没有单独 HANDOFF.md，状态分散在 README、automation logs 和线程摘要中。
- 独立验证系统缺 PFIOS 真实 ACK，不能宣称双系统完全闭环。
- 政策系统缺 API key / platform auth，不能宣称全网在线覆盖。
- 消费分析系统工程可验收，但用户主观验收和 ChatGPT 对照仍未完成。

## 12. 下一轮执行计划

下一轮只做一件事：PFIOS 总协调执行层。

任务：

1. 读取 QBVS `qbvs_handshake_request.json`。
2. 在 PFIOS 生成真实 `pfi_os_handshake_ack.json`。
3. 新增或更新 PFIOS `System Coordination` 状态数据文件。
4. 把 AI-Research、Consumption、QBVS、Policy 的 ACK/blocked 状态纳入状态文件。
5. 增加一个不打开浏览器也可运行的审计命令。
6. 更新 `HANDOFF.md` 和 `docs/ResearchBus.md`。
7. 运行 targeted tests 和互通审计。

暂停其它所有非必要功能开发，直到这一步完成。
