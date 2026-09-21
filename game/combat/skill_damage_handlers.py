# =========================================================
#                      BURN DAMAGE
# =========================================================

def damage_for_burn_stacks(attacker, target, skill):

    for debuff in target.debuffs:

        if debuff.effect_id != "burn":
            continue

        multiplier = skill.damage_handler_data["multipliers_by_stacks"][debuff.stacks]

        result = {
            "damage_multiplier": multiplier
        }

        ignore_defense_at = (skill.damage_handler_data.get("ignore_defense_at_stacks"))

        if (
            ignore_defense_at is not None
            and debuff.stacks >= ignore_defense_at
        ):
            result["ignore_defense"] = True

        return result

    return {
        "damage_multiplier": 1
    }


# =========================================================
#                      HANDLER REGISTRY
# =========================================================

DAMAGE_HANDLERS = {
    "damage_for_burn_stacks": damage_for_burn_stacks
}

