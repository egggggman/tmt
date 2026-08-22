# Acceptance Stage #002 Results Audit #1

## Verdict

**REJECT — the Stage #002 execution completed fail-closed and its arithmetic is internally consistent, but the raw artifact omits the second duplicate digest/artifact and all authoritative opportunity-context records, so duplicate determinism and 56 context-backed REACHED claims cannot be independently reconstructed.**

This is an evidence-serialization/runner defect. The audit found no gameplay defect and does not dispute the 32 typed-event-backed reaches or the 55 authenticated EXECUTED references.

## Frozen evidence

- Audited commit: `c124408758ad0381aebf88a5d4e26cf89abffc6e`
- Raw artifact: `docs/cardcade/ACCEPTANCE_STAGE_002_RESULTS.json`
- Raw SHA-256: `0e1631f24fba87eca54566f9072a9e1651e00f9c9ca73e75e1bfaa7522fc66c7`
- The raw artifact was not modified.
- No Stage game was rerun.
- No runner, engine, Action, Pilot, test, or deck was modified.

## Independently reproduced structure and arithmetic

The audit parsed the complete raw artifact and recomputed canonical SHA-256 digests without using
the stored digest values as inputs.

| Check | Independent result |
|---|---:|
| Full manifest rebuilt from frozen deck/card data | exact match |
| Manifest digest | `58788be5bc4322ba7ffc5aa36b1df61fd3f487d6b2ea539b3129a998d4cdf771` |
| Aggregate digest | `6afc18984d7eab6bf0ce57d6be643649b0b85ebcfc7a25866c072094d6ee148e` |
| All 16 per-game report digests | exact match |
| Matrix membership | exactly 4 pairings × 2 seeds × 2 orientations |
| Distinct game IDs | 16 |
| Claimed duplicate executions | 32 |
| Runner stops serialized | 0 |
| Invariant violations serialized | 0 |
| Coverage summaries across game/pairing/orientation/deck | exact recomputation |

The matrix contains each authorized tuple exactly once:

- Donatello/Krang: seeds 7201–7202, canonical and reversed;
- Michelangelo/Bebop & Rocksteady: seeds 7211–7212, canonical and reversed;
- Splinter/Shredder: seeds 7221–7222, canonical and reversed;
- April/Casey: seeds 7231–7232, canonical and reversed.

## Classification totals and integrity

### Unique semantic keys across all games

| Class | Union | Intersection across all 16 games |
|---|---:|---:|
| EXECUTED | 10 | 0 |
| REACHED / UNSUPPORTED | 16 | 0 |
| PRESENT / UNREACHED | 209 | 0 |

### Runtime rows

| Evidence table | EXECUTED | REACHED / UNSUPPORTED | PRESENT / UNREACHED | Total |
|---|---:|---:|---:|---:|
| Semantic occurrences | 15 | 66 | 142 | 223 |
| Presence/object-fragment rows | 29 | 66 | 3,628 | 3,723 |

Every occurrence and presence row has exactly one allowed classification. Every per-game
`classification_sets` value exactly equals a fresh set projection from its presence rows.

The same semantic key can occur in more than one class within one game because different runtime
objects carrying the same Oracle fragment can have different histories: one instance may execute
or reach an opportunity while another remains merely present. This is not a row-level exclusivity
failure; the object/occurrence identities remain distinct.

## EXECUTED authentication

All 55 serialized execution references also appear in the authenticated set. The audit rebuilt an
independent evidence-kind/ID index from each report's immutable transaction/event collections,
then required exact evidence kind, evidence ID, source identity, Oracle fragment, semantic key, and
presence lineage. No authentication failure was found.

| Evidence kind | Authenticated references |
|---|---:|
| `trigger_resolved` | 26 |
| `tokens_created` | 15 |
| `damage_dealt` | 3 |
| `discard_draw` | 3 |
| `hand_bottom_draw` | 3 |
| `strike_damage_step` | 2 |
| `lifelink` | 1 |
| `sneak` | 1 |
| `trample` | 1 |
| **Total** | **55** |

