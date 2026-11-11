from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TemporaryKeyword, TurnStep
from tmnt_design_studio.stage002 import _drain_ordinary_step_priority

SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
TUNNEL_RATS = CardFact(
    "Tunnel Rats",
    "{1}{B}",
    2,
    "Creature — Rat",
    "{4}{B}: Return this card from your graveyard to the battlefield tapped.",
    power=2,
    toughness=2,
)
FROG_BUTLER = CardFact(
    "Frog Butler",
    "{1}{G}",
    2,
    "Creature — Frog Spirit",
    "{2}: This creature gains reach until end of turn.",
    power=2,
    toughness=2,
)
FLYER = CardFact(
    "Synthetic Flyer",
    "{1}{U}",
    2,
    "Creature — Bird",
    keywords=("Flying",),
    power=2,
    toughness=2,
)
REACH_FRAGMENT = "{2}: This creature gains reach until end of turn."


class PassUntilTargetPilot:
    def __init__(self, game, *, target_object_id, target_fragment):
        self.game = game
        self.target_object_id = target_object_id
        self.target_fragment = target_fragment
        self.used = False

    def choose_priority(self, _view, options):
        if not self.used and self._target_window_is_open():
            target = next(
                (
                    option
                    for option in options
                    if option.kind is ActionKind.ACTIVATE_ABILITY
                    and option.object_id == self.target_object_id
                    and option.oracle_fragment == self.target_fragment
                ),
                None,
            )
            if target is not None:
                self.used = True
                return target
        return next(option for option in options if option.kind is ActionKind.PASS_PRIORITY)

    def _target_window_is_open(self):
        raise NotImplementedError


class EndStepTunnelRatsPilot(PassUntilTargetPilot):
    def _target_window_is_open(self):
        return self.game.step is TurnStep.END_STEP


class AttackerPriorityReachPilot(PassUntilTargetPilot):
    def _target_window_is_open(self):
        return self.game.step is TurnStep.DECLARE_ATTACKERS


class PassPriorityPilot:
    def choose_priority(self, _view, options):
        return next(option for option in options if option.kind is ActionKind.PASS_PRIORITY)


def _advance_to_end_step(game):
    while game.step is not TurnStep.END_STEP:
        if game.step is TurnStep.COMBAT_DAMAGE:
            game.resolve_combat_damage()
        game.advance_step()


def test_stage002_naturally_offers_tunnel_rats_at_empty_end_step_priority():
    game = Game(([SWAMP, PLAINS, PLAINS, PLAINS, PLAINS] * 4, [PLAINS] * 20), seed=381385)
    game.begin_turn()
    lands = [
        game.create_permanent(card, 0, summoning_sick=False)
        for card in (SWAMP, PLAINS, PLAINS, PLAINS, PLAINS)
    ]
    source = game._create_card_object(TUNNEL_RATS, 0, "graveyard")
    game.players[0].graveyard.append(source)
    _advance_to_end_step(game)
    assert game.stack == [] and game.priority_state is None

    pilot = EndStepTunnelRatsPilot(
        game, target_object_id=source.object_id, target_fragment=TUNNEL_RATS.oracle_text
    )
    _drain_ordinary_step_priority(game, pilot)

    returned = [item for item in game.players[0].battlefield if item.card.name == "Tunnel Rats"]
    assert pilot.used
    assert len(returned) == 1 and returned[0].tapped
    assert returned[0].object_id != source.object_id
    assert source.zone == "former" and source not in game.players[0].graveyard
    assert all(land.tapped for land in lands)
    assert game.step is TurnStep.END_STEP
    assert game.priority_state is None and game.stack == []
    assert sum(event["event"] == "tunnel_rats_returned" for event in game.events) == 1
    game.check_invariants()


def test_frog_reach_is_available_after_attackers_before_blockers_on_empty_stack():
    game = Game(([PLAINS] * 20, [PLAINS] * 20), seed=382385)
    game.begin_turn()
    attacker = game.create_permanent(FLYER, 0, summoning_sick=False)
    frog = game.create_permanent(FROG_BUTLER, 1, summoning_sick=True)
    lands = [game.create_permanent(PLAINS, 1, summoning_sick=False) for _ in range(2)]

    game.advance_step()
    _drain_ordinary_step_priority(game, PassPriorityPilot())
    game.advance_step()
    attack = next(
        option
        for option in game.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    game.execute_attack_action(attack, defer_step_transition=True)
    pilot = AttackerPriorityReachPilot(
        game, target_object_id=frog.object_id, target_fragment=REACH_FRAGMENT
    )
    _drain_ordinary_step_priority(game, pilot)

    assert pilot.used
    assert game.step is TurnStep.DECLARE_ATTACKERS
    assert game._attackers_declared and game.priority_state is None
    assert frog.summoning_sick and not frog.tapped
    assert all(land.tapped for land in lands)
    assert game.has_temporary_keyword(frog, TemporaryKeyword.REACH)
    assert game.legal_block_options(attack, 1) == ()

    game.advance_step()
    assert game.step is TurnStep.DECLARE_BLOCKERS
    assert any(
        (attacker.object_id, frog.object_id) in option.blocks
        for option in game.legal_block_options(attack, 1)
    )
