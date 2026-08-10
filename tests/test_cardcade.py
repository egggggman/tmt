import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.cardcade import (
    CardModel,
    DeckProfile,
    _choose_cast,
    _pilot,
    _score,
    apply_profile_prior_condition,
    compare_runs,
    derive_card_model,
    load_roster,
    profile_prior_inventory,
    run_profile_strength_audit,
    run_round_robin,
    validate_roster,
    write_run,
)

ROOT = Path(__file__).parents[1]
ROSTER = ROOT / "cardcade" / "roster-0.1.json"
ROSTER_02 = ROOT / "cardcade" / "roster-0.2.json"


def test_beta_roster_has_ten_structurally_valid_decks():
    roster = load_roster(ROSTER)
    assert len(validate_roster(roster, ROOT)) == 10


def test_prototype_02_roster_is_structurally_valid_and_preserves_frozen_decks():
    baseline = {deck.id: deck for deck in load_roster(ROSTER)}
    candidate = {deck.id: deck for deck in load_roster(ROSTER_02)}
    assert len(validate_roster(list(candidate.values()), ROOT)) == 10
    assert {
        deck_id for deck_id in baseline if baseline[deck_id].decklist != candidate[deck_id].decklist
    } == {"donatello", "krang"}
    assert candidate["donatello"].mana_curve == {0: 23, 1: 8, 2: 9, 3: 14, 4: 6}
    assert candidate["krang"].mana_curve == {0: 22, 1: 8, 2: 15, 3: 8, 4: 3, 5: 2, 8: 2}


def test_smoke_round_robin_is_complete_balanced_and_reproducible():
    roster = load_roster(ROSTER)
    first = run_round_robin(roster, 20, 20260809)
    second = run_round_robin(roster, 20, 20260809)
    assert first == second
    assert first["total_games"] == 900
    assert len(first["pairings"]) == 45
    for pairing in first["pairings"].values():
        rows = [
            row
            for row in first["matches"]
            if {row["deck_a"], row["deck_b"]} == {pairing["deck_a"], pairing["deck_b"]}
        ]
        assert sum(row["starting_player"] == pairing["deck_a"] for row in rows) == 10
        assert sum(row["starting_player"] == pairing["deck_b"] for row in rows) == 10


def test_run_artifacts_include_ten_by_ten_matrix(tmp_path):
    result = run_round_robin(load_roster(ROSTER), 20, 7)
    write_run(result, tmp_path)
    matrix = json.loads((tmp_path / "matchup-matrix.json").read_text())
    assert len(matrix) == 10
    assert all(len(row) == 10 for row in matrix.values())


def test_odd_games_are_rejected_because_starts_cannot_be_balanced():
    with pytest.raises(ValueError, match="positive even"):
        run_round_robin(load_roster(ROSTER), 19, 7)


def test_artifact_pilots_emit_setup_payoff_and_sequencing_telemetry():
    import random

    roster = {deck.id: deck for deck in load_roster(ROSTER)}
    for deck_id in ("donatello", "krang"):
        states = [_pilot(random.Random(seed), roster[deck_id], True) for seed in range(100)]
        assert any(state["artifact_setup_cast"] >= 2 for state in states)
        assert any(state["artifact_payoffs_cast"] > 0 for state in states)
        assert all("artifact_sequencing_holds" in state for state in states)
    assert any(
        _pilot(random.Random(seed), roster["krang"], True)["affinity_mana_saved"] > 0
        for seed in range(100)
    )


def test_card_derived_model_limits_affinity_to_actual_affinity_cards():
    roster = {deck.id: deck for deck in load_roster(ROSTER)}
    krang = roster["krang"]
    affinity_cards = [card for card in krang.cards if card.affinity]
    assert {card.name for card in affinity_cards} == {"Krang, Master Mind"}
    assert all(card.mana_value == 8 and card.affinity_floor == 2 for card in affinity_cards)
    assert not next(card for card in krang.cards if card.name == "Ray Fillet, Man Ray").affinity


def test_all_ten_decks_use_actual_card_facts_and_emit_generic_roles():
    roster = load_roster(ROSTER_02)
    assert {deck.id for deck in roster} == {
        "leonardo",
        "raphael",
        "donatello",
        "michelangelo",
        "splinter",
        "april_oneil",
        "casey_jones",
        "shredder",
        "krang",
        "bebop_rocksteady",
    }
    for deck in roster:
        assert len(deck.cards) == 60
        assert all(card.card_type != "generic" for card in deck.cards)
        assert all(card.roles for card in deck.cards if card.card_type != "land")
        assert any(card.card_type == "creature" for card in deck.cards)
        assert any(card.card_type in {"interaction", "support"} for card in deck.cards)


