# Monster RPG — Combat Port Handoff

**Status: playable-monster data and combat prototype port closed for the
current roster.** Next development focus: the battle UI, pixel-art assets,
animation and visual feedback.

## What is shared between Python and Godot

- `godot/data/monster_data.json`: monster identities, stats, base kit slots.
- `godot/data/skill_data.json`: 68 abilities, effect/handler settings,
  cooldowns, targeting and presentation text.
- `godot/data/passive_data.json`: 34 passive definitions, effect settings,
  rich descriptions and Resonance tooltip variations.
- `godot/data/resonance_data.json`: the R1–R5 upgrade sequence for 12 monsters.

Python and Godot both read these files; do not recreate the data as a
second hard-coded dictionary in GDScript. Skill handler data is exposed to
Godot via `Skill.shared_definition`, `Skill.has_handler()` and
`Skill.get_handler_data()`. Monster passives are resolved by handler
from the shared `passive_definitions` dictionary.

Specialized gameplay effects still execute in the Godot combat classes.
**Sharing configurations does not mean sharing Python/GDScript executable
code**, and it is not yet a guarantee of perfect engine-to-engine parity.

## Validated playable scope

- 24 constructible battle monsters, with 84 roster/Resonance configurations.
- All existing skill IDs, active passive IDs, Resonance slots and tooltips.
- Python contract and simulation tests.
- Actual Godot 4.7.2 headless import/compilation and gameplay smoke cases:
  damage, healing, Soul Recall resurrection, Frozen Scales consumption and
  Headlong Charge ally buffs/turn order.
- A handler reference contract that flags new unrecognized handler types.

Both checks are run by `.github/workflows/validate.yml` on every push to
`main` and on pull requests. From the repository root:

```powershell
python -m pytest -q
python scripts/check_godot.py
```

For Windows without Godot on PATH, see `godot/data/README.md`.

## Intentionally not part of this port milestone

- A complete automated match-by-match parity suite between Python and
  Godot for every advanced mechanic and every randomized outcome.
- Story/campaign progression, full summoning banners, inventory and glyph
  equipment, persistence, TOA, PvP matchmaking and game economy UI.
- Localization, sprites, combat animation, sounds and final battle layout.
- Unassigned legacy passive variants (for example,
  `frostborne_shattered_fury`) that cannot currently be obtained from the
  R0–R5 monster kits.

These are future feature-development tasks, **not blockers for starting the
visual iteration of the combat screen**. When a new monster adds an unfamiliar
handler, extend the Godot executor, update its shared JSON record and add
a headless combat regression before considering it complete.

## Next milestone: visual battle overhaul

Start with a fixed battlefield layout for the two teams, establish the
pixel-art size/camera rules and sprite orientations, then replace placeholder
combat HUD artwork. Preserve the existing skill, status and action-gauge
interfaces while changing the presentation. Iterate visually with a small
representative encounter before redrawing every monster.
