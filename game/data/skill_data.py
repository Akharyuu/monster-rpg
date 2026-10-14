from ..models.enums import SkillType, TargetType

SKILL_DATA = {

    # =========================================================
    #                         SLIME
    # =========================================================

    # S1
    "ooze_slam": {
        "name": "Ooze Slam",
        "type": SkillType.DAMAGE,
        "multiplier": 2.3,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 0
    },

    # =========================================================
    #                         SPROUT
    # =========================================================

    # S1
    "nurturing_lash": {
        "name": "Nurturing Lash",
        "type": SkillType.DAMAGE,
        "multiplier": 1.6,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 0,

        "after_use_handlers": [
            {
                "handler": "heal_lowest_hp_ally",
                "data": {
                    "max_health_ratio": 0.05
                }
            }
        ]
    },

    # =========================================================
    #                         WISP
    # =========================================================

    # S1
    "will_o_glow": {
        "name": "Will-o'-Glow",
        "type": SkillType.DAMAGE,
        "multiplier": 2.6,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 0,

        "on_hit_handlers": [
            {
                "handler": "reduce_action_gauge",
                "data": {
                    "chance": 0.60,
                    "amount": 0.10
                }
            }
        ],
    },

    # =========================================================
    #                         THORNET
    # =========================================================

    # ---------------------------------------------------------
    #                      SHARED SKILLS
    # ---------------------------------------------------------

    # S1
    "needle_rush": {
        "name": "Needle Rush",
        "type": SkillType.DAMAGE,
        "multiplier": 1.65,
        "hits": 2,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 0,

        "effects": [
            {
                "effect_id": "poison",
                "chance": 0.35,
                "turns": 2,
                "trigger": "per_hit"
            }
        ]
    },


    # ---------------------------------------------------------
    #                    IGNEOUS THORNET
    # ---------------------------------------------------------

    # S2
    "fever_sting": {
        "name": "Fever Sting",
        "type": SkillType.DAMAGE,
        "multiplier": 1.55,
        "hits": 3,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "damage_handler": "damage_if_condition",
        "damage_handler_data": {
            "condition": {
                "type": "target_has_debuff",
                "effect_id": "poison",
                "state": "skill_start"
            },
            "damage_multiplier": 1.15
        }
    },

    # ---------------------------------------------------------
    #                    ABYSSAL THORNET
    # ---------------------------------------------------------

    # S2
    "numbing_sting": {
        "name": "Numbing Sting",
        "type": SkillType.DAMAGE,
        "multiplier": 2.50,
        "hits": 2,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "effects": [
            {
                "effect_id": "poison",
                "chance": 0.25,
                "turns": 2,
                "trigger": "per_hit"
            },

            {
                "effect_id": "stun",
                "chance": 0.60,
                "turns": 1,
                "trigger": "after_skill",
                "condition": {
                    "type": "target_gained_debuff",
                    "effect_id": "poison"
                }
            }
        ]
    },

    # ---------------------------------------------------------
    #                    STORM THORNET
    # ---------------------------------------------------------

    # S2
    "swarm_pierce": {
        "name": "Swarm Pierce",
        "type": SkillType.DAMAGE,
        "multiplier": 2.50,
        "hits": 3,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "damage_handler": "damage_if_condition",
        "damage_handler_data": {
            "condition": {
                "type": "target_has_any_debuff",
                "state": "skill_start"
            },
            "multipliers_by_hit": {
                1: 1.00,
                2: 1.15,
                3: 1.30
            }
        }
    },

    # =========================================================
    #                          DRYAD
    # =========================================================

    # ---------------------------------------------------------
    #                      SHARED SKILLS
    # ---------------------------------------------------------

    # S1
    "vine_barrage": {
        "name": "Vine Barrage",
        "type": SkillType.DAMAGE,
        "multiplier": 0.70,
        "hits": 3,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 0,

        "after_use_handlers": [
            {
                "handler": "heal_lowest_hp_ally",
                "data": {
                    "healing_hp_ratio": 0.08
                }
            }
        ]
    },

    # S1
    "vine_barrage_nourishment": {
        "name": "Vine Barrage: Nourishment",
        "type": SkillType.DAMAGE,
        "multiplier": 0.70,
        "hits": 3,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 0,

        "after_use_handlers": [
            {
                "handler": "heal_lowest_hp_ally",
                "data": {
                    "healing_hp_ratio": 0.15
                }
            }
        ]
    },

    # ---------------------------------------------------------
    #                       STORM DRYAD
    # ---------------------------------------------------------

    # S2
    "breath_of_the_grove": {
        "name": "Breath of the Grove",
        "type": SkillType.HEALING,
        "target_type": TargetType.ALL_ALLIES,
        "cooldown": 5,

        "after_use_handlers": [
            {
                "handler": "heal_all_allies",
                "data": {
                    "healing_hp_ratio": 0.25
                }
            }
        ]
    },

    # S2
    "breath_of_the_grove_sanctuary": {
        "name": "Breath of the Grove: Sanctuary",
        "type": SkillType.HEALING,
        "target_type": TargetType.ALL_ALLIES,
        "cooldown": 5,

        "after_use_handlers": [
            {
                "handler": "heal_all_allies",
                "data": {
                    "healing_hp_ratio": 0.35
                }
            },
            {
                "handler": "apply_aoe_buff",
                "data": {
                    "effect_id": "immunity",
                    "turns": 1
                }
            }
        ]
    },

    # S2
    "breath_of_the_grove_evergreen": {
        "name": "Breath of the Grove: Evergreen",
        "type": SkillType.HEALING,
        "target_type": TargetType.ALL_ALLIES,
        "cooldown": 4,

        "after_use_handlers": [
            {
                "handler": "heal_all_allies",
                "data": {
                    "healing_hp_ratio": 0.35
                }
            },
            {
                "handler": "apply_aoe_buff",
                "data": {
                    "effect_id": "immunity",
                    "turns": 1
                }
            },
            {
                "handler": "apply_aoe_buff",
                "data": {
                    "effect_id": "regrowth",
                    "turns": 2
                }
            }
        ]
    },

    # =========================================================
    #                         GRIFFON
    # =========================================================

    # ---------------------------------------------------------
    #                      SHARED SKILLS
    # ---------------------------------------------------------

    # S1
    "rending_talons": {
        "name": "Rending Talons",
        "type": SkillType.DAMAGE,
        "multiplier": 1.80,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 0
    },

    # ---------------------------------------------------------
    #                     IGNEOUS GRIFFON
    # ---------------------------------------------------------

    # S2
    "searing_gale": {
        "name": "Searing Gale",
        "type": SkillType.DAMAGE,
        "multiplier": 2.00,
        "hits": 2,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "reduce_action_gauge",
                "data": {
                    "chance": 0.50,
                    "amount": 0.20
                }
            }
        ],
    },

    "searing_gale_turbulence": {
        "name": "Searing Gale: Turbulence",
        "type": SkillType.DAMAGE,
        "multiplier": 2.00,
        "hits": 2,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "reduce_action_gauge",
                "data": {
                    "chance": 0.75,
                    "amount": 0.20
                }
            }
        ],
    },

    "searing_gale_heatstorm": {
        "name": "Searing Gale: Heatstorm",
        "type": SkillType.DAMAGE,
        "multiplier": 2.00,
        "hits": 2,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 3,

        "on_hit_handlers": [
            {
                "handler": "reduce_action_gauge",
                "data": {
                    "chance": 0.75,
                    "amount": 0.30
                }
            }
        ],
    },



    # S3
    "meteor_dive": {
        "name": "Meteor Dive",
        "type": SkillType.DAMAGE,
        "multiplier": 4.20,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 5,

        "damage_handler": "damage_with_speed_scaling",
        "damage_handler_data": {
            "speed_scaling": 0.001
        }
    },

    "meteor_dive_violent_crash": {
        "name": "Meteor Dive: Violent Crash",
        "type": SkillType.DAMAGE,
        "multiplier": 4.20,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 5,

        "damage_handler": "damage_with_speed_scaling",
        "damage_handler_data": {
            "speed_scaling": 0.001
        },

        "effects": [
            {
                "effect_id": "stun",
                "chance": 0.75,
                "turns": 1,
                "trigger": "after_skill",
                "condition": {
                    "type": "target_action_gauge_below",
                    "threshold": 0.50
                }
            }
        ]
    },

    "meteor_dive_terminal_impact": {
        "name": "Meteor Dive: Terminal Impact",
        "type": SkillType.DAMAGE,
        "multiplier": 4.20,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "damage_handler": "damage_with_speed_scaling",
        "damage_handler_data": {
            "speed_scaling": 0.001
        },

        "effects": [
            {
                "effect_id": "stun",
                "chance": 1.00,
                "turns": 1,
                "trigger": "after_skill",
                "condition": {
                    "type": "target_action_gauge_below",
                    "threshold": 0.50,
                    "threshold_if_caster_has_buff": {
                        "effect_id": "speed_up",
                        "threshold": 0.70
                    }
                }
            }
        ]
    },

    # =========================================================
    #                         DRAKE
    # =========================================================

    # ---------------------------------------------------------
    #                      SHARED SKILLS
    # ---------------------------------------------------------

    # S1
    "draconic_claw": {
        "name": "Draconic Claw",
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

    # ---------------------------------------------------------
    #                     IGNEOUS DRAKE
    # ---------------------------------------------------------

    # S2
    "scorching_breath": {
        "name": "Scorching Breath",
        "type": SkillType.DAMAGE,
        "multiplier": 3.75,
        "hits": 2,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "damage_handler": "damage_for_burn_stacks",
        "damage_handler_data": {
            "multipliers_by_stacks": {
                1: 1.08,
                2: 1.16,
                3: 1.24
            }

        }
    },

    "scorching_breath_afterburn": {
        "name": "Scorching Breath: Afterburn",
        "type": SkillType.DAMAGE,
        "multiplier": 3.75,
        "hits": 2,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "damage_handler": "damage_for_burn_stacks",
        "damage_handler_data": {
            "multipliers_by_stacks": {
                1: 1.08,
                2: 1.16,
                3: 1.24
            }
        },

        "after_skill_handlers": [
            {
                "handler": "add_burn_if_target_started_with_burn",
                "data": {
                    "stacks": 1,
                    "turns": 3
                }
            }
        ]
    },



    # S3
    "flame_devourer": {
        "name": "Flame Devourer",
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
            }
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
            "multipliers_by_stacks": {
                1: 1.15,
                2: 1.30,
                3: 1.45
            }
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

    # ---------------------------------------------------------
    #                     ABYSSAL DRAKE
    # ---------------------------------------------------------

    # S2
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
                "chance": 0.50,
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

        "on_hit_handlers": [
            {
                "handler": "reduce_action_gauge_if_debuff",
                "data": {
                    "effect_id": "speed_break",
                    "amount": 0.10
                }
            }
        ],

        "effects": [
            {
                "effect_id": "speed_break",
                "chance": 0.50,
                "turns": 2,
                "trigger": "per_hit"
            }
        ]
    },



    # S3
    "glacial_collapse": {
        "name": "Glacial Collapse",
        "type": SkillType.DAMAGE,
        "multiplier": 4.10,
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
                "chance": 1.00,
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
        "multiplier": 4.10,
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
            },
            {
                "effect_id": "freeze",
                "chance": 0.75,
                "turns": 1,
                "trigger": "per_hit",
                "ignore_resistance": True,
                "condition": {
                    "type": "target_lacks_debuff",
                    "effect_id": "speed_break"
                }
            }
        ]
    },

    # ---------------------------------------------------------
    #                       STORM DRAKE
    # ---------------------------------------------------------

    # S2
    "lightning_rush": {
        "name": "Lightning Rush",
        "type": SkillType.DAMAGE,
        "multiplier": 1.75,
        "hits": 2,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "after_use_handlers": [
            {
                "handler": "apply_self_buff",
                "data": {
                    "effect_id": "speed_up",
                    "turns": 2
                }
            }
        ]
    },

    "lightning_rush_blitz": {
        "name": "Lightning Rush: Blitz",
        "type": SkillType.DAMAGE,
        "multiplier": 1.75,
        "hits": 2,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 3,

        "after_use_handlers": [
            {
                "handler": "apply_self_buff",
                "data": {
                    "effect_id": "speed_up",
                    "turns": 2
                }
            },
            {
                "handler": "increase_action_gauge",
                "data": {
                    "amount": 0.15
                }
            }
        ]
    },



    # S3
    "stormbreak": {
        "name": "Stormbreak",
        "type": SkillType.DAMAGE,
        "multiplier": 1.60,
        "hits": 10,
        "target_type": TargetType.RANDOM_ENEMIES,
        "cooldown": 6,

        "hit_distribution": "one_each_then_random",

        "repeated_target_damage": {
            "full_damage_hits": 5,
            "later_hit_multiplier": 0.25,
            "first_hit_bonus_if_caster_buff": {
                "effect_id": "speed_up",
                "multiplier": 1.50
            }
        },

        "effects": [
            {
                "effect_id": "stun",
                "chance": 0.50,
                "turns": 1,
                "trigger": "hit_count_threshold",
                "min_hits": 3
            }
        ]
    },

    "stormbreak_requiem": {
        "name": "Stormbreak: Requiem",
        "type": SkillType.DAMAGE,
        "multiplier": 1.60,
        "hits": 10,
        "target_type": TargetType.RANDOM_ENEMIES,
        "cooldown": 6,

        "hit_distribution": "one_each_then_random",

        "repeated_target_damage": {
            "full_damage_hits": 5,
            "later_hit_multiplier": 0.25,
            "first_hit_bonus_if_caster_buff": {
                "effect_id": "speed_up",
                "multiplier": 1.50
            }
        },

        "effects": [
            {
                "effect_id": "stun",
                "chance": 0.50,
                "turns": 1,
                "trigger": "hit_count_threshold",
                "min_hits": 3
            }
        ],

        "after_use_handlers": [
            {
                "handler": "aoe_follow_up_attack",
                "data": {
                    "damage_multiplier": 0.75
                }
            }
        ]
    }
