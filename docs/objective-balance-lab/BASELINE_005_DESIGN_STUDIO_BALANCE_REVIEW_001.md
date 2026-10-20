# Design Studio Review — Baseline 005 Control Attempt 9

## Decision

**Control interpretation: READY.** Attempt 9 is the first complete authenticated Baseline 005 control and is suitable for Design Studio balance interpretation.

**Design action: recommendations only.** No deck list, runtime, baseline, or control artifact is changed by this review. No additional simulation or promotion is authorized here.

Control: `OBL-BASELINE-005-LTB-REPAIR-CONTROL-ATTEMPT-009`  
Runtime: `defefdce8a716ceef6dcedad1a6f50e2abc367bd3cb772a369853506d2f5398d`  
Schedule SHA-256: `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`  
Artifact SHA-256: `55a1f0074e5c61548744ed78421ade014ea04627ac01a6f772dfce5daad19c09`

The run completed 4,500/4,500 games across 45 cells, with zero runtime errors, one preserved draw, and six deterministic replay cells matching. The ten frozen deck identities and 172-row ledger were unchanged. Earlier failed controls and diagnostics remain excluded.

## Observed balance

| Deck | Wins / 900 | Win rate | Wilson 95% interval |
| --- | ---: | ---: | ---: |
| Leonardo | 429 | 47.67% | 44.42–50.93% |
| Raphael | 555 | 61.67% | 58.45–64.79% |
| Donatello | 521 | 57.89% | 54.64–61.07% |
| Michelangelo | 453 | 50.33% | 47.07–53.59% |
| Splinter | 608 | 67.56% | 64.43–70.53% |
| Shredder | 329 | 36.56% | 33.47–39.75% |
| Krang | 433 | 48.11% | 44.86–51.38% |
| Bebop & Rocksteady | 316 | 35.11% | 32.06–38.29% |
| April O'Neil | 325 | 36.11% | 33.04–39.30% |
| Casey Jones | 530 | 58.89% | 55.64–62.06% |

The first player won 2,594/4,500 games (57.64%); each deck started 450 games. Mean ending turn was 19.82, median 18, range 9–71. The largest observed cells were:

- Splinter over Bebop & Rocksteady, 84–16.
- Splinter over April, 82–18.
- Raphael over April, 80–20.
- Donatello over Shredder, 77–23.
- Casey over April, 74–26.
- Leonardo over April, 71–29.
- Raphael over Bebop & Rocksteady, 71–29.

Stable comparison points are Michelangelo (50.33%), Leonardo (47.67%), and Krang (48.11%); their aggregate rates do not prove that every matchup is balanced, but they provide useful controls for future isolated tests.

Execution telemetry records 87,966 casts, 205,729 activation events, 4,984 aura events, and 942 ETB life-gain events. These are exposure measures, not effectiveness measures. The AcceptancePilot is deterministic but is not human-play quality evidence.

## Interpretation: observation versus hypothesis

### Splinter — highest-priority pressure reduction

**Observed:** 67.56% aggregate, with wins over B&R 84%, April 82%, Shredder 75%, Krang 67%, Leonardo 66%, Donatello 62%, Michelangelo 63%, and Casey 61%. The deck is also only 48% against Raphael, so this is not universal dominance.

**Hypothesis:** Splinter's tribal board development and recursive/value package may be converting early creature presence into too much pressure against decks with weaker interaction. The matrix does not identify which individual card causes that effect; mechanic-use counts cannot establish it.

**Smallest proposed isolated test:** `−1 Splinter, Hamato Yoshi / +1 Stomped by the Foot`. This reduces one copy of the deck's central tribal engine while preserving a printed-theme interaction card already present at three copies. This is a hypothesis probe, not an authorized change.

**Expected effect:** modestly reduce Splinter's extreme wins, especially against B&R, April, and Shredder, while preserving the deck's creature/tribal identity.

**Risk:** could overcorrect the Splinter–Raphael and Splinter–Casey cells, where Splinter is only 52% and 61%, respectively; replacing a creature with interaction may also increase polarization elsewhere.

**Validation:** isolated 900-game Splinter substitution, same schedule/control runtime, with Raphael and Casey as sentinels and B&R/April/Shredder as primary diagnostics. Require aggregate and cell-level distribution review, not aggregate win rate alone.

### Bebop & Rocksteady — lowest aggregate and severe pressure losses

