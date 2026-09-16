from .enums import Attribute, SkillType

MONSTER_DATA = {
    "drake_igneous": {
        "name": "Kaelgor",
        "family": "Drake",
        "attribute": Attribute.IGNEOUS,
        "rarity": 5,

        "max_health": 12125,
        "attack": 963,
        "defense": 707,
        "speed": 112,

        "skills": [
            "drake_claw",
            "scorching_breath",
            "flame_devourer"
        ],

        "passives": [
            "cinderblood"
        ]
    },
    "drake_abyssal": {
        "name": "Vharak",
        "family": "Drake",
        "attribute": Attribute.ABYSSAL,
        "rarity": 5,
        
        "max_health": 14075,
        "attack": 693,
        "defense": 921,
        "speed": 108,

        "skills": [
            "drake_claw",
            "rime_breath",
            "glacial_collapse"
        ],

        "passives": [
            "frozen_scales"
        ]
    },
    "drake_storm": {
        "name": "???",
        "family": "Drake",
        "attribute": Attribute.STORM,
        "rarity": 5,
        
        "max_health": 9875,
        "attack": 1047,
        "defense": 653,
        "speed": 118,

        "skills": [
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
        "speed": 80,

        "skills": [
            "drake_claw"
        ]
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
    },
    "piñata": {
        "name": "Piñata",
        "family": "Piñata",
        "attribute": Attribute.AETHER,
        "rarity": 10,
        
        "max_health": 100000,
        "attack": 1000,
        "defense": 1000,
        "speed": 100,

        "skills": [
            "drake_claw"
        ],

        "passives": []
    }
}