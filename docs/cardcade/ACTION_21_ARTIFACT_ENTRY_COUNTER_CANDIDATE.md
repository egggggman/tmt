# Action #21 — Artifact Entry Counter

Bounded candidate for Donatello, Way with Machines: whenever an artifact you control enters, put one +1/+1 counter on the authoritative source.

The implementation uses existing trigger, Stack/Priority, provenance, incarnation, and counter systems. It filters by controller and Artifact type, creates one trigger per qualifying entry, and applies the counter only when the trigger resolves against the same authoritative source incarnation. Stale, relinked, wrong-zone, wrong-controller, and nonartifact cases fail closed.

Excluded: arbitrary enters triggers, other payloads or counters, deck changes, calibration, balance work, broad simulation, Prototype 0.3, and Action #22.
