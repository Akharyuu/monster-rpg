import random

from ..data.status_effect_data import STATUS_EFFECT_DATA
from ..factories.status_effect_factory import create_status_effect


# =========================================================
#                    SPECIAL MARK HANDLERS
# =========================================================

def apply_named_and_vulnerability(
    caster,
    target,
    skill,
    data,
    target_result
):

    caster.apply_named(
        target,
        turns=data.get(
            "named_turns",
            2
        )
    )

    effect = {
        "effect_id": "vulnerability",
        "chance": data.get(
            "vulnerability_chance",
            1.0
        ),
        "turns": data.get(
            "vulnerability_turns",
            2
        )
    }

    applied_effect = skill.try_apply_effect(
        effect,
        caster,
        target,
        target_result.get(
            "snapshot"
        ),
        target_result.get(
            "telemetry"
        )
    )

    if applied_effect is not None:
        target_result[
            "effects_applied"
        ].append(
            applied_effect
        )


# =========================================================
#                      HANDLER REGISTRY
# =========================================================

BEFORE_HIT_HANDLERS = {
    "apply_named_and_vulnerability":
        apply_named_and_vulnerability
}
