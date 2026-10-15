class_name PrototypeFactory
extends RefCounted

const MonsterScript = preload("res://scripts/models/monster.gd")
const DamageSkillScript = preload("res://scripts/models/damage_skill.gd")
const SupportSkillScript = preload("res://scripts/models/support_skill.gd")

const LEVEL_ONE_MULTIPLIER := 0.35


static func create_level_one_monster(monster_id: String):
    var monster = null

    match monster_id:
        "drake_igneous":
            monster = _create_igneous_drake()
        "drake_abyssal":
            monster = _create_abyssal_drake()
        "drake_aether":
            monster = _create_aether_drake()
        "drake_storm":
            monster = _create_storm_drake()
        "drake_void":
            monster = _create_void_drake()
        "dullahan_void":
            monster = _create_void_dullahan()
        "slime_storm":
            monster = _create_storm_slime()
        "slime_abyssal":
            monster = _create_abyssal_slime()
        "slime_igneous":
            monster = _create_igneous_slime()
        _:
            push_error("Unknown prototype monster id: %s" % monster_id)
            return null

    _attach_skill_descriptions(monster)
    return monster


static func _attach_skill_descriptions(monster) -> void:
    var descriptions := {
        "draconic_claw":
            "Attacks one enemy. Has a 30% chance to apply Defense Break for 2 turns.",

        "scorching_breath":
            "Attacks all enemies twice. Deals increased damage based on the target's Burn stacks.",

        "flame_devourer":
            "Attacks one enemy. Deals increased damage based on Burn stacks, then consumes the Burn present before the attack to heal the caster.",

        "rime_breath":
            "Attacks all enemies twice. Each hit has a 50% chance to apply Speed Break for 2 turns.",

        "glacial_collapse":
            "Attacks all enemies, reducing their Action Gauge by 10%. Enemies with Speed Break are also subject to Freeze for 1 turn.",

        "lightning_rush":
            "Attacks one enemy twice, then grants the caster Speed Up for 2 turns.",

        "stormbreak":
            "Strikes enemies 10 times at random, hitting each living enemy at least once first. A target hit 3 or more times has a 50% chance to be Stunned. Later repeated hits deal reduced damage, while the first hit gains bonus damage if the caster has Speed Up.",

        "sovereign_breath":
            "Attacks all enemies. Afterwards, attempts to Silence them for 1 turn. Silence chance increases by 10% for each buff on the caster, from 30% up to 80%.",

        "heavens_decree":
            "Grants all allies Attack Up, Immunity and Veil for 2 turns.",

        "null_rend":
            "Attacks one enemy twice. The second hit has a 60% chance to apply Oblivion for 2 turns.",

        "dismantle":
            "Attacks all enemies 3 times. The first hit strips buffs. Hits 2 and 3 gain 8% damage for every buff removed and each has a 30% chance to apply Defense Break for 2 turns.",

        "severing_blade":
            "Attacks one enemy. Has a 30% chance to apply Heal Block for 2 turns.",

        "spinal_scourge":
            "Attacks all enemies 3 times. Damage increases by 5% for each monster that has died in battle, up to 25%.",

        "deaths_gaze":
            "Names one enemy for 2 turns before dealing damage and attempts to apply Vulnerability for 2 turns. While a target is Named, this Dullahan becomes Headless, gaining 20% Speed and immunity to Silence unless affected by Oblivion.",

        "ooze_slam":
            "Attacks one enemy."
    }

    for skill in monster.skills:
        skill.description = str(
            descriptions.get(skill.skill_id, "")
        )


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
            },
            {},
            "all_enemies"
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


static func _create_abyssal_drake():
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
            "rime_breath",
            "Rime Breath",
            3.15,
            2,
            [],
            "attack",
            4,
            [
                {
                    "effect_id": "speed_break",
                    "chance": 0.50,
                    "turns": 2,
                    "trigger": "per_hit"
                }
            ],
            {},
            {},
            "all_enemies"
        ),

        DamageSkillScript.new(
            "glacial_collapse",
            "Glacial Collapse",
            4.10,
            1,
            [],
            "attack",
            5,
            [
                {
                    "effect_id": "freeze",
                    "chance": 1.00,
                    "turns": 1,
                    "trigger": "per_hit",
                    "condition": {
                        "type": "target_has_debuff",
                        "effect_id": "speed_break"
                    }
                }
            ],
            {},
            {},
            "all_enemies",
            0.10
        )
    ]

    var monster = MonsterScript.new(
        "drake_abyssal",
        "Vharak",
        "Drake",
        "abyssal",
        5,
        _scaled(14075),
        _scaled(693),
        _scaled(921),
        _scaled(216),
        skills,
        LEVEL_ONE_MULTIPLIER
    )

    monster.combat_resources["frozen_scales"] = 0
    monster.combat_resource_maximums[
        "frozen_scales"
    ] = 3

    return monster


