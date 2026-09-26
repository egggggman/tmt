# Shredder Prototype 0.3 Candidate Packet

Status: **CANDIDATE ANALYSIS ONLY — NO DECKLIST AUTHORIZED**

Final recommendation: **GATHER_HUMAN_EVIDENCE_FIRST**

## Authorization and evidence chain

This packet is permitted by the merged limited authorization:

- Authorization: `docs/design-studio/PROTOTYPE_0_3_LIMITED_AUTHORIZATION.md`
- Decision: `AUTHORIZE_LIMITED_DECKS_ONLY`
- Authorized deck: Shredder
- Calibration review: `docs/design-studio/CALIBRATION_V1_PROTOTYPE_0_3_REVIEW.md`
- Calibration run: `CALIBRATION_V1_20260923T141649Z_3f838930291e`
- Completion state: `AUDIT_PASS`
- Banked completion-audit SHA-256: `D202D3B35814E2B67CF2959E73282264CD8AC2B93EA877FB8C8970D1D48616BE`
- Corrected analysis: `docs/cardcade/CALIBRATION_V1_20260923T141649Z_3f838930291e/CALIBRATION_ANALYSIS_V1.json` and `.md`
- Analysis JSON Git-blob SHA-256: `EC409344E0BDB23C754106DAFB2DF6B828BCDEA0476999CD44357E12499131EE`
- Analysis Markdown Git-blob SHA-256: `96EEC193CF7AE8E9AEC908F2B5879C399A032B087989F0FCCDCC074BEE7CB1C0`
- Preserved baseline: `decks/shredder/PROTOTYPE_0.1.txt` and `.md`
- Playtest record: `decks/shredder/PLAYTEST_LOG.md`

No production evidence, engine/runtime/Pilot code, or preserved deck file was changed.
This packet does not create `PROTOTYPE_0.3` and does not authorize a card swap.

## Current prototype identity

Shredder is a ruthless, pressure-oriented mono-black deck. Its intended identity is to
deploy evasive Foot soldiers, sacrifice expendable permanents, remove resistance, and
let central threats grow from permanents leaving the battlefield. It must remain
villainous, sacrifice/removal driven, and distinct from Splinter rather than becoming
generic midrange.

The preserved list is 60 cards: 24 creatures, 14 noncreatures, and 22 Swamps. Its
baseline analysis reports average nonland mana value 2.66, targeted removal 5 copies
across 2 cards, evasion 8, sacrifice support 3, interaction density 13.2%, and threat
density 63.2%.

## Named problem

**Shredder generates broad matchup pressure with too little recoverable counterplay under
the represented game model.**

This is narrower than “Shredder is too strong.” It identifies a repeatable environment
problem while preserving uncertainty about whether the cause is threat redundancy,
removal density, Super Shredder growth, AcceptancePilot policy, unsupported opponent
defense, or an interaction among them.

Ownership: the Calibration review classifies this as `DECK_REVISION_EVIDENCE_CREDIBLE`,
with a primary deck/balance hypothesis and retained Pilot/semantic caveats. The packet
does not claim that every observed point is deck-owned.

## Calibration V1 evidence

Shredder completed 36,864 games: 27,845 wins and 9,019 losses, for a 75.53% win rate
(approximately 75.09%–75.97% Wilson 95% CI). It exceeded 55% in 8 of 9 matchups, was
45–55% in 1, and was below 45% in 0. This breadth is stronger evidence than a single
polarized pairing.

The complete matchup observations are:

| Opponent | Shredder win rate |
|---|---:|
| Leonardo | 70.51% |
| Raphael | 52.76% |
| Donatello | 87.16% |
| Michelangelo | 73.14% |
| Splinter | 70.39% |
| Krang | 89.92% |
| Bebop & Rocksteady | 82.10% |
| April O’Neil | 91.11% |
| Casey Jones | 62.72% |

The aggregate result is not a seat-orientation artifact finding. The corrected overall
first-player rate was 50.64%; the canonical/reversed aggregate difference is explicitly
`DECK-IDENTITY CONFOUNDED — NOT A SEAT-EFFECT ESTIMATE`.

## Matchup structure

