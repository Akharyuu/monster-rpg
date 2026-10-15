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
                    "healing_hp_ratio": 0.05
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
    },

    # =========================================================
    #                        DULLAHAN
    # =========================================================

    # ---------------------------------------------------------
    #                      SHARED SKILLS
    # ---------------------------------------------------------

    "severing_blade": {
        "name": "Severing Blade",
        "type": SkillType.DAMAGE,
        "multiplier": 2.60,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 0,

        "effects": [
            {
                "effect_id": "heal_block",
                "chance": 0.30,
                "turns": 2,
                "trigger": "after_skill"
            }
        ]
    },

    # ---------------------------------------------------------
    #                    IGNEOUS DULLAHAN
    # ---------------------------------------------------------

    "relentless_pursuit": {
        "name": "Relentless Pursuit",
        "type": SkillType.DAMAGE,
        "multiplier": 1.85,
        "hits": 2,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "damage_handler": "damage_by_missing_health",
        "damage_handler_data": {
            "max_bonus_damage": 0.30
        }
    },

    "relentless_pursuit_blood_trail": {
        "name": "Relentless Pursuit: Blood Trail",
        "type": SkillType.DAMAGE,
        "multiplier": 1.85,
        "hits": 2,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "damage_handler": "damage_by_missing_health",
        "damage_handler_data": {
            "max_bonus_damage": 0.45
        },

        "on_hit_handlers": [
            {
                "handler": "gain_action_gauge_if_target_low_hp",
                "data": {
                    "health_threshold": 0.50,
                    "amount": 0.20
                }
            }
        ]
    },

    "death_sentence": {
        "name": "Death Sentence",
        "type": SkillType.DAMAGE,
        "multiplier": 4.60,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 5,

        "damage_handler": "execute_below_health_threshold",
        "damage_handler_data": {
            "health_threshold": 0.25,
            "defense_ignore_ratio": 0.50
        }
    },

    "death_sentence_execution": {
        "name": "Death Sentence: Execution",
        "type": SkillType.DAMAGE,
        "multiplier": 4.60,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "damage_handler": "execute_below_health_threshold",
        "damage_handler_data": {
            "health_threshold": 0.33,
            "defense_ignore_ratio": 0.50
        }
    },

    "death_sentence_massacre": {
        "name": "Death Sentence: Massacre",
        "type": SkillType.DAMAGE,
        "multiplier": 4.60,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "damage_handler": "execute_below_health_threshold",
        "damage_handler_data": {
            "health_threshold": 0.33,
            "defense_ignore_ratio": 0.50
        },

        "after_use_handlers": [
            {
                "handler": "follow_up_skill_on_kill",
                "data": {
                    "skill_slot": 2
                }
            }
        ]
    },

    # ---------------------------------------------------------
    #                    ABYSSAL DULLAHAN
    # ---------------------------------------------------------

    "spectral_shackles": {
        "name": "Spectral Shackles",
        "type": SkillType.DAMAGE,
        "multiplier": 1.95,
        "hits": 2,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "speed_break",
                    "chance": 0.50,
                    "turns": 2,
                    "hit_indices": [0]
                }
            },
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "attack_break",
                    "chance": 0.50,
                    "turns": 2,
                    "hit_indices": [1]
                }
            }
        ]
    },

    "spectral_shackles_binding": {
        "name": "Spectral Shackles: Binding",
        "type": SkillType.DAMAGE,
        "multiplier": 1.95,
        "hits": 2,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "speed_break",
                    "chance": 0.70,
                    "turns": 2,
                    "hit_indices": [0]
                }
            },
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "attack_break",
                    "chance": 0.70,
                    "turns": 2,
                    "hit_indices": [1]
                }
            }
        ]
    },

    "spectral_shackles_lockdown": {
        "name": "Spectral Shackles: Lockdown",
        "type": SkillType.DAMAGE,
        "multiplier": 1.95,
        "hits": 2,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "speed_break",
                    "chance": 0.90,
                    "turns": 2,
                    "hit_indices": [0]
                }
            },
            {
                "handler": "apply_debuff_on_hit_indices",
                "data": {
                    "effect_id": "attack_break",
                    "chance": 0.90,
                    "turns": 2,
                    "hit_indices": [1]
                }
            }
        ],

        "after_use_handlers": [
            {
                "handler": "reduce_action_gauge_if_both_debuffs_applied",
                "data": {
                    "effect_ids": [
                        "speed_break",
                        "attack_break"
                    ],
                    "amount": 0.20
                }
            }
        ]
    },

    "inescapable_fate": {
        "name": "Inescapable Fate",
        "type": SkillType.DAMAGE,
        "multiplier": 3.00,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 5,

        "after_skill_handlers": [
            {
                "handler": "extend_target_debuffs",
                "data": {
                    "turns": 1,
                    "silence_required_debuffs": 3,
                    "silence_turns": 1
                }
            }
        ]
    },

    "inescapable_fate_ironbound": {
        "name": "Inescapable Fate: Ironbound",
        "type": SkillType.DAMAGE,
        "multiplier": 3.00,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 4,

        "damage_handler": "damage_with_bonus_stat",
        "damage_handler_data": {
            "bonus_stat": "defense",
            "bonus_scaling": 1.20
        },

        "after_skill_handlers": [
            {
                "handler": "extend_target_debuffs",
                "data": {
                    "turns": 1,
                    "silence_required_debuffs": 3,
                    "silence_turns": 1
                }
            }
        ]
    },

    # ---------------------------------------------------------
    #                     STORM DULLAHAN
    # ---------------------------------------------------------

    "gale_pursuit": {
        "name": "Gale Pursuit",
        "type": SkillType.DAMAGE,
        "multiplier": 2.25,
        "hits": 1,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "reduce_action_gauge",
                "data": {
                    "amount": 0.20
                }
            }
        ]
    },

    "gale_pursuit_crosswind": {
        "name": "Gale Pursuit: Crosswind",
        "type": SkillType.DAMAGE,
        "multiplier": 2.25,
        "hits": 1,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "reduce_action_gauge_with_threshold_bonus",
                "data": {
                    "amount": 0.25,
                    "threshold": 0.50,
                    "bonus_amount": 0.10
                }
            }
        ]
    },

    "gale_pursuit_tempest": {
        "name": "Gale Pursuit: Tempest",
        "type": SkillType.DAMAGE,
        "multiplier": 2.25,
        "hits": 1,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "on_hit_handlers": [
            {
                "handler": "reduce_action_gauge_with_threshold_bonus",
                "data": {
                    "amount": 0.25,
                    "threshold": 0.50,
                    "bonus_amount": 0.10
                }
            }
        ],

        "after_use_handlers": [
            {
                "handler": "apply_team_buff",
                "data": {
                    "effect_id": "speed_up",
                    "turns": 2
                }
            }
        ]
    },

    "headlong_charge": {
        "name": "Headlong Charge",
        "type": SkillType.SUPPORT,
        "target_type": TargetType.SELF,
        "cooldown": 5,

        "after_use_handlers": [
            {
                "handler": "support_lowest_gauge_ally",
                "data": {
                    "self_buffs": [
                        {
                            "effect_id": "attack_up",
                            "turns": 2
                        },
                        {
                            "effect_id": "speed_up",
                            "turns": 2
                        }
                    ],
                    "ally_action_gauge": 0.20
                }
            }
        ]
    },

    "headlong_charge_rally": {
        "name": "Headlong Charge: Rally",
        "type": SkillType.SUPPORT,
        "target_type": TargetType.SELF,
        "cooldown": 5,

        "after_use_handlers": [
            {
                "handler": "support_lowest_gauge_ally",
                "data": {
                    "self_buffs": [
                        {
                            "effect_id": "attack_up",
                            "turns": 2
                        },
                        {
                            "effect_id": "speed_up",
                            "turns": 2
                        }
                    ],
                    "ally_buffs": [
                        {
                            "effect_id": "attack_up",
                            "turns": 2
                        },
                        {
                            "effect_id": "speed_up",
                            "turns": 2
                        }
                    ],
                    "ally_action_gauge": 0.30
                }
            }
        ]
    },

    "headlong_charge_stampede": {
        "name": "Headlong Charge: Stampede",
        "type": SkillType.SUPPORT,
        "target_type": TargetType.SELF,
        "cooldown": 5,

        "after_use_handlers": [
            {
                "handler": "support_lowest_gauge_ally",
                "data": {
                    "self_buffs": [
                        {
                            "effect_id": "attack_up",
                            "turns": 2
                        },
                        {
                            "effect_id": "speed_up",
                            "turns": 2
                        }
                    ],
                    "ally_buffs": [
                        {
                            "effect_id": "attack_up",
                            "turns": 2
                        },
                        {
                            "effect_id": "speed_up",
                            "turns": 2
                        }
                    ],
                    "ally_action_gauge": 0.30,
                    "force_next_turn": True
                }
            }
        ]
    },

    # ---------------------------------------------------------
    #                    AETHER DULLAHAN
    # ---------------------------------------------------------

    "soulpiercer": {
        "name": "Soulpiercer",
        "type": SkillType.DAMAGE,
        "multiplier": 4.10,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 3,

        "damage_handler": "damage_for_soul_charges",
        "damage_handler_data": {
            "damage_per_charge": 0.06,
            "max_charges": 5
        }
    },

    "soulpiercer_ascension": {
        "name": "Soulpiercer: Ascension",
        "type": SkillType.DAMAGE,
        "multiplier": 4.10,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 3,

        "damage_handler": "damage_for_soul_charges",
        "damage_handler_data": {
            "damage_per_charge": 0.08,
            "max_charges": 5
        }
    },

    "beyond_the_veil": {
        "name": "Beyond the Veil",
        "type": SkillType.DAMAGE,
        "multiplier": 1.25,
        "hits": 4,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 7,

        "damage_handler": "damage_for_soul_charges",
        "damage_handler_data": {
            "damage_per_charge": 0.10,
            "max_charges": 5,
            "use_consumed_charges": True
        }
    },

    "beyond_the_veil_soul_recall": {
        "name": "Beyond the Veil: Soul Recall",
        "type": SkillType.DAMAGE,
        "multiplier": 1.25,
        "hits": 4,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 6,

        "damage_handler": "damage_for_soul_charges",
        "damage_handler_data": {
            "damage_per_charge": 0.10,
            "max_charges": 5,
            "use_consumed_charges": True,
            "disable_bonus_if_ally_dead": True
        },

        "after_use_handlers": [
            {
                "handler": "revive_most_recent_ally",
                "data": {
                    "health_ratio_by_charges": {
                        1: 0.30,
                        2: 0.40,
                        3: 0.50,
                        4: 0.60,
                        5: 0.70
                    },
                    "action_gauge": 0.30
                }
            }
        ]
    },

    "beyond_the_veil_convergence": {
        "name": "Beyond the Veil: Convergence",
        "type": SkillType.DAMAGE,
        "multiplier": 1.25,
        "hits": 4,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 6,

        "damage_handler": "damage_for_soul_charges",
        "damage_handler_data": {
            "damage_per_charge": 0.10,
            "max_charges": 5,
            "use_consumed_charges": True,
            "disable_bonus_if_ally_dead": True,
            "allow_bonus_with_dead_at_max": True
        },

        "after_use_handlers": [
            {
                "handler": "revive_most_recent_ally",
                "data": {
                    "health_ratio_by_charges": {
                        1: 0.30,
                        2: 0.40,
                        3: 0.50,
                        4: 0.60,
                        5: 0.70
                    },
                    "action_gauge": 0.30
                }
            }
        ]
    },

    # ---------------------------------------------------------
    #                     VOID DULLAHAN
    # ---------------------------------------------------------

    "spinal_scourge": {
        "name": "Spinal Scourge",
        "type": SkillType.DAMAGE,
        "multiplier": 1.40,
        "hits": 3,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "damage_handler": "damage_for_dead_monsters",
        "damage_handler_data": {
            "damage_per_dead_monster": 0.05,
            "max_dead_monsters": 5,
            "max_bonus_damage": 0.25
        }
    },

    "spinal_scourge_ossuary": {
        "name": "Spinal Scourge: Ossuary",
        "type": SkillType.DAMAGE,
        "multiplier": 1.40,
        "hits": 3,
        "target_type": TargetType.ALL_ENEMIES,
        "cooldown": 4,

        "damage_handler": "damage_for_dead_monsters",
        "damage_handler_data": {
            "damage_per_dead_monster": 0.08,
            "max_dead_monsters": 5,
            "max_bonus_damage": 0.40
        }
    },

    "deaths_gaze": {
        "name": "Death's Gaze",
        "type": SkillType.DAMAGE,
        "multiplier": 4.70,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 6,

        "before_hit_handlers": [
            {
                "handler": "apply_named_and_vulnerability",
                "data": {
                    "hit_indices": [0],
                    "named_turns": 2,
                    "vulnerability_chance": 1.00,
                    "vulnerability_turns": 2
                }
            }
        ]
    },

    "deaths_gaze_last_name": {
        "name": "Death's Gaze: Last Name",
        "type": SkillType.DAMAGE,
        "multiplier": 4.70,
        "hits": 1,
        "target_type": TargetType.SINGLE_ENEMY,
        "cooldown": 5,

        "before_hit_handlers": [
            {
                "handler": "apply_named_and_vulnerability",
                "data": {
                    "hit_indices": [0],
                    "named_turns": 2,
                    "vulnerability_chance": 1.00,
                    "vulnerability_turns": 3
                }
            }
        ]
    }

}

