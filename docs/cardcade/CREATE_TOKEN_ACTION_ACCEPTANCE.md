# Create Token Action Acceptance Audit

Audit date: 2026-08-14 EDT

Committed baseline: `2218b68f0786dc01e0155c7388a769e9ab927086`

Candidate state: uncommitted changes to `card_interpreter07.py`, `engine07.py`, and
`test_create_token_action.py`. This audit did not modify those files. The only audit write is this
evidence report.

## Recommendation

REJECT

The authoritative token transaction itself is coherent and passes every direct identity, zone,
state-based-action, characteristic, event, and determinism probe. The coverage boundary is not yet
safe, however. `CardInterpreter.unsupported_fragments()` treats every recognized token fragment as
handled and suppresses the fragment whenever `TokenCreationProgram` has neither an
`unsupported_reason` nor a `retained_limitation`. Eighteen executable token-payload fragments have
no retained limitation. Several of their trigger, activation, condition, preceding-effect, or
follow-up semantics are not represented by the engine.

Executable probes confirmed, for example, that Waste Not, Dark Leo & Shredder, Rat King,
Verminister, Uneasy Alliance, Foot Mystic, and Mouser Foundry are omitted from unsupported reporting
even though their relevant discard, combat-damage, end-step condition, activated ability,
conditional ETB, and artifact enter/leave delivery paths are not implemented. This is a silent
coverage overclaim and fails the explicit-unsupported-semantics requirement.

The smallest evidence-backed correction is to separate **bounded Create Token payload support** from
**whole Oracle-fragment support**. A recognized/executable payload must retain a delivery,
condition, preceding-effect, activation, or follow-up limitation unless the complete represented
fragment is actually wired to an authoritative event/trigger/spell/ability path. Add adversarial
tests for the examples above. The recognition pass must also retain Plague of Vermin as explicit
UNKNOWN/unsupported despite its “creates” grammar. No additional token-copy, variable-quantity,
replacement, combat, activation, or other Action implementation is required to correct these
blockers.

## Repository and audit integrity

- local HEAD was exactly `2218b68f0786dc01e0155c7388a769e9ab927086`;
- local and remote `agent/cardcade-create-token` committed HEADs matched;
- the committed baseline contains only the Action Coverage report;
- the candidate implementation and tests remained uncommitted throughout the audit;
- no deck, Prototype 0.3, calibration, smoke, pilot, or unrelated Action change was present;
- `git diff --check` passed before this report was created.

## Coverage-count reconciliation

The numeric recognition and token-payload counts are reproducible from the authoritative
472-print / 332-Oracle-object snapshot:

| Claim | Independent result | Finding |
| --- | ---: | --- |
| Frozen-roster recognition | 21 cards / 10 decks | Count confirmed |
| Full-pool recognition | 62 Oracle objects / 67 fragments | Parser count reproduced, but population not confirmed: Plague of Vermin is missing |
| Frozen-roster bounded token payload | 17 cards / 10 decks | Count confirmed |
| Full-pool bounded token payload | 46 objects / 47 fragments | Count confirmed |
| Regression-tested recognition | 21 / 10 and 62 / 67 | Test confirms the parser's current population, not the complete baseline population |
| Token transaction exercised | 17 / 10 and 46 / 47 | The corpus test calls the same transaction for all 47 bounded payloads |

“Bounded executable” is valid only for the Create Token payload. It is not evidence that the full
Oracle fragment, its delivery mechanism, or compound semantics are supported. The current
unsupported-reporting behavior fails to preserve that distinction.

The matching `62 / 67` recognition total also masks a membership defect. Plague of Vermin's Oracle
text says that each player “creates a 1/1 black Rat creature token for each 1 life they paid this
way.” The candidate's singular `create` pattern returns no token program for that fragment. Plague
of Vermin was explicitly part of the baseline's seven UNKNOWN objects and Create Token family, so
it must remain recognized-but-UNKNOWN/unsupported rather than disappear from the coverage universe.
The 62-object parser output below therefore cannot by itself confirm the baseline's 62-object
population even though its raw count happens to match.

## Exact frozen-roster inventory

`Executable` below means the token payload has fixed, derivable characteristics and quantity. It
does not claim that every source card's full delivery context is implemented.

