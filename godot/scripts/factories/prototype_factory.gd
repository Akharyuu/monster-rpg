class_name PrototypeFactory
extends RefCounted

const MonsterScript = preload("res://scripts/models/monster.gd")
const DamageSkillScript = preload("res://scripts/models/damage_skill.gd")
const SupportSkillScript = preload("res://scripts/models/support_skill.gd")

const LEVEL_ONE_MULTIPLIER := 0.35
const SHARED_MONSTER_DATA_PATH := "res://data/monster_data.json"
const SHARED_SKILL_DATA_PATH := "res://data/skill_data.json"

static var _shared_monsters: Dictionary = {}
static var _shared_skills: Dictionary = {}


static func _get_shared_monsters() -> Dictionary:
    if not _shared_monsters.is_empty():
        return _shared_monsters

    var raw_json: String = FileAccess.get_file_as_string(
        SHARED_MONSTER_DATA_PATH
    )
    var parsed: Variant = JSON.parse_string(raw_json)

    if not (parsed is Dictionary):
        push_error("Invalid shared monster JSON")
        return {}

    if int(parsed.get("schema_version", -1)) != 1:
        push_error("Unsupported monster data schema version")
        return {}

    var records: Variant = parsed.get("monsters", {})

    if not (records is Dictionary):
        push_error("Missing monsters in shared JSON")
        return {}

    _shared_monsters = records
    return _shared_monsters


# Core skill parameters use the same data file as the Python engine.
# Godot-specific handler execution is retained during the next migration.
static func _get_shared_skills() -> Dictionary:
    if not _shared_skills.is_empty():
        return _shared_skills

    var raw_json: String = FileAccess.get_file_as_string(
        SHARED_SKILL_DATA_PATH
    )
    var parsed: Variant = JSON.parse_string(raw_json)

    if not (parsed is Dictionary):
        push_error("Invalid shared skill JSON")
        return {}
    if int(parsed.get("schema_version", -1)) != 1:
        push_error("Unsupported skill data schema version")
        return {}

    var records: Variant = parsed.get("skills", {})
    if not (records is Dictionary):
        push_error("Missing skills in shared JSON")
        return {}

    _shared_skills = records
    return _shared_skills


static func _sync_skill_from_shared_data(skill) -> bool:
    var definitions: Dictionary = _get_shared_skills()
    var skill_id: String = str(skill.skill_id)

    if not definitions.has(skill_id):
        push_error("Missing shared skill id: %s" % skill_id)
        return false

    var entry: Dictionary = definitions[skill_id]
    var skill_type: String = str(entry.get("type", ""))

    if skill_type == "damage":
        if not (skill is DamageSkill):
            push_error("Expected damage skill: %s" % skill_id)
            return false
    elif skill_type == "healing" or skill_type == "support":
        if not (skill is SupportSkill):
            push_error("Expected support skill: %s" % skill_id)
            return false
    else:
        push_error("Unknown skill type: %s" % skill_id)
        return false

    skill.skill_name = str(entry["name"])
    skill.cooldown = int(entry["cooldown"])
    skill.target_type = str(entry["target_type"])

    if skill is DamageSkill:
        skill.multiplier = float(entry["multiplier"])
        skill.hits = int(entry.get("hits", 1))
        skill.hit_multipliers = entry.get("hit_multipliers", [])
        skill.scaling_stat = str(entry.get("scaling_stat", "attack"))
        skill.hit_distribution = str(entry.get("hit_distribution", ""))
        skill.repeated_target_damage = entry.get(
            "repeated_target_damage", {}
        )
        skill.resolve_hits_by_round = bool(
            entry.get("resolve_hits_by_round", false)
        )

        # Handler-adapter effects can exist only in Godot; overwrite
        # them only when the shared data declares direct effects.
        if entry.has("effects"):
            skill.effects = entry["effects"]

        # Simple JSON handler adapters shared by the early monster set
        # (and reused by existing advanced monster constructors).
        for handler_config in entry.get("on_hit_handlers", []):
            var handler_id: String = str(
                handler_config.get("handler", "")
            )
            var gauge_data: Dictionary = handler_config.get("data", {})
            if handler_id == "reduce_action_gauge":
                skill.action_gauge_reduction_per_hit = float(
                    gauge_data.get("amount", 0.0)
                )
                skill.action_gauge_reduction_chance = float(
                    gauge_data.get("chance", 1.0)
                )
            elif handler_id == "reduce_action_gauge_if_debuff":
                skill.action_gauge_reduction_if_debuff_id = str(
                    gauge_data.get("effect_id", "")
                )
                skill.action_gauge_reduction_if_debuff_amount = float(
                    gauge_data.get("amount", 0.0)
                )
            elif handler_id == "reduce_action_gauge_with_threshold_bonus":
                skill.action_gauge_reduction_per_hit = float(
                    gauge_data.get("amount", 0.0)
                )
                skill.action_gauge_threshold = float(
                    gauge_data.get("threshold", -1.0)
                )
                skill.action_gauge_bonus_reduction = float(
                    gauge_data.get("bonus_amount", 0.0)
                )
            elif handler_id == "gain_action_gauge_if_target_low_hp":
                skill.action_gauge_gain_if_target_low_hp_threshold = float(
                    gauge_data.get("health_threshold", 0.0)
                )
                skill.action_gauge_gain_if_target_low_hp_amount = float(
                    gauge_data.get("amount", 0.0)
                )

        for handler_config in entry.get("before_hit_handlers", []):
            if str(handler_config.get("handler", "")) == "apply_named_and_vulnerability":
                var named_data: Dictionary = handler_config.get("data", {})
                skill.apply_named_before_hit = true
                skill.named_turns = int(named_data.get("named_turns", 0))
                skill.vulnerability_chance = float(
                    named_data.get("vulnerability_chance", 0.0)
                )
                skill.vulnerability_turns = int(
                    named_data.get("vulnerability_turns", 0)
                )

        for handler_config in entry.get("after_use_handlers", []):
            if str(handler_config.get("handler", "")) == "heal_lowest_hp_ally":
                var healing_data: Dictionary = handler_config.get("data", {})
                skill.heal_lowest_hp_ally_ratio = float(
                    healing_data.get("healing_hp_ratio", 0.0)
                )

        var damage_data: Dictionary = entry.get(
            "damage_handler_data", {}
        )
        match str(entry.get("damage_handler", "")):
            "damage_if_condition":
                var condition: Dictionary = damage_data.get(
                    "condition", {}
                )
                match str(condition.get("type", "")):
                    "target_has_debuff":
                        skill.conditional_required_debuff_id = str(
                            condition.get("effect_id", "")
                        )
                    "target_has_any_debuff":
                        skill.conditional_requires_any_debuff = true

                skill.conditional_damage_multiplier = float(
                    damage_data.get("damage_multiplier", 1.0)
                )
                var per_hit: Dictionary = damage_data.get(
                    "multipliers_by_hit", {}
                )
                if not per_hit.is_empty():
                    var multipliers: Array = []
                    for hit_number in range(1, skill.hits + 1):
                        multipliers.append(float(
                            per_hit.get(str(hit_number), 1.0)
                        ))
                    skill.conditional_hit_damage_multipliers = multipliers

            "damage_by_missing_health":
                skill.max_missing_health_bonus = float(
                    damage_data.get("max_bonus_damage", 0.0)
                )
            "execute_below_health_threshold":
                skill.execute_health_threshold = float(
                    damage_data.get("health_threshold", 0.0)
                )
                skill.execute_defense_ignore_ratio = float(
                    damage_data.get("defense_ignore_ratio", 0.0)
                )
            "damage_for_soul_charges":
                skill.damage_per_soul_charge = float(
                    damage_data.get("damage_per_charge", 0.0)
                )
                skill.max_soul_charges = int(
                    damage_data.get("max_charges", 0)
                )
                skill.use_consumed_soul_charges = bool(
                    damage_data.get("use_consumed_charges", false)
                )
            "damage_for_dead_monsters":
                skill.damage_per_dead_monster = float(
                    damage_data.get("damage_per_dead_monster", 0.0)
                )
                skill.max_dead_monsters = int(
                    damage_data.get("max_dead_monsters", 0)
                )
                skill.max_dead_monster_bonus = float(
                    damage_data.get("max_bonus_damage", 0.0)
                )
            "damage_with_bonus_stat":
                skill.bonus_stat = str(
                    damage_data.get("bonus_stat", "")
                )
                skill.bonus_stat_scaling = float(
                    damage_data.get("bonus_scaling", 0.0)
                )
            "damage_with_speed_scaling":
                skill.speed_damage_scaling = float(
                    damage_data.get("speed_scaling", 0.0)
                )
    elif skill_type == "healing" or skill_type == "support":
        var buffs: Array = []
        for handler_config in entry.get("after_use_handlers", []):
            var handler_id: String = str(
                handler_config.get("handler", "")
            )
            var handler_data: Dictionary = handler_config.get(
                "data", {}
            )
            if handler_id == "heal_all_allies":
                skill.healing_hp_ratio = float(
                    handler_data.get("healing_hp_ratio", 0.0)
                )
            elif handler_id == "apply_aoe_buff":
                buffs.append({
                    "effect_id": str(handler_data["effect_id"]),
                    "turns": int(handler_data["turns"])
                })
        skill.buffs_to_apply = buffs

    return true


