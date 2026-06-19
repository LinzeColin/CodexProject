-- Roll back G2 core domain schema.
-- Keep schema_migrations so the migration runner can record the rollback transaction.

DROP TABLE IF EXISTS seed_runs;
DROP TABLE IF EXISTS company_research_universe;
DROP TABLE IF EXISTS supply_chain_stages;
DROP TABLE IF EXISTS calibration_runs;
DROP TABLE IF EXISTS operation_logs;
DROP TABLE IF EXISTS score_results;
DROP TABLE IF EXISTS scoring_runs;
DROP TABLE IF EXISTS scoring_profile_versions CASCADE;
DROP TABLE IF EXISTS scoring_profiles;
DROP TABLE IF EXISTS scoring_models;
DROP TABLE IF EXISTS watchlist_items;
DROP TABLE IF EXISTS watchlists;
DROP TABLE IF EXISTS exploration_steps;
DROP TABLE IF EXISTS exploration_sessions;
DROP TABLE IF EXISTS supply_chain_relationship_attributes;
DROP TABLE IF EXISTS entity_industry_memberships;
DROP TABLE IF EXISTS industries;
DROP TABLE IF EXISTS changes;
DROP TABLE IF EXISTS ingestion_runs;
DROP TABLE IF EXISTS event_evidence;
DROP TABLE IF EXISTS event_participants;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS relationship_evidence;
DROP TABLE IF EXISTS relationships;
DROP TABLE IF EXISTS relationship_type_catalog;
DROP TABLE IF EXISTS relationship_families;
DROP TABLE IF EXISTS source_documents;
DROP TABLE IF EXISTS sources;
DROP TABLE IF EXISTS entity_identifiers;
DROP TABLE IF EXISTS entity_aliases;
DROP TABLE IF EXISTS entities;

DROP TYPE IF EXISTS change_type;
DROP TYPE IF EXISTS evidence_role;
DROP TYPE IF EXISTS epistemic_status;
DROP TYPE IF EXISTS entity_type;
