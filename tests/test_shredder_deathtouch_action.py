import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    CardFact,
    Game,
    TemporaryKeyword,
    TriggeredAbilityObject,
    TriggerEffect,
)

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
SHREDDER = CardFact(
    "Shredder, Unrelenting",
    "{3}{B}",
    4,
    "Creature — Mutant",
    "Whenever Shredder enters or attacks, another target creature "
    "you control gains deathtouch until end of turn.",
    4,
    4,
)
BEAR = CardFact("Bear", "{1}", 1, "Creature — Bear", power=2, toughness=2)
FRAGMENT = SHREDDER.oracle_text


def game():
    g = Game(([LAND] * 60, [LAND] * 60), seed=2500)
    g.begin_turn()
    return g


def pass_priority(g):
    while g.priority_state is not None:
        if g.priority_state.resolution_pending:
            g.process_priority_resolution()
        else:
            g.execute_priority_action(g.legal_priority_actions(g.priority_state.player_index)[0])


def setup(target_controller=0):
    g = game()
    source = g.create_permanent(SHREDDER, 0, summoning_sick=False)
    target = g.create_permanent(BEAR, target_controller, summoning_sick=False)
    return g, source, target


def etb(g, source):
    g._process_creature_entered_triggers(source)
    return g.stack[-1]


def test_exact_grammar_and_neighbor_fail_closed():
    i = CardInterpreter()
    c = i.shredder_deathtouch_semantic_coverage(SHREDDER, FRAGMENT)
    assert c and c.fully_supported
    assert (
        i.shredder_deathtouch_semantic_coverage(
            SHREDDER, FRAGMENT.replace("deathtouch", "hexproof")
        )
        is None
    )


def test_etb_stack_priority_and_resolution_grant_cleanup():
    g, s, t = setup()
    a = etb(g, s)
    assert isinstance(a, TriggeredAbilityObject)
    assert a.effect is TriggerEffect.SHREDDER_DEATHTOUCH
    assert not g.has_temporary_keyword(t, TemporaryKeyword.DEATHTOUCH)
    pass_priority(g)
    assert g.has_temporary_keyword(t, TemporaryKeyword.DEATHTOUCH)
    g._perform_cleanup()
    assert not g.has_temporary_keyword(t, TemporaryKeyword.DEATHTOUCH)


@pytest.mark.parametrize("event", ["etb", "attack"])
@pytest.mark.parametrize("opponent_creature", [False, True])
def test_no_legal_target_does_not_stack_shredder_trigger(event, opponent_creature):
    g = game()
    s = g.create_permanent(SHREDDER, 0, summoning_sick=False)
    if opponent_creature:
        g.create_permanent(BEAR, 1, summoning_sick=False)

    def unexpected_target_choice(*_args):
        pytest.fail("No target chooser call is legal without candidates")

    g.counter_target_chooser = unexpected_target_choice
    if event == "etb":
        g._process_creature_entered_triggers(s)
    else:
        g.resolve_attack_pt_effects([s])

    assert not any(
        isinstance(ability, TriggeredAbilityObject)
        and ability.effect is TriggerEffect.SHREDDER_DEATHTOUCH
        for ability in g.stack
    )
    assert not g.pending_triggers


def test_source_is_not_a_legal_target():
    g, s, t = setup()
    g.counter_target_chooser = lambda _p, _s, ids: s.object_id
    with pytest.raises(ValueError, match="target chooser"):
        etb(g, s)


def test_target_leaves_or_relinks_fails_closed():
    g, s, t = setup()
    etb(g, s)
    g.put_into_graveyard(t)
    pass_priority(g)
    assert g.events[-2].get("event") != "shredder_deathtouch_granted"
    g, s, t = setup()
    etb(g, s)
    g._objects[t.object_id] = s
    with pytest.raises(ValueError, match="Shredder trigger"):
        g.resolve_top_of_stack()


def test_source_leaves_and_attack_trigger_still_resolves():
    g, s, t = setup()
    etb(g, s)
    g.put_into_graveyard(s)
    pass_priority(g)
    assert g.has_temporary_keyword(t, TemporaryKeyword.DEATHTOUCH)
    g, s, t = setup()
    g.resolve_attack_pt_effects([s])
    assert isinstance(g.stack[-1], TriggeredAbilityObject)
    assert g.stack[-1].effect is TriggerEffect.SHREDDER_DEATHTOUCH
    pass_priority(g)
    assert g.has_temporary_keyword(t, TemporaryKeyword.DEATHTOUCH)
