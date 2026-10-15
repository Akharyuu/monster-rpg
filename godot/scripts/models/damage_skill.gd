class_name DamageSkill
extends Skill

const StatusEffectFactoryScript = preload(
    "res://scripts/factories/status_effect_factory.gd"
)

var multiplier: float
var hits: int
var hit_multipliers: Array
var scaling_stat: String
var effects: Array
var heal_lowest_hp_ally_ratio: float = 0.0

# Optional handler-like data used by the first playable slice.
var damage_for_burn_stacks: Dictionary = {}
var consume_burn_and_heal: Dictionary = {}
var action_gauge_reduction_per_hit: float = 0.0
var action_gauge_reduction_chance: float = 1.0
var hit_distribution: String = ""
var repeated_target_damage: Dictionary = {}
var resolve_hits_by_round: bool = false
var strip_buffs_hit_index: int = -1
var damage_per_removed_buff: float = 0.0
var removed_buff_damage_hit_indices: Array = []
var damage_per_dead_monster: float = 0.0
var max_dead_monsters: int = 0
var max_dead_monster_bonus: float = 0.0
var apply_named_before_hit: bool = false
var named_turns: int = 0
var vulnerability_chance: float = 0.0
var vulnerability_turns: int = 0
var damage_per_soul_charge: float = 0.0
var max_soul_charges: int = 0
var use_consumed_soul_charges: bool = false
var disable_soul_bonus_if_ally_dead: bool = false
var soul_charges_consumed: int = 0
var max_missing_health_bonus: float = 0.0
var execute_health_threshold: float = 0.0
var execute_defense_ignore_ratio: float = 0.0
var speed_damage_scaling: float = 0.0
var conditional_required_debuff_id: String = ""
var conditional_requires_any_debuff: bool = false
var conditional_damage_multiplier: float = 1.0
var conditional_hit_damage_multipliers: Array = []
var action_gauge_reduction_if_debuff_id: String = ""
var action_gauge_reduction_if_debuff_amount: float = 0.0
var add_burn_if_started_with_burn: bool = false
var extra_burn_stacks: int = 1
var extra_burn_turns: int = 3
var reset_skill_slot_if_burn_stacks: int = 0
var reset_skill_required_burn_stacks: int = 0
var action_gauge_gain_if_target_low_hp_threshold: float = 0.0
var action_gauge_gain_if_target_low_hp_amount: float = 0.0
var action_gauge_threshold: float = -1.0
var action_gauge_bonus_reduction: float = 0.0
var bonus_stat: String = ""
var bonus_stat_scaling: float = 0.0


func _init(
    p_skill_id: String,
    p_name: String,
    p_multiplier: float,
    p_hits: int = 1,
    p_hit_multipliers: Array = [],
    p_scaling_stat: String = "attack",
    p_cooldown: int = 0,
    p_effects: Array = [],
    p_damage_for_burn_stacks: Dictionary = {},
    p_consume_burn_and_heal: Dictionary = {},
    p_target_type: String = "single_enemy",
    p_action_gauge_reduction_per_hit: float = 0.0,
    p_hit_distribution: String = "",
    p_repeated_target_damage: Dictionary = {},
    p_resolve_hits_by_round: bool = false,
    p_strip_buffs_hit_index: int = -1,
    p_damage_per_removed_buff: float = 0.0,
    p_removed_buff_damage_hit_indices: Array = [],
    p_damage_per_dead_monster: float = 0.0,
    p_max_dead_monsters: int = 0,
    p_max_dead_monster_bonus: float = 0.0,
    p_apply_named_before_hit: bool = false,
    p_named_turns: int = 0,
    p_vulnerability_chance: float = 0.0,
    p_vulnerability_turns: int = 0
) -> void:
    super(
        p_skill_id,
        p_name,
        p_cooldown,
        p_target_type
    )

    multiplier = p_multiplier
    hits = p_hits
    hit_multipliers = p_hit_multipliers
    scaling_stat = p_scaling_stat
    effects = p_effects
    damage_for_burn_stacks = p_damage_for_burn_stacks
    consume_burn_and_heal = p_consume_burn_and_heal
    action_gauge_reduction_per_hit = (
        p_action_gauge_reduction_per_hit
    )
    hit_distribution = p_hit_distribution
    repeated_target_damage = p_repeated_target_damage
    resolve_hits_by_round = p_resolve_hits_by_round
    strip_buffs_hit_index = p_strip_buffs_hit_index
    damage_per_removed_buff = p_damage_per_removed_buff
    removed_buff_damage_hit_indices = (
        p_removed_buff_damage_hit_indices
    )
    damage_per_dead_monster = p_damage_per_dead_monster
    max_dead_monsters = p_max_dead_monsters
    max_dead_monster_bonus = p_max_dead_monster_bonus
    apply_named_before_hit = p_apply_named_before_hit
    named_turns = p_named_turns
    vulnerability_chance = p_vulnerability_chance
    vulnerability_turns = p_vulnerability_turns


