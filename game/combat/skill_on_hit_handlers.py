import random

from ..combat.passive_triggers import trigger_passives
from ..factories.status_effect_factory import create_status_effect

# =========================================================
#                    ACTION GAUGE HANDLERS
# =========================================================

def reduce_action_gauge(caster, target, skill, data):
    
    target.reduce_action_gauge(data["amount"])


def reduce_action_gauge_if_debuff(
    caster,
    target,
    skill,
    data
):

    required_debuff = data["effect_id"]

    has_required_debuff = any(
        debuff.effect_id == required_debuff
        for debuff in target.debuffs
    )

    if not has_required_debuff:
        return

    target.reduce_action_gauge(
        data["amount"]
    )




# =========================================================
#                     DEBUFF HANDLERS
# =========================================================

def apply_debuff_on_hit_indices(
    caster,
    target,
    skill,
    data
):

    hit_index = data.get(
        "_hit_index"
    )

    if hit_index not in data["hit_indices"]:
        return

    if random.random() > data["chance"]:
        return

    accuracy = caster.get_effective_stat(
        "accuracy"
    )

    resistance = target.get_effective_stat(
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

    effect = create_status_effect(
        effect_id=data["effect_id"],
        duration=data["turns"],
        source=caster
    )

    target.apply_status_effect(
        effect
    )


# =========================================================
#                       STRIP HANDLERS
# =========================================================

def strip_buffs_on_hit(
    caster,
    target,
    skill,
    data
):

    hit_index = data.get(
        "_hit_index"
    )

    if hit_index != data.get(
        "hit_index",
        0
    ):
        return

    veil = next(
        (
            buff
            for buff in target.buffs
            if buff.effect_id == "veil"
        ),
        None
    )

    if veil is not None:
        target.buffs.remove(
            veil
        )
        return

    removed_count = len(
        target.buffs
    )

    if removed_count <= 0:
        return

    target.buffs = []

    trigger_passives(
        "on_remove_enemy_buff",
        caster,
        {
            "target": target,
            "removed_count": removed_count,
            "skill": skill
        }
    )


# =========================================================
#                      HANDLER REGISTRY
# =========================================================

ON_HIT_HANDLERS = {
    "reduce_action_gauge": reduce_action_gauge,
    "reduce_action_gauge_if_debuff":
        reduce_action_gauge_if_debuff,
    "apply_debuff_on_hit_indices":
        apply_debuff_on_hit_indices,
    "strip_buffs_on_hit":
        strip_buffs_on_hit
}

