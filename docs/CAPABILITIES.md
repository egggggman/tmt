# Capability Catalog and Rule Guide

## Boundary

The Capability Engine answers one question: **What does this Magic card do?** The Oracle card is the
analysis unit. Faces, Oracle text, and normalized keywords contribute objective evidence. The engine
does not contain TMNT, Character, Design Intent, Theme, Deck Profile, recommendation, synergy-score,
or deck-analysis logic.

> Store facts. Compute intelligence. Preserve decisions.

## Confidence

Confidence is evidence strength in `[0,1]`, not quality, power, theme fit, or recommendation strength.
Direct unambiguous text normally receives 0.95–0.98, a normalized keyword 0.90–0.95, and a narrower
but context-sensitive phrase 0.75–0.90. Multiple rules for one Capability combine by maximum
confidence; every matched rule retains its own evidence. Add overrides state their own confidence,
remove overrides suppress without deleting derivation, and adjustments apply a signed delta clamped
to `[0,1]`.

## Canonical vocabulary

| Identifier | Canonical name | Narrow definition | Evidence sources | Positive example | Negative control / limitation |
|---|---|---|---|---|---|
| `targeted-removal` | targeted removal | Removes a chosen opposing permanent or creature. | Oracle text: `destroy/exile target …` | “Exile target creature.” | “Destroy target creature you control” is excluded; sacrifice and damage are not inferred. |
| `board-wipe` | board wipe | Destroys or exiles all of a broad permanent class. | Oracle text: `destroy/exile all …` | “Destroy all creatures.” | One-sided mass bounce, damage, and global power reduction are not yet classified. |
| `protection` | protection | Grants your permanent or player hexproof, indestructible, or protection. | Keyword; narrow Oracle-text grant | “Creatures you control gain indestructible.” | Prevention alone and protection granted only to opponents are excluded. |
| `counterspell` | counterspell | Counters a spell or stack ability. | Oracle text: `counter target …` | “Counter target spell.” | “This spell can’t be countered” is excluded. |
| `card-draw` | card draw | Directly instructs the controller to draw cards. | Imperative Oracle-text phrase | “Draw two cards.” | Replacement effects, opponent-only draws, reminder text, and “draws” in names do not match. |
| `card-selection` | card selection | Filters or examines library cards without inherently increasing hand size. | Scry/surveil keyword; top-library look phrase | “Scry 2.” | Tutors, looting, and broad library manipulation are not inferred. |
| `ramp` | ramp | Adds reusable mana capacity or puts an extra land onto the battlefield. | Oracle text putting a land onto battlefield | “Put that land card onto the battlefield.” | Land-to-hand search and temporary mana are intentionally excluded. |
| `mana-fixing` | mana fixing | Offers a choice of mana colors. | Oracle text: `add one mana of any color` | “Add one mana of any color.” | Single-color production and color identity alone do not match. |
| `token-creation` | token creation | Directly creates game-piece tokens. | Imperative Oracle text: `create … token` | “Create two 1/1 tokens.” | Token mentions used only as costs, conditions, or references do not match. |
| `recursion` | recursion | Returns or casts a targeted card from a graveyard. | Oracle text return/cast-from-graveyard phrase | “Return target creature card from your graveyard to your hand.” | Self-recurring cards and untargeted mass recursion are not yet covered. |
| `graveyard-interaction` | graveyard interaction | Exiles targeted cards from a graveyard. | Oracle text exile-from-graveyard phrase | “Exile target card from a graveyard.” | Mill and incidental graveyard counting are not classified. |
| `combat-support` | combat support | Temporarily gives the controller’s creature team a power/toughness bonus. | Oracle-text team-pump phrase | “Creatures you control get +1/+1 until end of turn.” | Single-creature pumps and permanent anthem effects are not yet covered. |
| `evasion` | evasion | Makes the controller’s creature harder to block. | Evasion keyword; narrow unblockable phrase | Flying; “Target creature you control can’t be blocked.” | Unblockability granted to an opponent’s creature is excluded. |
| `life-gain` | life gain | Directly causes the controller to gain life. | Oracle text: `you gain … life` | “You gain 3 life.” | Opponent life gain and life loss do not match. |
| `sacrifice-support` | sacrifice support | Explicitly provides or rewards sacrificing a permanent. | Oracle-text sacrifice phrase | “Sacrifice another creature:” | Opponent sacrifice instructions may still need semantic refinement; incidental rules mentions are excluded where the phrase does not match. |
| `artifact-synergy` | artifact synergy | Explicitly uses artifacts as a resource, condition, or beneficiary. | Narrow artifact-reference phrase | “Artifacts you control …” | Merely being an Artifact is not evidence; this deliberately broad bucket has lower confidence. |
| `equipment-synergy` | equipment synergy | Explicitly uses Equipment, equipped status, or equip cost. | Oracle-text Equipment phrase | “Equipped creature gets …” | Merely having the Equipment subtype is not enough without matching text. |
| `cost-reduction` | cost reduction | Explicitly reduces a spell, ability, or equip cost. | Oracle text: `costs … less` | “Artifact spells cost {1} less.” | Alternative costs, free casting, and cost increases are not classified. |
| `tempo` | tempo | Temporarily sets back an opposing permanent by bouncing or tap-locking it. | Narrow bounce or tap/untap phrase | “Return target nonland permanent to its owner’s hand.” | Self-bounce and ordinary tapping without an untap restriction are excluded. |
| `finisher` | finisher | Creates explicit broad game-ending combat pressure. | Additional-combat or team-double-strike phrase | “There is an additional combat phase.” | High mana value, large stats, and subjective threat quality are never sufficient alone. |

## Rule and evidence lifecycle

Rules are an ordered immutable tuple. The rule-set checksum covers every rule field and ordering, so a
pattern, exclusion, confidence, or order change alters the checksum. A released rule set is never
silently rewritten under the same version. Derivation deletes the current derived/evidence layer and
rebuilds it in one transaction. Removed rules and deprecated catalog entries therefore cannot leave
active results. If a run fails, the transaction rolls back, the failed run remains audited, and the
previous successful computed state remains visible.

For cards with faces, face text replaces duplicated card-level text as evidence. Each match records the
correct face number. Normalized card-level keywords remain Oracle-card evidence. This avoids counting
the same first-face text once at card level and again at face level.

## Known limitations

- Rules use English Oracle text and normalized English keywords.
- Parenthetical reminder text is removed with a conservative non-nested pattern before matching.
- There is no full Comprehensive Rules interpreter.
- The engine does not infer combos, dependencies, delayed interactions, or semantic equivalence.
- Narrow rules favor explainable precision over recall; documented false negatives are expected to
  become new versioned rules only after objective evidence and negative controls are defined.
