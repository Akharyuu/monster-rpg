class_name SupportSkill
extends Skill

const StatusEffectFactoryScript = preload(
    "res://scripts/factories/status_effect_factory.gd"
)

var buffs_to_apply: Array = []
var healing_hp_ratio: float = 0.0


func _init(
    p_skill_id: String,
    p_name: String,
    p_cooldown: int = 0,
    p_buffs_to_apply: Array = [],
    p_target_type: String = "all_allies"
) -> void:
    super(
        p_skill_id,
        p_name,
        p_cooldown,
        p_target_type
    )

    buffs_to_apply = p_buffs_to_apply


func execute_targets(
    caster,
    targets: Array
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

    var effects_applied: Array = []
    var target_results: Array = []
    var total_healing: int = 0

    for target in targets:
        if target == null or not target.is_alive():
            continue

        var target_effects: Array = []
        var target_healing: int = 0

        if healing_hp_ratio > 0.0:
            var intended_heal: int = int(
                caster.get_healing_hp()
                * healing_hp_ratio
                * caster.get_direct_heal_multiplier(target)
            )

            target_healing = target.heal(
                intended_heal
            )
            total_healing += target_healing

        for buff_config in buffs_to_apply:
            var status_effect = (
                StatusEffectFactoryScript.create_status_effect(
                    str(buff_config["effect_id"]),
                    int(buff_config["turns"]),
                    caster,
                    int(buff_config.get("stacks", 1))
                )
            )

            var applied_effect = target.apply_status_effect(
                status_effect
            )

            if applied_effect != null:
                target_effects.append(applied_effect)
                effects_applied.append(applied_effect)

        target_results.append({
            "target": target,
            "damage": 0,
            "critical_hits": 0,
            "effects_applied": target_effects,
            "resisted_effects": [],
            "healing": target_healing
        })

    trigger_cooldown()

    return {
        "success": true,
        "damage": 0,
        "critical_hits": 0,
        "effects_applied": effects_applied,
        "resisted_effects": [],
        "healing": total_healing,
        "target_results": target_results
    }