| Card | Frozen deck exposure | Payload classification |
| --- | --- | --- |
| Courier of Comestibles | Michelangelo | Executable |
| Crustacean Commando | Donatello; April O'Neil; Krang | Executable |
| Donatello, Gadget Master | Donatello | Recognized only: copy |
| Foot Mystic | Splinter; Shredder | Executable |
| Improvised Arsenal | Casey Jones | Recognized only: copy |
| Lita, Little Orphan Amphibian | Leonardo | Executable |
| Michelangelo, Mutant BFF | Michelangelo | Executable |
| Michelangelo, Weirdness to 11 | Michelangelo | Executable |
| Mighty Mutanimals | Leonardo | Executable |
| Mouser Attack! | Raphael | Executable |
| Mouser Foundry | Casey Jones | Executable |
| Mutagen Man, Living Ooze | Bebop & Rocksteady | Recognized only: variable quantity |
| Mutant Chain Reaction | Michelangelo; Bebop & Rocksteady | Executable |
| Ooze Spill | Donatello; Krang | Executable |
| Ravenous Robots | Casey Jones | Executable |
| Ray Fillet, Man Ray | April O'Neil; Krang | Executable |
| Return to the Sewers | Donatello; April O'Neil | Executable |
| Slithering Cryptid | Michelangelo | Executable |
| Tainted Treats | Bebop & Rocksteady | Executable |
| The Last Ronin's Technique | Leonardo | Recognized only: attacking context |
| Zoo Escapees | Michelangelo; Bebop & Rocksteady | Executable |

This is 21 distinct roster cards. Each of the ten frozen decks contains at least one recognized card
and at least one executable token payload.

## Exact full-pool Oracle-object inventory

The final column is `executable fragments / recognized fragments`. Oracle IDs make the 62-object
population reproducible independent of print name or set printing.

