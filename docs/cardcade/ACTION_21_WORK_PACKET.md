# Cardcade Action #21 — Work Packet

Authoritative implementation task: GitHub Issue #71.

Base at authorization: `12c5722466f6aea2ee690119e93ebcae2ee05b0e`.

Implement only the bounded Oracle-derived artifact-entry trigger represented by Donatello, Way with Machines: when an artifact enters the battlefield under the relevant controller, put exactly one +1/+1 counter on the authoritative source permanent through existing trigger / Stack / Priority machinery.

Preserve source incarnation and zone identity; fail closed for stale, relinked, wrong-controller, nonartifact, or nonauthoritative objects. Preserve reconstructive entry-event → trigger → Stack → resolution → counter evidence.

Do not broaden into arbitrary enters triggers, other payloads, other counters, deck/Pilot changes, calibration, balance claims, Prototype 0.3, broad simulation, GUI/runner work, or Action #22.

Required handoff: focused and regression tests, full pytest, Ruff check/format, `git diff --check`, exact base/candidate SHAs, explicit exclusions, near-neighbor limitations, and a PR for independent acceptance.

Implementation worker self-check is not independent acceptance. Required flow: implement → validate → document → hand off.
