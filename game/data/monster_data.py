from ..models.enums import Attribute

MONSTER_DATA = {

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    #                      ★ RARITY 1 ★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

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
        "speed": 138,

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
        "speed": 130,

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
        "speed": 150,

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
        "speed": 142,

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
        "speed": 134,

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
        "speed": 154,

        "skills": [
            "nurturing_lash"
        ]
    },

    # =========================================================
    #                         WISPS
    # =========================================================

    "wisp_igneous": {
        "name": "Igneous Wisp",
        "family": "Wisp",
        "attribute": Attribute.IGNEOUS,
        "rarity": 1,

        "max_health": 5500,
        "attack": 465,
        "defense": 292,
        "speed": 158,

        "skills": [
            "will_o_glow"
        ]
    },

    "wisp_abyssal": {
        "name": "Abyssal Wisp",
        "family": "Wisp",
        "attribute": Attribute.ABYSSAL,
        "rarity": 1,

        "max_health": 5750,
        "attack": 425,
        "defense": 318,
        "speed": 154,

        "skills": [
            "will_o_glow"
        ]
    },

    "wisp_storm": {
        "name": "Storm Wisp",
        "family": "Wisp",
        "attribute": Attribute.STORM,
        "rarity": 1,

        "max_health": 5250,
        "attack": 445,
        "defense": 278,
        "speed": 166,

        "skills": [
            "will_o_glow"
        ]
    },

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    #                      ★ RARITY 2 ★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

    # =========================================================
    #                         THORNETS
    # =========================================================

    "thornet_igneous": {
        "name": "Igneous Thornet",
        "family": "Thornet",
        "attribute": Attribute.IGNEOUS,
        "rarity": 2,

        "max_health": 6150,
        "attack": 675,
        "defense": 352,
        "speed": 166,

        "skills": [
            "needle_rush",
            "fever_sting"
        ]
    },

    "thornet_abyssal": {
        "name": "Abyssal Thornet",
        "family": "Thornet",
        "attribute": Attribute.ABYSSAL,
        "rarity": 2,

        "max_health": 6400,
        "attack": 585,
        "defense": 382,
        "speed": 174,

        "skills": [
            "needle_rush",
            "numbing_sting"
        ]
    },

    "thornet_storm": {
        "name": "Storm Thornet",
        "family": "Thornet",
        "attribute": Attribute.STORM,
        "rarity": 2,

        "max_health": 5850,
        "attack": 640,
        "defense": 338,
        "speed": 181,

        "skills": [
            "needle_rush",
            "swarm_pierce"
        ]
    },

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    #                      ★ RARITY 3 ★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

    # =========================================================
    #                         DRIADS
    # =========================================================

    "dryad_storm": {
        "name": "???",
        "family": "Dryad",
        "attribute": Attribute.STORM,
        "rarity": 3,

        "max_health": 11150,
        "attack": 545,
        "defense": 760,
        "speed": 204,

        "skills": [
            "vine_barrage",
            "breath_of_the_grove"
        ]
    },

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    #                      ★ RARITY 4 ★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

    # =========================================================
    #                        GRIFFONS
    # =========================================================

    "griffon_igneous": {
        "name": "???",
        "family": "Griffon",
        "attribute": Attribute.IGNEOUS,
        "rarity": 4,

        "max_health": 8900,
        "attack": 890,
        "defense": 595,
        "speed": 232,

        "skills": [
            "rending_talons",
            "searing_gale",
            "meteor_dive"
        ]
    },

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    #                      ★ RARITY 5 ★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

    # =========================================================
    #                         DRAKES
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
            "draconic_claw",
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
            "draconic_claw",
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
            "draconic_claw",
            "lightning_rush",
            "stormbreak"
        ],

        "passives": [
            "thunderheart"
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