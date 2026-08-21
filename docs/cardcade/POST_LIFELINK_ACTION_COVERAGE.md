# Post-Lifelink Action Coverage

Status: evidence-only Action #9 recommendation  
Audited date: 2026-08-20  
Audited branch: `main`  
Audited HEAD: `4c15424494cb0de6869537d31fc2f14881711295`  
Integrated change: PR #38, accepted bounded Lifelink damage-result processing

## Decision

Recommend **Action #9: bounded optional hand-bottom filtering followed by conditional Draw**.

The first represented consumer should be the generic Oracle construction “You may put a card from
your hand on the bottom of your library. If you do, draw a card.” This is a reusable semantic
transaction, not a Manhole Missile card-name implementation. It does not authorize general
Discard, arbitrary library ordering, mass Draw, replacement Draw, attack-trigger delivery, or
unrelated spell follow-ups.

## PR #38 integration evidence

PR #38 was based on `main` `47eee13482efef625e2a11f75163f71ac567342d`. At the final gate,
current `main` was still that exact commit, the merge base matched it, and the branch had no
intervening Cardcade conflict. GitHub reported `MERGEABLE / CLEAN`, and both checks passed.

The PR diff contained exactly:

- `src/tmnt_design_studio/card_interpreter07.py`;
- `src/tmnt_design_studio/engine07.py`;
- `tests/test_lifelink_action.py`;
- `docs/cardcade/POST_TRAMPLE_ACTION_COVERAGE.md`;
- `docs/cardcade/LIFELINK_ACTION_ACCEPTANCE.md`.

The acceptance report remained byte-identical in the repository at SHA-256
`e6f7e2c82b7a9233badd65fd5ea084d399369333ed4f54e5b027f369b2edbc11`.
PR #38 was squash-merged as `4c15424494cb0de6869537d31fc2f14881711295`, which is also the
resulting local and remote `main` HEAD.

Merged-main validation passed:

- full suite: **415 passed / 1 skipped**;
- Lifelink: **16 passed**;
- SemanticCoverage plus card data: **10 passed**;
- damage/combat/strike/Trample: **122 passed**;
- identity/SBA/Stack/cost/trigger/layer/Token/Return: **117 passed**;
- Ruff format and check: clean;
- `git diff --check`: clean.

GitHub Actions run 32434902146 passed on the merged HEAD.

## Integrated Acceptance evidence

Acceptance Match #001 seeds 7001–7005 were replayed twice. Every duplicate JSON artifact was
byte-identical.

| Seed | Winner | Ending turn | Unsupported events | Exact pairs | Lifelink transactions |
|---:|---|---:|---:|---:|---:|
| 7001 | Raphael | 16 | 9 | 9 | 0 |
| 7002 | Raphael | 16 | 5 | 4 | 0 |
| 7003 | Leonardo | 19 | 11 | 9 | 0 |
| 7004 | Leonardo | 21 | 11 | 10 | 1 |
| 7005 | Raphael | 16 | 4 | 4 | 0 |
| **Aggregate** | | | **40** | **14** | **1** |

The genuine seed-7004 transaction remains Leonardo, Cutting Edge dealing 1 regular combat damage
and its controller gaining 1 life. All runs contained zero invariant violations.

## Evidence universe

The ranking was recomputed from the authoritative 472-print / 332-Oracle-object TMT/PZA/TMC
snapshot, the canonically resolved 102-card frozen roster across all ten decks, the seven unchanged
context-sensitive UNKNOWN objects, and the actual merged-main execution surface.

Accepted Create Token, Deal Damage, Scry, First/Double Strike, Activated-Ability delivery,
Targeted Return, Trample, and Lifelink payloads are not charged again when an unsupported parent,
choice, cost, permission, or follow-up is the real blocker.

The seven UNKNOWN objects remain Arcane Signet, Chromatic Lantern, Command Tower, Double Jump //
Flying Kick, Exotic Orchard, Fast Forward, and Plague of Vermin.

