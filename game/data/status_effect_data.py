from ..models.enums import EffectType

STATUS_EFFECT_DATA =  {
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
    "stun": {
        "name": "Stun",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier" : None
    },
    "freeze": {
        "name": "Freeze",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier" : None
    },
    "silence": {
        "name": "Silence",
        "stat": None,
        "effect_type": EffectType.DEBUFF,
        "modifier" : None
    },
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
    "immunity": {
        "name": "Immunity",
        "stat": None,
        "effect_type": EffectType.BUFF,
        "modifier": None
    },
}