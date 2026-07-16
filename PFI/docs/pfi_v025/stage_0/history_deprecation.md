# PFI v0.2.5 历史约束废弃政策

本政策是 `PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS` 的 human-auditable derived view。历史材料继续作为事实、失败证据或设计参考保存，但只有经过本表分类且不与 Active Requirements 冲突的内容才可被后续任务引用。历史结果、旧验收结论、旧截图和旧数量均不能独立证明当前完成、当前一致或 v0.2.5 验收。

## 判定规则

- `requirement_disposition` 决定历史内容能否驱动当前实现；`fact_level` 与 `owner_evidence_state` 只描述证据性质，不能替代 disposition。
- `SUPERSEDED` 不删除历史事实，只禁止其继续充当 active requirement 或 current completion proof。
- `REFERENCE_ONLY_*` 只允许在对应参考目的内使用；引用时必须同时保留当前 contract、resolution task 和重新验证要求。
- Active contract、当前仓库证据和本表冲突时，以 Active Requirements 的 authority order 为准，并保持冲突为 blocked，禁止自行“统一”。

## Authority and source hashes

Authority order：latest explicit user decision → pinned v0.2.5 Task Pack/Roadmap → verified current repository/runtime/App/database/test evidence → non-conflicting classified history → historical completion claims have no independent authority。

| source | canonical SHA-256 |
|---|---|
| Roadmap | `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b` |
| Task Pack | `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2` |

任一 digest 或 authority order 不匹配时停止；不得用历史副本、相似文件或旧 closeout 代替 canonical source。

## Navigation history

| item_id | historical_rule_or_class | requirement_disposition | fact_level | owner_evidence_state | evidence_ref | prohibited_use | active_replacement_or_retained_principle | resolution_task |
|---|---|---|---|---|---|---|---|---|
| HIST-NAV-COUNT-06 | 历史六入口导航数量 | SUPERSEDED | EXTRACTED | CONTRADICTED | PFI v0.2.5 Roadmap Appendix A；Active Requirements `official_nav` | 作为当前一级入口数量、当前 IA 或当前验收依据 | 当前正式一级入口固定为有序且唯一的 10 项；旧入口只能按 target compatibility alias 规则保留 | S6-P1-T1；S6-P1-T2；S6-P1-T3 |
| HIST-NAV-COUNT-08 | 历史八入口导航数量 | SUPERSEDED | EXTRACTED | CONTRADICTED | PFI 历史 Stage 1 IA 记录；Active Requirements `official_nav` | 作为 v0.2.5 导航目标或证明 Appendix A 已实现 | 当前目标为 10 个 primary entries；目标与 verified-current route 必须分开记录 | S6-P1-T1；S6-P1-T2；S6-P1-T3 |
| HIST-NAV-COUNT-09 | 历史九入口及“市场与研究非一级入口”规则 | SUPERSEDED | EXTRACTED | CONTRADICTED | PFI v0.2.3 导航恢复记录；PFI v0.2.5 Roadmap Appendix A | 排除“市场与研究”或恢复九入口 | “市场与研究”是第 9 个正式一级入口，canonical target route 为 `/market-research` | S6-P1-T1；S6-P1-T2；S6-P1-T3 |
| HIST-NAV-COUNT-15 | 历史十五入口把 primary 与 alias 混列 | SUPERSEDED | EXTRACTED | CONTRADICTED | PFI v0.2.1 Web Shell 历史；Active Requirements `navigation_policy` | 把 alias、command 或 search input 暴露成 primary navigation | primary inventory 仅 10 项；兼容输入不得进入 primary navigation、accessibility primary tree 或 no-JS primary list | S6-P1-T1；S6-P1-T2；S6-P1-T3 |
| HIST-NAV-COUNT-16 | 历史十六入口或额外 system/development 入口提案 | SUPERSEDED | RECONSTRUCTED | CONTRADICTED | PFI 历史导航材料分类；Active Requirements `official_nav` | 新增第 11 个以上 primary entry 或独立 system/development product entry | 不扩张 10 项 primary contract；系统能力归入现有 PFI 页面或内部 namespace | S6-P1-T1；S6-P1-T2；S6-P1-T3 |
| HIST-MARKET-PRIMARY-BAN | 历史“市场/研究不得作为正式一级能力”限制 | SUPERSEDED | EXTRACTED | CONTRADICTED | PFI v0.2.3 恢复记录；Roadmap Appendix A | 删除“市场与研究”一级入口或以旧限制否决当前目标 | “市场与研究”保留为一个正式一级入口；`/market`、`/research` 仅为 compatibility inputs | S6-P1-T1；S6-P1-T2；S6-P1-T3 |
| HIST-ALIASES-AS-PRIMARY | 首页、市场、研究、持仓、策略实验室、数据与系统等 alias 曾作为一级入口显示 | SUPERSEDED | EXTRACTED | CONTRADICTED | Active Requirements `target_compatibility_aliases` 与 `verified_current_declared_aliases` | 把 compatibility alias 计入 10 个正式入口，或把当前 query destination 误标为 target-complete | alias 只提供兼容解析；primary label、target route 与 verified-current route 分层维护 | S6-P1-T1；S6-P1-T2；S6-P1-T3 |

