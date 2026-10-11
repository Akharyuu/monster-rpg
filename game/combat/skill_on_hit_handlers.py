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
#                      HANDLER REGISTRY
# =========================================================

ON_HIT_HANDLERS = {
    "reduce_action_gauge": reduce_action_gauge,
    "reduce_action_gauge_if_debuff":
        reduce_action_gauge_if_debuff
}

