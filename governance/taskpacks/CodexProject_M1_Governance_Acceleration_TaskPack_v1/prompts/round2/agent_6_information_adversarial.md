# Round 2 - Agent 6 信息与交互对抗复审


共同规则：
- RUN_MODE=READ_ONLY；禁止修改、生成、安装、提交、推送或触发写模式。
- 不读取同轮其他 Agent 输出；不得 spawn 子 Agent。
- 只读取根治理执行链和直接测试；不扫项目业务目录。
- 每项问题必须给出路径/符号/命令证据、严重度、是否阻塞、修复和必需测试。
- 没有实际运行的测试标记 NOT_RUN；不得写成 PASSED。
- 输出一个符合 `schemas/review_report.schema.json` 的 JSON；其中 `findings[]` 必须符合 `schemas/finding.schema.json`；另附一个不超过 2 页的 Markdown 摘要。


输入：Round 1 consolidated summary + M1-S candidate。攻击压缩方案是否导致：Acceptance/Evidence 丢失、Agent 偏离、错误 NOT_APPLICABLE、关键失败隐藏、handoff 依赖聊天记忆、新真相源、中文可读性下降。输出必须给出 owner 首屏与 compact CLI 的验收标准。
