# Issue 289: complete counter and temporary keyword instant

This checkpoint stacks on draft PR #310. The ten frozen Baseline 005 decks, original 172-row ledger, prior overlays, and historical simulations remain unchanged. Four games below are bounded diagnostics, not balance estimates.

## Selection

| Family | Frozen copies / critical rows | Assessment |
| --- | ---: | --- |
| Saved by the Shell | 3 / 3 | Conditional Turtle discount already executes; a complete targeted counter plus temporary trample, hexproof, and indestructible spell reuses the counter, keyword, and combat model. **Selected.** |
| Mind Transfer Protocol | 3 / 2 | Needs a temporary artifact-creature type change, base 4/5 P/T layer, and draw coupled into one spell. Remains critical. |

The [prior checkpoint](ISSUE_289_MODAL_SPELL_RESULTS.md) and [machine overlay](ISSUE_289_COUNTER_KEYWORD_GRANT_CHECKPOINT.json) preserve the full assessment and remaining rows. No card or deck name controls execution.

## Rules and evidence

The interpreter recognizes a whole instant or sorcery with a supported conditional generic discount and an instruction placing a counter on a target creature its controller controls, followed by supported temporary keywords. Unknown companion clauses, keywords, and target patterns leave the spell unsupported; no partial cast is offered. The engine offers only legal targets, rechecks target and payment on announcement, places the spell on the normal stack, and rechecks the target at resolution. An illegal target produces no counter or keyword effects. Successful resolution places the +1/+1 counter, grants trample, hexproof, and indestructible until cleanup, checks state-based actions, and retains the counter afterward. Temporary hexproof respects controller identity, including optional triggered target selection and resolution; temporary indestructible prevents destroy and lethal/deathtouch damage but not zero toughness. Trample uses normal combat assignment. The temporary effects survive the spell source leaving the stack and expire at end of turn.

- Ten focused tests cover the frozen Oracle fixture and a renamed source, refusal of incomplete clauses, target legality, cost reduction and full payment, main and priority actions, stale payment, controller and zone changes, fizzle and countering, temporary hexproof and indestructible, trigger targeting before and after a hexproof grant, trample combat, cleanup, source departure, invariants, and repeatable snapshots. Existing discount and trample tests were updated for complete support.
- Four mirrored Michelangelo/Raphael and Michelangelo/Shredder frozen-deck diagnostics matched four deterministic replays without runtime errors. They recorded four Saved by the Shell casts, four paid costs at the Turtle-reduced `{G}` cost, and four complete counter and keyword resolutions. The [machine diagnostics](ISSUE_289_COUNTER_KEYWORD_GRANT_SMOKE.json) retain game digests, cost sources, target and stack IDs, and keyword grants. The manifest's Michelangelo source SHA used CRLF; this checkout's LF file hashes to the recorded SHA when its line endings alone are normalized. No deck text changed.
- The original ledger SHA-256 remains `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`; the #310 overlay SHA-256 remains `899c16171c0ce61056033bff50abe77068035819ad9f6828a6d45428edabc77c`. Exactly three Saved clause rows change: **14 critical / 61 important / 3 partial → 11 critical / 61 important / 2 partial**. The cost discount row changes from partial to supported; two effect rows change from gap to supported. All 172 row identities remain fixed.
- Semantic runtime changes from `82e98882e36523ade85ee4261a8f0f7675bef98fa50ac4d96d43469d6f2fcf77` to `1ecd33d0702f60c5c892a94a43112c238874518334cdcb4ed80acf5d831a57ca`. Historical Baseline 005 controls are not runtime compatible. Baseline 005 manifest SHA-256 remains `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
- Focused and affected regression tests: **93 passed**. Full regression: **1,825 passed, 10 skipped**. Baseline 005 structural validation, repository-wide Ruff check and format, exact row-change audit, Markdown links, and diff check passed. The structural validator prints historical land-count prose; authenticated manifest and deck checks pass. The sealed V3 packet was not edited; its assertion projects only the three new inactive temporary keyword fields in current pilot views.

**Checkpoint acceptance:** pending final-head CI. **Baseline 005 calibration readiness:** BLOCKED by eleven critical entries, including linked play, recursion, library/hand effects, Mind Transfer Protocol, and zone-changing removal. No control, deck revision, merge, or promotion occurred.