Raphael is the near-balanced matchup at 52.76%. Both decks present early pressure,
combat-centric decisions, and a similar demand for immediate board interaction. The
result is consistent with pressure meeting pressure and does not isolate one Shredder
mechanic as the cause.

Casey at 62.72% is materially better for Shredder but not an extreme result. Casey’s
artifact/equipment plan can contest the board, while its sequencing and attachment
boundaries may reduce reliable recovery. This is a useful counterplay pairing, not proof
that removal alone is oppressive.

The other seven matchups are heavily Shredder-favored: 70.39%–91.11%. The breadth across
artifact, tempo, creature, and value-oriented opponents argues for a combined pressure
profile—early threats plus evasion, removal, and departure payoffs—rather than a single
isolated mechanic. Opponent-side unsupported defenses and AcceptancePilot behavior remain
alternative explanations that human play must test.

## Deck-specific semantic inventory

“Full” means the named role is represented for the bounded execution surface, not that
every Oracle clause on the card is implemented. “Partial” records material boundaries.
No numerical correction factor is inferred.

| Card / copies | Intended role | Cardcade role coverage | Material boundary | Pilot interaction | Simulated bias direction |
|---|---|---|---|---|---|
| Dream Beavers / 4 | Cheap evasive pressure, ETB life swing and Scry | Partial | Compound ETB delivery; Scry child is supported, but the full compound fragment is bounded | Low-cost creature policy can deploy it readily | Direction unknown; early pressure may be represented while compound value may be understated |
| Squirrelanoids / 4 | Early evasive Foot-soldier pressure | Full for ordinary creature/evasion/combat surface | No separate card-specific reached limitation is established in the reviewed evidence | Maximum-attacker policy directly rewards wide evasive attacks | Potentially overstated if all-out attack policy is stronger than human play |
| Super Shredder / 4 | Central departure-payoff threat and snowball engine | Partial-to-strong | Permanent-departure counter path is supported; broader sequencing and every supporting departure are not a complete causal model | Cheap-creature and maximum-attack policies can create more departure opportunities | Direction unknown; runaway risk is credible but not isolated |
| Oroku Saki, Shredder Rising / 3 | Early threat and Sneak/pressure development | Partial | Bounded Sneak exists; full card-specific interactions remain dependency-limited | Low-cost creature sequencing favors access to early board presence | Likely overstated only if human pilots use less aggressive sequencing; otherwise unknown |
| Foot Mystic / 3 | Evasive/lifelink pressure and Disappear setup | Partial | Lifelink and bounded combat are represented; Disappear/token delivery remains unsupported | Maximum attacks may expose lifelink pressure without modeling all setup choices | Direction unknown |
| Shark Shredder, Killer Clone / 3 | High-end evasive finisher, Double Strike, Sneak payoff | Partial | Intrinsic Double Strike and bounded Sneak are supported; graveyard theft/entered-attacking compound semantics are bounded | Pilot can select the first legal Sneak and attack broadly | Finisher contribution may be understated or distorted; direction unknown |
| Shredder, Unrelenting / 3 | Threat plus temporary deathtouch support | Partial | ETB/attack target/deathtouch path is supported only with high dependency; broader target/priority sequencing is bounded | Supplied legal target choices and aggressive attacks favor visible use | Direction unknown |
| Shredder’s Armor / 4 | Equipment-like sacrifice-to-weaponize engine | Partial / not meaningfully complete | Attachments, Equipment activation, and attachment lifecycle are unsupported boundaries | Pilot cannot exercise the intended attachment decision surface fully | Likely understated for the intended strategic role |
| Stomped by the Foot / 3 | Removal plus expendable-permanent pressure | Partial | Ordinary removal/combat surfaces are represented; compound sacrifice/departure sequencing is not fully isolated | AcceptancePilot uses supplied removal opportunities and aggressive follow-up | Could be overstated if removal is easier to access than in human play; unknown |
| Shredder’s Technique / 3 | Removal, pressure conversion, and sacrifice value | Partial | Card-specific compound semantics and priority windows are bounded | Visible legal casts are chosen deterministically, not strategically evaluated | Direction unknown |
| Ninja Teen / 2 | Departure payoff, menace, and recursion/pressure | Partial | Menace, Disappear/recursion, and related delayed behavior remain unsupported or bounded | Pilot can use legal attack options but cannot model the full long-term choice surface | Likely understated for recursion value; pressure effect direction unknown |
| Anchovy & Banana Pizza / 2 | Support/resource card that sustains the villainous pressure plan | Unknown-to-partial | The reviewed evidence does not isolate its complete card-specific contribution | Any supplied legal action follows fixed Pilot policy | Direction unknown; do not attribute aggregate strength to this card |

