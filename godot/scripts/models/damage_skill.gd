class_name DamageSkill
extends Skill

var multiplier: float
var hits: int
var hit_multipliers: Array[float]
var scaling_stat: String


func _init(
    p_skill_id: String,
    p_name: String,
    p_multiplier: float,
    p_hits: int = 1,
    p_hit_multipliers: Array[float] = [],
    p_scaling_stat: String = "attack",
    p_cooldown: int = 0
) -> void:
    super(p_skill_id, p_name, p_cooldown)

    multiplier = p_multiplier
    hits = p_hits
    hit_multipliers = p_hit_multipliers
    scaling_stat = p_scaling_stat


func base_damage_calc(
    attacker: Monster,
    defender: Monster,
    hit_multiplier: float = 1.0,
    damage_multiplier: float = 1.0,
    ignore_defense: bool = false,
    defense_ignore_ratio: float = 0.0,
    bonus_raw_damage: float = 0.0
) -> float:
    var effective_scaling_stat := attacker.get_effective_stat(
        scaling_stat
    )

    if scaling_stat == "max_health":
        effective_scaling_stat *= 0.08

    var raw_damage := (
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
        var effective_defense := defender.get_effective_stat(
            "defense"
        )

        effective_defense *= maxf(
            0.0,
            1.0 - defense_ignore_ratio
        )

        damage_reduction = (
            1000.0
            / (1000.0 + effective_defense)
        )

    var attribute_modifier := (
        attacker.get_attribute_modifier(defender)
    )

    return maxf(
        1.0,
        raw_damage
        * damage_reduction
        * attribute_modifier
    )


func damage_calc(
    attacker: Monster,
    defender: Monster,
    hit_multiplier: float = 1.0
) -> Dictionary:
    var base_damage := base_damage_calc(
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

    var final_damage := maxi(
        1,
        int(base_damage * critical_damage_bonus)
    )

    return {
        "damage": final_damage,
        "critical": critical
    }


func execute(
    attacker: Monster,
    defender: Monster
) -> Dictionary:
    if not is_available():
        return {
            "success": false,
            "damage": 0,
            "critical_hits": 0
        }

    var total_damage := 0
    var critical_hits := 0

    for hit_index in range(hits):
        var hit_multiplier := 1.0

        if not hit_multipliers.is_empty():
            hit_multiplier = hit_multipliers[hit_index]

        var result := damage_calc(
            attacker,
            defender,
            hit_multiplier
        )

        total_damage += defender.receive_damage(
            result["damage"]
        )

        if result["critical"]:
            critical_hits += 1

    trigger_cooldown()

    return {
        "success": true,
        "damage": total_damage,
        "critical_hits": critical_hits
    }
