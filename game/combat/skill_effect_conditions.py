# =========================================================
#                    EFFECT CONDITIONS
# =========================================================

def target_has_debuff(caster, target, skill, condition, snapshot=None):
    
    effect_id = condition["effect_id"]
    state = condition.get("state", "current")

    if state == "skill_start":

        if snapshot is None:
            return False

        return (
            effect_id
            in snapshot["debuffs"]
        )

    if state == "current":

        return any(
            debuff.effect_id == effect_id
            for debuff in target.debuffs
        )

    raise ValueError(
        f"Unsupported condition state: {state}"
    )



def target_gained_debuff(
    caster,
    target,
    skill,
    condition,
    snapshot=None
):

    effect_id = condition["effect_id"]

    if snapshot is None:
        return False

    previous_stacks = 0

    if effect_id in snapshot["debuffs"]:
        previous_stacks = (
            snapshot["debuffs"][effect_id]["stacks"]
        )

    current_stacks = 0

    for debuff in target.debuffs:
        if debuff.effect_id == effect_id:
            current_stacks = debuff.stacks
            break

    return current_stacks > previous_stacks



def target_has_any_debuff(caster, target, skill, condition, snapshot=None):

    state = condition.get("state", "current")

    if state == "skill_start":

        if snapshot is None:
            return False

        return bool(snapshot["debuffs"])

    if state == "current":

        return bool(target.debuffs)

    raise ValueError(
        f"Unsupported condition state: {state}"
    )



def target_action_gauge_below( caster, target, skill, condition, snapshot=None):

    threshold = condition["threshold"]

    conditional_threshold = condition.get("threshold_if_caster_has_buff")

    if conditional_threshold:

        required_buff = conditional_threshold["effect_id"]

        has_buff = any(
            buff.effect_id == required_buff
            for buff in caster.buffs
        )

        if has_buff:
            threshold = conditional_threshold["threshold"]

    return target.action_gauge < threshold


# =========================================================
#                    CONDITION REGISTRY
# =========================================================

EFFECT_CONDITIONS = {
    "target_has_debuff": target_has_debuff,
    "target_gained_debuff": target_gained_debuff,
    "target_has_any_debuff": target_has_any_debuff,
    "target_action_gauge_below": target_action_gauge_below
}