| Oracle object | Oracle ID | Payloads |
| --- | --- | ---: |
| April O'Neil, Human Element | `020963ef-24c0-48cc-8776-bc257df684bc` | 1 / 1 |
| April O'Neil, Live on the Scene | `4900c157-8d9f-4f92-aaca-5246b6e2832e` | 1 / 1 |
| Baxter Stockman | `e610bfd4-d064-410b-929c-1d9dd82828b1` | 1 / 1 |
| Big Apple, 3 a.m. | `dd01ef1f-f6be-498f-82e0-dc04833e685f` | 0 / 1 |
| Big Mother Mouser | `94751968-e006-45d0-970b-0ed45d28e6cc` | 0 / 1 |
| Biogenic Ooze | `d2d84ba5-0d20-4ce3-8f1f-93cd9ef94f5f` | 2 / 2 |
| Chrome Dome | `3dc71e16-b935-4ad7-b3f7-945ac2c179a7` | 0 / 1 |
| Coin of Mastery | `d78518ee-df79-48d1-b9d5-4f968b441899` | 1 / 1 |
| Courier of Comestibles | `049d8b06-db90-4b9c-8195-d987b3ef1005` | 1 / 1 |
| Crustacean Commando | `b24a87af-407f-4c58-80b4-caab9c65a233` | 1 / 1 |
| Dark Leo & Shredder | `c3ea6af5-48b9-45d2-9576-46cacb2db5b0` | 1 / 1 |
| Donatello, Gadget Master | `bb6aef0d-052b-44e6-b4cd-2d2eafd84969` | 0 / 1 |
| Doubling Season | `01546b7d-a233-4176-8843-d732074dc5b6` | 0 / 1 |
| Endless Foot Assault | `77ccafd9-6d76-4658-81ab-bde0454fcc15` | 0 / 2 |
| Featherbrained Filcher | `79a9fc1c-a6a9-483a-9ba7-d09fe41760c3` | 1 / 1 |
| Foot Chopper | `1eed017a-342a-47a8-9395-890ef0bd1eb2` | 1 / 1 |
| Foot Mystic | `2043fbde-48c4-4a77-8911-8991d77de1eb` | 1 / 1 |
| Genghis Frog | `1d6d0348-46ad-46ed-ae7b-d7510f0ebe70` | 1 / 1 |
| Here Comes a New Hero! | `c4fb12cb-05e1-4df2-b62e-3391621a601b` | 0 / 1 |
| Improvised Arsenal | `4f02aa99-481c-4089-8f7c-cfe7eaa7dda0` | 0 / 1 |
| Jennika, Bad Apple Big Sister | `b55da4d3-2cad-4c89-ad3f-7d8397b64d52` | 1 / 1 |
| Lita, Little Orphan Amphibian | `212fdb7c-1c7e-4eed-b1ed-bcc14a425da8` | 1 / 1 |
| Lord Dregg, Insect Invader | `2db77e35-a54a-4e9c-8081-c97822515879` | 1 / 1 |
| Mechanized Ninja Cavalry | `2db8dda3-8136-4cf2-ba2d-ecc344a36725` | 1 / 1 |
| Michelangelo, Mutant BFF | `fe1eb8b3-c605-4711-a057-ed3565bfe75c` | 1 / 1 |
| Michelangelo, Weirdness to 11 | `170ab932-9d50-4ce7-9a42-08e1edce7e7c` | 1 / 1 |
| Michelangelo, the Heart | `f11e914c-16bc-4836-bc14-bc1b5de9cd87` | 1 / 1 |
| Mighty Mutanimals | `fcdc7dfc-04b5-411a-ab49-282b9c2608e2` | 1 / 1 |
| Mona Lisa, Ever Adaptable | `9fa38462-57b6-4f2f-a73c-f14a66f56946` | 1 / 1 |
| Mouser Attack! | `bae5dc68-1fd1-428d-bee7-c238e07b21ea` | 1 / 1 |
| Mouser Foundry | `404e958b-ead9-4ec7-b786-7b3d65e29967` | 1 / 1 |
| Mutagen Man, Living Ooze | `472d9a18-19a0-46c0-a4bf-328ebec7ce41` | 0 / 1 |
| Mutant Chain Reaction | `ea9fc868-374b-4acc-be0d-4283907b4524` | 1 / 1 |
| Ninja Pizza | `58c615f3-8c3b-47bf-8032-809fc4232ccb` | 1 / 1 |
| Old Hob, Alleycat Blues | `e88b1520-aa9a-41ee-9036-4d4bebd1a0c0` | 1 / 1 |
| Ooze Spill | `c1c5f9da-1396-4406-b803-b64f66b8e49d` | 1 / 1 |
| Pizza Face, Gastromancer | `e71479c9-bb38-4112-bf8a-41b39a3ade51` | 1 / 1 |
| Raphael, the Muscle | `22008c3b-6e15-41cc-a15c-7871495191aa` | 1 / 1 |
| Rat King, Pale Piper | `da359f85-7a11-4575-848d-642d1ae0ddbb` | 1 / 1 |
| Rat King, Verminister | `a5656dab-5ce6-48fd-9eae-2c06969bb8df` | 1 / 1 |
| Ravenous Robots | `45873747-f2a4-4d83-9492-bfc97df7b605` | 1 / 1 |
| Ray Fillet, Man Ray | `698098b8-b8e4-4e88-b13a-6b039579d192` | 1 / 1 |
| Return to the Sewers | `a3ee8565-f34c-4073-bc94-3fe9ec6bbe8a` | 1 / 1 |
| Roadkill Rodney | `cd8761ef-b57b-456b-aa12-374ac825087e` | 1 / 2 |
| Sally Pride, Lioness Leader | `b529f6b0-c6b2-4eb3-bb48-178e1eda75f3` | 0 / 1 |
| Shellshock | `f406630b-d9f1-4fc5-b3f3-5327384b2901` | 0 / 1 |
| Shredder, Shadow Master | `ee82947d-1cf0-4c53-84d4-81f81c6201ee` | 0 / 1 |
| Slash, Reptile Rampager | `8abff7b5-fe27-46bd-b951-b5d9f93f3a14` | 1 / 1 |
| Slithering Cryptid | `f570bac8-9987-4963-af02-476d18abc847` | 1 / 1 |
| Splinter, the Mentor | `fdcb016e-36e7-46b3-9dff-20b9b9cc421d` | 1 / 1 |
| Tainted Treats | `60826714-b9fd-4c89-b9f2-1a3c3229686b` | 1 / 1 |
| Tempestra, Dame of Games | `12401ad1-b5c9-43dc-9389-04aaf5db8b26` | 0 / 1 |
| The Cloning of Shredder | `bd768e8f-8f04-487e-85e9-2828d6fd8745` | 0 / 2 |
| The Last Ronin's Technique | `6a51bb21-0c01-4ad8-99d7-17685db90b69` | 0 / 1 |
| The Ooze | `82a6fa6f-13c2-4ea3-bec2-c51b56b2783b` | 1 / 2 |
| Tokka & Rahzar, Unsupervised | `8d857d79-bdb2-4ca3-abd6-7db8f6b3bcfa` | 1 / 1 |
| Triceraton Commander | `45d40cdb-21cc-4569-a894-83dd3026c947` | 0 / 1 |
| Turtle Blimp | `bb8c6dd2-1abe-4eb2-be1f-b0c078e5f257` | 1 / 1 |
| Uneasy Alliance | `989b93fe-cad0-4890-a228-8a20ca666f10` | 1 / 1 |
| Waste Not | `00fdcc19-88ed-46c3-91f0-095806228105` | 1 / 1 |
| Wooden Cane | `d41eec6c-de14-4809-abae-b94355674a33` | 1 / 1 |
| Zoo Escapees | `107e9ada-4e2e-4032-addd-274bca956621` | 1 / 1 |