func base_damage_calc(
    attacker,
    defender,
    hit_multiplier: float = 1.0,
    damage_multiplier: float = 1.0,
    ignore_defense: bool = false,
    defense_ignore_ratio: float = 0.0,
    bonus_raw_damage: float = 0.0
) -> float:
    var effective_scaling_stat: float = attacker.get_effective_stat(
        scaling_stat
    )

    if scaling_stat == "max_health":
        effective_scaling_stat *= 0.08

    var raw_damage: float = (
        effective_scaling_stat
        * multiplier
        * damage_multiplier
        * hit_multiplier
        + bonus_raw_damage
    )

    if raw_damage <= 0:
        return 1.0

    var damage_reduction := 1.0

    if not ignore_defense:
        var effective_defense: float = defender.get_effective_stat(
            "defense"
        )

        effective_defense *= maxf(
            0.0,
            1.0 - defense_ignore_ratio
        )

        var defense_reference: float = (
            744.0 * defender.stat_scale
        )

        if defense_reference <= 0.0:
            defense_reference = 744.0

        damage_reduction = (
            1.0
            / (
                1.0
                + pow(
                    effective_defense
                    / defense_reference,
                    1.1
                )
            )
        )

    var attribute_modifier: float = (
        attacker.get_attribute_modifier(defender)
    )

    var passive_damage_multiplier: float = (
        attacker.get_passive_damage_multiplier()
    )

    var direct_damage_taken_multiplier: float = (
        defender.get_direct_damage_taken_multiplier()
    )

    return maxf(
        1.0,
        raw_damage
        * damage_reduction
        * attribute_modifier
        * passive_damage_multiplier
        * direct_damage_taken_multiplier
    )


func get_burn_damage_multiplier(defender) -> float:
    if damage_for_burn_stacks.is_empty():
        return 1.0

    var stacks: int = defender.get_debuff_stacks("burn")

    if stacks <= 0:
        return 1.0

    var multipliers: Dictionary = damage_for_burn_stacks.get(
        "multipliers_by_stacks",
        {}
    )

    return float(multipliers.get(stacks, 1.0))


