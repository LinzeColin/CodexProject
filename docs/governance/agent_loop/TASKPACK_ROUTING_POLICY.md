# Task Pack Routing Policy

本策略解决 Owner 不需要记住项目路径规则的问题。ChatGPT 仍应生成完整
dual-plane Task Pack；仓库层只在路由唯一、低风险、可证明时补全缺失 metadata。

## Routing Source Of Truth

唯一事实源是 `docs/governance/agent_loop/PROJECT_ROUTING_MATRIX.md` 中的
`AGENT_LOOP_ROUTING_MATRIX_JSON` block。脚本不得从业务目录猜规则。

## Normalization Flow

1. Workflow 先把入口内容写入 `/tmp/agent_loop/taskpack.raw.md`。
2. `autofill_taskpack_metadata.py` 读取 raw Task Pack。
3. `route_taskpack.py` 使用 routing matrix 判断项目。
4. 如果路由唯一，脚本只补全缺失的 `project`、`allowed_paths`、
   `forbidden_paths`、`validation_commands`。
5. 正常化后的 Task Pack 写入 `/tmp/agent_loop/taskpack.md`。
6. `validate_taskpack.py` 只验证 normalized Task Pack。

## Safe Autofill Rules

- 只在唯一项目强匹配时补全。
- 不把 T2 降级成 T1。
- 不修改 `risk_tier`、`auto_merge`、`production_deploy`。
- 不移除已有 `forbidden_paths`，只做去重合并。
- 不用 N/A validation 替代真实命令；缺少可运行命令时阻断。
- 不跨项目合并；多项目默认拆成多个 Task Pack。

## Blocking Rules

脚本必须阻断以下情况：

- 没有 metadata wrapper。
- metadata JSON 无法解析。
- project 缺失且无法唯一路由。
- project 指向多个项目。
- allowed paths 指向多个业务项目。
- routing matrix 没有该 project。
- 缺失 validation commands 且 matrix 无可运行默认命令。

阻断时 workflow 添加 `agent:blocked`，并在 audit issue 评论候选项目、
缺失字段和阻断原因。
