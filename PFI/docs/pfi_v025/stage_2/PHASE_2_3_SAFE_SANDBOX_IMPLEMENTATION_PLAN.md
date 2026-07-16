# PFI v0.2.5 Stage 2 Phase 2.3 实施计划

## Run Contract

- Phase：`V025-S2-P2.3`
- Tasks：`S2-P3-T1..T4`
- Acceptance：`ACC-PFI-V025-S2-P23-SAFE-SANDBOX`
- Risk：`T3_PRIVACY_REAL_DATA`
- 当前 Phase 之外：Stage 2 whole-stage review、用户验收、Stage 3、production FX load、GitHub push、canonical App install。

## 目标与范围

1. 使用 commit-bound immutable Git objects 作为交易来源快照，不 checkout 或复制原始文件到仓库。
2. 将 canonical operational SQLite 只读复制到 `0700` 临时目录中的 `0600` 文件，只在副本执行 integrity/schema-count 检查并删除副本。
3. 对实际 `8815` 行输入进行三轮读取与 CSV parse，只记录 elapsed、peak Python allocation、行数、field count 与 object identity。
4. 无真实输入时返回 blocked；函数不接受外部财务 records/rows/fixtures，不生成 fallback。
5. 生成 Stage 2 evidence index，但保持 whole-stage review 和用户验收为未开始，不进入 Stage 3。

## 验证

- `PFI/tests/test_v025_stage2_safe_sandbox.py`
- Phase 2.1/2.2 focused compatibility
- Task Pack Evidence schema
- source before/after 与 temp cleanup
- fixed-input privacy/no-fake scan
- full-checkout project governance、semantic sync 与 renderer
- exact changed-file scope 与 `git diff --check`

## 回滚与停止条件

只撤销 Phase 2.3 commit。若 source identity/hash 改变、临时副本未清理、私密值进入 evidence、真实输入缺失时发生 fallback，或需要网络/生产写入，则本 Phase blocked 并停止。
