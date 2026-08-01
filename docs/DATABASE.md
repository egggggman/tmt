# SewerGraph Database Specification

## Purpose

SewerGraph is the SQLite knowledge database for TMNT Design Studio. It stores durable information that cannot be safely recreated from other canonical sources or that must be preserved as project history.

## Database principles

1. Imported Magic facts remain separate from TMNT interpretation.
2. Derived Capabilities are reproducible from explicit rules.
3. Designer overrides are rare, documented, and auditable.
4. Recommendations, Deck Profiles, theme coverage, and deck-health scores are computed rather than canonical stored truth.
5. Deck Versions are immutable historical snapshots.
6. Every table has one clear responsibility.
7. Foreign keys are always enabled.
8. Migrations are ordered, recorded, and immutable after release.

## Logical domains

### 1. System and imports

- `schema_migrations` — records applied migration versions.
- `metadata` — stores small database-level values such as schema version and source dates.
- `imports` — records Scryfall import attempts, status, counts, and errors.

### 2. Magic facts

- `cards` — stores the canonical Oracle-level card identity and common searchable facts.
- `card_printings` — stores printing-specific fields when needed, including Scryfall card ID, set, collector number, rarity, artist, and release date.
- `card_faces` — stores ordered faces for multifaced cards.
- `legalities` — stores per-format legality; Version 1 filters to Standard.
- `keywords` / `card_keywords` — normalized keyword vocabulary and card relationships.
- `types` / `card_types` — normalized card types.
- `subtypes` / `card_subtypes` — normalized card subtypes.

Oracle identity and printing identity must not be conflated. Oracle-level design knowledge attaches to the underlying card unless a printing-specific distinction is intentionally required.

### 3. Capabilities

- `capabilities` — canonical gameplay-function vocabulary.
- `capability_rules` — explicit rules used to derive Capabilities from card facts.
- `card_capabilities` — derived results, including confidence and rule provenance.
- `capability_overrides` — documented additions, removals, or adjustments made by designers.

The effective Capability set is computed from derived results plus active overrides.

Migration `011_capability_engine.sql` adds stable catalog identifiers, categories, and status;
versioned rule keys, confidence, fields read, exclusions, and descriptions; plus these audit tables:

- `capability_rule_sets` — immutable version/checksum identity for reproducible rules.
- `capability_derivation_runs` — outcome, timestamps, counts, exact rule set, and source import.
- `capability_evidence` — source fact, matched value, optional face, rule, run, and confidence.

Overrides retain add/remove/adjust decisions separately with rationale, evidence context, signed
confidence delta, active state, and timestamps. A partial unique index permits only one active
decision for an Oracle card and Capability; inactive rows retain history.
Insert/update triggers require nonblank rationale and evidence context and enforce action-specific
fields: add requires confidence, remove permits neither confidence field, and adjust requires only a
signed delta. Updates refresh the audit timestamp.

Confidence is evidence strength in `[0,1]`: 0 means no support and 1 means direct, unambiguous
support. Initial rules use 0.75–0.98. Multiple rules combine by maximum, not addition, while all
evidence remains visible. Adjustment overrides use a `[-1,1]` delta and clamp to `[0,1]`.

### 4. TMNT knowledge and intent

- `characters` — TMNT characters, allies, villains, teams, or factions.
- `design_intents` — direct children of Characters defining a specific gameplay interpretation.
- `themes` — narrative and identity concepts.
- `design_intent_themes` — prioritized Themes for a Design Intent.
- `theme_capabilities` — explains which Capabilities express each Theme.
- `design_intent_capabilities` — optional direct capability priorities for intent-specific needs not fully captured by reusable Theme mappings.
- `experience_goals` — intended player experiences attached to a Design Intent.

### 5. Sewer Decks

- `decks` — a Sewer Deck owned by one Design Intent.
- `deck_versions` — immutable snapshots with version labels, status, and notes.
- `deck_cards` — card quantities in a Deck Version.

A Deck Version must support validation for Standard legality, exactly 60 main-deck cards, and normal copy limits, with explicit handling for cards whose rules override copy limits. Diagnostic analysis may inspect a different size while preserving a warning.

Migration `012_deck_analysis_engine.sql` adds reproducible computed-analysis storage:

- `deck_analysis_engine_versions` — immutable analysis version and checksum identities.
- `deck_analysis_runs` — successful and failed attempts with complete source provenance.
- `deck_analysis_metrics` — JSON values with formulas and evidence.
- `deck_analysis_findings` — severity, named rule, source metric, message, and threshold.
- `deck_analysis_relationships` — objective fact relationships and contributing card evidence.
- `current_deck_analyses` — the latest successful result pointer per Deck Version.

### 6. Design knowledge

- `design_notes` — categorized human-authored notes attached to supported subjects.
- `design_decisions` — durable decisions with rationale and status.
- `card_relationships` — curated card-to-card relationships such as Supports, Conflicts With, Replacement, Upgrade, or Combo.
- `design_sessions` — records focused deck-design work and resulting changes.

### 7. Playtesting

- `playtest_sessions` — test sessions tied to one Deck Version.
- `playtest_observations` — measurable findings and qualitative feedback.

Version 1 may begin with session-level data and expand to individual game records only when real use demonstrates the need.

## Stored versus computed

### Stored

- Imported card facts
- Capability rules and derived results
- Capability overrides and rationale
- Characters and Design Intents
- Themes and priorities
- Decks, versions, and card quantities
- Notes, decisions, sessions, and observations

### Computed

- Deck Profile
- Mana curve and color balance
- Capability coverage
- Theme coverage
- Identity drift
- Deck health
- Candidate rankings
- Recommendation score, confidence, and explanation
- Dossiers

## Planned migration sequence

1. `001_initialize.sql`
2. `002_mtg_core.sql`
3. `003_capabilities.sql`
4. `004_tmnt_knowledge.sql`
5. `005_decks.sql`
6. `006_design_history.sql`
7. `007_playtesting.sql`
8. `008_indexes.sql`
9. `009_seed_foundation.sql`
10. `010_import_audit.sql`
11. `011_capability_engine.sql`
12. `012_deck_analysis_engine.sql`

## Validation requirements

A fresh database build must:

- Apply all migrations without error.
- Record each migration exactly once.
- Enforce foreign keys.
- Reject invalid enumerated values and quantities.
- Prevent duplicate natural relationships.
- Preserve Deck Version history.
- Support safe repeatable Scryfall imports.
- Produce no stored recommendations or other unreproducible analysis.

## Scryfall import audit and transaction behavior

Migration `010_import_audit.sql` extends `imports` with the source URI and type, source update time, SHA-256 checksum, byte size, processed/imported/skipped/warning/error counts, serialized warnings, and canonical source metadata.

The audit attempt is committed before source acquisition and fact processing. All fact upserts, natural-relationship replacement, validation, and the successful outcome transition occur in one immediate transaction. Failures roll back that transaction, then update the durable attempt to `failed`.

Reimporting an identical source produces stable fact rows and natural relationships while adding a new audit attempt. Identical snapshots are intentionally revalidated rather than skipped so every operator-requested attempt has a complete, independently auditable outcome. A changed source updates canonical facts by their natural identities and replaces relationships for every included Oracle ID.

ZIP input must contain exactly one root-level JSON file. Zero JSON members, multiple JSON members, nested members, parent traversal, absolute paths, and backslash-based paths are rejected before the member is read. Archives are read in memory and are never extracted to the filesystem.

The importer accepts both legacy Scryfall JSON-array bulk payloads and the current gzipped JSON Lines bulk payload advertised by `jsonl_download_uri`.
