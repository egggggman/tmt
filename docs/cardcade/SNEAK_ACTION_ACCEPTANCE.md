# Sneak Casting Transaction Acceptance Audit #1

Status: **ACCEPT**  
Audit date: 2026-08-20  
Branch: `agent/cardcade-sneak`  
Evidence checkpoint: `12087bd783448039f3c74bcff4b54334daa083f7`  
Audited candidate fingerprint: `927fef529dc10bb711bea8e3d406a63591a261a1`

## Audit integrity

This was an evidence-only audit. No implementation or test file was modified. This report is the
only tracked artifact created by the audit. The candidate was uncommitted throughout.

The fingerprint was independently reproduced as SHA-1 of the newline-joined, path-sorted complete
file SHA-256 values for the five candidate files. It remained
`927fef529dc10bb711bea8e3d406a63591a261a1` after source inspection, executable probes, validation,
and duplicate replay.

## Authoritative rules basis

The audit used Wizards' current [Comprehensive Rules text](https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt),
the official [Teenage Mutant Ninja Turtles update bulletin](https://magic.wizards.com/en/news/announcements/teenage-mutant-ninja-turtles-update-bulletin),
and the official [set mechanics article](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-mechanics).

The represented transaction agrees with the relevant rules boundary:

- CR 702.190a-b makes Sneak a stack permission during the declare-blockers step, using the stated
  Sneak cost plus returning an unblocked attacker controlled by the caster rather than paying the
  spell's mana cost; the resulting permanent enters tapped and attacking the same defender.
- CR 601.2h prohibits partial cost payment.
- CR 400.7 requires zone changes to produce new objects.
- CR 506.3d and 508.4d preserve the attacking state and defender of a permanent put onto the
  battlefield attacking without declaring it as an attacker.
- CR 111.7 and 704.5d govern token cessation after a token leaves the battlefield.
- CR 704.5j supplies the legend-rule state-based action used in the seed-7004 forensic case.

## Transaction and boundary findings

### Interpretation and legal-option generation

`CardInterpreter` recognizes Sneak from Oracle text and the authoritative keyword, parses a fixed
Sneak mana requirement, and returns Action-specific interpretation paired with generic
`SemanticCoverage`. The implementation contains no source-card-name dispatch. The engine—not the
interpreter or Pilot—checks the card's Hand identity, active player, declare-blockers timing,
completed blocker declaration, empty represented stack/Priority boundary, creature type, supported
fixed cost, mana sources, and authoritative unblocked attacker.

The Pilot receives immutable engine-generated `ActionOption` values and may choose an option or
pass. Submission is revalidated against a newly generated legal-option set. A direct nonactive-
player probe produced no Sneak options; a fabricated nonactive-player option and a forged defender
plan were both rejected with byte-equivalent pre/post snapshots.

### Atomic announcement and costs

The engine recomputes the complete `SneakPaymentPlan` before commitment. It validates all mana
source runtime identities, battlefield membership, land status, untapped status, uniqueness, the
Hand object, the attacker, unblocked combat membership, and the same bounded 1v1 defender before
mutating zones or tapping mana. The returned Hand incarnation and Stack object are constructed as
new runtime objects; only after all checks pass are mana sources tapped, the attacker returned, and
the spell moved Hand to Stack.

Executable adversarial probes reject wrong step, pre-blocker timing, nonactive player, blocked
attacker, stale/fabricated/equal-valued attacker, stale/fabricated/equal-valued Hand card,
insufficient mana, reused/invalid mana sources, unsupported hybrid cost, noncreature Sneak, and a
forged defender. The asserted failure snapshots show no partial tap, return, Hand removal, Stack
placement, or combat mutation.

### Stack, Priority, and resolution

Every accepted announcement creates an authoritative `StackObject`. Resolution is refused until
the engine-owned Priority epoch records both represented players passing. The Stack object is then
revalidated and resolves to a new battlefield `Permanent`; no direct Hand-to-battlefield shortcut
exists.

The permanent enters tapped, attacking the plan's defending player, and summoning sick. It is added
to authoritative combat state without emitting a new `attackers_declared` event. Strike-step and
combat-damage eligibility use that current authoritative combat object. Postcombat transition and
cleanup remove all mutable Sneak/combat participation state.

The return cost creates a new Hand identity owned by the attacker's owner, including when another
player controls the attacker. A returned token receives the required transient Hand incarnation and
then ceases at the ensuing state-based-action boundary. Stale pre-return references cannot bind to
the new Hand object. The resolving Sneak creature likewise has an identity distinct from both the
Hand card and Stack object.

### Sneak-paid children

Supported `if its Sneak cost was paid` ETB P/T processing creates a distinct typed trigger object,
then uses its own Stack placement, Priority/pass epoch, and resolution. It is not folded into Sneak
resolution. Unsupported children remain independently reported and prevent false full-fragment
support where they share a classified fragment. A supported Sneak parent therefore does not
silently promote an unsupported child.

## Coverage reproduction

An independent pass over the authoritative 472-print / 332-Oracle-object TMT/PZA/TMC snapshot
reproduced:

| Scope | Recognized | Bounded executable | Fully supported |
| --- | ---: | ---: | ---: |
| Full pool | 27 objects / 32 fragments | 14 / 14 | 14 / 14 |
| Frozen roster | 18 cards / 6 decks | 11 cards / 6 decks | 11 cards / 6 decks |

Stable membership digests reproduced exactly:

- recognized: `af93d6edb678df9768372cfc215f2e4fabab455d0eeff2422d05f5a87934b320`;
- executable: `8f49420ba3fd4e31bc9746f2e3b50f70fa9ec7add295840925a4610606bba924`;
- full: `8f49420ba3fd4e31bc9746f2e3b50f70fa9ec7add295840925a4610606bba924`.

The 14 executable/full objects are Dark Leo & Shredder; Donatello, Gadget Master; Karai, Future of
the Foot; Leonardo, Big Brother; Leonardo, Cutting Edge; Leonardo, Leader in Blue; Leonardo, Sewer
Samurai; Michelangelo, Improviser; Oroku Saki, Shredder Rising; Raphael, the Nightwatcher; Shark
Shredder, Killer Clone; Shredder, Unrelenting; Splinter, Hamato Yoshi; and Turncoat Kunoichi.

Corpus inspection confirms that technique/noncreature forms, granted-Sneak text, Sneak references,
and unsupported hybrid-cost shapes are recognized but not executable. Separate compound child
fragments remain separately classified. This candidate does not claim general alternate casting,
general instant-speed casting permission, arbitrary defenders, arbitrary costs, or arbitrary
Sneak-paid triggers. `semantic_coverage.py` is unchanged; its generic model imports or introspects no
Sneak program or runtime type.

## Acceptance replay

The merged baseline replay was independently reproduced at **33 unsupported events / 12 exact
pairs**. Two candidate runs of seeds 7001-7005 were byte-identical per seed and produced:

| Seed | Winner | Ending turn | Sneak transactions |
| ---: | --- | ---: | ---: |
| 7001 | Raphael | 14 | 0 |
| 7002 | Raphael | 18 | 0 |
| 7003 | Leonardo | 19 | 1 |
| 7004 | Leonardo | 43 | 1 |
| 7005 | Raphael | 16 | 1 |

Aggregate candidate evidence is **20 unsupported events / 7 exact pairs**, **3 Sneak
transactions**, **44 Priority grants / 44 passes**, **1 block-restriction rejection**, and **0
invariant violations**.

All five baseline Sneak pairs disappear: Leonardo, Big Brother (7 events); Leonardo, Leader in Blue
(5); Leonardo, Cutting Edge (2); Leonardo, Sewer Samurai's Sneak fragment (2); and Raphael, the
Nightwatcher (1). That is 17 removed events. The net reduction is 13 because legitimate longer/new
execution exposes four downstream events: Wingnut's unsupported Alliance choice increases from 4
to 5, and Leonardo, Sewer Samurai's unsupported graveyard/finality fragment increases from 2 to 5.
No Sneak limitation was suppressed or relabeled as a generic follow-up.

The three immutable records reconstruct independently:

- seed 7003, turn 11: April O'Neil `object-000164` returns as Hand `object-000184`; Leonardo, Big
  Brother moves Hand `object-000151` to Stack `object-000185`, passes Priority epoch 2, and resolves
  as tapped/attacking `object-000186` against defender 1;
- seed 7004, turn 9: April O'Neil `object-000152` returns as Hand `object-000171`; Leonardo, Cutting
  Edge moves Hand `object-000127` to Stack `object-000172`, passes Priority epoch 1, and resolves as
  tapped/attacking `object-000173` against defender 1;
- seed 7005, turn 3: Prehistoric Pet `object-000137` returns as Hand `object-000144`; Leonardo, Big
  Brother moves Hand `object-000123` to Stack `object-000145`, passes Priority epoch 1, and resolves
  as tapped/attacking `object-000146` against defender 1.

## Seed 7004 forensic reconstruction

At turn 9 the authoritative attack event declares April `object-000152` and the existing Leonardo,
Cutting Edge `object-000161`. The only block pairs `object-000161` with Null Group Biological Assets
`object-000166`, so April is a legal unblocked attacker. The engine-generated Sneak option pays the
white component with land `object-000139` and returns April. Cutting Edge moves through Stack
`object-000172`; both players pass the engine-owned Priority epoch; and it resolves as new permanent
`object-000173`, tapped and attacking defender 1 without another attack-declaration event.

The existing `object-000161` and new `object-000173` legitimately coexist after resolution and
before the next SBA. The legend-rule event then keeps the existing copy and moves new
`object-000173` to graveyard as new object `object-000174`. The existing copy remains in combat,
exchanges regular combat damage with Null Group, and later moves to graveyard as `object-000175`
for lethal damage. April's returned Hand object remains `object-000171` until its later normal cast.
These identities and event ordering rule out duplicate-object binding, skipped legend/lethal SBAs,
incorrect combat insertion, and Priority leakage.

The resulting turn-43 game follows from a legal engine-generated but strategically poor choice:
the Pilot returned April to cast a second legendary Cutting Edge that immediately lost the legend
choice. Pilot quality is outside this Action's acceptance boundary; the submitted option and every
engine transition were legal.

## Validation

| Gate | Result |
| --- | --- |
| Full suite | **479 passed / 1 skipped** |
| Focused Sneak suite | **17 passed** |
| SemanticCoverage + card data | **10 passed** |
| Casting / Stack / Priority / cost / zone / combat regressions | **185 passed** |
| Ruff format check | clean; 5 candidate files already formatted |
| Ruff check | clean |
| `git diff --check` | clean |
| Candidate fingerprint after audit | `927fef529dc10bb711bea8e3d406a63591a261a1` |

No material rules, identity, transaction, telemetry, architecture, coverage, or deterministic-replay
blocker remains within the deliberately bounded scope.

**ACCEPT — bounded Sneak casting transaction is suitable to bank with its documented coverage.**
