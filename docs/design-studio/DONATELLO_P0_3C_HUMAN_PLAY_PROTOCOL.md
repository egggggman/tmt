# Donatello Prototype 0.3c Human-Play Protocol

Status: **HUMAN PLAY WITH KNOWN IMBALANCE**

This is the active Design Studio gate for Donatello after the post-response
Cardcade smoke. It defines the smallest useful first physical playtest. It is
not a balance tournament and does not authorize a new prototype.

## Candidate and authority

Use **Donatello Prototype 0.3c** only. Do not substitute P0.3a or P0.3b and
do not change the list between games.

P0.3c differs from P0.3b by:

```text
-2 Sewer-veillance Cam
-2 Return to the Sewers
+3 Mouser Mark III
+1 Ooze Spill
```

The gate follows the post-response smoke artifact
[`PROTOTYPE_0_3C_POST_RESPONSE_SMOKE_RESULTS.md`](PROTOTYPE_0_3C_POST_RESPONSE_SMOKE_RESULTS.md),
whose decision was `P0_3C_RESPONSE_SUPPORT_VALIDATED` and whose human-play
assessment was `HUMAN_PLAY_WITH_KNOWN_IMBALANCE`.

## Simulator context for testers

The frozen P0.3c smoke was directional evidence only:

| Opponent | Donatello result |
| --- | ---: |
| Shredder | 10–30 |
| Raphael | 5–35 |
| Casey Jones | 11–29 |
| Aggregate | **26–94 (21.7%)** |

Historical aggregates were P0.3a `18–102`, P0.3b `15–105`, and P0.3c
`26–94`. These are not expected human win rates. Cardcade has already
represented and regression-tested Technique, Does Machines setup and level 2,
Way with Machines counters, Flying, Mouser hybrid mana and attack restriction,
Ooze hand-response countering, and Mutagen creation. Human choices remain the
important unknown.

## First session

Play **12 total games**, with no sideboards:

| Matchup | Games | Donatello starts | Opponent starts |
| --- | ---: | ---: | ---: |
| Donatello / Shredder | 4 | 2 | 2 |
| Donatello / Raphael | 4 | 2 | 2 |
| Donatello / Casey Jones | 4 | 2 | 2 |

Use the project's normal mulligan rules. Have the same human pilots swap decks
where practical, or rotate pilots so one person's skill or preferences do not
define the entire result. Record pilot names or initials when practical.

Do not tune, sideboard, or replace cards between games. Record games as played.

## Record after every game

Use the concise
[`DONATELLO_P0_3C_HUMAN_PLAY_RESULTS_TEMPLATE.md`](DONATELLO_P0_3C_HUMAN_PLAY_RESULTS_TEMPLATE.md).
Required factual fields are matchup, starting player, winner, ending turn,
Donatello mulligans, and opponent mulligans.

For Donatello, also record whether the following occurred:

- first meaningful creature/body and its turn;
- Mouser drawn, cast early, and used for a profitable block;
- Does Machines cast and reach level 2;
- leveling felt like a tempo loss at that moment;
- Ooze drawn, held with mana available, and used against a meaningful spell;
- Way with Machines attacked;
- Donatello ever felt stabilized.

“Early” means turns 2–5 for this first pass. If a fact is not observable or
the player cannot remember it, mark `unknown` rather than reconstructing it.

## Brief subjective questions

After each game, Donatello's pilot answers:

1. Fun, 1–5: **Was this deck fun to pilot?**
2. Agency, 1–5: **Did you feel like you had meaningful choices?**
3. Power: clearly too weak / somewhat weak / competitive / somewhat strong /
   clearly too strong.
4. Identity: strongly felt like Donatello / somewhat felt like Donatello /
   neutral / weak identity / wrong identity.
5. Main friction: too slow / not enough interaction / weak creatures / engine
   costs too much mana / cards stranded in hand / cannot close games / poor
   draws / opponent simply had stronger curve / no major problem / other.

Add one short free-text observation when useful; do not let note-taking
interrupt play.

## Focus questions

Pay particular attention to these human-versus-Pilot questions:

- Does a human deploy Mouser earlier than AcceptancePilot, and does the 2/3
  body stabilize turns 2–5?
- Does a human intentionally hold mana for Ooze, and does that create real
  defensive leverage?
- Did leveling Does Machines feel worth the mana at that moment?
- Does Way with Machines function as a closer, merely add incremental value,
  die before contributing, or create exciting artifact-engine turns?
- Do recovered artifacts create meaningful choices?
- Does the deck feel clever and identity-consistent, or mainly slow and
  frustrating?

## Post-session classification

After all 12 games, choose exactly one overall status:

- `P0_3C_HUMAN_DIRECTION_VALIDATED`
- `P0_3C_HUMAN_PROMISING_BUT_WEAK`
- `P0_3C_HUMAN_REVISION_REQUIRED`
- `P0_3C_HUMAN_INCONCLUSIVE`

Also choose exactly one primary ownership classification:

- `POWER`
- `FUN`
- `IDENTITY`
- `INTERACTION`
- `TEMPO`
- `CLOSING`
- `NO_CLEAR_PROBLEM`

The sample is too small for a balance claim. Do not select a revision merely
because Donatello loses games. A later P0.3d requires a repeatable human
observation, such as Mouser being good but too sparse, Does Machines costing
too much tempo, Ooze being valuable but too scarce, Way failing to close, a
specific underperforming card, or the deck not being fun.

## Gate boundary

Do not run another simulator smoke, modify Cardcade, alter P0.3c, or create
P0.3d as part of this protocol. Human evidence is the next decision input.
