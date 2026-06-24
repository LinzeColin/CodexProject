# renderer_field_matrix.md

状态：PASS

本文件是 S2-GATE 只读证据快照，不是新的事实源。字段事实仍以项目
`docs/governance/project.yaml`、`roadmap.yaml`、`events.jsonl` 和
`scripts/lean_governance.py` 渲染器为准。

## 渲染字段矩阵

| 人类视图 | 关键字段 | 来源 | S2 结果 |
|---|---|---|---|
| `功能清单` | feature id、name、description、status、owner、acceptance、risk、evidence | `project.yaml` | 已从 canonical facts 渲染，禁止链接页降级 |
| `开发记录` | Stage -> Phase -> Task、Stop Conditions、Stop Gates、pass criteria、evidence、failure action | `roadmap.yaml` | 已渲染产品 roadmap，不渲染组合治理 roadmap |
| `开发记录` | blockers、next_unique_task、task test commands/results、risks、rollback | `roadmap.yaml` 和 `events.jsonl` | S2PBT02 改为 canonical 派生，去除硬编码 `NOT_APPLICABLE` 覆盖 |
| `模型参数文件` | model、formula、parameter、version、active counts | `project.yaml` | active 只统计 `status=active`，不混入 deprecated/proposed |
| 三个中文视图 | no-op write | 当前文件内容 SHA 与渲染结果比较 | S2PBT03 支持内容相同不写入，支持 `--view` 单视图 |

## 机器校验证据

- `python -B scripts/lean_governance.py validate --all`：errors=0，warnings=0。
- `python -B scripts/lean_governance.py ci --changed-only --base-ref HEAD~1`：8 个目标项目
  `check_render.drift_count=0`，`reference_issue_count=0`，`write=false`。
- S2PBT02 commit：`e05aa93e`。
- S2PBT03 commit：`ffb60236`。

## 关键边界

- `roadmap_kind: product` 是进入项目 `开发记录` 的前置机器门。
- 组合治理整改 Roadmap 不写入任何项目产品开发记录。
- 本文件仅记录 gate 证据，不参与渲染计算。