The table totals the candidate parser's 62 objects, 67 recognized fragments, 46 objects with at
least one executable token payload, and 47 executable payload fragments. It is the exact list behind
the candidate test. It is not a complete reconciliation to the prior Action Coverage population
because Plague of Vermin is absent.

## Direct token-transaction findings

Independent in-memory probes, separate from the candidate tests, confirmed:

- three tokens received three fresh deterministic IDs;
- a token created under player 1's control had owner 1 and controller 1;
- `tapped` was preserved for all tokens in a tapped batch;
- a derived Ninja token retained `Creature — Ninja`, black color, 1/1 printed P/T, and flying;
- all creature tokens were initially summoning sick and became legal attackers on a later controller
  turn;
- two +1/+1 counters plus a temporary +3/-1 modifier evaluated from 1/1 to 6/2, then cleanup
  removed only the temporary modifier and left a persistent 3/3 token;
- cleanup did not remove a battlefield token;
- a fabricated equal-valued token was rejected;
- a token that moved to a nonbattlefield zone could not move again before the SBA boundary;
- the nonbattlefield incarnation ceased at the SBA boundary and post-cessation references were
  rejected;
- an invalid creature-token definition caused no state change and consumed no object identity;
- duplicate seeded creation produced equal snapshots and event ledgers without consuming new RNG;
- one typed `tokens_created` event represented the batch and three typed `creature_entered` events
  represented its members.

The candidate's 18 dedicated tests cover these same areas and execute all 47 bounded payloads.

## Predefined artifact-token boundary

Food, Mutagen, Treasure, and Clue definitions carry authoritative type and rules text, but their
activated abilities are not represented as legal engine options. Independent probes created each
token and confirmed:

- `retained_limitation == token_activated_ability_not_implemented`;
- no legal main action referenced the token object;
- no token was tapped or sacrificed;
- no card was drawn, mana produced, counter placed, or life gained;
- life remained 20 and graveyards remained empty.

Creation therefore does not itself implement activation or sacrifice. The limitation must remain
attached to every applicable coverage record.

## Excluded semantic-family audit

| Excluded family | Authoritative exposure | Candidate result |
| --- | ---: | --- |
| Token copies | 9 objects / 10 fragments | Non-executable; `token_copy_not_implemented` |
| Variable quantities | 8 / 8 | Non-executable; `variable_token_quantity_not_implemented` |
| Replacement effects | 1 / 1 | Non-executable; `token_replacement_effect_not_implemented` |
| Tapped-and-attacking context | 1 / 1 | Non-executable; `token_attacking_context_not_implemented` |
| Attach/follow-up | Wooden Cane; Foot Chopper | Creation payload executable; follow-up limitation retained |
| Delayed destruction and granted haste | Old Hob, Alleycat Blues | Creation payload executable; follow-up limitation retained |
| Food/Mutagen/Treasure/Clue activation | 26 fragments | Creation payload executable; activation limitation retained |

The copy set is Here Comes a New Hero!, Shredder, Shadow Master, Tempestra, Roadkill Rodney,
Endless Foot Assault, Chrome Dome, Donatello, Gadget Master, Improvised Arsenal, and both chapters
of The Cloning of Shredder. The variable set is Shellshock, Big Mother Mouser, Big Apple, 3 a.m.,
Endless Foot Assault, Mutagen Man, The Ooze, Sally Pride, and Triceraton Commander. Doubling Season
is the replacement object. The Last Ronin's Technique is the tapped-and-attacking object.

Intrinsic token keywords derived as part of fixed characteristics are distinct from Old Hob's
temporary granted haste. Old Hob's haste and delayed destruction are not executed. No excluded
family above was accidentally executed by the token transaction.

## Silent whole-fragment overclaim

The following 18 executable payload fragments have no retained limitation and are removed from
unsupported reporting as though the full fragment were represented:

