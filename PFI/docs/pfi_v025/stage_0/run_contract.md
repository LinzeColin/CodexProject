# PFI v0.2.5 Stage 0 / Phase 0.2 Run Contract

## Identity and Acceptance

| field | value |
|---|---|
| contract_id | `PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS` |
| acceptance_id | `ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT` |
| roadmap_tasks | `S0-P2-T1`、`S0-P2-T2`、`S0-P2-T3`、`S0-P2-T4` |
| risk_tier | `T2` |
| run_mode | `IMPLEMENT` |
| max_phases_per_run | `1` |
| candidate_result | Phase-local only；不等于 Stage 0、v0.2.5 或 overall acceptance |

本 run 只冻结 Active Requirements、历史 disposition、scope boundary、run rules、Phase evidence 及获批 governance companions。未解决 conflict 保持可见；任何文档、toast、marker、string-only test、fake screenshot、screenshot path 或 single number 都不能独立证明完成。

## Authority and source hashes

Authority order：latest explicit user decision → pinned v0.2.5 Task Pack/Roadmap → verified current repository/runtime/App/database/test evidence → non-conflicting classified history → historical completion claims have no independent authority。

| source | canonical identity |
|---|---|
| Roadmap | `/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md`；SHA-256 `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b` |
| Task Pack | `/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip`；SHA-256 `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2` |
| Approved design | `PFI/docs/pfi_v025/stage_0/PHASE_0_2_DESIGN.md` |
| Machine contract | `PFI/config/pfi_v025_active_requirements.json`；schema `PFIV025ActiveRequirementsV1` |

Source hash、ZIP integrity、contract identity 或 authority order 任一不符时停止；不得以相似文件、旧版本、历史 closeout 或 reconstructed value 代替。

## Exact read set

允许读取仅限完成本 Phase contract 所需的最小集合：

1. 上述 pinned Roadmap、Task Pack ZIP 与 approved Phase 0.2 design。
2. `PFI/config/pfi_v025_active_requirements.json` 及本 Phase 新建的三份 human policy/evidence quartet。
3. 为 verified-current navigation parity 而只读 `PFI/web/app/routes.js`、`PFI/web/app/shell.js`；不得修改。
4. 当前 Git identity、branch/upstream、HEAD、refs、live advertised main、merge-base、path-limited PFI diff 与 exact twenty-path status。
5. 十二个具名 governance companions，只为本 contract iteration、traceability、status 和 changed-scope validation。
6. Task Pack 中 Phase schema/validator 所需成员，只在 guarded temporary extraction root 读取；不得写回 source ZIP。
7. 受保护路径只允许 metadata-only aggregate fingerprint；不得读取或输出 private financial/App file contents、individual protected paths 或 credentials。

任何新增 read surface 必须证明与唯一 Acceptance 直接相关；否则停止并保持最小范围。

## Exact twenty-file write set

唯一允许 write ledger 是以下八个 core artifacts：

1. `PFI/config/pfi_v025_active_requirements.json`
2. `PFI/docs/pfi_v025/stage_0/history_deprecation.md`
3. `PFI/docs/pfi_v025/stage_0/scope_boundary.md`
4. `PFI/docs/pfi_v025/stage_0/run_contract.md`
5. `PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json`
6. `PFI/reports/pfi_v025/stage_0/phase_0_2/terminal.log`
7. `PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt`
8. `PFI/reports/pfi_v025/stage_0/phase_0_2/risk_and_rollback.md`

以及十二个获批 governance companions：

9. `PFI/docs/governance/MODEL_SPEC.md`
10. `PFI/docs/governance/model_registry.yaml`
11. `PFI/docs/governance/formula_registry.yaml`
12. `PFI/docs/governance/parameter_registry.csv`
13. `PFI/docs/governance/DEVELOPMENT_LEDGER.md`
14. `PFI/docs/governance/development_events.jsonl`
15. `PFI/docs/governance/delivery_tasks.yaml`
16. `PFI/docs/governance/TRACEABILITY_MATRIX.csv`
17. `PFI/docs/governance/VERSION_MATRIX.yaml`
18. `PFI/docs/governance/STATUS.md`
19. `PFI/docs/governance/OWNER_STATUS.md`
20. `PFI/CHANGELOG.md`

Allowed-path set 必须 exactly equal 上述集合：不能少一条、不能多第 21 条。companions 只记录本 contract iteration，不得编造 model、formula、parameter、version、test result、owner decision 或 resolved conflict。

## Explicit non-goals and forbidden paths

