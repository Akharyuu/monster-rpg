from ..models.enums import SealstoneType

CAMPAIGN_DATA = {
    1: {
        # =========================================================
        # MISSION 1
        # =========================================================
        1: {
            "name": "Welcome, Binder",

            "events": [
                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": "Welcome to the Binder Organization."
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "As a Binder, your job is to protect people "
                                "from dangerous Nimaras."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "To do that, we form Bonds with Nimaras "
                                "sealed inside Sealstones."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "Once bound, that Nimara becomes your Servant."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": "And today, you're getting your first one."
                        },
                    ]
                },

                {
                    "reward": {
                        "items": [
                            {
                                "item": SealstoneType.RUNIC,
                                "amount": 1
                            }
                        ]
                    }
                },

                {
                    "unseal": {
                        "sealstone_type": SealstoneType.RUNIC,
                        "forced_monster_id": "drake_igneous"
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": "An Igneous Gryphon. Not bad for your first Bond."
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "Come on. There's a forest outside the city "
                                "where new Binders usually train."
                            )
                        },
                    ]
                },

                # -------------------------------------------------
                # STAGE 1
                # Basic combat / S1 / Action Gauge
                # -------------------------------------------------
                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "slime_storm",
                                "level": 1
                            }
                        ],

                        "tutorial": {
                            "allowed_skills": [1]
                        }
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": "Good. Your Servant acts when its Action Gauge is full."
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "Speed determines how quickly that gauge fills. "
                                "Keep an eye on the turn order."
                            )
                        },
                    ]
                },

                # -------------------------------------------------
                # STAGE 2
                # Multiple enemies / S2 / AoE / attributes
                # -------------------------------------------------
                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "slime_abyssal",
                                "level": 2
                            },
                            {
                                "monster_id": "sprout_igneous",
                                "level": 3
                            }
                        ],

                        "tutorial": {
                            "introduce_skill": 2,
                            "teach_attributes": True
                        }
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "Different attributes interact differently. "
                                "Igneous has the advantage over Storm, "
                                "but struggles against Abyssal."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "You'll learn the matchups quickly. "
                                "For now, that's enough for your first day."
                            )
                        }
                    ]
                },
            ]
        },


        # =========================================================
        # MISSION 2
        # =========================================================
        2: {
            "name": "Field Training",

            "events": [
                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "Yesterday I was telling you what to do. "
                                "Today you'll make more of the decisions yourself."
                            )
                        }
                    ]
                },

                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "forest_nimara_1",
                                "level": 2
                            }
                        ],

                        "tutorial": {
                            "introduce_skill": 3,
                            "teach_cooldowns": True
                        }
                    }
                },

                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "forest_nimara_1",
                                "level": 2
                            },
                            {
                                "monster_id": "forest_nimara_storm",
                                "level": 2
                            }
                        ]
                    }
                },

                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "forest_nimara_storm",
                                "level": 3
                            },
                            {
                                "monster_id": "forest_nimara_abyssal",
                                "level": 2
                            }
                        ]
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": "Hold on."
                        },
                        {
                            "speaker": "senpai",
                            "text": "There's something between those roots."
                        },
                        {
                            "speaker": "player",
                            "text": "A Sealstone?"
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "Looks like it. A common one, but perfectly usable."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": "You found it. It's yours."
                        },
                    ]
                },

                {
                    "reward": {
                        "items": [
                            {
                                "type": "sealstone",
                                "id": "arcane",
                                "amount": 1
                            }
                        ]
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "Let's head back. You can perform the Unsealing "
                                "once we're in the city."
                            )
                        }
                    ]
                },

                {
                    "unseal": {
                        "sealstone_type": "arcane",

                        # TODO: replace when the family is designed.
                        "forced_monster_id": "starter_storm_healer"
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "A Storm Servant with healing capabilities. "
                                "That'll change how you approach a fight."
                            )
                        }
                    ]
                },
            ]
        },


        # =========================================================
        # MISSION 3
        # =========================================================
        3: {
            "name": "First Assignment",

            "events": [
                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "Training's over. We've been assigned to protect "
                                "one of the roads outside the city."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "Nothing unusual. A few aggressive Nimaras "
                                "have been attacking travelers."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "This time you'll use both of your Servants."
                            )
                        },
                    ]
                },

                # -------------------------------------------------
                # 2v2 - healing tutorial
                # -------------------------------------------------
                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "road_nimara_1",
                                "level": 3
                            },
                            {
                                "monster_id": "road_nimara_2",
                                "level": 3
                            }
                        ],

                        "tutorial": {
                            "teach_healing": True,
                            "teach_team_combat": True
                        }
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "That's why a team matters. "
                                "Damage isn't the only thing that wins battles."
                            )
                        }
                    ]
                },

                # -------------------------------------------------
                # 2v3 - healing + attributes together
                # -------------------------------------------------
                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "road_nimara_storm",
                                "level": 3
                            },
                            {
                                "monster_id": "road_nimara_abyssal",
                                "level": 3
                            },
                            {
                                "monster_id": "road_nimara_1",
                                "level": 3
                            }
                        ],

                        "tutorial": {
                            "reinforce_attributes": True
                        }
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": "Looks like that's the last of them."
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "The Organization pays for completed assignments. "
                                "You've earned this."
                            )
                        }
                    ]
                },

                {
                    "reward": {
                        "items": [
                            {
                                "type": "sealstone",
                                "id": "arcane",
                                "amount": 1
                            }
                        ]
                    }
                },

                {
                    "unseal": {
                        "sealstone_type": "arcane",

                        # TODO: replace when the family is designed.
                        "forced_monster_id": "starter_abyssal_support"
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "Interesting. This one specializes in manipulating "
                                "the flow of battle rather than raw damage."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "You'll see soon enough what buffs and debuffs "
                                "can do."
                            )
                        }
                    ]
                },
            ]
        },


        # =========================================================
        # MISSION 4
        # =========================================================
        4: {
            "name": "Opened Ruins",

            "events": [
                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "We've received a strange report this morning."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "An entrance has appeared in some ancient ruins "
                                "outside the city."
                            )
                        },
                        {
                            "speaker": "player",
                            "text": "Appeared?"
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "That part of the structure was completely sealed "
                                "the last time it was surveyed."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "We're only checking the surroundings for now."
                            )
                        }
                    ]
                },

                # -------------------------------------------------
                # 3v2 - buffs/debuffs introduction
                # -------------------------------------------------
                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "ruins_outskirts_nimara_1",
                                "level": 4
                            },
                            {
                                "monster_id": "ruins_outskirts_nimara_2",
                                "level": 4
                            }
                        ],

                        "tutorial": {
                            "teach_buffs": True,
                            "teach_debuffs": True
                        }
                    }
                },

                # -------------------------------------------------
                # 3v3 - one Nimara clearly does not belong here
                # -------------------------------------------------
                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "ruins_outskirts_nimara_1",
                                "level": 4
                            },
                            {
                                "monster_id": "ruins_outskirts_nimara_2",
                                "level": 4
                            },

                            # TODO:
                            # Future mountain/snow-region Nimara.
                            {
                                "monster_id": "mountain_nimara_1",
                                "level": 5
                            }
                        ]
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": "Wait."
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "That last Nimara shouldn't be anywhere near this region."
                            )
                        },
                        {
                            "speaker": "player",
                            "text": "How far away does it normally live?"
                        },
                        {
                            "speaker": "senpai",
                            "text": "Far enough that this isn't a coincidence."
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "I'm reporting this. "
                                "We're not going inside without authorization."
                            )
                        }
                    ]
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "We've got permission. "
                                "The Organization wants us to investigate the ruins."
                            )
                        }
                    ]
                },
            ]
        },


        # =========================================================
        # MISSION 5
        # =========================================================
        5: {
            "name": "Ancient Ruins",

            "events": [
                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "No one knows exactly what these structures "
                                "were originally used for."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "Most of what we know about the ancient civilization "
                                "comes from places like this."
                            )
                        }
                    ]
                },

                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "ruins_nimara_1",
                                "level": 5
                            },
                            {
                                "monster_id": "ruins_nimara_2",
                                "level": 5
                            }
                        ]
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "These mechanisms have power running through them."
                            )
                        },
                        {
                            "speaker": "player",
                            "text": "Is that unusual?"
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "For ruins that have been inactive for centuries? "
                                "Very."
                            )
                        }
                    ]
                },

                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "ruins_nimara_1",
                                "level": 6
                            },
                            {
                                "monster_id": "ruins_nimara_2",
                                "level": 5
                            },
                            {
                                "monster_id": "ruins_nimara_3",
                                "level": 5
                            }
                        ]
                    }
                },

                # -------------------------------------------------
                # Empowered Nimara
                # First appearance of Glyphs
                # -------------------------------------------------
                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "empowered_nimara_1",
                                "level": 7,

                                # Exact Glyph TBD.
                                "glyphs": [
                                    "tutorial_glyph"
                                ]
                            }
                        ]
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": "That wasn't normal."
                        },
                        {
                            "speaker": "player",
                            "text": "It was stronger than the others."
                        },
                        {
                            "speaker": "senpai",
                            "text": "It was using a Glyph."
                        },
                        {
                            "speaker": "player",
                            "text": "A Glyph?"
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "Ancient technology. "
                                "Binders use them to strengthen their Servants."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "But a free Nimara shouldn't be equipped with one."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": "Someone put it there."
                        }
                    ]
                },
            ]
        },


        # =========================================================
        # MISSION 6
        # =========================================================
        6: {
            "name": "The Hidden Hand",

            "events": [
                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "Whatever is happening here, "
                                "we're close to the source."
                            )
                        }
                    ]
                },

                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "ruins_nimara_2",
                                "level": 7
                            },
                            {
                                "monster_id": "ruins_nimara_3",
                                "level": 7
                            }
                        ]
                    }
                },

                # -------------------------------------------------
                # First appearance of the unknown antagonist
                # -------------------------------------------------
                {
                    "dialog": [
                        {
                            "speaker": "unknown",
                            "text": "You've come further than I expected."
                        },
                        {
                            "speaker": "senpai",
                            "text": "Who are you?"
                        },
                        {
                            "speaker": "unknown",
                            "text": "That isn't important."
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "The Nimaras outside. "
                                "The Glyph. That was you."
                            )
                        },
                        {
                            "speaker": "unknown",
                            "text": "You're beginning to understand."
                        },
                    ]
                },

                # Eventually this can become a dedicated cinematic/event.
                {
                    "dialog": [
                        {
                            "speaker": "unknown",
                            "text": "Let's see how much your new Binder has learned."
                        }
                    ]
                },

                # -------------------------------------------------
                # CHAPTER 1 BOSS
                #
                # Boss design:
                # - changes attribute after being attacked
                # - buffs itself
                # - forces attribute rotation
                # - rewards healing + buffs/debuffs
                #
                # Exact kit belongs in monster design, not here.
                # -------------------------------------------------
                {
                    "battle": {
                        "enemies": [
                            {
                                "monster_id": "chapter_1_boss",
                                "level": 10
                            }
                        ],

                        "boss": True
                    }
                },

                {
                    "dialog": [
                        {
                            "speaker": "unknown",
                            "text": "Interesting."
                        },
                        {
                            "speaker": "senpai",
                            "text": "Don't move!"
                        },
                        {
                            "speaker": "unknown",
                            "text": "Another time."
                        }
                    ]
                },

                {
                    "dialog": [
                        {
                            "speaker": "player",
                            "text": "He was controlling that Nimara."
                        },
                        {
                            "speaker": "senpai",
                            "text": "I know."
                        },
                        {
                            "speaker": "player",
                            "text": "Without a Sealstone."
                        },
                        {
                            "speaker": "senpai",
                            "text": "...I know."
                        },
                        {
                            "speaker": "senpai",
                            "text": "We're going back. The Organization needs to hear this."
                        }
                    ]
                },

                # -------------------------------------------------
                # Back at the Organization
                # -------------------------------------------------
                {
                    "dialog": [
                        {
                            "speaker": "senpai",
                            "text": (
                                "They'll investigate the ruins and everything "
                                "we found down there."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "For now, there's something else you need to know."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "Your Gryphon has reached the limit of its current "
                                "manifestation."
                            )
                        },
                        {
                            "speaker": "player",
                            "text": "Level 10?"
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "Every Servant eventually reaches a point where "
                                "ordinary combat experience isn't enough."
                            )
                        },
                        {
                            "speaker": "senpai",
                            "text": (
                                "If you want it to keep growing, "
                                "you'll need to learn about Breakthroughs."
                            )
                        }
                    ]
                },

                {
                    "unlock": {
                        # Name provisional.
                        "content": "breakthrough_grounds"
                    }
                },
            ]
        },
    }
}