,

    # ---------------------------------------------------------
    #                       AETHER DRAKE
    # ---------------------------------------------------------

    # S2
    "sovereign_breath": {
        "name": "Sovereign Breath",
        "type": SkillType.DAMAGE,
        "multiplier": 3.00,
        "hits": 1,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "after_use_handlers": [
            {
                "handler": "apply_scaling_silence",
                "data": {
                    "base_chance": 0.30,
                    "chance_per_buff": 0.10,
                    "max_chance": 0.80,
                    "turns": 1
                }
            }
        ]
    },

    "sovereign_breath_subjugation": {
        "name": "Sovereign Breath: Subjugation",
        "type": SkillType.DAMAGE,
        "multiplier": 3.00,
        "hits": 1,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 3,

        "after_use_handlers": [
            {
                "handler": "apply_scaling_silence",
                "data": {
                    "base_chance": 0.50,
                    "chance_per_buff": 0.10,
                    "max_chance": 1.00,
                    "turns": 1
                }
            }
        ]
    },

    # S3
    "heavens_decree": {
        "name": "Heaven's Decree",
        "type": SkillType.SUPPORT,
        "target_type": TargetType.ALL_ALLIES,
        "cooldown": 6,

        "after_use_handlers": [
            {
                "handler": "apply_aoe_buff",
                "data": {
                    "effect_id": "attack_up",
                    "turns": 2
                }
            },
            {
                "handler": "apply_aoe_buff",
                "data": {
                    "effect_id": "immunity",
                    "turns": 2
                }
            },
            {
                "handler": "apply_aoe_buff",
                "data": {
                    "effect_id": "veil",
                    "turns": 2
                }
            }
        ]
    },

    "heavens_decree_apotheosis": {
        "name": "Heaven's Decree: Apotheosis",
        "type": SkillType.SUPPORT,
        "target_type": TargetType.ALL_ALLIES,
        "cooldown": 6,

        "after_use_handlers": [
            {
                "handler": "apply_aoe_buff",
                "data": {
                    "effect_id": "attack_up",
                    "turns": 3
                }
            },
            {
                "handler": "apply_aoe_buff",
                "data": {
                    "effect_id": "immunity",
                    "turns": 3
                }
            },
            {
                "handler": "apply_aoe_buff",
                "data": {
                    "effect_id": "veil",
                    "turns": 3
                }
            },
            {
                "handler": "grant_extra_turn",
                "data": {}
            }
        ]
    },

    # ---------------------------------------------------------
    #                        VOID DRAKE
    # ---------------------------------------------------------

    # S2
    "null_rend": {
        "name": "Null Rend",
        "type": SkillType.DAMAGE,
        "multiplier": 2.10,
        "hits": 2,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "oblivion",
                    "chance": 0.60,
                    "turns": 2,
                    "hit_indices": [1]
                }
            }
        ]
    },

    "null_rend_obliterate": {
        "name": "Null Rend: Obliterate",
        "type": SkillType.DAMAGE,
        "multiplier": 2.10,
        "hits": 2,
        "hit_multipliers": [
            1.00,
            1.30
        ],
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "oblivion",
                    "chance": 0.80,
                    "turns": 2,
                    "hit_indices": [1]
                }
            }
        ]
    },

    "null_rend_annihilation": {
        "name": "Null Rend: Annihilation",
        "type": SkillType.DAMAGE,
        "multiplier": 2.10,
        "hits": 2,
        "hit_multipliers": [
            1.00,
            1.30
        ],
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "oblivion",
                    "chance": 0.80,
                    "turns": 2,
                    "hit_indices": [1]
                }
            }
        ],

        "after_use_handlers": [
            {
                "handler": "banish_killed_oblivion_targets",
                "data": {}
            }
        ]
    },

    # S3
    "dismantle": {
        "name": "Dismantle",
        "type": SkillType.DAMAGE,
        "multiplier": 1.45,
        "hits": 3,
        "target_type": TargetType.ALL_ENEMIES,
        "resolve_hits_by_round": True,
        "cooldown": 5,

        "damage_handler": "damage_for_removed_buffs",
        "damage_handler_data": {
            "affected_hit_indices": [1, 2],
            "damage_per_removed_buff": 0.08
        },

        "on_hit_handlers": [
            {
                "handler": "strip_buffs_on_hit",
                "data": {
                    "hit_index": 0,
                    "track_removed_buffs_for_skill_damage": True
                }
            },
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "defense_break",
                    "chance": 0.30,
                    "turns": 2,
                    "hit_indices": [1, 2]
                }
            }
        ]
    },

    "dismantle_decimation": {
        "name": "Dismantle: Decimation",
        "type": SkillType.DAMAGE,
        "multiplier": 1.45,
        "hits": 3,
        "target_type": TargetType.ALL_ENEMIES,
        "resolve_hits_by_round": True,
        "cooldown": 4,

        "damage_handler": "damage_for_removed_buffs",
        "damage_handler_data": {
            "affected_hit_indices": [1, 2],
            "damage_per_removed_buff": 0.08
        },

        "on_hit_handlers": [
            {
                "handler": "strip_buffs_on_hit",
                "data": {
                    "hit_index": 0,
                    "track_removed_buffs_for_skill_damage": True
                }
            },
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "defense_break",
                    "chance": 0.50,
                    "turns": 2,
                    "hit_indices": [1, 2]
                }
            }
        ]
    }

}

