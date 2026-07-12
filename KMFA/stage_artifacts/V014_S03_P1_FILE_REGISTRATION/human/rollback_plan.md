# KMFA v0.1.4 S03-P1 Rollback Plan

## 回滚范围

如本 phase 验证失败，仅回滚以下 public-safe 资产：

- `KMFA/tools/v014_s03_p1_raw_file_registration.py`
- `KMFA/tools/check_v014_s03_p1_file_registration.py`
- `KMFA/tests/test_v014_s03_p1_file_registration.py`
- `KMFA/metadata/imports/v014_s03_p1_public_raw_file_register.json`
- `KMFA/metadata/protocol/raw_data_roots_v1_4_s03_p1.json`
- `KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/`
- 本轮追加的 S03-P1 governance 记录

## 私有运行时

- 可删除本轮生成的 `KMFA/.codex_private_runtime/V014_S03_P1_FILE_REGISTRATION/` 以清理本地诊断。
- 私有运行时不得迁入公开 GitHub。

## 不可触碰

- 不得修改、删除、移动、重命名、覆盖、转换或写入 `/Users/linzezhang/Downloads/KMFA_MetaData`。
- 不得为了回滚而删除 raw/private inbox、ZIP、Excel、PDF、私有 CSV、SQLite/db、合同、银行流水、薪资或税务材料。
- 不得用 GitHub upload 作为回滚手段。

## 验证

回滚后复跑 S02 Stage review validator、S03-P1 validator、focused unit test、governance validators、raw/private path scan、strict secret scan 和 `git diff --check -- KMFA`。
