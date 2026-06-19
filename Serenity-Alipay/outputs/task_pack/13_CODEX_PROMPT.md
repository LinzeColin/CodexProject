# 13 Codex Prompt

Use this prompt to start the next implementation turn.

```text
开始 Pursuing Goal：在当前 workspace 实现 Serenity Daily Analysis MVP。

请先读取：
- AGENTS.md instructions in current thread
- HANDOFF.md
- outputs/requirements/PRD_SERENITY_DAILY_ANALYSIS.md
- outputs/task_pack/*.md

目标：
实现一个本地优先、dry-run 默认的 Serenity Daily Analysis MVP。第一轮只完成 Phases 0-2：
1. Python package skeleton
2. config
3. SQLite schema creation
4. CLI: doctor, init-db, import-alipay, run --slot --dry-run, report
5. Alipay CSV import template and importer
6. manual candidate/fund rule source loader
7. deterministic metrics/scoring engine
8. risk hard gates: MDD >= 40.00%, recovery >= 365 days
9. benchmark comparison fields for Shanghai Composite and S&P 500 over 1m/3m/10D
10. Markdown report draft

边界：
- 不自动下单
- 不发送真实邮件，先生成 Mail-ready notification draft
- 不存储 secrets/cookies/passwords
- moomoo/OpenD 不可用时必须显式降级，不静默成功
- 聚合源 fallback 只能补视图，不能单独 Action-Ready

验收：
- 能运行 `python -m app.cli doctor`
- 能运行 `python -m app.cli init-db`
- 能用模板导入 Alipay CSV
- 能 `python -m app.cli run --slot R7 --dry-run`
- 能生成 SQLite 记录和 Markdown report
- 有 focused tests 覆盖 timezone slots, import, scoring hard gates

执行方式：
先给 compact execution contract，然后实现。每轮只做最小高置信 diff，完成后运行最小验证并汇报结果。
```