## Experience and completion history

| item_id | historical_rule_or_class | requirement_disposition | fact_level | owner_evidence_state | evidence_ref | prohibited_use | active_replacement_or_retained_principle | resolution_task |
|---|---|---|---|---|---|---|---|---|
| HIST-DARK-AI-CONSOLE | 默认深色 AI console、证据抽屉或开发工作台方向 | SUPERSEDED | EXTRACTED | CONTRADICTED | Active Requirements `experience_policy.visual_direction` | 作为正式产品默认视觉、页面骨架或高质量验收基线 | 正式体验为 bright / high-quality / restrained / zh-CN；反馈与配置只在 Settings | S5-P1-T1；S5-P1-T2；S7-P1-T1 |
| HIST-TASKPACK-LONGPAGE-PHONE-MOCKUP | Task Pack 长页、anchor-only 导航与手机 mockup/preview 壳 | SUPERSEDED | EXTRACTED | CONTRADICTED | PFI v0.2.5 Roadmap experience requirements；Active Requirements `experience_policy` | 用单长页、换标题模板、iframe/mockup 或截图路径替代真实 route/history/deep-link/refresh | 每个二级页面有独立语义并通过真实 URL、history、focus、error、responsive 证据验收 | S5-P1-T1；S5-P1-T2；S7-P1-T1；S11-P2-T1 |
| HIST-OLD-CLOSEOUT-CLAIMS | v0.2.1-v0.2.4 及旧 Stage/overall closeout 结论 | SUPERSEDED | EXTRACTED | STALE | README、HANDOFF、三份 owner documents 与旧 reports；conflict `PFI-V025-CONFLICT-OWNER-VIEWS` | 声明 v0.2.5、当前 Stage、release identity 或最终交付已完成 | 历史结果保留为过去时；当前状态只能由 v0.2.5 task、acceptance、fresh evidence 与 explicit acceptance 证明 | S0-P3-T1；S12-P3-T1 |
| HIST-PFI-OS-SECOND-ROOT | PFI OS 曾被描述成独立产品根或第二正式 UI | SUPERSEDED | EXTRACTED | CONTRADICTED | Active Requirements `product_boundaries.pfi_os_second_product_allowed=false` | 建立第二 product root、第二 primary UI、第二 owner status 或独立 release identity | `PFI/src/pfi_os` 只可作为 PFI 内部实现 namespace；正式 UI 仍唯一 | S0-P2-T3；S1-P1-T1 |
| HIST-SIDE-REVIEW-HTML | side review HTML、logic review page 或内部审查页曾作为交付面 | SUPERSEDED | EXTRACTED | CONTRADICTED | Active Requirements `execution_policy.completion_proof_disallowed` | 作为正式页面、第二 UI、用户入口或独立验收证明 | 审查材料只能是非产品 evidence；正式 acceptance 绑定 designated render implementation 和真实交互证据 | S11-P2-T1；S11-P3-T1 |
| HIST-FAKE-FINANCIAL-ACCEPTANCE | demo/sample/synthetic/fixture/mock/fake 财务值、单数值或假零验收 | SUPERSEDED | EXTRACTED | CONTRADICTED | Active Requirements `data_policy` 与 `execution_policy.completion_proof_disallowed` | 作为真实财务、ready、confirmed zero、计算正确或产品完成证明 | 只允许真实输入；缺失输入为 `blocked`/`not_run`；financial zero 必须具备完整 provenance 与 confirmed-zero evidence | S3-P1-T1；S4-P1-T1；S11-P1-T1 |
| HIST-FAILURE-EVIDENCE | 旧失败截图、错误日志、回归复现和验收退回记录 | REFERENCE_ONLY_FAILURE_EVIDENCE | EXTRACTED | VERIFIED | 版本化 reports、review findings 与 regression records | 反向证明当前已修复、当前通过或当前 release identity 一致 | 可用于设计 regression 和 stop gate；每个当前结论仍需在当前 commit/runtime 上 fresh rerun | 对应当前 finding 的 Roadmap task；不得省略 fresh validation |

