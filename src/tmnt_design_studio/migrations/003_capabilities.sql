CREATE TABLE capabilities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL
);
CREATE TABLE capability_rules (
    id INTEGER PRIMARY KEY,
    capability_id INTEGER NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
    rule_type TEXT NOT NULL,
    expression TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    UNIQUE (capability_id, rule_type, expression)
);
CREATE TABLE card_capabilities (
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    capability_id INTEGER NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
    rule_id INTEGER NOT NULL REFERENCES capability_rules(id) ON DELETE CASCADE,
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    PRIMARY KEY (oracle_id, capability_id, rule_id)
);
CREATE TABLE capability_overrides (
    id INTEGER PRIMARY KEY,
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    capability_id INTEGER NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
    action TEXT NOT NULL CHECK (action IN ('add','remove','adjust')),
    confidence REAL CHECK (confidence BETWEEN 0 AND 1),
    rationale TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);

