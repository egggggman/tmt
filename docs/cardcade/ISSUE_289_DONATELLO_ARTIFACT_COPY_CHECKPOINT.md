# Issue #289 — Donatello artifact-copy checkpoint

## Runtime reconciliation

PR #347’s historical Markdown recorded runtime
`b4690f9f5609d1b9ad2a99a2ad80469d6a9b86a8e7d621bd92e88ea7545087fe`.
That value is preserved as the prior checkpoint evidence. The authenticated final
authority for this checkpoint is the runtime recorded in both new JSON artifacts:
`deeba684652abf2f0de958c97969bc3f6a5731a055d104f39ae789cf1e063a71`.

## Generic behavior

The exact Donatello clause is:

`Whenever Donatello deals combat damage to a player, create a token that's a copy of target artifact you control.`

The implementation derives this from the creature self-reference and Oracle
shape. A positive combat-damage-to-player event creates an independent triggered
ability. At stack placement, the controller receives a deterministic legal
artifact target choice. At resolution, the target must still be an authoritative
artifact controlled by that controller; otherwise the effect resolves without a
token. The copied permanent uses copiable characteristics only, enters as an
independent unattached token, and retains source/controller/event provenance.
Source departure does not erase the trigger. Counters, attachments, temporary
effects, and other noncopiable state are not copied.

## Evidence and readiness

- Coverage: 0 critical, 2 important, 0 identified blockers, 2 unbounded effects.
- Original ledger: 172 rows, unchanged identities.
- Baseline 005 deck hashes and historical runtime evidence: preserved.
- Focused deterministic fixtures: generic parsing, legal target selection,
  copied-token entry, target departure fizzles, source departure independence,
  and invariant checks.
- Frozen diagnostics: six games with exact replays. No natural Donatello combat
  damage occurred in these short diagnostics, so trigger/selection/resolution
  counts are zero; this is pilot exposure evidence only.

The remaining unbounded effects are Hamato Guardian Stance and Michelangelo
Improviser. Baseline 005 calibration remains blocked until those effects are
implemented or credibly bounded. No deck change, calibration control, merge,
promotion, or balance conclusion is authorized here.
