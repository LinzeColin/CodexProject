# 证据包模板 · ADP V0.1 每任务

> 复制此结构到 `docs/pursuing_goal/v0_1/evidence/<TASK_ID>/`。**缺任何适用项，状态只能是 INCOMPLETE。**
> 每任务开工前先答 6 个问题；完成以 `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` 结束；**实现者不自签 Stage Gate PASS**。

## 目录结构

```text
evidence/<TASK_ID>/
  TASK_REPORT.md              # 必需：见下方骨架
  changed_files.txt           # 必需：非空；与 git diff --name-only 逐字一致
  commands.log                # 必需：可复现验收命令与结果
  cost_value.json             # 必需：含 release_mode + recurring_cloud_cost_delta_usd_month（UNKNOWN≠0）
  known_gaps.md               # 必需：未解决项 + 派工
  git.diff                    # 适用：改动补丁
  test-results/               # 适用：代码任务
  benchmarks/before.json+after.json   # 适用：性能任务
  screenshots-or-videos/      # 适用：UI 任务（二进制不入仓时以文字+指纹替代并说明）
  data-samples/               # 适用：数据任务
  migration.sql + rollback.sql# 适用：schema 任务
  deployment_manifest.preview.json    # 适用：部署任务（NOT_DEPLOYED 标 N/A）
```

## TASK_REPORT.md 骨架

```markdown
# TASK_REPORT · <TASK_ID>｜<标题>

## 唯一目标（达成）
<一句话>

## 六个开始前问题（已回答）
1. 唯一目标；2. 允许修改文件；3. 绝不能改变的行为；4. 基线 build+data；5. 验收命令+业务验证；6. 回滚。

## 交付物
<列出并指向文件>

## 验收结果（实测）
<逐条对照 acceptance>

## Data / Performance / Visual
<before → after 或 N/A>

## Value / Cost
- Value：<measured>
- Cost：<measured；UNKNOWN≠0>

## Known gaps
见 known_gaps.md

## 不适用证据项
<列出 N/A 项及原因>

## 完成声明
​```text
Task / Commit / Files changed / Tests / Business evidence /
Data-Performance-Visual / Value / Cost / Known gaps /
Deployment / Rollback / Verifier: 待独立上下文复核（实现者不自签 PASS）
​```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
```

## 自检（提交前）

```bash
python3 tools/check_dag.py                       # 90 唯一 + 无环
python3 tools/validate_evidence.py <TASK_ID>     # READY 或 INCOMPLETE（不会给 PASS）
python3 tools/task_runner.py <TASK_ID>           # 依赖就绪 + 证据完整（不会给 PASS）
```
