# Post–Action #18 measurement and Action #19 proposal

Proposal only. No Action #19 implementation or acceptance is authorized by this report.

## Baseline and measurement

Executed from `C:\Projects\tmt` on clean `main` at `0f679bb766695bbfe0ea634785e97b934f239464` after a fast-forward pull. The only subsequent changes are these evidence artifacts. Action #18 — Alliance is banked in that baseline.

Used the smallest existing frozen multi-matchup coverage-aware matrix: Acceptance Stage #002. It ran **16 distinct games / 32 executions**, two byte-equivalent executions per game. Pairings, each in canonical and reversed orientation:

| Pairing | Seeds |
| --- | --- |
| Donatello P0.2 / Krang P0.2 | 7201, 7202 |
| Michelangelo P0.1 / Bebop-Rocksteady P0.1 | 7211, 7212 |
| Splinter P0.1 / Shredder P0.1 | 7221, 7222 |
| April O'Neil P0.1 / Casey Jones P0.1 | 7231, 7232 |

This is an eight-deck, four-matchup screening sample, not full-roster coverage. Leonardo and Raphael are absent. No historical Stage 0.2 totals were reused. No calibration, balance analysis, 900-game smoke, or Prototype 0.3 work was run.

## Recoverable results

Existing reconciliation classified **17 EXECUTED, 37 REACHED/UNSUPPORTED, and 147 PRESENT/UNREACHED occurrence records**. Occurrences are the existing runner's game-scoped semantic occurrence IDs, not a claim about every repeated trigger or potential opportunity. Duplicate executions are not counted twice. Twelve exact unsupported semantic keys remain; five games contain no reached/unsupported occurrence records. This does not establish full rules coverage or balance validity.

Ranked by occurrences, then games, then matchups; ties use semantic key solely for reproducibility. Solo-clearance is derived from existing occurrence evidence: games in which the named semantic is the sole unsupported semantic key. It is a screening opportunity, not a prediction that gameplay after implementation will be clean. It is not a native runner metric.

| Rank | Frozen corpus member | Occurrences | Games | Matchups | Solo-clearance games |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | Utrom Scientists | 9 | 6 | 2 | 0 |
| 2 | Fugitive Droid | 6 | 4 | 1 | 0 |
| 3 | Donatello, Way with Machines | 4 | 3 | 1 | 0 |
| 4 | Ravenous Robots | 3 | 3 | 1 | 0 |
| 5 | Ray Fillet, Man Ray | 3 | 3 | 1 | 0 |
| 6 | Casey Jones, Jury-Rig Justiciar | 3 | 3 | 1 | 0 |
| 7 | Rock Soldiers | 2 | 2 | 1 | 0 |
| 8 | Stockman, Mad Fly-entist | 2 | 2 | 1 | 0 |
| 9 | Casey Jones, Vigilante | 2 | 2 | 1 | 0 |
| 10 | Courier of Comestibles | 1 | 1 | 1 | 1 |
| 11 | Zoo Escapees | 1 | 1 | 1 | 1 |
| 12 | Shredder, Unrelenting | 1 | 1 | 1 | 1 |

The JSON ranking preserves every counted game/occurrence/object ID, affected matchup, solo-clearance game ID, limitation, and exact Oracle fragment. Ranks refer to exact semantics, not whole-card implementation completeness.

## Proposed Action #19 — Stun counters

**ACTION →** Stun counters, bounded to Utrom Scientists' existing frozen ETB tap-and-stun effect. This leads this sample on occurrences, games, and matchups (9 / 6 / 2). It has zero solo-clearance games, so this is a reach-based leverage recommendation, not a guaranteed game-clearance optimum. Other single-semantic games exist, as the table shows. This sample does not establish a global optimum or implementation effort estimate.