## Exact residual Acceptance attribution

| Missing semantic capability | Events | Pairs | Exact exposure |
|---|---:|---:|---|
| Sneak casting transaction | 16 | 5 | Big Brother 5; Leader in Blue 5; Sewer Samurai 3; Cutting Edge 2; Nightwatcher 1 |
| Filtering plus Draw | 8 | 2 | Manhole Missile optional hand-bottom/Draw 4; Null Group optional Discard/Draw attack trigger 4 |
| Exile/graveyard/play permissions | 7 | 3 | Sewer Samurai graveyard/finality 3; Raphael exile-top 2; Raphael play-exiled 2 |
| Wingnut modal trigger/choice/keyword grant | 3 | 1 | Alliance flying/menace/haste choice 3 |
| Menace / blocker-count expansion | 2 | 1 | Raphael, Most Attitude 2 |
| Look/reveal/selection | 2 | 1 | Casey Jones look-four artifact selection 2 |
| Food activation/use | 2 | 1 | Lita Food reminder/activation 2 |
| **Total** | **40** | **14** | |

No Lifelink event or pair remains. The prior 42/15 surface became 40/14 through one real Lifelink
execution, not through child recognition suppressing an unsupported parent.

## Fresh corpus and dependency census

The corpus was recensused from current `main`; these are recognition/reach figures, not support
claims.

| Family | Full-pool objects / fragments | Frozen reach | Current dependency state |
|---|---:|---:|---|
| Draw references | 54 / 54 | 18 text-bearing cards / 7 decks | Broad reach; current exposed uses are gated by two different filters and one trigger |
| Imperative hand-bottom then Draw | 1 / 1 | 1 card / 2 decks | Exact Manhole pattern; its Deal Damage parent executes four times in Acceptance |
| Sneak | 27 / 32 | 18 mechanic-bearing cards / 6 decks | Return, Stack, Priority, and combat exist; return-as-cost, special casting timing, and tapped-and-attacking entry remain |
| Direct trigger language | 171 / 200 | 54 cards / 10 decks | Broad parent domain; every exposed child still needs another missing semantic capability |
| Discard | 16 / 19 | 10 cards / 6 decks | Null Group also needs attack-trigger delivery and Draw |
| Direct exile/play/graveyard-casting instructions | 25 / 27 | 5 cards / 5 decks | Heterogeneous permissions, durations, finality replacement, and tracked-object rules |
| Menace | 17 / 18 | 6 cards / 4 decks | Requires multiple-blocker legality beyond the represented one-blocker model |
| Food activation/reminder | 5 / 5 | 3 cards / 3 decks | Activated delivery exists; sacrifice cost, token cessation, and life gain remain coupled |
| Look/reveal-to-hand selection | 3 / 3 | 2 cards / 4 decks | Private choice, type filtering, reveal, hand movement, and random-bottom ordering |
| Choice-of-keyword grant | 1 / 1 | 1 card / 1 deck | Wingnut additionally requires Alliance delivery and duration/keyword support |
| Equipment/equip or attachment language | 15 / 40 | 6 cards / 6 decks | No direct residual pair; attachment and equip costs remain a separate architecture slice |

The Draw count includes references and triggered outcomes; it must not be interpreted as 54
immediately executable fixed Draw instructions. Likewise, one roster card refers to Sneak without
itself carrying the mechanic, so the mechanic-bearing frozen count remains 18 rather than the 19
raw text references.

## Re-ranked candidates

