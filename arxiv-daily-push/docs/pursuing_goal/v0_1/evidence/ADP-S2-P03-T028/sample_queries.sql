-- ADP-S2-P03-T028 DuckDB rebuild queries (local Parquet; no Cloudflare)
-- documents_total
SELECT COUNT(*) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_documents__*.parquet');
-- documents_distinct_canonical
SELECT COUNT(DISTINCT canonical_id) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_documents__*.parquet');
-- documents_per_month
SELECT first_seen_month AS k, COUNT(*) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_documents__*.parquet') GROUP BY 1 ORDER BY 1;
-- versions_total
SELECT COUNT(*) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_document_versions__*.parquet');
-- version_events_per_month
SELECT month AS k, COUNT(*) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_document_versions__*.parquet') GROUP BY 1 ORDER BY 1;
-- orphan_versions
SELECT COUNT(*) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_document_versions__*.parquet') ver LEFT JOIN read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_documents__*.parquet') d ON ver.canonical_id = d.canonical_id WHERE d.canonical_id IS NULL;
-- signal_repost_multi_source
SELECT COUNT(*) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_documents__*.parquet') WHERE item_count > 1;
-- signal_multi_version_docs
SELECT COUNT(*) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_documents__*.parquet') WHERE version_count > 1;
-- signal_status_distribution
SELECT status AS k, COUNT(*) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_document_versions__*.parquet') GROUP BY 1 ORDER BY 1;
-- signal_months_covered
SELECT COUNT(DISTINCT month) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_document_versions__*.parquet');
-- earliest_version_month
SELECT MIN(month) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_document_versions__*.parquet');
-- latest_version_month
SELECT MAX(month) AS v FROM read_parquet('/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-main-worktree-CodexProject-adp/6c611ddc-f264-4d55-9b19-b0f39a03415d/scratchpad/t028_snap/data/cn_document_versions__*.parquet');
