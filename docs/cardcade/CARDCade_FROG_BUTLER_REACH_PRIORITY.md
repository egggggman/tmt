# Frog Butler Reach Priority Action

**Base:** accepted `main` at `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
**Scope:** expose the existing `{2}: This creature gains reach until end of
turn.` ability in an already-open nonempty-stack priority window.

The official [Magic Comprehensive Rules effective June 19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf)
rule 117.1b permits an activated ability whenever its controller has priority;
the Reach ability has no sorcery-only restriction and no tap symbol. Rule 302.6
therefore does not bar a summoning-sick Frog from using it. The engine already
implements the ability's payment, resolution, temporary keyword, cleanup,
source-departure behavior, and blocker interaction, but the stack-priority
action list omitted the action.

The candidate adds only a `GRANT_REACH_UNTIL_EOT` option generator for the
player holding an existing priority window and routes it through the existing
activated-ability executor. It verifies the two-mana payment plan before
offering the action. It does not add an empty-stack priority driver. The
current engine does not create ordinary empty-stack priority windows between
steps; that remains a separate timing-model limitation.

Deterministic tests cover action availability and resolution in an existing
stack window, summoning sickness with a non-tap cost, insufficient mana, and
previously covered expiration, source departure, and combat-blocking behavior.
No complete-game tests were run.