static func _sync_monster_skills(monster) -> bool:
    for skill in monster.skills:
        if not _sync_skill_from_shared_data(skill):
            return false
    return true


# Generic constructor for monsters whose basic skills are fully
# described by skill_data.json. Richer handlers will migrate gradually.
# JSON stores numeric map keys as strings, while the GDScript damage
# handlers use integer stack-count lookups.
static func _int_keyed_skill_values(raw: Dictionary) -> Dictionary:
    var values: Dictionary = {}
    for key in raw:
        values[int(key)] = float(raw[key])
    return values


# Build effects/handler adapters from canonical definitions. Gameplay
# execution remains in DamageSkill and BattleController.
static func _create_shared_damage_skill(skill_id: String):
    var definitions: Dictionary = _get_shared_skills()
    if not definitions.has(skill_id):
        push_error("Unknown shared damage skill: %s" % skill_id)
        return null

    var entry: Dictionary = definitions[skill_id]
    if str(entry.get("type", "")) != "damage":
        push_error("Expected shared damage skill: %s" % skill_id)
        return null

    var effects: Array = entry.get("effects", []).duplicate(true)
    var strip_hit_index: int = -1

    for handler_config in entry.get("on_hit_handlers", []):
        var handler_id: String = str(
            handler_config.get("handler", "")
        )
        var handler_data: Dictionary = handler_config.get("data", {})

        if handler_id == "apply_debuff_on_hit_indices":
            # The Godot execution engine consumes targeted debuffs from
            # DamageSkill.effects, rather than from a Python handler.
            effects.append({
                "effect_id": str(handler_data["effect_id"]),
                "chance": float(handler_data.get("chance", 1.0)),
                "turns": int(handler_data["turns"]),
                "hit_indices": handler_data["hit_indices"]
            })
        elif handler_id == "strip_buffs_on_hit":
            strip_hit_index = int(handler_data["hit_index"])

    var burn_damage: Dictionary = {}
    var burn_healing: Dictionary = {}
    var damage_handler: String = str(entry.get("damage_handler", ""))
    var damage_data: Dictionary = entry.get("damage_handler_data", {})

    if damage_handler == "damage_for_burn_stacks":
        burn_damage["multipliers_by_stacks"] = (
            _int_keyed_skill_values(
                damage_data.get("multipliers_by_stacks", {})
            )
        )
        if damage_data.has("ignore_defense_at_stacks"):
            burn_damage["ignore_defense_at_stacks"] = int(
                damage_data["ignore_defense_at_stacks"]
            )

    for handler_config in entry.get("after_skill_handlers", []):
        if str(handler_config.get("handler", "")) == "consume_burn_and_heal":
            var handler_data: Dictionary = handler_config.get("data", {})
            burn_healing["heal_by_stacks"] = (
                _int_keyed_skill_values(
                    handler_data.get("heal_by_stacks", {})
                )
            )

    var skill = DamageSkillScript.new(
        skill_id,
        str(entry["name"]),
        float(entry["multiplier"]),
        int(entry.get("hits", 1)),
        entry.get("hit_multipliers", []),
        str(entry.get("scaling_stat", "attack")),
        int(entry["cooldown"]),
        effects,
        burn_damage,
        burn_healing,
        str(entry["target_type"])
    )

    skill.strip_buffs_hit_index = strip_hit_index

    if damage_handler == "damage_for_removed_buffs":
        skill.damage_per_removed_buff = float(
            damage_data.get("damage_per_removed_buff", 0.0)
        )
        skill.removed_buff_damage_hit_indices = damage_data.get(
            "affected_hit_indices", []
        )

    for handler_config in entry.get("after_skill_handlers", []):
        var handler_id: String = str(
            handler_config.get("handler", "")
        )
        var handler_data: Dictionary = handler_config.get("data", {})

        if handler_id == "add_burn_if_target_started_with_burn":
            skill.add_burn_if_started_with_burn = true
            skill.extra_burn_stacks = int(
                handler_data.get("stacks", 1)
            )
            skill.extra_burn_turns = int(
                handler_data.get("turns", 3)
            )
        elif handler_id == "reset_cooldown_by_burn_stacks":
            skill.reset_skill_slot_if_burn_stacks = int(
                handler_data.get("skill_slot", 0)
            )
            skill.reset_skill_required_burn_stacks = int(
                handler_data.get("required_stacks", 0)
            )

    return skill


static func _create_shared_skill(skill_id: String):
    var definitions: Dictionary = _get_shared_skills()
    if not definitions.has(skill_id):
        push_error("Unknown shared skill: %s" % skill_id)
        return null

    var entry: Dictionary = definitions[skill_id]
    var skill_type: String = str(entry.get("type", ""))

    if skill_type == "damage":
        return _create_shared_damage_skill(skill_id)

    if skill_type == "healing" or skill_type == "support":
        var buffs: Array = []
        for handler_config in entry.get("after_use_handlers", []):
            if str(handler_config.get("handler", "")) == "apply_aoe_buff":
                var data: Dictionary = handler_config.get("data", {})
                buffs.append({
                    "effect_id": str(data["effect_id"]),
                    "turns": int(data["turns"])
                })
        return SupportSkillScript.new(
            skill_id,
            str(entry["name"]),
            int(entry["cooldown"]),
            buffs,
            str(entry["target_type"])
        )

    push_error("Unsupported shared skill type: %s" % skill_id)
    return null


# The non-Drake advanced prototypes now use their JSON skill IDs.
# Soul Charges are stored on the monster, not on skill definitions.
static func _create_shared_advanced_monster(monster_id: String):
    var records: Dictionary = _get_shared_monsters()
    if not records.has(monster_id):
        push_error("Unknown shared advanced monster: %s" % monster_id)
        return null

    var skills: Array = []
    for skill_id in records[monster_id].get("skills", []):
        var skill = _create_shared_skill(str(skill_id))
        if skill == null:
            return null
        skills.append(skill)

    var monster = _make_monster_from_data(monster_id, skills)
    if monster == null:
        return null

    if monster_id == "dullahan_aether":
        monster.combat_resources["soul_charges"] = 0
        monster.combat_resource_maximums["soul_charges"] = 5

    return monster


