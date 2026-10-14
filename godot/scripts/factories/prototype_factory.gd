class_name PrototypeFactory
extends RefCounted

const LEVEL_ONE_MULTIPLIER := 0.35


static func create_level_one_monster(monster_id: String) -> Monster:
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


static func _create_igneous_drake() -> Monster:
    var skills: Array[Skill] = [
        DamageSkill.new(
            "draconic_claw",
            "Draconic Claw",
            2.5,
            1,
            [],
            "attack",
            0
        )
    ]

    return Monster.new(
        "drake_igneous",
        "Kaelgor",
        "Drake",
        "igneous",
        5,
        _scaled(12125),
        _scaled(963),
        _scaled(707),
        _scaled(224),
        skills
    )


static func _create_storm_slime() -> Monster:
    var skills: Array[Skill] = [
        DamageSkill.new(
            "ooze_slam",
            "Ooze Slam",
            2.3,
            1,
            [],
            "attack",
            0
        )
    ]

    return Monster.new(
        "slime_storm",
        "Storm Slime",
        "Slime",
        "storm",
        1,
        _scaled(7200),
        _scaled(455),
        _scaled(320),
        _scaled(150),
        skills
    )
