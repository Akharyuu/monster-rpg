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
        "trigger": ["before_skill", "on_hit"],
        "handler": "apply_burn",
        "chance": 0.65,
        "stacks": 1,
        "turns": 2,
        "action_gauge": 0.10,
        "action_gauge_once_per_skill": True
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

        "reset_cooldown_skill_slot": 3,

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

    "frostborne_everlasting_winter": {
        "name": "Frostborne: Everlasting Winter",

        "traits": [
            "preserve_freeze_on_hit",
            "preserve_applied_freeze_on_damage"
        ]
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
                "lightning_rush",
                "lightning_rush_blitz"
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

    # =========================================================
    #                      AETHER DRAKE
    # =========================================================

    "celestial_authority": {
        "name": "Celestial Authority",
        "trigger": "on_receive_hit",
        "handler": "celestial_authority",

        "handler_data": {
            "chance": 0.30,
            "turns": 2
        }
    },

    "celestial_authority_ascendance": {
        "name": "Celestial Authority: Ascendance",
        "trigger": "on_receive_hit",
        "handler": "celestial_authority",

        "handler_data": {
            "chance": 0.50,
            "turns": 2,
            "action_gauge_to_most_buffed_ally": 0.20
        }
    },

    "divine_grace": {
        "name": "Divine Grace",
        "trigger": "on_apply_buff",
        "handler": "divine_grace",

        "handler_data": {
            "heal_ratio_per_buff": 0.05
        }
    },

    "divine_grace_enlightenment": {
        "name": "Divine Grace: Enlightenment",
        "trigger": "on_apply_buff",
        "handler": "divine_grace",

        "handler_data": {
            "heal_ratio_per_buff": 0.05,
            "accuracy_bonus": 25
        }
    },

    # =========================================================
    #                       VOID DRAKE
    # =========================================================

    "bottomless_hunger": {
        "name": "Bottomless Hunger",
        "trigger": "on_remove_enemy_buff",
        "handler": "bottomless_hunger",

        "handler_data": {
            "heal_ratio_per_buff": 0.10,
            "action_gauge_per_buff": 0.08
        }
    },

    "voidborn": {
        "name": "Voidborn",
        "trigger": "on_remove_enemy_buff",
        "handler": "voidborn",

        "handler_data": {
            "max_stacks": 5,
            "invincibility_turns": 2,
            "extra_activation_invincibility_turns": 1,
            "extra_activation_damage_bonus": 0.20
        }
    },

    "voidborn_transcendence": {
        "name": "Voidborn: Transcendence",
        "trigger": "on_remove_enemy_buff",
        "handler": "voidborn",

        "handler_data": {
            "max_stacks": 5,
            "invincibility_turns": 2,
            "extra_activation_invincibility_turns": 1,
            "extra_activation_damage_bonus": 0.20,
            "full_cleanse_on_activation": True
        }
    },

    # =========================================================
    #                     IGNEOUS DULLAHAN
    # =========================================================

    "final_omen": {
        "name": "Final Omen",
        "trigger": "on_enemy_healed",
        "handler": "final_omen",

        "handler_data": {
            "hp_threshold": 0.50,
            "attack_up_turns": 1
        }
    },

    "final_omen_fulfilled": {
        "name": "Final Omen: Fulfilled",
        "trigger": "on_enemy_healed",
        "handler": "final_omen",

        "handler_data": {
            "hp_threshold": 0.50,
            "attack_up_turns": 1,
            "healing_received_multiplier": 0.70
        }
    },

    # =========================================================
    #                     ABYSSAL DULLAHAN
    # =========================================================

    "chilling_presence": {
        "name": "Chilling Presence",
        "trigger": "after_turn",
        "handler": "chilling_presence",

        "handler_data": {
            "debuffs_per_enemy": 1
        }
    },

    "chilling_presence_suffocation": {
        "name": "Chilling Presence: Suffocation",
        "trigger": "after_turn",
        "handler": "chilling_presence",

        "handler_data": {
            "debuffs_per_enemy": 2
        }
    },

    # =========================================================
    #                      STORM DULLAHAN
    # =========================================================

    "the_hunt": {
        "name": "The Hunt",
        "trigger": "after_turn",
        "handler": "the_hunt",

        "handler_data": {
            "action_gauge_steal": 0.20
        }
    },

    # =========================================================
    #                     AETHER DULLAHAN
    # =========================================================

    "soul_vessel": {
        "name": "Soul Vessel",
        "trigger": [
            "before_skill",
            "after_skill",
            "on_any_death"
        ],
        "handler": "soul_vessel",

        "handler_data": {
            "max_charges": 5,
            "charges_per_damage_skill": 1,
            "charges_per_death": 1,
            "consume_all_on_skill_ids": [
                "beyond_the_veil",
                "beyond_the_veil_soul_recall",
                "beyond_the_veil_convergence"
            ]
        }
    },

    "soul_vessel_last_rites": {
        "name": "Soul Vessel: Last Rites",
        "trigger": [
            "before_skill",
            "after_skill",
            "on_any_death"
        ],
        "handler": "soul_vessel",

        "handler_data": {
            "max_charges": 5,
            "charges_per_damage_skill": 1,
            "charges_per_death": 1,
            "consume_all_on_skill_ids": [
                "beyond_the_veil",
                "beyond_the_veil_soul_recall",
                "beyond_the_veil_convergence"
            ],
            "last_rites_skill_ids": [
                "severing_blade"
            ],
            "last_rites_threshold": 0.50
        }
    },

    "soul_vessel_requiem": {
        "name": "Soul Vessel: Requiem",
        "trigger": [
            "before_skill",
            "after_skill",
            "on_any_death"
        ],
        "handler": "soul_vessel",

        "handler_data": {
            "max_charges": 5,
            "charges_per_damage_skill": 1,
            "charges_per_death": 2,
            "consume_all_on_skill_ids": [
                "beyond_the_veil",
                "beyond_the_veil_soul_recall",
                "beyond_the_veil_convergence"
            ],
            "last_rites_skill_ids": [
                "severing_blade"
            ],
            "last_rites_threshold": 0.50
        }
    },

    # =========================================================
    #                      VOID DULLAHAN
    # =========================================================

    "headless_rider": {
        "name": "Headless Rider",
        "handler": "headless_rider",

        "handler_data": {
            "speed_bonus": 0.20
        }
    },

    "headless_rider_unbound": {
        "name": "Headless Rider: Unbound",
        "handler": "headless_rider",

        "handler_data": {
            "speed_bonus": 0.30
        }
    },

    "deathless_rider": {
        "name": "Deathless Rider",
        "handler": "deathless_rider",

        "handler_data": {
            "speed_bonus": 0.30,
            "internal_cooldown": 6
        }
    },

    "death_march": {
        "name": "Death's Gaze: Death March",
        "trigger": "on_any_death",
        "handler": "death_march",

        "handler_data": {
            "named_turns": 2,
            "vulnerability_turns": 3
        }
    }

}