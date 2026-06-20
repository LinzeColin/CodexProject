-- Roll back production snapshot and fact-version layers.

DROP TABLE IF EXISTS fact_version_evidence;
DROP TABLE IF EXISTS fact_versions;
DROP TABLE IF EXISTS data_snapshots;
