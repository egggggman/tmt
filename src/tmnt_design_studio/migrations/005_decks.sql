CREATE TABLE decks (
    id INTEGER PRIMARY KEY,
    design_intent_id INTEGER NOT NULL REFERENCES design_intents(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    format TEXT NOT NULL DEFAULT 'standard' CHECK (format = 'standard'),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (design_intent_id, name)
);
CREATE TABLE deck_versions (
    id INTEGER PRIMARY KEY,
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE RESTRICT,
    version_label TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft','testing','retired','released')),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (deck_id, version_label)
);
CREATE TABLE deck_cards (
    deck_version_id INTEGER NOT NULL REFERENCES deck_versions(id) ON DELETE RESTRICT,
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE RESTRICT,
    section TEXT NOT NULL DEFAULT 'main' CHECK (section IN ('main','sideboard')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (deck_version_id, oracle_id, section)
);

