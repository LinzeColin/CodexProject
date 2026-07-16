# Root Cleanliness Contract

根入口只承担稳定导航与 always-on 治理，不承载当前 Task/Run 状态、完整项目百科或大体积证据。

## Canonical sources

- `governance/projects.yaml`：active、retired、migrated project 与 root required files。
- `governance/root_cleanliness_budget.json`：入口字节预算、root item owner/purpose、项目入口要求、必备铁律与临时状态禁用模式。
- `scripts/root_cleanliness_audit.py`：只读、确定性、fail-closed 执行器。

AGENTS/README 中重复的迁移项目表已合并为 registry 单一事实源；文档只保留“不得恢复 migrated path”的稳定规则。没有删除项目数据、历史、evidence 或完整根文件。

## Hard gates

```bash
python3 -B scripts/root_cleanliness_audit.py --root . --json
```

必须同时满足：

- `AGENTS.md <= 4096 bytes`；`README.md <= 8192 bytes`；两份初始入口合计 `<= 12288 bytes`。
- 每个 tracked candidate root item 有唯一 owner/purpose；active/retired project 目录由 registry 动态归属。
- active project ID/path 唯一，目录存在，`README.md` 与 `AGENTS.md` 可达，README 表与 registry 完全一致。
- migrated path 不再出现在 candidate tree；active changed-scope exclusion 必须显式列入 policy，默认不允许。
- AGENTS 必备铁律齐全；README 无短期执行状态；入口 Markdown local link 全部存在且不能逃逸仓库。

输出包含 policy/registry SHA-256、HEAD、预算、项目数、root inventory 与错误列表；不含 timestamp，因此同一 tree 的结果可重放比较。

## Change and rollback

新增 root item 必须在同一 Task 中声明 owner/purpose 并通过测试。删除、移动、合并完整文件前必须先证明 exact reference=0、replacement accepted、source hash 和 rollback；本 Task 只合并重复说明，不做完整文件删除。

失败时不得降低预算、跳过链接、排除 required project 或修改无关项目。回滚使用普通 commit revert，再运行 focused test、root audit 与 changed-scope governance；禁止 history rewrite 或 force-push。
