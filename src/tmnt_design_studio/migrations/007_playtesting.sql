CREATE TABLE playtest_sessions (
    id INTEGER PRIMARY KEY,
    deck_version_id INTEGER NOT NULL REFERENCES deck_versions(id) ON DELETE RESTRICT,
    played_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    games_played INTEGER NOT NULL DEFAULT 0 CHECK (games_played >= 0),
    notes TEXT
);
CREATE TABLE playtest_observations (
    id INTEGER PRIMARY KEY,
    playtest_session_id INTEGER NOT NULL REFERENCES playtest_sessions(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    observation TEXT NOT NULL,
    measurement REAL,
    UNIQUE (playtest_session_id, category, observation)
);

