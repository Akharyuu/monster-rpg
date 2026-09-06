from .enums import SkillType

SKILL_DATA = {
    "drake_claw": {
        "name": "Drake Claw",
        "type": SkillType.DAMAGE,
        "power": 25,
        "cooldown": 0,
        "effects": [
            {
                "effect_id": "defense_break",
                "chance": 1,
                "turns": 2
            }
        ]
    },
    "abyssal_surge": {
        "name": "Abyssal Surge",
        "type": SkillType.DAMAGE,
        "power": 40,
        "cooldown": 3
    },
    "crushing_depths": {
        "name": "Crushing Depths",
        "type": SkillType.DAMAGE,
        "power": 65,
        "cooldown": 5
    },
    "fake_out": {
        "name": "Fake Out",
        "type": SkillType.DAMAGE,
        "power": 5,
        "cooldown": 0,
        "effects": [
            {
                "effect_id": "poison",
                "chance": 1,
                "turns": 2,
                "stacks": 6
            }
        ]
    }
}