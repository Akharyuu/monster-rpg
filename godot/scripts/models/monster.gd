class_name Monster
extends RefCounted

const SkillScript = preload("res://scripts/models/skill.gd")

var monster_id: String
var monster_name: String
var family: String
var attribute: String
var rarity: int

var level: int = 1
var ascended: bool = false
var stat_scale: float = 1.0

var max_health: int
var health: int
var attack: int
var defense: int
var speed: int

var accuracy: float = 25.0
var resistance: float = 25.0
var crit_rate: float = 15.0
var crit_damage: float = 50.0

var action_gauge: float = 0.0
var skills: Array = []

var buffs: Array = []
var debuffs: Array = []
var combat_resources: Dictionary = {}
var combat_resource_maximums: Dictionary = {}
var special_states: Dictionary = {}
var named_target = null
var named_by = null
var battle_dead_count: int = 0

# Lightweight prototype representation of passive effects that trigger
# whenever this monster lands a hit. This will later become the full
# passive system used by Python.
var on_hit_effects: Array = []


func _init(
    p_monster_id: String,
    p_name: String,
    p_family: String,
    p_attribute: String,
    p_rarity: int,
    p_max_health: int,
    p_attack: int,
    p_defense: int,
    p_speed: int,
    p_skills: Array = [],
    p_stat_scale: float = 1.0
) -> void:
    monster_id = p_monster_id
    monster_name = p_name
    family = p_family
    attribute = p_attribute
    rarity = p_rarity

    max_health = p_max_health
    health = p_max_health
    attack = p_attack
    defense = p_defense
    speed = p_speed
    skills = p_skills
    stat_scale = p_stat_scale


func is_alive() -> bool:
    return health > 0


func is_stunned() -> bool:
    return get_debuff("stun") != null


func is_frozen() -> bool:
    return get_debuff("freeze") != null


func is_silenced() -> bool:
    if (
        is_headless()
        and not has_oblivion()
    ):
        return false

    return get_debuff("silence") != null


func has_oblivion() -> bool:
    return get_debuff("oblivion") != null


func is_headless() -> bool:
    return bool(
        special_states.get("headless", false)
    )


func cannot_act() -> bool:
    return is_stunned() or is_frozen()


func has_buff(effect_id: String) -> bool:
    for buff in buffs:
        if buff.effect_id == effect_id:
            return true

    return false


func get_combat_resource(
    resource_id: String,
    default_value: int = 0
) -> int:
    return int(
        combat_resources.get(resource_id, default_value)
    )


func add_combat_resource(
    resource_id: String,
    amount: int,
    maximum: int
) -> int:
    var new_value: int = mini(
        maximum,
        get_combat_resource(resource_id) + amount
    )

    combat_resources[resource_id] = new_value
    return new_value


func consume_combat_resource(
    resource_id: String,
    amount: int
) -> int:
    var current: int = get_combat_resource(resource_id)
    var consumed: int = mini(current, amount)

    combat_resources[resource_id] = current - consumed
    return consumed


func get_base_stat(stat: String) -> float:
    match stat:
        "max_health", "health":
            return max_health
        "attack":
            return attack
        "defense":
            return defense
        "speed":
            return speed
        "accuracy":
            return accuracy
        "resistance":
            return resistance
        "crit_rate":
            return crit_rate
        "crit_damage":
            return crit_damage
        _:
            push_error("Unknown stat: %s" % stat)
            return 0.0


func get_effective_stat(stat: String) -> float:
    var multiplicative_modifier := 1.0
    var additive_modifier := 0.0

    for buff in buffs:
        if buff.stat == stat:
            if buff.modifier_mode == "additive":
                additive_modifier += float(buff.modifier)
            elif buff.modifier != null:
                multiplicative_modifier *= float(buff.modifier)

    for debuff in debuffs:
        if debuff.stat == stat:
            if debuff.modifier_mode == "additive":
                additive_modifier += float(debuff.modifier)
            elif debuff.modifier != null:
                multiplicative_modifier *= float(debuff.modifier)

    var value: float = (
        get_base_stat(stat)
        * multiplicative_modifier
        + additive_modifier
    )

    if (
        stat == "speed"
        and monster_id == "dullahan_void"
        and is_headless()
        and not has_oblivion()
    ):
        value += speed * 0.20

    return value


func get_passive_damage_multiplier() -> float:
    if has_oblivion():
        return 1.0

    if monster_id != "drake_storm":
        return 1.0

    var bonus_speed: float = maxf(
        0.0,
        get_effective_stat("speed") - speed
    )

    return 1.0 + bonus_speed * 0.003


func get_attribute_modifier(defender) -> float:
    if (
        (attribute == "igneous" and defender.attribute == "abyssal")
        or (attribute == "abyssal" and defender.attribute == "storm")
        or (attribute == "storm" and defender.attribute == "igneous")
    ):
        return 0.85

    if (
        (attribute == "igneous" and defender.attribute == "storm")
        or (attribute == "abyssal" and defender.attribute == "igneous")
        or (attribute == "storm" and defender.attribute == "abyssal")
    ):
        return 1.15

    return 1.0


