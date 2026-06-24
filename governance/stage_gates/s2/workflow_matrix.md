# workflow_matrix.md

状态：PASS

本文件是 S2PC-GATE 只读证据快照，不是新的事实源。实际执行合同以
`.github/workflows/project-governance.yml` 和 `tools/budget_guard.py` 为准。

## CI 事件矩阵

PR/main label：`changed-only fast gate`。

| 事件 | 默认命令 | 是否写仓库 | 是否全量语义/仪表板/attestation |
|---|---|---:|---:|
| `pull_request` | `python3 scripts/lean_governance.py ci --changed-only --base-ref "${GOVERNANCE_BASE_REF}"` | 否 | 否 |
| `push` to `main` | `python3 scripts/lean_governance.py ci --changed-only --base-ref "${GOVERNANCE_BASE_REF}"` | 否 | 否 |
| `workflow_dispatch scope=changed-only` | `python3 scripts/lean_governance.py ci --changed-only` with optional `base_ref` | 否 | 否 |
| `workflow_dispatch scope=project` | `python3 scripts/lean_governance.py validate --project <project> --semantic` | 否 | 仅所选项目 |
| `schedule` | full information-quality, full semantic/drift, generated views artifact | 仓库否，artifact 是 | 是 |
| `workflow_dispatch scope=all` | full information-quality, full semantic/drift, generated views artifact, CI attestation | 仓库否，artifact 是 | 是 |

## Stop Hook 矩阵

| Hook | 行为 |
|---|---|
| Stop Hook | `continue=true`，advisory only，不读文件，不运行全量测试，不阻塞普通开发 |
| 建议命令 | `python3 scripts/lean_governance.py ci --changed-only --base-ref <base_ref>` |
| 全量治理 | schedule 或 manual all scope |

## 机器检查

- `python -B tools/budget_guard.py --self-test`：status=PASS。
- `python -B scripts/governance_setup_doctor.py --json`：workflow_entry_gates.status=PASS。
