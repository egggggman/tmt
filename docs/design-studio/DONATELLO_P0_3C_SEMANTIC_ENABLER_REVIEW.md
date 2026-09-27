# Donatello Prototype 0.3c Semantic-Enabler Review

Decision: **`AUTHORIZE_MOUSER_MARK_III_SEMANTIC_ENABLER`**

This is a review-only authorization. No deck, Cardcade semantic, Pilot, or smoke
schedule is changed here. Prototype 0.3c remains uncreated until the separate
semantic PR is complete and validated.

## 1. Blocked-state summary

The preceding review recorded
[P0_3C_CANDIDATE_SELECTION_BLOCKED](DONATELLO_P0_3C_CANDIDATE_SELECTION_BLOCKED.md)
because no four-card package simultaneously provided an early body, immediate
tempo, Standard legality, mono-blue mana compatibility, legal quantities, and
faithful Cardcade execution.

The P0.3b experiment already exercised Utrom Scientists as the supported body/
tempo candidate. It cast 55 times at an average turn of 14.45 and did not move
Donatello's frozen result. Repeating that candidate would not test the known
critical-turn problem.

The present question is narrower: whether one small reusable semantic slice can
make a different early artifact body faithful enough to unlock a credible P0.3c
experiment.

## 2. Mouser Mark III analysis

The authoritative card data identifies Mouser Mark III as:

| Field | Value |
| --- | --- |
| Mana cost | `{1}{U/R}` |
| Mana value | 2 |
| Type line | Artifact Creature — Robot |
| Power/toughness | 2/3 |
| Oracle text | `This creature can't attack unless you control another artifact.` |
| Standard | Legal |

This is a materially better critical-turn body than Utrom Scientists. It can be
cast on turn two with a blue source, blocks as a normal 2/3 without any artifact,
and contributes an artifact entry for Way with Machines. Its attack restriction
does not reduce its defensive value. Donatello's existing artifact density means
that the restriction will often permit attacks later, but the simulator must still
check the condition rather than assume it.

The smallest faithful behavior is:

- Mouser remains a normal artifact creature and may block normally;
- during attacker declaration, it is an eligible attacker only if its controller
  controls another artifact permanent;
- the condition is evaluated from the current battlefield at declaration time;
- no Donatello-specific branch is needed;
- AcceptancePilot can continue selecting from the engine's legal attack options.

## 3. Chrome Dome analysis

The authoritative card data identifies Chrome Dome as:

| Field | Value |
| --- | --- |
| Mana cost | `{2}` |
| Mana value | 2 |
| Type line | Artifact Creature — Robot Ninja |
| Power/toughness | 1/3 |
| Oracle text | `Other artifact creatures you control get +1/+0.` and a `{5}` artifact-copy activation |
| Standard | Legal |

Supporting only the static anthem would be a possible bounded semantic slice, but
it would omit the card's second activated ability. That omission is less severe
than treating an unsupported activation as present, but Chrome Dome is still only a
defensive 1/3 until the static effect is wired and does not itself provide
immediate interaction. Supporting the copy activation would require target,
copy, temporary-token, haste, and delayed-sacrifice semantics. That is materially
broader than the Mouser slice and does not directly solve the early tempo test.

Chrome Dome is therefore not authorized.

## 4. Skateboard analysis

The authoritative card data identifies Skateboard as:

| Field | Value |
| --- | --- |
| Mana cost | `{1}` |
| Mana value | 1 |
| Type line | Artifact — Equipment |
| Oracle text | `When this Equipment enters, tap target permanent.` Equipped creature gets `+1/+0` and haste; equip `{1}` |
| Standard | Legal |

Although Skateboard is cheap and artifact-aligned, faithful execution requires an
ETB target, Equipment attachment state, continuous granted power/haste, equip
activation timing, and interaction with combat legality. A partial implementation
would either make the card a one-shot tap spell or silently omit its central
Equipment behavior. This is broader than the authorized one-enabler question and
does not provide an early creature body by itself.

Skateboard is not authorized.

## 5. Hybrid-mana determination

Under Magic rules, `{U/R}` is a hybrid symbol: each symbol may be paid with either
one blue or one red mana. An Island therefore can pay the blue option in
`{1}{U/R}`. Mouser Mark III is compatible with Donatello's Island-only mana base;
the red half of the hybrid symbol does not make the card uncastable in this deck.