func receive_damage(amount: int) -> int:
    var was_alive: bool = is_alive()
    var actual_damage: int = mini(amount, health)

    health = maxi(0, health - amount)

    if was_alive and not is_alive():
        _clear_special_states_on_death()

    return actual_damage


func _clear_special_states_on_death() -> void:
    if named_by != null:
        var source = named_by
        named_by = null
        special_states.erase("named")

        if (
            source != null
            and source.named_target == self
        ):
            source.clear_named_target()

    if named_target != null:
        clear_named_target()


func heal(amount: int) -> int:
    if not is_alive():
        return 0

    if get_debuff("heal_block") != null:
        return 0

    var old_health: int = health
    health = mini(max_health, health + amount)
    return health - old_health


func apply_status_effect(effect):
    if effect == null:
        return null

    var effects_list: Array

    if effect.effect_type == "buff":
        effects_list = buffs
    elif effect.effect_type == "debuff":
        if (
            effect.effect_id == "silence"
            and is_headless()
            and not has_oblivion()
        ):
            return null

        if has_buff("immunity"):
            return null

        effects_list = debuffs
    else:
        return null

    for active_effect in effects_list:
        if active_effect.effect_id == effect.effect_id:
            if effect.duration > active_effect.remaining_turns:
                active_effect.remaining_turns = effect.duration

            active_effect.stacks = mini(
                active_effect.max_stacks,
                active_effect.stacks + effect.stacks
            )

            active_effect.source = effect.source
            return active_effect

    if effects_list.size() < 5:
        effects_list.append(effect)
        return effect

    return null


func apply_named(
    target,
    turns: int = 2
) -> void:
    clear_named_target()

    named_target = target
    special_states["headless"] = true

    target.named_by = self
    target.special_states["named"] = turns


func clear_named_target() -> void:
    if (
        named_target != null
        and named_target.named_by == self
    ):
        named_target.named_by = null
        named_target.special_states.erase("named")

    named_target = null
    special_states.erase("headless")


func reduce_special_state_turns() -> void:
    if named_by == null:
        return

    var remaining: int = int(
        special_states.get("named", 0)
    ) - 1

    if remaining > 0:
        special_states["named"] = remaining
        return

    var source = named_by
    named_by = null
    special_states.erase("named")

    if (
        source != null
        and source.named_target == self
    ):
        source.clear_named_target()


func get_direct_damage_taken_multiplier() -> float:
    if get_debuff("vulnerability") != null:
        return 1.15

    return 1.0


func remove_buffs_for_strip() -> int:
    var veil = null

    for buff in buffs:
        if buff.effect_id == "veil":
            veil = buff
            break

    if veil != null:
        buffs.erase(veil)
        return 0

    var removed_count: int = buffs.size()

    if removed_count > 0:
        buffs.clear()

    return removed_count


func get_debuff(effect_id: String):
    for debuff in debuffs:
        if debuff.effect_id == effect_id:
            return debuff

    return null


func get_debuff_stacks(effect_id: String) -> int:
    var debuff = get_debuff(effect_id)

    if debuff == null:
        return 0

    return debuff.stacks


func consume_debuff_stacks(
    effect_id: String,
    amount: int
) -> int:
    var debuff = get_debuff(effect_id)

    if debuff == null:
        return 0

    var consumed: int = mini(amount, debuff.stacks)
    debuff.stacks -= consumed

    if debuff.stacks <= 0:
        debuffs.erase(debuff)

    return consumed


func apply_damage_over_time() -> Dictionary:
    var total_damage := 0
    var sources: Array[String] = []

    for debuff in debuffs:
        var damage := 0

        if debuff.effect_id == "burn":
            match debuff.stacks:
                1:
                    damage = int(max_health * 0.03)
                2:
                    damage = int(max_health * 0.06)
                3:
                    damage = int(max_health * 0.10)

        if damage <= 0:
            continue

        total_damage += receive_damage(damage)

        sources.append(
            "%s x%d" % [
                debuff.effect_name,
                debuff.stacks
            ]
        )

    return {
        "damage": total_damage,
        "sources": sources
    }


func reduce_status_effect_turns(
    effects_at_turn_start: Array = []
) -> void:
    # Match Python exactly: only effects that existed when the
    # turn began lose duration. An empty snapshot means reduce none.
    for buff in buffs:
        if buff in effects_at_turn_start:
            buff.reduce_remaining_turns()

    for debuff in debuffs:
        if debuff in effects_at_turn_start:
            debuff.reduce_remaining_turns()

    buffs = buffs.filter(
        func(effect): return effect.is_active()
    )

    debuffs = debuffs.filter(
        func(effect): return effect.is_active()
    )


func get_skill(index: int):
    if index < 1 or index > skills.size():
        return null

    return skills[index - 1]


func reduce_skill_cooldowns() -> void:
    for skill in skills:
        skill.reduce_cooldown()


func increase_action_gauge(amount: float) -> void:
    action_gauge = clampf(
        action_gauge + amount,
        0.0,
        1.0
    )


func reset_action_gauge() -> void:
    action_gauge = 0.0
