# Stage 1 Whole-Stage Risk and Rollback

- Acceptance：`ACC-PFI-V025-STAGE1-WHOLE-REVIEW`。
- Tracked result：`candidate_pass_pending_postcommit_attestation`；不等于 production 或 final human acceptance。
- Runtime risk：本机 Streamlit 与 lock 版本仍可能漂移；release identity/cache policy 在每次候选启动时重新验证，Stage 12 rebuilt-runtime 仍需最终 UAT。
- Privacy risk：截图像素、browser accessibility tree、visible DOM/full HTML/live form controls 和 decompressed trace 均需独立零发现；任一 finding 立即拒绝 attestation。
- Entry risk：canonical Applications/Desktop/Downloads 不在本轮写范围；唯一 canonical install 仍为 `S12-P2-T1`。
- Remote risk：本轮不 push；唯一 push 保留在 `S12-P3-T4` explicit acceptance 之后。
- 回滚顺序：先以 path-limited compensating commit 撤销唯一 direct binding successor，再撤销 final remediation content `04390bcf17c18de107eb2f1b4ce051c83638f98c`。
- 禁止回滚方式：不改写 Phase commits、events 或 attestations，不删除用户数据，不触碰 canonical Apps、live services 或 remote refs。