The current Cardcade payment model does not yet represent that rule. Its
`mana_requirement` and activation-cost parsers accept generic and single-color
symbols but reject `U/R` as an unsupported symbol. No existing hybrid payment path
was found in the runtime or tests.

This is a small generic payment extension needed to make the candidate castable,
not a reason to classify Mouser as off-color. It must be tested independently with
blue payment, red payment where available, insufficient payment, and deterministic
source selection. The Donatello deck itself still supplies only Islands.

## 6. Semantic implementation-cost comparison

| Candidate | Missing surface | Reusability | Misrepresentation risk | Breadth |
| --- | --- | --- | --- | --- |
| **Mouser Mark III** | Hybrid mana payment plus one conditional attacker-eligibility restriction | Generic hybrid cost handling and generic attack legality | Low if the restriction is checked only at declaration | Narrow |
| **Chrome Dome** | Artifact-specific static P/T effect; copy activation remains after a static-only slice | Static layers reusable; copy/token activation is broad | Medium to high if the card is tested without its copy ability | Medium/high |
| **Skateboard** | ETB target, Equipment attachment, granted P/T and haste, equip timing | Several reusable systems | High if reduced to “tap on entry” | Broad |

Mouser is the only candidate whose complete relevant gameplay can be represented
with a small pair of generic primitives. The authorization is therefore for one
candidate semantic enabler, named Mouser Mark III, with hybrid payment plumbing
treated as the necessary generic castability part of that same bounded slice.

## 7. P0.3c package feasibility

Once Mouser is faithfully supported, a legal four-card package becomes credible
within the existing authorization. The preferred shape to evaluate is:

```text
-2 Sewer-veillance Cam
-2 Return to the Sewers
+3 Mouser Mark III
+1 Ooze Spill
```

This is not a deck creation or approval of the final list. It is the smallest
feasibility shape that respects the four-copy limit: Ooze Spill moves from three
to four rather than illegally adding two copies, while three turn-two artifact
bodies provide genuine density. It preserves Does Machines, Donatello's
Technique, and Way with Machines, changes no lands, and keeps Donatello's artifact
identity.

The package tests both requested axes:

- Mouser supplies earlier artifact battlefield presence and a 2/3 defensive body;
- the additional Ooze Spill supplies one more already-supported artifact-aligned
  counterspell/Mutagen tempo card;
- Mouser entries increase the available artifact-entry events for Way;
- the cut pool removes delayed utility rather than core engine cards.

AcceptancePilot already selects ordinary creature casts through the generic
creature action path and receives legal attack options from the engine. No
Mouser-specific Pilot strategy should be added. Ooze Spill already has an
implemented cast/resolution surface; the later semantic PR must only confirm that
the existing Pilot can use its legal option in this list.

## 8. Simulator-development tradeoff

Implementing Mouser is justified only as a bounded diagnostic enabler. It does not
authorize:

- broad hybrid-mana support beyond the fixed reusable symbol model;
- a general attack-AI redesign;
- Chrome Dome copy/static work;
- Equipment infrastructure;
- new Pilot priorities;
- a deck change in the semantic PR.

The later Cardcade PR must prove that the restriction is enforced at attacker
declaration, that Mouser can still block without another artifact, that Islands can
pay its hybrid symbol, and that non-Mouser cards retain their existing behavior.
Only after those tests pass should a separate Design Studio PR create P0.3c and
validate the proposed package without running the smoke in either implementation
PR.

## 9. Decision

`AUTHORIZE_MOUSER_MARK_III_SEMANTIC_ENABLER`

This is the sole semantic enabler authorized by this review. Chrome Dome and
Skateboard remain unapproved alternatives. No deck revision is authorized in this
PR.

## 10. Exact next gate

Create one separate, focused Cardcade PR implementing only the reusable hybrid-cost
and conditional-attacker-legality slice required for Mouser Mark III. Validate the
slice with unit tests and a deterministic cast/attack regression; do not modify
any deck or run either the compact diagnostic or 240-game smoke in that PR.

After that PR is merged and green, create a separate preserved P0.3c Design Studio
candidate using the four-card feasibility shape above, authenticate it, validate
its structure and legality, and then decide whether the exact frozen smoke should
be run. No P0.3c file is created by this review.
