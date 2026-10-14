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


func _init(
    p_skill_id: String,
    p_name: String,
    p_multiplier: float,
    p_hits: int = 1,
    p_hit_multipliers: Array = [],
    p_scaling_stat: String = "attack",
    p_cooldown: int = 0,
    p_effects: Array = []
) -> void:
    super(p_skill_id, p_name, p_cooldown)

    multiplier = p_multiplier
    hits = p_hits
    hit_multipliers = p_hit_multipliers
    scaling_stat = p_scaling_stat
    effects = p_effects


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

        # Calibrated against the current level-50 roster.
        # The reference scales with monster level so DEF remains
        # relevant at low levels instead of collapsing toward zero.
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


func damage_calc(
    attacker,
    defender,
    hit_multiplier: float = 1.0
) -> Dictionary:
    var base_damage: float = base_damage_calc(
        attacker,
        defender,
        hit_multiplier
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


func try_apply_effect(
    effect_config: Dictionary,
    attacker,
    defender
):
    var chance: float = float(
        effect_config.get("chance", 1.0)
    )

    if randf() > chance:
        return null

    var effect_id: String = effect_config["effect_id"]
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
            return null

    var status_effect = (
        StatusEffectFactoryScript.create_status_effect(
            effect_id,
            int(effect_config["turns"]),
            attacker,
            int(effect_config.get("stacks", 1))
        )
    )

    if status_effect == null:
        return null

    if status_effect.effect_type == "buff":
        return attacker.apply_status_effect(status_effect)

    return defender.apply_status_effect(status_effect)


func execute(
    attacker,
    defender
) -> Dictionary:
    if not is_available():
        return {
            "success": false,
            "damage": 0,
            "critical_hits": 0,
            "effects_applied": []
        }

    var total_damage := 0
    var critical_hits := 0
    var effects_applied: Array = []

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

    if defender.is_alive():
        for effect_config in effects:
            if effect_config.get(
                "trigger",
                "after_skill"
            ) != "after_skill":
                continue

            var applied_effect = try_apply_effect(
                effect_config,
                attacker,
                defender
            )

            if applied_effect != null:
                effects_applied.append(applied_effect)

    trigger_cooldown()

    return {
        "success": true,
        "damage": total_damage,
        "critical_hits": critical_hits,
        "effects_applied": effects_applied
    }
