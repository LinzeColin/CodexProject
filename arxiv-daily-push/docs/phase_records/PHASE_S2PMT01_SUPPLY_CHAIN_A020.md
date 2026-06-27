# PHASE S2PMT01 Supply Chain A-020

## 状态

- status: `completed_local_validation_with_sbom_ci_gate`
- phase: `S2PM`
- task_id: `S2PMT01`
- finding_id: `A-020`
- finding_title: `依赖、CI Action、SBOM 与权限最小化未形成供应链基线`
- completed_at: `2026-06-27T23:31:39+10:00`

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
- 完整 SBOM 生成缺口已由 2026-06-27 本地确定性 SBOM 摘要关闭；CI 强制执行已由 project-governance changed-only/push/PR 门关闭；联网漏洞数据库查询仍以 fail-closed 本地 finding 输入/例外门作为当前等价 attestation，不执行联网扫描；Action commit SHA 全量 pinning 仍由显式 mutable Action 例外策略和后续 release/security gate 管控。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。


## 2026-06-27 SBOM and CI Enforcement Refresh

- refresh_task_id: `S2PMT01-SUPPLY-CHAIN-A020-SBOM-CI`
- review_task_id: `S2PMT07-P1-A020-TECHNICAL-REVIEW`
- status: `completed_local_validation_no_production`
- generated_at: `2026-06-27 23:31:39 Australia/Sydney`

本轮补上 A-020 先前保留的两个硬缺口：

- 本地确定性 SBOM：`build_dependency_sbom` 解析 `arxiv-daily-push/pyproject.toml`，当前 component_count=`1`、runtime_dependency_count=`0`、build_dependency_count=`1`、sbom_hash=`02e2dae24bb290cc98202dc7d6cc38dabb917b202dc69487935dc8ffcbf7bd49`。
- CI 强制门：`.github/workflows/project-governance.yml` 的 push/PR/changed-only 路径运行 `arxiv-daily-push/tests/test_security_boundary.py`，`audit_supply_chain_ci_enforcement` 当前 status=`pass`。
- 漏洞门：`build_dependency_vulnerability_gate` 仍对 high/critical finding fail closed；无完整 `approved_by`、`expires_at`、`rationale` 的例外会阻断。
- Action 策略：workflow audit 仍要求第三方 Action commit-SHA pinning，GitHub 官方 mutable `actions/*@vN` 只能通过显式 approved mutable refs 例外。

本刷新只改变本地供应链证据门和 CI 测试门；不启用真实 SMTP、不安装 scheduler、不上传 Release、不改公共 Schema/DB/source adapter/ranking/queue、不改 `CURRENT`、不改 V7.1/V7.2 合同文件、不关闭 P0/P1、不声明 Stage 2 production accepted。

新增证据：

- `governance/run_manifests/ADP-S2PMT01-SUPPLY-CHAIN-A020-SBOM-CI-20260627.json`
- `governance/run_manifests/ADP-S2PMT07-P1-A020-TECHNICAL-REVIEW-20260627.json`
- `arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_A020_TECHNICAL_REVIEW.md`
- `.github/workflows/project-governance.yml`
- `arxiv-daily-push/tests/test_security_boundary.py`
