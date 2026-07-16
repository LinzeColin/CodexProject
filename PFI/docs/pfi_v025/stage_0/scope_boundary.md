# PFI v0.2.5 产品与集成范围边界

```text
formal_ui = PFI/web/index.html + route/shell modules + local App/localhost wrapper
active_product_count = 1
active_ui_count = 1
designated_render_implementation_per_acceptance = 1
Finder and localhost = two access surfaces to the same build/runtime
```

本文件是 `PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS` 的 human-auditable derived view。PFI 是本合同唯一产品主体；任何 namespace、integration、public shell、独立系统或候选 App 都不得形成第二产品根、第二 active UI 或第二可编辑事实源。

## Authority and source hashes

Authority order：latest explicit user decision → pinned v0.2.5 Task Pack/Roadmap → verified current repository/runtime/App/database/test evidence → non-conflicting classified history → historical completion claims have no independent authority。

| source | canonical SHA-256 |
|---|---|
| Roadmap | `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b` |
| Task Pack | `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2` |

任一 digest 或 authority order 不匹配时停止；不得让 integration 或 candidate surface 从其他来源扩张本合同边界。

## One-product identity matrix

| invariant | active rule | evidence gate |
|---|---|---|
| Product identity | 只有 PFI；Alpha、PFI OS、Cloudflare、QBVS/QuantLab 均不是第二 PFI 产品 | `active_product_count == 1`；owner/release records 只指向 PFI |
| UI identity | 正式 UI 是 `PFI/web/index.html`、route/shell modules 与同一 build/runtime 的 local App/localhost wrapper | `active_ui_count == 1`；每项 acceptance 只指定一个 render implementation |
| Access identity | Finder 与 localhost 是同一 build/runtime 的两个 access surfaces，不是两个交付物 | frontend/backend/manifest/asset/commit identity 与 bundle hashes 相符 |
| Data authority | PFI canonical read model 与 provenance 决定私有财务事实；integration 只能读取明确 allowlist | 禁止 private value 写入 Git/evidence；所有 metric 保留 source/coverage/as_of/formula/parameter/read-model hashes |
| Release identity | isolated candidate、public shell 或独立系统均不能替代 canonical PFI release acceptance | Stage 1 candidate disposable；canonical install 与 final upload 仅在 Stage 12 指定 gate |

## Integration boundary matrix