- 不修改 UI、routes、shell、runtime、source code、tests、schemas、formula、parameter、SQLite、raw/processed data 或真实财务值。
- 不修改 `PFI/README.md`、`PFI/HANDOFF.md`、`PFI/VERSION`、`PFI/功能清单.md`、`PFI/开发记录.md`、`PFI/模型参数文件.md`；这些 current conflicts 由后续 task 解决。
- 不创建第二 product root/UI、PFI OS product、Ralpha、Alpha page、Cloudflare private-data bridge 或 QBVS/QuantLab primary entry。
- 不读取、写入、安装、替换或修复 `/Applications/PFI.app`、`~/Desktop/PFI.app`、`~/Downloads/PFI.app`、`~/.pfi`、repo data/MetaDatabase 或 caches；本 Phase 不启动/停止 listener。
- 不执行 ordinary fetch、pull、rebase、merge、push、force-push、tag/release、GitHub upload 或 ref mutation；仅 preflight 明确允许的 exact advertised-SHA object hydration 可在 refs/FETCH_HEAD/shallow 全量不变证明下发生。
- 不执行 Phase 0.3、whole-Stage review、Stage 1 或任何 later Stage；不声明 Stage 0/v0.2.5/overall complete。

## Preflight and stop conditions

Preflight 必须证明：canonical cwd/git root；branch `codex/pfi`；upstream `origin/main`；configured origin；frozen `PHASE_BASE`；pre-write clean porcelain；live main 可解析且 remote-side PFI diff quiet；两份 source hashes 与 ZIP integrity 正确；八个 core artifacts 起始不存在、十二 companions 存在；guarded metadata-only before fingerprint 已记录。

任一条件成立即停止，不写/不提交/不推进：

- branch/upstream/root/HEAD/source hash/ZIP/contract identity 不符，或 live-main PFI drift 不可安全分类；
- unknown or unrelated worktree change、forbidden path change、allowed set 非 exact 20、index 与 worktree coverage 不一致；
- canonical JSON、三份 projection、schema、semantic、route parity、source hashes、privacy scan、diff check 或 governance gate 失败；
- private value、credential、absolute private path、financial fallback、non-ready zero、伪造 evidence 或未绑定 resolution task 的 `UNKNOWN` 出现；
- protected metadata before/after 不同，App/entry/data/cache/listener 发生 side effect，或 rollback evidence 不完整；
- governance conflict 未获得 external post-commit attestation，却被写成 resolved/candidate pass；
- blocked review finding 被跳过、waive 或改写为 acceptance。

### Runtime stop gates

`PFI-V025-CONFLICT-RUNTIME-LISTENERS` 当前保持 `blocked`。本 Phase 只记录该事实，不探测性终止进程、不选择 preferred listener、不启动新 runtime，也不以现有 localhost health 证明 acceptance；由 `S1-P3-T2` 解决 preferred runtime，并在 `S12-P2-T2` fresh re-verify。

## Validation commands and expected evidence

Validation 必须 fresh 执行并把真实 command、exit code 与必要 stdout/stderr 写入 `terminal.log`，聚合结论写入 `evidence.json`：

1. 三份 policy existence assertion：exit `0`。
2. 从 canonical JSON 重新构造 projection，逐份解析 marker 中 JSON 并要求 semantic equality；7 conflicts、2 complete overrides、3 identical payloads：exit `0`。
3. Active Requirements strong semantic/type/route gate 与 Task Pack schema validator：exit `0`。
4. 对 history 21 个 exact row IDs/dispositions、scope 6 个 exact surface rows/8 Alpha fields、run 13 ordered sections、exact 20 paths、source hashes、Stage sequence 和 mandatory stop statement 做 deterministic assertion：exit `0`。
5. `git diff --check`、private-value/forbidden-path scan、exact changed-files ledger、index/worktree parity：exit `0`。
6. focused changed-scope governance、sparse-aware preflight、atomic commit 后 external attestation 与 protected metadata after comparison：全部 exit `0` 才能给 Phase candidate result。

存在性或文档自述只证明 artifact 可读取，不证明 schema/semantic/governance、commit、side-effect 或 acceptance gate。

## Data/DB/App/migration impact = none

本 Phase 对 data、database、App、migration、network runtime、canonical entry、user data 和 financial calculations 的允许影响均为 `none`。只能产生 exact twenty repository artifacts、声明的 guarded temporary evidence 与一次后续 atomic Phase commit。任何 protected metadata delta 都是 hard stop，不能解释成“预期副作用”。

## Stage boundary review sequence

唯一允许顺序是：

