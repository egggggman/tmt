from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game
FRAGMENT='When this creature enters, destroy up to one target noncreature artifact.'
SOURCE=CardFact('Rock Soldiers','{2}{R}',3,'Creature - Soldier',FRAGMENT,power=3,toughness=3)
ART=CardFact('Relic','{2}',2,'Artifact')
def test_exact_and_neighbor():
    i=CardInterpreter(); assert i.rock_soldiers_etb_semantic_coverage(SOURCE,FRAGMENT).fully_supported
    assert i.rock_soldiers_etb_semantic_coverage(SOURCE,'When this creature enters, destroy target artifact.') is None
def test_entry_resolves_destroy_once():
    g=Game(([SOURCE],[ART]),seed=2300); g.begin_turn(); src=g.create_permanent(SOURCE,0); target=g.create_permanent(ART,0); g._process_creature_entered_triggers(src); assert target.zone=='graveyard'
