# TMNT the Cardcade Game

Cardcade is the reproducible evidence system for the ten-deck Mutants the Gathering battle set. It reports observations and hypotheses under a named engine, Pilot, roster, deck version, seed, and protocol. It does not revise decks or authorize product decisions.

## Authority and boundaries

- Cardcade reports evidence and hypotheses.
- Design Studio owns deck revisions and Prototype decisions.
- HQ owns authorization gates.
- Prototype 0.2 is frozen; Prototype 0.3 design-cycle investigation is limited to four named decks and actual deck files remain **NOT AUTHORIZED**.
- Calibration V1 balance evidence is complete and audited; interpretation and deck revision remain Design Studio decisions.

Engine 0.8 is the accepted architectural foundation. Banked post-foundation evidence reaches Action #32 where repository evidence supports acceptance; Action #33 remains **NOT AUTHORIZED**. Pilot Fitness V3 is a bounded pass, not a balance conclusion.

## Calibration governance

Calibration Protocol V1 is the governing prospective dataset. It requires **184,320 distinct games** and preserves exact run identity, wrapper bytes, authentication material, seed identity, schedule identity, and separate execution authorization. Seed Table V2 is frozen and immutable; it must not be regenerated, replaced, or consumed outside an authorized run.

The repository-owned sequence is:

1. reserve a fresh run identity;
2. render the exact run-specific wrapper;
3. hash and freeze the wrapper and identity/authentication material;
4. obtain HQ authentication of those exact bytes;
5. obtain separate HQ execution authorization;
6. execute the unchanged wrapper;
7. audit integrity before statistical analysis.

PR #172, merged as `58a8bac85600318ccd727959770b60869003c017`, established the fail-closed run-ID reservation contract. Reservation is not execution and does not consume seeds.

## V16 status

V16 run `CALIBRATION_V1_20260919T012117Z_65775003` reached **121,808 / 184,320 distinct games (66.09%)** before failing closed because local storage was exhausted. V16 is classified as an incomplete storage/evidence failure, not balance evidence and not a demonstrated gameplay-engine failure.

V16 must never be resumed, combined with later calibration results, or used for partial balance conclusions. Historical calibration evidence remains preserved, including verified archive migration. The authenticated baseline and release constraints remain in `docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json` and related historical records.

## Qualified execution layout

- `C:\Projects\tmt` is the code/runtime location.
- `G:\` is the qualified prospective live calibration evidence target.
- G: is NTFS, with **976.56 GiB capacity** and **874.66 GiB free** at qualification.
- Qualification completed **2,000 / 2,000** atomic temp-write, `os.replace`, and read-back cycles with zero failures.
- Historical archived evidence remains preserved separately.

Calibration V1 run `CALIBRATION_V1_20260923T141649Z_3f838930291e` completed and passed its completion audit. Production evidence remains external on G:; the repository analysis is descriptive evidence only.

## Current critical path

Design Studio candidate-packet investigation for four named decks → later explicit card-level decision. No result automatically authorizes a deck change or Prototype 0.3 file.

No step in this path changes simulator semantics, decks, seeds, or Protocol V1. No step authorizes Prototype 0.3 by itself.

## Historical Cardcade 0.1 record

The following is preserved historical context, not the current calibration contract.

Cardcade 0.1 was a stochastic resource/tempo model covering opening hands and mulligans, land drops, mana use, broad board/support/interaction development, strategy execution, starting-player advantage, and a noisy closing race. It did not execute card text, priority, the stack, combat, targets, replacement effects, or matchup-specific decisions. Its smoke results were engine and ecosystem diagnostics, not proof that decks were balanced or fun.

Its historical ladder was:

| Stage | Games per unique pairing | Total games | Historical purpose |
| --- | ---: | ---: | --- |
| Smoke | 20 | 900 | Structure, telemetry, obvious model/deck outliers |
| Calibration | 100 | 4,500 | Locate major imbalances and model sensitivity |
| Development | 500 | 22,500 | Evaluate Design Studio revisions |
| Validation | 1,000+ | 45,000+ | Freeze a baseline candidate |

Those figures describe the old Cardcade 0.1 model and must not be substituted for Calibration Protocol V1.
