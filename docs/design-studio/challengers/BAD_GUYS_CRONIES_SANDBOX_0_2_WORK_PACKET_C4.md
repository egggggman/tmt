# Bad Guys — Shredder's Cronies Sandbox 0.2
## Work Packet C4 — generic kicker and conditional removal

**Checkpoint recommendation: READY for independent C4 review; gameplay testing remains BLOCKED.**

C4 starts from the accepted C3 semantic runtime
`ab38515951c7faa1b1006a3e03ec4620c03a646538c2a3e54e44733716f44a37` and produces
semantic runtime
`6b2f86bf1834aece9dc1b3bc3817451601fb5c88e8581f1c7f6ba2a1d50d63a0`.
No deck, Baseline 005, R9-B, or historical evidence was changed, and no gameplay
simulation was run.

### Exact Oracle fixture

The pinned snapshot represents *Stomped by the Foot* as:

> Kicker—Sacrifice an artifact or creature. (You may sacrifice an artifact or
> creature in addition to any other costs as you cast this spell.) Target creature
> gets -2/-2 until end of turn. If this spell was kicked, that creature gets -5/-5
> until end of turn instead.

The interpreter recognizes this complete shape generically: an instant, an
artifact-or-creature kicker sacrifice, a targeted creature, and a conditional
temporary P/T replacement. It does not dispatch on card or deck names.

### Implemented semantics

- Main-phase and priority action generation exposes both unpaid and each legal
  artifact/creature sacrifice choice, while retaining normal mana payment.
- Announcement validates the target as a current creature, validates controller
  ownership and battlefield authority of the kicker sacrifice, and pays the
  sacrifice atomically before placing the spell on the stack.
- The kicker choice is retained on the stack object and serialized in evidence;
  resolution rechecks the target incarnation and applies either −2/−2 or −5/−5.
- Illegal targets fizzle without retargeting. Lethal toughness is handled by the
  existing state-based-action path, and the temporary modifier expires at cleanup.
- Event provenance records kicker payment and resolution source/target identities;
  forged or incomplete choices fail closed.

### Deterministic validation

`tests/test_kicker_removal_c4.py` covers complete grammar recognition, ordinary
and kicked payment choices, exact target validation, target departure before
resolution, lethal state-based actions, cleanup, and fail-closed invalid actions.
The focused C4 suite passes **4 tests**. Full pytest passes **1,650**, with **10
skipped**. Ruff check, Ruff format check, structural validation, and the
repository diff checks are required for publication; CI status is reported on
the review checkpoint after the remote commit is created.

### Remaining limitations

Mutagen artifact-token activation-cost reduction remains a distinct unsupported
family. Mutant Chain Reaction, Tainted Treats, Cowabunga! hidden-zone selection,
Paramecia Coloniex recursion, and Menace/Rhino grants remain open. No C5 work is
included here.

### Reproducibility

```text
uv run pytest -q tests/test_kicker_removal_c4.py tests/test_variable_x_tokens_c3.py
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

The machine-readable coverage overlay is
`BAD_GUYS_CRONIES_SANDBOX_0_2_COVERAGE_AUDIT_AB_RUNTIME.json`.
