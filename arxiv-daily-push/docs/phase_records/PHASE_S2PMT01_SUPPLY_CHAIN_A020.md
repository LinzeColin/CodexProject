# PHASE S2PMT01 Supply Chain A-020

## 状态

- status: `completed_local_validation`
- phase: `S2PM`
- task_id: `S2PMT01`
- finding_id: `A-020`
- finding_title: `依赖、CI Action、SBOM 与权限最小化未形成供应链基线`
- completed_at: `2026-06-26T21:28:09+10:00`

## 范围

本记录补强 V7.1 inherited P1 finding `A-020` 的本地供应链机器门证据：

- `build_supply_chain_baseline` 现在包含 workflow 静态审计、Action 引用策略和依赖漏洞例外门。
- workflow 静态审计扫描 ADP/Governance workflow 的 `permissions` 与 `uses:` 引用，不执行 workflow、不联网。
- `contents: write`、`permissions: write-all` 和未知未固定第三方 mutable Action 引用会阻断。
- 当前 GitHub 官方 `actions/*@vN` 引用必须在显式例外清单内，并带理由；生产启用前仍需独立复审。
- 高/严重依赖漏洞发现必须有包含 `approved_by`、`expires_at`、`rationale` 的例外记录，否则阻断。
- 当前 main 上 9 个 ADP/Governance workflow 的本地扫描结果为 `pass`，Action refs 44，权限声明 13，issues 0。

## 非范围

本记录不启用真实 SMTP，不安装 scheduler，不上传 Release，不改 workflow 行为，不生成完整 SBOM，不把所有 Action 引用改为 commit SHA，不执行联网漏洞数据库查询，不改公共 Schema、DB migration、source adapter、ranking、queue、`CURRENT` 或 V7.1/V7.2 合同文件；不关闭 inherited P0/P1；不声明 `INTEGRATED_PRODUCTION_ACCEPTED`、`DAILY_OPERATION` 或 Stage 2 生产通过。

## 代码证据

- `arxiv-daily-push/src/arxiv_daily_push/security_boundary.py`
- `arxiv-daily-push/tests/test_security_boundary.py`
- `governance/run_manifests/ADP-S2PMT01-SUPPLY-CHAIN-A020-20260626.json`

## 验证

- `py_compile`: PASS
- `python3 -m unittest arxiv-daily-push/tests/test_security_boundary.py -q`: 7 OK
- `python3 -m unittest arxiv-daily-push/tests/test_security_boundary.py arxiv-daily-push/tests/test_user_center_candidate_pool.py -q`: 14 OK
- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: 522 OK
- V7.2 validator: PASS
- ADP project governance: errors 0 / warnings 0
- changed-only governance semantic: errors 0 / warnings 0
- governance sync validator: errors 0 / warnings 0
- lean check-render: drift_count 0 / reference_issue_count 0
- YAML/JSON/JSONL/CSV/manifest parse: OK
- `git diff --check`: PASS
- current workflow audit: `status=pass`, `workflow_count=9`, `action_refs=44`, `permission_refs=13`, `issues=0`

## 剩余阻断

- 本修复只提供 A-020 的本地机器门整改证据。
- 完整 SBOM 生成、联网漏洞数据库查询、Action commit SHA 全量 pinning 和 CI 强制执行仍需后续独立任务或 release/security gate 明确拥有。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。
