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

## Migration status

**Migrated:** monster identity, rarity, attributes, base stats, base skill and
passive references (Python consumes all of them; Godot consumes identity and
stats, and validates its base skill IDs).

**Still to migrate:** skill definitions, passive definitions, Resonance upgrade
rules, localized names and tooltip descriptions. Until those are migrated,
combat handlers remain implemented independently in Python and GDScript.

Run `python -m pytest -q` after editing JSON. Open the battle scene in Godot
to check parsing and battle setup as well. Data/schema changes should be
accompanied by Python contract tests and by Godot validation.