func damage_calc(
    attacker,
    defender,
    hit_multiplier: float = 1.0,
    snapshot_health_ratio: float = -1.0,
    condition_multiplier: float = 1.0
) -> Dictionary:
    var bonus_damage: float = (
        get_burn_damage_multiplier(defender)
        * condition_multiplier
    )

    if damage_per_soul_charge > 0.0:
        var soul_charges: int = (
            soul_charges_consumed
            if use_consumed_soul_charges
            else attacker.get_combat_resource(
                "soul_charges"
            )
        )

        soul_charges = mini(
            soul_charges,
            max_soul_charges
        )

        if (
            disable_soul_bonus_if_ally_dead
            and attacker.ally_dead_for_soul_bonus
        ):
            soul_charges = 0

        bonus_damage *= (
            1.0
            + soul_charges * damage_per_soul_charge
        )

    if speed_damage_scaling > 0.0:
        bonus_damage *= (
            1.0
            + attacker.get_effective_stat("speed")
            * speed_damage_scaling
        )

    if max_missing_health_bonus > 0.0:
        var current_health_ratio: float = (
            float(defender.health) / float(defender.max_health)
            if defender.max_health > 0
            else 0.0
        )

        var missing_health_ratio: float = maxf(
            0.0,
            1.0 - current_health_ratio
        )

        bonus_damage *= (
            1.0
            + minf(
                missing_health_ratio * max_missing_health_bonus,
                max_missing_health_bonus
            )
        )

    if damage_per_dead_monster > 0.0:
        var counted_dead: int = mini(
            attacker.battle_dead_count,
            max_dead_monsters
        )

        var dead_bonus: float = minf(
            counted_dead * damage_per_dead_monster,
            max_dead_monster_bonus
        )

        bonus_damage *= 1.0 + dead_bonus

    var defense_ignore_ratio: float = 0.0
    var ignore_defense: bool = false

    var ignore_defense_at_stacks = (
        damage_for_burn_stacks.get(
            "ignore_defense_at_stacks",
            null
        )
    )

    if (
        ignore_defense_at_stacks != null
        and defender.get_debuff_stacks("burn")
        >= int(ignore_defense_at_stacks)
    ):
        ignore_defense = true

    if (
        execute_health_threshold > 0.0
        and snapshot_health_ratio >= 0.0
        and snapshot_health_ratio < execute_health_threshold
    ):
        defense_ignore_ratio = execute_defense_ignore_ratio

    var bonus_raw_damage := 0.0

    if (
        not bonus_stat.is_empty()
        and bonus_stat_scaling > 0.0
    ):
        bonus_raw_damage = (
            attacker.get_effective_stat(bonus_stat)
            * bonus_stat_scaling
        )

    var base_damage: float = base_damage_calc(
        attacker,
        defender,
        hit_multiplier,
        bonus_damage,
        ignore_defense,
        defense_ignore_ratio,
        bonus_raw_damage
    )

    var critical := false
    var critical_damage_bonus := 1.0

    if randi_range(1, 100) <= int(
        attacker.get_effective_stat("crit_rate")
    ):
        critical_damage_bonus += (
            attacker.get_effective_stat("crit_damage")
            / 100.0
        )
        critical = true

    var final_damage: int = maxi(
        1,
        int(base_damage * critical_damage_bonus)
    )

    return {
        "damage": final_damage,
        "critical": critical
    }


func effect_condition_met(
    condition: Dictionary,
    attacker,
    defender,
    applied_effects_this_use: Array = []
) -> bool:
    if condition.is_empty():
        return true

    var condition_type: String = str(
        condition.get("type", "")
    )

    match condition_type:
        "target_has_debuff":
            return (
                defender.get_debuff(
                    str(condition.get("effect_id", ""))
                )
                != null
            )
        "target_lacks_debuff":
            return (
                defender.get_debuff(
                    str(condition.get("effect_id", ""))
                )
                == null
            )

        "target_gained_debuff":
            var required_id: String = str(
                condition.get("effect_id", "")
            )

            for effect in applied_effects_this_use:
                if (
                    effect != null
                    and effect.effect_id == required_id
                ):
                    return true

            return false

        "target_action_gauge_below":
            var threshold: float = float(
                condition.get("threshold", 0.0)
            )

            var buff_rule: Dictionary = condition.get(
                "threshold_if_caster_has_buff",
                {}
            )

            if (
                not buff_rule.is_empty()
                and attacker.has_buff(
                    str(buff_rule.get("effect_id", ""))
                )
            ):
                threshold = float(
                    buff_rule.get("threshold", threshold)
                )

            return defender.action_gauge < threshold

        _:
            return true


func try_apply_effect(
    effect_config: Dictionary,
    attacker,
    defender,
    applied_effects_this_use: Array = []
) -> Dictionary:
    var effect_id: String = str(
        effect_config["effect_id"]
    )

    var condition: Dictionary = effect_config.get(
        "condition",
        {}
    )

    var result := {
        "effect_id": effect_id,
        "applied_effect": null,
        "resisted": false
    }

    if not effect_condition_met(
        condition,
        attacker,
        defender,
        applied_effects_this_use
    ):
        return result

    var chance: float = float(
        effect_config.get("chance", 1.0)
    )

    if randf() > chance:
        return result

    var is_debuff: bool = (
        effect_config.get("effect_type", "debuff")
        == "debuff"
    )

    if (
        is_debuff
        and not effect_config.get("ignore_resistance", false)
    ):
        var accuracy: float = attacker.get_effective_stat(
            "accuracy"
        )

        var resistance: float = defender.get_effective_stat(
            "resistance"
        )

        var resist_chance: float = clampf(
            resistance - accuracy,
            15.0,
            100.0
        )

        if randf_range(0.0, 100.0) < resist_chance:
            result["resisted"] = true
            return result

    var status_effect = (
        StatusEffectFactoryScript.create_status_effect(
            effect_id,
            int(effect_config["turns"]),
            attacker,
            int(effect_config.get("stacks", 1))
        )
    )

    if status_effect == null:
        return result

    if status_effect.effect_type == "buff":
        result["applied_effect"] = (
            attacker.apply_status_effect(status_effect)
        )
    else:
        result["applied_effect"] = (
            defender.apply_status_effect(status_effect)
        )

    return result