def test_same_card_facts_derive_same_roles_and_values_without_deck_identity():
    facts = {
        "mana_value": 2,
        "mana_cost": "{1}{U}",
        "type_line": "Instant",
        "oracle_text": "Return target nonland permanent to its owner's hand. Draw a card.",
        "keywords": [],
    }
    leonardo_copy = derive_card_model("Leonardo label", facts)
    krang_copy = derive_card_model("Krang label", facts)
    assert replace(leonardo_copy, name="same") == replace(krang_copy, name="same")
    assert set(leonardo_copy.roles) == {"card_advantage", "tempo"}


def test_engine_06_outcomes_ignore_all_legacy_profile_strength_priors():
    roster = load_roster(ROSTER_02)
    neutral = apply_profile_prior_condition(roster)
    authored_run = run_round_robin(roster, 2, 20260809)
    neutral_run = run_round_robin(neutral, 2, 20260809)
    assert authored_run["decks"] == neutral_run["decks"]
    assert authored_run["pairings"] == neutral_run["pairings"]
    assert [row["winner"] for row in authored_run["matches"]] == [
        row["winner"] for row in neutral_run["matches"]
    ]


def test_affinity_discount_respects_card_colored_mana_floor():
    import random

    cards = (
        *(CardModel("Island", 0, "land") for _ in range(7)),
        *(CardModel("Setup", 1, "support", artifact_permanent=True) for _ in range(10)),
        CardModel("Payoff", 8, "creature", affinity=True, affinity_floor=2),
    )
    profile = DeckProfile(
        id="test",
        name="Test",
        decklist="",
        mana_curve={0: 7, 1: 10, 8: 1},
        creature_rate=0,
        interaction_rate=0,
        board_value=1,
        mana_value=1,
        support_value=1,
        interaction_value=1,
        synergy="",
        strategy="",
        artifact_plan="affinity",
        cards=cards,
    )
    states = [_pilot(random.Random(seed), profile, True) for seed in range(200)]
    discounted = [state for state in states if state["affinity_discount_events"]]
    assert discounted
    assert all(state["affinity_mana_saved"] <= 6 for state in discounted)
    assert all(state["affinity_spells_cast"] == 1 for state in discounted)


def test_artifact_score_uses_milestones_not_unbounded_piece_counts():
    profile = load_roster(ROSTER)[2]
    state = {
        "board_t8": 0,
        "mana_spent": 0,
        "support": 0,
        "interaction_used": 0,
        "artifact_setup_cast": 2,
        "artifact_payoffs_cast": 1,
        "affinity_mana_saved": 0,
        "mulligans": 0,
    }
    baseline = _score(profile, state)
    state.update(artifact_setup_cast=20, artifact_payoffs_cast=10)
    assert _score(profile, state) == baseline


def test_payoff_tag_does_not_force_setup_when_immediate_board_line_is_better():
    setup = CardModel("Setup", 2, "support", artifact_permanent=True)
    payoff = CardModel("Payoff", 3, "creature", artifact_payoff=True)
    profile = DeckProfile(
        id="test",
        name="Test",
        decklist="",
        mana_curve={0: 20, 2: 20, 3: 20},
        creature_rate=0,
        interaction_rate=0,
        board_value=3,
        mana_value=1,
        support_value=0.2,
        interaction_value=1,
        synergy="",
        strategy="",
        artifact_plan="invention",
        cards=(setup, payoff),
    )
    chosen, decision = _choose_cast(
        profile, [setup, payoff], [setup, payoff], artifacts=0, board=0, mana=3
    )
    assert chosen is payoff
    assert decision["legal_lines"] == 3
    assert decision["rejected_lines"] == 1
    assert "payoff_not_ready" in decision["chosen_reason"]


def test_payoff_cast_and_realization_are_distinct_and_rejections_are_reported():
    import random

    roster = {deck.id: deck for deck in load_roster(ROSTER)}
    states = [_pilot(random.Random(seed), roster["donatello"], True) for seed in range(100)]
    assert all(
        state["artifact_payoffs_realized"] <= state["artifact_payoff_cards_cast"]
        for state in states
    )
    assert any(state["artifact_payoff_lines_rejected"] > 0 for state in states)
    assert all(
        state["sequencing_rejected_lines"]
        <= state["sequencing_legal_lines"] - state["sequencing_decisions"]
        for state in states
    )


