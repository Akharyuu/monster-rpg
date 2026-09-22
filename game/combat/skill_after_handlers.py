# =========================================================
#                      BURN HANDLERS
# =========================================================

def consume_burn_and_heal(caster, target, skill, data, context):

    initial_burn_stacks = (
        context
        .get("debuffs", {})
        .get("burn", {})
        .get("stacks", 0)
    )

    if initial_burn_stacks == 0:
        return

    burn_effect = None

    for debuff in target.debuffs:
        if debuff.effect_id == "burn":
            burn_effect = debuff
            break

    # Consume only the Burn stacks that existed before the skill.
    if burn_effect is not None:

        burn_effect.stacks -= initial_burn_stacks

        if burn_effect.stacks <= 0:
            target.debuffs.remove(burn_effect)

    heal_ratio = data["heal_by_stacks"][initial_burn_stacks]

    heal_amount = int(caster.max_health * heal_ratio)

    caster.heal(heal_amount)



def reset_cooldown_by_burn_stacks(caster, target, skill, data, context):

    initial_burn_stacks = (
        context
        .get("debuffs", {})
        .get("burn", {})
        .get("stacks", 0)
    )

    if initial_burn_stacks < data["required_stacks"]:
        return

    target_skill = caster.get_skill(
        data["skill_slot"]
    )

    if target_skill is None:
        return

    target_skill.current_cooldown = 0

    
# =========================================================
#                      HANDLER REGISTRY
# =========================================================

AFTER_SKILL_HANDLERS = {
    "consume_burn_and_heal": consume_burn_and_heal,
    "reset_cooldown_by_burn_stacks": reset_cooldown_by_burn_stacks
}

