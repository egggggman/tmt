# Baxter's Mutant Menagerie — exploratory 0.1

Status: DRAFT / NOT STRUCTURALLY VALIDATED / NOT SIMULATED. Separate eleventh candidate; does not alter Baseline 005.

## Main deck (60)

### Creatures (22)
4 Mouser Mark III
4 Ravenous Robots
4 Buzz Bots
3 Purple Dragon Punks
3 Baxter Stockman
2 Stockman, Mad Fly-entist
2 Rock Soldiers

### Noncreature spells (15)
4 Mouser Foundry
4 Mouser Attack!
3 Sewer-veillance Cam
2 Negate
2 Return to the Sewers

### Lands (23)
12 Island
11 Mountain

## Design intent
Blue-red Robot-token tempo/midrange. Early artifact creatures and token creation turn on Ravenous Robots and Baxter's combat buff; Buzz Bots provide flying/card replacement. Foundry and Return to the Sewers provide interaction. Basic-only mana base is intentionally provisional; investigate dual-land options after structural validation.

## Verification and test gates
- Card names, mana costs, Oracle text, Standard legality and color identity require authoritative Scryfall snapshot validation, including the current date.
- Check card counts and the full mana curve; assess 23-land/5-mana Baxter reliability, interaction and curve.
- Audit simulator coverage for triggered artifact casting/token creation, beginning-of-combat targeted buff, first strike/vigilance, death draw, haste-grant activated ability, enters/leaves triggers, sacrifice and modal instant actions, and Islandcycling.
- No win-rate claims; no Cardcade simulation until engine readiness and independent validation.
- Compare with Donatello, Krang, Shredder, and Bebop & Rocksteady using consistent baseline/runtime.

## Evidence
https://mtg.wtf/card/tmt/139/Baxter-Stockman
https://mtg.wtf/card/tmt/96/Mouser-Foundry
https://mtg.wtf/card/tmt/159/Mouser-Mark-III
https://mtg.wtf/card/tmt/32/Buzz-Bots
https://mtg.wtf/card/tmt/95/Mouser-Attack

Related issue: #360.