def test_interaction_is_only_valued_when_opposing_board_has_targets():
    result = run_round_robin(load_roster(ROSTER), 20, 19)
    for match in result["matches"]:
        for deck_id, state in match["players"].items():
            opponent_id = match["deck_b"] if deck_id == match["deck_a"] else match["deck_a"]
            assert state["interaction_used"] <= match["players"][opponent_id]["board_t8"]
            assert state["interaction_used"] + state["interaction_dead"] == state["interaction"]


def test_sensitivity_comparison_preserves_protocol_and_reports_diagnostics():
    roster = load_roster(ROSTER)
    run = run_round_robin(roster, 20, 23)
    comparison = compare_runs(run, run)
    assert comparison["protocol"]["total_games"] == 900
    assert all(row["shift"] == 0 for row in comparison["matchup_shifts"])
    assert set(comparison["diagnostics"]) == {"donatello", "krang", "shredder"}
    assert comparison["engine_stability_gate"]["passed"]
    assert comparison["engine_stability_gate"]["threshold"] == 0.15


def test_stability_gate_rejects_matchup_movement_over_fifteen_points():
    run = run_round_robin(load_roster(ROSTER), 20, 29)
    candidate = deepcopy(run)
    pairing = next(iter(candidate["pairings"].values()))
    pairing["deck_a_win_rate"] = 1.0 if pairing["deck_a_win_rate"] <= 0.8 else 0.0
    comparison = compare_runs(run, candidate)
    assert not comparison["engine_stability_gate"]["passed"]
    assert len(comparison["engine_stability_gate"]["threshold_exceeded"]) == 1


def test_profile_prior_inventory_is_complete_and_neutralization_uses_means():
    roster = load_roster(ROSTER_02)
    inventory = profile_prior_inventory(roster)
    assert set(inventory["fields"]) == {
        "creature_rate",
        "interaction_rate",
        "board_value",
        "mana_value",
        "support_value",
        "interaction_value",
    }
    neutral = apply_profile_prior_condition(roster)
    for field, details in inventory["fields"].items():
        assert {getattr(deck, field) for deck in neutral} == {details["neutral_value"]}
    assert [deck.decklist for deck in neutral] == [deck.decklist for deck in roster]
    assert [deck.cards for deck in neutral] == [deck.cards for deck in roster]


def test_profile_audit_preserves_protocol_and_attributes_each_prior():
    audit = run_profile_strength_audit(load_roster(ROSTER_02), 2, 20260809)
    assert audit["protocol"]["pairings"] == 45
    assert audit["protocol"]["games_per_condition"] == 90
    assert audit["protocol"]["starts_per_deck_per_pairing"] == 1
    conditions = audit["conditions"]
    assert {"baseline", "neutralized", "contracted_50pct", "amplified_150pct"} <= set(conditions)
    for field in audit["inventory"]["fields"]:
        assert f"neutralize_{field}" in conditions
    for run in conditions.values():
        assert run["total_games"] == 90
        assert all("score_delta_components" in match for match in run["matches"])


def test_calibration_artifacts_preserve_the_frozen_protocol():
    directory = ROOT / "cardcade" / "runs" / "calibration-0.1"
    configuration = json.loads((directory / "configuration.json").read_text())
    run = json.loads((directory / "run.json").read_text())
    matrix = json.loads((directory / "matchup-matrix.json").read_text())

    assert configuration["source_commit"].startswith("0dbb04a")
    assert configuration["engine_version"] == run["engine_version"] == "cardcade-0.4.0"
    assert configuration["seed"] == run["seed"] == 20260809
    assert run["games_per_pairing"] == 100
    assert run["pairing_count"] == 45
    assert run["total_games"] == 4500
    assert configuration["roster_hash"] == run["roster_hash"]
    assert len(configuration["decklists"]) == len(matrix) == 10
    for pairing in run["pairings"].values():
        rows = [
            row
            for row in run["matches"]
            if {row["deck_a"], row["deck_b"]} == {pairing["deck_a"], pairing["deck_b"]}
        ]
        assert len(rows) == 100
        assert sum(row["starting_player"] == pairing["deck_a"] for row in rows) == 50
        assert sum(row["starting_player"] == pairing["deck_b"] for row in rows) == 50
