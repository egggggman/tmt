# Issue 289 — shared interaction spell checkpoint

**HQ recommendation: BLOCKED** for the unchanged Baseline 005 45-cell / 4,500-game control. This checkpoint stacks on draft [PR #295](https://github.com/egggggman/tmt/pull/295), itself stacked on #294 and the accepted #290–#293 checkpoint chain. It changes no deck, frozen catalog, historical simulation, or previous coverage ledger.

## Immutable provenance and runtime

The [original 172-row ledger](ISSUE_289_COVERAGE_LEDGER.csv) remains SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`; the [land checkpoint](ISSUE_289_LAND_SEMANTICS_CHECKPOINT.json) remains SHA-256 `69d299f87678e59434e0b015c176cafcc245ddd3d476642d576f4e13e30c4bcf` and runtime `26a20e23ec621f492a7e4cf980ec431b0349bd520816baafbd9e9b72150a4c11`. The new [full-row overlay](ISSUE_289_SHARED_INTERACTION_CHECKPOINT.json) records the runtime `5a7b948a7c6745971bfb9d66471aee4a369363ff944f2926fad0536700f7aed3`. Earlier controls, including Combined 007, cannot be reused under this runtime. No calibration batch was run.

| Execution judgment | #295 | This checkpoint |
|---|---:|---:|
| Critical P0 | 46 | **41** |
| Important P1 | 71 | **68** |
| Partial | 2 | **2** |
| Gap | 115 | **107** |
| Supported by overlays | 15 | **23** |
| Prior covered / annotation | 33 / 7 | **33 / 7** |

Eight ledger entries close, representing two Cowabunga! deck rows and both Stomped by the Foot clauses in three decks. Stomped has **ten physical frozen deck copies** (three Splinter, four Shredder, three Bebop & Rocksteady); Cowabunga! has **six** (three Michelangelo, three Bebop & Rocksteady). The engine parses complete Oracle clauses and uses the parsed program for the effect; no card or deck name dispatch was introduced.

Stomped pays `{1}{B}` from the normal mana planner. The pilot can cast the ordinary version or announce the kicker by choosing a controlled artifact or creature to sacrifice. Both players' creatures are legal targets; the target can itself be paid as the sacrifice, in which case resolution finds the target illegal and the spell has no effect. The cast stack object records the paid sacrifice, and resolution applies the corresponding −2/−2 or −5/−5 temporary modifier, then checks state-based actions. After blockers are declared, a represented payable instant opens a normal priority window before combat damage. Tests include first strike and double strike sequencing and cleanup expiration. The pilot considers these actions by target state rather than card identity.

Cowabunga! pays `{G}` as a sorcery, privately inspects up to four actual top library objects, offers a legal optional choice only for printed Mutant, Ninja, Turtle or land characteristics, reveals the selected card and puts it into hand, and randomizes only the rest onto the bottom. The random permutation has a recorded deterministic RNG domain and the event records inspected, selected, and bottom IDs. Invalid chooser output leaves hand, library, RNG, and stack unchanged.

The focused suite covers frozen and renamed cards, unsupported appended clauses, payment, sacrifice/target legality, resolution after a target leaves, priority after blocking and for main actions, temporary P/T expiration, first/double strike, optional decline, subtype and land eligibility, invalid choices, invariants, and exact snapshot/event replay (**12 passed**). Full regression: **1,698 passed, 10 skipped**. Two mirrored frozen B&R/Shredder diagnostic games and their replays matched exactly without runtime errors ([machine smoke](ISSUE_289_SHARED_INTERACTION_SMOKE.json)). Three Stomped resolutions appeared; neither game resolved Cowabunga!, so its direct execution proof is the focused tests. Ruff check/format and diff checks passed. The unchanged Baseline 005 structural validator passed; its console sentence about historical land totals remains stale and is not treated as provenance.

## Remaining gate

Forty-one P0 and 68 P1 ledger entries remain, with two partials. The next shared intervention should address **Spicy Oatmeal Pizza** entry damage across Raphael/Casey and **Mutant Chain Reaction** or other cross-deck removal, then the severe identity clauses: Raphael's linked exile/play permissions, Bebop & Rocksteady's attack/block obligation, April Hacktivist's end-step card draw, and modal or conditional combat spells. This checkpoint is mechanical evidence, not a fresh balance estimate. Design Studio owns any later deck decisions; HQ must authorize the control only after a readiness threshold is reached.
