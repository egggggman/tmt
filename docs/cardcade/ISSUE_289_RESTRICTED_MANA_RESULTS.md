# Issue 289 — restricted mana checkpoint

Stacked on draft PR #301. This is an engine checkpoint, not a Baseline 005 balance result.
The ten Baseline 005 deck lists and prior calibration evidence remain unchanged.

## Oracle fixture and scope

The frozen catalog gives Purple Dragon Punks (four Casey Jones copies):

> `{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability.`

The interpreter accepts the general tap-to-add-one-mana grammar and the represented
artifact-spell/activated-ability restriction, independent of card name. Unsupported
follow-up text and unfamiliar restrictions fail closed. Any-color output is also
interpreted generically, replacing the previous Frog Butler name branch for mana.

Each generated mana unit retains its source object ID, production event ID, color,
quantity, and allowed spending contexts. Artifact spells and activated abilities
can select eligible units; nonartifact spells cannot. Announcements revalidate exact
production IDs before consumption. Invalid multi-unit payments leave the entire
pool untouched. Activation costs (including tapping and sacrifice) and consumption
are evidenced separately, including hand-zone landcycling activation costs. Mana
abilities resolve immediately without entering the
stack or changing an existing priority window. Unspent mana expires at each step
boundary. Lands continue to use the established direct land payment planner, so
pilot activation options do not auto-tap land mana abilities.

## Validation evidence

- `tests/test_restricted_mana.py`: general/renamed and frozen-text interpretation;
  legal artifact cast and activated-ability payment; illegal creature cast; source
  departure; stale plans and all-or-nothing consumption; priority and stack
  independence; summoning sickness; step expiry; replay equality.
- Existing Frog Butler mana, casting discount, activation, and sealed V3 pilot
  fixtures were revalidated. The original activation membership digest remains an
  explicit predecessor assertion; new membership is separately locked. The V3
  codec omits the empty optional mana choice in historical fixture projections.
- Full regression: **1,759 passed, 10 skipped**. Focused Ruff check and format,
  `git diff --check`, and Baseline 005 structural validation passed.
- Machine evidence: `ISSUE_289_RESTRICTED_MANA_CHECKPOINT.json` and
  `ISSUE_289_RESTRICTED_MANA_SMOKE.json`. The smoke uses four mirrored frozen
  Casey/Krang and Casey/Raphael games, four exact replays, 20 restricted mana
  productions, and 10 matched production-to-payment references. These are
  diagnostic games, never a balance experiment.
- Baseline 005 structural validation passes. Its old status string contains
  historical 24→22 land prose; the authenticated lists and manifest are unchanged.

## Coverage and gates

The original 172-row ledger has SHA-256
`56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`.
The exact #301 overlay predecessor has SHA-256
`555fda0587cdfbb30cabf522a27d522628736dfbd1114d5c97f3b672b08c70a2`.
The new overlay preserves every row and changes only Purple Dragon Punks from P0
gap to supported: **23 critical, 64 important, 3 partial** remain; 84 gaps,
45 supported, 33 covered, and 7 annotations. The remaining critical mechanics
still block calibration.

Semantic runtime: `0d953551f6faee293e74afb9642c75c8cc7a9c93142f64a4c0d7b45537d3832a`.
This differs from PR #301's
`a3044b406738ae66f12ad3173a655849a5b5317ae2c009d80a460edfca94a178`;
the old Baseline 005 control is not runtime compatible. The other newly parsed
catalog mana fragments are outside the frozen ten-deck roster or have independent
companion clauses; this checkpoint makes no whole-card coverage claim for them.

**Checkpoint acceptance:** READY for independent review after remote CI succeeds.
**Baseline 005 calibration:** BLOCKED. No 4,500-game control is authorized.

No deck revision, promotion, automatic merge, or calibration simulation occurred.
