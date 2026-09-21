# =========================================================
#                    ACTION GAUGE HANDLERS
# =========================================================

def reduce_action_gauge(caster, target, skill, data):
    
    target.reduce_action_gauge(data["amount"])


# =========================================================
#                      HANDLER REGISTRY
# =========================================================

ON_HIT_HANDLERS = {
    "reduce_action_gauge": reduce_action_gauge
}

