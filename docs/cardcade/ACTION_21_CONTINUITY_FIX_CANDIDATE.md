# Action #21 Continuity Fix Candidate

Base: `e5196718922f7ec59f15e6f451718a42d1c34d95`

This bounded correction extends the existing artifact-entry self-counter recognizer to accept the
authoritative short self-reference `Donatello` for `Donatello, Way with Machines`. It does not add
card-specific dispatch or alter the existing trigger, Stack/Priority, provenance, or counter machinery.

The accepted Action #21 focused suite passes. A fresh bounded Stage #002 run (16 games / 32 executions)
was duplicate-deterministic, had zero invariant violations and zero runner stops, and classified the two
previous Donatello REACHED / UNSUPPORTED witnesses as EXECUTED:

- `donatello-krang:canonical:7201`
- `donatello-krang:reversed:7202`

The continuity result is evidence that the recognizer mismatch is repaired. Action #25 remains unauthorized
pending independent review.
