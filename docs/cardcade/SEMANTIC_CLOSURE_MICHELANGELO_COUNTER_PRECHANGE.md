# Michelangelo Extra +1/+1 Counter Replacement - Pre-change Checkpoint

Exact Oracle fragment:
`If one or more +1/+1 counters would be put on a creature you control, that many plus one +1/+1 counters are put on it instead.`

Game.place_counters is the authoritative counter-placement path. It validates battlefield targets, records before/after placement evidence, and evaluates static replacement occurrences. The missing behavior is the additional +1/+1 counter for an authoritative Michelangelo source. This bounded change preserves the existing placement path and counter types, adding only exact predicate applicability, deterministic source and quantity evidence, and fail-closed source departure behavior.
