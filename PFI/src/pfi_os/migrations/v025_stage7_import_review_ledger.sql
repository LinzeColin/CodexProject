CREATE TABLE IF NOT EXISTS pfi_schema_migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_batches (
    batch_id TEXT PRIMARY KEY,
    batch_fingerprint TEXT NOT NULL UNIQUE,
    source_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('preview_ready', 'confirmed', 'failed', 'rolled_back')),
    file_count INTEGER NOT NULL CHECK (file_count >= 0),
    valid_file_count INTEGER NOT NULL CHECK (valid_file_count >= 0),
    bytes_count INTEGER NOT NULL CHECK (bytes_count >= 0),
    raw_record_count INTEGER NOT NULL CHECK (raw_record_count >= 0),
    transaction_count INTEGER NOT NULL CHECK (transaction_count >= 0),
    review_count INTEGER NOT NULL CHECK (review_count >= 0),
    date_start TEXT NOT NULL DEFAULT '',
    date_end TEXT NOT NULL DEFAULT '',
    field_mapping_json TEXT NOT NULL DEFAULT '[]',
    errors_json TEXT NOT NULL DEFAULT '[]',
    attempt_count INTEGER NOT NULL DEFAULT 1 CHECK (attempt_count >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    confirmed_at TEXT,
    rolled_back_at TEXT
);

CREATE TABLE IF NOT EXISTS import_files (
    file_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batches(batch_id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    bytes_count INTEGER NOT NULL CHECK (bytes_count >= 0),
    source_id TEXT,
    parser_version TEXT,
    raw_store_ref TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ready', 'error')),
    error_code TEXT,
    error_text TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(batch_id, content_sha256)
);

CREATE TABLE IF NOT EXISTS import_staged_transactions (
    staged_transaction_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batches(batch_id) ON DELETE CASCADE,
    transaction_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    raw_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    description TEXT NOT NULL,
    confidence REAL NOT NULL,
    review_state TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(batch_id, payload_sha256)
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    ledger_entry_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batches(batch_id) ON DELETE RESTRICT,
    transaction_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    raw_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    description TEXT NOT NULL,
    confidence REAL NOT NULL,
    ledger_state TEXT NOT NULL CHECK (ledger_state IN ('posted', 'pending_review', 'excluded')),
    category TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(batch_id, transaction_id)
);

CREATE TABLE IF NOT EXISTS import_review_queue (
    review_id TEXT PRIMARY KEY,
    ledger_entry_id TEXT NOT NULL UNIQUE REFERENCES ledger_entries(ledger_entry_id) ON DELETE CASCADE,
    batch_id TEXT NOT NULL REFERENCES import_batches(batch_id) ON DELETE RESTRICT,
    transaction_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'resolved')),
    reason TEXT NOT NULL,
    decision TEXT,
    category TEXT NOT NULL DEFAULT '',
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS import_audit_events (
    event_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batches(batch_id) ON DELETE RESTRICT,
    review_id TEXT,
    event_type TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_import_batches_status ON import_batches(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_import_files_sha ON import_files(content_sha256);
CREATE INDEX IF NOT EXISTS idx_staged_batch ON import_staged_transactions(batch_id);
CREATE INDEX IF NOT EXISTS idx_ledger_batch_state ON ledger_entries(batch_id, ledger_state);
CREATE INDEX IF NOT EXISTS idx_review_status ON import_review_queue(status, updated_at);
