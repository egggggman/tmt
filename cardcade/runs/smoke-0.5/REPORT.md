# Cardcade Prototype 0.2 Smoke Report

Status: **completed — credible diagnostic result; recalibration blocked**

## Protocol

- Engine `cardcade-0.4.0`; seed `20260809`
- Prototype 0.2 roster hash `ee0c1df6c45388d994b1f5e0dac5346a20078e36e588f18211aafb490ab5fc3b`
- 20 games per pairing; 45 pairings; 900 games; exactly 10 starts for each deck per pairing
- Donatello and Krang use Prototype 0.2; the other eight lists remain Prototype 0.1
- Structural validation: ten 60-card decks; changed cards reuse Standard-legal cards already
  accepted in structurally valid Prototype 0.1 lists

Cardcade is a heuristic rehearsal, not a Magic rules engine. It reports observations and
hypotheses; it does not authorize deck changes.

## Aggregate comparison

| Deck | Calibration 0.1 | Smoke 0.5 | Change |
|---|---:|---:|---:|
| Donatello | 63.2% | 66.7% | +3.4 pp |
| Krang | 63.7% | 62.8% | -0.9 pp |
| Raphael | 52.6% | 52.8% | +0.2 pp |
| April O'Neil | 45.6% | 47.2% | +1.7 pp |
| Casey Jones | 45.3% | 47.2% | +1.9 pp |
| Bebop & Rocksteady | 47.0% | 47.2% | +0.2 pp |
| Splinter | 44.3% | 46.7% | +2.3 pp |
| Shredder | 50.3% | 46.1% | -4.2 pp |
| Michelangelo | 45.1% | 44.4% | -0.7 pp |
| Leonardo | 42.9% | 38.9% | -4.0 pp |

The first player won 52.8%, close to Calibration 0.1's 52.2%. With only 20 games per matchup,
small movements are directional rather than calibration-strength evidence.

## Hypothesis results

### Donatello

Full execution fell from 92.0% to 83.9%, payoff realization from 93.8% to 85.0%, and realized
payoffs from 2.77 to 2.00 per game. Setup remained 98.3%, preserving the invention identity.
Aggregate strength did not contract in this sample, and Donatello remained 75% over Michelangelo,
75% over April, and 85% over Shredder. The reliability hypothesis is supported, but the balance
hypothesis is unresolved.

### Krang

Full execution fell from 82.1% to 58.9%, payoff realization to 58.9%, affinity discount frequency
to 40.0%, and affinity mana saved from 2.42 to 1.89 per game. Setup remained 100% and artifacts cast
rose to 6.16 per game, preserving infrastructure. Aggregate strength remained 62.8%, with Krang 85%
over Casey, 70% over Leonardo, and 70% over Shredder. The result suggests Cardcade's broad Krang
strength is not sufficiently explained by namesake frequency, recovery, or affinity execution.

### Watchlists and polarity

Eleven pairings finished outside 35–65%. Seven involve Donatello or Krang. The remaining four are
Leonardo–April (30–70), Leonardo–Shredder (20–80), Splinter–Casey (30–70), and Splinter–Shredder
(75–25). Leonardo fell to 38.9%, so no buff is authorized from this smoke. Splinter rose to 46.7%
without a change, supporting continued observation rather than an immediate buff.

Bebop & Rocksteady again flooded at 38.3%, closely reproducing Calibration 0.1's 37.0%. The model
defines flood coarsely as seven lands by turn eight and does not model all cycling or mana-sink
decisions. Keep the deck unchanged and prioritize human telemetry. Shredder remains unchanged; its
46.1% smoke result does not reverse the much larger 50.3% calibration result.

## Decision

Smoke 0.5 is structurally valid, reproducible, start-balanced, and diagnostically credible. It is
**not a promotion pass**: Donatello and Krang remain above target with substantial polarity, and
Krang's strength persists despite large reductions in modeled engine execution. Do not run a
100-game Prototype 0.2 calibration yet. Design Studio should combine human games with a review of
the fixed deck-profile strength assumptions before deciding whether another card revision is
warranted. No further deck change is authorized by Cardcade.
