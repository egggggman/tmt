CREATE TABLE design_notes (
    id INTEGER PRIMARY KEY,
    subject_type TEXT NOT NULL CHECK (subject_type IN ('character','design_intent','deck','deck_version','card')),
    subject_id TEXT NOT NULL,
    category TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE design_decisions (
    id INTEGER PRIMARY KEY,
    design_intent_id INTEGER NOT NULL REFERENCES design_intents(id) ON DELETE RESTRICT,
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('proposed','accepted','superseded','rejected')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE card_relationships (
    source_oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    target_oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    relationship TEXT NOT NULL CHECK (relationship IN ('supports','conflicts_with','replacement','upgrade','combo')),
    rationale TEXT NOT NULL,
    PRIMARY KEY (source_oracle_id, target_oracle_id, relationship),
    CHECK (source_oracle_id <> target_oracle_id)
);
CREATE TABLE design_sessions (
    id INTEGER PRIMARY KEY,
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE RESTRICT,
    resulting_deck_version_id INTEGER REFERENCES deck_versions(id) ON DELETE RESTRICT,
    summary TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT
);

