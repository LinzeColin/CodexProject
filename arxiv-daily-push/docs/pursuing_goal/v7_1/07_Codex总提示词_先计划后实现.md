# 可直接交给 Codex 的总提示词

```text
你正在处理 CodexProject/arxiv-daily-push。

当前产品合同：ADP-PRODUCT-CONTRACT-V7.1
当前 Roadmap：ADP-ROADMAP-V7.1
当前 legacy 任务：S2P1T01
当前 canonical 映射：S2PBT01
并行根合同任务（唯一下一治理 Task）：S2PAT05

必须先读取：
1. 根 AGENTS.md
2. docs/governance/STANDARD.md
3. arxiv-daily-push/AGENTS.md
4. HANDOFF/00_下一Agent先读.md
5. 本任务包 README_先读.md
6. 09_并行审查/并行审查汇总与合并结论.md
7. 00_系统总纲与不可漂移产品契约.md
8. ROADMAP/ARXIV_DAILY_PUSH_ROADMAP_V7_1_CN.md
9. 仅当前 Task 对应的任务卡

产品不可漂移结构：
- D1–D4 四个数据源域；
- B1 科学理论、B2 工程产品产业、B3 政策资本地缘；
- B4 社会时代、B5 风险反证失败、B6 个人机会能力经济转化；
- 每日 M1/M2/M3/M4，三封主邮件加一封跨板块汇总；
- 每周总结和每月总结；
- 一改四查三基；
- 全局中文优先；
- 显示真实队列、讲解、发送、复习、行动和 ROI 数量。

执行约束：
- 一次只处理一个 Task ID 和一个 Acceptance ID；
- 先 PLAN/READ_ONLY，不全仓扫描；
- 在修改前列出允许读取、允许修改、测试命令、风险、回滚、Stop Conditions 和唯一 Stop Gate；
- Stage2 连接器只能输出 Canonical/EvidencePacket，不得直接生成最终邮件；
- 不得把来源域直接当作阅读板块；
- 不得恢复旧五封邮件结构；
- 不得把新要求只写在聊天、PR 描述或隐藏 docs 中，必须同步进入中文三基文件和用户中心；
- 不得把 PROPOSED/UNKNOWN 写成已实现；
- 不自动合并 PR，不自动改冻结参数；
- 真实 SMTP、restore、scheduler install 和 DAILY_OPERATION 在 S2PMT07 前保持关闭；
- not_verified 不得改写为 PASS。

PR/Closeout 必须声明：
product_contract_version
product_contract_sha256
roadmap_version
canonical_task_id
legacy_task_id（如适用）
影响的 D/B/M
是否修改 EvidencePacket、状态机、参数、人类视图

完成后输出：
1. 状态 PASS/BLOCKED/FAILED/DEFERRED；
2. diff summary；
3. 实际测试命令、退出码和结果；
4. Requirement/Feature/Task/Function/Test/Artifact/Evidence 追踪；
5. 三基文件和用户中心更新情况；
6. 剩余风险；
7. 回滚；
8. 下一唯一 Task 是否解锁。
```


## V7.1 强制审查门

任何 Agent 必须先读取 `HANDOFF/00_下一Agent先读.md` 与 `09_并行审查/并行审查汇总与合并结论.md`。P0/P1 未清零不得进入生产 Gate；Stage2 Shadow 连接器仅按 merge policy 例外并行。