func apply_on_hit_passives(
    attacker,
    defender,
    applied_effects: Array
) -> void:
    if attacker.has_oblivion():
        return

    # Cinderblood-style passives do NOT use Accuracy/Resistance in Python.
    # They only roll their own proc chance, then apply the status effect.
    for effect_config in attacker.on_hit_effects:
        var chance: float = float(
            effect_config.get("chance", 1.0)
        )

        if randf() > chance:
            continue

        var status_effect = (
            StatusEffectFactoryScript.create_status_effect(
                effect_config["effect_id"],
                int(effect_config["turns"]),
                attacker,
                int(effect_config.get("stacks", 1))
            )
        )

        if status_effect == null:
            continue

        var applied_effect = defender.apply_status_effect(
            status_effect
        )

        if applied_effect != null:
            applied_effects.append(applied_effect)

            var action_gauge_gain: float = float(
                effect_config.get(
                    "action_gauge",
                    0.0
                )
            )

            var once_per_skill: bool = bool(
                effect_config.get(
                    "action_gauge_once_per_skill",
                    false
                )
            )

            if (
                action_gauge_gain > 0.0
                and (
                    not once_per_skill
                    or not attacker.on_hit_action_gauge_granted_this_skill
                )
            ):
                attacker.increase_action_gauge(
                    action_gauge_gain
                )

                if once_per_skill:
                    attacker.on_hit_action_gauge_granted_this_skill = true


func resolve_after_skill(
    attacker,
    defender,
    starting_burn_stacks: int
) -> int:
    if (
        consume_burn_and_heal.is_empty()
        or starting_burn_stacks <= 0
    ):
        return 0

    defender.consume_debuff_stacks(
        "burn",
        starting_burn_stacks
    )

    var heal_by_stacks: Dictionary = (
        consume_burn_and_heal.get(
            "heal_by_stacks",
            {}
        )
    )

    var heal_ratio: float = float(
        heal_by_stacks.get(
            starting_burn_stacks,
            0.0
        )
    )

    var heal_amount := int(
        attacker.max_health * heal_ratio
    )

    return attacker.heal(heal_amount)


