# PHASE S2PAT05 Roadmap Stop Code A-021

## 状态

- status: `completed_local_validation`
- phase: `S2PA`
- task_id: `S2PAT05`
- finding_id: `A-021`
- finding_title: `Roadmap 依赖为空、Stop Code 混用自由文本，机器门不可可靠执行`
- completed_at: `2026-06-26T21:16:10+10:00`

## 范围

本记录补强 V7.1 inherited P1 finding `A-021` 的 V7.2 本地机器门证据：

- V7.2 validator 新增 Roadmap 机器门。
- `stop_codes_v7_2.yaml` 的注册 Stop Code 与 inherited V7.1 Stop Code 会合并为允许集合。
- Roadmap 中任意 `stop_conditions` 必须是数组，且每项必须命中注册 Stop Code。
- Roadmap 中任意 `dependencies`、`depends_on`、`required_dependencies` 必须是数组；依赖目标必须能在 Roadmap 任务引用中定位。
- 明确定义的任务依赖图不得自依赖或形成环。
- validator 输出 `roadmap_machine_gate` 指标，便于后续 agent 和 CI 直接判断。

## 非范围

本记录不修改 V7.1 只读历史基线，不改 V7.2 product/CURRENT/roadmap/stop-code 合同内容，不启用真实 SMTP，不安装 scheduler，不上传 Release，不改公共 Schema、DB migration、source adapter、ranking、queue 或邮件生产开关；不关闭 inherited P0/P1；不声明 `INTEGRATED_PRODUCTION_ACCEPTED`、`DAILY_OPERATION` 或 Stage 2 生产通过。

## 代码证据

- `arxiv-daily-push/docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py`
- `arxiv-daily-push/tests/test_v7_2_roadmap_machine_gate.py`
- `governance/run_manifests/ADP-S2PAT05-ROADMAP-STOP-CODE-A021-20260626.json`

## 验证

- `py_compile`: PASS
- `python3 -m unittest arxiv-daily-push/tests/test_v7_2_roadmap_machine_gate.py -q`: 5 OK
- `python3 arxiv-daily-push/docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root arxiv-daily-push/docs/pursuing_goal/v7_2`: PASS, `roadmap_machine_gate.status=PASS`
- `python3 -m unittest discover -s arxiv-daily-push/docs/pursuing_goal/v7_2/tests -q`: 4 OK
- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: 518 OK
- `python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 / warnings 0
- `python3 scripts/validate_governance_sync.py`: errors 0 / warnings 0
- `python3 scripts/lean_governance.py render --project arxiv-daily-push --write`: updated 3 generated three-base views
- `python3 scripts/lean_governance.py check-render --project arxiv-daily-push`: drift 0 / reference issues 0
- `python3 -m json.tool governance/run_manifests/ADP-S2PAT05-ROADMAP-STOP-CODE-A021-20260626.json`: PASS
- `git diff --check`: PASS
- `python3 scripts/validate_semantic_extractors.py arxiv-daily-push`: non-blocking long-run attempt interrupted after more than 60 seconds; not claimed as PASS

## 剩余阻断

- 本修复只提供 A-021 的 V7.2 本地机器门整改证据。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。
