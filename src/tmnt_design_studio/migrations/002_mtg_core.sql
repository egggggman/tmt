CREATE TABLE cards (
    oracle_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mana_cost TEXT,
    mana_value REAL NOT NULL DEFAULT 0 CHECK (mana_value >= 0),
    oracle_text TEXT,
    color_identity TEXT NOT NULL DEFAULT '',
    type_line TEXT NOT NULL
);
CREATE TABLE card_printings (
    scryfall_id TEXT PRIMARY KEY,
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    set_code TEXT NOT NULL,
    collector_number TEXT NOT NULL,
    rarity TEXT NOT NULL CHECK (rarity IN ('common','uncommon','rare','mythic','special','bonus')),
    artist TEXT,
    released_at TEXT,
    UNIQUE (set_code, collector_number)
);
CREATE TABLE card_faces (
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    face_number INTEGER NOT NULL CHECK (face_number >= 0),
    name TEXT NOT NULL,
    mana_cost TEXT,
    oracle_text TEXT,
    type_line TEXT NOT NULL,
    PRIMARY KEY (oracle_id, face_number)
);
CREATE TABLE legalities (
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    format TEXT NOT NULL CHECK (format = 'standard'),
    legality TEXT NOT NULL CHECK (legality IN ('legal','not_legal','restricted','banned')),
    PRIMARY KEY (oracle_id, format)
);
CREATE TABLE keywords (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE card_keywords (
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    keyword_id INTEGER NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    PRIMARY KEY (oracle_id, keyword_id)
);
CREATE TABLE types (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE card_types (
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    type_id INTEGER NOT NULL REFERENCES types(id) ON DELETE CASCADE,
    PRIMARY KEY (oracle_id, type_id)
);
CREATE TABLE subtypes (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE card_subtypes (
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    subtype_id INTEGER NOT NULL REFERENCES subtypes(id) ON DELETE CASCADE,
    PRIMARY KEY (oracle_id, subtype_id)
);

