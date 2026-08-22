# Creature Dies → Draw One Acceptance Audit #1

Status: **REJECT**  
Audit date: 2026-08-22  
Branch: `agent/cardcade-dies-draw`  
Audited candidate: `d65b21d352b9552e6d046ab2c2e7c2d984da2755`  
Candidate CI: **UNCONFIRMED**

## Verdict

**REJECT — authoritative last-known creature provenance is missing from death
qualification.**

The bounded implementation correctly recognizes only `When this creature dies, draw a card.`,
uses a distinct trigger and Stack object, respects Priority/pass, resolves through the existing Draw
path, preserves last-known controller, and handles failed Draw through the subsequent state-based
action boundary. Corpus membership remains limited to Buzz Bots, and neighboring Oracle forms
remain unsupported.

The material defect is narrower. `put_into_graveyard()` qualifies the event from the printed card
definition rather than the permanent's authoritative last-known battlefield characteristics. A
printed creature that ceased being a creature on the battlefield would therefore incorrectly
produce `CREATURE_DIED` and the Draw trigger when moved to a graveyard. Under the represented rules
boundary, “dies” requires that the object was a creature immediately before the battlefield-to-
graveyard transition.

## Smallest evidence-backed correction

Freeze authoritative last-known battlefield characteristics in the death event and require the
departing object to have been a creature at that moment. Resolution and invariants must authenticate
that frozen provenance rather than infer creaturehood later from `CardDefinition`.

Required adversarial evidence:

1. printed creature and authoritative creature at departure triggers;
2. printed creature but authoritative noncreature at departure does not trigger;
3. fabricated or relinked last-known creature provenance fails closed;
4. lethal damage, simultaneous deaths, controller identity, Priority/pass, Draw, and empty-library
   behavior remain unchanged.

No broader dies-trigger parser, gameplay capability, deck change, Stage #002 rerun, calibration,
smoke test, Pilot change, or Prototype 0.3 work is justified by this rejection.

