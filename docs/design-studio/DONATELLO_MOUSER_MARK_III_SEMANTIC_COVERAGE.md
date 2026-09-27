# Mouser Mark III Semantic Coverage

Status: implementation candidate only; Prototype 0.3c is still not created and no
smoke is authorized by this artifact.

## Exact card text

The authoritative snapshot records Mouser Mark III as an artifact creature with
mana cost `{1}{U/R}`, mana value 2, power/toughness 2/3, and this Oracle text:

> This creature can't attack unless you control another artifact.

## Support added

Cardcade now represents the two narrow reusable requirements needed for this card:

- the authorized `{U/R}` hybrid symbol is parsed as one mana requirement payable
  by either listed color; unrelated hybrid pairs remain outside this narrow
  compatibility slice;
- the legal attacker generator recognizes the exact generic restriction and checks
  for another artifact permanent controlled by the attacker’s controller.

Hybrid payment selection is deterministic and supports both floating mana and
untapped land sources. A qualifying artifact must be a current controlled
battlefield permanent, and the Mouser itself is excluded. Artifact creatures and
noncreature artifacts qualify; cards in an opponent’s battlefield, hand, or
graveyard do not.

The restriction is checked at attacker declaration. It does not affect blocking,
and does not bypass summoning sickness, tapped-creature legality, Flying, Reach,
first strike, or double strike handling. AcceptancePilot was not changed; it
continues to receive engine-generated legal attacker options.

## Tests

Focused coverage includes:

- blue and red payment of `{U/R}`;
- insufficient hybrid payment and unchanged generic-cost behavior;
- the authoritative Mouser card data, cast, and 2/3 battlefield characteristics;
- no attack when Mouser is alone;
- enabling by another controlled artifact creature or noncreature artifact;
- exclusion of opponent, hand, and graveyard artifacts;
- multiple Mousers seeing one another;
- normal blocking without another artifact;
- dynamic enable/disable as an artifact enters or leaves;
- preservation of summoning-sickness legality.

## Remaining limitations

This change does not implement Chrome Dome, Skateboard, Equipment attachment,
artifact-copy effects, token engines, or any additional Donatello semantics. It
does not redesign AcceptancePilot and does not claim that Donatello is balanced.

Prototype 0.3c remains uncreated. A separate Design Studio deck PR must make and
validate the authorized candidate package after this semantic implementation is
merged; the compact diagnostic and frozen 240-game smoke remain later gates.

The repository's frozen preflight source identities were refreshed for the two
modified Cardcade source files. The smoke schedule, deck inputs, and calibration
evidence were not changed, and no smoke was run.
