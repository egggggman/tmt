ALTER TABLE imports ADD COLUMN source_uri TEXT;
ALTER TABLE imports ADD COLUMN source_type TEXT;
ALTER TABLE imports ADD COLUMN source_updated_at TEXT;
ALTER TABLE imports ADD COLUMN checksum TEXT CHECK (checksum IS NULL OR length(checksum) = 64);
ALTER TABLE imports ADD COLUMN source_size INTEGER CHECK (source_size IS NULL OR source_size >= 0);
ALTER TABLE imports ADD COLUMN processed_count INTEGER NOT NULL DEFAULT 0 CHECK (processed_count >= 0);
ALTER TABLE imports ADD COLUMN skipped_count INTEGER NOT NULL DEFAULT 0 CHECK (skipped_count >= 0);
ALTER TABLE imports ADD COLUMN warning_count INTEGER NOT NULL DEFAULT 0 CHECK (warning_count >= 0);
ALTER TABLE imports ADD COLUMN error_count INTEGER NOT NULL DEFAULT 0 CHECK (error_count >= 0);
ALTER TABLE imports ADD COLUMN warnings TEXT;
ALTER TABLE imports ADD COLUMN source_metadata TEXT;

UPDATE metadata SET value = '010', updated_at = CURRENT_TIMESTAMP WHERE key = 'schema_version';
