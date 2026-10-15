class_name PrototypeFactory
extends RefCounted

const MonsterScript = preload("res://scripts/models/monster.gd")
const DamageSkillScript = preload("res://scripts/models/damage_skill.gd")
const SupportSkillScript = preload("res://scripts/models/support_skill.gd")

const LEVEL_ONE_MULTIPLIER := 0.35
const SHARED_MONSTER_DATA_PATH := "res://data/monster_data.json"
const SHARED_SKILL_DATA_PATH := "res://data/skill_data.json"
const SHARED_PASSIVE_DATA_PATH := "res://data/passive_data.json"
const SHARED_RESONANCE_DATA_PATH := "res://data/resonance_data.json"

static var _shared_monsters: Dictionary = {}
static var _shared_skills: Dictionary = {}
static var _shared_passives: Dictionary = {}
static var _shared_resonances: Dictionary = {}


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


static func _get_shared_passives() -> Dictionary:
    if not _shared_passives.is_empty():
        return _shared_passives

    var parsed: Variant = JSON.parse_string(
        FileAccess.get_file_as_string(SHARED_PASSIVE_DATA_PATH)
    )
    if not (parsed is Dictionary):
        push_error("Invalid shared passive JSON")
        return {}
    if int(parsed.get("schema_version", -1)) != 1:
        push_error("Unsupported passive data schema version")
        return {}
    var records: Variant = parsed.get("passives", null)
    if not (records is Dictionary):
        push_error("Missing passives in shared JSON")
        return {}

    _shared_passives = records
    return _shared_passives


static func _get_shared_resonances() -> Dictionary:
    if not _shared_resonances.is_empty():
        return _shared_resonances

    var parsed: Variant = JSON.parse_string(
        FileAccess.get_file_as_string(SHARED_RESONANCE_DATA_PATH)
    )
    if not (parsed is Dictionary):
        push_error("Invalid shared resonance JSON")
        return {}
    if int(parsed.get("schema_version", -1)) != 1:
        push_error("Unsupported resonance data schema version")
        return {}
    var records: Variant = parsed.get("resonances", null)
    if not (records is Dictionary):
        push_error("Missing resonances in shared JSON")
        return {}

    _shared_resonances = records
    return _shared_resonances


# Compute the active passive kit from shared base IDs and ordered
# Resonance actions, exactly as Python's Resonance system does.
static func _assign_shared_passives(monster) -> bool:
    var roster: Dictionary = _get_shared_monsters()
    var definitions: Dictionary = _get_shared_passives()
    var resonances: Dictionary = _get_shared_resonances()
    var record: Dictionary = roster.get(monster.monster_id, {})
    var active: Dictionary = {}

    for passive_id in record.get("passives", []):
        var id: String = str(passive_id)
        if not definitions.has(id):
            push_error("Missing base passive: %s" % id)
            return false
        active[id] = definitions[id]

    var levels: Dictionary = resonances.get(monster.monster_id, {})
    for level in range(1, monster.resonance + 1):
        for action in levels.get(str(level), []):
            var operation: String = str(action.get("action", ""))
            if operation == "add_passive":
                var added_id: String = str(action["passive"])
                if not definitions.has(added_id) or active.has(added_id):
                    push_error("Invalid added passive: %s" % added_id)
                    return false
                active[added_id] = definitions[added_id]
            elif operation == "replace_passive":
                var old_id: String = str(action["old"])
                var new_id: String = str(action["new"])
                if not active.has(old_id) or not definitions.has(new_id):
                    push_error("Invalid passive replacement: %s" % new_id)
                    return false
                active.erase(old_id)
                active[new_id] = definitions[new_id]

    monster.passive_definitions = active

    # The on-hit passive execution stays in the existing combat engine.
    monster.on_hit_effects = []
    var burn: Dictionary = monster.get_passive_by_handler("apply_burn")
    if not burn.is_empty():
        monster.on_hit_effects.append({
            "effect_id": "burn",
            "chance": float(burn.get("chance", 0.0)),
            "turns": int(burn.get("turns", 2)),
            "stacks": int(burn.get("stacks", 1)),
            "action_gauge": float(burn.get("action_gauge", 0.0)),
            "action_gauge_once_per_skill": bool(
                burn.get("action_gauge_once_per_skill", false)
            )
        })

    var resource_handlers := {
        "frozen_scales": "frozen_scales",
        "soul_vessel": "soul_charges",
        "voidborn": "voidborn"
    }
    for handler_id in resource_handlers:
        var passive: Dictionary = monster.get_passive_by_handler(
            str(handler_id)
        )
        if passive.is_empty():
            continue
        var maximum_key: String = "max_stacks"
        if handler_id == "soul_vessel":
            maximum_key = "max_charges"
        elif handler_id == "frozen_scales":
            maximum_key = "max_scales"

        # Frozen Scales defines max_scales at the top level;
        # Soul Vessel and Voidborn use nested handler_data.
        var data: Dictionary = passive.get(
            "handler_data", passive
        )
        var maximum: int = int(data.get(maximum_key, 0))
        if maximum <= 0:
            push_error("Invalid passive resource cap: %s" % handler_id)
            return false

        var key: String = str(resource_handlers[handler_id])
        monster.combat_resources[key] = 0
        monster.combat_resource_maximums[key] = maximum

    return true


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

    if monster == null:
        return null
    monster.resonance = clampi(resonance, 0, 5)
    if not _apply_resonance(monster):
        return null
    if not _sync_monster_skills(monster):
        return null
    if not _assign_shared_passives(monster):
        return null
    _attach_skill_descriptions(monster)
    _attach_passive_description(monster)
    return monster


