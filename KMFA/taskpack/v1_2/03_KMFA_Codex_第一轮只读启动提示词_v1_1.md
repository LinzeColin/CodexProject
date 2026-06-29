# CODEX 第一轮启动提示词｜KMFA｜只读计划

Project: KMFA
Mode: PLAN / READ_ONLY
Risk: T3 for money, tax, privacy, source side effects. No production side effects.

目标：
读取本包中的 `01_KMFA_Codex_TaskPack_v1_1_完整防遗漏.md` 与 `02_KMFA_Codex_Development_Roadmap_18_Stages_v1_1.md`，不要直接实现。先输出实施计划和风险评审。

必须读取：
1. CodexProject/AGENTS.md
2. CodexProject/docs/governance/STANDARD.md
3. 本TaskPack
4. 本Roadmap
5. 需求追溯矩阵
6. 数据治理与质量门禁
7. 模型公式函数参数主注册表
8. 零差异验证与测试计划

禁止：
1. 不直接写UI。
2. 不直接生成报告。
3. 不接红圈、金蝶、WPS、银行、税务自动接口。
4. 不提交原始敏感数据。
5. 不修改原始上传数据。
6. 不使用float处理金额。
7. 不跳过零差异和质量门禁。

输出：
1. implementation_plan.md
2. files_to_read.md
3. files_to_modify.md
4. test_commands.md
5. rollback_plan.md
6. risk_register.md
7. stop_conditions.md
8. no_omission_check_result.md

通过后再进入 S01。任何P0要求未绑定任务、验收、测试、证据时，停止并报告。
