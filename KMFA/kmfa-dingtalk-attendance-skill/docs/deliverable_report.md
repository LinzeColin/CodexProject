---
title: "kmfa-dingtalk-attendance 完整任务包报告"
subtitle: "Skill v0.3 / 阶段二 Shadow Payroll / 数据库与工资基线"
date: "2026-07-07"
geometry: margin=18mm
fontsize: 10pt
mainfont: "Noto Sans CJK SC"
CJKmainfont: "Noto Sans CJK SC"
---

# 结论

本任务包将 KMFA 钉钉考勤流程命名并配置为 `kmfa-dingtalk-attendance-skill`。设计目标不是节省 token，而是把考勤数据做成数据库化、可追溯、可重放、可验收、可进入工资计算基线的稳定流程。

默认策略采用方案 B 的 operator skill 结构，但目标直接按 v0.3：

1. 采集打卡结果、打卡详情、地点、经纬度、基准地点和轨迹证据。
2. 使用 PostgreSQL-compatible schema 作为长期数据库目标。
3. 每月结束后，次月 1-5 日夜间 automation 对上月运行 5 次阶段二 shadow payroll 验证。
4. 5 次 canonical snapshot hash 完全一致，目标月达到 Q5，并生成 payroll baseline candidate。
5. 任意不一致时生成 divergence report，不进入 Q5。

# 任务包结构

```text
KMFA/kmfa-dingtalk-attendance-skill/
  SKILL.md
  references/
  scripts/
  templates/
  agents/openai.yaml

automation/
  morning_prompt.md
  evening_prompt.md

database/
  postgres_schema.sql
  views_payroll_baseline.sql

docs/
  codex_task_pack.md
  acceptance_criteria.md
  stage2_protocol.md
  accuracy_robustness_design.md
  swot_response_matrix.md

schemas/
  *.schema.json

tests/
  test_stage2_consensus.py
```

# 核心验收

| 模块 | 验收标准 |
|---|---|
| Skill | Codex 可显式调用 `$kmfa-dingtalk-attendance-skill` |
| 数据采集 | 打卡结果 + 打卡详情 + 地点/轨迹证据 + raw JSON |
| 数据库 | raw、detail、trajectory、derived facts、policy、stage2、payroll baseline 表齐全 |
| 阶段二 | 次月 1-5 日夜间各一次，共 5 次 |
| 一致性 | 5 次 canonical hash 完全一致 |
| 工资基线 | Q5 后生成 payroll baseline candidate |

# 准确性机制

## 原始证据

所有 DingTalk 响应都保留 raw JSON，并写入 batch、endpoint、request scope、pagination status、raw hash。

## 规范化事实

每条 payroll-facing 事实必须链接 raw IDs、policy version、identity version 和 canonical hash。

## 阶段二一致性

五次运行不是多数票；必须 exact hash consensus。

# 数据库目标

PostgreSQL schema 包含：

- `raw_import_batch`
- `raw_attendance_result`
- `raw_attendance_detail`
- `attendance_trajectory_point`
- `employee_identity_map`
- `attendance_day_fact`
- `attendance_punch_fact`
- `policy_version`
- `rule_config_snapshot`
- `classification_result`
- `exception_case`
- `canonical_month_snapshot`
- `stage2_shadow_run`
- `stage2_consensus_certificate`
- `payroll_baseline_attendance`
- `payroll_export_audit`

# Automation 规则

| 自动化 | 行为 |
|---|---|
| 上午 | health/freshness/gap/anomaly，不跑阶段二 |
| 晚上 | 采集、入库、验证、阶段二候选 |
| 次月 1-4 日晚上 | 写 run_01-run_04 |
| 次月 5 日晚上 | 写 run_05 并比较五次 hash |

# 已验证脚本

已在任务包内验证：

```text
python3 -m py_compile scripts/*.py
python3 tests/test_stage2_consensus.py
month_gate.py evening 2026-08-01 => eligible for 202607 run_01
month_gate.py morning 2026-08-01 => not eligible
month_gate.py evening 2026-08-06 => not eligible
```

# 下一步

把任务包复制到 KMFA repo，按 `docs/codex_task_pack.md` 执行安装、数据库迁移、现有采集适配器接入和 automation prompt 替换。