| surface | owner | allowed_reads | allowed_writes | prohibited_behavior | privacy_class | release_identity | evidence_gate |
|---|---|---|---|---|---|---|---|
| PFI | PFI owner；canonical product governance | PFI real inputs、immutable raw/read-only copies、normalized/read model、approved configuration 与 provenance | 仅在当前 Roadmap task、Acceptance ID 和 exact run allowlist 内写 PFI product/governance artifacts | 第二 product/UI；假财务 fallback；未授权交易/支付；私有值进 Git/evidence；自动 Phase/Stage advancement | private-local；derived evidence 必须 redacted | 唯一 canonical PFI product/release identity | current contract + focused tests + changed-scope governance + explicit acceptance；未解决 conflict 保持 blocked |
| Alpha | 独立 Alpha owner；不由 PFI UI 管理 | 只读 exact eight-field versioned PFI Context：`net_worth_state`、`investable_cash_state`、`cashflow_pressure`、`asset_allocation`、`risk_budget`、`investment_behavior_tags`、`consumption_pressure_summary`、`data_freshness`；envelope metadata 仅 `schema_version`、`as_of`、`source_or_read_model_hash`、`privacy_classification` | none；`alpha_writeback_allowed=false` | 写回 ledger/holdings/trades；成为 PFI primary entry；读取未列明字段；创建 Ralpha；共享凭证或提交交易 | minimized versioned context；按 `privacy_classification` 强制降敏 | 独立 release；不得证明或改变 PFI acceptance | schema/version/hash/privacy allowlist 全等；read-only proof；无 PFI writeback |
| PFI OS / Streamlit internal namespace | PFI internal implementation owner | 同一 PFI build/runtime 所需的 approved local modules 与 read model | 仅作为 PFI 内部 implementation namespace 随当前 task allowlist 修改 | 创建第二 root、第二 active UI、独立 owner status、独立 product navigation 或独立 release identity | 与 PFI 相同的 private-local boundary | 继承唯一 PFI identity；`pfi_os_second_product_allowed=false` | root/UI count 均为 1；wrapper 与 formal UI 的 frontend/backend/manifest/asset/commit identity 相符 |
| Cloudflare public shell | public-shell deployment owner；与 local PFI acceptance 分离 | 只读 qualitative、redacted、explicitly-public data | 仅 public shell 自身允许范围；不得写 local PFI ledger/read model | 读取 private accounts、holdings、reports、SQLite、credentials、absolute paths；替代 local PFI；把 public shell 当 canonical PFI acceptance | public-redacted；禁止 private financial values | 独立 public deployment identity；不是 canonical local release identity | redaction/allowlist audit；private-read count 为 0；external public proof 与 local PFI gate 分开 |
| QBVS / QuantLab | 独立或内部 capability owner | 仅显式 integration contract 所列 qualitative/derived inputs | 仅各自 owner 范围；不得写 PFI canonical facts | 成为 PFI primary entry、第二 product root/UI、接管 PFI investment management 或获得 live-trading authority | independent/minimized；不得继承 PFI private access | 独立 capability identity；不参与 PFI primary release identity | 10-item primary navigation 无该 entry；cross-system contract read-only；no order/payment proof |
| Stage 1 isolated candidate PFI.app | PFI Stage 1 validation owner | source 仅 `PFI/macos/PFI.app`；复制后读取 candidate 与 checkout binding | 只允许复制到 `$STAGE1_TEMP_ROOT/PFI.app`，并写 run-created isolated `HOME`、`PFI_DATA_HOME`、browser profile、runtime cache 与 ports | 修改 `/Applications/PFI.app`、Desktop/Downloads entries 或其他 canonical entry；复用 canonical HOME/data/profile/cache/ports；promote candidate；自动重试 install | isolated-private；candidate/evidence 不含 private values | disposable validation candidate；永不成为 final promoted App | `source_tree_hash`、`copied_bundle_hash`、`checkout_binding_hash`；frontend/backend/manifest/asset/commit match；canonical-entry before/after hash；LaunchServices registration/cleanup record |

## Stage 1 isolated candidate

Stage 1 的唯一允许 App 动作是从 `PFI/macos/PFI.app` 复制一个 candidate 到 run-created、非 canonical 的 `$STAGE1_TEMP_ROOT/PFI.app`。`$STAGE1_TEMP_ROOT` 必须由该 run 使用 `mktemp` 创建；candidate 必须隔离 `HOME`、`PFI_DATA_HOME`、browser profile、runtime cache 与 ports。允许通过 Finder 启动 candidate，但启动、注册、清理和销毁过程不得改写 `/Applications/PFI.app`、`~/Desktop/PFI.app`、`~/Downloads/PFI.app` 或任何 canonical entry。candidate disposable、never final promoted；缺任一 binding/identity/before-after proof 即 blocked。

## Approved governance companion override

Override `PFI-V025-S0-GOVERNANCE-COMPANIONS` 仅允许 Phase 0.2 的八个 Roadmap core artifacts 与十二个具名 governance companions 组成 exact twenty-path implementation ledger。它不授权 root tool、schema、project registry、测试、UI、runtime、data、App、其他项目或任何第 21 条路径。合同内状态保持 `approved_pending_validation` 且 `blocks_phase_0_2_candidate=true`，直至 exact path coverage、sparse-aware preflight、atomic commit 与 post-commit external attestation 全部通过；失败或缺项继续 blocked，不得自行回写为 resolved。

## Derived active-contract projection

下列 payload 从 canonical Active Requirements 派生，不是独立可编辑事实源。

