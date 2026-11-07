from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game
from tmnt_design_studio.mana_ledger07 import ManaSpendingContext


LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain", "({T}: Add {R}.)")
PAID_CREATURE = CardFact(
    "Synthetic Red Hero",
    "",
    0,
    "Creature — Test Hero",
    "{R}: Synthetic Red Hero gains first strike until end of turn.",
    2,
    2,
)


def setup_paid_food():
    game = Game(([LAND] * 20, [LAND] * 20), seed=38701)
    game.begin_turn()
    source = game.create_permanent(PAID_CREATURE, 0, summoning_sick=False)
    game.floating_mana.add(
        0,
        source.object_id,
        "R",
        1,
        "restricted-red-activation-production",
        allowed_contexts={ManaSpendingContext.ACTIVATED_ABILITY},
        expiration_boundary=f"turn-{game.turn}:step-end:{game.step.value}",
    )
    game.log(
        "floating_mana_produced",
        source_id=source.object_id,
        stack_object_id="restricted-red-activation-production",
        player_index=0,
        color="R",
        quantity=1,
    )
    return game, source


def test_supported_battlefield_ability_uses_activated_ability_restricted_mana():
    game, source = setup_paid_food()
    fragment = PAID_CREATURE.oracle_text
    semantics = CardInterpreter().activated_ability_semantics(PAID_CREATURE, fragment)
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.GRANT_SELF_FIRST_STRIKE_UNTIL_EOT

    plan = game.activation_payment_plan(0, source, fragment)
    assert plan is not None
    assert plan.mana_payment is not None
    assert plan.mana_payment.spending_context is ManaSpendingContext.ACTIVATED_ABILITY
    ability = game.announce_activated_ability(0, source, fragment)
    assert ability is not None
    assert game.stack == [ability]
    assert game.floating_mana.snapshot(0, ManaSpendingContext.ACTIVATED_ABILITY) == {}
    assert game.floating_mana.consumptions(0)[0].source_event_id == (
        "restricted-red-activation-production"
    )
    game.check_invariants()