The inventory does not support a claim that Shredder’s complete strategic plan is fully
represented. It does support the narrower claim that ordinary creature deployment,
combat, several evasive bodies, bounded removal, and the Super Shredder departure-counter
path are present enough to make the broad result inspectable.

## What appears to drive the simulated strength

### Evidence-supported observations

- Threat density is high at 63.2%, with 24 creatures and 8 evasion entries in the baseline.
- Shredder wins broadly, not only in one matchup: 8 of 9 opponents exceed 55%.
- Super Shredder’s permanent-departure counter fragment is an observed, supported semantic.
- The deck contains 5 targeted-removal copies across 2 cards and a 13.2% interaction density.
- The near-even Raphael result demonstrates that Shredder can encounter meaningful pressure
  and counterpressure inside the same model.

### Plausible but unproven explanations

- Efficient early evasive pressure may convert maximum-attacker policy into reliable damage.
- Removal may clear blockers often enough that the threat density compounds.
- Super Shredder may create runaway states once ordinary departures accumulate.
- Four copies of Super Shredder plus multiple three-copy Shredder legends may create too much
  high-end threat redundancy, though no card-attribution analysis proves this.
- Opponents may lose defensive or recovery tools whose semantics are unsupported, exaggerating
  Shredder’s practical advantage.

No single hypothesis is established as the cause. The evidence supports testing the combined
pressure profile while avoiding an automatic nerf to one named card.

## Baseline-question review

| Baseline question | Disposition | Reason |
|---|---|---|
| Does Super Shredder snowball too quickly? | Supported concern, human confirmation required | Broad overperformance plus a supported departure-counter trigger makes runaway growth plausible, but the calibration does not expose state trajectories or fun. |
| Does removal leave meaningful counterplay? | Unresolved; requires human play | Shredder is 62.72% against Casey and 52.76% against Raphael, but the matrix cannot distinguish removal from threats or opponent semantic gaps. |
| Does sacrifice feel ruthless rather than fiddly? | Requires human play | The simulator can record legal transactions, not decision satisfaction, tracking burden, or opponent experience. |
| Do repeated Shredder legends clog the hand? | Unresolved; requires human play | The 4/3/3/3 high-threat identity may create congestion, but no hand-quality or play-experience evidence is banked. |
| Are 22 lands sufficient? | Unresolved | The curve is heavier than a low-curve aggro deck; full-game outcomes do not establish missed-land frequency as the cause. |
| Is removal oppressive in the beta pod? | Supported concern, not proven | Broad wins and 5 removal copies warrant testing, but Casey/Raphael results show that counterplay may exist. |
| Does Shredder remain villainous and distinct from Splinter? | Requires human play | The written identity is distinct, but simulation cannot measure theme expression or fun. |

## Smallest candidate-change hypotheses

These are investigation hypotheses, not approved changes. Each should be tested in human
play or a separately approved candidate packet before any list is altered.

### H1 — Reduce threat/payoff redundancy

- Implicated: the four-copy Super Shredder package and/or one of the three-copy Shredder
  legend packages; no exact swap selected.
- Rationale: broad strength and possible runaway states are consistent with redundant threats,
  especially when departures also grow Super Shredder.
- Expected effect: fewer repeated snowball draws and more recovery windows.
- Identity risk: could remove the signature Shredder inevitability and make the deck generic.
- Matchup impact: likely reduces broad pressure, with the greatest effect against slower decks;
  Raphael should be monitored as a counterpressure control.
- Unintended consequence: a reduction may merely lower consistency without improving opponent fun.
- Human play first: **yes**.

### H2 — Reduce removal redundancy rather than core threat identity

