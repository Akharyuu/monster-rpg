PASSIVE_DATA = {

    # =========================================================
    #                    IGNEOUS DRAKE
    # =========================================================

    "cinderblood": {
        "name": "Cinderblood",
        "trigger": "on_hit",
        "handler": "apply_burn",
        "chance": 0.35,
        "stacks": 1,
        "turns": 2,
        "action_gauge": 0
    },

    "cinderblood_ignite": {
        "name": "Cinderblood: Ignite",
        "trigger": "on_hit",
        "handler": "apply_burn",
        "chance": 0.50,
        "stacks": 1,
        "turns": 2,
        "action_gauge": 0
    },

    "cinderblood_molten_core": {
        "name": "Cinderblood: Molten Core",
        "trigger": "on_hit",
        "handler": "apply_burn",
        "chance": 0.50,
        "stacks": 2,
        "turns": 2,
        "action_gauge": 0.10
    },

    # =========================================================
    #                    ABYSSAL DRAKE
    # =========================================================
    
    "frozen_scales": {
        "name": "Frozen Scales",
        "trigger": ["before_skill", "after_skill"],
        "handler": "frozen_scales",

        "max_scales": 3,
        "required_scales": 3,

        "buffs": [
            {
                "effect_id": "defense_up",
                "turns": 2
            },
            {
                "effect_id": "immunity",
                "turns": 2
            }
        ]
    },

    "frozen_scales_everfrost": {
        "name": "Frozen Scales: Everfrost",
        "trigger": ["before_skill", "after_skill"],
        "handler": "frozen_scales",

        "max_scales": 3,
        "required_scales": 3,

        "reset_cooldown_at_max": 3,

        "buffs": [
            {
                "effect_id": "defense_up",
                "turns": 2
            },
            {
                "effect_id": "immunity",
                "turns": 2
            }
        ]
    },

    "frostborne": {
        "name": "Frostborne",
        "traits": [
            "preserve_freeze_on_hit"
        ]    
    },

    "frostborne_shattered_fury": {
        "name": "Frostborne: Shattered Fury",

        "traits": [
            "preserve_freeze_on_hit"
        ],

        "trigger": "freeze_broken_by_damage",
        "handler": "shattered_fury",

        "buffs": [
            {
                "effect_id": "attack_up",
                "turns": 1
            },
            {
                "effect_id": "crit_rate_up",
                "turns": 1
            }
        ],

        "action_gauge": 0.15
    },
}