func execute_on_target(
    attacker,
    defender
) -> Dictionary:
    var total_damage := 0
    var critical_hits := 0
    var hits_landed := 0
    var effects_applied: Array = []
    var resisted_effects: Array[String] = []

    var starting_burn_stacks: int = (
        defender.get_debuff_stacks("burn")
    )

    var starting_health_ratio: float = (
        float(defender.health) / float(defender.max_health)
        if defender.max_health > 0
        else 0.0
    )

    var condition_met_at_start := false

    if not conditional_required_debuff_id.is_empty():
        condition_met_at_start = (
            defender.get_debuff(
                conditional_required_debuff_id
            )
            != null
        )
    elif conditional_requires_any_debuff:
        condition_met_at_start = not defender.debuffs.is_empty()

    if apply_named_before_hit and defender.is_alive():
        attacker.apply_named(
            defender,
            named_turns
        )

        var vulnerability_result: Dictionary = (
            try_apply_effect(
                {
                    "effect_id": "vulnerability",
                    "chance": vulnerability_chance,
                    "turns": vulnerability_turns
                },
                attacker,
                defender
            )
        )

        var vulnerability_effect = (
            vulnerability_result["applied_effect"]
        )

        if vulnerability_effect != null:
            effects_applied.append(
                vulnerability_effect
            )
        elif vulnerability_result["resisted"]:
            resisted_effects.append(
                "vulnerability"
            )

    for hit_index in range(hits):
        var target_health_ratio_before_hit: float = (
            float(defender.health) / float(defender.max_health)
            if defender.max_health > 0
            else 0.0
        )
        var target_action_gauge_before_hit: float = (
            defender.action_gauge
        )

        var hit_multiplier := 1.0

        if not hit_multipliers.is_empty():
            hit_multiplier = hit_multipliers[hit_index]

        var condition_multiplier := 1.0

        if condition_met_at_start:
            if not conditional_hit_damage_multipliers.is_empty():
                condition_multiplier = float(
                    conditional_hit_damage_multipliers[
                        hit_index
                    ]
                )
            else:
                condition_multiplier = conditional_damage_multiplier

        var result: Dictionary = damage_calc(
            attacker,
            defender,
            hit_multiplier,
            starting_health_ratio,
            condition_multiplier
        )

        var actual_damage: int = defender.receive_damage(
            result["damage"],
            attacker
        )

        total_damage += actual_damage

        if actual_damage > 0:
            hits_landed += 1

        if result["critical"]:
            critical_hits += 1

        if (
            action_gauge_gain_if_target_low_hp_threshold > 0.0
            and defender.is_alive()
            and target_health_ratio_before_hit
            < action_gauge_gain_if_target_low_hp_threshold
        ):
            attacker.increase_action_gauge(
                action_gauge_gain_if_target_low_hp_amount
            )

        if (
            not action_gauge_reduction_if_debuff_id.is_empty()
            and defender.get_debuff(
                action_gauge_reduction_if_debuff_id
            ) != null
        ):
            defender.action_gauge = maxf(
                0.0,
                defender.action_gauge
                - action_gauge_reduction_if_debuff_amount
            )

        apply_on_hit_passives(
            attacker,
            defender,
            effects_applied
        )

        if (
            attacker.monster_id == "drake_storm"
            and attacker.resonance >= 1
            and not attacker.has_oblivion()
            and attacker.has_buff("speed_up")
            and skill_id in [
                "draconic_claw",
                "lightning_rush",
                "lightning_rush_blitz"
            ]
            and defender.is_alive()
            and randf() <= 0.10
        ):
            var short_circuit_result: Dictionary = (
                try_apply_effect(
                    {
                        "effect_id": "stun",
                        "chance": 1.00,
                        "turns": 1
                    },
                    attacker,
                    defender,
                    effects_applied
                )
            )

            var short_circuit_stun = (
                short_circuit_result["applied_effect"]
            )

            if short_circuit_stun != null:
                effects_applied.append(
                    short_circuit_stun
                )

                if attacker.resonance >= 4:
                    var stormbreak_skill = (
                        attacker.get_skill(3)
                    )

                    if stormbreak_skill != null:
                        stormbreak_skill.current_cooldown = max(
                            0,
                            stormbreak_skill.current_cooldown - 1
                        )

        if (
            action_gauge_reduction_per_hit > 0.0
            and randf() <= action_gauge_reduction_chance
        ):
            var gauge_reduction: float = (
                action_gauge_reduction_per_hit
            )

            if (
                action_gauge_threshold >= 0.0
                and target_action_gauge_before_hit
                > action_gauge_threshold
            ):
                gauge_reduction += (
                    action_gauge_bonus_reduction
                )

            defender.action_gauge = maxf(
                0.0,
                defender.action_gauge
                - gauge_reduction
            )

        if defender.is_alive():
            for effect_config in effects:
                if not _effect_triggers_on_hit(
                    effect_config,
                    hit_index
                ):
                    continue

                var effect_result: Dictionary = (
                    try_apply_effect(
                        effect_config,
                        attacker,
                        defender
                    )
                )

                var applied_effect = effect_result[
                    "applied_effect"
                ]

                if applied_effect != null:
                    effects_applied.append(
                        applied_effect
                    )
                elif effect_result["resisted"]:
                    resisted_effects.append(
                        str(effect_result["effect_id"])
                    )

    if defender.is_alive():
        for effect_config in effects:
            if effect_config.has("hit_indices"):
                continue

            if effect_config.get(
                "trigger",
                "after_skill"
            ) != "after_skill":
                continue

            var effect_result: Dictionary = try_apply_effect(
                effect_config,
                attacker,
                defender,
                effects_applied
            )

            var applied_effect = effect_result[
                "applied_effect"
            ]

            if applied_effect != null:
                effects_applied.append(applied_effect)
            elif effect_result["resisted"]:
                resisted_effects.append(
                    str(effect_result["effect_id"])
                )

    var healing: int = resolve_after_skill(
        attacker,
        defender,
        starting_burn_stacks
    )

    if (
        add_burn_if_started_with_burn
        and starting_burn_stacks > 0
        and defender.is_alive()
    ):
        var extra_burn = (
            StatusEffectFactoryScript.create_status_effect(
                "burn",
                extra_burn_turns,
                attacker,
                extra_burn_stacks
            )
        )
        defender.apply_status_effect(extra_burn)

    if (
        reset_skill_slot_if_burn_stacks > 0
        and starting_burn_stacks
        >= reset_skill_required_burn_stacks
    ):
        var skill_to_reset = attacker.get_skill(
            reset_skill_slot_if_burn_stacks
        )

        if skill_to_reset != null:
            skill_to_reset.current_cooldown = 0

    return {
        "damage": total_damage,
        "critical_hits": critical_hits,
        "hits_landed": hits_landed,
        "effects_applied": effects_applied,
        "resisted_effects": resisted_effects,
        "healing": healing
    }


