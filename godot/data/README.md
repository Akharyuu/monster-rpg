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

## Godot Drake factories

- All five Drakes and their 12 Resonance skill variants now construct
  abilities through `skill_data.json`. Their base monster identities and
  skill slots remain in `monster_data.json`.
- The adapter translates numeric stack lookups (Burn damage/healing),
  conditional on-hit debuffs, buff stripping, removed-buff damage,
  additional Burn and cooldown resets to the existing GDScript runtime.
- Support buffs and healing ratios are also resolved from the shared
  `after_use_handlers`. Unique Cinderblood and Frozen Scales monster
  resources are still initialized by Godot; game mechanics are unchanged.
- Remaining Dullahan/Griffon/Dryad constructors still use compatibility
  code and are next in the migration.

## Complete playable skill construction

- All 24 supported battle prototypes now construct their base skills
  from shared IDs in `monster_data.json` and `skill_data.json`.
- Every Dullahan, Griffon and Dryad Resonance skill replacement now
  creates its skill using shared JSON definitions.
- Godot keeps one DamageSkill and one SupportSkill constructor inside
  the shared adapters. Soul Charges, execution/missing-health scaling,
  Named/Vulnerability, dead-monster damage, defense/speed scaling and
  Action Gauge conditions are now read from JSON.
- Engine-specific combat handlers and monster-specific resources still
  execute in GDScript; migrating those handlers and passives is separate.

## Shared passives and Resonance rules

- `passive_data.json` holds all 34 passive definitions, and
  `resonance_data.json` holds the R1-R5 upgrade rules for 12 monsters.
- Python imports both JSON documents through compatibility modules,
  restoring integer Resonance level keys.
- Godot resolves each monster's active passive IDs using the canonical
  base monster references and Resonance add/replace actions.
- Cinderblood, Frozen Scales, Soul Charges and Voidborn resource caps,
  Thunderheart, Nature's Grace, Frostborne, Final Omen, Headless Rider,
  Chilling Presence and The Hunt now consume shared passive parameters.
- Godot now applies skill replacements and additions from the same
  ordered R1-R5 JSON actions as Python. Slots are validated and converted
  from 1-based schema indices to 0-based Godot indices.
- Remaining combat-handler branches and rich tooltips are separate
  migration steps.

## Canonical tooltip descriptions

- All 68 skill tooltips (`summary`, rich-text `effects`) are stored in
  their respective `skill_data.json` records under `tooltip`.
- The eight base passive tooltips now live under `tooltip` in their
  `passive_data.json` entries. Godot reads the monster's base passive
  references to resolve them.
- Rich BBCode markup, effect ordering, and the existing UI fallback
  behavior are preserved. Combat execution still uses separate fields.
- Resonance-dependent passive tooltip compositions remain in GDScript
  until they can be represented without losing special UI behavior.

## Migration status

**Migrated:** monster identity, rarity, attributes, base stats, base skill
and passive references, and canonical skill definitions. Godot consumes shared
core skill parameters and selected handler data.

**Still to migrate:** remaining engine-specific passive/skill execution
branches, dynamic Resonance-dependent passive tooltip composition, and
localization. All skill and base-passive tooltip records are now shared.
Combat handler implementations remain independent in Python and GDScript.

Run `python -m pytest -q` after editing JSON. Open the battle scene in Godot
to check parsing and battle setup as well. Data/schema changes should be
accompanied by Python contract tests and by Godot validation.
