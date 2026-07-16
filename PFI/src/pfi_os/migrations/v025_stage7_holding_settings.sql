CREATE TABLE IF NOT EXISTS pfi_schema_migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v025_holding_records (
    holding_id TEXT PRIMARY KEY,
    client_ref TEXT NOT NULL UNIQUE,
    portfolio_id TEXT NOT NULL,
    instrument_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    quantity TEXT NOT NULL,
    average_cost TEXT,
    market_price TEXT,
    currency TEXT NOT NULL,
    source_id TEXT NOT NULL,
    as_of TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('active', 'deleted')),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS v025_holding_change_sets (
    request_id TEXT PRIMARY KEY,
    operation_count INTEGER NOT NULL CHECK (operation_count > 0),
    projection_hash_before TEXT NOT NULL,
    projection_hash_after TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v025_holding_events (
    event_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES v025_holding_change_sets(request_id) ON DELETE RESTRICT,
    holding_id TEXT NOT NULL REFERENCES v025_holding_records(holding_id) ON DELETE RESTRICT,
    operation TEXT NOT NULL CHECK (operation IN ('create', 'update', 'delete')),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    before_hash TEXT,
    after_hash TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v025_settings_preferences (
    scope TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v025_settings_events (
    event_id TEXT PRIMARY KEY,
    scope TEXT NOT NULL REFERENCES v025_settings_preferences(scope) ON DELETE RESTRICT,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    payload_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_v025_holdings_status
ON v025_holding_records(status, portfolio_id, instrument_id);

CREATE INDEX IF NOT EXISTS idx_v025_holding_events_request
ON v025_holding_events(request_id, holding_id);

CREATE INDEX IF NOT EXISTS idx_v025_settings_events_scope
ON v025_settings_events(scope, revision);