This evidence supports the 15 executed semantic occurrences and 10-key EXECUTED union. The larger
reference count is expected because one semantic execution can have multiple mature evidence
records, such as trigger resolution plus child transaction evidence.

## The 16 REACHED / UNSUPPORTED semantics

Frequency is `games / classified occurrences / witnesses`. “#001” states whether the exact
semantic key overlaps Acceptance #001; all others are Stage #002 novelty. Decks are frozen-manifest
exposure, not a claim that every listed copy reached the opportunity.

| Card — frozen deck exposure | Exact Oracle fragment | Reach evidence | Frequency | #001 | Explicit missing semantics |
|---|---|---|---:|:---:|---|
| Rock Soldiers — Casey | `When this creature enters, destroy up to one target noncreature artifact.` | exact self-ETB typed event | 2 / 2 / 2 | No | Oracle ability |
| Courier of Comestibles — Michelangelo | `When this creature enters, you may search your library for a Food card, reveal it, put it into your hand, then shuffle. If you don't put a card into your hand this way, create a Food token. (It's an artifact with "{2}, {T}, Sacrifice this token: You gain 3 life.")` | exact self-ETB typed event | 1 / 1 / 1 | No | conditional token context |
| Zoo Escapees — Bebop & Rocksteady; Michelangelo | `When this creature leaves the battlefield, create a Mutagen token. (It's an artifact with "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.")` | departure context at combat damage | 1 / 1 / 1 | No | trigger context; Mutagen activation |
| Donatello, Way with Machines — Donatello | `Whenever an artifact you control enters, put a +1/+1 counter on Donatello.` | artifact-entry/count context | 2 / 3 / 3 | No | Oracle ability |
| Buzz Bots — April; Donatello; Krang | `When this creature dies, draw a card.` | departure contexts at main/combat boundaries | 8 / 13 / 13 | No | Oracle ability |
| Ravenous Robots — Casey | `{R}, {T}: Creature tokens you control gain haste until end of turn.` | payable activation context with token subjects | 3 / 3 / 6 | No | activation child effect |
| Shredder, Unrelenting — Shredder | `Whenever Shredder enters or attacks, another target creature you control gains deathtouch until end of turn.` | authoritative attack-declaration event | 1 / 1 / 1 | No | Oracle ability |
| Ray Fillet, Man Ray — April; Krang | `{2}, Remove a +1/+1 counter from a creature you control: Draw a card.` | activation context with removable-counter subjects | 3 / 3 / 12 | No | nonmana cost; Draw child |
| Utrom Scientists — April; Krang | `When this creature enters, tap up to one target creature and put a stun counter on it. (If a permanent with a stun counter would become untapped, remove one from it instead.)` | exact self-ETB typed event | 6 / 9 / 9 | No | Oracle ability |
| Dream Beavers — Shredder; Splinter | `When this creature enters, each opponent loses 1 life and you gain 1 life. Scry 1. (Look at the top card of your library. You may put that card on the bottom.)` | exact self-ETB typed event | 4 / 8 / 8 | No | preceding effects and trigger context around Scry |
| Casey Jones, Jury-Rig Justiciar — Casey | `When Casey Jones enters, look at the top four cards of your library. You may reveal an artifact card from among them and put it into your hand. Put the rest on the bottom of your library in a random order.` | exact self-ETB typed event | 3 / 3 / 3 | **Yes** | Oracle ability |
| Super Shredder — Shredder | `Whenever another permanent leaves the battlefield, put a +1/+1 counter on Super Shredder.` | departure contexts at main/combat boundaries | 3 / 5 / 13 | No | Oracle ability |
| Stockman, Mad Fly-entist — Krang | `When Stockman enters, draw a card, then discard a card.` | exact self-ETB typed event | 2 / 2 / 2 | No | sequential Draw/Discard ability |
| Casey Jones, Vigilante — Casey | `When Casey Jones enters, draw three cards. At the beginning of your next upkeep, discard three cards at random.` | exact self-ETB typed event | 2 / 2 / 2 | No | compound Draw/delayed random Discard |
| Fugitive Droid — April; Donatello; Krang | `{U}, Sacrifice this creature: Counter target spell that targets an artifact or creature you control.` | activation/response context with represented subjects | 4 / 6 / 8 | No | nonmana cost, targets/choices, counter child |
| Donatello, Turtle Techie — Donatello | `When Donatello enters, if you control an artifact, draw a card.` | exact self-ETB typed event with artifact predicate | 2 / 4 / 4 | No | Oracle ability |

