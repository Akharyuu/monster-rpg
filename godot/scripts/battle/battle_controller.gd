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
var forced_next_monster = null


func setup(p_allies: Array, p_enemies: Array) -> void:
    allies = p_allies
    enemies = p_enemies
    recorded_dead_monsters = []
    forced_next_monster = null

    for ally in allies:
        ally.combat_opponents = enemies

    for enemy in enemies:
        enemy.combat_opponents = allies


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

    if (
        forced_next_monster != null
        and forced_next_monster.is_alive()
    ):
        active_monster = forced_next_monster
        forced_next_monster = null
    else:
        forced_next_monster = null
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

    var chilling: Dictionary = active_monster.get_passive_by_handler(
        "chilling_presence"
    )
    if not chilling.is_empty():
        var chilling_data: Dictionary = chilling.get(
            "handler_data", {}
        )
        var extend_count: int = int(
            chilling_data.get("debuffs_per_enemy", 0)
        )

        for enemy in opponents:
            if not enemy.is_alive():
                continue

            var eligible: Array = []

            for debuff in enemy.debuffs:
                if debuff.extendable:
                    eligible.append(debuff)

            if eligible.is_empty():
                continue

            eligible.shuffle()

            for index in range(
                mini(extend_count, eligible.size())
            ):
                eligible[index].remaining_turns += 1
                eligible[index].duration += 1

        return

    var hunt: Dictionary = active_monster.get_passive_by_handler(
        "the_hunt"
    )
    if not hunt.is_empty():
        var hunt_data: Dictionary = hunt.get("handler_data", {})
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
            float(hunt_data.get("action_gauge_steal", 0.0)),
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
    var frozen_passive: Dictionary = active_monster.get_passive_by_handler(
        "frozen_scales"
    )
    var annihilation_oblivion_snapshot: Dictionary = {}

    if skill.has_handler("banish_killed_oblivion_targets"):
        for target in targets:
            if target != null:
                annihilation_oblivion_snapshot[target] = (
                    target.get_debuff("oblivion") != null
                )

    active_monster.battle_dead_count = (
        (allies.size() - get_living(allies).size())
        + (enemies.size() - get_living(enemies).size())
    )

    var soul_passive: Dictionary = active_monster.get_passive_by_handler(
        "soul_vessel"
    )
    var soul_data: Dictionary = soul_passive.get("handler_data", {})
    if not soul_passive.is_empty():
        active_monster.ally_dead_for_soul_bonus = (
            get_living(allies).size() < allies.size()
            if active_monster in allies
            else get_living(enemies).size() < enemies.size()
        )

        if (
            not active_monster.has_oblivion()
            and skill.skill_id in soul_data.get(
                "consume_all_on_skill_ids", []
            )
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
        not frozen_passive.is_empty()
        and not active_monster.has_oblivion()
        and skill.skill_id in frozen_passive.get("trigger_skill_ids", [])
    ):
        var current_scales: int = active_monster.get_combat_resource(
            "frozen_scales"
        )
        var required_scales: int = int(
            frozen_passive.get("required_scales", 0)
        )
        if required_scales > 0 and current_scales >= required_scales:
            active_monster.consume_combat_resource(
                "frozen_scales", required_scales
            )
            block_frozen_scales_generation = true
            caster_feedback.append("FROZEN SCALES CONSUMED")

            for buff_config in frozen_passive.get("buffs", []):
                var buff_id: String = str(buff_config["effect_id"])
                var buff = StatusEffectFactoryScript.create_status_effect(
                    buff_id, int(buff_config["turns"]), active_monster
                )
                active_monster.apply_status_effect(buff)
                if buff_id == "defense_up":
                    caster_feedback.append("DEF UP!")
                elif buff_id == "immunity":
                    caster_feedback.append("IMMUNITY!")


    var last_rites_low_hp_target := false

    if (
        not soul_passive.is_empty()
        and skill.skill_id in soul_data.get("last_rites_skill_ids", [])
        and not targets.is_empty()
        and targets[0] != null
        and targets[0].max_health > 0
    ):
        last_rites_low_hp_target = (
            float(targets[0].health)
            / float(targets[0].max_health)
            < float(soul_data.get("last_rites_threshold", 0.0))
        )

    var result: Dictionary = skill.execute_targets(
        active_monster,
        targets
    )

    if skill.has_handler("aoe_follow_up_attack"):
        _resolve_stormbreak_requiem_follow_up(
            skill,
            result,
            caster_feedback
        )

    if skill.has_handler(
        "reduce_action_gauge_if_both_debuffs_applied"
    ):
        var lockdown_data: Dictionary = skill.get_handler_data(
            "reduce_action_gauge_if_both_debuffs_applied"
        )
        var required_effects: Array = lockdown_data.get("effect_ids", [])
        for target_result in result.get(
            "target_results",
            []
        ):
            var applied_ids: Array[String] = []

            for effect in target_result.get(
                "effects_applied",
                []
            ):
                applied_ids.append(effect.effect_id)

            if (
                required_effects.size() == 2
                and str(required_effects[0]) in applied_ids
                and str(required_effects[1]) in applied_ids
            ):
                target_result["target"].action_gauge = maxf(
                    0.0,
                    target_result["target"].action_gauge
                    - float(lockdown_data.get("amount", 0.0))
                )
                caster_feedback.append(
                    "LOCKDOWN -20% AG"
                )

    if skill.has_handler("extend_target_debuffs"):
        var extension_data: Dictionary = skill.get_handler_data(
            "extend_target_debuffs"
        )
        var extension_turns: int = int(extension_data.get("turns", 0))
        for target_result in result.get(
            "target_results",
            []
        ):
            var target = target_result["target"]

            if not target.is_alive():
                continue

            for debuff in target.debuffs:
                if debuff.extendable:
                    debuff.remaining_turns += extension_turns
                    debuff.duration += extension_turns

            if target.debuffs.size() >= int(
                extension_data.get("silence_required_debuffs", 3)
            ):
                var silence = (
                    StatusEffectFactoryScript.create_status_effect(
                        "silence",
                        int(extension_data.get("silence_turns", 1)),
                        active_monster
                    )
                )

                if target.apply_status_effect(silence) != null:
                    target_result["effects_applied"].append(
                        silence
                    )
                    result["effects_applied"].append(
                        silence
                    )
                    caster_feedback.append("SILENCE!")

    if skill.has_handler("apply_team_buff"):
        var team_buff_data: Dictionary = skill.get_handler_data(
            "apply_team_buff"
        )
        var storm_team: Array = (
            allies
            if active_monster in allies
            else enemies
        )

        for ally in storm_team:
            if not ally.is_alive():
                continue

            var team_speed_up = (
                StatusEffectFactoryScript.create_status_effect(
                    str(team_buff_data.get("effect_id", "")),
                    int(team_buff_data.get("turns", 0)),
                    active_monster
                )
            )
            ally.apply_status_effect(team_speed_up)

        caster_feedback.append("TEMPEST - TEAM SPD UP!")

    if (
        active_monster.monster_id == "drake_void"
        and active_monster.resonance >= 2
    ):
        var voidborn_activations: int = int(
            result.get("voidborn_activations", 0)
        )

        if voidborn_activations > 0:
            caster_feedback.append(
                "VOIDBORN ACTIVATED!"
            )

    if skill.has_handler("banish_killed_oblivion_targets"):
        for target_result in result.get(
            "target_results",
            []
        ):
            var target = target_result["target"]

            if (
                not target.is_alive()
                and bool(
                    annihilation_oblivion_snapshot.get(
                        target,
                        false
                    )
                )
            ):
                target.banished = true
                caster_feedback.append(
                    "ANNIHILATION - BANISHED!"
                )

    if skill.has_handler("follow_up_skill_on_kill"):
        _resolve_massacre_follow_up(
            skill,
            result,
            caster_feedback
        )

    if (
        skill is DamageSkill
        and skill.heal_lowest_hp_ally_ratio > 0.0
    ):
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

            var healing_ratio: float = (
                skill.heal_lowest_hp_ally_ratio
            )

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

    if skill.has_handler("support_lowest_gauge_ally"):
        var support_data: Dictionary = skill.get_handler_data(
            "support_lowest_gauge_ally"
        )
        for self_buff in support_data.get("self_buffs", []):
            var status = StatusEffectFactoryScript.create_status_effect(
                str(self_buff["effect_id"]),
                int(self_buff["turns"]),
                active_monster
            )
            active_monster.apply_status_effect(status)
            if str(self_buff["effect_id"]) == "attack_up":
                caster_feedback.append("ATK UP!")
            elif str(self_buff["effect_id"]) == "speed_up":
                caster_feedback.append("SPD UP!")

        var team: Array = allies if active_monster in allies else enemies
        var gauge_target = active_monster
        var living_allies: Array = []
        for ally in team:
            if ally.is_alive() and ally != active_monster:
                living_allies.append(ally)

        if not living_allies.is_empty():
            gauge_target = living_allies[0]
            for ally in living_allies:
                if ally.action_gauge < gauge_target.action_gauge:
                    gauge_target = ally

        for ally_buff in support_data.get("ally_buffs", []):
            var status = StatusEffectFactoryScript.create_status_effect(
                str(ally_buff["effect_id"]),
                int(ally_buff["turns"]),
                active_monster
            )
            gauge_target.apply_status_effect(status)

        var gauge_gain: float = float(
            support_data.get("ally_action_gauge", 0.0)
        )
        gauge_target.increase_action_gauge(gauge_gain)

        if (
            bool(support_data.get("force_next_turn", false))
            and gauge_target != active_monster
        ):
            forced_next_monster = gauge_target

        caster_feedback.append(
            "%s - %s +%d%% AG"
            % [
                skill.skill_name.to_upper(),
                gauge_target.monster_name,
                int(gauge_gain * 100.0)
            ]
        )

    var hunger: Dictionary = active_monster.get_passive_by_handler(
        "bottomless_hunger"
    )
    if not hunger.is_empty() and not active_monster.has_oblivion():
        var hunger_data: Dictionary = hunger.get("handler_data", {})
        var removed_buffs: int = int(
            result.get("removed_buffs", 0)
        )

        if removed_buffs > 0:
            var total_passive_healing := 0

            for _removed_buff in range(removed_buffs):
                total_passive_healing += active_monster.heal(
                    int(
                        active_monster.max_health
                        * float(hunger_data.get("heal_ratio_per_buff", 0.0))
                    )
                )

                active_monster.increase_action_gauge(
                    float(hunger_data.get("action_gauge_per_buff", 0.0))
                )

            result["healing"] = int(
                result.get("healing", 0)
            ) + total_passive_healing

            caster_feedback.append(
                "BOTTOMLESS HUNGER x%d" % removed_buffs
            )

    if skill.has_handler("apply_self_buff"):
        var self_buff_data: Dictionary = skill.get_handler_data(
            "apply_self_buff"
        )
        var speed_up = (
            StatusEffectFactoryScript.create_status_effect(
                str(self_buff_data.get("effect_id", "")),
                int(self_buff_data.get("turns", 0)),
                active_monster
            )
        )

        if active_monster.apply_status_effect(speed_up) != null:
            caster_feedback.append("SPD UP!")

        if skill.has_handler("increase_action_gauge"):
            var gauge_data: Dictionary = skill.get_handler_data(
                "increase_action_gauge"
            )
            var amount: float = float(gauge_data.get("amount", 0.0))
            active_monster.increase_action_gauge(amount)
            caster_feedback.append("BLITZ +%d%% AG" % int(amount * 100.0))

    if skill.has_handler("apply_scaling_silence"):
        var silence_data: Dictionary = skill.get_handler_data(
            "apply_scaling_silence"
        )
        var silence_chance: float = minf(
            float(silence_data.get("max_chance", 1.0)),
            float(silence_data.get("base_chance", 0.0))
            + active_monster.buffs.size()
            * float(silence_data.get("chance_per_buff", 0.0))
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
                        "turns": int(silence_data.get("turns", 1))
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

    var grace: Dictionary = active_monster.get_passive_by_handler(
        "divine_grace"
    )
    if not grace.is_empty() and not active_monster.has_oblivion():
        var grace_data: Dictionary = grace.get("handler_data", {})
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
                * float(grace_data.get("heal_ratio_per_buff", 0.0))
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

    if skill.has_handler("grant_extra_turn"):
        active_monster.action_gauge = 1.0
        caster_feedback.append("APOTHEOSIS - EXTRA TURN!")

    if (
        not active_monster.has_oblivion()
        and not active_monster.get_passive_by_handler(
            "natures_grace"
        ).get("handler_data", {}).get("overgrowth", {}).is_empty()
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

    var instinct: Dictionary = active_monster.get_passive_by_handler(
        "apply_self_buff"
    )
    if not instinct.is_empty() and not active_monster.has_oblivion():
        var instinct_data: Dictionary = instinct.get("handler_data", {})
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
                    str(instinct_data.get("effect_id", "")),
                    int(instinct_data.get("turns", 0)),
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
        not frozen_passive.is_empty()
        and not active_monster.has_oblivion()
        and skill.skill_id in frozen_passive.get("trigger_skill_ids", [])
        and not block_frozen_scales_generation
    ):
        var scales_gained := 0
        for target_result in result.get("target_results", []):
            for effect in target_result.get("effects_applied", []):
                if effect.effect_id == "freeze":
                    scales_gained += 1
                    break

        if scales_gained > 0:
            var max_scales: int = int(frozen_passive.get("max_scales", 0))
            var new_total: int = active_monster.add_combat_resource(
                "frozen_scales", scales_gained, max_scales
            )
            caster_feedback.append(
                "FROZEN SCALES %d/%d" % [new_total, max_scales]
            )

            if (
                frozen_passive.has("reset_cooldown_skill_slot")
                and new_total >= int(
                    frozen_passive.get("required_scales", 0)
                )
            ):
                var glacial_skill = active_monster.get_skill(
                    int(frozen_passive["reset_cooldown_skill_slot"])
                )
                if glacial_skill != null:
                    glacial_skill.current_cooldown = 0
                    caster_feedback.append(
                        "EVERFROST - GLACIAL COLLAPSE READY!"
                    )

    if not soul_passive.is_empty() and not active_monster.has_oblivion():
        var soul_max: int = int(soul_data.get("max_charges", 0))
        var new_total: int = active_monster.add_combat_resource(
            "soul_charges",
            int(soul_data.get("charges_per_damage_skill", 0)),
            soul_max
        )

        if (
            skill.skill_id in soul_data.get("last_rites_skill_ids", [])
            and last_rites_low_hp_target
        ):
            new_total = active_monster.add_combat_resource(
                "soul_charges",
                1,
                soul_max
            )
            caster_feedback.append(
                "LAST RITES +1 SOUL CHARGE"
            )

        caster_feedback.append(
            "SOUL CHARGE %d/%d" % [new_total, soul_max]
        )

    # Finalize Deathless Rider only after the entire skill (including
    # follow-up hits) has resolved, so later hits cannot kill the target.
    result["deathless_survivors"] = []

    for combatant in allies + enemies:
        if combatant.finalize_deathless_rider():
            result["deathless_survivors"].append(
                combatant
            )

    _resolve_new_deaths(caster_feedback)

    result["caster_feedback"] = caster_feedback
    return result


func _resolve_massacre_follow_up(
    skill,
    result: Dictionary,
    caster_feedback: Array[String]
) -> void:
    var killed_target := false

    for target_result in result.get(
        "target_results",
        []
    ):
        if not target_result["target"].is_alive():
            killed_target = true
            break

    if not killed_target:
        return

    var opponents: Array = (
        enemies
        if active_monster in allies
        else allies
    )
    var living_opponents: Array = get_living(
        opponents
    )

    if living_opponents.is_empty():
        return

    var follow_target = living_opponents[0]

    for opponent in living_opponents:
        var opponent_ratio: float = (
            float(opponent.health)
            / float(opponent.max_health)
        )
        var current_ratio: float = (
            float(follow_target.health)
            / float(follow_target.max_health)
        )

        if opponent_ratio < current_ratio:
            follow_target = opponent

    var follow_data: Dictionary = skill.get_handler_data(
        "follow_up_skill_on_kill"
    )
    var follow_skill = active_monster.get_skill(
        int(follow_data.get("skill_slot", 0))
    )

    if follow_skill == null:
        return

    var follow_result: Dictionary = (
        follow_skill.execute_targets(
            active_monster,
            [follow_target]
        )
    )

    if not follow_result.get("success", false):
        return

    result["damage"] = int(
        result.get("damage", 0)
    ) + int(
        follow_result.get("damage", 0)
    )

    result["critical_hits"] = int(
        result.get("critical_hits", 0)
    ) + int(
        follow_result.get("critical_hits", 0)
    )

    result["effects_applied"].append_array(
        follow_result.get(
            "effects_applied",
            []
        )
    )

    result["resisted_effects"].append_array(
        follow_result.get(
            "resisted_effects",
            []
        )
    )

    result["target_results"].append_array(
        follow_result.get(
            "target_results",
            []
        )
    )

    caster_feedback.append(
        "MASSACRE - RELENTLESS PURSUIT!"
    )


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

    var follow_up_data: Dictionary = skill.get_handler_data(
        "aoe_follow_up_attack"
    )
    var damage_multiplier: float = float(
        follow_up_data.get("damage_multiplier", 0.0)
    )
    var follow_up_damage := 0

    for target in opponents:
        if not target.is_alive():
            continue

        var damage_result: Dictionary = skill.damage_calc(
            active_monster,
            target,
            damage_multiplier
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
        or caster.has_oblivion()
        or caster.get_passive_by_handler(
            "natures_grace"
        ).get("handler_data", {}).get("overgrowth", {}).is_empty()
    ):
        return

    var overheal: int = maxi(
        0,
        intended_heal - actual_heal
    )

    if overheal <= 0:
        return

    var overgrowth: Dictionary = caster.get_passive_by_handler(
        "natures_grace"
    ).get("handler_data", {}).get("overgrowth", {})
    var shield_value: int = mini(
        int(overheal * float(overgrowth.get("overheal_conversion", 0.0))),
        int(target.max_health * float(overgrowth.get("max_shield_ratio", 0.0)))
    )

    if shield_value <= 0:
        return

    var shield = (
        StatusEffectFactoryScript.create_status_effect(
            "shield",
            int(overgrowth.get("shield_turns", 0)),
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
            var owner_soul: Dictionary = owner.get_passive_by_handler(
                "soul_vessel"
            )
            if (
                not owner.is_alive()
                or owner_soul.is_empty()
                or owner.has_oblivion()
            ):
                continue

            var owner_soul_data: Dictionary = owner_soul.get(
                "handler_data", {}
            )
            var charges_from_death: int = int(
                owner_soul_data.get("charges_per_death", 0)
            )
            var soul_limit: int = int(owner_soul_data.get(
                "max_charges", 0
            ))
            var new_total: int = owner.add_combat_resource(
                "soul_charges",
                charges_from_death,
                soul_limit
            )

            if owner == active_monster:
                caster_feedback.append(
                    "SOUL VESSEL - DEATH %d/%d" % [
                        new_total, soul_limit
                    ]
                )

        var death_march_owner = monster.death_named_by

        if (
            death_march_owner != null
            and death_march_owner.is_alive()
            and death_march_owner.monster_id == "dullahan_void"
            and death_march_owner.resonance >= 5
            and not death_march_owner.has_oblivion()
        ):
            var opponents: Array = (
                enemies
                if death_march_owner in allies
                else allies
            )
            var candidates: Array = []

            for opponent in opponents:
                if opponent.is_alive():
                    candidates.append(opponent)

            if not candidates.is_empty():
                var next_target = candidates[0]

                for opponent in candidates:
                    var opponent_ratio: float = (
                        float(opponent.health)
                        / float(opponent.max_health)
                    )
                    var current_ratio: float = (
                        float(next_target.health)
                        / float(next_target.max_health)
                    )

                    if opponent_ratio < current_ratio:
                        next_target = opponent

                death_march_owner.apply_named(
                    next_target,
                    2
                )

                var vulnerability = (
                    StatusEffectFactoryScript.create_status_effect(
                        "vulnerability",
                        3,
                        death_march_owner
                    )
                )

                var accuracy: float = (
                    death_march_owner.get_effective_stat(
                        "accuracy"
                    )
                )
                var resistance: float = (
                    next_target.get_effective_stat(
                        "resistance"
                    )
                )
                var resist_chance: float = clampf(
                    resistance - accuracy,
                    15.0,
                    100.0
                )

                if (
                    randf_range(0.0, 100.0)
                    >= resist_chance
                ):
                    next_target.apply_status_effect(
                        vulnerability
                    )

                if death_march_owner == active_monster:
                    caster_feedback.append(
                        "DEATH MARCH - NEW TARGET NAMED!"
                    )

        monster.death_named_by = null


# The extra action is part of the R2+ skill definition, not a
# Dullahan-specific numeric exception in the battle controller.
func _soul_recall_action(caster) -> Dictionary:
    if caster == null:
        return {}
    var skill = caster.get_skill(3)
    if skill == null:
        return {}
    var action: Dictionary = skill.shared_definition.get(
        "active_action", {}
    )
    if str(action.get("id", "")) not in [
        "soul_recall", "soul_recall_convergence"
    ]:
        return {}
    return action


func can_use_soul_recall(caster) -> bool:
    if caster == null or not caster.is_alive():
        return false
    var action: Dictionary = _soul_recall_action(caster)
    if (
        action.is_empty()
        or caster.has_oblivion()
        or caster.is_silenced()
        or caster.get_combat_resource("soul_charges") < int(
            action.get("required_charges", 0)
        )
    ):
        return false
    return caster in allies or caster in enemies


func execute_soul_recall(target) -> Dictionary:
    var caster = active_monster
    if (
        not can_use_soul_recall(caster)
        or target == null
        or target.is_alive()
        or target.banished
    ):
        return {"success": false}

    var team: Array = allies if caster in allies else enemies
    if target not in team:
        return {"success": false}

    var action: Dictionary = _soul_recall_action(caster)
    caster.consume_combat_resource(
        "soul_charges", int(action.get("consume_charges", 0))
    )
    target.health = maxi(
        1, int(target.max_health * float(action.get(
            "revive_health_ratio", 0.0
        )))
    )
    target.action_gauge = float(action.get("action_gauge", 0.0))
    target.buffs.clear()
    target.debuffs.clear()
    target.special_states.clear()
    target.named_target = null
    target.named_by = null
    target.death_named_by = null

    for resource_id in target.combat_resource_maximums:
        target.combat_resources[resource_id] = 0

    recorded_dead_monsters.erase(target)

    return {
        "success": true,
        "damage": 0,
        "critical_hits": 0,
        "healing": target.health,
        "effects_applied": [],
        "resisted_effects": [],
        "target_results": [],
        "caster_feedback": [
            "SOUL RECALL - %s REVIVED!" % target.monster_name
        ]
    }

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

        var authority: Dictionary = defender.get_passive_by_handler(
            "celestial_authority"
        )
        if (
            authority.is_empty()
            or defender.has_oblivion()
            or hit_count <= 0
        ):
            continue

        var authority_data: Dictionary = authority.get("handler_data", {})
        var authority_chance: float = float(
            authority_data.get("chance", 0.0)
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
                    int(authority_data.get("turns", 0)),
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

                if authority_data.has(
                    "action_gauge_to_most_buffed_ally"
                ):
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
                            float(authority_data[
                                "action_gauge_to_most_buffed_ally"
                            ])
                        )


func choose_enemy_target():
    var living_allies := get_living(allies)

    if living_allies.is_empty():
        return null

    return living_allies.pick_random()
