ALTER TABLE capabilities ADD COLUMN identifier TEXT;
ALTER TABLE capabilities ADD COLUMN category TEXT NOT NULL DEFAULT 'utility';
ALTER TABLE capabilities ADD COLUMN status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','deprecated'));
CREATE UNIQUE INDEX capabilities_identifier_unique ON capabilities(identifier);

ALTER TABLE capability_rules ADD COLUMN rule_key TEXT;
ALTER TABLE capability_rules ADD COLUMN ruleset_version TEXT;
ALTER TABLE capability_rules ADD COLUMN rule_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE capability_rules ADD COLUMN confidence REAL NOT NULL DEFAULT 0.8
    CHECK (confidence BETWEEN 0 AND 1);
ALTER TABLE capability_rules ADD COLUMN fields_read TEXT NOT NULL DEFAULT '[]';
ALTER TABLE capability_rules ADD COLUMN exclusions TEXT NOT NULL DEFAULT '[]';
ALTER TABLE capability_rules ADD COLUMN description TEXT NOT NULL DEFAULT '';
CREATE UNIQUE INDEX capability_rules_key_version_unique
    ON capability_rules(rule_key, ruleset_version, rule_version);

CREATE TABLE capability_rule_sets (
    version TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    rules_checksum TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active','retired')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE capability_derivation_runs (
    id INTEGER PRIMARY KEY,
    ruleset_version TEXT NOT NULL REFERENCES capability_rule_sets(version),
    import_id INTEGER NOT NULL REFERENCES imports(id),
    status TEXT NOT NULL CHECK (status IN ('running','succeeded','failed')),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    card_count INTEGER NOT NULL DEFAULT 0 CHECK (card_count >= 0),
    result_count INTEGER NOT NULL DEFAULT 0 CHECK (result_count >= 0),
    error TEXT
);

ALTER TABLE card_capabilities ADD COLUMN derivation_run_id INTEGER
    REFERENCES capability_derivation_runs(id);

CREATE TABLE capability_evidence (
    id INTEGER PRIMARY KEY,
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    capability_id INTEGER NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
    rule_id INTEGER REFERENCES capability_rules(id) ON DELETE CASCADE,
    derivation_run_id INTEGER NOT NULL REFERENCES capability_derivation_runs(id),
    evidence_type TEXT NOT NULL CHECK (evidence_type IN
        ('oracle_text','keyword','card_type','subtype','numeric_condition','face','override')),
    source_field TEXT NOT NULL,
    source_value TEXT NOT NULL,
    matched_value TEXT NOT NULL,
    face_number INTEGER CHECK (face_number IS NULL OR face_number >= 0),
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    UNIQUE (oracle_id, capability_id, rule_id, derivation_run_id, source_field, matched_value,
            face_number)
);

ALTER TABLE capability_overrides ADD COLUMN evidence_context TEXT NOT NULL DEFAULT '';
ALTER TABLE capability_overrides ADD COLUMN confidence_delta REAL
    CHECK (confidence_delta BETWEEN -1 AND 1);
ALTER TABLE capability_overrides ADD COLUMN created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE capability_overrides ADD COLUMN updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP;
CREATE UNIQUE INDEX capability_overrides_one_active
    ON capability_overrides(oracle_id, capability_id) WHERE active = 1;

CREATE TRIGGER capability_overrides_validate_insert
BEFORE INSERT ON capability_overrides
FOR EACH ROW
WHEN trim(NEW.rationale) = ''
  OR trim(NEW.evidence_context) = ''
  OR (NEW.action = 'add' AND (NEW.confidence IS NULL OR NEW.confidence_delta IS NOT NULL))
  OR (NEW.action = 'remove' AND (NEW.confidence IS NOT NULL OR NEW.confidence_delta IS NOT NULL))
  OR (NEW.action = 'adjust' AND (NEW.confidence IS NOT NULL OR NEW.confidence_delta IS NULL))
BEGIN
    SELECT RAISE(ABORT, 'capability override fields do not match action');
END;

CREATE TRIGGER capability_overrides_validate_update
BEFORE UPDATE ON capability_overrides
FOR EACH ROW
WHEN trim(NEW.rationale) = ''
  OR trim(NEW.evidence_context) = ''
  OR (NEW.action = 'add' AND (NEW.confidence IS NULL OR NEW.confidence_delta IS NOT NULL))
  OR (NEW.action = 'remove' AND (NEW.confidence IS NOT NULL OR NEW.confidence_delta IS NOT NULL))
  OR (NEW.action = 'adjust' AND (NEW.confidence IS NOT NULL OR NEW.confidence_delta IS NULL))
BEGIN
    SELECT RAISE(ABORT, 'capability override fields do not match action');
END;

CREATE TRIGGER capability_overrides_touch_updated_at
AFTER UPDATE ON capability_overrides
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE capability_overrides SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE INDEX capability_runs_status ON capability_derivation_runs(status, id);
CREATE INDEX capability_evidence_card ON capability_evidence(oracle_id, capability_id);
CREATE INDEX card_capabilities_run ON card_capabilities(derivation_run_id);
