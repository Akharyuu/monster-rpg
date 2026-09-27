PASSIVE_DATA = {

    # =========================================================
    #                        STORM DRYAD
    # =========================================================

    "natures_grace": {
        "name": "Nature's Grace",
        "handler": "natures_grace",

        "handler_data": {
            "hp_threshold": 0.50,
            "healing_multiplier": 1.20
        }
    },

    "natures_grace_overgrowth": {
        "name": "Nature's Grace: Overgrowth",
        "handler": "natures_grace",

        "handler_data": {
            "hp_threshold": 0.50,
            "healing_multiplier": 1.20,

            "overgrowth": {
                "overheal_conversion": 0.50,
                "max_shield_ratio": 0.10,
                "shield_turns": 2
            }
        }
    },

    # =========================================================
    #                      IGNEOUS GRIFFON
    # =========================================================

    "hawk_instinct": {
        "name": "Hawk Instinct",
        "trigger": "on_apply_stun",
        "handler": "apply_self_buff",

        "handler_data": {
            "effect_id": "speed_up",
            "chance": 1.00,
            "turns": 2
        }
    },

    # =========================================================
    #                      IGNEOUS DRAKE
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
    #                      ABYSSAL DRAKE
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

    # =========================================================
    #                      STORM DRAKE
    # =========================================================

    "thunderheart": {
        "name": "Thunderheart",
        "handler": "thunderheart",

        "handler_data": {
            "damage_per_bonus_speed": 0.003,
        }
    },

    "thunderheart_overclocked": {
        "name": "Thunderheart: Overclocked",
        "handler": "thunderheart",

        "handler_data": {
            "damage_per_bonus_speed": 0.003,
            "speed_per_crit": 5,
            "max_crit_rate_bonus": 30
        }
    },

    "short_circuit": {
        "name": "Short Circuit",
        "trigger": "on_hit",
        "handler": "stun_on_hit_if_buff",

        "handler_data": {
            "required_buff": "speed_up",
            "allowed_skill_ids": [
                "draconic_claw",
                "lightning_rush"
            ],
            "chance": 0.10,
            "turns": 1
        }
    },

    "short_circuit_chain_reaction": {
        "name": "Short Circuit: Chain Reaction",
        "trigger": "on_hit",
        "handler": "stun_on_hit_if_buff",

        "handler_data": {
            "required_buff": "speed_up",
            "allowed_skill_ids": [
                "draconic_claw",
                "lightning_rush",
                "lightning_rush_blitz"
            ],
            "chance": 0.10,
            "turns": 1,

            "on_success": {
                "reduce_skill_cooldown": {
                    "skill_ids": [
                        "stormbreak",  
                        "stormbreak_requiem" 
                    ],
                    "amount": 1
                }
            }
        }
    },
}