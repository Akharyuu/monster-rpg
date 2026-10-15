class_name PrototypeFactory
extends RefCounted

const MonsterScript = preload("res://scripts/models/monster.gd")
const DamageSkillScript = preload("res://scripts/models/damage_skill.gd")
const SupportSkillScript = preload("res://scripts/models/support_skill.gd")

const LEVEL_ONE_MULTIPLIER := 0.35


static func create_level_one_monster(
    monster_id: String,
    resonance: int = 0
):
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
        "dullahan_aether":
            monster = _create_aether_dullahan()
        "dullahan_igneous":
            monster = _create_igneous_dullahan()
        "dullahan_abyssal":
            monster = _create_abyssal_dullahan()
        "dullahan_storm":
            monster = _create_storm_dullahan()
        "thornet_igneous":
            monster = _create_thornet("igneous")
        "thornet_abyssal":
            monster = _create_thornet("abyssal")
        "thornet_storm":
            monster = _create_thornet("storm")
        "wisp_igneous":
            monster = _create_wisp("igneous")
        "wisp_abyssal":
            monster = _create_wisp("abyssal")
        "wisp_storm":
            monster = _create_wisp("storm")
        "sprout_igneous":
            monster = _create_sprout("igneous")
        "sprout_abyssal":
            monster = _create_sprout("abyssal")
        "sprout_storm":
            monster = _create_sprout("storm")
        "griffon_igneous":
            monster = _create_igneous_griffon()
        "dryad_storm":
            monster = _create_storm_dryad()
        "slime_storm":
            monster = _create_storm_slime()
        "slime_abyssal":
            monster = _create_abyssal_slime()
        "slime_igneous":
            monster = _create_igneous_slime()
        _:
            push_error("Unknown prototype monster id: %s" % monster_id)
            return null

    monster.resonance = clampi(resonance, 0, 5)
    _apply_resonance(monster)
    _attach_skill_descriptions(monster)
    _attach_passive_description(monster)
    return monster


