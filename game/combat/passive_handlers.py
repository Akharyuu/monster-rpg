import random

from ..data.passive_data import PASSIVE_DATA
from ..factories.status_effect_factory import create_status_effect
from ..combat.telemetry import record_telemetry


# =========================================================
#                      SELF BUFFS
# =========================================================

def apply_self_buff(owner, context, passive):

    data = passive.handler_data

    trigger_chance = random.random()

    if trigger_chance > data.get("chance", 1.00):
        return

    status_effect = create_status_effect(
        effect_id=data["effect_id"],
        duration=data["turns"],
        stacks=data.get("stacks", 1),
        source=owner
    )

    owner.apply_status_effect(status_effect)


# =========================================================
#                         BURN
# =========================================================

def apply_burn(owner, context, passive):

    data = PASSIVE_DATA[passive.skill_id]

    # Some passives can grant Action Gauge only once during a skill use.
    # before_skill resets that temporary flag for the new action.
    if context.get("trigger") == "before_skill":

        if data.get(
            "action_gauge_once_per_skill",
            False
        ):
            passive.action_gauge_granted_this_skill = False

        return

    target = context["target"]

    chance = random.random()

    if chance <= data["chance"]:

        burn = create_status_effect(
            effect_id="burn",
            duration=data["turns"],
            stacks=data.get("stacks", 1),
            source=owner
        )

        applied_effect = target.apply_status_effect(burn)

        if applied_effect:
            action_gauge_gain = data.get(
                "action_gauge",
                0
            )

            once_per_skill = data.get(
                "action_gauge_once_per_skill",
                False
            )

            already_granted = getattr(
                passive,
                "action_gauge_granted_this_skill",
                False
            )

            can_gain_gauge = (
                action_gauge_gain > 0
                and (
                    not once_per_skill
                    or not already_granted
                )
            )

            if can_gain_gauge:
                owner.increase_action_gauge(
                    action_gauge_gain
                )

                if once_per_skill:
                    passive.action_gauge_granted_this_skill = True


# =========================================================
#                         STUN
# =========================================================

def stun_on_hit_if_buff(owner, context, passive):

    data = passive.handler_data

    skill = context.get("skill")
    target = context.get("target")

    if skill is None or target is None:
        return

    if skill.skill_id not in data["allowed_skill_ids"]:
        return

    has_required_buff = any(
        buff.effect_id == data["required_buff"]
        for buff in owner.buffs
    )

    if not has_required_buff:
        return

    if random.random() > data["chance"]:
        return

    stun = create_status_effect(
        effect_id="stun",
        duration=data["turns"],
        source=owner
    )

    applied_effect = target.apply_status_effect(
        stun
    )

    if applied_effect is None:
        return

    on_success = data.get("on_success")

    if on_success is None:
        return

    cooldown_reduction = on_success.get("reduce_skill_cooldown")

    if cooldown_reduction is not None:

        skill_ids = cooldown_reduction["skill_ids"]

        amount = cooldown_reduction["amount"]

        for owned_skill in owner.skills:

            if owned_skill.skill_id in skill_ids:

                owned_skill.current_cooldown = max( 0, owned_skill.current_cooldown - amount )

                break


# =========================================================
#                     FROZEN SCALES
# =========================================================

def frozen_scales(owner, context, passive):

    data = PASSIVE_DATA[passive.skill_id]

    skill = context["skill"]
    trigger = context["trigger"]

    # Frozen Scales only reacts to S3.
    if owner.get_skill(3) is not skill:
        return

    # BEFORE SKILL
    if trigger == "before_skill":

        current_scales = owner.get_combat_resource(
            "frozen_scales"
        )

        # By default, this execution can generate Frozen Scales.
        context["block_frozen_scales_generation"] = False

        # If S3 starts with 3 scales, consume them and activate the buffs.
        if current_scales >= data["required_scales"]:

            owner.consume_combat_resource(
                "frozen_scales",
                data["required_scales"]
            )

            context["block_frozen_scales_generation"] = True

            for buff_config in data["buffs"]:

                effect_id = buff_config["effect_id"]

                status_effect = create_status_effect(
                    effect_id=effect_id,
                    duration=buff_config["turns"],
                    source=owner
                )

                owner.apply_status_effect(status_effect)

        return

    # AFTER SKILL
    if trigger == "after_skill":

        # The S3 that consumed 3 scales cannot generate new ones.
        if context.get(
            "block_frozen_scales_generation",
            False
        ):
            return

        skill_result = context.get("skill_result")

        if skill_result is None or not skill_result.success:
            return

        scales_gained = 0

        # Each enemy successfully Frozen by this S3 gives 1 scale.
        for target_result in skill_result.target_results:

            effects_applied = target_result["effects_applied"]

            froze_target = False

            for effect in effects_applied:
                if effect.effect_id == "freeze":
                    froze_target = True
                    break

            if froze_target:
                scales_gained += 1

        if scales_gained > 0:
            owner.add_combat_resource(
                "frozen_scales",
                scales_gained,
                data["max_scales"]
            )

            current_scales = owner.get_combat_resource(
                "frozen_scales"
            )

            # Everfrost: reaching max Frozen Scales resets S3 cooldown.
            reset_skill_slot = data.get(
                "reset_cooldown_skill_slot"
            )

            if (
                reset_skill_slot is not None
                and current_scales >= data["max_scales"]
            ):
                skill_to_reset = owner.get_skill(
                    reset_skill_slot
                )

                if skill_to_reset is not None:
                    skill_to_reset.current_cooldown = 0