The exact frequencies sum to 66 classified occurrences and 88 witnesses. Of those witnesses, 32
use typed rules-event IDs. Each of those 32 IDs resolves to the matching immutable `rules_event`
record, event kind, subject identity, turn, and step in the raw report.

The remaining 56 witnesses use `cause_kind = authoritative_context`. They cover Zoo Escapees,
Donatello Way with Machines, Buzz Bots, Ravenous Robots, Ray Fillet, Super Shredder, and Fugitive
Droid. Those are plausible genuine unsupported gameplay opportunities, not evidence of newly
implemented behavior. However, the raw artifact does not contain the context records needed to
authenticate their detailed predicates.

## Material evidence blockers

### 1. Duplicate determinism is asserted but not independently preserved

Each game stores one `duplicate_sha256`. The artifact does not store first and second canonical
snapshot digests, nor both duplicate snapshots. The 16 stored values are distinct across the 16
different games, which proves only that the games differ. It cannot prove that each game's two
executions were byte-identical.

`execution_count = 32` is therefore a runner-produced arithmetic claim (`16 × 2`), not
independently reconstructive duplicate evidence. The runner may have compared the two snapshots in
memory, but Results Audit #1 cannot independently verify that gate from this immutable artifact.

### 2. Authoritative context provenance is omitted

The raw artifact contains 68 context-based witnesses in total, including 56 attached to
REACHED / UNSUPPORTED occurrences, but contains **zero** serialized `opportunity_contexts` records.
The witness rows retain a `cause_id`, source, subjects, zones, turn, phase, and step, but omit the
context's typed facts and provenance needed for the previously audited applicability checks:
instruction occurrence identity, cost/resource facts, exact artifact-count membership, departure
identity, Stack/response linkage, and target/choice predicates.

Consequently the seven context-backed semantics above cannot be independently promoted from
PRESENT / UNREACHED using the raw result alone. This does not prove those promotions false; it
means the durable evidence is insufficient to audit them.

## Runner defects versus gameplay findings

- **Runner/evidence defects:** missing paired duplicate evidence and missing authoritative-context
  records in the per-game result.
- **Verified evidence:** manifest/report/aggregate arithmetic, matrix membership, zero serialized
  stop/invariant records, all 55 EXECUTED reference authentications, and all 32 typed-event witness
  links.
- **Genuine unsupported gameplay surface:** the 16 fragments remain explicit unsupported semantics;
  none was silently executed. The audit does not authorize implementing any of them.
- **Gameplay defect:** none established by this audit.

## Smallest correction

Do not change gameplay or semantic support.

1. Serialize both canonical duplicate snapshot digests (or both immutable duplicate artifacts) per
   game so equality can be independently checked rather than inferred from one stored digest.
2. Serialize the authoritative `opportunity_contexts` used by every context-backed witness,
   including their immutable typed facts and IDs, and include them in each report digest.
3. Add runner tests proving duplicate mismatch evidence is reconstructive and every context witness
   resolves to exactly one serialized context whose applicability facts agree.
4. Preserve this raw artifact unchanged. After the evidence-only runner correction is independently
   accepted, rerun Stage #002 from game #1 to generate a new results artifact.

## Gate

- Acceptance Stage #002 Results Audit #1: **REJECT**
- Stage #002 results: **not accepted as durable independently auditable evidence**
- Stage #002 gameplay: no failure established
- Action #13 and all downstream work: **not authorized**
- Prototype 0.3, calibration, smoke, Pilot changes, deck revisions, and gameplay changes: blocked

**REJECT — preserve the completed raw run as historical evidence, correct only duplicate/context serialization in the runner, independently audit that correction, and rerun Stage #002 only after the tooling gate passes.**
