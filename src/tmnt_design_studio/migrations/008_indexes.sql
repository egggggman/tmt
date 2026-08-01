CREATE INDEX idx_card_printings_oracle ON card_printings(oracle_id);
CREATE INDEX idx_legalities_format_legality ON legalities(format, legality);
CREATE INDEX idx_card_capabilities_capability ON card_capabilities(capability_id);
CREATE INDEX idx_design_intents_character ON design_intents(character_id);
CREATE INDEX idx_deck_versions_deck ON deck_versions(deck_id, created_at);
CREATE INDEX idx_deck_cards_oracle ON deck_cards(oracle_id);
CREATE INDEX idx_playtests_deck_version ON playtest_sessions(deck_version_id);

