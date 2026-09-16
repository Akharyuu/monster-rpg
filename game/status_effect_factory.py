from .data.status_effect_data import STATUS_EFFECT_DATA
from .models.status_effect import StatusEffect

def create_status_effect(
    effect_id,
    duration,
    source=None,
    stacks=1
):
    effect_data = STATUS_EFFECT_DATA[effect_id]

    return StatusEffect(
        effect_id=effect_id,
        name=effect_data["name"],
        stat=effect_data["stat"],
        effect_type=effect_data["effect_type"],
        modifier=effect_data["modifier"],
        duration=duration,
        stacks=stacks,
        max_stacks=effect_data.get("max_stacks", 1),
        source=source,
        modifier_mode=effect_data.get(
            "modifier_mode",
            "multiplicative"
        )
    )