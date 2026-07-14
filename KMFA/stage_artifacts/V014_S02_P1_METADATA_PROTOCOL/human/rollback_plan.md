# KMFA v0.1.4 S02-P1 Rollback Plan

## 回滚范围

如本 phase 验证失败，仅回滚以下 public-safe 资产：

- `KMFA/metadata/protocol/raw_data_roots_v1_4.json`
- `KMFA/stage_artifacts/V014_S02_P1_METADATA_PROTOCOL/`
- `KMFA/tools/check_v014_s02_p1_metadata_protocol.py`
- `KMFA/tests/test_v014_s02_p1_metadata_protocol.py`
- 本轮追加的 S02-P1 governance 记录

## 不可回滚/不可触碰

- 不得修改、删除、移动、重命名、覆盖或写入 `/Users/linzezhang/Downloads/KMFA_MetaData`。
- 不得为了回滚而删除 raw/private inbox、ZIP、Excel、PDF、私有 CSV、SQLite/db、合同、银行流水、薪资或税务材料。
- 不得用 GitHub upload 作为回滚手段。

## 验证

回滚后复跑 `KMFA/tools/metadata_protocol_check.py`、S01 Stage review validator、governance validators、raw/private path scan、strict secret scan 和 `git diff --check -- KMFA`。
