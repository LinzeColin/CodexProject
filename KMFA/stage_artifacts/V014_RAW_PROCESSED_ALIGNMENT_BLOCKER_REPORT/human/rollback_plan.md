# Rollback Plan

- 删除本 phase 新增的 `V014_RAW_PROCESSED_ALIGNMENT_BLOCKER_REPORT` 证据目录。
- 删除 `KMFA/metadata/quality/v014_raw_processed_alignment_blocker_*.json` copies。
- 回滚本 phase 新增工具、validator、focused test 和治理索引记录。
- 不需要 raw 数据回滚，因为本 phase 不读取、不写入、不删除、不移动 raw 数据。
