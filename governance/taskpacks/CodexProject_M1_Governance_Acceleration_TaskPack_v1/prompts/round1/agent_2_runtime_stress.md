# Round 1 - Agent 2 运行、压力与生命周期


共同规则：
- RUN_MODE=READ_ONLY；禁止修改、生成、安装、提交、推送或触发写模式。
- 不读取同轮其他 Agent 输出；不得 spawn 子 Agent。
- 只读取根治理执行链和直接测试；不扫项目业务目录。
- 每项问题必须给出路径/符号/命令证据、严重度、是否阻塞、修复和必需测试。
- 没有实际运行的测试标记 NOT_RUN；不得写成 PASSED。
- 输出一个符合 `schemas/review_report.schema.json` 的 JSON；其中 `findings[]` 必须符合 `schemas/finding.schema.json`；另附一个不超过 2 页的 Markdown 摘要。


重点：0/1/多项目选择、重复与并发、取消/超时、自动 schedule、concurrency cancellation、后台进程关闭、临时目录、缓存、日志、证据保存、零写入、真实结果有效性。先给测试计划；安全可运行的只读命令才执行。