static func _create_shared_drake(monster_id: String):
    var monsters: Dictionary = _get_shared_monsters()
    if not monsters.has(monster_id):
        push_error("Unknown shared Drake: %s" % monster_id)
        return null

    var skills: Array = []
    for skill_id in monsters[monster_id].get("skills", []):
        var skill = _create_shared_skill(str(skill_id))
        if skill == null:
            return null
        skills.append(skill)

    var monster = _make_monster_from_data(monster_id, skills)
    if monster == null:
        return null

    # Monster-specific passive resources are not skill definitions.
    if monster_id == "drake_igneous":
        monster.on_hit_effects = [
            {
                "effect_id": "burn",
                "chance": 0.35,
                "turns": 2,
                "stacks": 1
            }
        ]
    elif monster_id == "drake_abyssal":
        monster.combat_resources["frozen_scales"] = 0
        monster.combat_resource_maximums["frozen_scales"] = 3

    return monster


static func _create_shared_damage_monster(monster_id: String):
    var monsters: Dictionary = _get_shared_monsters()
    if not monsters.has(monster_id):
        push_error("Unknown shared monster: %s" % monster_id)
        return null

    var skills: Array = []
    for skill_id in monsters[monster_id].get("skills", []):
        var skill = _create_shared_damage_skill(str(skill_id))
        if skill == null:
            return null
        skills.append(skill)

    return _make_monster_from_data(monster_id, skills)


static func _make_monster_from_data(
    monster_id: String,
    skills: Array
):
    var definitions: Dictionary = _get_shared_monsters()

    if not definitions.has(monster_id):
        push_error("Missing shared monster id: %s" % monster_id)
        return null

    var entry: Dictionary = definitions[monster_id]
    var base_skill_ids: Array = entry.get("skills", [])

    if base_skill_ids.size() != skills.size():
        push_error("Shared skill count mismatch for %s" % monster_id)
        return null

    for index in range(skills.size()):
        if skills[index].skill_id != str(base_skill_ids[index]):
            push_error(
                "Shared skill ID mismatch for %s at slot %d"
                % [monster_id, index + 1]
            )
            return null

    # Some canonical names are intentionally placeholders. Until
    # they are named, derive the display name from attribute/family.
    var display_name: String = str(entry["name"])

    if display_name == "???":
        display_name = "%s %s" % [
            str(entry["attribute"]).capitalize(),
            str(entry["family"])
        ]

    return MonsterScript.new(
        monster_id,
        display_name,
        str(entry["family"]),
        str(entry["attribute"]),
        int(entry["rarity"]),
        _scaled(float(entry["max_health"])),
        _scaled(float(entry["attack"])),
        _scaled(float(entry["defense"])),
        _scaled(float(entry["speed"])),
        skills,
        LEVEL_ONE_MULTIPLIER
    )



static func create_level_one_monster(
    monster_id: String,
    resonance: int = 0
):
    var monster = null

    match monster_id:
        "drake_igneous":
            monster = _create_shared_drake(monster_id)
        "drake_abyssal":
            monster = _create_shared_drake(monster_id)
        "drake_aether":
            monster = _create_shared_drake(monster_id)
        "drake_storm":
            monster = _create_shared_drake(monster_id)
        "drake_void":
            monster = _create_shared_drake(monster_id)
        "dullahan_void":
            monster = _create_shared_advanced_monster(monster_id)
        "dullahan_aether":
            monster = _create_shared_advanced_monster(monster_id)
        "dullahan_igneous":
            monster = _create_shared_advanced_monster(monster_id)
        "dullahan_abyssal":
            monster = _create_shared_advanced_monster(monster_id)
        "dullahan_storm":
            monster = _create_shared_advanced_monster(monster_id)
        "thornet_igneous":
            monster = _create_shared_damage_monster(monster_id)
        "thornet_abyssal":
            monster = _create_shared_damage_monster(monster_id)
        "thornet_storm":
            monster = _create_shared_damage_monster(monster_id)
        "wisp_igneous":
            monster = _create_shared_damage_monster(monster_id)
        "wisp_abyssal":
            monster = _create_shared_damage_monster(monster_id)
        "wisp_storm":
            monster = _create_shared_damage_monster(monster_id)
        "sprout_igneous":
            monster = _create_shared_damage_monster(monster_id)
        "sprout_abyssal":
            monster = _create_shared_damage_monster(monster_id)
        "sprout_storm":
            monster = _create_shared_damage_monster(monster_id)
        "griffon_igneous":
            monster = _create_shared_advanced_monster(monster_id)
        "dryad_storm":
            monster = _create_shared_advanced_monster(monster_id)
        "slime_storm":
            monster = _create_shared_damage_monster(monster_id)
        "slime_abyssal":
            monster = _create_shared_damage_monster(monster_id)
        "slime_igneous":
            monster = _create_shared_damage_monster(monster_id)
        _:
            push_error("Unknown prototype monster id: %s" % monster_id)
            return null

    monster.resonance = clampi(resonance, 0, 5)
    _apply_resonance(monster)
    if not _sync_monster_skills(monster):
        return null
    _attach_skill_descriptions(monster)
    _attach_passive_description(monster)
    return monster