| Rank | Candidate | Direct Acceptance leverage | Frozen/full-pool and dependency assessment |
|---:|---|---|---|
| 1 | **Optional hand-bottom filtering + conditional Draw** | **4 events / 1 pair; four existing Manhole Deal Damage executions provide direct delivery** | Exact pattern is 1 / 1 in the pool and 1 card / 2 decks, but it establishes reusable private hand choice, Hand→Library-bottom movement, and fixed Draw. Existing Stack, Deal Damage, Scry choice views, runtime identity, and zone transactions make it medium complexity and immediately executable. |
| 2 | Draw Cards primitive | Child of 8 events / 2 pairs, but clears neither pair alone | Highest pool reach at 54 references and seven decks. It remains blocked by hand-bottom filtering for Manhole and by Discard plus attack-trigger delivery for Null Group. |
| 3 | Sneak casting transaction | 16 / 5 | Largest raw surface and major Turtle gameplay impact, but still a compound high-complexity mechanic: special Declare Blockers casting window, return-as-cost, alternate/additional payment, and tapped-and-attacking entry. |
| 4 | Trigger-delivery expansion | Parent of portions of 13 events / 5 pairs | Very broad 171-object domain, but delivery alone completes no residual pair: children still need Draw/filtering, exile permissions, modal choice/grants, or look/selection. |
| 5 | Exile/graveyard/play permissions | 7 / 3 | Good direct exposure, but the three pairs span different permission, duration, zone, replacement, and tracked-object semantics. They are not one bounded Action. |
| 6 | Food activation/use | 2 / 1 | Accepted activated delivery and Create Token help, but Acceptance currently executes no Food-token transaction. Supporting the reminder would require transactional tap/mana/sacrifice costs, token cessation, and life gain; telemetry reduction alone would not be execution evidence. |
| 7 | Menace / blocker-count expansion | 2 / 1 | Could complete one pair, but requires multiple blockers, legality enumeration, ordering, and combat assignment expansion. |
| 8 | Wingnut modal keyword grant | 3 / 1 | Requires Alliance delivery, a legal modal choice, duration, and separate Flying/Menace/Haste boundaries. |
| 9 | Casey look/reveal selection | 2 / 1 | Narrow compound library operation requiring hidden choice, type filtering, reveal, Hand movement, and deterministic random-bottom ordering. |
| 10 | Equipment/equip | 0 direct | Meaningful roster reach but no direct 40/14 leverage and substantial attachment/cost/state work. |

Raw event count is not the score. Sneak's 16 events do not make it the smallest truthful next
Action. Trigger delivery and generic Draw have broad corpus leverage but do not independently close
a currently exposed pair. Food's pair can disappear from telemetry without a Food token ever being
created in Acceptance, so it lacks the direct execution evidence available for Manhole Missile.

## Action #9 recommendation

Implement an Oracle-derived **bounded optional hand-bottom filtering followed by conditional
Draw** transaction.

The interpreter should separately classify the optional choice, fixed one-card Hand→Library-bottom
movement, conditional “if you do” dependency, fixed Draw payload, surrounding parent, and any later
follow-up through `SemanticCoverage`. The engine should present immutable private legal choices,
revalidate runtime identity, move the selected card as a new object to the bottom of its owner's
library, and draw exactly one card only when the optional move was legally completed. Declining or
having no legal hand card must remain coherent and deterministic.

For Manhole Missile, the existing Deal Damage instruction and this follow-up are sequential parts
of one resolving spell. The implementation must therefore preserve correct resolution atomicity and
must not use Deal Damage's current internal SBA boundary to deliver the follow-up after the spell is
already treated as resolved. Any necessary bounded deferral of SBA/trigger processing must be
explicit and regression-tested rather than approximated.

Unsupported areas should remain explicit: generic Discard, opponent-hand choices, multiple-card or
random hand movement, variable Draw, Draw replacement/prevention, “draw that many,” attack-trigger
delivery, and arbitrary compound spell instructions.

This Action outranks generic Draw because it closes a real pair through four already-executing
parent transactions rather than adding an unreachable child. It outranks Sneak because it reuses
existing Stack, damage, hidden-choice, identity, and zone foundations without introducing a new
combat casting window or tapped-and-attacking entry. It outranks Food and Menace because it has
direct execution evidence and does not require nonmana sacrifice costs or multiple-blocker combat.

No Action #9 implementation is included in this evidence-only report.
