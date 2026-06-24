# Prompt for a New Developer / Agent

你接手的是 `EVA_OS`，一个本地优先、证据驱动的个人研究中台。请先读这个交接包，再读仓库根目录的：

```text
README.md
HANDOFF.md
AGENT_CONTINUITY.md
15_OPEN_QUESTIONS.md
UPLOAD_MANIFEST.md
docs/EVA_OS.md
docs/Index.md
```

请遵守：

1. 不要一次性升级所有系统。
2. 每次只做一个子系统或一个明确 Run Contract。
3. 不要启用实盘交易、真实下单、自动付款、自动下注。
4. 不要上传私有 holdings、截图、SQLite runtime、`.env`、日志、raw imports。
5. 改代码前先确认当前测试和运行环境。
6. 完成后必须更新受影响文档和 focused tests。
7. 如果没有完整 `.venv`，不要声称 full suite 通过。

推荐第一步：

```text
重建 .venv -> 跑 focused tests -> 做 Vectorized Research Mode MVP
```

请输出你的执行合同：

```text
1. 目标
2. 最小范围
3. 要读的文件
4. 可能修改的文件
5. 验证命令
6. 风险和停止条件
```
