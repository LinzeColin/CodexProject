# Stage 2 Phase 2.1 数据根目录决策

## 决策

canonical private runtime root 是逻辑 alias `$PFI_DATA_HOME`。若环境变量未设置，现有 PFI OS 合同解析到显式用户状态 alias `~/.pfi`。当前只读观测为 `user_state_default`，但 Git Evidence 不保存实际绝对路径。

这不是 Task Pack 预设优先级，而是基于当前运行合同和只读事实作出的项目决策：

1. PFI OS 的 private operational state 已由 `$PFI_DATA_HOME` 合同管理，默认解析到 `~/.pfi`。
2. private runtime root 必须位于 public Git 之外。
3. `MetaDatabase/PFI` 当前仅作为历史 Git-object 交易来源，不能兼任 private operational root。
4. `PFI/MetaDatabase` 当前只是 repository placeholder，不是财务数据根。

## Alias 策略

| root | 角色 | 当前状态 | 策略 |
|---|---|---|---|
| `$PFI_DATA_HOME` | canonical private runtime root | active via user-state default | 唯一写入路由合同；本 Phase 不写 |
| `~/.pfi` | explicit user-state alias | aliases canonical in current environment | 显式 alias，不重复计数 |
| `MetaDatabase/PFI` | historical Git-object source | ready read-only object surface | 只读来源，不自动迁移 |
| `PFI/MetaDatabase` | repository placeholder | metadata only | 不冒充真实来源 |

禁止 silent copy、move、merge、delete 或双向同步。后续若更改 `$PFI_DATA_HOME`，必须重新运行 inventory 并显式记录 alias；不能把旧根自动合并到新根。

## 当前风险

- 当前 private root mode 观测为 `0755`，operational SQLite 为 `0644`，存在 group/other permission 风险。本 Phase 只登记风险，不改权限；权限 hardening 需要独立授权与回归。
- operational SQLite 仅证明文件完整、固定 schema 可见且探测前后不变；其 `record_count/coverage/as_of` 保持 `null`，不能推导财务零值。
- 交易来源记录数为 `8815`、coverage 为 `2022-06-06..2026-06-03`；它只证明交易/消费分类 source input available，分类仍需标准化、经济事件、幂等账本与对账合同，不证明任何财务指标可计算。
