# 证据与日志

用于放置 run evidence、audit logs、manifest/hash、stage evidence 和复审证据摘要。

当前 S03 P3 已完成。S03 P3 新增机器文件：

- `机器治理/证据与日志/raw_archive_manifests/raw_manifest.s03_p3_baseline.jsonl`
- `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl`

这些文件用于记录 raw manifest/hash 的 source/file/hash/imported_at 映射。
当前没有真实 raw transcript，因此 baseline 可以为空。它们是机器文件，不是人类主要页面。
