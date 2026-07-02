# WDA Agent Contract

默认用户可见输出使用中文；代码、API、库名和错误信息可保留英文。

## 工作树边界

- 本项目唯一长期工作树：`/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/WDA`。
- 项目源码与治理入口位于 `WDA/`，不得切换到其他项目目录推进开发。
- 不得读取或展开 Alpha、PFI、EEI、KMFA、Memory Atlas、Serenity、OpMe_System、KM_IDSystem 等无关项目。
- 多个 Codex 聊天框可以共同使用这个工作树，但都必须在同一分支和同一项目边界内推进。

## 任务入口

开始任何任务前先读：

1. 根级 `AGENTS.md`
2. `WDA/AGENTS.md`
3. `WDA/README.md`
4. `WDA/docs/HANDOFF.md`
5. 当前任务直接点名的文件

不要扫描整个 monorepo。需要更多上下文时，先说明为什么必须扩大范围。

## 治理要求

- WDA 暂处于 `definition_pending`，不得编造产品能力、模型、公式、参数或生产就绪结论。
- 三份 owner 入口 `功能清单.md`、`开发记录.md`、`模型参数文件.md` 必须保留为中文可读事实入口。
- 机器事实源以 `docs/governance/project.yaml`、`roadmap.yaml`、`events.jsonl`、`VERSION` 和 `CHANGELOG.md` 为准。
- 模型、公式、参数在业务范围明确前保持 `NOT_APPLICABLE` 或 `UNKNOWN`，并绑定后续任务。

## 验证

优先运行项目级轻量验证：

```bash
/usr/bin/python3 -B scripts/lean_governance.py check-render --project WDA
```

完整 governance validate 可能要求 full monorepo root schema 和其他注册项目路径；不要为了通过该命令展开其他项目，先报告 sparse 限制。
