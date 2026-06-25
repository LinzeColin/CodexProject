# Round 1 - Agent 1 安全与代码质量


共同规则：
- RUN_MODE=READ_ONLY；禁止修改、生成、安装、提交、推送或触发写模式。
- 不读取同轮其他 Agent 输出；不得 spawn 子 Agent。
- 只读取根治理执行链和直接测试；不扫项目业务目录。
- 每项问题必须给出路径/符号/命令证据、严重度、是否阻塞、修复和必需测试。
- 没有实际运行的测试标记 NOT_RUN；不得写成 PASSED。
- 输出一个符合 `schemas/review_report.schema.json` 的 JSON；其中 `findings[]` 必须符合 `schemas/finding.schema.json`；另附一个不超过 2 页的 Markdown 摘要。


重点：供应链、权限、fail-open、base/diff 错误、错误吞噬、全局脏工作树、竞态、异常/超时、测试脆弱性、单体可维护性、Required Check 连续性。

必读：`AGENTS.md`、`STANDARD.md`、`lean_governance.py`、workflow、`projects.yaml`、直接治理测试。
