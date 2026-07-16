# PFI v0.2.5 Stage 0 Whole-Stage Review — Risk and Rollback

## Scope

本记录只覆盖 Stage 0 whole-stage review、direct lifecycle companions 与用户验收请求。没有业务 UI、产品代码、测试代码、模型/公式/参数 registry、App、runtime、data/DB、installation、migration 或 GitHub push 变更。

## Remaining risks

- 本次 Codex pass 可能被误读为 v0.2.5 production acceptance；实际仍有 27 个开放 P0/P1 findings。
- local tracking `origin/main` stale，authoritative remote main 与本地分叉；Stage 12 final delivery 前必须重新建立唯一 remote transaction identity，本轮不改 ref。
- 两个 canonical listeners 均 healthy，但 singleton 尚未建立；继续由 Stage 1/12 resolution tasks 处理。
- external attestations 位于 Git common-dir；tracked whole-stage index 持久保存其 SHA、commit、status 和关键 bindings，但不能把 tracked 摘要误写为密码学签名。
- generic governance classifier 会把 `evidence.json`、`.json` 和 `risk_and_rollback.md` 机械误判为 config/model behavior change；sparse worktree 还会把未物化 root schemas、other project roots 和 `tests/cloudflare` 报为 missing。legacy STOP 必须保留；full-tree shadow 的 PFI structural/semantic `0/0` 只用于证明这些是 tooling/sparse false positives，不得为取悦分类器改动无关 model/formula/parameter registries。
- `human_acceptance.json` 仍不存在；用户 blanket approval 不是 evidence-bound acceptance。

## Rollback

- 提交前：仅撤销 `changed_files.txt` 中 exact 16 paths 的本轮 hunks/files。
- 提交后：revert whole-review commit，返回 `a590a3da20f2cf569c11114a3f46e1ff1a0ef6f2` 的 Phase 0.3 compensation-resolved 基线；不得改写 Phase 0.1–0.3 commits、events 或 external attestations。
- rollback 不触碰 App、runtime、data/DB、user files 或 remote refs。

## Stop

任何 hash mismatch、scope expansion、private financial value、unexplained ref mutation、runtime/data write、Stage 1 path 或 reviewer C/I/M 重新出现，都使 whole-stage candidate 失败并停止在 Stage 0。
