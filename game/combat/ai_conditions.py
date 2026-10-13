# =========================================================
#                    SETUP CONDITIONS
# =========================================================

def target_has_debuff(requirement, context):

    opponents = context["opponents"]

    if requirement["scope"] == "any_enemy":

        return any(
            requirement["effect_id"] == debuff.effect_id
            for opponent in opponents
            if opponent.is_alive
            for debuff in opponent.debuffs
        )

    raise ValueError(
        f"Unsupported AI scope: {requirement['scope']}"
    )



def target_debuff_stacks(requirement, context):

    opponents = context["opponents"]

    if requirement["scope"] == "any_enemy":

        required_effect_id = requirement["effect_id"]
        required_stacks = requirement["stacks"]

        return any(
            debuff.effect_id == required_effect_id
            and debuff.stacks >= required_stacks
            for opponent in opponents
            if opponent.is_alive
            for debuff in opponent.debuffs
        )

    raise ValueError(
        f"Unsupported AI scope: {requirement['scope']}"
    )



def ally_dead_exists(requirement, context):

    team = context["team"]

    return any(
        not ally.is_alive
        for ally in team
    )



def ally_dead_exists(requirement, context):

    team = context["team"]

    return any(
        not ally.is_alive
        for ally in team
    )


def target_has_buff(requirement, context):

    opponents = context["opponents"]

    scope = requirement.get(
        "scope",
        "any_enemy"
    )

    if scope == "any_enemy":

        return any(
            opponent.buffs
            for opponent in opponents
            if opponent.is_alive
        )

    raise ValueError(
        f"Unsupported AI scope: {scope}"
    )


# =========================================================
#                    CONDITION REGISTRY
# =========================================================

AI_CONDITIONS = {
    "target_has_debuff": target_has_debuff,
    "target_debuff_stacks": target_debuff_stacks,
    "target_has_buff": target_has_buff,
    "ally_dead_exists": ally_dead_exists
}