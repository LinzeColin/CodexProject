# Stage 1+ 与 Stage 2 并行开发及跨线程同步合同

## 1. 并行而不分裂

| 轨道 | 主要职责 | 当前入口 | 禁止事项 |
|---|---|---|---|
| G 产品/治理 | V7 合同、决策、Roadmap、中文人类视图 | `S2PAT01` | 不得写业务采集器 |
| D 数据源 | D1–D4 connector、身份、许可、fixture、Shadow | `S2PBT01` | 不得自行定义最终邮件 |
| E 证据/知识 | EvidencePacket V2、图谱、反证、路由 | `S2PG` | 不得绑定单一来源逻辑 |
| Q 内容质量 | 深度解释、金标、个人影响 | `S2PH` | 不得跳过证据级别 |
| U 用户体验 | 一改四查三基、中文、真实状态 | `S2PI` | 不得复制第二套可编辑事实源 |
| R 成长转化 | 复习、行动、资产、ROI、周/月 | `S2PJ` | 不得补造收益和成长率 |
| M 交付 | M1–M4、错峰、水位线、幂等 | `S2PK` | 不得恢复五封旧结构 |
| I 集成验收 | 重放、真实运行、恢复、生产 Gate | `S2PL` | 不得用代码存在替代运行证据 |

每个 Codex 线程仍遵守“一次只处理一个 Task、一个目录范围、一个 Acceptance”。

## 2. 强制读取声明

所有 Stage 2 PR 必须包含：

```text
product_contract_version: ADP-PRODUCT-CONTRACT-V7.1
product_contract_sha256: <合并后实际哈希>
roadmap_version: ADP-ROADMAP-V7.1
canonical_task_id: <S2P...>
legacy_task_id: <如适用>
source_domains_affected: [D1..D4]
reading_boards_affected: [B1..B6]
mail_products_affected: [M1..M4]
changes_evidence_packet: true/false
changes_lifecycle: true/false
changes_human_views: true/false
changes_parameters: true/false
```

哈希不一致时触发 `CONTRACT-HASH-MISMATCH`。

## 3. 当前两个线程

### 根合同线程 `S2PAT01`

只读审计后，负责将本任务包收敛进：

- `docs/governance/product_contract.yaml`；
- `docs/governance/decision_log.yaml`；
- `docs/governance/requirements.yaml`；
- `docs/governance/roadmap.yaml`；
- `00_用户中心/05_系统总纲开发要求与验收标准.md`；
- `AGENTS.md`、README、三基文件的唯一入口和哈希声明。

### 来源线程 `S2PBT01` / legacy `S2P1T01`

可以继续：

- fixture；
- connector；
- 规范化；
- 身份/版本/许可；
- EvidencePacket 兼容；
- focused tests。

不得：

- 直接生成最终邮件；
- 把 D1 等同 B1；
- 宣称来源晋升已通过而未读取 V7 合同；
- 修改三基文件为旧五封结构。

## 4. 文件所有权

公共 Schema 只能由明确的集成任务修改。连接器任务通过扩展点适配，不得各自复制 Schema。多个线程若必须触碰同一文件，后开始的线程进入 BLOCKED 并提交冲突矩阵，不得抢写。

## 5. 公共接口

```text
Connector → RawRecord / CanonicalDocument / CanonicalEvent / EvidencePacket
Analyzer → InsightUnit / Claim / CounterEvidence / PersonalImpact
Router → B1–B6 assignment + reason codes
Orchestrator → M1–M4 status/waterline/idempotency
Learning → Review / Action / Asset / Conversion
```

## 6. 每个 Task 开始前

必须写入开发记录：

1. canonical Task ID、legacy alias、Acceptance；
2. Pursuing Goal 和非目标；
3. 允许读取文件；
4. 允许修改文件；
5. 测试命令；
6. 风险、回滚、Stop Conditions；
7. 对合同、Schema、三基文件和用户中心的影响。

## 7. 每个 Task 结束后

必须记录：状态、diff summary、真实命令和退出码、证据路径、追踪矩阵、资源峰值、剩余风险、回滚、下一任务是否解锁，以及三基文件是否重新渲染并通过漂移检查。


## V7.1 强制审查门

任何 Agent 必须先读取 `HANDOFF/00_下一Agent先读.md` 与 `09_并行审查/并行审查汇总与合并结论.md`。P0/P1 未清零不得进入生产 Gate；Stage2 Shadow 连接器仅按 merge policy 例外并行。
