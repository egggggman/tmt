CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,
    checksum TEXT NOT NULL CHECK (length(checksum) = 64),
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE imports (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    source_date TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    imported_count INTEGER NOT NULL DEFAULT 0 CHECK (imported_count >= 0),
    error TEXT,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT
);