1. Waste Not — opponent discards a creature card trigger;
2. Rat King, Pale Piper — nontoken creature leaves trigger;
3. Biogenic Ooze — creature ETB trigger;
4. Biogenic Ooze — activated token creation;
5. Jennika, Bad Apple Big Sister — self ETB trigger;
6. Ravenous Robots — artifact-spell-cast trigger;
7. Slash, Reptile Rampager — attack trigger;
8. Baxter Stockman — self ETB trigger;
9. Dark Leo & Shredder — combat-damage trigger plus conditional life loss;
10. Mechanized Ninja Cavalry — self ETB trigger;
11. Turtle Blimp — Vehicle ETB trigger;
12. Mighty Mutanimals — self ETB trigger;
13. Rat King, Verminister — conditional end-step trigger plus counter placement;
14. Uneasy Alliance — activated cost, exile effect, and sorcery restriction;
15. Foot Mystic — conditional ETB trigger;
16. Lord Dregg, Insect Invader — conditional end-step trigger;
17. Mouser Attack! — modal spell choice/delivery;
18. Mouser Foundry — artifact enter-or-leave trigger.

Some represented self-ETB and attack shapes have genuine delivery support. The list remains unsafe
as a whole because the interpreter does not distinguish those supported wrappers from the many
unrepresented ones before suppressing unsupported telemetry. Numeric payload coverage can remain;
whole-fragment coverage cannot.

## Card-name and special-case audit

No source-card-name dispatch was found in the Create Token implementation. Recognition uses Oracle
fragment patterns, quantities, characteristics, and the generic Food, Mutagen, Treasure, and Clue
token definitions. A renamed synthetic ETB source produced tokens through the same trigger path.
The existing generic Alliance modal path can invoke an executable token program without testing
Lita's name. No roster, deck, seed, or Acceptance Match name appears in the Create Token source.

The four predefined token-type names are legitimate token-definition facts, not source-card
dispatch. Their use semantics remain unsupported as described above.

## Preserved UNKNOWN classifications

Create Token supplies no new evidence to resolve the seven pre-existing context-sensitive UNKNOWN
Oracle objects:

- Command Tower;
- Arcane Signet;
- Exotic Orchard;
- Chromatic Lantern;
- Fast Forward;
- Double Jump // Flying Kick;
- Plague of Vermin.

The first four still need commander/opponent color context, Fast Forward still needs multiplayer
goad routing, Double Jump // Flying Kick still needs split/Fuse casting semantics, and Plague of
Vermin still needs iterative turn-order life bidding. Recognition of Plague of Vermin's eventual
token payload would not implement its choice and life-payment protocol. The candidate currently
fails even to recognize that payload because the Oracle grammar uses “creates” rather than
“create”; this supplies no reason to reclassify the object and is instead a recognition blocker.

## Acceptance Match #001

Each seed was executed twice. Duplicate rendered snapshots were byte-equivalent.

| Seed | Winner / turn | Unsupported events / exact pairs | Block rejections | Invariant violations | Token transactions |
| ---: | --- | ---: | ---: | ---: | ---: |
| 7001 | Raphael / 16 | 14 / 13 | 0 | 0 | 0 |
| 7002 | Leonardo / 17 | 14 / 8 | 2 | 0 | 0 |
| 7003 | Leonardo / 17 | 19 / 13 | 0 | 0 | 0 |
| 7004 | Leonardo / 21 | 21 / 18 | 1 | 0 | 0 |
| 7005 | Raphael / 16 | 13 / 8 | 3 | 0 | 0 |
| **Aggregate** | expected trajectories | **81 / 23** | **6** | **0** | **0** |

Zero acceptance token transactions is an observed execution fact, not a failure of deterministic
replay. The acceptance pilot did not choose Lita's Food mode. The Food fragment remains unsupported
because the token's activation is intentionally outside this Action.

## Validation

- full suite: **197 passed / 1 skipped**;
- dedicated Create Token tests: **18 passed**;
- authoritative card-data integrity tests: **5 passed**;
- Ruff format check: passed, 33 files already formatted;
- Ruff check: passed;
- `git diff --check`: passed before this report was added;
- deterministic acceptance duplicate replay: passed for all five seeds;
- acceptance aggregate: 81 unsupported events / 23 exact pairs, six block rejections, zero
  invariant violations, zero token transactions.

The successful validation establishes that the defect is a semantic coverage/reporting blocker,
not a general runtime regression. The implementation and tests remain uncommitted for correction
and review.
