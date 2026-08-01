CREATE TABLE characters (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK (kind IN ('character','ally','villain','team','faction')),
    description TEXT
);
CREATE TABLE design_intents (
    id INTEGER PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    UNIQUE (character_id, name)
);
CREATE TABLE themes (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, description TEXT NOT NULL);
CREATE TABLE design_intent_themes (
    design_intent_id INTEGER NOT NULL REFERENCES design_intents(id) ON DELETE CASCADE,
    theme_id INTEGER NOT NULL REFERENCES themes(id) ON DELETE CASCADE,
    priority INTEGER NOT NULL CHECK (priority > 0),
    PRIMARY KEY (design_intent_id, theme_id)
);
CREATE TABLE theme_capabilities (
    theme_id INTEGER NOT NULL REFERENCES themes(id) ON DELETE CASCADE,
    capability_id INTEGER NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
    weight REAL NOT NULL DEFAULT 1 CHECK (weight > 0),
    rationale TEXT NOT NULL,
    PRIMARY KEY (theme_id, capability_id)
);
CREATE TABLE design_intent_capabilities (
    design_intent_id INTEGER NOT NULL REFERENCES design_intents(id) ON DELETE CASCADE,
    capability_id INTEGER NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
    priority INTEGER NOT NULL CHECK (priority > 0),
    rationale TEXT NOT NULL,
    PRIMARY KEY (design_intent_id, capability_id)
);
CREATE TABLE experience_goals (
    id INTEGER PRIMARY KEY,
    design_intent_id INTEGER NOT NULL REFERENCES design_intents(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    priority INTEGER NOT NULL CHECK (priority > 0),
    UNIQUE (design_intent_id, description)
);