func _effect_triggers_on_hit(
    effect_config: Dictionary,
    hit_index: int
) -> bool:
    if effect_config.has("hit_indices"):
        return hit_index in effect_config["hit_indices"]

    return (
        effect_config.get("trigger", "")
        == "per_hit"
    )


func execute_round_based_targets(
    attacker,
    defenders: Array
) -> Dictionary:
    var target_results: Dictionary = {}
    var removed_buffs_total := 0
    var total_damage := 0
    var total_critical_hits := 0
    var all_effects: Array = []
    var all_resisted: Array[String] = []
    var voidborn_damage_bonus := 0.0
    var voidborn_activations := 0

    for defender in defenders:
        if defender == null or not defender.is_alive():
            continue

        target_results[defender] = {
            "target": defender,
            "damage": 0,
            "critical_hits": 0,
            "hits_landed": 0,
            "effects_applied": [],
            "resisted_effects": [],
            "healing": 0,
            "buffs_removed": 0
        }

    for hit_index in range(hits):
        for defender in target_results:
            if not defender.is_alive():
                continue

            var damage_multiplier := 1.0

            if hit_index in removed_buff_damage_hit_indices:
                damage_multiplier += (
                    removed_buffs_total
                    * damage_per_removed_buff
                    + voidborn_damage_bonus
                )

            var hit_multiplier := 1.0

            if not hit_multipliers.is_empty():
                hit_multiplier = float(
                    hit_multipliers[hit_index]
                )

            var base_damage: float = base_damage_calc(
                attacker,
                defender,
                hit_multiplier,
                damage_multiplier
            )

            var critical := false
            var critical_multiplier := 1.0

            if randi_range(1, 100) <= int(
                attacker.get_effective_stat("crit_rate")
            ):
                critical = true
                critical_multiplier += (
                    attacker.get_effective_stat(
                        "crit_damage"
                    )
                    / 100.0
                )

            var final_damage: int = maxi(
                1,
                int(base_damage * critical_multiplier)
            )

            var actual_damage: int = defender.receive_damage(
                final_damage,
                attacker
            )

            var target_result: Dictionary = (
                target_results[defender]
            )

            target_result["damage"] += actual_damage
            total_damage += actual_damage

            if actual_damage > 0:
                target_result["hits_landed"] += 1

            if critical:
                target_result["critical_hits"] += 1
                total_critical_hits += 1

            apply_on_hit_passives(
                attacker,
                defender,
                target_result["effects_applied"]
            )

            if (
                hit_index == strip_buffs_hit_index
                and defender.is_alive()
            ):
                var removed_from_target: int = (
                    defender.remove_buffs_for_strip()
                )

                removed_buffs_total += removed_from_target
                target_result["buffs_removed"] += (
                    removed_from_target
                )

                if (
                    attacker.monster_id == "drake_void"
                    and attacker.resonance >= 2
                    and not attacker.has_oblivion()
                    and removed_from_target > 0
                ):
                    for _removed_buff in range(
                        removed_from_target
                    ):
                        var current_voidborn: int = (
                            attacker.add_combat_resource(
                                "voidborn",
                                1,
                                5
                            )
                        )

                        if current_voidborn < 5:
                            continue

                        attacker.consume_combat_resource(
                            "voidborn",
                            5
                        )
                        voidborn_activations += 1

                        if attacker.resonance >= 3:
                            attacker.debuffs.clear()

                        if voidborn_activations == 1:
                            var invincibility = (
                                StatusEffectFactoryScript.create_status_effect(
                                    "invincibility",
                                    2,
                                    attacker
                                )
                            )
                            attacker.apply_status_effect(
                                invincibility
                            )
                        else:
                            var existing_invincibility = (
                                attacker.get_buff(
                                    "invincibility"
                                )
                            )

                            if existing_invincibility != null:
                                existing_invincibility.remaining_turns += 1
                                existing_invincibility.duration += 1

                            voidborn_damage_bonus += 0.20

            if defender.is_alive():
                for effect_config in effects:
                    if not _effect_triggers_on_hit(
                        effect_config,
                        hit_index
                    ):
                        continue

                    var effect_result: Dictionary = (
                        try_apply_effect(
                            effect_config,
                            attacker,
                            defender
                        )
                    )

                    var applied_effect = effect_result[
                        "applied_effect"
                    ]

                    if applied_effect != null:
                        target_result[
                            "effects_applied"
                        ].append(applied_effect)
                    elif effect_result["resisted"]:
                        target_result[
                            "resisted_effects"
                        ].append(
                            str(effect_result["effect_id"])
                        )

    for defender in target_results:
        var target_result: Dictionary = (
            target_results[defender]
        )

        all_effects.append_array(
            target_result["effects_applied"]
        )
        all_resisted.append_array(
            target_result["resisted_effects"]
        )

    return {
        "success": true,
        "damage": total_damage,
        "critical_hits": total_critical_hits,
        "effects_applied": all_effects,
        "resisted_effects": all_resisted,
        "healing": 0,
        "removed_buffs": removed_buffs_total,
        "voidborn_activations": voidborn_activations,
        "target_results": target_results.values()
    }