static func _attach_skill_descriptions(monster) -> void:
    var tooltip_data := {
        "draconic_claw": {
            "summary": "A precise claw strike against one enemy.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]30% chance[/b] to apply [color=#ff7777]Defense Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "scorching_breath": {
            "summary": "Engulfs all enemies in a two-hit breath attack.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases with the target's [color=#ff7777]Burn[/color] stacks."
                }
            ]
        },

        "flame_devourer": {
            "summary": "Consumes the target's flames to empower the strike and restore the caster.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Deals increased damage based on [color=#ff7777]Burn[/color] stacks."
                },
                {
                    "kind": "heal",
                    "text": "Consumes the Burn present before the attack and [color=#76e6a8]heals the caster[/color]."
                }
            ]
        },

        "rime_breath": {
            "summary": "A freezing breath that strikes the entire enemy team twice.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Each hit has a [b]50% chance[/b] to apply [color=#ff7777]Speed Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "glacial_collapse": {
            "summary": "Crushes the enemy team under a sudden glacial impact.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Reduces each target's [b]Action Gauge by 10%[/b]."
                },
                {
                    "kind": "control",
                    "text": "Targets with [color=#ff7777]Speed Break[/color] can be [color=#ff7777]Frozen[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "lightning_rush": {
            "summary": "Rushes one enemy with two rapid lightning-infused strikes.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "After attacking, grants the caster [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "stormbreak": {
            "summary": "Unleashes ten lightning strikes across random enemies.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Hits every living enemy at least once before distributing the remaining strikes randomly."
                },
                {
                    "kind": "control",
                    "text": "A target hit [b]3+ times[/b] has a [b]50% chance[/b] to be [color=#ff7777]Stunned[/color]."
                },
                {
                    "kind": "damage",
                    "text": "Repeated hits after the fifth deal reduced damage. The first hit gains bonus damage while the caster has [color=#70c8ff]Speed Up[/color]."
                }
            ]
        },

        "sovereign_breath": {
            "summary": "Blasts all enemies with sovereign aether.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Attempts to apply [color=#ff7777]Silence[/color] for [b]1 turn[/b]."
                },
                {
                    "kind": "special",
                    "text": "Silence chance starts at [b]30%[/b] and gains [b]+10% per caster buff[/b], up to [b]80%[/b]."
                }
            ]
        },

        "heavens_decree": {
            "summary": "Empowers the entire allied team with celestial authority.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "Grants [color=#70c8ff]Attack Up[/color], [color=#70c8ff]Immunity[/color] and [color=#70c8ff]Veil[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "null_rend": {
            "summary": "Tears into one enemy with two void-infused strikes.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "The second hit has a [b]60% chance[/b] to apply [color=#ff7777]Oblivion[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "dismantle": {
            "summary": "Disassembles the enemy team's defenses over three sweeping hits.",
            "effects": [
                {
                    "kind": "special",
                    "text": "[b]Hit 1:[/b] strips enemy buffs."
                },
                {
                    "kind": "damage",
                    "text": "[b]Hits 2-3:[/b] gain [b]+8% damage[/b] for every buff removed."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hits 2-3:[/b] each has a [b]30% chance[/b] to apply [color=#ff7777]Defense Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "needle_rush": {
            "summary": "Strikes one enemy twice with venomous needles.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Each hit has a [b]35% chance[/b] to apply [color=#ff7777]Poison[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "fever_sting": {
            "summary": "Drives three fevered stings into one enemy.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Deals increased damage if the target is already affected by [color=#ff7777]Poison[/color]."
                }
            ]
        },

        "numbing_sting": {
            "summary": "Pierces one enemy twice with numbing venom.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Each hit has a [b]25% chance[/b] to apply [color=#ff7777]Poison[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "If this skill applies Poison, has a [b]60% chance[/b] to apply [color=#ff7777]Stun[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "swarm_pierce": {
            "summary": "Overwhelms one enemy with three rapid piercing attacks.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "If the target already has a debuff when the skill begins, each successive hit deals more damage."
                }
            ]
        },

        "will_o_glow": {
            "summary": "Launches a flickering spirit flame at one enemy.",
            "effects": [
                {
                    "kind": "control",
                    "text": "[b]60% chance[/b] to reduce the target's [b]Action Gauge by 10%[/b]."
                }
            ]
        },

        "nurturing_lash": {
            "summary": "Strikes one enemy with a living vine, then restores a wounded ally.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "After attacking, heals the living ally with the lowest HP ratio for [b]5% of the caster's Max HP[/b]."
                }
            ]
        },

        "rending_talons": {
            "summary": "Rends one enemy with a powerful talon strike.",
            "effects": []
        },

        "searing_gale": {
            "summary": "Unleashes a scorching gale that tears through all enemies in two waves.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Each hit has a [b]50% chance[/b] to reduce the target's [b]Action Gauge by 20%[/b]."
                }
            ]
        },

        "meteor_dive": {
            "summary": "Crashes down on one enemy with overwhelming speed.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases according to the caster's Speed."
                }
            ]
        },

        "meteor_dive_violent_crash": {
            "summary": "Crashes down on one enemy with overwhelming speed.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases according to the caster's Speed."
                },
                {
                    "kind": "debuff",
                    "text": "If the target has less than [b]50% Action Gauge[/b], has a [b]75% chance[/b] to apply [color=#ff7777]Stun[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "meteor_dive_terminal_impact": {
            "summary": "Crashes down on one enemy with overwhelming speed.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases according to the caster's Speed."
                },
                {
                    "kind": "debuff",
                    "text": "Applies [color=#ff7777]Stun[/color] for [b]1 turn[/b] if the target has less than [b]50% Action Gauge[/b]."
                },
                {
                    "kind": "special",
                    "text": "While the caster has [color=#70c8ff]Speed Up[/color], the Action Gauge threshold becomes [b]70%[/b]."
                }
            ]
        },

        "searing_gale_turbulence": {
            "summary": "Unleashes a scorching gale that tears through all enemies in two waves.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Each hit has a [b]75% chance[/b] to reduce the target's [b]Action Gauge by 20%[/b]."
                }
            ]
        },

        "searing_gale_heatstorm": {
            "summary": "Unleashes an intensified scorching gale across the enemy team.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Each hit has a [b]75% chance[/b] to reduce the target's [b]Action Gauge by 30%[/b]."
                },

            ]
        },

        "vine_barrage": {
            "summary": "Strikes one enemy with three rapid vines.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "After attacking, heals the living ally with the lowest HP ratio for [b]8% of the caster's Max HP[/b]."
                }
            ]
        },

        "vine_barrage_nourishment": {
            "summary": "Strikes one enemy with three rapid vines, then channels stronger restorative energy.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "After attacking, heals the living ally with the lowest HP ratio for [b]15% of the caster's Max HP[/b]."
                }
            ]
        },

        "breath_of_the_grove": {
            "summary": "Channels restorative energy through the entire allied team.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "Heals all living allies for [b]25% of the caster's Max HP[/b]."
                }
            ]
        },

        "breath_of_the_grove_sanctuary": {
            "summary": "Bathes the allied team in restorative energy and protective grace.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "Heals all living allies for [b]35% of the caster's Max HP[/b]."
                },
                {
                    "kind": "buff",
                    "text": "Grants [color=#70c8ff]Immunity[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "breath_of_the_grove_evergreen": {
            "summary": "Floods the allied team with lasting restorative energy.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "Heals all living allies for [b]35% of the caster's Max HP[/b]."
                },
                {
                    "kind": "buff",
                    "text": "Grants [color=#70c8ff]Immunity[/color] for [b]1 turn[/b]."
                },
                {
                    "kind": "buff",
                    "text": "Grants [color=#70c8ff]Regrowth[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "gale_pursuit": {
            "summary": "Sweeps through the enemy team in a burst of storm speed.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Reduces each enemy's [b]Action Gauge by 20%[/b]."
                }
            ]
        },

        "headlong_charge": {
            "summary": "Accelerates the Dullahan and pulls an ally into the fight.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "Grants the caster [color=#70c8ff]Attack Up[/color] and [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "Increases the living ally with the lowest Action Gauge by [b]20%[/b]."
                }
            ]
        },

        "spectral_shackles": {
            "summary": "Binds one enemy with two spectral strikes.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]Hit 1:[/b] 50% chance to apply [color=#ff7777]Speed Break[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hit 2:[/b] 50% chance to apply [color=#ff7777]Attack Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "relentless_pursuit": {
            "summary": "Relentlessly hunts down a wounded enemy with two strikes.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases as the target loses Health, up to [b]+30%[/b] at 0% HP."
                }
            ]
        },

        "death_sentence": {
            "summary": "Delivers a lethal single-target strike.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "If the target starts the skill below [b]25% HP[/b], ignores [b]50% of its Defense[/b]."
                }
            ]
        },

        "soulpiercer": {
            "summary": "Pierces one enemy with condensed soul energy.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Deals [b]+6% damage[/b] for each [color=#d9a6ff]Soul Charge[/color], up to [b]5[/b]."
                }
            ]
        },

        "beyond_the_veil": {
            "summary": "Releases stored souls in a four-hit attack against all enemies.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Consumes all [color=#d9a6ff]Soul Charges[/color] before attacking."
                },
                {
                    "kind": "damage",
                    "text": "Each consumed Soul Charge grants [b]+10% damage[/b]."
                }
            ]
        },

        "severing_blade": {
            "summary": "A heavy single-target slash.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]30% chance[/b] to apply [color=#ff7777]Heal Block[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "spinal_scourge": {
            "summary": "Sweeps through all enemies with three brutal strikes.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Gains [b]+5% damage[/b] for every monster that has died in battle, up to [b]+25%[/b]."
                }
            ]
        },

        "deaths_gaze": {
            "summary": "Names one enemy for death before delivering a devastating strike.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Applies [color=#d9a6ff]Named[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "Applies [color=#ff7777]Vulnerability[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "While a target is Named, the Dullahan becomes [color=#d9a6ff]Headless[/color]: [b]+20% Speed[/b] and immunity to Silence unless affected by Oblivion."
                }
            ]
        },

        "ooze_slam": {
            "summary": "Slams into one enemy.",
            "effects": []
        }
    }

    for skill in monster.skills:
        var data: Dictionary = tooltip_data.get(
            skill.skill_id,
            {}
        )

        skill.tooltip_summary = str(
            data.get("summary", skill.description)
        )

        skill.tooltip_effects = data.get(
            "effects",
            []
        )

        skill.description = skill.tooltip_summary