**RESOLVE →** Recognize the exact frozen fragment below through generic self-ETB and target machinery. The trigger may choose zero or one legal creature. Freeze and authenticate its target incarnation, recheck at resolution, then tap that creature and put one stun counter on it. An already-tapped legal target can receive the counter; an absent or illegal target cannot transfer the effect. Represent stun counters authoritatively and consume one counter instead of untapping when a supported untap event would untap that permanent. Multiple counters must not all disappear on one such event. Preserve the ordinary trigger/Stack/Priority and deterministic choice lifecycle. These are proposed acceptance requirements, not implemented claims.

**EXCLUSIONS →** No universal counter or replacement-effect framework; no additional untap cards, proliferate, counter transfer/removal abilities, other tap-and-freeze grammars, keyword subsystems, Pilot tuning, deck revisions, or unrelated mechanics. Preserve unsupported near-neighbor behavior. Any interaction requiring an absent rules subsystem must remain an explicit dependency rather than silently approximated.

**ACCEPTANCE →** Exact frozen corpus/grammar recognition; generic non-card-specific execution; deterministic zero/one target choice; normal Stack/Priority; legal already-tapped targets; stale, replaced, wrong-zone, fabricated, and resolution-illegal targets fail closed; authoritative counter state and evidence; one-counter-per-untap prevention and later normal untapping; source departure does not invalidate a legitimately stacked trigger; supported untap paths all observe the counter; near neighbors remain unsupported; focused and full regressions plus Ruff and diff checks. Authenticate conformance execution evidence against the actual target/tap/counter history. Review counter interactions against the rules before implementation; do not expand scope to conceal unsupported interactions.

**BALANCE →** No balance claim or authorization. Results are coverage screening only; `balance_valid` is false in the ranking artifact. No win-rate recommendation or Prototype 0.3 authorization.

**READY →** Ready for owner review of this bounded proposal, conditional on agreement with the sample limitation and final rules/interaction scoping. Not ready to implement or bank without separate authorization. No gameplay branch has been created.

## Exact ranked Oracle fragments

1. **Utrom Scientists** (`89793c8c-98a3-4621-ad3d-cfc5949c65da:0:0:37ce5a4d7762180cb84023a47a371810a02d0a49c7788466bf3c6c2192346f20`)

   When this creature enters, tap up to one target creature and put a stun counter on it. (If a permanent with a stun counter would become untapped, remove one from it instead.)

2. **Fugitive Droid** (`c04d4fd4-e5aa-431d-824b-8bc94245f103:0:1:734e0672683610a83b78e8a0cd92475a9ba9c52ca4cc2561b936d1c60dd246b4`)

   {U}, Sacrifice this creature: Counter target spell that targets an artifact or creature you control.

3. **Donatello, Way with Machines** (`194af2be-50c7-484b-bdd3-402bad70335b:0:1:c0a2c27a75ab4696bfe690ea52e8591e793a4dfe7bc043acea3ce08eb2e4664a`)

   Whenever an artifact you control enters, put a +1/+1 counter on Donatello.

4. **Ravenous Robots** (`45873747-f2a4-4d83-9492-bfc97df7b605:0:1:60414c2470ad86b814ab1396706899ac58bd8aa80da483f36a9fbaa0e52e0f48`)

   {R}, {T}: Creature tokens you control gain haste until end of turn.

5. **Ray Fillet, Man Ray** (`698098b8-b8e4-4e88-b13a-6b039579d192:0:2:c3d749f2944441da05d1bfdf5ec98a4f4712e5d98b049f111d930d89bd2f354b`)

   {2}, Remove a +1/+1 counter from a creature you control: Draw a card.

6. **Casey Jones, Jury-Rig Justiciar** (`b4c4fdb9-e034-49c0-9f7f-07e8cae19eb2:0:1:07ec8ec16239068dc5d083fa3ddc78c542eee5ff4b90ca04eee1ec256a57c526`)

   When Casey Jones enters, look at the top four cards of your library. You may reveal an artifact card from among them and put it into your hand. Put the rest on the bottom of your library in a random order.

7. **Rock Soldiers** (`0217da8e-e74f-4f5c-ab75-f17600f94405:0:0:edb6c7a32990c8d16dec8c331e2bc43c8b09663b4fed3f9c76f734eb164eab6b`)

   When this creature enters, destroy up to one target noncreature artifact.

