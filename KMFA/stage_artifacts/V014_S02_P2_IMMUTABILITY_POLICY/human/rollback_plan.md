# KMFA v0.1.4 S02-P2 Rollback Plan

If this phase must be reverted:

1. Revert `KMFA/metadata/protocol/immutability_policy_lock_v1_4.json`.
2. Revert `KMFA/stage_artifacts/V014_S02_P2_IMMUTABILITY_POLICY/`.
3. Revert `KMFA/tools/check_v014_s02_p2_immutability_policy.py` and `KMFA/tests/test_v014_s02_p2_immutability_policy.py`.
4. Revert S02-P2 governance rows in `KMFA/README.md`, `KMFA/HANDOFF.md`, `KMFA/功能清单.md`, `KMFA/开发记录.md`, `KMFA/模型参数文件.md`, `KMFA/docs/governance/`, and `KMFA/metadata/stage_status.jsonl`.
5. Do not touch `/Users/linzezhang/Downloads/KMFA_MetaData`.

Rollback success condition: `git status --short --branch` shows no S02-P2 changes and S02-P1 validators still pass.
