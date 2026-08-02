CREATE TABLE deck_analysis_engine_versions (
    version TEXT PRIMARY KEY,
    checksum TEXT NOT NULL CHECK (length(checksum) = 64),
    description TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active','retired')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE deck_analysis_runs (
    id INTEGER PRIMARY KEY,
    deck_version_id INTEGER NOT NULL REFERENCES deck_versions(id) ON DELETE RESTRICT,
    import_id INTEGER NOT NULL REFERENCES imports(id) ON DELETE RESTRICT,
    capability_run_id INTEGER NOT NULL REFERENCES capability_derivation_runs(id) ON DELETE RESTRICT,
    engine_version TEXT NOT NULL REFERENCES deck_analysis_engine_versions(version),
    engine_checksum TEXT NOT NULL CHECK (length(engine_checksum) = 64),
    deck_checksum TEXT NOT NULL CHECK (length(deck_checksum) = 64),
    status TEXT NOT NULL CHECK (status IN ('running','succeeded','failed')),
    diagnostic INTEGER NOT NULL DEFAULT 0 CHECK (diagnostic IN (0,1)),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    metric_count INTEGER NOT NULL DEFAULT 0 CHECK (metric_count >= 0),
    finding_count INTEGER NOT NULL DEFAULT 0 CHECK (finding_count >= 0),
    relationship_count INTEGER NOT NULL DEFAULT 0 CHECK (relationship_count >= 0),
    warnings TEXT NOT NULL DEFAULT '[]',
    error TEXT
);

CREATE TABLE deck_analysis_metrics (
    run_id INTEGER NOT NULL REFERENCES deck_analysis_runs(id) ON DELETE CASCADE,
    metric_key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    formula TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    PRIMARY KEY (run_id, metric_key)
);

CREATE TABLE deck_analysis_findings (
    run_id INTEGER NOT NULL REFERENCES deck_analysis_runs(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    severity TEXT NOT NULL CHECK (severity IN ('warning','observation','information')),
    rule_key TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    message TEXT NOT NULL,
    threshold_json TEXT NOT NULL,
    PRIMARY KEY (run_id, ordinal),
    UNIQUE (run_id, rule_key, metric_key)
);

CREATE TABLE deck_analysis_relationships (
    run_id INTEGER NOT NULL REFERENCES deck_analysis_runs(id) ON DELETE CASCADE,
    relationship_key TEXT NOT NULL,
    left_fact TEXT NOT NULL,
    right_fact TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    PRIMARY KEY (run_id, relationship_key)
);

CREATE TABLE current_deck_analyses (
    deck_version_id INTEGER PRIMARY KEY REFERENCES deck_versions(id) ON DELETE RESTRICT,
    run_id INTEGER NOT NULL UNIQUE REFERENCES deck_analysis_runs(id) ON DELETE RESTRICT
);

CREATE INDEX deck_analysis_runs_deck_status
    ON deck_analysis_runs(deck_version_id, status, id);
CREATE INDEX deck_analysis_runs_provenance
    ON deck_analysis_runs(import_id, capability_run_id, engine_version);

CREATE TRIGGER current_deck_analysis_must_succeed_insert
BEFORE INSERT ON current_deck_analyses
FOR EACH ROW
WHEN NOT EXISTS (
    SELECT 1 FROM deck_analysis_runs
    WHERE id = NEW.run_id AND deck_version_id = NEW.deck_version_id AND status = 'succeeded'
)
BEGIN
    SELECT RAISE(ABORT, 'current deck analysis must reference a successful matching run');
END;

CREATE TRIGGER current_deck_analysis_must_succeed_update
BEFORE UPDATE ON current_deck_analyses
FOR EACH ROW
WHEN NOT EXISTS (
    SELECT 1 FROM deck_analysis_runs
    WHERE id = NEW.run_id AND deck_version_id = NEW.deck_version_id AND status = 'succeeded'
)
BEGIN
    SELECT RAISE(ABORT, 'current deck analysis must reference a successful matching run');
END;
