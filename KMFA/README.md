# KMFA｜经营分析系统

KMFA 是面向 C-level management / board 的经营分析系统。当前优先级是文件型项目成本分析 MVP：先建立项目治理、数据治理、金额精度、零差异、差异队列、人工处理事件、重跑链路和可追溯经营报告基础。

## 当前状态

| 项目 | 内容 |
|---|---|
| project_id | `KMFA` |
| 当前版本 | `0.1.0-s02p3` |
| 当前 Stage | `S02｜数据治理内核与 metadata 协议` |
| 当前 Phase | `S02-P3｜数据质量等级` |
| 当前 Task | `S2PCT01/S2PCT02/S2PCT03` |
| 风险等级 | `T3`，涉及经营数据、金额、税务、隐私和公开仓库边界 |
| GitHub 目录 | `LinzeColin/CodexProject/KMFA` |
| Stage 上传规则 | S02-P1/P2/P3 已完成且 Stage 2 复审通过；当前可整体上传 GitHub |

## 双平面结构

### 人类可读面

| 文件 | 用途 |
|---|---|
| `README.md` | 项目入口、范围、状态、运行边界 |
| `功能清单.md` | 面向 owner 的功能、限制、证据和下一任务 |
| `开发记录.md` | Stage -> Phase -> Task 开发记录、验收、风险、回滚 |
| `模型参数文件.md` | 模型、公式、参数、质量门禁和验证状态 |
| `HANDOFF.md` | 跨线程交接摘要 |

### 机器可读面

| 文件/目录 | 用途 |
|---|---|
| `docs/governance/project.yaml` | Lean v2 项目事实 |
| `docs/governance/roadmap.yaml` | Lean v2 Roadmap 事实 |
| `docs/governance/events.jsonl` | Lean v2 事件 |
| `docs/governance/*` | v1 兼容治理文件 |
| `metadata/project/project.yaml` | KMFA 内部项目配置草案 |
| `metadata/stage_status.jsonl` | Stage/Phase/Task 状态登记草案 |
| `metadata/model_registry.yaml` | KMFA 内部模型参数机器镜像草案 |
| `metadata/traceability/requirements.csv` | 完整需求追溯矩阵，P0/P1 绑定任务、验收、测试、证据 |
| `tools/no_omission_check.py` | 正式防遗漏检查脚本，可在 CI/本地运行 |
| `stage_artifacts/` | Stage/Phase 证据包 |

## P0 MVP 边界

P0 是文件型项目成本分析 MVP，目标链路如下：

```text
上传/登记权威项目成本资料
-> 原始文件hash与manifest
-> 字段映射
-> A0黄金基准
-> 金额整数分标准化
-> 零差异校验
-> 差异队列
-> 人工处理事件
-> 重跑派生链路
-> 项目成本报告
-> 经营总览摘要
```

当前 `S02-P3` 已建立 Q0-Q5 数据质量等级、A/B/C/D 报告可信等级和报告发布门禁协议，但仍不实现上述业务链路。

## 禁止事项

- 不提交原始敏感数据到公开 GitHub。
- 不自动付款、报税、开票、发工资或发奖金。
- 不对外发送完整经营报告。
- 不在金额计算中使用 float。
- 不把缺数据报告伪装成完整报告。
- 不自动选择 PDF 或 Excel 冲突的一边。
- 不用工具化、营销化、非真实软件感的前端或报告文案。

## 验证命令

当前 S02-P3 最小验证:

```bash
python3 KMFA/tools/check_report_grade_gate.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/metadata_protocol_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
python3 KMFA/tools/no_omission_check.py
git diff --check -- KMFA
```
