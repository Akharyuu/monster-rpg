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
        active_monster.monster_id == "drake_storm"
        and skill.skill_id == "lightning_rush"
    ):
        var speed_up = (
            StatusEffectFactoryScript.create_status_effect(
                "speed_up",
                2,
                active_monster
            )
        )

        if active_monster.apply_status_effect(speed_up) != null:
            caster_feedback.append("SPD UP!")

    if (
        active_monster.monster_id == "drake_aether"
        and skill.skill_id == "sovereign_breath"
    ):
        var silence_chance: float = minf(
            0.80,
            0.30 + active_monster.buffs.size() * 0.10
        )

        for target_result in result.get(
            "target_results",
            []
        ):
            var target = target_result["target"]

            if not target.is_alive():
                continue

            var effect_result: Dictionary = (
                skill.try_apply_effect(
                    {
                        "effect_id": "silence",
                        "chance": silence_chance,
                        "turns": 1
                    },
                    active_monster,
                    target
                )
            )

            var applied_effect = effect_result[
                "applied_effect"
            ]

            if applied_effect != null:
                target_result["effects_applied"].append(
                    applied_effect
                )
                result["effects_applied"].append(
                    applied_effect
                )
            elif effect_result["resisted"]:
                target_result["resisted_effects"].append(
                    "silence"
                )
                result["resisted_effects"].append(
                    "silence"
                )

    _resolve_receive_hit_passives(
        active_monster,
        result,
        caster_feedback
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


func _resolve_receive_hit_passives(
    attacker,
    result: Dictionary,
    caster_feedback: Array[String]
) -> void:
    for target_result in result.get(
        "target_results",
        []
    ):
        var defender = target_result["target"]
        var hit_count: int = int(
            target_result.get("hits_landed", 0)
        )

        if (
            defender.monster_id != "drake_aether"
            or hit_count <= 0
        ):
            continue

        for _hit_index in range(hit_count):
            if randf() > 0.30:
                continue

            var accuracy: float = defender.get_effective_stat(
                "accuracy"
            )
            var resistance: float = attacker.get_effective_stat(
                "resistance"
            )
            var resist_chance: float = clampf(
                resistance - accuracy,
                15.0,
                100.0
            )

            if randf_range(0.0, 100.0) < resist_chance:
                continue

            var attack_break = (
                StatusEffectFactoryScript.create_status_effect(
                    "attack_break",
                    2,
                    defender
                )
            )

            var applied_effect = attacker.apply_status_effect(
                attack_break
            )

            if applied_effect != null:
                if (
                    "CELESTIAL AUTHORITY - ATK DOWN!"
                    not in caster_feedback
                ):
                    caster_feedback.append(
                        "CELESTIAL AUTHORITY - ATK DOWN!"
                    )


func choose_enemy_target():
    var living_allies := get_living(allies)

    if living_allies.is_empty():
        return null

    return living_allies.pick_random()
