from .enums import Attribute

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
            {
                "name": "Drake Claw",
                "power": 25,
                "cooldown": 0
            },
            {
                "name": "Abyssal Surge",
                "power": 45,
                "cooldown": 3
            },
            {
                "name": "Crushing Depths",
                "power": 60,
                "cooldown": 5
            }
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
    }
}