```text
whole-Stage fresh review -> findings remediation -> re-review pass -> explicit acceptance -> next Stage
```

每个 Stage 必须独立 fresh review；findings 必须先 remediation，再由 re-review 明确通过，最后取得 explicit user acceptance。A blocked finding cannot be waived into acceptance. Phase candidate、local commit、green focused test、prepared evidence 或 reviewer draft 均不得自动推进 Phase/Stage。

## Stage 1 isolated-candidate override

Override `PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE` supersedes Roadmap `S1-P3-T1/S1-P3-T3` 中 Stage 1 canonical install/entry mutation 的解释。Stage 1 只可从 `PFI/macos/PFI.app` 复制到 run-created `$STAGE1_TEMP_ROOT/PFI.app`，隔离 `HOME`、`PFI_DATA_HOME`、browser profile、runtime cache、ports，并记录 source/copied/checkout hashes、frontend/backend/manifest/asset/commit identity、canonical-entry before/after hash 与 LaunchServices registration/cleanup。candidate disposable、never final promoted；不修改 `/Applications`、Desktop、Downloads entries。

## Stage 12 single install/upload transaction

Canonical App install 仅在 `S12-P2-T1` 发生一次：先从 `release_content_commit` fresh rebuild candidate，验证 `build_hash`、`asset_hash`、`commit_hash`，备份 canonical App，再 promotion；失败恢复 backup，`automatic_install_retry_allowed=false`。安装后在 `S12-P2-T2` 独立验证 installed-App identity 与 listener/runtime。

Final GitHub main upload 仅在 `S12-P3-T4` explicit acceptance 后发生一次：冻结 `expected_remote_main_sha`，证明 strict fast-forward；`release_content_commit` 冻结 runtime content，`acceptance_candidate_commit` 绑定 pending request/evidence 且不改 runtime，`final_record_commit` 只 append accepted record 且不声称自己的 SHA。release-content freeze 后禁止 rebase/merge/runtime-content commit。single push 必须从 exact `expected_remote_main_sha` fast-forward 到 `final_record_commit`，force push 禁止；随后分别证明 remote parity、installed App identity、local owner-view consistency。

Pre-push remote drift 或 remote unchanged 的 failed push：保持 blocked、restore saved canonical App、等待新 explicit decision。若 remote 已更新但 post-push/parity 失败：冻结 remote/local/App state，禁止自动 App rollback、remote rewrite、force push 或第二次 install/push，等待 explicit recovery decision。

### Release identity gates

`PFI-V025-CONFLICT-RELEASE-IDENTITY` 与 `PFI-V025-CONFLICT-APP-IDENTITY` 当前均为 blocked。Stage 1 candidate 证明不能声明 canonical App 为 v0.2.5；release identity 由 `S1-P1-T1` 开始收敛，在 `S12-P2-T1` install proof 与 `S12-P3-T1` owner/release normalization 后，才由 external evidence 判断。

## Pre-commit rollback

在 atomic Phase commit 前发现失败时，立即停止；保存 terminal/risk evidence，撤销 index 中 exact twenty paths，并仅对本 run 已确认修改的 companions 恢复 `PHASE_BASE` 内容、移除本 run 确认新建的八个 core artifacts。不得运行 whole-tree `reset --hard`、不得覆盖用户/其他 agent 改动、不得删除 protected data/App/cache。随后证明 exact twenty paths 已恢复、其他 porcelain 与 protected metadata 相对 before baseline 不变；不能证明时升级 blocked。

## Post-commit append-only-safe compensating rollback

Phase commit 后禁止 amend、rebase、history rewrite、force push 或伪造原 evidence。若尚未 push 且必须回滚，使用新的 path-limited compensating commit 反向恢复 Phase commit，并 append rollback event/evidence；若已 push 或 external attestation 已绑定，则冻结状态，记录 failing gate、commit identities 与 protected metadata，等待 explicit recovery decision。任何 rollback 都不能把已发生事实从 append-only history 中删除，也不能自动进入 Phase 0.3。

## Approved policy overrides

- `PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE`：Stage 1 canonical install/entry replacement 已 superseded；replacement gate 是 `S12-P2-T1`。
- `PFI-V025-S0-GOVERNANCE-COMPANIONS`：本 Phase 仅获批 exact 8 core + 12 named companions；contract 内仍 `approved_pending_validation`，external post-commit attestation 前继续 block candidate pass。

## Mandatory stop statement

```text
Stage 0 / Phase 0.2 candidate result; do not enter Phase 0.3 in this run.
```

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
