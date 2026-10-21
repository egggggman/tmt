# Bad Guys — deterministic validation work order 001

Status: READY FOR ENGINEERING EXECUTION, NOT ENGINE-VERIFIED.

## Inventory result
The frozen ten-deck environment plus the Bad Guys sandbox contains 108 distinct card names (basic lands included), compared with 105 in frozen Baseline 005 alone. Only **three** Bad Guys card names are new to the combined ten-deck card pool: `Foot Elite`, `Foot Ninjas`, `Tokka & Rahzar, Terrible Twos`. Other Bad Guys inclusions were already present elsewhere in the ten-deck environment, though their combinations and pilot context can be new.

This is a useful efficiency finding: prioritize the three genuinely new card semantics, plus combinations with existing cards, rather than retesting all 17 from scratch.

## Fixture order (do not mark passed without actual execution)
1. **Foot Elite**: attack trigger fires at declare attackers; must target another friendly creature; +1/+0 and indestructible apply through combat and expire at end of turn. Negative test when no other creature is present.
2. **Foot Ninjas**: ordinary cast and Sneak alternative; require unblocked attacker during declare blockers; return that attacker to hand; enter tapped/attacking; gain three life; check pilot opportunity and legal cost payment. Negative case with no unblocked attacker.
3. **Tokka & Rahzar**: compare mana actually spent to spell mana value, trigger 3 damage to that spell's controller only when spent < MV; ordinary-cost control and discounted spell positive case. Validate menace blocking and can't-be-countered behavior separately.
4. **Existing cross-card paths**: Bebop & Rocksteady attack/block discard-or-sacrifice; Foot Mystic Disappear after a permanent leaves; Zoo Escapees leaving; Ice Cream Kitty sacrifice/draw; Shredder's Armor equip sacrifice and recalculation; Stomped kicker sacrifice; Foot Elite's protection in those combats.
5. **Pilot and mana**: check whether pilot selects Sneak, uses sacrifice outlets meaningfully, identifies profitable Foot Elite attacks, and can deploy early board with 20 lands. Opportunity metrics require actual legal-action enumeration; action logs alone are insufficient.

## Execution commands — to be resolved from repository
Use existing test runner and coverage ledger. Before executing, identify exact test paths and commands from current main; do not invent a passing result or assume keyword presence implies semantics. Preserve deterministic fixture seeds and runtime identity. Run targeted fixtures, then the repository regression suite. Report pass/fail per mechanic with failing seed and minimized game state.

## Gates
- **BLOCKED for gameplay simulation** until semantic fixtures, pilot coverage, and live Standard legality are verified.
- **READY for engineering preflight execution** with no deck changes.
- Existing Baseline 005, R9-B evidence, and the Bad Guys sandbox remain frozen.

No simulator tests or gameplay were executed to produce this work order.
