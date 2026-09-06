from .enums import Attribute, SkillType

MONSTER_DATA = {
    "drake_igneous": {
        "name": "Kaelgor",
        "family": "Drake",
        "attribute": Attribute.IGNEOUS,
        "rarity": 4,

        "max_health": 120,
        "attack": 35,
        "defense": 20,
        "speed": 105,

        "skills": [
            "drake_claw"
        ]
    },
    "drake_abyssal": {
        "name": "Vharak",
        "family": "Drake",
        "attribute": Attribute.ABYSSAL,
        "rarity": 5,
        
        "max_health": 120,
        "attack": 35,
        "defense": 20,
        "speed": 105,

        "skills": [
            "fake_out",
            "drake_claw"
        ]
    },
    "goblin_igneous": {
        "name": "Trull",
        "family": "Goblin",
        "attribute": Attribute.IGNEOUS,
        "rarity": 2,

        "max_health": 75,
        "attack": 13,
        "defense": 8,
        "speed": 95,
    },
    "golem_storm": {
        "name": "Gorga'th",
        "family": "Golem",
        "attribute": Attribute.STORM,
        "rarity": 3,

        "max_health": 160,
        "attack": 5,
        "defense": 38,
        "speed": 45,

        "skills": [
            {
                "skill_id": "heavy_slam",
                "name": "Heavy Slam",
                "type": SkillType.DAMAGE,
                "power": 20,
                "cooldown": 0
            },
            {
                "skill_id": "earths_echo",
                "name": "Earth's Echo",
                "type": SkillType.HEALING,
                "scaling_stat": "defense",
                "base_scaling_ratio": 0.35,
                "cooldown": 3
            }
        ]
    }
}