static func _attach_skill_descriptions(monster) -> void:
    var tooltip_data := {
        "draconic_claw": {
            "summary": "A precise claw strike against one enemy.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]30% chance[/b] to apply [color=#ff7777]Defense Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "scorching_breath": {
            "summary": "Engulfs all enemies in a two-hit breath attack.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases with the target's [color=#ff7777]Burn[/color] stacks."
                }
            ]
        },

        "scorching_breath_afterburn": {
            "summary": "Engulfs all enemies in a two-hit breath attack and feeds existing flames.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases with the target's [color=#ff7777]Burn[/color] stacks."
                },
                {
                    "kind": "debuff",
                    "text": "If the target is already affected by [color=#ff7777]Burn[/color], applies [b]1 additional Burn stack[/b] for [b]3 turns[/b]."
                }
            ]
        },

        "flame_devourer": {
            "summary": "Consumes the target's flames to empower the strike and restore the caster.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Deals increased damage based on [color=#ff7777]Burn[/color] stacks."
                },
                {
                    "kind": "heal",
                    "text": "Consumes the Burn present before the attack and [color=#76e6a8]heals the caster[/color]."
                }
            ]
        },

        "flame_devourer_rekindled": {
            "summary": "Consumes the target's flames to empower the strike and restore the caster.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Deals increased damage based on [color=#ff7777]Burn[/color] stacks."
                },
                {
                    "kind": "heal",
                    "text": "Consumes the Burn present before the attack and [color=#76e6a8]heals the caster[/color]."
                },
                {
                    "kind": "special",
                    "text": "Consuming [b]3 Burn stacks[/b] resets [b]Scorching Breath[/b]."
                }
            ]
        },

        "flame_devourer_incineration": {
            "summary": "Consumes the target's flames in a devastating finishing strike.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Deals increased damage based on [color=#ff7777]Burn[/color] stacks."
                },
                {
                    "kind": "damage",
                    "text": "At [b]3 Burn stacks[/b], ignores the target's Defense."
                },
                {
                    "kind": "heal",
                    "text": "Consumes the Burn present before the attack and [color=#76e6a8]heals the caster[/color]."
                },
                {
                    "kind": "special",
                    "text": "Consuming [b]3 Burn stacks[/b] resets [b]Scorching Breath[/b]."
                }
            ]
        },

        "rime_breath": {
            "summary": "A freezing breath that strikes the entire enemy team twice.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Each hit has a [b]50% chance[/b] to apply [color=#ff7777]Speed Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "rime_breath_frigid": {
            "summary": "A freezing breath that strikes the entire enemy team twice.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Each hit reduces [b]10% Action Gauge[/b] if the target is affected by [color=#ff7777]Speed Break[/color]."
                },
                {
                    "kind": "debuff",
                    "text": "Each hit has a [b]50% chance[/b] to apply [color=#ff7777]Speed Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "glacial_collapse": {
            "summary": "Crushes the enemy team under a sudden glacial impact.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Reduces each target's [b]Action Gauge by 10%[/b]."
                },
                {
                    "kind": "control",
                    "text": "Targets with [color=#ff7777]Speed Break[/color] can be [color=#ff7777]Frozen[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "glacial_collapse_absolute_zero": {
            "summary": "Crushes the enemy team under an absolute glacial collapse.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Reduces each target's [b]Action Gauge by 10%[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "Targets with [color=#ff7777]Speed Break[/color] are [color=#ff7777]Frozen[/color] for [b]1 turn[/b], ignoring Resistance."
                },
                {
                    "kind": "debuff",
                    "text": "Other targets have a [b]75% chance[/b] to be [color=#ff7777]Frozen[/color] for [b]1 turn[/b], ignoring Resistance."
                }
            ]
        },

        "lightning_rush": {
            "summary": "Rushes one enemy with two rapid lightning-infused strikes.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "After attacking, grants the caster [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "lightning_rush_blitz": {
            "summary": "Rushes one enemy with two rapid lightning-infused strikes.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "After attacking, grants the caster [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "After attacking, gains [b]15% Action Gauge[/b]."
                }
            ]
        },

        "stormbreak": {
            "summary": "Unleashes ten lightning strikes across random enemies.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Hits every living enemy at least once before distributing the remaining strikes randomly."
                },
                {
                    "kind": "control",
                    "text": "A target hit [b]3+ times[/b] has a [b]50% chance[/b] to be [color=#ff7777]Stunned[/color]."
                },
                {
                    "kind": "damage",
                    "text": "Repeated hits after the fifth deal reduced damage. The first hit gains bonus damage while the caster has [color=#70c8ff]Speed Up[/color]."
                }
            ]
        },

        "stormbreak_requiem": {
            "summary": "Unleashes ten lightning strikes across random enemies, followed by a final sweeping discharge.",
            "effects": [
                {
                    "kind": "control",
                    "text": "A target hit [b]3+ times[/b] has a [b]50% chance[/b] to be [color=#ff7777]Stunned[/color] for [b]1 turn[/b]."
                },
                {
                    "kind": "damage",
                    "text": "After the ten strikes, unleashes an additional attack against all living enemies."
                }
            ]
        },

        "sovereign_breath": {
            "summary": "Blasts all enemies with sovereign aether.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Applies [color=#ff7777]Silence[/color] for [b]1 turn[/b]."
                },
                {
                    "kind": "special",
                    "text": "Silence chance starts at [b]30%[/b] and gains [b]+10% per caster buff[/b], up to [b]80%[/b]."
                }
            ]
        },

        "sovereign_breath_subjugation": {
            "summary": "Overwhelms the enemy team with sovereign aether, suppressing their ability to act.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]50% chance[/b] to apply [color=#ff7777]Silence[/color] for [b]1 turn[/b] ([b]+10% chance[/b] for each buff on the caster)."
                }
            ]
        },

        "heavens_decree": {
            "summary": "Empowers the entire allied team with celestial authority.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "Grants [color=#70c8ff]Attack Up[/color], [color=#70c8ff]Immunity[/color] and [color=#70c8ff]Veil[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "heavens_decree_apotheosis": {
            "summary": "Elevates the entire allied team under overwhelming celestial authority.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "Grants [color=#70c8ff]Attack Up[/color], [color=#70c8ff]Immunity[/color] and [color=#70c8ff]Veil[/color] for [b]3 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "Grants the caster an [b]extra turn[/b]."
                }
            ]
        },

        "null_rend": {
            "summary": "Tears into one enemy with two void-infused strikes.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "The second hit has a [b]60% chance[/b] to apply [color=#ff7777]Oblivion[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "null_rend_obliterate": {
            "summary": "Tears into one enemy with two increasingly destructive void strikes.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "The second hit has an [b]80% chance[/b] to apply [color=#ff7777]Oblivion[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "null_rend_annihilation": {
            "summary": "Tears into one enemy with two void strikes that can erase the fallen from battle.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "The second hit has an [b]80% chance[/b] to apply [color=#ff7777]Oblivion[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "If this skill defeats a target that was already affected by [color=#ff7777]Oblivion[/color], the target becomes [color=#d9a6ff]Banished[/color]."
                },
                {
                    "kind": "special",
                    "text": "A [color=#d9a6ff]Banished[/color] monster cannot be revived."
                }
            ]
        },

        "dismantle": {
            "summary": "Disassembles the enemy team's defenses over three sweeping hits.",
            "effects": [
                {
                    "kind": "special",
                    "text": "[b]Hit 1:[/b] strips enemy buffs."
                },
                {
                    "kind": "damage",
                    "text": "[b]Hits 2-3:[/b] deal increased damage for every buff removed."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hits 2-3:[/b] each has a [b]30% chance[/b] to apply [color=#ff7777]Defense Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "dismantle_decimation": {
            "summary": "Disassembles the enemy team's defenses over three sweeping hits.",
            "effects": [
                {
                    "kind": "special",
                    "text": "[b]Hit 1:[/b] strips enemy buffs."
                },
                {
                    "kind": "damage",
                    "text": "[b]Hits 2-3:[/b] deal increased damage for every buff removed."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hits 2-3:[/b] each has a [b]50% chance[/b] to apply [color=#ff7777]Defense Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "needle_rush": {
            "summary": "Strikes one enemy twice with venomous needles.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Each hit has a [b]35% chance[/b] to apply [color=#ff7777]Poison[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "fever_sting": {
            "summary": "Drives three fevered stings into one enemy.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Deals increased damage if the target is already affected by [color=#ff7777]Poison[/color]."
                }
            ]
        },

        "numbing_sting": {
            "summary": "Pierces one enemy twice with numbing venom.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Each hit has a [b]25% chance[/b] to apply [color=#ff7777]Poison[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "If this skill applies Poison, has a [b]60% chance[/b] to apply [color=#ff7777]Stun[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "swarm_pierce": {
            "summary": "Overwhelms one enemy with three rapid piercing attacks.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "If the target already has a debuff when the skill begins, each successive hit deals more damage."
                }
            ]
        },

        "will_o_glow": {
            "summary": "Launches a flickering spirit flame at one enemy.",
            "effects": [
                {
                    "kind": "control",
                    "text": "[b]60% chance[/b] to reduce the target's [b]Action Gauge by 10%[/b]."
                }
            ]
        },

        "nurturing_lash": {
            "summary": "Strikes one enemy with a living vine, then restores a wounded ally.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "After attacking, heals the living ally with the lowest HP ratio for [b]5% of the caster's Max HP[/b]."
                }
            ]
        },

        "rending_talons": {
            "summary": "Rends one enemy with a powerful talon strike.",
            "effects": []
        },

        "searing_gale": {
            "summary": "Unleashes a scorching gale that tears through all enemies in two waves.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Each hit has a [b]50% chance[/b] to reduce the target's [b]Action Gauge by 20%[/b]."
                }
            ]
        },

        "meteor_dive": {
            "summary": "Crashes down on one enemy with overwhelming speed.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases according to the caster's Speed."
                }
            ]
        },

        "meteor_dive_violent_crash": {
            "summary": "Crashes down on one enemy with overwhelming speed.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases according to the caster's Speed."
                },
                {
                    "kind": "debuff",
                    "text": "If the target has less than [b]50% Action Gauge[/b], has a [b]75% chance[/b] to apply [color=#ff7777]Stun[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "meteor_dive_terminal_impact": {
            "summary": "Crashes down on one enemy with overwhelming speed.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases according to the caster's Speed."
                },
                {
                    "kind": "debuff",
                    "text": "Applies [color=#ff7777]Stun[/color] for [b]1 turn[/b] if the target has less than [b]50% Action Gauge[/b] ([b]70%[/b] if the caster has [color=#70c8ff]Speed Up[/color])."
                }
            ]
        },

        "searing_gale_turbulence": {
            "summary": "Unleashes a scorching gale that tears through all enemies in two waves.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Each hit has a [b]75% chance[/b] to reduce the target's [b]Action Gauge by 20%[/b]."
                }
            ]
        },

        "searing_gale_heatstorm": {
            "summary": "Unleashes an intensified scorching gale across the enemy team.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Each hit has a [b]75% chance[/b] to reduce the target's [b]Action Gauge by 30%[/b]."
                },

            ]
        },

        "vine_barrage": {
            "summary": "Strikes one enemy with three rapid vines.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "After attacking, heals the living ally with the lowest HP ratio for [b]8% of the caster's Max HP[/b]."
                }
            ]
        },

        "vine_barrage_nourishment": {
            "summary": "Strikes one enemy with three rapid vines, then channels stronger restorative energy.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "After attacking, heals the living ally with the lowest HP ratio for [b]15% of the caster's Max HP[/b]."
                }
            ]
        },

        "breath_of_the_grove": {
            "summary": "Channels restorative energy through the entire allied team.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "Heals all living allies for [b]25% of the caster's Max HP[/b]."
                }
            ]
        },

        "breath_of_the_grove_sanctuary": {
            "summary": "Bathes the allied team in restorative energy and protective grace.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "Heals all living allies for [b]35% of the caster's Max HP[/b]."
                },
                {
                    "kind": "buff",
                    "text": "Grants [color=#70c8ff]Immunity[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "breath_of_the_grove_evergreen": {
            "summary": "Floods the allied team with lasting restorative energy.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "Heals all living allies for [b]35% of the caster's Max HP[/b]."
                },
                {
                    "kind": "buff",
                    "text": "Grants [color=#70c8ff]Immunity[/color] for [b]1 turn[/b]."
                },
                {
                    "kind": "buff",
                    "text": "Grants [color=#70c8ff]Regrowth[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "gale_pursuit": {
            "summary": "Sweeps through the enemy team in a burst of storm speed.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Reduces each enemy's [b]Action Gauge by 20%[/b]."
                }
            ]
        },

        "gale_pursuit_crosswind": {
            "summary": "Sweeps through the enemy team with a disruptive crosswind.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Reduces each enemy's [b]Action Gauge by 25%[/b] ([b]35%[/b] if they have more than [b]50% Action Gauge[/b])."
                }
            ]
        },

        "gale_pursuit_tempest": {
            "summary": "Sweeps through the enemy team and drives the allied team forward.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Reduces each enemy's [b]Action Gauge by 25%[/b] ([b]35%[/b] if they have more than [b]50% Action Gauge[/b])."
                },
                {
                    "kind": "buff",
                    "text": "Grants all allies [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "headlong_charge": {
            "summary": "Accelerates the Dullahan and pulls an ally into the fight.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "Grants the caster [color=#70c8ff]Attack Up[/color] and [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "Increases the living ally with the lowest Action Gauge by [b]20%[/b]."
                }
            ]
        },

        "headlong_charge_rally": {
            "summary": "Rallies the Dullahan and the ally furthest from taking a turn.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "Grants the caster and the selected ally [color=#70c8ff]Attack Up[/color] and [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "Increases that ally's [b]Action Gauge by 30%[/b]."
                }
            ]
        },

        "headlong_charge_stampede": {
            "summary": "Launches a coordinated charge that immediately brings an ally into action.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "Grants the caster and the selected ally [color=#70c8ff]Attack Up[/color] and [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "Increases that ally's [b]Action Gauge by 30%[/b] and makes them take the next turn."
                }
            ]
        },

        "spectral_shackles": {
            "summary": "Binds one enemy with two spectral strikes.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]Hit 1:[/b] 50% chance to apply [color=#ff7777]Speed Break[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hit 2:[/b] 50% chance to apply [color=#ff7777]Attack Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "spectral_shackles_binding": {
            "summary": "Binds one enemy more tightly with two spectral strikes.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]Hit 1:[/b] 70% chance to apply [color=#ff7777]Speed Break[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hit 2:[/b] 70% chance to apply [color=#ff7777]Attack Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "spectral_shackles_lockdown": {
            "summary": "Locks one enemy down with two spectral strikes.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]Hit 1:[/b] 90% chance to apply [color=#ff7777]Speed Break[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hit 2:[/b] 90% chance to apply [color=#ff7777]Attack Break[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "control",
                    "text": "If both debuffs are applied, reduces the target's [b]Action Gauge by 20%[/b]."
                }
            ]
        },

        "inescapable_fate": {
            "summary": "Condemns one enemy to an inescapable fate.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Extends all extendable debuffs on the target by [b]1 turn[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "If the target has at least [b]3 debuffs[/b], applies [color=#ff7777]Silence[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "inescapable_fate_ironbound": {
            "summary": "Condemns one enemy with a strike strengthened by the Dullahan's Defense.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage also scales with the caster's Defense."
                },
                {
                    "kind": "debuff",
                    "text": "Extends all extendable debuffs on the target by [b]1 turn[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "If the target has at least [b]3 debuffs[/b], applies [color=#ff7777]Silence[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "relentless_pursuit": {
            "summary": "Relentlessly hunts down a wounded enemy with two strikes.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases as the target loses Health."
                }
            ]
        },

        "relentless_pursuit_blood_trail": {
            "summary": "Relentlessly hunts down a wounded enemy with two increasingly dangerous strikes.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases as the target loses Health."
                },
                {
                    "kind": "special",
                    "text": "Each hit against a target below [b]50% HP[/b] grants [b]20% Action Gauge[/b]."
                }
            ]
        },

        "death_sentence": {
            "summary": "Delivers a lethal single-target strike.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Partially ignores Defense if the target is below [b]25% HP[/b]."
                }
            ]
        },

        "death_sentence_execution": {
            "summary": "Delivers a lethal strike designed to execute weakened enemies.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Partially ignores Defense if the target is below [b]33% HP[/b]."
                }
            ]
        },

        "death_sentence_massacre": {
            "summary": "Executes a weakened enemy and immediately continues the hunt.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Partially ignores Defense if the target is below [b]33% HP[/b]."
                },
                {
                    "kind": "special",
                    "text": "If this skill defeats an enemy, immediately uses [b]Relentless Pursuit[/b] against the living enemy with the lowest HP ratio."
                }
            ]
        },

        "soulpiercer": {
            "summary": "Pierces one enemy with condensed soul energy.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases with each [color=#d9a6ff]Soul Charge[/color], up to [b]5[/b]."
                }
            ]
        },

        "soulpiercer_ascension": {
            "summary": "Pierces one enemy with concentrated soul energy.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases more strongly with each [color=#d9a6ff]Soul Charge[/color], up to [b]5[/b]."
                }
            ]
        },

        "beyond_the_veil": {
            "summary": "Releases stored souls in a four-hit attack against all enemies.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Consumes all [color=#d9a6ff]Soul Charges[/color] before attacking."
                },
                {
                    "kind": "damage",
                    "text": "Damage increases with each consumed Soul Charge."
                }
            ]
        },

        "beyond_the_veil_soul_recall": {
            "summary": "Releases stored souls in a four-hit attack against all enemies.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Consumes all [color=#d9a6ff]Soul Charges[/color] before attacking."
                },
                {
                    "kind": "damage",
                    "text": "Damage increases with each consumed Soul Charge."
                }
            ]
        },

        "beyond_the_veil_convergence": {
            "summary": "Releases a convergence of stored souls in a four-hit attack against all enemies.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Consumes all [color=#d9a6ff]Soul Charges[/color] before attacking."
                },
                {
                    "kind": "damage",
                    "text": "Damage increases with each consumed Soul Charge."
                }
            ]
        },

        "severing_blade": {
            "summary": "A heavy single-target slash.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]30% chance[/b] to apply [color=#ff7777]Heal Block[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "spinal_scourge": {
            "summary": "Sweeps through all enemies with three brutal strikes.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases for every monster that has died in battle."
                }
            ]
        },

        "spinal_scourge_ossuary": {
            "summary": "Sweeps through all enemies with three strikes empowered by the dead.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases for every monster defeated in the battle."
                }
            ]
        },

        "deaths_gaze": {
            "summary": "Names one enemy for death before delivering a devastating strike.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Applies [color=#d9a6ff]Named[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "Applies [color=#ff7777]Vulnerability[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "deaths_gaze_last_name": {
            "summary": "Names one enemy for death before delivering a devastating strike.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Applies [color=#d9a6ff]Named[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "Applies [color=#ff7777]Vulnerability[/color] for [b]3 turns[/b]."
                }
            ]
        },

        "ooze_slam": {
            "summary": "Slams into one enemy.",
            "effects": []
        }
    }

    for skill in monster.skills:
        var data: Dictionary = tooltip_data.get(
            skill.skill_id,
            {}
        )

        skill.tooltip_summary = str(
            data.get("summary", skill.description)
        )

        skill.tooltip_effects = data.get(
            "effects",
            []
        )

        skill.description = skill.tooltip_summary