static func _attach_skill_descriptions(monster) -> void:
    # Tooltip summaries and formatted effects live in skill_data.json
    # alongside the canonical combat definitions.
    var definitions: Dictionary = _get_shared_skills()

    for skill in monster.skills:
        var entry: Dictionary = definitions.get(
            str(skill.skill_id), {}
        )
        var tooltip: Dictionary = entry.get("tooltip", {})
        skill.tooltip_summary = str(
            tooltip.get("summary", skill.description)
        )
        var effects: Array = tooltip.get("effects", [])
        skill.tooltip_effects = effects.duplicate(true)
        skill.description = skill.tooltip_summary


static func _attach_passive_description(monster) -> void:
    # Base passive presentation comes from the canonical passive record.
    # Resonance-specific compositions below are kept intact for now.
    monster.passive_tooltip = {}
    var monster_record: Dictionary = _get_shared_monsters().get(
        monster.monster_id, {}
    )
    var base_passives: Array = monster_record.get("passives", [])
    if not base_passives.is_empty():
        var passive_id: String = str(base_passives[0])
        var passive_record: Dictionary = _get_shared_passives().get(
            passive_id, {}
        )
        var tooltip: Dictionary = passive_record.get("tooltip", {})
        monster.passive_tooltip = tooltip.duplicate(true)

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
        # The base Bottomless Hunger tooltip is loaded from
        # passive_data.json above, not from a local passive_data map.
        var bottomless_data: Dictionary = (
            monster.passive_tooltip.duplicate(true)
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


# Apply skill changes from the same ordered R1-R5 rules as Python.
# Passive actions are applied separately by _assign_shared_passives().
static func _apply_resonance(monster) -> bool:
    var rules: Dictionary = _get_shared_resonances()
    if rules.is_empty():
        push_error("Shared Resonance rules are unavailable")
        return false

    var levels: Dictionary = rules.get(monster.monster_id, {})
    for rank in range(1, monster.resonance + 1):
        for action in levels.get(str(rank), []):
            var operation: String = str(action.get("action", ""))

            if operation == "replace_skill":
                # The JSON uses 1-based slots; Godot arrays use 0-based.
                var slot: int = int(action.get("slot", 0)) - 1
                if slot < 0 or slot >= monster.skills.size():
                    push_error(
                        "Invalid Resonance slot for %s at R%d: %d"
                        % [monster.monster_id, rank, slot + 1]
                    )
                    return false

                var replacement_id: String = str(
                    action.get("new", "")
                )
                var replacement = _create_shared_skill(replacement_id)
                if replacement == null:
                    return false
                monster.skills[slot] = replacement

            elif operation == "add_skill":
                var extra_id: String = str(action.get("skill", ""))
                var extra_skill = _create_shared_skill(extra_id)
                if extra_skill == null:
                    return false
                monster.skills.append(extra_skill)

            elif (
                operation == "add_passive"
                or operation == "replace_passive"
            ):
                continue

            else:
                push_error(
                    "Unsupported Resonance action: %s" % operation
                )
                return false

    return true