- Implicated: the 5-copy targeted-removal package across Stomped by the Foot and Shredder’s
  Technique; no exact cut or replacement selected.
- Rationale: test whether blocker removal, rather than creature quality, creates the perceived
  lack of counterplay.
- Expected effect: more opponent battlefield persistence and fewer unopposed attacks.
- Identity risk: Shredder must remain removal-driven and ruthless; excessive reduction breaks intent.
- Matchup impact: most informative against Casey, Raphael, and creature-heavy Splinter;
  slower/value matchups may remain heavily favorable.
- Unintended consequence: removal may not be the cause, and cutting it could only expose Shredder
  to bad matchups without addressing runaway threats.
- Human play first: **yes**.

### H3 — Reduce early evasive pressure redundancy

- Implicated: the Dream Beavers/Squirrelanoids early pressure package; no exact copy change selected.
- Rationale: maximum-attacker policy and 8 evasion entries may create a strong early damage floor.
- Expected effect: more time for opponents to stabilize and distinguish early damage from late payoff.
- Identity risk: Foot-soldier pressure is central to Shredder’s villainous identity.
- Matchup impact: likely most visible against April, Krang, and other decks that need setup time;
  may not change Raphael or Casey meaningfully.
- Unintended consequence: the test could weaken the deck’s intended ruthless tempo without reducing
  the Super Shredder problem.
- Human play first: **yes**.

### H4 — Address legendary congestion as a play-experience lever

- Implicated: the combined Super Shredder, Oroku Saki, Shark Shredder, and Shredder, Unrelenting
  packages; no exact replacement selected.
- Rationale: the baseline explicitly asks whether repeated legends clog the hand.
- Expected effect: more meaningful hand decisions and fewer stranded duplicate threats.
- Identity risk: high; the multiple Shredder identities are a major character expression.
- Matchup impact: unknown; it may improve play experience without materially changing the matrix.
- Unintended consequence: reducing legendary density may remove the very redundancy that enables
  the observed pressure, confounding a balance test with an identity test.
- Human play first: **yes**.

No hypothesis currently justifies a candidate decklist. The smallest responsible action is
to observe which problem players actually experience before selecting one lever.

## Focused human-play validation plan

### Opponents and starting-player balance

Prioritize four pairings:

1. Raphael, the near-even control pairing;
2. Casey Jones, the materially favorable but non-extreme pairing;
3. Donatello, an extreme 87.16% matchup;
4. April O’Neil, an extreme 91.11% matchup.

Use at least **24 human games**: 6 games per pairing, with 3 games per deck starting
and 3 games with Shredder starting. Randomize seating order and record mulligans. A larger
32–40 game set is preferable, but 24 is the minimum useful first pass for structured
qualitative comparison, not a replacement for Calibration V1.

### Record for every game

- starting player, mulligans, and opening land sequence;
- turn of first meaningful pressure and first removal use;
- whether Super Shredder appeared, how many departures fed it, and whether it created a
  runaway state;
- number and timing of removal decisions, including whether the opponent had recoverable
  counterplay;
- sacrifice decisions, tracking burden, and whether choices felt meaningful;
- legendary congestion, stranded cards, and recovery after a failed attack;
- opponent fun, pilot fun, perceived oppression, and Shredder/Splinter distinctness;
- whether the game was decided by early evasion, removal, Super Shredder, or another visible cause.

### Falsifiers

The current hypothesis is weakened if human games show that:

- Raphael and Casey routinely stabilize or reverse games despite the simulated spread;
- Shredder’s wins are not associated with early evasion, removal, or departure growth;
- Super Shredder rarely creates runaway states;
- players find sacrifice decisions engaging and counterplay plentiful;
- the extreme April/Donatello results are primarily caused by those decks’ unsupported plans;
- legend congestion or mana problems dominate the experience instead of excessive strength.

## Tradeoffs and recommendation

Every candidate lever risks flattening Shredder’s intended identity. A successful revision
must preserve ruthless pressure, villainous sacrifice/removal play, meaningful decisions,
and distinction from Splinter. The matrix alone cannot choose between threat, removal,
evasion, payoff, or identity levers.

The required next step is human evidence before any candidate decklist is prepared.

GATHER_HUMAN_EVIDENCE_FIRST