## Retained reference classes

| item_id | historical_rule_or_class | requirement_disposition | fact_level | owner_evidence_state | evidence_ref | prohibited_use | active_replacement_or_retained_principle | resolution_task |
|---|---|---|---|---|---|---|---|---|
| ARCH-SINGLE-UI-AND-REAL-RUNTIME | 单一 PFI UI 与真实本地 runtime 架构原则 | REFERENCE_ONLY_ARCHITECTURE | EXTRACTED | PARTIALLY_VERIFIED | PFI architecture history；Active Requirements `product_boundaries` | 以历史架构说明替代当前 build/runtime identity、listener 或 acceptance 证据 | 保留 single product / single UI 原则；当前实现必须重新证明 frontend/backend/manifest/asset/commit identity | S1-P1-T1；S1-P3-T2；S12-P2-T2 |
| ARCH-IMMUTABLE-RAW-READMODEL-PROVENANCE | immutable raw → normalized/read model → metric provenance | REFERENCE_ONLY_ARCHITECTURE | EXTRACTED | PARTIALLY_VERIFIED | PFI data architecture history；Active Requirements `data_policy.metric_required_provenance` | 推断当前数据完整、指标 ready 或 financial zero | 保留 immutable input 与可追溯 read model 原则；每个 metric 仍需 source/coverage/as_of/formula/parameter/read-model hashes | S3-P1-T1；S4-P1-T1；S11-P1-T1 |
| ARCH-DURABLE-OPS-BACKUP-RESTORE | durable operations、backup 与 restore 原则 | REFERENCE_ONLY_ARCHITECTURE | EXTRACTED | PARTIALLY_VERIFIED | PFI delivery history；Active Requirements `delivery_policy` | 证明当前 App 已备份、可恢复、已安装或交付完成 | 保留备份先于 canonical promotion、失败恢复且不自动重试原则；以 Stage 12 fresh evidence 为准 | S12-P2-T1；S12-P2-T2 |
| ARCH-DETERMINISTIC-CORE-NO-AUTOTRADE | deterministic financial core；无自动下单、支付或实盘执行 | REFERENCE_ONLY_ARCHITECTURE | EXTRACTED | VERIFIED | Active Requirements `product_boundaries.live_trading_or_payment_execution_authorized=false` | 扩张为投资建议正确性、交易授权或生产连接证明 | deterministic rules 与 no-autotrade/no-payment 是持续安全边界，不授权任何 real-money side effect | 所有 Stage；任何例外必须另立 T3 gate 与 explicit user decision |
| REF-FAST-DEEP-PATH | fast path / deep path 的历史执行分层方向 | REFERENCE_ONLY_DIRECTION | EXTRACTED | PARTIALLY_VERIFIED | PFI workflow history；root T0-T3 routing contract | 绕过 model/formula/data/release/safety gate，或以 fast path 自动推进 Phase/Stage | 普通工作可最小化上下文；涉及财务、release、App、schema 或 safety 必须升级并受 one-Phase contract 约束 | 每个 run preflight；高风险任务使用 T2/T3 |
| REF-APPROVED-HTML-DIRECTION | 已批准 HTML 视觉参考与交互方向 | REFERENCE_ONLY_DIRECTION | EXTRACTED | PARTIALLY_VERIFIED | approved design references；Active Requirements `experience_policy` | 把 reference HTML、截图或视觉相似度当作正式实现与 acceptance | 仅保留 bright/high-quality/restrained 方向；正式结果须在 designated render implementation 上验证语义、交互和可访问性 | S5-P1-T1；S7-P1-T1；S11-P2-T1 |
| OVERRIDE-PER-STAGE-DELIVERY | Roadmap 中 Stage 1 canonical install 与 per-Stage delivery 的旧解释 | SUPERSEDED | EXTRACTED | CONTRADICTED | override `PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE`；Active Requirements `delivery_policy` | 每 Stage reinstall/push、Stage 1 修改 canonical entries，或把 isolated candidate promotion 为 final | Stage 1 只验证 disposable isolated candidate；canonical install 仅 `S12-P2-T1` 一次；final main upload 仅在 `S12-P3-T4` explicit acceptance 后一次 | S1-P3-T1；S1-P3-T3；S12-P2-T1；S12-P3-T4 |

## Active conflict projection

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