func _get_random_hit_multiplier(
    attacker,
    target_hit_number: int
) -> float:
    if repeated_target_damage.is_empty():
        return 1.0

    var multiplier_value := 1.0
    var full_damage_hits: int = int(
        repeated_target_damage.get(
            "full_damage_hits",
            hits
        )
    )

    if target_hit_number > full_damage_hits:
        multiplier_value *= float(
            repeated_target_damage.get(
                "later_hit_multiplier",
                1.0
            )
        )

    if target_hit_number == 1:
        var first_hit_bonus: Dictionary = (
            repeated_target_damage.get(
                "first_hit_bonus_if_caster_buff",
                {}
            )
        )

        if (
            not first_hit_bonus.is_empty()
            and attacker.has_buff(
                str(first_hit_bonus.get(
                    "effect_id",
                    ""
                ))
            )
        ):
            multiplier_value *= float(
                first_hit_bonus.get(
                    "multiplier",
                    1.0
                )
            )

    return multiplier_value


func execute_random_targets(
    attacker,
    defenders: Array
) -> Dictionary:
    var living_targets: Array = defenders.filter(
        func(target): return target != null and target.is_alive()
    )

    if living_targets.is_empty():
        return {
            "success": true,
            "damage": 0,
            "critical_hits": 0,
            "effects_applied": [],
            "resisted_effects": [],
            "healing": 0,
            "target_results": []
        }

    var guaranteed_targets: Array = []

    if hit_distribution == "one_each_then_random":
        guaranteed_targets = living_targets.duplicate()
        guaranteed_targets.shuffle()

    var result_by_target: Dictionary = {}
    var hit_counts: Dictionary = {}
    var total_damage := 0
    var total_critical_hits := 0
    var all_effects: Array = []
    var all_resisted: Array[String] = []

    for _hit_index in range(hits):
        living_targets = defenders.filter(
            func(target): return target != null and target.is_alive()
        )

        if living_targets.is_empty():
            break

        var target = null

        while (
            not guaranteed_targets.is_empty()
            and not guaranteed_targets[-1].is_alive()
        ):
            guaranteed_targets.pop_back()

        if not guaranteed_targets.is_empty():
            target = guaranteed_targets.pop_back()
        else:
            target = living_targets.pick_random()

        if not result_by_target.has(target):
            result_by_target[target] = {
                "target": target,
                "damage": 0,
                "critical_hits": 0,
                "hits_landed": 0,
                "effects_applied": [],
                "resisted_effects": [],
                "healing": 0
            }
            hit_counts[target] = 0

        hit_counts[target] = int(hit_counts[target]) + 1
        var target_hit_number: int = int(hit_counts[target])

        var hit_multiplier: float = (
            _get_random_hit_multiplier(
                attacker,
                target_hit_number
            )
        )

        var damage_result: Dictionary = damage_calc(
            attacker,
            target,
            hit_multiplier
        )

        var actual_damage: int = target.receive_damage(
            int(damage_result["damage"]),
            attacker
        )

        var target_result: Dictionary = (
            result_by_target[target]
        )

        target_result["damage"] += actual_damage

        if actual_damage > 0:
            target_result["hits_landed"] += 1

        if damage_result["critical"]:
            target_result["critical_hits"] += 1
            total_critical_hits += 1

        total_damage += actual_damage

        apply_on_hit_passives(
            attacker,
            target,
            target_result["effects_applied"]
        )

    for target in result_by_target:
        var target_result: Dictionary = result_by_target[
            target
        ]

        if target.is_alive():
            for effect_config in effects:
                if effect_config.get(
                    "trigger",
                    ""
                ) != "hit_count_threshold":
                    continue

                if int(target_result["hits_landed"]) < int(
                    effect_config.get("min_hits", 1)
                ):
                    continue

                var effect_result: Dictionary = try_apply_effect(
                    effect_config,
                    attacker,
                    target
                )

                var applied_effect = effect_result[
                    "applied_effect"
                ]

                if applied_effect != null:
                    target_result["effects_applied"].append(
                        applied_effect
                    )
                elif effect_result["resisted"]:
                    target_result["resisted_effects"].append(
                        str(effect_result["effect_id"])
                    )

        all_effects.append_array(
            target_result["effects_applied"]
        )
        all_resisted.append_array(
            target_result["resisted_effects"]
        )

    return {
        "success": true,
        "damage": total_damage,
        "critical_hits": total_critical_hits,
        "effects_applied": all_effects,
        "resisted_effects": all_resisted,
        "healing": 0,
        "target_results": result_by_target.values()
    }