static func _attach_passive_description(monster) -> void:
    var passive_data := {
        "drake_igneous": {
            "name": "Cinderblood",
            "summary": "Each landed hit can ignite the target.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Each hit has a [b]35% chance[/b] to apply [color=#ff7777]Burn[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "drake_abyssal": {
            "name": "Frozen Scales",
            "summary": "Builds Frozen Scales through successful Freezes, then consumes them to fortify the caster.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Each enemy Frozen by [b]Glacial Collapse[/b] grants [b]1 Frozen Scale[/b], up to [b]3[/b]."
                },
                {
                    "kind": "buff",
                    "text": "Before casting Glacial Collapse at [b]3/3[/b], consumes all scales and grants [color=#70c8ff]Defense Up[/color] and [color=#70c8ff]Immunity[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "drake_storm": {
            "name": "Thunderheart",
            "summary": "Converts bonus Speed into offensive power.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases by [b]0.3%[/b] for every point of Speed above the base value."
                }
            ]
        },

        "drake_aether": {
            "name": "Celestial Authority",
            "summary": "Punishes enemies that strike the Aether Drake.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "When hit, has a [b]30% chance[/b] to apply [color=#ff7777]Attack Break[/color] to the attacker for [b]2 turns[/b]."
                }
            ]
        },

        "drake_void": {
            "name": "Bottomless Hunger",
            "summary": "Feeds on buffs removed from enemies.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "For each enemy buff removed, heals [b]10% Max HP[/b]."
                },
                {
                    "kind": "special",
                    "text": "For each enemy buff removed, gains [b]8% Action Gauge[/b]."
                }
            ]
        },

        "dullahan_storm": {
            "name": "The Hunt",
            "summary": "Steals momentum from the enemy closest to taking a turn.",
            "effects": [
                {
                    "kind": "special",
                    "text": "After this monster's turn, steals up to [b]20% Action Gauge[/b] from the living enemy with the highest Action Gauge."
                }
            ]
        },

        "dullahan_abyssal": {
            "name": "Chilling Presence",
            "summary": "Extends the enemy team's debuffs after every turn.",
            "effects": [
                {
                    "kind": "special",
                    "text": "After this monster's turn, extends [b]1 random extendable debuff[/b] on each living enemy by [b]1 turn[/b]."
                },
                {
                    "kind": "special",
                    "text": "[color=#d9a6ff]Stun[/color] and [color=#d9a6ff]Freeze[/color] cannot be extended."
                }
            ]
        },

        "dullahan_aether": {
            "name": "Soul Vessel",
            "summary": "Collects Soul Charges through combat and empowers soul-based attacks.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Gains [b]1 Soul Charge[/b] after using a damage skill, up to [b]5[/b]."
                },
                {
                    "kind": "special",
                    "text": "Gains [b]1 Soul Charge[/b] whenever any monster dies."
                },
                {
                    "kind": "special",
                    "text": "[b]Beyond the Veil[/b] consumes all stored Soul Charges before attacking."
                }
            ]
        },

        "dullahan_void": {
            "name": "Headless Rider",
            "summary": "Empowers the Dullahan while it has a Named target.",
            "effects": [
                {
                    "kind": "special",
                    "text": "While [color=#d9a6ff]Headless[/color], gains [b]+20% Speed[/b]."
                },
                {
                    "kind": "special",
                    "text": "While Headless, cannot be Silenced unless affected by [color=#ff7777]Oblivion[/color]."
                }
            ]
        }
    }

    monster.passive_tooltip = passive_data.get(
        monster.monster_id,
        {}
    )

    if (
        monster.monster_id == "dryad_storm"
        and monster.resonance >= 1
    ):
        monster.passive_tooltip = {
            "name": (
                "Nature's Grace: Overgrowth"
                if monster.resonance >= 5
                else "Nature's Grace"
            ),
            "summary": "Strengthens direct healing on wounded allies.",
            "effects": [
                {
                    "kind": "heal",
                    "text": "Direct healing is increased by [b]20%[/b] when the target is below [b]50% HP[/b]."
                }
            ]
        }

        if monster.resonance >= 5:
            monster.passive_tooltip["effects"].append(
                {
                    "kind": "buff",
                    "text": "Overhealing is partially converted into a [color=#70c8ff]Shield[/color], up to [b]10% of the target's Max HP[/b]."
                }
            )

    if (
        monster.monster_id == "griffon_igneous"
        and monster.resonance >= 2
    ):
        monster.passive_tooltip = {
            "name": "Hawk Instinct",
            "summary": "Accelerates the Griffon whenever it successfully stuns an enemy.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "When this monster applies [color=#ff7777]Stun[/color], gains [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                }
            ]
        }