# =========================================================
#                     SHATTERED FURY
# =========================================================

def shattered_fury(owner, context, passive):

    data = PASSIVE_DATA[passive.skill_id]

    attacker = context["attacker"]

    for buff_config in data["buffs"]:

        effect_id = buff_config["effect_id"]

        buff = create_status_effect(
            effect_id=effect_id,
            duration=buff_config["turns"],
            source=owner
        )

        attacker.apply_status_effect(buff)

    attacker.increase_action_gauge(
        data["action_gauge"]
    )





# =========================================================
#                  AETHER DRAKE PASSIVES
# =========================================================

def celestial_authority(owner, context, passive):

    attacker = context.get("attacker")

    if attacker is None or not attacker.is_alive:
        return

    data = passive.handler_data

    if random.random() > data["chance"]:
        return

    accuracy = owner.get_effective_stat(
        "accuracy"
    )

    resistance = attacker.get_effective_stat(
        "resistance"
    )

    resist_chance = max(
        15,
        resistance - accuracy
    )

    resist_chance = min(
        100,
        resist_chance
    )

    if random.uniform(0, 100) < resist_chance:
        return

    attack_break = create_status_effect(
        effect_id="attack_break",
        duration=data["turns"],
        source=owner
    )

    applied_effect = attacker.apply_status_effect(
        attack_break
    )

    if applied_effect is None:
        return

    action_gauge = data.get(
        "action_gauge_to_most_buffed_ally",
        0
    )

    if action_gauge <= 0:
        return

    team = getattr(
        owner,
        "_combat_team",
        [owner]
    )

    living_team = [
        ally
        for ally in team
        if ally.is_alive
    ]

    if not living_team:
        return

    target_ally = max(
        living_team,
        key=lambda ally: len(ally.buffs)
    )

    target_ally.increase_action_gauge(
        action_gauge
    )



def divine_grace(owner, context, passive):

    target = context.get("target")

    if target is None or not target.is_alive:
        return

    data = passive.handler_data

    heal_amount = int(
        target.max_health
        * data["heal_ratio_per_buff"]
    )

    actual_heal = target.heal(
        heal_amount
    )

    record_telemetry(
        context.get("telemetry"),
        owner,
        "healing",
        actual_heal
    )


# =========================================================
#                   VOID DRAKE PASSIVES
# =========================================================

def bottomless_hunger(owner, context, passive):

    removed_count = context.get(
        "removed_count",
        0
    )

    if removed_count <= 0:
        return

    data = passive.handler_data

    record_telemetry(
        context.get("telemetry"),
        owner,
        "bottomless_hunger_activations",
        1
    )

    for _ in range(removed_count):

        heal_amount = int(
            owner.max_health
            * data["heal_ratio_per_buff"]
        )

        actual_heal = owner.heal(
            heal_amount
        )

        record_telemetry(
            context.get("telemetry"),
            owner,
            "healing",
            actual_heal
        )

        action_gauge_gain = data[
            "action_gauge_per_buff"
        ]

        owner.increase_action_gauge(
            action_gauge_gain
        )

        record_telemetry(
            context.get("telemetry"),
            owner,
            "action_gauge_from_bottomless_hunger",
            action_gauge_gain
        )



def voidborn(owner, context, passive):

    removed_count = context.get(
        "removed_count",
        0
    )

    if removed_count <= 0:
        return

    data = passive.handler_data

    max_stacks = data["max_stacks"]

    for _ in range(removed_count):

        owner.add_combat_resource(
            "voidborn",
            1,
            max_stacks
        )

        if owner.get_combat_resource(
            "voidborn"
        ) < max_stacks:
            continue

        owner.consume_combat_resource(
            "voidborn",
            max_stacks
        )

        record_telemetry(
            context.get("telemetry"),
            owner,
            "voidborn_activations",
            1
        )

        if data.get(
            "full_cleanse_on_activation",
            False
        ):
            owner.reset_debuffs()

        invincibility = create_status_effect(
            effect_id="invincibility",
            duration=data["invincibility_turns"],
            source=owner
        )

        owner.apply_status_effect(
            invincibility
        )


# =========================================================
#                      HANDLER REGISTRY
# =========================================================

PASSIVE_HANDLERS = {
    "apply_self_buff": apply_self_buff,
    "apply_burn": apply_burn,
    "stun_on_hit_if_buff": stun_on_hit_if_buff,
    "frozen_scales": frozen_scales,
    "shattered_fury": shattered_fury,
    "celestial_authority": celestial_authority,
    "divine_grace": divine_grace,
    "bottomless_hunger": bottomless_hunger,
    "voidborn": voidborn
}

