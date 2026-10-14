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

        "speed_break":
            return StatusEffectScript.new(
                "speed_break",
                "Speed Break",
                "speed",
                "debuff",
                0.7,
                duration,
                stacks,
                1,
                source,
                "multiplicative"
            )

        "defense_up":
            return StatusEffectScript.new(
                "defense_up",
                "Defense Up",
                "defense",
                "buff",
                1.3,
                duration,
                stacks,
                1,
                source,
                "multiplicative"
            )

        "attack_up":
            return StatusEffectScript.new(
                "attack_up",
                "Attack Up",
                "attack",
                "buff",
                1.3,
                duration,
                stacks,
                1,
                source,
                "multiplicative"
            )

        "veil":
            return StatusEffectScript.new(
                "veil",
                "Veil",
                null,
                "buff",
                null,
                duration,
                stacks,
                1,
                source,
                "multiplicative"
            )

        "attack_break":
            return StatusEffectScript.new(
                "attack_break",
                "Attack Break",
                "attack",
                "debuff",
                0.7,
                duration,
                stacks,
                1,
                source,
                "multiplicative"
            )

        "immunity":
            return StatusEffectScript.new(
                "immunity",
                "Immunity",
                null,
                "buff",
                null,
                duration,
                stacks,
                1,
                source,
                "multiplicative"
            )

        "burn":
            return StatusEffectScript.new(
                "burn",
                "Burn",
                null,
                "debuff",
                null,
                duration,
                stacks,
                3,
                source,
                "multiplicative"
            )

        "stun":
            return StatusEffectScript.new(
                "stun",
                "Stun",
                null,
                "debuff",
                null,
                duration,
                stacks,
                1,
                source,
                "multiplicative"
            )

        "freeze":
            return StatusEffectScript.new(
                "freeze",
                "Freeze",
                null,
                "debuff",
                null,
                duration,
                stacks,
                1,
                source,
                "multiplicative"
            )

        "silence":
            return StatusEffectScript.new(
                "silence",
                "Silence",
                null,
                "debuff",
                null,
                duration,
                stacks,
                1,
                source,
                "multiplicative"
            )

        _:
            push_error("Unknown status effect id: %s" % effect_id)
            return null
