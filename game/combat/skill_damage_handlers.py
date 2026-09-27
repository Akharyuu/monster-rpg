from ..combat.skill_effect_conditions import EFFECT_CONDITIONS


# =========================================================
#                     CONDITION DAMAGE
# =========================================================

def damage_if_condition(attacker, target, skill, snapshot, hit_index):

    data = skill.damage_handler_data
    condition = data["condition"]

    condition_handler = EFFECT_CONDITIONS[condition["type"]]

    condition_met = condition_handler(
        attacker,
        target,
        skill,
        condition,
        snapshot
    )

    if not condition_met:
        return {
            "damage_multiplier": 1
        }

    # Case 1: same multiplier for every hit.
    if "damage_multiplier" in data:
        return {
            "damage_multiplier": data["damage_multiplier"]
        }

    # Case 2: different multiplier depending on the hit.
    if "multipliers_by_hit" in data:

        hit_number = hit_index + 1

        return {
            "damage_multiplier": data["multipliers_by_hit"][hit_number]
        }

    return {
        "damage_multiplier": 1
    }


# =========================================================
#                    BURN STACKS DAMAGE
# =========================================================

def damage_for_burn_stacks(attacker, target, skill, snapshot, hit_index):

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
#                       STAT SCALING
# =========================================================

def damage_with_speed_scaling(attacker, target, skill, snapshot, hit_index):

    data = skill.damage_handler_data

    effective_speed = attacker.get_effective_stat("speed")

    damage_multiplier = ( 1 + effective_speed * data["speed_scaling"] )

    return {
        "damage_multiplier": damage_multiplier
    }


# =========================================================
#                     HANDLER REGISTRY
# =========================================================

DAMAGE_HANDLERS = {
    "damage_for_burn_stacks": damage_for_burn_stacks,
    "damage_if_condition": damage_if_condition,
    "damage_with_speed_scaling": damage_with_speed_scaling
}

