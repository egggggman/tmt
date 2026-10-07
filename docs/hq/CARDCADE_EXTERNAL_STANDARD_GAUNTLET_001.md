# Cardcade External Standard Gauntlet 001 — Work Packet

Owner: 🏢 HQ coordination  
Execution owner: 🕹️ TMNT the Cardcade Game  
Interpretation authority: 🧪 Design Studio  
Status: **SPECIFICATION ONLY — EXECUTION NOT YET AUTHORIZED**

## Purpose

Create a reproducible external robustness benchmark for the Mutants the Gathering environment using public Standard 60-card deck lists, with Moxfield as a candidate discovery source.

This benchmark is **secondary evidence**. The primary product remains the ten-deck Mutants the Gathering battle environment, and internal balance remains the primary balance target.

## Governing question

How do the ten current Mutants the Gathering decks behave against a broad, frozen sample of ordinary outside Standard decks, and does that evidence reveal:

- environment-wide power-level mismatch;
- unusual outlier behavior by one or more TMNT decks;
- archetype-specific weaknesses or strengths;
- possible simulator or fixed-pilot bias that is not obvious inside the closed ten-deck environment?

The benchmark must **not** tune every TMNT deck toward a 50% external win rate.

## Required capabilities before execution

Cardcade must demonstrate that it can ingest and validate an external deck without silently approximating unsupported cards or mechanics.

Before any benchmark games:

1. Resolve every card and printing in each candidate external list.
2. Confirm the list is a legal 60-card Standard deck for the benchmark's frozen legality date.
3. Produce Action/semantic coverage for every nonland card.
4. Reject or quarantine any list whose important gameplay cannot be represented credibly by the current engine.
5. Preserve the exact imported deck text, source metadata, content hash, legality result, and coverage result.
6. Use generic game rules and pilot behavior only. No deck-name, archetype-name, author-name, or TMNT-specific strategy exceptions.
7. Demonstrate deterministic replay under the benchmark runtime before scaling.

A deck that cannot pass these gates is not a valid gauntlet member.

## Discovery pool

Target **25–50 external decks** initially.

Moxfield may be used to discover candidates, but random discovery must not mean uncontrolled sampling. Preserve enough source metadata to reproduce the pool and distinguish discovery from acceptance.

Prefer diversity across broad gameplay structures such as:

- aggressive creature decks;
- midrange;
- control;
- tempo;
- ramp;
- artifact/synergy decks;
- graveyard or recursion strategies;
- other Standard archetypes the engine can represent credibly.

Do not select decks because they produce a desired TMNT win rate.

Do not repeatedly redraw the sample until the results look balanced.

## Freeze protocol

Once accepted, create **EXTERNAL_STANDARD_GAUNTLET_001** with:

- exact deck lists;
- stable member IDs;
- source URLs or source identifiers where permitted;
- retrieval date;
- legality date;
- deck-content SHA-256;
- archetype classification with classification method recorded;
- semantic/action coverage status;
- exclusions and exclusion reasons;
- benchmark manifest hash.

The frozen pool must remain unchanged for comparisons. Any later membership change creates a new gauntlet version.

## Testing progression

Do not begin with a large matrix.

### Stage A — ingestion and semantics

Validate candidate lists individually. No balance conclusions.

### Stage B — smoke

Run a small deterministic smoke sample against a limited TMNT subset to prove external-deck execution, logging, game completion, and replay stability.

### Stage C — pilot/engine validation

Inspect representative games across different external archetypes. Look specifically for systematic passivity, illegal sequencing, unspent resources, unsupported triggers/actions, targeting defects, or archetype-specific pilot failures.

If simulator behavior is questionable, stop. Do not compensate by editing decks.

### Stage D — benchmark

Only after A–C pass may Cardcade execute the frozen external benchmark across the ten current TMNT decks.

The exact game count and schedule are to be proposed by Cardcade after the accepted pool size and runtime cost are known. Starting-player splits must be balanced and seeds/schedule preserved.

## Reporting

Report at minimum:

- aggregate TMNT environment win rate against the gauntlet;
- each TMNT deck's aggregate external result;
- each external member's aggregate result;
- results grouped by broad archetype where classification is credible;
- starting-player split;
- ending-turn distribution;
- runtime errors and unsupported/partial semantics;
- deterministic replay results;
- outlier cells;
- confidence intervals where appropriate;
- comparison with the current internal Baseline 005 picture without treating the two datasets as interchangeable.

## Interpretation rules

External results are **diagnostic, not automatic design authority**.

Examples:

- If most TMNT decks are weak or strong by a similar amount, investigate environment-wide power level and simulator/pilot behavior before deck-by-deck revisions.
- If one TMNT deck is an external outlier while the rest cluster together, return the evidence to Design Studio as a targeted hypothesis.
- If a deck is strong internally but ordinary externally, investigate matchup composition before concluding that the deck is generically overpowered.
- If a deck is strong both internally and externally, that strengthens—but does not by itself prove—a power-level hypothesis.
- If unrelated external decks show implausibly similar failures, investigate Cardcade before touching TMNT deck construction.

No deck revision is authorized by this work packet.

## Relationship to human Game Day

Human Game Day Candidate 0.1 remains the immediate priority.

External Gauntlet work must not delay physical preparation or replace human evidence about fun, clarity, identity, interaction, or replay desire.

Recommended sequence:

**Internal Baseline 005 evidence → Human Game Day → External Standard Gauntlet → Design Studio interpretation**

Preparatory specification/ingestion work may proceed in parallel only when it does not interfere with Game Day readiness.

## Evidence preservation

Preserve:

- candidate discovery record;
- accepted and rejected external lists;
- rejection reasons;
- frozen manifest;
- runtime identity;
- schedules and seeds;
- raw results;
- replay evidence;
- analysis artifacts;
- final Cardcade handoff.

Never overwrite a prior gauntlet version.

## Stop conditions

Stop and return to HQ/Cardcade review if:

- Standard legality cannot be established reproducibly;
- important external cards require unsupported semantics;
- pilot behavior appears systematically invalid for an archetype;
- deterministic replay fails;
- the source pool cannot be frozen/reproduced;
- external testing would require TMNT deck changes merely to make the simulator work.

## Authorization boundary

This packet authorizes **design of the benchmark and readiness investigation only**.

It does **not** authorize:

- large simulation batches;
- changes to Baseline 005;
- TMNT deck revisions;
- external-result-based promotions;
- simulator shortcuts designed to force balance;
- replacement of internal balance or human playtesting as project authority.

### NEXT MOVE → 🕹️ Cardcade

After Game Day preparation is secure, perform a readiness audit for external Standard-deck ingestion and report the smallest missing capability, if any, before proposing Gauntlet 001 execution.

COWABUNGA.
