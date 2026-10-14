class_name BattleController
extends RefCounted

const StatusEffectFactoryScript = preload(
    "res://scripts/factories/status_effect_factory.gd"
)

var allies: Array = []
var enemies: Array = []

var active_monster
var active_turn_effects: Array = []


func setup(p_allies: Array, p_enemies: Array) -> void:
    allies = p_allies
    enemies = p_enemies


func get_living(team: Array) -> Array:
    return team.filter(
        func(monster): return monster.is_alive()
    )


func get_living_combatants() -> Array:
    return get_living(allies) + get_living(enemies)


func is_player_side(monster) -> bool:
    return monster in allies


func is_enemy_side(monster) -> bool:
    return monster in enemies


func is_battle_over() -> bool:
    return (
        get_living(allies).is_empty()
        or get_living(enemies).is_empty()
    )


func player_won() -> bool:
    return (
        not get_living(allies).is_empty()
        and get_living(enemies).is_empty()
    )


func fill_action_gauges() -> void:
    var combatants := get_living_combatants()

    if combatants.is_empty():
        return

    var smallest_time := INF

    for combatant in combatants:
        var speed: float = combatant.get_effective_stat(
            "speed"
        )
        var gauge_gain: float = speed / 2000.0

        if gauge_gain <= 0.0:
            continue

        var remaining_gauge: float = (
            1.0 - combatant.action_gauge
        )

        smallest_time = minf(
            smallest_time,
            remaining_gauge / gauge_gain
        )

    if smallest_time == INF:
        return

    for combatant in combatants:
        var speed: float = combatant.get_effective_stat(
            "speed"
        )
        var gauge_gain: float = speed / 2000.0

        if gauge_gain > 0.0:
            combatant.increase_action_gauge(
                gauge_gain * smallest_time
            )


func get_ready_combatant():
    var ready: Array = []

    for combatant in get_living_combatants():
        if combatant.action_gauge >= 0.999999:
            ready.append(combatant)

    if ready.is_empty():
        return null

    var chosen = ready[0]

    for combatant in ready:
        if (
            combatant.get_effective_stat("speed")
            > chosen.get_effective_stat("speed")
        ):
            chosen = combatant

    return chosen


func begin_next_turn() -> Dictionary:
    if is_battle_over():
        return {
            "battle_over": true,
            "player_won": player_won()
        }

    fill_action_gauges()
    active_monster = get_ready_combatant()

    if active_monster == null:
        return {
            "error": "No combatant reached full Action Gauge."
        }

    active_monster.reset_action_gauge()

    active_turn_effects = []
    active_turn_effects.append_array(
        active_monster.buffs
    )
    active_turn_effects.append_array(
        active_monster.debuffs
    )

    active_monster.reduce_skill_cooldowns()

    var dot_result: Dictionary = (
        active_monster.apply_damage_over_time()
    )

    return {
        "battle_over": false,
        "monster": active_monster,
        "dot_result": dot_result
    }


func active_monster_cannot_act() -> bool:
    return (
        active_monster != null
        and active_monster.cannot_act()
    )


func get_active_control_effect_id() -> String:
    if active_monster == null:
        return ""

    if active_monster.is_stunned():
        return "stun"

    if active_monster.is_frozen():
        return "freeze"

    return ""


func end_active_turn() -> void:
    if active_monster == null:
        return

    active_monster.reduce_status_effect_turns(
        active_turn_effects
    )


func clear_active_monster() -> void:
    active_monster = null
    active_turn_effects = []


func get_skill(slot: int):
    if active_monster == null:
        return null

    return active_monster.get_skill(slot)


func execute_active_skill(
    skill,
    targets: Array
) -> Dictionary:
    if active_monster == null:
        return {
            "success": false
        }

    var caster_feedback: Array[String] = []
    var block_frozen_scales_generation := false

    if (
        active_monster.monster_id == "drake_abyssal"
        and skill.skill_id == "glacial_collapse"
    ):
        var current_scales: int = (
            active_monster.get_combat_resource(
                "frozen_scales"
            )
        )

        if current_scales >= 3:
            active_monster.consume_combat_resource(
                "frozen_scales",
                3
            )
            block_frozen_scales_generation = true

            var defense_up = (
                StatusEffectFactoryScript.create_status_effect(
                    "defense_up",
                    2,
                    active_monster
                )
            )

            var immunity = (
                StatusEffectFactoryScript.create_status_effect(
                    "immunity",
                    2,
                    active_monster
                )
            )

            active_monster.apply_status_effect(defense_up)
            active_monster.apply_status_effect(immunity)

            caster_feedback.append("FROZEN SCALES CONSUMED")
            caster_feedback.append("DEF UP!")
            caster_feedback.append("IMMUNITY!")

    var result: Dictionary = skill.execute_targets(
        active_monster,
        targets
    )

    if (
        active_monster.monster_id == "drake_abyssal"
        and skill.skill_id == "glacial_collapse"
        and not block_frozen_scales_generation
    ):
        var scales_gained := 0

        for target_result in result.get(
            "target_results",
            []
        ):
            var froze_target := false

            for effect in target_result.get(
                "effects_applied",
                []
            ):
                if effect.effect_id == "freeze":
                    froze_target = true
                    break

            if froze_target:
                scales_gained += 1

        if scales_gained > 0:
            var new_total: int = (
                active_monster.add_combat_resource(
                    "frozen_scales",
                    scales_gained,
                    3
                )
            )

            caster_feedback.append(
                "FROZEN SCALES %d/3" % new_total
            )

    result["caster_feedback"] = caster_feedback
    return result


func choose_enemy_target():
    var living_allies := get_living(allies)

    if living_allies.is_empty():
        return null

    return living_allies.pick_random()