static func _attach_passive_description(monster) -> void:
    var passive_data := {
        "drake_igneous": {
            "name": "Cinderblood",
            "summary": "Each landed hit can ignite the target.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Each hit has a [b]35% chance[/b] to apply [color=#ff7777]Burn[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "drake_abyssal": {
            "name": "Frozen Scales",
            "summary": "Builds Frozen Scales through successful Freezes, then consumes them to fortify the caster.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Each enemy Frozen by [b]Glacial Collapse[/b] grants [b]1 Frozen Scale[/b], up to [b]3[/b]."
                },
                {
                    "kind": "buff",
                    "text": "Before casting Glacial Collapse at [b]3/3[/b], consumes all scales and grants [color=#70c8ff]Defense Up[/color] and [color=#70c8ff]Immunity[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "drake_storm": {
            "name": "Thunderheart",
            "summary": "Converts bonus Speed into offensive power.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases by [b]0.3%[/b] for every point of Speed above the base value."
                }
            ]
        },

        "drake_aether": {
            "name": "Celestial Authority",
            "summary": "Turns enemy aggression into control over the flow of battle.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "When hit, has a [b]30% chance[/b] to apply [color=#ff7777]Attack Break[/color] to the attacker for [b]2 turns[/b]."
                }
            ]
        },

        "drake_void": {
            "name": "Bottomless Hunger",
            "summary": "Feeds on buffs removed from enemies.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "For each enemy buff removed, heals [b]10% Max HP[/b]."
                },
                {
                    "kind": "special",
                    "text": "For each enemy buff removed, gains [b]8% Action Gauge[/b]."
                }
            ]
        },

        "dullahan_abyssal": {
            "name": "Chilling Presence",
            "summary": "Extends the enemy team's debuffs after every turn.",
            "effects": [
                {
                    "kind": "special",
                    "text": "After this monster's turn, extends [b]1 random extendable debuff[/b] on each living enemy by [b]1 turn[/b]."
                },
                {
                    "kind": "special",
                    "text": "[color=#ff7777]Stun[/color] and [color=#ff7777]Freeze[/color] cannot be extended."
                }
            ]
        },

        "dullahan_aether": {
            "name": "Soul Vessel",
            "summary": "Collects Soul Charges through combat and empowers soul-based attacks.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Gains [b]1 Soul Charge[/b] after using a damage skill, up to [b]5[/b]."
                },
                {
                    "kind": "special",
                    "text": "Gains [b]1 Soul Charge[/b] whenever any monster dies."
                },
                {
                    "kind": "special",
                    "text": "[b]Beyond the Veil[/b] consumes all stored Soul Charges before attacking."
                }
            ]
        },

        "dullahan_void": {
            "name": "Headless Rider",
            "summary": "Empowers the Dullahan while it has a Named target.",
            "effects": [
                {
                    "kind": "special",
                    "text": "While [color=#d9a6ff]Headless[/color], gains [b]+20% Speed[/b]."
                },
                {
                    "kind": "special",
                    "text": "While [color=#d9a6ff]Headless[/color], cannot be Silenced unless affected by [color=#ff7777]Oblivion[/color]."
                }
            ]
        }
    }

    monster.passive_tooltip = passive_data.get(
        monster.monster_id,
        {}
    )

    if monster.monster_id == "dullahan_aether":
        var soul_vessel_data: Dictionary = {
            "name": (
                "Soul Vessel: Requiem"
                if monster.resonance >= 4
                else (
                    "Soul Vessel: Last Rites"
                    if monster.resonance >= 1
                    else "Soul Vessel"
                )
            ),
            "summary": "Collects Soul Charges and converts them into offensive or restorative power.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Gains [b]1 Soul Charge[/b] after using a damage skill, up to [b]5[/b]."
                },
                {
                    "kind": "special",
                    "text": (
                        "Gains [b]2 Soul Charges[/b] whenever any monster dies."
                        if monster.resonance >= 4
                        else "Gains [b]1 Soul Charge[/b] whenever any monster dies."
                    )
                }
            ]
        }

        if monster.resonance >= 1:
            soul_vessel_data["effects"].append(
                {
                    "kind": "special",
                    "text": "[b]Severing Blade[/b] grants [b]1 additional Soul Charge[/b] when used against a target below [b]50% HP[/b]."
                }
            )

        if monster.resonance >= 2:
            soul_vessel_data["effects"].append(
                {
                    "kind": "special",
                    "text": "At [b]5 Soul Charges[/b], unlocks [color=#d9a6ff]Soul Recall[/color]."
                }
            )

        monster.passive_tooltip = soul_vessel_data
        monster.passive_tooltips = [
            soul_vessel_data
        ]

    if monster.monster_id == "dullahan_void":
        var headless_data: Dictionary = {
            "name": (
                "Deathless Rider"
                if monster.resonance >= 4
                else (
                    "Headless Rider: Unbound"
                    if monster.resonance >= 1
                    else "Headless Rider"
                )
            ),
            "summary": (
                "Defies lethal blows while hunting a Named foe."
                if monster.resonance >= 4
                else "Empowers the Dullahan while it has a Named target."
            ),
            "effects": [
                {
                    "kind": "special",
                    "text": (
                        "While [color=#d9a6ff]Headless[/color], gains [b]+30% Speed[/b]."
                        if monster.resonance >= 1
                        else "While [color=#d9a6ff]Headless[/color], gains [b]+20% Speed[/b]."
                    )
                },
                {
                    "kind": "special",
                    "text": "While [color=#d9a6ff]Headless[/color], cannot be Silenced unless affected by [color=#ff7777]Oblivion[/color]."
                }
            ]
        }

        if monster.resonance >= 4:
            headless_data["effects"].append(
                {
                    "kind": "special",
                    "text": "While [color=#d9a6ff]Headless[/color], survives lethal damage with [b]1 HP[/b]. After the attack, cleanses all debuffs and loses [color=#d9a6ff]Headless[/color]. [b]6-turn cooldown[/b]."
                }
            )

        if monster.resonance >= 4:
            headless_data["internal_cooldown_id"] = (
                "deathless_rider"
            )

        monster.passive_tooltip = headless_data
        monster.passive_tooltips = [
            headless_data
        ]

        if monster.resonance >= 5:
            monster.passive_tooltips.append(
                {
                    "name": "Death's Gaze: Death March",
                    "summary": "Carries the death sentence forward when a Named enemy falls.",
                    "effects": [
                        {
                            "kind": "special",
                            "text": "When the [color=#d9a6ff]Named[/color] target dies, the living enemy with the lowest HP ratio becomes [color=#d9a6ff]Named[/color] for [b]2 turns[/b]."
                        },
                        {
                            "kind": "debuff",
                            "text": "Applies [color=#ff7777]Vulnerability[/color] to the new target for [b]3 turns[/b]."
                        }
                    ]
                }
            )

    if monster.monster_id == "dullahan_abyssal":
        if monster.resonance >= 3:
            monster.passive_tooltip = {
                "name": "Chilling Presence: Suffocation",
                "summary": "Deepens the enemy team's existing debuffs after every turn.",
                "effects": [
                    {
                        "kind": "special",
                        "text": "After this monster's turn, extends up to [b]2 random extendable debuffs[/b] on each living enemy by [b]1 turn[/b]."
                    },
                    {
                        "kind": "special",
                        "text": "[color=#ff7777]Stun[/color] and [color=#ff7777]Freeze[/color] cannot be extended."
                    }
                ]
            }

    if (
        monster.monster_id == "dullahan_storm"
        and monster.resonance >= 2
    ):
        monster.passive_tooltip = {
            "name": "The Hunt",
            "summary": "Steals momentum from the enemy closest to taking a turn.",
            "effects": [
                {
                    "kind": "special",
                    "text": "After this monster's turn, steals up to [b]20% Action Gauge[/b] from the living enemy with the highest Action Gauge."
                }
            ]
        }

    if monster.monster_id == "drake_void":
        var bottomless_data: Dictionary = passive_data.get(
            "drake_void",
            {}
        )

        monster.passive_tooltips = []
        if not bottomless_data.is_empty():
            monster.passive_tooltips.append(
                bottomless_data
            )
            monster.passive_tooltip = bottomless_data

        if monster.resonance >= 2:
            var voidborn_data: Dictionary = {
                "name": (
                    "Voidborn: Transcendence"
                    if monster.resonance >= 3
                    else "Voidborn"
                ),
                "summary": "Feeds on stripped power until the Void Drake erupts into a protected state.",
                "effects": [
                    {
                        "kind": "special",
                        "text": "Each enemy buff removed grants [b]1 Voidborn stack[/b], up to [b]5[/b]."
                    },
                    {
                        "kind": "buff",
                        "text": (
                            "At [b]5 Voidborn stacks[/b], consumes all stacks to cleanse all debuffs and grant [color=#70c8ff]Invincibility[/color] for [b]2 turns[/b]."
                            if monster.resonance >= 3
                            else "At [b]5 Voidborn stacks[/b], consumes all stacks and grants [color=#70c8ff]Invincibility[/color] for [b]2 turns[/b]."
                        )
                    }
                ]
            }

            monster.passive_tooltips.append(
                voidborn_data
            )

    if (
        monster.monster_id == "dullahan_igneous"
        and monster.resonance >= 2
    ):
        monster.passive_tooltip = {
            "name": (
                "Final Omen: Fulfilled"
                if monster.resonance >= 4
                else "Final Omen"
            ),
            "summary": "Preys on wounded enemies that try to recover.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "When an enemy below [b]50% HP[/b] is healed, gains [color=#70c8ff]Attack Up[/color] for [b]1 turn[/b]."
                }
            ]
        }

        if monster.resonance >= 4:
            monster.passive_tooltip["effects"].append(
                {
                    "kind": "special",
                    "text": "Enemies below [b]50% HP[/b] receive reduced healing."
                }
            )

    if monster.monster_id == "drake_storm":
        var thunderheart_data: Dictionary = {
            "name": (
                "Thunderheart: Overclocked"
                if monster.resonance >= 3
                else "Thunderheart"
            ),
            "summary": "Converts bonus Speed into offensive power.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases according to the monster's bonus Speed."
                }
            ]
        }

        if monster.resonance >= 3:
            thunderheart_data["effects"].append(
                {
                    "kind": "special",
                    "text": "Bonus Speed also increases Crit Rate."
                }
            )

        monster.passive_tooltips = [
            thunderheart_data
        ]
        monster.passive_tooltip = thunderheart_data

        if monster.resonance >= 1:
            var short_circuit_data: Dictionary = {
                "name": (
                    "Short Circuit: Chain Reaction"
                    if monster.resonance >= 4
                    else "Short Circuit"
                ),
                "summary": "Turns Speed Up into a chance to disrupt enemies.",
                "effects": [
                    {
                        "kind": "debuff",
                        "text": "While affected by [color=#70c8ff]Speed Up[/color], S1 and S2 hits have a [b]10% chance[/b] to apply [color=#ff7777]Stun[/color] for [b]1 turn[/b]."
                    }
                ]
            }

            if monster.resonance >= 4:
                short_circuit_data["effects"].append(
                    {
                        "kind": "special",
                        "text": "Successfully applying Stun reduces [b]Stormbreak[/b]'s cooldown by [b]1 turn[/b]."
                    }
                )

            monster.passive_tooltips.append(
                short_circuit_data
            )

    if monster.monster_id == "drake_aether":
        var authority_data: Dictionary = {
            "name": (
                "Celestial Authority: Ascendance"
                if monster.resonance >= 2
                else "Celestial Authority"
            ),
            "summary": "Punishes enemies that strike the Aether Drake.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": (
                        "When hit, has a [b]50% chance[/b] to apply [color=#ff7777]Attack Break[/color] to the attacker for [b]2 turns[/b]."
                        if monster.resonance >= 2
                        else "When hit, has a [b]30% chance[/b] to apply [color=#ff7777]Attack Break[/color] to the attacker for [b]2 turns[/b]."
                    )
                }
            ]
        }

        if monster.resonance >= 2:
            authority_data["effects"].append(
                {
                    "kind": "special",
                    "text": "On success, grants [b]20% Action Gauge[/b] to the living ally with the most buffs."
                }
            )

        monster.passive_tooltips = [
            authority_data
        ]
        monster.passive_tooltip = authority_data

        if monster.resonance >= 1:
            var divine_grace_data: Dictionary = {
                "name": (
                    "Divine Grace: Enlightenment"
                    if monster.resonance >= 4
                    else "Divine Grace"
                ),
                "summary": "Blesses allies whenever this monster grants them buffs.",
                "effects": [
                    {
                        "kind": "heal",
                        "text": "Each buff applied by this monster heals the target for [b]5% Max HP[/b]."
                    }
                ]
            }

            if monster.resonance >= 4:
                divine_grace_data["effects"].append(
                    {
                        "kind": "special",
                        "text": "Also grants the caster [b]+25% Accuracy[/b]."
                    }
                )

            monster.passive_tooltips.append(
                divine_grace_data
            )

    if monster.monster_id == "drake_igneous":
        if monster.resonance >= 4:
            monster.passive_tooltip = {
                "name": "Cinderblood: Molten Core",
                "summary": "Ignites enemies more aggressively and feeds the Drake's momentum.",
                "effects": [
                    {
                        "kind": "debuff",
                        "text": "Each landed hit has a [b]65% chance[/b] to apply [color=#ff7777]Burn[/color] for [b]2 turns[/b]."
                    },
                    {
                        "kind": "special",
                        "text": "The first Burn applied by each skill grants [b]10% Action Gauge[/b]."
                    }
                ]
            }
        elif monster.resonance >= 1:
            monster.passive_tooltip = {
                "name": "Cinderblood: Ignite",
                "summary": "Each landed hit can ignite the target.",
                "effects": [
                    {
                        "kind": "debuff",
                        "text": "Each landed hit has a [b]50% chance[/b] to apply [color=#ff7777]Burn[/color] for [b]2 turns[/b]."
                    }
                ]
            }

    if monster.monster_id == "drake_abyssal":
        var frozen_scales_data: Dictionary = {
            "name": (
                "Frozen Scales: Everfrost"
                if monster.resonance >= 3
                else "Frozen Scales"
            ),
            "summary": "Builds Frozen Scales through successful Freezes, then consumes them to fortify the caster.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Each enemy Frozen by [b]Glacial Collapse[/b] grants [b]1 Frozen Scale[/b], up to [b]3[/b]."
                },
                {
                    "kind": "buff",
                    "text": "Before casting Glacial Collapse at [b]3/3[/b], consumes all scales and grants [color=#70c8ff]Defense Up[/color] and [color=#70c8ff]Immunity[/color] for [b]2 turns[/b]."
                }
            ]
        }

        if monster.resonance >= 3:
            frozen_scales_data["effects"].append(
                {
                    "kind": "special",
                    "text": "Reaching [b]3 Frozen Scales[/b] resets [b]Glacial Collapse[/b]."
                }
            )

        monster.passive_tooltips = [
            frozen_scales_data
        ]
        monster.passive_tooltip = frozen_scales_data

        if monster.resonance >= 2:
            var frostborne_data: Dictionary = {
                "name": (
                    "Frostborne: Everlasting Winter"
                    if monster.resonance >= 4
                    else "Frostborne"
                ),
                "summary": "Prevents the Drake's frozen targets from being freed by damage.",
                "effects": [
                    {
                        "kind": "special",
                        "text": (
                            "[color=#ff7777]Freeze[/color] applied by this monster cannot be broken by any source of damage."
                            if monster.resonance >= 4
                            else "Damage dealt by this monster does not break [color=#ff7777]Freeze[/color]."
                        )
                    }
                ]
            }

            monster.passive_tooltips.append(
                frostborne_data
            )

    if (
        monster.monster_id == "dryad_storm"
        and monster.resonance >= 1
    ):
        monster.passive_tooltip = {
            "name": (
                "Nature's Grace: Overgrowth"
                if monster.resonance >= 5
                else "Nature's Grace"
            ),
            "summary": "Strengthens direct healing on wounded allies.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "Direct healing is increased by [b]20%[/b] when the target is below [b]50% HP[/b]."
                }
            ]
        }

        if monster.resonance >= 5:
            monster.passive_tooltip["effects"].append(
                {
                    "kind": "buff",
                    "text": "Overhealing is partially converted into a [color=#70c8ff]Shield[/color], up to [b]10% of the target's Max HP[/b]."
                }
            )

    if (
        monster.monster_id == "griffon_igneous"
        and monster.resonance >= 2
    ):
        monster.passive_tooltip = {
            "name": "Hawk Instinct",
            "summary": "Accelerates the Griffon whenever it successfully stuns an enemy.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "When this monster applies [color=#ff7777]Stun[/color], gains [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                }
            ]
        }


    if (
        monster.passive_tooltips.is_empty()
        and not monster.passive_tooltip.is_empty()
    ):
        monster.passive_tooltips = [
            monster.passive_tooltip
        ]


