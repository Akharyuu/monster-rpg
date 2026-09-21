# =========================================================
#                     HEALING HANDLERS
# =========================================================

def heal_lowest_hp_ally(caster, skill, data, context, skill_result):

    team = context["team"]

    living_allies = [
        ally
        for ally in team
        if ally.is_alive
    ]

    if not living_allies:
        return None

    target = min(
        living_allies,
        key=lambda ally: ally.health / ally.max_health
    )

    heal_amount = int(
        caster.max_health * data["max_health_ratio"]
    )

    actual_heal = target.heal(heal_amount)

    return {
        "type": "heal",
        "target": target,
        "value": actual_heal
    }


# =========================================================
#                      HANDLER REGISTRY
# =========================================================

AFTER_USE_HANDLERS = {
    "heal_lowest_hp_ally": heal_lowest_hp_ally
}