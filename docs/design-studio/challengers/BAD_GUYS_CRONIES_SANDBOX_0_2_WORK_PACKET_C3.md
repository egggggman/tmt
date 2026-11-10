# Bad Guys — Shredder's Cronies Sandbox 0.2
## Work Packet C3 — generic variable-X token creation

**Decision: READY for independent C3 checkpoint review; gameplay testing remains BLOCKED.**

This checkpoint starts from accepted C2 runtime
`c95426fe7baba7794884782e781df1deda0c8d162cf70df03f0a8da1528a6691` and produces
semantic runtime `ab38515951c7faa1b1006a3e03ec4620c03a646538c2a3e54e44733716f44a37`.
The candidate, Baseline 005, R9-B, and historical simulation evidence were not
changed. No gameplay simulations were run.

## Exact Oracle behavior

The accepted pinned card snapshot represents the relevant clause as:

> When Mutagen Man enters, create X Mutagen tokens. (They're artifacts with
> "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature.
> Activate only as a sorcery.")

The implementation recognizes the reusable shape: a creature with an X mana
symbol and an ETB clause creating X tokens. It does not dispatch on Mutagen Man
or any deck name. The separate artifact-token activation discount remains
unsupported and is intentionally out of scope.

## Implemented semantics

- X is an explicit nonnegative announcement choice; legal main actions expose
  each currently payable X value.
- The resolved requirement includes X plus the fixed colored/generic symbols;
  missing, negative, or unaffordable values are rejected atomically.
- The announced X is retained on the stack object, copied to the entering
  permanent, and captured on the ETB trigger. It survives source departure and
  independent stack resolution.
- Resolution creates exactly X tokens with the parsed token definition and
  controller. X=0 creates no token event batch; countered spells never enter and
  never create tokens.
- Each spell has an independent X value and deterministic event provenance.

## Evidence

Focused C3 tests (`tests/test_variable_x_tokens_c3.py`) cover X=0/1/many,
insufficient and malformed payment, source departure before ETB resolution,
independent X values, countered spells, exact token characteristics/controller,
and invariant checks. The token coverage contract was updated to recognize the
new generic family (including the other snapshot card with the same bounded
shape); no deck list or historical artifact was edited.

The C2 regression suite remains green after the semantic change. Full pytest,
Ruff, formatting, structural validation, and CI results are recorded on the
published checkpoint commit. No C4 work or gameplay test is included.

## Remaining limitation

The artifact-token `{1}` activation discount remains a distinct unsupported
cost-reduction family. It must not be inferred from C3's variable-X payment
support.

**Recommendation:** READY for independent acceptance of C3; BLOCKED for any
gameplay simulation or C4 until HQ reviews this checkpoint.
