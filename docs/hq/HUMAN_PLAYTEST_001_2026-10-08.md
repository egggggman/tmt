# Human Playtest 001 — Original Notes and Initial Handoff

Status: three human physical games reported; **qualitative evidence, not calibrated win rates**.
Source: player notes submitted 2026-10-08. Spelling and original phrasing retained in raw section.
Deck identity: frozen Human Game Day Candidate 0.1 / Baseline 005. Five exact-card proxies had been reported; whether they appeared in these games was not specified.

## Raw player notes (verbatim)

```text
game 1 
rahpael vs casey jones

issues pulling land after multiple mulligans
had to look up skateboard card and figure out haste and how to play the card
raphael won 1st round and going first
raphael was still at 11 health by the time casey jones deck died and there was overkill due to double strike
raphaels skateboards stopped me dead in my tracks
issues getting land in hand




important to have reference material to oracle effects
game 2
splinter vs michaelangelo

michaelangel went first
the final health count was -5 / 6 - overkill on last play to feel what was actually in play
game was tilted to the splinter side but 2 food tokens revived a low hp michaelangelo
this changed the outcome of the game


game 3
casey jones vs michaelangelo

casey jones went first
final health count was 8 / -4 - with casey jones winning
It was pretty neck and neck until casey jones was able to build up the team faster
it was a matter of 1 turn being the difference - if michaelangelo had another turn - he would have won



Did the game feel close? Why or why not?
Raphael was an outlier. The games were relatively close with maybe an extra turn being the determining factor
Did either player feel unable to meaningfully participate?
no
What was the most fun moment?
watching the strategy and learning the different strategies of the different decks. player engagement is good
What was frustrating, confusing, or slow?
dual color card confusion having to look up a few symantecs like artifact/artifact creature and sneak
Did each deck's identity come through?
michaelangelo was able to control the battlefield and take chances with rewards - but not a lot of michaelangelo cards presented themselves
splinter was clearly splinter
raphael was definitely raphael

Would you replay this exact matchup?
yes - raphael is broken but we left him out of the matchups
Any card or interaction that should be reviewed?

skateboard should be reviewed - got 3 in the draw which could have made the game one sided out out of the gate
some of the mulligans could be in part due to recently built decks and card clumps
```

## Structured extraction (without inventing missing details)

| Game | First player | Reported winner | Result / notes |
|---|---|---|---|
| Raphael vs Casey Jones | Raphael | Raphael | Raphael at 11 life; Casey defeated with double-strike overkill. Multiple mulligans and land difficulty; Skateboard and haste lookup; three Skateboards seen in draw (not explicitly identified as opening hand). |
| Splinter vs Michelangelo | Michelangelo | **Michelangelo (player-confirmed in follow-up)** | Notes say final life -5 / 6, with no explicit mapping to deck order; Splinter appeared ahead, but two Food tokens revived low-life Michelangelo and changed the outcome. **Winner confirmed as Michelangelo in a subsequent player clarification; original life notation remains unmapped.** |
| Casey Jones vs Michelangelo | Casey Jones | Casey Jones | Final life 8 / -4 in listed deck order; felt close, with potentially one decisive turn. |

Game lengths, mulligan counts, exact sequencing, card effects, and identity of players were not recorded.

## Cross-game observations

**Positive**
- No player reported being unable to meaningfully participate.
- Engagement and willingness to replay were positive.
- Distinct identities were evident for Raphael and Splinter; Michelangelo's battlefield control/risk-reward pattern appeared, although few named Michelangelo cards appeared.
- Food-token comeback and Casey/Michelangelo near finish are encouraging qualitative signals.

**Concerns**
- Raphael vs Casey felt distinctly one-sided; Skateboard and double strike merit a card-interaction/rules audit.
- Mana access and mulligans were frustrating; insufficient shuffle/card clumping was raised as a possibility, not a verified cause.
- Oracle/rules lookup interruptions included Skateboard, haste, artifacts vs artifact creatures, Sneak, and dual-color interpretation.
- Raphael was excluded from subsequent matchups due to perceived power. This creates selection bias in any later aggregate human win rate.

## Comparison with preserved Baseline 005 (descriptive only)

- Casey vs Raphael: Cardcade 37/63 (Casey/Raphael); the observed Raphael win is directionally consistent but one game cannot establish imbalance.
- Michelangelo vs Splinter: Cardcade 46/54 (Michelangelo/Splinter); the confirmed Michelangelo comeback is a plausible outcome, not a contradiction.
- Casey vs Michelangelo: Cardcade 57/43 (Casey/Michelangelo); observed Casey win directionally consistent; player report of close game is more valuable than the binary result alone.

## Department handoffs

### 🧪 Design Studio — interpretation only
1. Investigate whether Raphael's pressure is genuinely oppressive in human play, with focus on multiple Skateboards and double strike.
2. Avoid changing Raphael, Skateboard, land counts, or mulligan rules from one match.
3. Track Michelangelo's identity expression and frequency of signature character cards in later games.
4. Keep Baseline 005 and all historical prototypes unchanged.

### 🕹️ Cardcade — evidence/semantics audit
1. Check generic Skateboard, haste, double strike and relevant combat/equipment semantics against authoritative card text and rules.
2. Compare the observed Raphael/Casey pattern with preserved match evidence and any known pilot limitations.
3. Report evidence and hypotheses; do not redesign decks or run large batches on this report alone.

### 📦 Mr. Paperback — high-priority usability work
Prototype a one-page quick reference covering:
- where to find current Oracle text and what to do when a card is confusing;
- haste and summoning sickness;
- artifacts vs artifact creatures and equipment;
- Sneak;
- mana symbols, color identity vs mana costs as applicable to the specific observed confusion;
- double strike and combat-damage ordering;
- Food token activation.

Verify wording against actual card Oracle text and official Magic rules before printing. Physical legibility and use at the table are required for acceptance.

## Next gate

Game 2 winner confirmed as Michelangelo by the player after the initial report. Original raw notes and ambiguous final-life notation remain unchanged. No deck revision is authorized.

COWABUNGA.