8. **Stockman, Mad Fly-entist** (`baa4cb1b-6fb5-46df-9cdd-54421ee0fc88:0:1:80c534db71c996b429b08e64b997f14ac0b547d0c015ad4204f2a12ae7beca31`)

   When Stockman enters, draw a card, then discard a card.

9. **Casey Jones, Vigilante** (`bc163b5a-0b1a-4257-8c07-5c7d5284015f:0:0:7205e4e46cce5b88d12207eff8a2435295a2a546050ce011603d754b1ee66e79`)

   When Casey Jones enters, draw three cards. At the beginning of your next upkeep, discard three cards at random.

10. **Courier of Comestibles** (`049d8b06-db90-4b9c-8195-d987b3ef1005:0:0:c038838a15cd2f48c196ee63c451e981f95ccfbabed4dff825563eac88c3e003`)

   When this creature enters, you may search your library for a Food card, reveal it, put it into your hand, then shuffle. If you don't put a card into your hand this way, create a Food token. (It's an artifact with "{2}, {T}, Sacrifice this token: You gain 3 life.")

11. **Zoo Escapees** (`107e9ada-4e2e-4032-addd-274bca956621:0:0:c34b0291b7b6b26a718ba7762560229497d1d607ff6957bff6ec9a35a1feeb5e`)

   When this creature leaves the battlefield, create a Mutagen token. (It's an artifact with "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.")

12. **Shredder, Unrelenting** (`59d96fc0-6580-43c2-8c6a-dcf983644561:0:2:a3dba7b962f1000f873f91c782ddd88cc2ffd1f4791a70743be63d6dcb7e38ad`)

   Whenever Shredder enters or attacks, another target creature you control gains deathtouch until end of turn.

## Commands and validation

Baseline commands: `git status --porcelain`, `git branch --show-current`, `git switch main`, `git pull --ff-only origin main`, `git rev-parse HEAD`, `git status --porcelain`.

Measurement command:

```powershell
uv run python scripts/run_acceptance_stage_002.py --execute --output docs/cardcade/POST_ACTION_18_ACCEPTANCE_STAGE_002_RESULTS.json
```

Validation command: `uv run pytest tests/test_stage002_runner.py -q` — **46 passed**, with the existing pytest cache-write permission warning. The existing `validate_stage_result_evidence` passed on the saved JSON; the entire manifest equals a fresh `build_stage_manifest` from this exact checkout. All 16 duplicate pairs match; zero conformance stops and zero invariant violations. No engine or runner edits were needed. Full pytest was not rerun for this evidence-only task.

Read-only inspection used `rg`, `Get-Content`, and inline `uv run python -` to inspect occurrence/presence records, map semantic keys to corpus fragments, and aggregate the ranking. The ranking algorithm counts each unsupported occurrence once per distinct game, tracks sets of game/pairing IDs, and identifies singleton unsupported-key games. All contributing IDs are serialized for reproduction from raw evidence. Standard SHA-256 and the existing manifest/report/aggregate validation establish integrity; this is local validation, not independent acceptance.

Raw artifact: `POST_ACTION_18_ACCEPTANCE_STAGE_002_RESULTS.json` (11,936,567 bytes).
SHA-256: `2daa13956f2a8571d3d77f6c48d9f373ec516ad206eb47e387d78c42b72796ec` (also saved in `.json.sha256`).
Manifest digest: `3cd6f1228865db55c4c17530d033592effa7624ebe1e5e4ee73a42c54c6d67b9`.
Aggregate digest: `5982c907c312dfa3cf41298ab8855ea31c89c2ad310dd0e13bf86a3cbd034134`.
Ranking: `POST_ACTION_18_UNSUPPORTED_RANKING.json`.

Artifacts are saved locally under `docs/cardcade`; they have not been committed or pushed. Stop after proposal: no implementation, merge, self-acceptance, deck changes, or calibration.
