# Cardcade — Bad Guys Prototype 0.1 repository preflight 001

Status: STRUCTURAL PASS / SEMANTIC GATE OPEN / NO SIMULATION AUTHORIZED.
Source: `decks/bad_guys/PROTOTYPE_0.1.txt` on `design/bad-guys-prototype-0-1`; comparison: frozen `docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt` on main.
Catalog: `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` on main. This is a repository snapshot, NOT an independently refreshed live Scryfall legality check.

## Structural results
- 60 cards; 20 basic lands (10 Swamp, 10 Forest); 30 creatures; 10 noncreature spells.
- All 17 distinct card names resolved against the repository snapshot. All marked Standard-legal in that snapshot; no more than four copies of a nonbasic card.
- Printed mana-value curve of 40 nonland cards: MV1=0, MV2=15, MV3=13, MV4=6, MV5=2, MV6=4. Mean printed nonland MV = 3.075. Six cards cost 5–6 mana, with only 20 lands. Cycling and Sneak can change effective casting cost; printed MV is not effective curve.
- Black-green mana feasibility: all hybrid symbols have black or green alternatives: B/G on Bebop & Rocksteady, Ice Cream Kitty and Putrid Pals; W/B on Foot Elite and Foot Ninjas; B/R on Tokka & Rahzar. No third-color source is required for the printed costs.
- Exact parent diff: 18 added and 18 removed copies across 17 changed card names. Frozen Baseline 005 was not modified.

## Risks requiring deterministic semantic checks
1. `Foot Elite`: attack trigger targets *another* friendly creature, granting +1/+0 and indestructible until EOT; verify trigger target, attack timing, protection and expiry.
2. `Foot Mystic`: Disappear checks whether a permanent left your battlefield earlier this turn, then creates a Ninja token when entering; verify ownership and turn-history attribution.
3. `Foot Ninjas`: Sneak alternative casting, returning an unblocked attacker during declare blockers, entering tapped/attacking, and ETB life gain; verify cost, timing and pilot selection.
4. `Shredder's Armor`: ETB attachment, +2/+1, and once-per-turn equip cost of sacrificing another nonland permanent; verify activation, targets and stat recomputation.
5. `Tokka & Rahzar, Terrible Twos`: trigger when mana spent on a spell is less than its mana value; verify comparison uses actual paid mana, not generic casting cost or printed MV alone.
6. `Bebop & Rocksteady`: mandatory discard or sacrifice when attacking/blocking; check whether the pilot recognizes both options and their relative costs.
7. `Tainted Treats` and `Stomped by the Foot`: verify targeting, kicker sacrifice, conditional effects, and associated leave-the-battlefield interactions.

## Code inspection (static only)
- `src/tmnt_design_studio/card_interpreter07.py` contains references to Sneak, Disappear, Equipment, indestructible and sacrifice.
- `src/tmnt_design_studio/pilot07.py` contains Sneak references, but static text matching does not prove action legality, complete semantics, or pilot quality.
- No deterministic fixtures or full repository test suite were executed in this checkpoint. Therefore engine readiness is **UNVERIFIED**, not failed.

## Design and evidence caveats
- No one-mana nonland play; 20 lands and six MV5+ cards raise an early development and castability hypothesis. Test land drops, mana spending, early attackers and high-cost cards stranded in hand before changing the deck.
- Historical B&R R9-B weak cells: Splinter 17%, Casey 28%, Raphael 31%. These are comparison targets, not forecasts for Bad Guys.
- The new package may create substantially more mechanically distinct branches than the one-card R9-B probe, but coverage improvement has not yet been measured.
- Canon check pending for supporting creatures whose Shredder affiliation is not self-evident.
- Current Standard legality must be rechecked against a live authoritative source before HQ authorizes gameplay validation.

## Next executable gate
Run repository structural validator and deterministic tests for the seven semantic groups above on an authenticated workspace; collect test names, results, runtime SHA, and failures. Resolve unsupported mechanics before smoke tests. Only then seek HQ authorization for the smallest smoke test, followed by isolation if warranted.

Preserve Baseline 005, all historical prototypes and R9-B evidence. No engine changes, candidate changes, baseline promotion, or simulation executed.