static func _create_void_dullahan():
    var severing_blade = DamageSkillScript.new(
        "severing_blade",
        "Severing Blade",
        2.60,
        1,
        [],
        "attack",
        0,
        [
            {
                "effect_id": "heal_block",
                "chance": 0.30,
                "turns": 2,
                "trigger": "after_skill"
            }
        ]
    )

    var spinal_scourge = DamageSkillScript.new(
        "spinal_scourge",
        "Spinal Scourge",
        1.40,
        3,
        [],
        "attack",
        4,
        [],
        {},
        {},
        "all_enemies"
    )

    spinal_scourge.damage_per_dead_monster = 0.05
    spinal_scourge.max_dead_monsters = 5
    spinal_scourge.max_dead_monster_bonus = 0.25

    var deaths_gaze = DamageSkillScript.new(
        "deaths_gaze",
        "Death's Gaze",
        4.70,
        1,
        [],
        "attack",
        6,
        []
    )

    deaths_gaze.apply_named_before_hit = true
    deaths_gaze.named_turns = 2
    deaths_gaze.vulnerability_chance = 1.00
    deaths_gaze.vulnerability_turns = 2

    var skills: Array = [
        severing_blade,
        spinal_scourge,
        deaths_gaze
    ]

    return MonsterScript.new(
        "dullahan_void",
        "Void Dullahan",
        "Dullahan",
        "void",
        5,
        _scaled(10500),
        _scaled(1015),
        _scaled(650),
        _scaled(228),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_void_drake():
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
            "null_rend",
            "Null Rend",
            2.10,
            2,
            [],
            "attack",
            4,
            [
                {
                    "effect_id": "oblivion",
                    "chance": 0.60,
                    "turns": 2,
                    "hit_indices": [1]
                }
            ]
        ),

        DamageSkillScript.new(
            "dismantle",
            "Dismantle",
            1.45,
            3,
            [],
            "attack",
            5,
            [
                {
                    "effect_id": "defense_break",
                    "chance": 0.30,
                    "turns": 2,
                    "hit_indices": [1, 2]
                }
            ],
            {},
            {},
            "all_enemies",
            0.0,
            "",
            {},
            true,
            0,
            0.08,
            [1, 2]
        )
    ]

    var monster = MonsterScript.new(
        "drake_void",
        "Void Drake",
        "Drake",
        "void",
        5,
        _scaled(10750),
        _scaled(995),
        _scaled(670),
        _scaled(230),
        skills,
        LEVEL_ONE_MULTIPLIER
    )

    return monster


static func _create_storm_drake():
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
            "lightning_rush",
            "Lightning Rush",
            1.75,
            2,
            [],
            "attack",
            4,
            []
        ),

        DamageSkillScript.new(
            "stormbreak",
            "Stormbreak",
            1.60,
            10,
            [],
            "attack",
            6,
            [
                {
                    "effect_id": "stun",
                    "chance": 0.50,
                    "turns": 1,
                    "trigger": "hit_count_threshold",
                    "min_hits": 3
                }
            ],
            {},
            {},
            "random_enemies",
            0.0,
            "one_each_then_random",
            {
                "full_damage_hits": 5,
                "later_hit_multiplier": 0.25,
                "first_hit_bonus_if_caster_buff": {
                    "effect_id": "speed_up",
                    "multiplier": 1.50
                }
            }
        )
    ]

    return MonsterScript.new(
        "drake_storm",
        "Storm Drake",
        "Drake",
        "storm",
        5,
        _scaled(9875),
        _scaled(1047),
        _scaled(653),
        _scaled(236),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_aether_drake():
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
            "sovereign_breath",
            "Sovereign Breath",
            3.00,
            1,
            [],
            "attack",
            4,
            [],
            {},
            {},
            "all_enemies"
        ),

        SupportSkillScript.new(
            "heavens_decree",
            "Heaven's Decree",
            6,
            [
                {
                    "effect_id": "attack_up",
                    "turns": 2
                },
                {
                    "effect_id": "immunity",
                    "turns": 2
                },
                {
                    "effect_id": "veil",
                    "turns": 2
                }
            ],
            "all_allies"
        )
    ]

    return MonsterScript.new(
        "drake_aether",
        "Aether Drake",
        "Drake",
        "aether",
        5,
        _scaled(12850),
        _scaled(725),
        _scaled(815),
        _scaled(230),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


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


static func _create_abyssal_slime():
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
        "slime_abyssal",
        "Abyssal Slime",
        "Slime",
        "abyssal",
        1,
        _scaled(8300),
        _scaled(420),
        _scaled(390),
        _scaled(130),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_igneous_slime():
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
        "slime_igneous",
        "Igneous Slime",
        "Slime",
        "igneous",
        1,
        _scaled(7600),
        _scaled(485),
        _scaled(330),
        _scaled(138),
        skills,
        LEVEL_ONE_MULTIPLIER
    )
