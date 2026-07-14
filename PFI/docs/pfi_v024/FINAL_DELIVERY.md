# PFI v0.2.4 Final Delivery

## Acceptance

- Task：`PFI-V024-FINAL-DELIVERY-20260710`
- Acceptance：`ACC-PFI-V024-FINAL-DELIVERY`
- 来源 package：`v0.2.3-repair`
- 内部 target：`v0.2.4`
- product commit：`17b9f59794740f927c5f531ba1aa334621a832e5`
- evidence commit：`SELF`，必须直接以 product commit 为父提交
- gate result：唯一一次 push 后，由 live verifier 证明 `HEAD == origin/main == git ls-remote origin main` 时为 pass
- tracked current status：`pending_live_verifier`；completion predicate pass 后由动态 verifier 解析为 complete，不提交第二个 closeout commit

## Delivery Proof

1. Product freeze：v0.2.3 compatibility `200 passed`；v0.2.4 regression `242 passed`；final-delivery focused `11 passed`。
2. App reinstall：`/Applications/PFI.app`、`~/Downloads/PFI.app` 已重装，`~/Desktop/PFI.app` 指向 Applications；lite acceptance `29 pass / 0 fail / 2 info`。
3. Native launcher：signed full-file hash 三入口一致；Mach-O code-section hash 与当前 `PFI_launcher.c` deterministic compile 一致；codesign、binding 与 exact dry-run 全通过。
4. Runtime parity：临时 current-code 服务使用 `/private/tmp` 数据、HOME 与 pycache；app/localhost bundle hash 相同且等于磁盘；5 个 filename-bound inline asset 在两入口逐项 hash 一致；console/page/http errors 均为 0。
5. Protected paths：`PFI/.venv`、`PFI/data`、`PFI/reports` 安装前后 metadata hash 均为 `sha256:8104c89128f7fb2d68c687af3ca4a0f6e521a703b021a2a8e994dde36db57512`，未修改。
6. GitHub parity：evidence commit 不自报自身 SHA；`stage_v024_final_delivery.py` 在 push 后实时读取 GitHub remote main、tracking ref、local HEAD、clean worktree 和 product direct-parent 关系。

机器证据：`PFI/docs/pfi_v024/FINAL_DELIVERY_EVIDENCE.json`。

## Scope Boundary

- future version 未开始。
- 不包含交易密码、券商订单、支付或自动真钱动作。
- 不修改、清理、删除或补造 `PFI/.venv`、`PFI/data`、`PFI/reports` 与真实财务数据。
- 最终交付不等于生产券商联通、真实凭证或实盘能力验收。

## Rollback

若 push 前任一 gate 失败：不 push，恢复 `/private/tmp/pfi-final-app-backup-aad1a1360/PFI.app` 到 Downloads，并移除本轮新增 app entry。

若 push 后需要回滚：revert evidence commit 与 product commit，再从回滚后的 canonical PFI 重新执行 `PFI/scripts/installPFIEntryApps.sh --all`；不回滚或改写真实财务数据。
