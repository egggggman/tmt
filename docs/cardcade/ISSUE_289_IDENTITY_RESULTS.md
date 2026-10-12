# Issue 289: critical deck identity checkpoint

Stacked on draft PR #297, commit `a01c627704104883d4e2885bd37cee343338a853`.
Baseline 005 deck lists, original 172-row ledger, and all earlier checkpoint files are unchanged.

## Executed semantics

| Oracle family | General execution and evidence | Ledger result |
| --- | --- | --- |
| Attack or block: sacrifice a permanent unless you discard a card | Legal declaration creates a stack trigger. Controller chooses a legal hand card or controlled permanent at resolution. Zone changes, state-based actions, event IDs, and source-independent resolution are tested. B&R may decline to attack or block. | 1 P0 closed |
| Must be blocked if able | Legal blocker assignments maximize satisfiable block requirements while respecting restrictions, including Menace. Illegal zero-block declarations are rejected. | 1 P0 closed |
| Linked exile and attack permission | Alliance exile records source and exiled-object identity. Attack permission picks one linked card, lasts this turn, survives source removal, and obeys land, spell, target, payment, and normal timing rules. Exiled spells use priority; targetable Aura and Flash paths share the normal action machinery. | 2 P0 rows remain partial; instant and specialized cast-family breadth needs review |
| Beginning of your end step: draw per spell type cast this turn | The trigger uses the end-step event and stack. Resolution counts distinct types from actual cast announcements, including multitype spells; draw moves cards and checks state. | 1 P0 closed |

The historical Raphael identifiers in the existing state and telemetry remain for compatibility. Runtime recognition uses self-reference and Oracle clauses rather than card or deck names. The legacy pilot view schema remains sealed; the pilot can select engine-issued actions outside its hand in postcombat main.

## Provenance and readiness

- Previous runtime: `9d263bb6151f3060dcacd59482f14a35d7759f1f0daae2a54c28c6dc0cb561a2`.
- New runtime: `4d1dd3aa00758c8bf150878bcc0379e0a92f9c604ca2339c478d3a1b533e24bb`.
- Original ledger SHA-256: `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`.
- Prior checkpoint SHA-256: `6fb3f210a07ac02282e7cffbfad619682282b49794b058fa10e216ebaa74275e`.
- Reproducible overlay: `PYTHONPATH=src:tools python tools/report_issue289_identity.py` produces `ISSUE_289_IDENTITY_CHECKPOINT.json` with all 172 rows, before/after counts, and three closed rows.
- Frozen-deck diagnostic: `PYTHONPATH=src:tools python tools/run_issue289_identity_smoke.py` produces `ISSUE_289_IDENTITY_SMOKE.json`; four mirrored games and four matching replays, no runtime errors. Three April end-step resolutions occurred in one diagnostic. The small samples are execution checks, not balance evidence. Focused fixture replays exercise B&R and Raphael event paths directly.

**Remaining:** 30 critical (P0), 68 important (P1), 2 partial. Next highest-impact work includes Raphael's remaining linked casting coverage, shared interaction for Cool but Rude, and B&R's Tainted Treats removal. Classification is about execution, not deck strength.

**Checkpoint acceptance:** pending complete regression and remote CI.
**Baseline 005 calibration readiness:** BLOCKED. No control games were run, no deck was revised, and no baseline was promoted.
