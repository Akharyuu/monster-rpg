SKILL_AI_DATA = {

    # =========================================================
    #                     IGNEOUS DRAKE
    # =========================================================

    "flame_devourer_incineration": {
        "setup_requirements": [
            {
                "condition": "target_debuff_stacks",
                "effect_id": "burn",
                "stacks": 2,
                "scope": "any_enemy"
            }
        ],
        "hold_until_setup": True,
        "preferred_target_debuff": {
            "effect_id": "burn",
            "stacks": 2
        }
    },

    # =========================================================
    #                     ABYSSAL DRAKE
    # =========================================================

    "glacial_collapse": {
        "setup_requirements": [
            {
                "condition": "target_has_debuff",
                "effect_id": "speed_break",
                "scope": "any_enemy"
            }
        ]
    },

    "glacial_collapse_absolute_zero": {
        "setup_requirements": [
            {
                "condition": "target_has_debuff",
                "effect_id": "speed_break",
                "scope": "any_enemy"
            }
        ]
    },

    "fever_sting": {
        "setup_requirements": [
            {
                "condition": "target_has_debuff",
                "effect_id": "poison",
                "scope": "any_enemy"
            }
        ]
    }
}

