-- Roll back transactional model activation and refresh state.

DROP TABLE IF EXISTS active_analysis_contexts;
DROP INDEX IF EXISTS scoring_profile_versions_one_global_active_idx;
