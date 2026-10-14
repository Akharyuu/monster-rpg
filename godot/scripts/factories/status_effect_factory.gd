class_name StatusEffectFactory
extends RefCounted

const StatusEffectScript = preload(
    "res://scripts/models/status_effect.gd"
)


static func create_status_effect(
    effect_id: String,
    duration: int,
    source = null,
    stacks: int = 1
):
    match effect_id:
        "defense_break":
            return StatusEffectScript.new(
                "defense_break",
                "Defense Break",
                "defense",
                "debuff",
                0.7,
                duration,
                stacks,
                1,
                source,
                "multiplicative"
            )

        _:
            push_error("Unknown status effect id: %s" % effect_id)
            return null
