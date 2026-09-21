from ..models.enums import Attribute

MONSTER_DATA = {

    # =========================================================
    #                          SLIMES
    # =========================================================

    "slime_igneous": {
        "name": "Igneous Slime",
        "family": "Slime",
        "attribute": Attribute.IGNEOUS,
        "rarity": 1,

        "max_health": 7600,
        "attack": 485,
        "defense": 330,
        "speed": 184,

        "skills": [
            "ooze_slam"
        ]
    },

    "slime_abyssal": {
        "name": "Abyssal Slime",
        "family": "Slime",
        "attribute": Attribute.ABYSSAL,
        "rarity": 1,

        "max_health": 8300,
        "attack": 420,
        "defense": 390,
        "speed": 176,

        "skills": [
            "ooze_slam"
        ]
    },

    "slime_storm": {
        "name": "Storm Slime",
        "family": "Slime",
        "attribute": Attribute.STORM,
        "rarity": 1,

        "max_health": 7200,
        "attack": 455,
        "defense": 320,
        "speed": 198,

        "skills": [
            "ooze_slam"
        ]
    },

    # =========================================================
    #                         SPROUTS
    # =========================================================

    "sprout_igneous": {
        "name": "Igneous Sprout",
        "family": "Sprout",
        "attribute": Attribute.IGNEOUS,
        "rarity": 1,

        "max_health": 6900,
        "attack": 410,
        "defense": 470,
        "speed": 188,

        "skills": [
            "nurturing_lash"
        ]
    },

    "sprout_abyssal": {
        "name": "Abyssal Sprout",
        "family": "Sprout",
        "attribute": Attribute.ABYSSAL,
        "rarity": 1,

        "max_health": 7400,
        "attack": 350,
        "defense": 535,
        "speed": 180,

        "skills": [
            "nurturing_lash"
        ]
    },

    "sprout_storm": {
        "name": "Storm Sprout",
        "family": "Sprout",
        "attribute": Attribute.STORM,
        "rarity": 1,

        "max_health": 6600,
        "attack": 380,
        "defense": 455,
        "speed": 202,

        "skills": [
            "nurturing_lash"
        ]
    },

    # =========================================================
    #                          DRAKES
    # =========================================================

    "drake_igneous": {
        "name": "Kaelgor",
        "family": "Drake",
        "attribute": Attribute.IGNEOUS,
        "rarity": 5,

        "max_health": 12125,
        "attack": 963,
        "defense": 707,
        "speed": 224,

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
        "speed": 216,

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
        "speed": 236,

        "skills": [
            "drake_claw"
        ]
    },

    # =========================================================
    #                          TEST
    # =========================================================

    "goblin_igneous": {
        "name": "Trull",
        "family": "Goblin",
        "attribute": Attribute.IGNEOUS,
        "rarity": 2,

        "max_health": 75,
        "attack": 13,
        "defense": 8,
        "speed": 160,

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
        "speed": 90,

        "skills": [
            "heavy_slam",
            "earths_echo"
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
        "speed": 200,

        "skills": [
            "drake_claw"
        ],

        "passives": []
    }
}