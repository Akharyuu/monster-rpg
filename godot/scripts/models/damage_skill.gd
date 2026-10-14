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

# Optional handler-like data used by the first playable slice.
var damage_for_burn_stacks: Dictionary = {}
var consume_burn_and_heal: Dictionary = {}
var action_gauge_reduction_per_hit: float = 0.0


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
    p_action_gauge_reduction_per_hit: float = 0.0
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

    return maxf(
        1.0,
        raw_damage
        * damage_reduction
        * attribute_modifier
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
    hit_multiplier: float = 1.0
) -> Dictionary:
    var bonus_damage: float = get_burn_damage_multiplier(
        defender
    )

    var base_damage: float = base_damage_calc(
        attacker,
        defender,
        hit_multiplier,
        bonus_damage
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
    defender
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
        _:
            return true


func try_apply_effect(
    effect_config: Dictionary,
    attacker,
    defender
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
        defender
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
    var effects_applied: Array = []
    var resisted_effects: Array[String] = []

    var starting_burn_stacks: int = (
        defender.get_debuff_stacks("burn")
    )

    for hit_index in range(hits):
        var hit_multiplier := 1.0

        if not hit_multipliers.is_empty():
            hit_multiplier = hit_multipliers[hit_index]

        var result: Dictionary = damage_calc(
            attacker,
            defender,
            hit_multiplier
        )

        total_damage += defender.receive_damage(
            result["damage"]
        )

        if result["critical"]:
            critical_hits += 1

        apply_on_hit_passives(
            attacker,
            defender,
            effects_applied
        )

        if action_gauge_reduction_per_hit > 0.0:
            defender.action_gauge = maxf(
                0.0,
                defender.action_gauge
                - action_gauge_reduction_per_hit
            )

        if defender.is_alive():
            for effect_config in effects:
                if effect_config.get(
                    "trigger",
                    "after_skill"
                ) != "per_hit":
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
            if effect_config.get(
                "trigger",
                "after_skill"
            ) != "after_skill":
                continue

            var effect_result: Dictionary = try_apply_effect(
                effect_config,
                attacker,
                defender
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

    return {
        "damage": total_damage,
        "critical_hits": critical_hits,
        "effects_applied": effects_applied,
        "resisted_effects": resisted_effects,
        "healing": healing
    }


func execute_targets(
    attacker,
    defenders: Array
) -> Dictionary:
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