<!-- PFI_V025_ACTIVE_PROJECTION_BEGIN -->
{
  "contract_id": "PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS",
  "blocking_conflicts": [
    {
      "conflict_id": "PFI-V025-CONFLICT-OWNER-VIEWS",
      "requirement_disposition": "BLOCKING_CURRENT_CONFLICT",
      "status": "blocked",
      "blocks_phase_0_2_candidate": false,
      "resolution_tasks": [
        "S0-P3-T1",
        "S12-P3-T1"
      ]
    },
    {
      "conflict_id": "PFI-V025-CONFLICT-RELEASE-IDENTITY",
      "requirement_disposition": "BLOCKING_CURRENT_CONFLICT",
      "status": "blocked",
      "blocks_phase_0_2_candidate": false,
      "resolution_tasks": [
        "S1-P1-T1",
        "S12-P3-T1"
      ]
    },
    {
      "conflict_id": "PFI-V025-CONFLICT-APP-IDENTITY",
      "requirement_disposition": "BLOCKING_CURRENT_CONFLICT",
      "status": "blocked",
      "blocks_phase_0_2_candidate": false,
      "resolution_tasks": [
        "S12-P2-T1"
      ]
    },
    {
      "conflict_id": "PFI-V025-CONFLICT-RUNTIME-LISTENERS",
      "requirement_disposition": "BLOCKING_CURRENT_CONFLICT",
      "status": "blocked",
      "blocks_phase_0_2_candidate": false,
      "resolution_tasks": [
        "S1-P3-T2",
        "S12-P2-T2"
      ]
    },
    {
      "conflict_id": "PFI-V025-CONFLICT-STALE-ROUTE-MARKERS",
      "requirement_disposition": "BLOCKING_CURRENT_CONFLICT",
      "status": "blocked",
      "blocks_phase_0_2_candidate": false,
      "resolution_tasks": [
        "S1-P1-T1",
        "S6-P1-T1",
        "S6-P1-T2",
        "S6-P1-T3",
        "S12-P3-T1"
      ]
    },
    {
      "conflict_id": "PFI-V025-CONFLICT-ROUTE-TARGET-GAP",
      "requirement_disposition": "BLOCKING_CURRENT_CONFLICT",
      "status": "blocked",
      "blocks_phase_0_2_candidate": false,
      "resolution_tasks": [
        "S6-P1-T1",
        "S6-P1-T2",
        "S6-P1-T3"
      ]
    },
    {
      "conflict_id": "PFI-V025-CONFLICT-GOVERNANCE-SCOPE",
      "requirement_disposition": "BLOCKING_CURRENT_CONFLICT",
      "status": "approved_pending_validation",
      "blocks_phase_0_2_candidate": true,
      "resolution_tasks": [
        "S0-P3-T1"
      ]
    }
  ],
  "policy_overrides": [
    {
      "override_id": "PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE",
      "authority": "latest_user_decision",
      "source_contract": "PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md:S1-P3-T1,S1-P3-T3",
      "original_action": "canonical_app_install_and_entry_replacement_in_stage_1",
      "status": "superseded",
      "effective_rule": "stage_1_uses_isolated_disposable_candidate_without_canonical_entry_mutation",
      "replacement_gate": "canonical_install_only_at_S12-P2-T1_after_stage_12_preconditions",
      "evidence_ref": "PFI/docs/pfi_v025/stage_0/run_contract.md#approved-policy-overrides"
    },
    {
      "override_id": "PFI-V025-S0-GOVERNANCE-COMPANIONS",
      "authority": "latest_user_decision",
      "source_contract": "PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md:Stage_0_allowed_files",
      "original_action": "stage_0_phase_0_2_writes_limited_to_eight_core_artifacts",
      "status": "superseded",
      "effective_rule": "phase_0_2_allows_exact_eight_core_artifacts_plus_twelve_named_governance_companions",
      "replacement_gate": "exact_twenty_path_ledger_plus_sparse_aware_preflight_and_postcommit_attestation",
      "evidence_ref": "PFI/docs/pfi_v025/stage_0/scope_boundary.md#approved-governance-companion-override"
    }
  ]
}
<!-- PFI_V025_ACTIVE_PROJECTION_END -->
