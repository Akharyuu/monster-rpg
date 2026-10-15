# Shared game data

Monster RPG is migrating its data definitions to a single source of truth.
Files in this folder are imported by **both** the Python game/simulations and
the Godot front end. Do not create separate per-engine copies.

## `monster_data.json` (schema version 1)

- Each entry is keyed by a stable `monster_id`.
- `name`, `family`, `attribute`, `rarity`, level-50 reference
  `max_health`, `attack`, `defense`, `speed`, base skill IDs and
  optional passive IDs are canonical.
- Attributes use lowercase IDs: `igneous`, `abyssal`, `storm`,
  `aether`, `void`.
- Base stats are **not** pre-scaled to level 1. Godot's current prototype
  still applies its level-1 multiplier of 0.35 on construction.
- A monster named `???` is still unnamed. Godot derives a temporary label
  such as `Void Dullahan`; Python preserves the canonical placeholder.
- Python imports `MONSTER_DATA` from `game.data.monster_data`. This is
  now a compatibility loader that maps only the attribute back to its Enum.
- Godot reads `res://data/monster_data.json` in
  `PrototypeFactory._make_monster_from_data`, and checks that base skill IDs
  still match the skills the factory currently constructs.

## `skill_data.json` (schema version 1)

- Contains all 68 skill definitions, including Resonance upgrades, by ID.
- `type` and `target_type` use lowercase identifiers, such as `damage`
  and `single_enemy`.
- Python imports `SKILL_DATA` from `game.data.skill_data`, which now reads
  the shared file and restores enum values and numeric lookup-table keys.
- Godot reads this same JSON after applying Resonance, to synchronize common
  parameters and straightforward healing/buff values.
- Godot now builds the 12 Slime, Sprout, Wisp and Thornet prototypes directly
  from shared skill IDs, names, targets, cooldowns, effects and multipliers.
  Their Action Gauge, poison/stun and conditional-damage adapters are read
  from the JSON as well. Skill-based lowest-HP-ally healing percentages are
  also read from JSON (including the Dryad's Vine Barrage variants).
- More complex monsters, Resonance replacements and engine-specific
  handlers still use compatibility constructors; those will be migrated
  incrementally without changing their combat behavior.

## Migration status

**Migrated:** monster identity, rarity, attributes, base stats, base skill
and passive references, and canonical skill definitions. Godot consumes shared
core skill parameters and selected handler data.

**Still to migrate:** remaining Godot skill handler adapters, passive
definitions, Resonance upgrade rules, localized names and tooltip descriptions.
Combat handler implementations remain independent in Python and GDScript.

Run `python -m pytest -q` after editing JSON. Open the battle scene in Godot
to check parsing and battle setup as well. Data/schema changes should be
accompanied by Python contract tests and by Godot validation.
