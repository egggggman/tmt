# Bad Guys Cronies Sandbox 0.2 — Work Packets A/B

Status: **READY for independent review; BLOCKED for gameplay testing**

This checkpoint implements only the two authorized semantic remediation packets for
`OBL-BAD-GUYS-CRONIES-SANDBOX-0.2`. No deck list, Baseline 005 artifact, R9-B
evidence, or gameplay simulation was changed or run.

## Provenance

- Pre-change semantic runtime: `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`
- Post-change semantic runtime: `00fc49eb47d9ffd3d0243564cc7c9763d11738ca9698811306102747a060d374`
- Implementation commit: `5017d35` (stacked on PR #363 head `0569ed82c90b6fab21fcc91b1bdba0b04615415f`)
- Candidate and Baseline 005 hashes are unchanged from the authenticated PR #363 report.

## Work Packet A — generic attack-target effect

The interpreter now recognizes the Oracle-shaped attack trigger generically and
produces an executable semantic program for another target creature controlled by
the attacking creature's controller. The engine creates the trigger, offers only
legal targets, rechecks the target at resolution, applies `+1/+0`, and records a
temporary indestructible effect through the normal end-of-turn cleanup path.

Indestructibility is honored by both lethal-damage state-based actions and explicit
destroy operations. A departed or otherwise illegal target fails closed. No card or
deck name is consulted by the execution path.

## Work Packet B — generic conditional ETB/Disappear effect

The engine now retains a typed permanent-departure history with the controller and
turn of departure. A conditional ETB token trigger is created only when the
intervening condition is true, and it is checked again at resolution. The token
creation program is the existing generic token machinery, including normal entry
events and object identities. Departure control, turn boundaries, and source
independence are preserved; unrelated lifelink behavior is unchanged.

History-only records do not perturb pre-existing event IDs or provenance ledgers for
other leave-the-battlefield mechanics. Existing authenticated LTB/Mutagen and
permanent-left counter evidence remains strict and regression-covered.

## Deterministic evidence

Focused Work Packet A/B tests: **3 passed**. The focused existing semantic,
permanent-left, Mutagen, and related regression fixtures passed (**86 passed**).
The complete repository suite passed: **1,629 passed, 10 skipped**.

Static checks passed:

- `uv run ruff check .`
- `uv run ruff format --check .`
- `git diff --check`
- `uv run python tools/validate_objective_balance_lab_baseline005.py`

The focused fixtures demonstrate full interpreter coverage, valid attack targeting,
temporary modifier and indestructible cleanup, lethal-damage and destroy prevention,
same-turn departure token creation, and rejection of departure under the wrong
controller. No smoke, isolation, matchup, or calibration games were executed.

## Coverage and remaining gate

Foot Elite and Foot Mystic's represented fragments now classify as fully executable
under the generic interpreter. The ten-deck readiness audit must be regenerated
under the post-change runtime before any additional coverage rows are considered
closed. Remaining required families include Rocksteady/Boar blocking restrictions,
mandatory sacrifice-or-discard obligations, Mutagen X/token and activation-discount
semantics, Stomped by the Foot, Mutant Chain Reaction, Tainted Treats, Cowabunga!,
Paramecia recursion, and menace grants.

**Recommendation:** READY for independent acceptance of Work Packets A/B. BLOCKED
for the next remediation packet and for all gameplay testing until HQ accepts this
checkpoint and a refreshed card-level coverage audit is published.
