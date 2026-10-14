class_name PrototypeFactory
extends RefCounted

const MonsterScript = preload("res://scripts/models/monster.gd")
const DamageSkillScript = preload("res://scripts/models/damage_skill.gd")

const LEVEL_ONE_MULTIPLIER := 0.35


static func create_level_one_monster(monster_id: String):
    match monster_id:
        "drake_igneous":
            return _create_igneous_drake()
        "slime_storm":
            return _create_storm_slime()
        _:
            push_error("Unknown prototype monster id: %s" % monster_id)
            return null


static func _scaled(value: float) -> int:
    return int(round(value * LEVEL_ONE_MULTIPLIER))


static func _create_igneous_drake():
    var skills: Array = [
        DamageSkillScript.new(
            "draconic_claw",
            "Draconic Claw",
            2.5,
            1,
            [],
            "attack",
            0,
            [
                {
                    "effect_id": "defense_break",
                    "chance": 0.30,
                    "turns": 2
                }
            ]
        ),

        DamageSkillScript.new(
            "scorching_breath",
            "Scorching Breath",
            3.75,
            2,
            [],
            "attack",
            4,
            [],
            {
                "multipliers_by_stacks": {
                    1: 1.08,
                    2: 1.16,
                    3: 1.24
                }
            }
        ),

        DamageSkillScript.new(
            "flame_devourer",
            "Flame Devourer",
            4.6,
            1,
            [],
            "attack",
            5,
            [],
            {
                "multipliers_by_stacks": {
                    1: 1.15,
                    2: 1.30,
                    3: 1.45
                }
            },
            {
                "heal_by_stacks": {
                    1: 0.12,
                    2: 0.25,
                    3: 0.40
                }
            }
        )
    ]

    var monster = MonsterScript.new(
        "drake_igneous",
        "Kaelgor",
        "Drake",
        "igneous",
        5,
        _scaled(12125),
        _scaled(963),
        _scaled(707),
        _scaled(224),
        skills,
        LEVEL_ONE_MULTIPLIER
    )

    # Cinderblood (base): each landed hit has a 35% chance to attempt
    # applying one Burn stack for 2 turns.
    monster.on_hit_effects = [
        {
            "effect_id": "burn",
            "chance": 0.35,
            "turns": 2,
            "stacks": 1
        }
    ]

    return monster


static func _create_storm_slime():
    var skills: Array = [
        DamageSkillScript.new(
            "ooze_slam",
            "Ooze Slam",
            2.3,
            1,
            [],
            "attack",
            0,
            []
        )
    ]

    return MonsterScript.new(
        "slime_storm",
        "Storm Slime",
        "Slime",
        "storm",
        1,
        _scaled(7200),
        _scaled(455),
        _scaled(320),
        _scaled(150),
        skills,
        LEVEL_ONE_MULTIPLIER
    )
