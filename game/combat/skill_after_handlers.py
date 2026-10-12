from ..factories.status_effect_factory import create_status_effect

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
#                    BURN EXTENSION
# =========================================================

def add_burn_if_target_started_with_burn(
    caster,
    target,
    skill,
    data,
    snapshot
):

    if not target.is_alive:
        return

    starting_debuffs = snapshot.get(
        "debuffs",
        {}
    )

    if "burn" not in starting_debuffs:
        return

    extra_burn = create_status_effect(
        effect_id="burn",
        duration=data.get("turns", 3),
        stacks=data.get("stacks", 1),
        source=caster
    )

    target.apply_status_effect(
        extra_burn
    )


# =========================================================
#                      HANDLER REGISTRY
# =========================================================

AFTER_SKILL_HANDLERS = {
    "consume_burn_and_heal": consume_burn_and_heal,
    "reset_cooldown_by_burn_stacks":
        reset_cooldown_by_burn_stacks,
    "add_burn_if_target_started_with_burn":
        add_burn_if_target_started_with_burn
}

