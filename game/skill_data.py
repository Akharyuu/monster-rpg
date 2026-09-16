from .enums import SkillType, TargetType

SKILL_DATA = {
    "drake_claw": {
        "name": "Drake Claw",
        "type": SkillType.DAMAGE,
        "multiplier": 2.5,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 0,

        "effects": [
            {
                "effect_id": "defense_break",
                "chance": 0.3,
                "turns": 2
            }
        ]
    },
    "scorching_breath": {
        "name": "Scorching Breath",
        "type": SkillType.DAMAGE,
        "multiplier": 3.75,
        "hits": 2,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "damage_handler": "damage_for_burn_stacks",
        "damage_handler_data": {
            1: 1.08,
            2: 1.16,
            3: 1.24
        }
    },
    "scorching_breath_afterburn": {
        "name": "Scorching Breath: Afterburn",
        "type": SkillType.DAMAGE,
        "multiplier": 3.75,
        "hits": 3,
        "hit_multipliers": [
            1.0, 
            1.0, 
            1.2
        ],
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "damage_handler": "damage_for_burn_stacks",
        "damage_handler_data": {
            1: 1.08,
            2: 1.16,
            3: 1.24
        }
    },
    "flame_devourer": {
        "name": "Flame Devourer",
        "type": SkillType.DAMAGE,
        "multiplier": 4.6,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 5,

        "damage_handler": "damage_for_burn_stacks",
        "damage_handler_data": {
            1: 1.15,
            2: 1.30,
            3: 1.45
        },

        "after_skill_handlers": [
            {
                "handler": "consume_burn_and_heal",
                "data": {
                    "heal_by_stacks": {
                        1: 0.12,
                        2: 0.25,
                        3: 0.40
                    }
                }
            }
        ]
    },
    "flame_devourer_rekindled": {
        "name": "Flame Devourer: Rekindled",
        "type": SkillType.DAMAGE,
        "multiplier": 4.6,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 5,

        "damage_handler": "damage_for_burn_stacks",
        "damage_handler_data": {
            1: 1.15,
            2: 1.30,
            3: 1.45
        },

        "after_skill_handlers": [
            {
                "handler": "consume_burn_and_heal",
                "data": {
                    "heal_by_stacks": {
                        1: 0.12,
                        2: 0.25,
                        3: 0.40
                    }
                }
            },
            {
                "handler": "reset_cooldown_by_burn_stacks",
                "data": {
                    "required_stacks": 3,
                    "skill_slot": 2
                }
            }
        ]
    },
    "flame_devourer_incineration": {
        "name": "Flame Devourer: Incineration",
        "type": SkillType.DAMAGE,
        "multiplier": 4.6,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 5,

        "damage_handler": "damage_for_burn_stacks",
        "damage_handler_data": {
            "multipliers_by_stacks": {
                1: 1.15,
                2: 1.30,
                3: 1.45
            },
            "ignore_defense_at_stacks": 3
        },

        "after_skill_handlers": [
            {
                "handler": "consume_burn_and_heal",
                "data": {
                    "heal_by_stacks": {
                        1: 0.12,
                        2: 0.25,
                        3: 0.40
                    }
                }
            },
            {
                "handler": "reset_cooldown_by_burn_stacks",
                "data": {
                    "required_stacks": 3,
                    "skill_slot": 2
                }
            }
        ]
    },
    "rime_breath": {
        "name": "Rime Breath",
        "type": SkillType.DAMAGE,
        "multiplier": 3.15,
        "hits": 2,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "effects": [
            {
                "effect_id": "speed_break",
                "chance": 0.30,
                "turns": 2,
                "trigger": "per_hit"
            }
        ]
    },
    "rime_breath_frigid": {
        "name": "Rime Breath: Frigid",
        "type": SkillType.DAMAGE,
        "multiplier": 3.15,
        "hits": 2,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "effects": [
            {
                "effect_id": "speed_break",
                "chance": 0.45,
                "turns": 2,
                "trigger": "per_hit"
            }
        ]
    },
    "glacial_collapse": {
        "name": "Glacial Collapse",
        "type": SkillType.DAMAGE,
        "multiplier": 4.1,
        "hits": 1,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 5,

        "on_hit_handlers": [
            {
                "handler": "reduce_action_gauge",
                "data": {
                    "amount": 0.10
                }
            }
        ],

        "effects": [
            {
                "effect_id": "freeze",
                "chance": 0.50,
                "turns": 1,
                "trigger": "per_hit",
                "condition": {
                    "type": "target_has_debuff",
                    "effect_id": "speed_break"
                }
            }
        ]
    },
    "glacial_collapse_absolute_zero": {
        "name": "Glacial Collapse: Absolute Zero",
        "type": SkillType.DAMAGE,
        "multiplier": 4.1,
        "hits": 1,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 5,

        "on_hit_handlers": [
            {
                "handler": "reduce_action_gauge",
                "data": {
                    "amount": 0.10
                }
            }
        ],

        "effects": [
            {
                "effect_id": "freeze",
                "chance": 1,
                "turns": 1,
                "trigger": "per_hit",
                "ignore_resistance": True,
                "condition": {
                    "type": "target_has_debuff",
                    "effect_id": "speed_break"
                }
            }
        ]
    },
}

