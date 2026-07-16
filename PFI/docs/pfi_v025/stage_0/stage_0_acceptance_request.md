# PFI v0.2.5 Stage 0 整阶段用户验收请求

status=prepared_pending_review_commit_attestation_and_user_acceptance
acceptance_id=ACC-PFI-V025-S0-WHOLE-REVIEW
version=v0.2.5
review_base=a590a3da20f2cf569c11114a3f46e1ff1a0ef6f2
review_commit=BOUND_BY_EXTERNAL_POSTCOMMIT_ATTESTATION
evidence_ref=PFI/reports/pfi_v025/stage_0/whole_stage_review/evidence.json
evidence_sha256=f30cab259f84660ef18749288251198f3964720fc2af61e71d198f48fe92954a

## 接受对象

请仅确认以下 Stage 0 范围：

1. 当前 Git、入口/UI/App/runtime、version source、data root/SQLite 与测试收集事实；
2. 固定的 10 个一级入口，包含“市场与研究”；
3. v0.2.5 Active Requirements、历史 6/8/9 入口与旧 closeout 的废弃/参考边界；
4. 38 个 findings、12 个 primary gaps、27 个仍开放的 P0/P1 production blockers；
5. Stage 0 只证明基线与合同可信，不证明 v0.2.5 production、App identity、single listener、真实数据完整、浏览器/UAT 或最终交付；
6. 方向为“先完成真实产品，不扩功能”，Stage 1 仅在本次 evidence-bound acceptance 后另行开始。

## 已知缺陷

- 27 个开放 P0/P1 findings 继续按 `gap_register.md` 路由，不能被本验收视为已修复。
- release/App/runtime/route/data/owner truth 仍存在已登记冲突。
- local tracking `origin/main` stale；authoritative remote main 与本地 Stage 0 历史分叉，但 remote-side PFI drift 为 none。本轮不 fetch/rebase/push。
- generic governance classifier 对 Stage evidence/risk filename 存在已证明的 scope false positive，sparse worktree 还会把未物化 root/test/project paths 报成 missing；本轮保留 legacy STOP，使用 full-tree shadow project governance、changed-scope semantic sync、exact-scope contract 与 external attestation 判定，不修改 root validator 或无关 model/formula/parameter registries。

## 有效确认格式

只有同时绑定 `v0.2.5`、最终 review commit、上述 evidence SHA-256、接受范围、已知缺陷和明确 acceptance statement 的回复才有效。单独回复 `1`、`批准`、`全部同意` 或 blanket execution authorization 不生成 `human_acceptance.json`。

在 external post-commit attestation 完成后，Codex 将给出一条可直接确认的完整 statement。确认前：`Stage 1 = not_started`。