static func _scaled(value: float) -> int:
    return int(round(value * LEVEL_ONE_MULTIPLIER))


static func _apply_resonance(monster) -> void:
    if monster.monster_id == "dullahan_aether":
        if monster.resonance >= 2:
            var skill_id: String = (
                "beyond_the_veil_convergence"
                if monster.resonance >= 5
                else "beyond_the_veil_soul_recall"
            )
            monster.skills[2] = _create_shared_skill(skill_id)
        if monster.resonance >= 3:
            monster.skills[1] = _create_shared_skill(
                "soulpiercer_ascension"
            )
        return

    if monster.monster_id == "dullahan_void":
        if monster.resonance >= 2:
            monster.skills[1] = _create_shared_skill(
                "spinal_scourge_ossuary"
            )
        if monster.resonance >= 3:
            monster.skills[2] = _create_shared_skill(
                "deaths_gaze_last_name"
            )
        return

    if monster.monster_id == "dullahan_abyssal":
        if monster.resonance >= 1:
            var skill_id: String = (
                "spectral_shackles_lockdown"
                if monster.resonance >= 4
                else "spectral_shackles_binding"
            )
            monster.skills[1] = _create_shared_skill(skill_id)
        if monster.resonance >= 2:
            var fate_id: String = (
                "inescapable_fate_ironbound"
                if monster.resonance >= 5
                else "inescapable_fate"
            )
            monster.skills.append(_create_shared_skill(fate_id))
        return

    if monster.monster_id == "dullahan_storm":
        if monster.resonance >= 1:
            var skill_id: String = (
                "gale_pursuit_tempest"
                if monster.resonance >= 4
                else "gale_pursuit_crosswind"
            )
            monster.skills[1] = _create_shared_skill(skill_id)
        if monster.resonance >= 3:
            var charge_id: String = (
                "headlong_charge_stampede"
                if monster.resonance >= 5
                else "headlong_charge_rally"
            )
            monster.skills[2] = _create_shared_skill(charge_id)
        return

    if monster.monster_id == "drake_void":
        if monster.resonance >= 1:
            var rend_id: String = (
                "null_rend_annihilation"
                if monster.resonance >= 5
                else "null_rend_obliterate"
            )
            monster.skills[1] = _create_shared_skill(rend_id)

        if monster.resonance >= 2:
            monster.combat_resources["voidborn"] = 0
            monster.combat_resource_maximums["voidborn"] = 5

        if monster.resonance >= 4:
            monster.skills[2] = _create_shared_skill(
                "dismantle_decimation"
            )
        return

    if monster.monster_id == "dullahan_igneous":
        if monster.resonance >= 1:
            monster.skills[1] = _create_shared_skill(
                "relentless_pursuit_blood_trail"
            )
        if monster.resonance >= 3:
            var skill_id: String = (
                "death_sentence_massacre"
                if monster.resonance >= 5
                else "death_sentence_execution"
            )
            monster.skills[2] = _create_shared_skill(skill_id)
        return

    if monster.monster_id == "drake_storm":
        if monster.resonance >= 2:
            monster.skills[1] = _create_shared_skill(
                "lightning_rush_blitz"
            )
        if monster.resonance >= 5:
            monster.skills[2] = _create_shared_skill(
                "stormbreak_requiem"
            )
        return

    if monster.monster_id == "drake_aether":
        if monster.resonance >= 3:
            monster.skills[1] = _create_shared_skill(
                "sovereign_breath_subjugation"
            )
        if monster.resonance >= 5:
            monster.skills[2] = _create_shared_skill(
                "heavens_decree_apotheosis"
            )
        return

    if monster.monster_id == "drake_igneous":
        if monster.resonance >= 1:
            monster.on_hit_effects = [
                {
                    "effect_id": "burn",
                    "chance": (
                        0.65
                        if monster.resonance >= 4
                        else 0.50
                    ),
                    "turns": 2,
                    "stacks": 1,
                    "action_gauge": (
                        0.10
                        if monster.resonance >= 4
                        else 0.0
                    ),
                    "action_gauge_once_per_skill": (
                        monster.resonance >= 4
                    )
                }
            ]

        if monster.resonance >= 2:
            monster.skills[1] = _create_shared_skill(
                "scorching_breath_afterburn"
            )
        if monster.resonance >= 3:
            monster.skills[2] = _create_shared_skill(
                "flame_devourer_rekindled"
            )
        if monster.resonance >= 5:
            monster.skills[2] = _create_shared_skill(
                "flame_devourer_incineration"
            )
        return

    if monster.monster_id == "drake_abyssal":
        if monster.resonance >= 1:
            monster.skills[1] = _create_shared_skill(
                "rime_breath_frigid"
            )
        if monster.resonance >= 5:
            monster.skills[2] = _create_shared_skill(
                "glacial_collapse_absolute_zero"
            )
        return

    if monster.monster_id == "dryad_storm":
        if monster.resonance >= 2:
            monster.skills[1] = _create_shared_skill(
                "breath_of_the_grove_sanctuary"
            )
        if monster.resonance >= 3:
            monster.skills[0] = _create_shared_skill(
                "vine_barrage_nourishment"
            )
        if monster.resonance >= 4:
            monster.skills[1] = _create_shared_skill(
                "breath_of_the_grove_evergreen"
            )
        return

    if monster.monster_id == "griffon_igneous":
        if monster.resonance >= 1:
            monster.skills[2] = _create_shared_skill(
                "meteor_dive_violent_crash"
            )
        if monster.resonance >= 3:
            monster.skills[1] = _create_shared_skill(
                "searing_gale_turbulence"
            )
        if monster.resonance >= 4:
            monster.skills[2] = _create_shared_skill(
                "meteor_dive_terminal_impact"
            )
        if monster.resonance >= 5:
            monster.skills[1] = _create_shared_skill(
                "searing_gale_heatstorm"
            )
        return
