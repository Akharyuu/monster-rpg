from ..models.enums import EffectType

STATUS_EFFECT_DATA =  {

    # =========================================================
    #                     STAT DEBUFFS
    # =========================================================

    "attack_break": {
        "name": "Attack Break",
        "stat": "attack",
        "effect_type": EffectType.DEBUFF,
        "modifier": 0.7
    },

    "defense_break": {
        "name": "Defense Break",
        "stat": "defense",
        "effect_type": EffectType.DEBUFF,
        "modifier": 0.7
    },

    "speed_break": {
        "name": "Speed Break",
        "stat": "speed",
        "effect_type": EffectType.DEBUFF,
        "modifier": 0.7
    },

    # =========================================================
    #                      CONTROL DEBUFFS
    # =========================================================

    "stun": {
        "name": "Stun",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier" : None,
        "extendable": False
    },

    "freeze": {
        "name": "Freeze",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier" : None,
        "extendable": False
    },

    "silence": {
        "name": "Silence",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier" : None
    },

    "oblivion": {
        "name": "Oblivion",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier": None
    },

    "heal_block": {
        "name": "Heal Block",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier": None
    },

    "vulnerability": {
        "name": "Vulnerability",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier": None,
        "direct_damage_taken_multiplier": 1.15
    },

    # =========================================================
    #                     DAMAGE OVER TIME
    # =========================================================

    "burn": {
        "name": "Burn",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier" : None,
        "max_stacks": 3
    },

    "poison": {
        "name": "Poison",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier" : None,
        "max_stacks": 10
    },

    # =========================================================
    #                      STAT BUFFS
    # =========================================================

    "attack_up": {
        "name": "Attack Up",
        "stat": "attack",
        "effect_type": EffectType.BUFF,
        "modifier": 1.3
    },

    "defense_up": {
        "name": "Defense Up",
        "stat": "defense",
        "effect_type": EffectType.BUFF,
        "modifier": 1.3
    },

    "speed_up": {
        "name": "Speed Up",
        "stat": "speed",
        "effect_type": EffectType.BUFF,
        "modifier": 1.3
    },

    "crit_rate_up": {
        "name": "Crit Rate Up",
        "effect_type": EffectType.BUFF,
        "stat": "crit_rate",
        "modifier": 30,
        "modifier_mode": "additive",
        "max_stacks": 1
    },

    # =========================================================
    #                    PROTECTIVE BUFFS
    # =========================================================
    
    "immunity": {
        "name": "Immunity",
        "stat": None,
        "effect_type": EffectType.BUFF,
        "modifier": None
    },

    "veil": {
        "name": "Veil",
        "stat": None,
        "effect_type": EffectType.BUFF,
        "modifier": None
    },

    "invincibility": {
        "name": "Invincibility",
        "stat": None,
        "effect_type": EffectType.BUFF,
        "modifier": None
    },

    "regrowth": {
        "name": "Regrowth",
        "stat": None,
        "effect_type": EffectType.BUFF,
        "modifier": None,
        "heal_ratio": 0.08
    },

    "shield": {
        "name": "Shield",
        "stat": None,
        "effect_type": EffectType.BUFF,
        "modifier": None
    }
}