# =========================================================
#                    EFFECT CONDITIONS
# =========================================================

def target_has_debuff(caster, target, skill, condition):
    
    effect_id = condition["effect_id"]

    return any(
        debuff.effect_id == effect_id
        for debuff in target.debuffs
    )


# =========================================================
#                    CONDITION REGISTRY
# =========================================================

EFFECT_CONDITIONS = {
    "target_has_debuff": target_has_debuff
}