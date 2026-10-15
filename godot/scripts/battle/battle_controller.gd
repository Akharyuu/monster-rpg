class_name BattleController
extends RefCounted

const StatusEffectFactoryScript = preload(
    "res://scripts/factories/status_effect_factory.gd"
)

var allies: Array = []
var enemies: Array = []

var active_monster
var active_turn_effects: Array = []
var recorded_dead_monsters: Array = []


func setup(p_allies: Array, p_enemies: Array) -> void:
    allies = p_allies
    enemies = p_enemies
    recorded_dead_monsters = []


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

    var hot_result: Dictionary = (
        active_monster.apply_healing_over_time()
    )

    var dot_result: Dictionary = (
        active_monster.apply_damage_over_time()
    )

    if not active_monster.is_alive():
        var ignored_feedback: Array[String] = []
        _resolve_new_deaths(ignored_feedback)

    return {
        "battle_over": false,
        "monster": active_monster,
        "hot_result": hot_result,
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

    _resolve_after_turn_passives()

    active_monster.reduce_status_effect_turns(
        active_turn_effects
    )

    active_monster.reduce_special_state_turns()


func _resolve_after_turn_passives() -> void:
    if active_monster == null:
        return

    if active_monster.has_oblivion():
        return

    var opponents: Array = (
        enemies
        if active_monster in allies
        else allies
    )

    if active_monster.monster_id == "dullahan_abyssal":
        for enemy in opponents:
            if not enemy.is_alive():
                continue

            var eligible: Array = []

            for debuff in enemy.debuffs:
                if debuff.extendable:
                    eligible.append(debuff)

            if eligible.is_empty():
                continue

            var chosen = eligible[
                randi_range(0, eligible.size() - 1)
            ]

            chosen.remaining_turns += 1
            chosen.duration += 1

        return

    if active_monster.monster_id == "dullahan_storm":
        var living_opponents: Array = []

        for enemy in opponents:
            if enemy.is_alive():
                living_opponents.append(enemy)

        if living_opponents.is_empty():
            return

        var target = living_opponents[0]

        for enemy in living_opponents:
            if enemy.action_gauge > target.action_gauge:
                target = enemy

        var stolen: float = minf(
            0.20,
            target.action_gauge
        )

        target.action_gauge = maxf(
            0.0,
            target.action_gauge - stolen
        )

        active_monster.increase_action_gauge(stolen)


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

    active_monster.battle_dead_count = (
        (allies.size() - get_living(allies).size())
        + (enemies.size() - get_living(enemies).size())
    )

    if active_monster.monster_id == "dullahan_aether":
        active_monster.ally_dead_for_soul_bonus = (
            get_living(allies).size() < allies.size()
            if active_monster in allies
            else get_living(enemies).size() < enemies.size()
        )

        if (
            not active_monster.has_oblivion()
            and skill.skill_id == "beyond_the_veil"
        ):
            var soul_charges: int = (
                active_monster.get_combat_resource(
                    "soul_charges"
                )
            )

            skill.soul_charges_consumed = soul_charges

            if soul_charges > 0:
                active_monster.consume_combat_resource(
                    "soul_charges",
                    soul_charges
                )

                caster_feedback.append(
                    "SOUL CHARGES CONSUMED %d" % soul_charges
                )
        else:
            skill.soul_charges_consumed = 0

    if (
        active_monster.monster_id == "drake_abyssal"
        and not active_monster.has_oblivion()
        and skill.skill_id in [
            "glacial_collapse",
            "glacial_collapse_absolute_zero"
        ]
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
        and skill.skill_id == "stormbreak_requiem"
    ):
        _resolve_stormbreak_requiem_follow_up(
            skill,
            result,
            caster_feedback
        )

    if skill.skill_id in [
        "vine_barrage",
        "vine_barrage_nourishment",
        "nurturing_lash"
    ]:
        var team: Array = (
            allies
            if active_monster in allies
            else enemies
        )

        var living_allies: Array = []

        for ally in team:
            if ally.is_alive():
                living_allies.append(ally)

        if not living_allies.is_empty():
            var heal_target = living_allies[0]

            for ally in living_allies:
                var ally_ratio: float = (
                    float(ally.health) / float(ally.max_health)
                )
                var target_ratio: float = (
                    float(heal_target.health)
                    / float(heal_target.max_health)
                )

                if ally_ratio < target_ratio:
                    heal_target = ally

            var healing_ratio: float = 0.05

            if skill.skill_id == "vine_barrage":
                healing_ratio = 0.08
            elif skill.skill_id == "vine_barrage_nourishment":
                healing_ratio = 0.15

            var intended_heal: int = int(
                active_monster.get_healing_hp()
                * healing_ratio
                * active_monster.get_direct_heal_multiplier(
                    heal_target
                )
            )

            var actual_heal: int = heal_target.heal(
                intended_heal
            )

            _apply_overgrowth_shield(
                active_monster,
                heal_target,
                intended_heal,
                actual_heal,
                caster_feedback
            )

            result["healing"] = int(
                result.get("healing", 0)
            ) + actual_heal

            caster_feedback.append(
                "%s - %s +%d HP"
                % [
                    skill.skill_name.to_upper(),
                    heal_target.monster_name,
                    actual_heal
                ]
            )

    if (
        active_monster.monster_id == "dullahan_storm"
        and skill.skill_id == "headlong_charge"
    ):
        var attack_up = (
            StatusEffectFactoryScript.create_status_effect(
                "attack_up",
                2,
                active_monster
            )
        )

        var speed_up = (
            StatusEffectFactoryScript.create_status_effect(
                "speed_up",
                2,
                active_monster
            )
        )

        active_monster.apply_status_effect(attack_up)
        active_monster.apply_status_effect(speed_up)

        var team: Array = (
            allies
            if active_monster in allies
            else enemies
        )

        var living_allies: Array = []

        for ally in team:
            if ally.is_alive() and ally != active_monster:
                living_allies.append(ally)

        var gauge_target = active_monster

        if not living_allies.is_empty():
            gauge_target = living_allies[0]

            for ally in living_allies:
                if ally.action_gauge < gauge_target.action_gauge:
                    gauge_target = ally

        gauge_target.increase_action_gauge(0.20)

        caster_feedback.append("ATK UP!")
        caster_feedback.append("SPD UP!")
        caster_feedback.append(
            "HEADLONG CHARGE - %s +20%% AG"
            % gauge_target.monster_name
        )

    if (
        active_monster.monster_id == "drake_void"
        and not active_monster.has_oblivion()
    ):
        var removed_buffs: int = int(
            result.get("removed_buffs", 0)
        )

        if removed_buffs > 0:
            var total_passive_healing := 0

            for _removed_buff in range(removed_buffs):
                total_passive_healing += active_monster.heal(
                    int(active_monster.max_health * 0.10)
                )

                active_monster.increase_action_gauge(
                    0.08
                )

            result["healing"] = int(
                result.get("healing", 0)
            ) + total_passive_healing

            caster_feedback.append(
                "BOTTOMLESS HUNGER x%d" % removed_buffs
            )

    if (
        active_monster.monster_id == "drake_storm"
        and skill.skill_id in [
            "lightning_rush",
            "lightning_rush_blitz"
        ]
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

        if skill.skill_id == "lightning_rush_blitz":
            active_monster.increase_action_gauge(0.15)
            caster_feedback.append("BLITZ +15% AG")

    if (
        active_monster.monster_id == "drake_aether"
        and skill.skill_id in [
            "sovereign_breath",
            "sovereign_breath_subjugation"
        ]
    ):
        var base_silence_chance: float = (
            0.50
            if skill.skill_id == "sovereign_breath_subjugation"
            else 0.30
        )
        var max_silence_chance: float = (
            1.00
            if skill.skill_id == "sovereign_breath_subjugation"
            else 0.80
        )
        var silence_chance: float = minf(
            max_silence_chance,
            base_silence_chance
            + active_monster.buffs.size() * 0.10
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

    if (
        active_monster.monster_id == "drake_aether"
        and active_monster.resonance >= 1
        and not active_monster.has_oblivion()
    ):
        var divine_grace_total := 0

        for target_result in result.get(
            "target_results",
            []
        ):
            var target = target_result["target"]
            var applied_buffs := 0

            for effect in target_result.get(
                "effects_applied",
                []
            ):
                if effect.effect_type == "buff":
                    applied_buffs += 1

            if applied_buffs <= 0:
                continue

            var heal_amount: int = int(
                target.max_health
                * 0.05
                * applied_buffs
            )
            var actual_heal: int = target.heal(
                heal_amount
            )

            divine_grace_total += actual_heal

            if actual_heal > 0:
                caster_feedback.append(
                    "DIVINE GRACE - %s +%d HP"
                    % [
                        target.monster_name,
                        actual_heal
                    ]
                )

        result["healing"] = int(
            result.get("healing", 0)
        ) + divine_grace_total

    if (
        active_monster.monster_id == "drake_aether"
        and skill.skill_id == "heavens_decree_apotheosis"
    ):
        active_monster.action_gauge = 1.0
        caster_feedback.append("APOTHEOSIS - EXTRA TURN!")

    if (
        active_monster.monster_id == "dryad_storm"
        and active_monster.resonance >= 5
        and not active_monster.has_oblivion()
    ):
        for target_result in result.get(
            "target_results",
            []
        ):
            _apply_overgrowth_shield(
                active_monster,
                target_result["target"],
                int(target_result.get(
                    "intended_healing",
                    0
                )),
                int(target_result.get(
                    "healing",
                    0
                )),
                caster_feedback
            )

    if (
        active_monster.monster_id == "griffon_igneous"
        and active_monster.resonance >= 2
        and not active_monster.has_oblivion()
    ):
        var applied_stun := false

        for target_result in result.get(
            "target_results",
            []
        ):
            for effect in target_result.get(
                "effects_applied",
                []
            ):
                if effect.effect_id == "stun":
                    applied_stun = true
                    break

            if applied_stun:
                break

        if applied_stun:
            var speed_up = (
                StatusEffectFactoryScript.create_status_effect(
                    "speed_up",
                    2,
                    active_monster
                )
            )

            if active_monster.apply_status_effect(speed_up) != null:
                caster_feedback.append(
                    "HAWK INSTINCT - SPD UP!"
                )

    _resolve_receive_hit_passives(
        active_monster,
        result,
        caster_feedback
    )

    if (
        active_monster.monster_id == "drake_abyssal"
        and not active_monster.has_oblivion()
        and skill.skill_id in [
            "glacial_collapse",
            "glacial_collapse_absolute_zero"
        ]
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

            if (
                active_monster.resonance >= 3
                and new_total >= 3
            ):
                var glacial_skill = (
                    active_monster.get_skill(3)
                )

                if glacial_skill != null:
                    glacial_skill.current_cooldown = 0
                    caster_feedback.append(
                        "EVERFROST - GLACIAL COLLAPSE READY!"
                    )

    if (
        active_monster.monster_id == "dullahan_aether"
        and not active_monster.has_oblivion()
    ):
        var new_total: int = active_monster.add_combat_resource(
            "soul_charges",
            1,
            5
        )

        caster_feedback.append(
            "SOUL CHARGE %d/5" % new_total
        )

    _resolve_new_deaths(caster_feedback)

    result["caster_feedback"] = caster_feedback
    return result


func _resolve_stormbreak_requiem_follow_up(
    skill,
    result: Dictionary,
    caster_feedback: Array[String]
) -> void:
    var opponents: Array = (
        enemies
        if active_monster in allies
        else allies
    )

    var follow_up_damage := 0

    for target in opponents:
        if not target.is_alive():
            continue

        var damage_result: Dictionary = skill.damage_calc(
            active_monster,
            target,
            0.75
        )

        var actual_damage: int = target.receive_damage(
            int(damage_result["damage"]),
            active_monster
        )

        follow_up_damage += actual_damage

        for target_result in result.get(
            "target_results",
            []
        ):
            if target_result["target"] != target:
                continue

            target_result["damage"] = int(
                target_result.get("damage", 0)
            ) + actual_damage
            target_result["hits_landed"] = int(
                target_result.get("hits_landed", 0)
            ) + 1

            if bool(damage_result.get("critical", false)):
                target_result["critical_hits"] = int(
                    target_result.get("critical_hits", 0)
                ) + 1
                result["critical_hits"] = int(
                    result.get("critical_hits", 0)
                ) + 1

            break

    result["damage"] = int(
        result.get("damage", 0)
    ) + follow_up_damage

    caster_feedback.append(
        "STORMBREAK: REQUIEM - FOLLOW-UP!"
    )


func _apply_overgrowth_shield(
    caster,
    target,
    intended_heal: int,
    actual_heal: int,
    caster_feedback: Array[String]
) -> void:
    if (
        caster == null
        or target == null
        or caster.monster_id != "dryad_storm"
        or caster.resonance < 5
        or caster.has_oblivion()
    ):
        return

    var overheal: int = maxi(
        0,
        intended_heal - actual_heal
    )

    if overheal <= 0:
        return

    var shield_value: int = mini(
        int(overheal * 0.50),
        int(target.max_health * 0.10)
    )

    if shield_value <= 0:
        return

    var shield = (
        StatusEffectFactoryScript.create_status_effect(
            "shield",
            2,
            caster
        )
    )
    shield.value = shield_value

    var applied = target.apply_status_effect(
        shield
    )

    if applied != null:
        caster_feedback.append(
            "OVERGROWTH - %s SHIELD %d"
            % [
                target.monster_name,
                applied.value
            ]
        )


func _resolve_new_deaths(
    caster_feedback: Array[String]
) -> void:
    var combatants: Array = allies + enemies

    for monster in combatants:
        if monster.is_alive():
            continue

        if monster in recorded_dead_monsters:
            continue

        recorded_dead_monsters.append(monster)

        for owner in combatants:
            if (
                not owner.is_alive()
                or owner.monster_id != "dullahan_aether"
                or owner.has_oblivion()
            ):
                continue

            var new_total: int = owner.add_combat_resource(
                "soul_charges",
                1,
                5
            )

            if owner == active_monster:
                caster_feedback.append(
                    "SOUL VESSEL - DEATH %d/5" % new_total
                )


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
            or defender.has_oblivion()
            or hit_count <= 0
        ):
            continue

        var authority_chance: float = (
            0.50
            if defender.resonance >= 2
            else 0.30
        )

        for _hit_index in range(hit_count):
            if randf() > authority_chance:
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

                if defender.resonance >= 2:
                    var defender_team: Array = (
                        allies
                        if defender in allies
                        else enemies
                    )
                    var living_team: Array = get_living(
                        defender_team
                    )

                    if not living_team.is_empty():
                        var gauge_target = living_team[0]

                        for ally in living_team:
                            if ally.buffs.size() > gauge_target.buffs.size():
                                gauge_target = ally

                        gauge_target.increase_action_gauge(
                            0.20
                        )


func choose_enemy_target():
    var living_allies := get_living(allies)

    if living_allies.is_empty():
        return null

    return living_allies.pick_random()