static func _scaled(value: float) -> int:
    return int(round(value * LEVEL_ONE_MULTIPLIER))


static func _apply_resonance(monster) -> void:
    if monster.monster_id == "dryad_storm":
        if monster.resonance >= 2:
            var sanctuary = SupportSkillScript.new(
                "breath_of_the_grove_sanctuary",
                "Breath of the Grove: Sanctuary",
                5,
                [
                    {
                        "effect_id": "immunity",
                        "turns": 1
                    }
                ],
                "all_allies"
            )
            sanctuary.healing_hp_ratio = 0.35
            monster.skills[1] = sanctuary

        if monster.resonance >= 3:
            var nourishment = DamageSkillScript.new(
                "vine_barrage_nourishment",
                "Vine Barrage: Nourishment",
                0.70,
                3,
                [],
                "attack",
                0,
                []
            )
            monster.skills[0] = nourishment

        if monster.resonance >= 4:
            var evergreen = SupportSkillScript.new(
                "breath_of_the_grove_evergreen",
                "Breath of the Grove: Evergreen",
                4,
                [
                    {
                        "effect_id": "immunity",
                        "turns": 1
                    },
                    {
                        "effect_id": "regrowth",
                        "turns": 2
                    }
                ],
                "all_allies"
            )
            evergreen.healing_hp_ratio = 0.35
            monster.skills[1] = evergreen

        return

    if monster.monster_id == "griffon_igneous":
        if monster.resonance >= 1:
            var violent_crash = DamageSkillScript.new(
                "meteor_dive_violent_crash",
                "Meteor Dive: Violent Crash",
                4.20,
                1,
                [],
                "attack",
                5,
                [
                    {
                        "effect_id": "stun",
                        "chance": 0.75,
                        "turns": 1,
                        "trigger": "after_skill",
                        "condition": {
                            "type": "target_action_gauge_below",
                            "threshold": 0.50
                        }
                    }
                ]
            )
            violent_crash.speed_damage_scaling = 0.001
            monster.skills[2] = violent_crash

        if monster.resonance >= 3:
            var turbulence = DamageSkillScript.new(
                "searing_gale_turbulence",
                "Searing Gale: Turbulence",
                2.00,
                2,
                [],
                "attack",
                4,
                [],
                {},
                {},
                "all_enemies",
                0.20
            )
            turbulence.action_gauge_reduction_chance = 0.75
            monster.skills[1] = turbulence

        if monster.resonance >= 4:
            var terminal_impact = DamageSkillScript.new(
                "meteor_dive_terminal_impact",
                "Meteor Dive: Terminal Impact",
                4.20,
                1,
                [],
                "attack",
                4,
                [
                    {
                        "effect_id": "stun",
                        "chance": 1.00,
                        "turns": 1,
                        "trigger": "after_skill",
                        "condition": {
                            "type": "target_action_gauge_below",
                            "threshold": 0.50,
                            "threshold_if_caster_has_buff": {
                                "effect_id": "speed_up",
                                "threshold": 0.70
                            }
                        }
                    }
                ]
            )
            terminal_impact.speed_damage_scaling = 0.001
            monster.skills[2] = terminal_impact

        if monster.resonance >= 5:
            var heatstorm = DamageSkillScript.new(
                "searing_gale_heatstorm",
                "Searing Gale: Heatstorm",
                2.00,
                2,
                [],
                "attack",
                3,
                [],
                {},
                {},
                "all_enemies",
                0.30
            )
            heatstorm.action_gauge_reduction_chance = 0.75
            monster.skills[1] = heatstorm

        return


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