func execute_targets(
    attacker,
    defenders: Array
) -> Dictionary:
    attacker.on_hit_action_gauge_granted_this_skill = false

    if not is_available():
        return {
            "success": false,
            "damage": 0,
            "critical_hits": 0,
            "effects_applied": [],
            "resisted_effects": [],
            "healing": 0,
            "target_results": []
        }

    if resolve_hits_by_round:
        var round_result: Dictionary = execute_round_based_targets(
            attacker,
            defenders
        )
        trigger_cooldown()
        return round_result

    if target_type == "random_enemies":
        var random_result: Dictionary = execute_random_targets(
            attacker,
            defenders
        )
        trigger_cooldown()
        return random_result

    var total_damage := 0
    var critical_hits := 0
    var effects_applied: Array = []
    var resisted_effects: Array[String] = []
    var total_healing := 0
    var target_results: Array = []

    for defender in defenders:
        if defender == null or not defender.is_alive():
            continue

        var target_result: Dictionary = execute_on_target(
            attacker,
            defender
        )

        total_damage += target_result["damage"]
        critical_hits += target_result["critical_hits"]
        total_healing += target_result["healing"]
        effects_applied.append_array(
            target_result["effects_applied"]
        )

        resisted_effects.append_array(
            target_result["resisted_effects"]
        )

        target_results.append({
            "target": defender,
            "damage": target_result["damage"],
            "critical_hits":
                target_result["critical_hits"],
            "hits_landed":
                target_result["hits_landed"],
            "effects_applied":
                target_result["effects_applied"],
            "resisted_effects":
                target_result["resisted_effects"],
            "healing": target_result["healing"]
        })

    trigger_cooldown()

    return {
        "success": true,
        "damage": total_damage,
        "critical_hits": critical_hits,
        "effects_applied": effects_applied,
        "resisted_effects": resisted_effects,
        "healing": total_healing,
        "target_results": target_results
    }


func execute(
    attacker,
    defender
) -> Dictionary:
    return execute_targets(
        attacker,
        [defender]
    )


func get_tooltip_hit_count() -> int:
    return hits