**Observed:** 35.11% aggregate. It loses to Raphael 29%, Shredder 43% (the matrix reports Shredder 57%), Splinter 16%, Casey 29%, Leonardo 37%, and Krang 34%; it is near functional only against April (45–55) and Donatello (41–59). Its interaction-cast count is the lowest of the ten decks (4,435), but that count is not proof of a causal interaction deficit.

**Hypothesis:** the deck may be failing to convert early creature development into resilient interaction against removal- and tempo-heavy opponents. This is consistent with the cell pattern, but the control does not isolate whether the cause is card quality, curve, pilot selection, or matchup-specific answers.

**Smallest proposed isolated test:** `−1 Frog Butler / +1 Stomped by the Foot`. The substitution increases the existing generic interaction package by one copy without changing lands or the promoted Primordial Pachyderm package.

**Expected effect:** improve survival and tempo in Raphael, Shredder, Splinter, and Casey cells, with the largest expected gain in the 16–29% cells.

**Risk:** could reduce creature density and worsen the already near-balanced April and Donatello cells; it may also be a pilot-policy rather than deck-power problem.

**Validation:** isolated 900-game test; primary cells Raphael, Shredder, Splinter, Casey; sentinels April and Donatello. Capture early board, interaction timing, unused mana, and whether Stomped is selected when legal.

### Shredder — weak aggregate despite strong matchup variance

**Observed:** 36.56% aggregate. It loses heavily to Donatello (23%), Splinter (25%), Raphael (33%), Casey (34%), and Leonardo (38%), while beating April (71%) and losing narrowly to B&R only when orientation is aggregated (Shredder 57%). This is a matchup-specific profile, not a simple global weakness.

**Hypothesis:** Shredder may need one more broadly useful answer or resilience piece against artifact/tribal development; the high interaction-cast count (6,624) indicates activity, not successful timing or target quality.

**Smallest proposed isolated test:** `−1 Shredder's Technique / +1 Anchovy & Banana Pizza`. Both are already in the frozen list; this shifts one slot toward a concrete creature-removal ETB effect while preserving the deck's removal identity.

**Expected effect:** improve Donatello, Splinter, Casey, and Raphael cells where opposing creatures appear to outlast or outscale Shredder's current answers.

**Risk:** may weaken the favorable April cell or reduce the deck's combat/tempo profile; ETB timing can be slower than an instant-speed answer.

**Validation:** isolated 900-game test with Donatello, Splinter, Casey, and Raphael primary; April and B&R sentinels. Record target legality, cast timing, removal resolution, and whether the card is naturally selected.

### April O'Neil — diagnostic before intervention

**Observed:** 36.11% aggregate, with severe losses to Raphael (20%), Splinter (18%), Casey (26%), Donatello (27%), Shredder (29%), and Leonardo (29%). April is near or above parity only against B&R (55%) and is below parity against every other deck.

**Hypothesis:** this may reflect a compound problem (pilot hand deployment, interaction timing, or curve) rather than one missing card. The control's mechanic telemetry cannot distinguish these causes.

**Recommendation:** do not make a card change in this review. Run a narrowly scoped April diagnostic first, measuring legal optional hand deployments, interaction opportunities, land/resource use, and early board presence. A card substitution should follow only if that diagnostic identifies a specific bottleneck.

### Raphael and Casey — monitor, do not weaken yet

Raphael is 61.67%, but it is 49% against Michelangelo and 52% against Splinter; its strongest pressure is concentrated against April (80%) and B&R (71%). Casey is 58.89%, with 74% over April and 71% over B&R, but 37% against Raphael and 39% against Splinter. These are not sufficient grounds for autonomous weakening. They are sentinels for isolated tests.

## Priority order

1. Splinter one-slot pressure-reduction probe.
2. B&R one-slot interaction-density probe.
3. Shredder one-slot removal/resilience probe.
4. April pilot/interaction diagnostic before any deck change.
5. Raphael and Casey monitoring as sentinels, not immediate nerf targets.
6. Preserve Leonardo, Michelangelo, and Krang as comparison anchors.

Each proposed substitution requires its own isolated validation and a fresh Design Studio decision. No combined validation is proposed.

## Evidence boundary and HQ request

This review makes no claim that any proposed card is causally responsible for the observed matrix. It uses the authenticated control only to prioritize hypotheses. The next authorized action, if HQ agrees, is **one** isolated hypothesis test beginning with the Splinter probe; otherwise the review remains interpretive only.

Baseline 005 remains frozen and historical evidence remains untouched.
