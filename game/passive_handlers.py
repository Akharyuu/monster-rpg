from .status_effect_data import STATUS_EFFECT_DATA
from .status_effect import StatusEffect
from .passive_data import PASSIVE_DATA
import random

def apply_burn(owner, context, passive):
    target = context["target"]

    chance = random.random()

    data = PASSIVE_DATA[passive.skill_id]

    if chance <= data["chance"]:
        burn_data = STATUS_EFFECT_DATA["burn"]

        burn = StatusEffect(
            effect_id="burn",
            name=burn_data["name"],
            stat=burn_data["stat"],
            effect_type=burn_data["effect_type"],
            modifier=burn_data["modifier"],
            duration=data["turns"],
            stacks=data["stacks"],
            max_stacks=burn_data["max_stacks"]
        )

        applied_effect = target.apply_status_effect(burn)

        if applied_effect:
            action_gauge_gain = data.get("action_gauge", 0)

            if action_gauge_gain > 0:
                owner.increase_action_gauge(action_gauge_gain)


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
                effect_data = STATUS_EFFECT_DATA[effect_id]

                status_effect = StatusEffect(
                    effect_id=effect_id,
                    name=effect_data["name"],
                    stat=effect_data["stat"],
                    effect_type=effect_data["effect_type"],
                    modifier=effect_data["modifier"],
                    duration=buff_config["turns"],
                    stacks=1,
                    max_stacks=effect_data.get("max_stacks", 1)
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


def shattered_fury(owner, context, passive):

    data = PASSIVE_DATA[passive.skill_id]

    attacker = context["attacker"]

    for buff_config in data["buffs"]:

        effect_id = buff_config["effect_id"]
        effect_data = STATUS_EFFECT_DATA[effect_id]

        buff = StatusEffect(
            effect_id=effect_id,
            name=effect_data["name"],
            stat=effect_data["stat"],
            effect_type=effect_data["effect_type"],
            modifier=effect_data["modifier"],
            duration=buff_config["turns"],
            stacks=1,
            max_stacks=effect_data.get("max_stacks", 1),
            source=owner,
            modifier_mode=effect_data.get("modifier_mode", "multiplicative")
        )

        attacker.apply_status_effect(buff)

    attacker.increase_action_gauge(
        data["action_gauge"]
    )





PASSIVE_HANDLERS = {
    "apply_burn": apply_burn,
    "frozen_scales": frozen_scales,
    "shattered_fury": shattered_fury
}

