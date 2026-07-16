-- ADP-S2-P02-T025 rollback（隔离副本验证；NOT applied to production）
DROP INDEX IF EXISTS idx_docver_status;
DROP INDEX IF EXISTS idx_docver_contenthash;
DROP INDEX IF EXISTS idx_docver_canonical;
DROP TABLE IF EXISTS cn_document_versions;
DROP TABLE IF EXISTS cn_documents;
DELETE FROM cn_meta WHERE key='document_version_schema';
