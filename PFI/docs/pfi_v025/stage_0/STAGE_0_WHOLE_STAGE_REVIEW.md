# PFI v0.2.5 Stage 0 整阶段审查

## 1. 唯一目标与边界

- Review ID：`PFI-V025-S0-WHOLE-REVIEW`
- Iteration：`ITER-20260712-PFI-V025-S0-WHOLE-REVIEW`
- Acceptance target：`ACC-PFI-V025-S0-WHOLE-REVIEW`
- Review base：`a590a3da20f2cf569c11114a3f46e1ff1a0ef6f2`
- Authority：SHA-256 为 `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b` 的 Roadmap，以及 SHA-256 为 `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2` 的 Task Pack。

本轮只复核 Stage 0 的 Phase 0.1、0.2、0.3、FND-030 补偿、六项 Acceptance Criteria、Stop Conditions、隐私边界与 Stage Closeout。未执行 Stage 1、业务 UI、产品逻辑、模型/公式/参数、App 安装、runtime 变更、数据或数据库写入、GitHub push。

## 2. Durable evidence chain

| layer | commit / binding | durable fact |
|---|---|---|
| Phase 0.1 | `332953e002162bce1b28aa616b24ddaa936f1935` | evidence SHA-256 `2f45b6b9774b24a0bc990d9476e13448604cdd9169e82e37f0c14c7c8daddf35` |
| Phase 0.2 | `7433be0d70bdae42959c1b71753d93f8737db60d` | evidence `d0e7e3c4413404c0dee91b1173b8d3e270c50faa6f06c3fc4cdd24ff90b6a1f8`；external attestation `8b579f727c9fdbe55fe8e9455ec28a4d7c6c45b4caf47fb7dbe1d6226859c60a` |
| Phase 0.3 original | `31368570082c34eca50c72c7d7b2ef46b0e6854d` | evidence `599648821cc2275693b8495516e342c3db6a3cc9e211c3a1e187da0fe4a09d31`；request `f71c70d15dc1c4c8f873833ba0df94ae3539a35352e7697ef523cd5ffbef4814`；attestation `b439444de5a110f07f48fe0fa1d566624183a38e4d7270d0f0bc6fb2e6d696d6` |
| FND-030 compensation | `a590a3da20f2cf569c11114a3f46e1ff1a0ef6f2` | corrected evidence `06201b1ed07c85970a2af1f91f4c8da72161d8cc04755f02c2e5741e7e8aa864`；corrected request `fc7327bb5cdec0dd34dac86fe0fa82389949707c360ea914ad44be7e672bad44`；external attestation `2161efc16fdd178dba81ff5da5b97633656d433da8a26c1f71896625b1905b13`，状态 `resolved_by_approved_compensation_override`，`blocks_phase_candidate=false` |

旧 Phase 文件中的 pre-commit/pending 文本是 commit-qualified 历史快照，不回写；本整阶段 index 是补偿后当前层。原始 P03 evidence/request 只按 `3136857:<path>` 解释，防止把后来补偿后的工作树误当成原提交内容。

## 3. 审查发现与整改

| finding_id | severity | current status | correction |
|---|---:|---|---|
| `PFI-V025-S0-REVIEW-C01` | Critical | fixed | 新增 durable whole-stage evidence、review audit、execution ledger、risk/rollback 与 evidence-bound 用户验收请求；Stage 1 仍未授权。 |
| `PFI-V025-S0-REVIEW-I01` | Important | fixed | 新增可直接执行的 read-only verifier；terminal 只把完整 argv 记为 `COMMAND`，独立审查和临时 shadow setup 分别记为 typed review/result records，不伪装成可重放命令。 |
| `PFI-V025-S0-REVIEW-I02` | Important | fixed | 将 trace、event、delivery 与 owner/status 的 lifecycle 统一为仍等待 external review-commit attestation 和 evidence-bound user acceptance。 |
| `PFI-V025-S0-REVIEW-M01` | Minor | fixed | 不改写 immutable P03 evidence；新增 correction-specific `line_exact` selector overlay，唯一绑定历史 FND-030 priority row，并明确旧宽 selector 被 supersede。 |

`git@github.com` 两处 email-like 命中是 SSH remote token，不是 author email、PII 或 credential；复判后 privacy finding 为 0。

## 4. Roadmap Acceptance verdict

| criterion | verdict | evidence |
|---|---|---|
| Git branch、HEAD、remote、worktree、recent commits | PASS | Phase 0.1 Git snapshot；whole-review fresh remote/ref probe |
| 当前入口、活动 UI、启动脚本、App、ports、version sources | PASS | `entry_inventory.json`；FND-030 compensation；whole-review runtime probe |
| candidate roots、DB、raw counts/ranges/hashes/permissions，无内容泄露 | PASS | `data_root_inventory.json`、`repository_inventory.json`、fresh immutable SQLite probe |
| 6/8/9 入口、旧原型、旧 closeout 非当前合同 | PASS | `history_deprecation.md` 的 stable IDs 与 dispositions |
| 机器合同固定 10 个入口且含市场与研究 | PASS | `pfi_v025_active_requirements.json#official_nav` |
| owner/version/build identity 冲突继续阻断 | PASS | `finding_ledger.csv`、`gap_register.md`、`current_state_matrix.md`；未声明统一 |

## 5. Stop Conditions

- 无法解释的 dirty worktree：未触发；审查开始时 clean，整阶段变更由 exact path ledger 解释。
- branch/remote main 无法确认：未触发；authoritative remote main 为 `2c91c22f3d334f82aa111245e452f8a35ac51cc6`，local tracking `origin/main` 为 stale `a8fdd0f6278d9819ea2e5c29c3c275166a5e46e5`，两者没有被混写为一致。
- 数据读取需要修改、移动、解密或上传：未触发；SQLite 使用 `mode=ro&immutable=1` 且 before/after 不变。
- runtime 来源不是仓库：未触发；8501/8502 两个 healthy listeners 均来自 canonical PFI root。双 listener 仍是后续开放 gap，不在 Stage 0 自行修复。

## 6. Codex verdict 与停止点

Stage 0 whole-stage review 的 Codex candidate verdict 为 `PASS_PENDING_REVIEW_COMMIT_ATTESTATION_AND_USER_ACCEPTANCE`。这只接受 Stage 0 baseline、active contract、history disposition、finding/gap ledger 与 evidence chain；27 个开放 P0/P1 product findings 继续阻断 v0.2.5 production acceptance。

Legacy sparse CI 保留真实 `STOP`：一层来自 `evidence/.json/risk` filename classifier 要求四个未发生变化的 model/formula/parameter companions，另一层来自 sparse worktree 中 root schemas、其他 project roots 与 `tests/cloudflare` 未物化。full-tree temporary shadow 的 PFI project governance 与 changed-scope semantic sync 均为 `0 errors / 0 warnings`；该对照只解析 tooling false positive，不改写 legacy result。

`human_acceptance.json` 故意不存在。用户必须按 `stage_0_acceptance_request.md` 明确绑定 version、review commit、evidence hash、accepted scope、known defects 和 acceptance statement；收到前保持 `Stage 1 = not_started`。
