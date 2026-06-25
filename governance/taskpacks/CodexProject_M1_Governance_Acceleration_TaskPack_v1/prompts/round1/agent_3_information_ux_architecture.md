# Round 1 - Agent 3 信息 UX 与架构


共同规则：
- RUN_MODE=READ_ONLY；禁止修改、生成、安装、提交、推送或触发写模式。
- 不读取同轮其他 Agent 输出；不得 spawn 子 Agent。
- 只读取根治理执行链和直接测试；不扫项目业务目录。
- 每项问题必须给出路径/符号/命令证据、严重度、是否阻塞、修复和必需测试。
- 没有实际运行的测试标记 NOT_RUN；不得写成 PASSED。
- 输出一个符合 `schemas/review_report.schema.json` 的 JSON；其中 `findings[]` 必须符合 `schemas/finding.schema.json`；另附一个不超过 2 页的 Markdown 摘要。


本任务无产品页面 UI；将 UI/交互审查映射到 GitHub 导航、README、AGENTS、CLI 首屏、错误反馈、命令连接、双平面、Roadmap、Agent 入口、交接和功能架构。重点发现多个真相源、信息噪声、重要事实埋藏和下一动作不清。不得建议新增平行 current truth。
