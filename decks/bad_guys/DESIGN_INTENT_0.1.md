# Bad Guys — Design Intent and Prototype 0.1 Review

Status: SANDBOX / NOT APPROVED FOR SIMULATION OR BASELINE PROMOTION.
Authority: HQ directive and GitHub Issue #359.
Deck: `decks/bad_guys/PROTOTYPE_0.1.txt`; Baseline 005 and all Bebop & Rocksteady histories remain untouched.

## Identity
**Bad Guys — Shredder's Cronies**: expendable bodies, reckless attacks, Foot Clan assault, opportunistic removal and creature/token sacrifice. Bebop & Rocksteady remain the featured characters. Distinct from Shredder's own deck (leadership/control) and Krang's technology engine. Black-green is retained to isolate the thematic redesign from a simultaneous color change.

## Verified repository card data
Card names, mana values, Oracle text and snapshot Standard legality checked against `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` (historical snapshot; live 2026-10-21 legality still needs separate confirmation). All 17 distinct listed cards resolve in the snapshot, are marked Standard-legal there, and comply with the four-copy rule. 60 cards: 20 lands (10 Swamp, 10 Forest), 40 nonlands. Hybrid W/B Foot Elite and Foot Ninjas can be paid using black; B/R Tokka & Rahzar using black; B/G Bebop & Rocksteady using black or green.

## Major choices and hypotheses
- **4 Bebop & Rocksteady, 2 Bebop, Warthog Warrior, 2 Rocksteady, Crash Courser:** preserve the featured duo, boar/rhino support, and the historical deck's signature. Bebop & Rocksteady's attack/block discard-or-sacrifice tax is an actual cost to manage.
- **4 Foot Elite:** attacking another creature grants +1/+0 and indestructible, potentially improving combat survival. This is the key *new* Foot pressure test.
- **4 Foot Mystic:** lifelink plus a Disappear Ninja token when a permanent left the battlefield earlier in the turn; creates a link between sacrifice and replenishment but the 4-mana cost is a concern.
- **2 Foot Ninjas:** high-cost Sneak threat with ETB life gain; thematic Foot presence, but may worsen curve or exceed current pilot semantics.
- **3 Tokka & Rahzar, Terrible Twos:** cheap menace pressure, and punishment for discounted spells; confirm Shredder-alignment in Canon before treating them as core henchmen.
- **4 Zoo Escapees, 2 Ice Cream Kitty, 2 Putrid Pals:** retained creature/resource support; Kitty converts expendable creatures/tokens into cards, Zoo Escapees leave Mutagen, Putrid Pals rewards a prior permanent leaving. These are mechanically coherent but are not independently established as Shredder's cronies; treat as provisional supporting roles.
- **1 Super Shredder:** menace plus counter growth when permanents leave, a low-copy thematic bridge. If this duplicates Shredder's own deck identity, replace after review.
- **3 Stomped by the Foot, 3 Tainted Treats:** cheap interaction; Stomped's sacrifice kicker potentially activates leave-the-battlefield payoffs; Tainted Treats answers artifacts or creatures.
- **2 Shredder's Armor:** equipment grants +2/+1 and has an equip cost involving sacrifice, another possible expendable-resource outlet; verify pilot/equipment semantic coverage.
- **2 Mutant Chain Reaction:** situational artifact/enchantment/flying-creature removal that also makes Mutagen; not generic creature removal.

## Changes vs Baseline 005
New package: +4 Foot Elite, +4 Foot Mystic, +2 Foot Ninjas, +3 Tokka & Rahzar, +1 Super Shredder, +2 Shredder's Armor.
Reduced/removed: -2 Mutagen Man, -2 Frog Butler, -2 Ice Cream Kitty, -3 Putrid Pals, -2 Paramecia Coloniex, -3 Cowabunga!, -1 Mutant Chain Reaction, -2 Illegitimate Business, -2 Primordial Pachyderm. Recheck the exact arithmetic mechanically before any runner preflight; this section is a design summary, not an authenticated candidate diff.

## Risks and limitations
1. Historical Attempt 9 B&R results: 35.11% aggregate, vs Splinter 16%, Casey 29%, Raphael 29%. R9-B candidate: 35.89%, vs Splinter 17%, Casey 28%, Raphael 31%. Original Attempt 9 raw control artifact remains unavailable; use only the preserved report with its limitation stated.
2. Foot Mystic (4 MV), Foot Ninjas (6 MV), Bebop Warrior (5 MV), Rocksteady (6 MV) could make 20 lands inadequate. Cycling helps some cards but is not equivalent to land count. Curve and mulligan/land-miss diagnostics are required.
3. Canon alignment of Tokka & Rahzar, Zoo Escapees, Kitty, Putrid Pals and Foot Mystic needs confirmation; mechanical fit is not proof of allegiance.
4. New card abilities (Sneak, attack-triggered indestructible, sacrifice equip, Disappear, triggered token generation) may not be fully supported by the current Cardcade runtime/pilot. Do not interpret simulations until Oracle/action coverage is checked.
5. Historical snapshot legality does not guarantee live legality. Reconfirm immediately before simulation.

## Smallest useful Cardcade gate
First run **structural and semantic preflight only**, not a 900-game simulation: validate deck hash and exact diff, live Standard legality, color/mana source feasibility, Oracle action coverage, and deterministic fixtures for Foot Elite attack trigger, Foot Mystic Disappear, Foot Ninjas Sneak, Shredder's Armor sacrifice-equip, and Tokka & Rahzar discounted-spell trigger. Audit pilot action selection. Report READY/BLOCKED and coverage deltas. Only then ask HQ to authorize a small deterministic smoke test; 900-game isolation remains a later, separate decision.

## HQ decision needed after preflight
Decide whether this candidate's theme and risks justify continuing; do not promote it, replace the frozen roster slot in official baseline, or run games automatically.