static func _create_thornet(attribute: String):
    var needle_rush = DamageSkillScript.new(
        "needle_rush",
        "Needle Rush",
        1.65,
        2,
        [],
        "attack",
        0,
        [
            {
                "effect_id": "poison",
                "chance": 0.35,
                "turns": 2,
                "trigger": "per_hit"
            }
        ]
    )

    var second_skill = null

    match attribute:
        "igneous":
            second_skill = DamageSkillScript.new(
                "fever_sting",
                "Fever Sting",
                1.55,
                3,
                [],
                "attack",
                4,
                []
            )
            second_skill.conditional_required_debuff_id = "poison"
            second_skill.conditional_damage_multiplier = 1.15

        "abyssal":
            second_skill = DamageSkillScript.new(
                "numbing_sting",
                "Numbing Sting",
                2.50,
                2,
                [],
                "attack",
                4,
                [
                    {
                        "effect_id": "poison",
                        "chance": 0.25,
                        "turns": 2,
                        "trigger": "per_hit"
                    },
                    {
                        "effect_id": "stun",
                        "chance": 0.60,
                        "turns": 1,
                        "trigger": "after_skill",
                        "condition": {
                            "type": "target_gained_debuff",
                            "effect_id": "poison"
                        }
                    }
                ]
            )

        "storm":
            second_skill = DamageSkillScript.new(
                "swarm_pierce",
                "Swarm Pierce",
                2.50,
                3,
                [],
                "attack",
                4,
                []
            )
            second_skill.conditional_requires_any_debuff = true
            second_skill.conditional_hit_damage_multipliers = [
                1.00,
                1.15,
                1.30
            ]

    var monster_id: String = "thornet_%s" % attribute
    var display_name: String = "%s Thornet" % attribute.capitalize()

    var hp: int = 6150
    var attack: int = 675
    var defense: int = 352
    var speed: int = 166

    match attribute:
        "abyssal":
            hp = 6400
            attack = 585
            defense = 382
            speed = 174
        "storm":
            hp = 5850
            attack = 640
            defense = 338
            speed = 181

    var skills: Array = [
        needle_rush,
        second_skill
    ]

    return MonsterScript.new(
        monster_id,
        display_name,
        "Thornet",
        attribute,
        2,
        _scaled(hp),
        _scaled(attack),
        _scaled(defense),
        _scaled(speed),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_wisp(attribute: String):
    var will_o_glow = DamageSkillScript.new(
        "will_o_glow",
        "Will-o'-Glow",
        2.60,
        1,
        [],
        "attack",
        0,
        [],
        {},
        {},
        "single_enemy",
        0.10
    )
    will_o_glow.action_gauge_reduction_chance = 0.60

    var monster_id: String = "wisp_%s" % attribute
    var display_name: String = "%s Wisp" % attribute.capitalize()

    var hp: int = 5500
    var attack: int = 465
    var defense: int = 292
    var speed: int = 158

    match attribute:
        "abyssal":
            hp = 5750
            attack = 425
            defense = 318
            speed = 154
        "storm":
            hp = 5250
            attack = 445
            defense = 278
            speed = 166

    var skills: Array = [
        will_o_glow
    ]

    return MonsterScript.new(
        monster_id,
        display_name,
        "Wisp",
        attribute,
        1,
        _scaled(hp),
        _scaled(attack),
        _scaled(defense),
        _scaled(speed),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_sprout(attribute: String):
    var nurturing_lash = DamageSkillScript.new(
        "nurturing_lash",
        "Nurturing Lash",
        1.60,
        1,
        [],
        "attack",
        0,
        []
    )

    var monster_id: String = "sprout_%s" % attribute
    var display_name: String = "%s Sprout" % attribute.capitalize()

    var hp: int = 6900
    var attack: int = 410
    var defense: int = 470
    var speed: int = 142

    match attribute:
        "abyssal":
            hp = 7400
            attack = 350
            defense = 535
            speed = 134
        "storm":
            hp = 6600
            attack = 380
            defense = 455
            speed = 154

    var skills: Array = [
        nurturing_lash
    ]

    return MonsterScript.new(
        monster_id,
        display_name,
        "Sprout",
        attribute,
        1,
        _scaled(hp),
        _scaled(attack),
        _scaled(defense),
        _scaled(speed),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_igneous_griffon():
    var rending_talons = DamageSkillScript.new(
        "rending_talons",
        "Rending Talons",
        1.80,
        1,
        [],
        "attack",
        0,
        []
    )

    var searing_gale = DamageSkillScript.new(
        "searing_gale",
        "Searing Gale",
        2.00,
        2,
        [],
        "attack",
        4,
        [],
        {},
        {},
        "all_enemies",
        0.20
    )
    searing_gale.action_gauge_reduction_chance = 0.50

    var meteor_dive = DamageSkillScript.new(
        "meteor_dive",
        "Meteor Dive",
        4.20,
        1,
        [],
        "attack",
        5,
        []
    )
    meteor_dive.speed_damage_scaling = 0.001

    var skills: Array = [
        rending_talons,
        searing_gale,
        meteor_dive
    ]

    return MonsterScript.new(
        "griffon_igneous",
        "Igneous Griffon",
        "Griffon",
        "igneous",
        4,
        _scaled(8900),
        _scaled(890),
        _scaled(595),
        _scaled(232),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_storm_dryad():
    var vine_barrage = DamageSkillScript.new(
        "vine_barrage",
        "Vine Barrage",
        0.70,
        3,
        [],
        "attack",
        0,
        []
    )

    var breath_of_the_grove = SupportSkillScript.new(
        "breath_of_the_grove",
        "Breath of the Grove",
        5,
        [],
        "all_allies"
    )
    breath_of_the_grove.healing_hp_ratio = 0.25

    var skills: Array = [
        vine_barrage,
        breath_of_the_grove
    ]

    return MonsterScript.new(
        "dryad_storm",
        "Storm Dryad",
        "Dryad",
        "storm",
        3,
        _scaled(11150),
        _scaled(545),
        _scaled(760),
        _scaled(204),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_storm_dullahan():
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

    var gale_pursuit = DamageSkillScript.new(
        "gale_pursuit",
        "Gale Pursuit",
        2.25,
        1,
        [],
        "attack",
        4,
        [],
        {},
        {},
        "all_enemies",
        0.20
    )

    var headlong_charge = SupportSkillScript.new(
        "headlong_charge",
        "Headlong Charge",
        5,
        [],
        "self"
    )

    var skills: Array = [
        severing_blade,
        gale_pursuit,
        headlong_charge
    ]

    return MonsterScript.new(
        "dullahan_storm",
        "Storm Dullahan",
        "Dullahan",
        "storm",
        4,
        _scaled(9800),
        _scaled(700),
        _scaled(650),
        _scaled(236),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_abyssal_dullahan():
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

    var spectral_shackles = DamageSkillScript.new(
        "spectral_shackles",
        "Spectral Shackles",
        1.95,
        2,
        [],
        "attack",
        4,
        [
            {
                "effect_id": "speed_break",
                "chance": 0.50,
                "turns": 2,
                "hit_indices": [0]
            },
            {
                "effect_id": "attack_break",
                "chance": 0.50,
                "turns": 2,
                "hit_indices": [1]
            }
        ]
    )

    var skills: Array = [
        severing_blade,
        spectral_shackles
    ]

    return MonsterScript.new(
        "dullahan_abyssal",
        "Abyssal Dullahan",
        "Dullahan",
        "abyssal",
        4,
        _scaled(10800),
        _scaled(650),
        _scaled(790),
        _scaled(212),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_igneous_dullahan():
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

    var relentless_pursuit = DamageSkillScript.new(
        "relentless_pursuit",
        "Relentless Pursuit",
        1.85,
        2,
        [],
        "attack",
        4,
        []
    )
    relentless_pursuit.max_missing_health_bonus = 0.30

    var death_sentence = DamageSkillScript.new(
        "death_sentence",
        "Death Sentence",
        4.60,
        1,
        [],
        "attack",
        5,
        []
    )
    death_sentence.execute_health_threshold = 0.25
    death_sentence.execute_defense_ignore_ratio = 0.50

    var skills: Array = [
        severing_blade,
        relentless_pursuit,
        death_sentence
    ]

    return MonsterScript.new(
        "dullahan_igneous",
        "Igneous Dullahan",
        "Dullahan",
        "igneous",
        4,
        _scaled(9200),
        _scaled(915),
        _scaled(610),
        _scaled(218),
        skills,
        LEVEL_ONE_MULTIPLIER
    )


static func _create_aether_dullahan():
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

    var soulpiercer = DamageSkillScript.new(
        "soulpiercer",
        "Soulpiercer",
        4.10,
        1,
        [],
        "attack",
        3,
        []
    )
    soulpiercer.damage_per_soul_charge = 0.06
    soulpiercer.max_soul_charges = 5

    var beyond_the_veil = DamageSkillScript.new(
        "beyond_the_veil",
        "Beyond the Veil",
        1.25,
        4,
        [],
        "attack",
        7,
        [],
        {},
        {},
        "all_enemies"
    )
    beyond_the_veil.damage_per_soul_charge = 0.10
    beyond_the_veil.max_soul_charges = 5
    beyond_the_veil.use_consumed_soul_charges = true

    var skills: Array = [
        severing_blade,
        soulpiercer,
        beyond_the_veil
    ]

    var monster = MonsterScript.new(
        "dullahan_aether",
        "Aether Dullahan",
        "Dullahan",
        "aether",
        5,
        _scaled(11200),
        _scaled(900),
        _scaled(720),
        _scaled(222),
        skills,
        LEVEL_ONE_MULTIPLIER
    )

    monster.combat_resources["soul_charges"] = 0
    monster.combat_resource_maximums["soul_charges"] = 5

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
