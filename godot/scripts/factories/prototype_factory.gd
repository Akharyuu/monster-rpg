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

        "scorching_breath_afterburn": {
            "summary": "Engulfs all enemies in a two-hit breath attack and feeds existing flames.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases with the target's [color=#ff7777]Burn[/color] stacks."
                },
                {
                    "kind": "debuff",
                    "text": "If the target is already affected by [color=#ff7777]Burn[/color], applies [b]1 additional Burn stack[/b] for [b]3 turns[/b]."
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

        "flame_devourer_rekindled": {
            "summary": "Consumes the target's flames to empower the strike and restore the caster.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Deals increased damage based on [color=#ff7777]Burn[/color] stacks."
                },
                {
                    "kind": "heal",
                    "text": "Consumes the Burn present before the attack and [color=#76e6a8]heals the caster[/color]."
                },
                {
                    "kind": "special",
                    "text": "Consuming [b]3 Burn stacks[/b] resets [b]Scorching Breath[/b]."
                }
            ]
        },

        "flame_devourer_incineration": {
            "summary": "Consumes the target's flames in a devastating finishing strike.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Deals increased damage based on [color=#ff7777]Burn[/color] stacks."
                },
                {
                    "kind": "damage",
                    "text": "At [b]3 Burn stacks[/b], ignores the target's Defense."
                },
                {
                    "kind": "heal",
                    "text": "Consumes the Burn present before the attack and [color=#76e6a8]heals the caster[/color]."
                },
                {
                    "kind": "special",
                    "text": "Consuming [b]3 Burn stacks[/b] resets [b]Scorching Breath[/b]."
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

        "rime_breath_frigid": {
            "summary": "A freezing breath that strikes the entire enemy team twice.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Each hit reduces [b]10% Action Gauge[/b] if the target is affected by [color=#ff7777]Speed Break[/color]."
                },
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

        "glacial_collapse_absolute_zero": {
            "summary": "Crushes the enemy team under an absolute glacial collapse.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Reduces each target's [b]Action Gauge by 10%[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "Targets with [color=#ff7777]Speed Break[/color] are [color=#ff7777]Frozen[/color] for [b]1 turn[/b], ignoring Resistance."
                },
                {
                    "kind": "debuff",
                    "text": "Other targets have a [b]75% chance[/b] to be [color=#ff7777]Frozen[/color] for [b]1 turn[/b], ignoring Resistance."
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

        "lightning_rush_blitz": {
            "summary": "Rushes one enemy with two rapid lightning-infused strikes.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "After attacking, grants the caster [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "After attacking, gains [b]15% Action Gauge[/b]."
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

        "stormbreak_requiem": {
            "summary": "Unleashes ten lightning strikes across random enemies, followed by a final sweeping discharge.",
            "effects": [
                {
                    "kind": "control",
                    "text": "A target hit [b]3+ times[/b] has a [b]50% chance[/b] to be [color=#ff7777]Stunned[/color] for [b]1 turn[/b]."
                },
                {
                    "kind": "damage",
                    "text": "After the ten strikes, unleashes an additional attack against all living enemies."
                }
            ]
        },

        "sovereign_breath": {
            "summary": "Blasts all enemies with sovereign aether.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Applies [color=#ff7777]Silence[/color] for [b]1 turn[/b]."
                },
                {
                    "kind": "special",
                    "text": "Silence chance starts at [b]30%[/b] and gains [b]+10% per caster buff[/b], up to [b]80%[/b]."
                }
            ]
        },

        "sovereign_breath_subjugation": {
            "summary": "Overwhelms the enemy team with sovereign aether, suppressing their ability to act.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]50% chance[/b] to apply [color=#ff7777]Silence[/color] for [b]1 turn[/b] ([b]+10% chance[/b] for each buff on the caster)."
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

        "heavens_decree_apotheosis": {
            "summary": "Elevates the entire allied team under overwhelming celestial authority.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "Grants [color=#70c8ff]Attack Up[/color], [color=#70c8ff]Immunity[/color] and [color=#70c8ff]Veil[/color] for [b]3 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "Grants the caster an [b]extra turn[/b]."
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

        "null_rend_obliterate": {
            "summary": "Tears into one enemy with two increasingly destructive void strikes.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "The second hit has an [b]80% chance[/b] to apply [color=#ff7777]Oblivion[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "null_rend_annihilation": {
            "summary": "Tears into one enemy with two void strikes that can erase the fallen from battle.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "The second hit has an [b]80% chance[/b] to apply [color=#ff7777]Oblivion[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "If this skill defeats a target that was already affected by [color=#ff7777]Oblivion[/color], the target becomes [color=#d9a6ff]Banished[/color]."
                },
                {
                    "kind": "special",
                    "text": "A [color=#d9a6ff]Banished[/color] monster cannot be revived."
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
                    "text": "[b]Hits 2-3:[/b] deal increased damage for every buff removed."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hits 2-3:[/b] each has a [b]30% chance[/b] to apply [color=#ff7777]Defense Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "dismantle_decimation": {
            "summary": "Disassembles the enemy team's defenses over three sweeping hits.",
            "effects": [
                {
                    "kind": "special",
                    "text": "[b]Hit 1:[/b] strips enemy buffs."
                },
                {
                    "kind": "damage",
                    "text": "[b]Hits 2-3:[/b] deal increased damage for every buff removed."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hits 2-3:[/b] each has a [b]50% chance[/b] to apply [color=#ff7777]Defense Break[/color] for [b]2 turns[/b]."
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
                    "text": "Applies [color=#ff7777]Stun[/color] for [b]1 turn[/b] if the target has less than [b]50% Action Gauge[/b] ([b]70%[/b] if the caster has [color=#70c8ff]Speed Up[/color])."
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

        "gale_pursuit_crosswind": {
            "summary": "Sweeps through the enemy team with a disruptive crosswind.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Reduces each enemy's [b]Action Gauge by 25%[/b] ([b]35%[/b] if they have more than [b]50% Action Gauge[/b])."
                }
            ]
        },

        "gale_pursuit_tempest": {
            "summary": "Sweeps through the enemy team and drives the allied team forward.",
            "effects": [
                {
                    "kind": "control",
                    "text": "Reduces each enemy's [b]Action Gauge by 25%[/b] ([b]35%[/b] if they have more than [b]50% Action Gauge[/b])."
                },
                {
                    "kind": "buff",
                    "text": "Grants all allies [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
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

        "headlong_charge_rally": {
            "summary": "Rallies the Dullahan and the ally furthest from taking a turn.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "Grants the caster and the selected ally [color=#70c8ff]Attack Up[/color] and [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "Increases that ally's [b]Action Gauge by 30%[/b]."
                }
            ]
        },

        "headlong_charge_stampede": {
            "summary": "Launches a coordinated charge that immediately brings an ally into action.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "Grants the caster and the selected ally [color=#70c8ff]Attack Up[/color] and [color=#70c8ff]Speed Up[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "special",
                    "text": "Increases that ally's [b]Action Gauge by 30%[/b] and makes them take the next turn."
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

        "spectral_shackles_binding": {
            "summary": "Binds one enemy more tightly with two spectral strikes.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]Hit 1:[/b] 70% chance to apply [color=#ff7777]Speed Break[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hit 2:[/b] 70% chance to apply [color=#ff7777]Attack Break[/color] for [b]2 turns[/b]."
                }
            ]
        },

        "spectral_shackles_lockdown": {
            "summary": "Locks one enemy down with two spectral strikes.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "[b]Hit 1:[/b] 90% chance to apply [color=#ff7777]Speed Break[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "[b]Hit 2:[/b] 90% chance to apply [color=#ff7777]Attack Break[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "control",
                    "text": "If both debuffs are applied, reduces the target's [b]Action Gauge by 20%[/b]."
                }
            ]
        },

        "inescapable_fate": {
            "summary": "Condemns one enemy to an inescapable fate.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": "Extends all extendable debuffs on the target by [b]1 turn[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "If the target has at least [b]3 debuffs[/b], applies [color=#ff7777]Silence[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "inescapable_fate_ironbound": {
            "summary": "Condemns one enemy with a strike strengthened by the Dullahan's Defense.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage also scales with the caster's Defense."
                },
                {
                    "kind": "debuff",
                    "text": "Extends all extendable debuffs on the target by [b]1 turn[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "If the target has at least [b]3 debuffs[/b], applies [color=#ff7777]Silence[/color] for [b]1 turn[/b]."
                }
            ]
        },

        "relentless_pursuit": {
            "summary": "Relentlessly hunts down a wounded enemy with two strikes.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases as the target loses Health."
                }
            ]
        },

        "relentless_pursuit_blood_trail": {
            "summary": "Relentlessly hunts down a wounded enemy with two increasingly dangerous strikes.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases as the target loses Health."
                },
                {
                    "kind": "special",
                    "text": "Each hit against a target below [b]50% HP[/b] grants [b]20% Action Gauge[/b]."
                }
            ]
        },

        "death_sentence": {
            "summary": "Delivers a lethal single-target strike.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Partially ignores Defense if the target is below [b]25% HP[/b]."
                }
            ]
        },

        "death_sentence_execution": {
            "summary": "Delivers a lethal strike designed to execute weakened enemies.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Partially ignores Defense if the target is below [b]33% HP[/b]."
                }
            ]
        },

        "death_sentence_massacre": {
            "summary": "Executes a weakened enemy and immediately continues the hunt.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Partially ignores Defense if the target is below [b]33% HP[/b]."
                },
                {
                    "kind": "special",
                    "text": "If this skill defeats an enemy, immediately uses [b]Relentless Pursuit[/b] against the living enemy with the lowest HP ratio."
                }
            ]
        },

        "soulpiercer": {
            "summary": "Pierces one enemy with condensed soul energy.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases with each [color=#d9a6ff]Soul Charge[/color], up to [b]5[/b]."
                }
            ]
        },

        "soulpiercer_ascension": {
            "summary": "Pierces one enemy with concentrated soul energy.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases more strongly with each [color=#d9a6ff]Soul Charge[/color], up to [b]5[/b]."
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
                    "text": "Damage increases with each consumed Soul Charge."
                }
            ]
        },

        "beyond_the_veil_soul_recall": {
            "summary": "Releases stored souls in a four-hit attack against all enemies.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Consumes all [color=#d9a6ff]Soul Charges[/color] before attacking."
                },
                {
                    "kind": "damage",
                    "text": "Damage increases with each consumed Soul Charge."
                }
            ]
        },

        "beyond_the_veil_convergence": {
            "summary": "Releases a convergence of stored souls in a four-hit attack against all enemies.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Consumes all [color=#d9a6ff]Soul Charges[/color] before attacking."
                },
                {
                    "kind": "damage",
                    "text": "Damage increases with each consumed Soul Charge."
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
                    "text": "Damage increases for every monster that has died in battle."
                }
            ]
        },

        "spinal_scourge_ossuary": {
            "summary": "Sweeps through all enemies with three strikes empowered by the dead.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases for every monster defeated in the battle."
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
                }
            ]
        },

        "deaths_gaze_last_name": {
            "summary": "Names one enemy for death before delivering a devastating strike.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Applies [color=#d9a6ff]Named[/color] for [b]2 turns[/b]."
                },
                {
                    "kind": "debuff",
                    "text": "Applies [color=#ff7777]Vulnerability[/color] for [b]3 turns[/b]."
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
            "summary": "Turns enemy aggression into control over the flow of battle.",
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
                    "text": "[color=#ff7777]Stun[/color] and [color=#ff7777]Freeze[/color] cannot be extended."
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
                    "text": "While [color=#d9a6ff]Headless[/color], cannot be Silenced unless affected by [color=#ff7777]Oblivion[/color]."
                }
            ]
        }
    }

    monster.passive_tooltip = passive_data.get(
        monster.monster_id,
        {}
    )

    if monster.monster_id == "dullahan_aether":
        var soul_vessel_data: Dictionary = {
            "name": (
                "Soul Vessel: Requiem"
                if monster.resonance >= 4
                else (
                    "Soul Vessel: Last Rites"
                    if monster.resonance >= 1
                    else "Soul Vessel"
                )
            ),
            "summary": "Collects Soul Charges and converts them into offensive or restorative power.",
            "effects": [
                {
                    "kind": "special",
                    "text": "Gains [b]1 Soul Charge[/b] after using a damage skill, up to [b]5[/b]."
                },
                {
                    "kind": "special",
                    "text": (
                        "Gains [b]2 Soul Charges[/b] whenever any monster dies."
                        if monster.resonance >= 4
                        else "Gains [b]1 Soul Charge[/b] whenever any monster dies."
                    )
                },
                {
                    "kind": "special",
                    "text": "[b]Beyond the Veil[/b] consumes all stored Soul Charges to increase its damage."
                }
            ]
        }

        if monster.resonance >= 1:
            soul_vessel_data["effects"].append(
                {
                    "kind": "special",
                    "text": "[b]Severing Blade[/b] grants [b]1 additional Soul Charge[/b] when used against a target below [b]50% HP[/b]."
                }
            )

        if monster.resonance >= 2:
            soul_vessel_data["effects"].append(
                {
                    "kind": "special",
                    "text": "At [b]5 Soul Charges[/b], [color=#d9a6ff]Soul Recall[/color] becomes available as an active action."
                }
            )

        monster.passive_tooltip = soul_vessel_data
        monster.passive_tooltips = [
            soul_vessel_data
        ]

    if monster.monster_id == "dullahan_void":
        var headless_data: Dictionary = {
            "name": (
                "Deathless Rider"
                if monster.resonance >= 4
                else (
                    "Headless Rider: Unbound"
                    if monster.resonance >= 1
                    else "Headless Rider"
                )
            ),
            "summary": (
                "Defies lethal blows while hunting a Named foe."
                if monster.resonance >= 4
                else "Empowers the Dullahan while it has a Named target."
            ),
            "effects": [
                {
                    "kind": "special",
                    "text": (
                        "While [color=#d9a6ff]Headless[/color], gains [b]+30% Speed[/b]."
                        if monster.resonance >= 1
                        else "While [color=#d9a6ff]Headless[/color], gains [b]+20% Speed[/b]."
                    )
                },
                {
                    "kind": "special",
                    "text": "While [color=#d9a6ff]Headless[/color], cannot be Silenced unless affected by [color=#ff7777]Oblivion[/color]."
                }
            ]
        }

        if monster.resonance >= 4:
            headless_data["effects"].append(
                {
                    "kind": "special",
                    "text": "While [color=#d9a6ff]Headless[/color], survives lethal damage with [b]1 HP[/b]. After the attack, cleanses all debuffs and loses [color=#d9a6ff]Headless[/color]. [b]6-turn cooldown[/b]."
                }
            )

        if monster.resonance >= 4:
            headless_data["internal_cooldown_id"] = (
                "deathless_rider"
            )

        monster.passive_tooltip = headless_data
        monster.passive_tooltips = [
            headless_data
        ]

        if monster.resonance >= 5:
            monster.passive_tooltips.append(
                {
                    "name": "Death's Gaze: Death March",
                    "summary": "Carries the death sentence forward when a Named enemy falls.",
                    "effects": [
                        {
                            "kind": "special",
                            "text": "When the [color=#d9a6ff]Named[/color] target dies, the living enemy with the lowest HP ratio becomes [color=#d9a6ff]Named[/color] for [b]2 turns[/b]."
                        },
                        {
                            "kind": "debuff",
                            "text": "Applies [color=#ff7777]Vulnerability[/color] to the new target for [b]3 turns[/b]."
                        }
                    ]
                }
            )

    if monster.monster_id == "dullahan_abyssal":
        if monster.resonance >= 3:
            monster.passive_tooltip = {
                "name": "Chilling Presence: Suffocation",
                "summary": "Deepens the enemy team's existing debuffs after every turn.",
                "effects": [
                    {
                        "kind": "special",
                        "text": "After this monster's turn, extends up to [b]2 random extendable debuffs[/b] on each living enemy by [b]1 turn[/b]."
                    },
                    {
                        "kind": "special",
                        "text": "[color=#ff7777]Stun[/color] and [color=#ff7777]Freeze[/color] cannot be extended."
                    }
                ]
            }

    if (
        monster.monster_id == "dullahan_storm"
        and monster.resonance >= 2
    ):
        monster.passive_tooltip = {
            "name": "The Hunt",
            "summary": "Steals momentum from the enemy closest to taking a turn.",
            "effects": [
                {
                    "kind": "special",
                    "text": "After this monster's turn, steals up to [b]20% Action Gauge[/b] from the living enemy with the highest Action Gauge."
                }
            ]
        }

    if monster.monster_id == "drake_void":
        var bottomless_data: Dictionary = passive_data.get(
            "drake_void",
            {}
        )

        monster.passive_tooltips = []
        if not bottomless_data.is_empty():
            monster.passive_tooltips.append(
                bottomless_data
            )
            monster.passive_tooltip = bottomless_data

        if monster.resonance >= 2:
            var voidborn_data: Dictionary = {
                "name": (
                    "Voidborn: Transcendence"
                    if monster.resonance >= 3
                    else "Voidborn"
                ),
                "summary": "Feeds on stripped power until the Void Drake erupts into a protected state.",
                "effects": [
                    {
                        "kind": "special",
                        "text": "Each enemy buff removed grants [b]1 Voidborn stack[/b], up to [b]5[/b]."
                    },
                    {
                        "kind": "buff",
                        "text": (
                            "At [b]5 Voidborn stacks[/b], consumes all stacks to cleanse all debuffs and grant [color=#70c8ff]Invincibility[/color] for [b]2 turns[/b]."
                            if monster.resonance >= 3
                            else "At [b]5 Voidborn stacks[/b], consumes all stacks and grants [color=#70c8ff]Invincibility[/color] for [b]2 turns[/b]."
                        )
                    }
                ]
            }

            monster.passive_tooltips.append(
                voidborn_data
            )

    if (
        monster.monster_id == "dullahan_igneous"
        and monster.resonance >= 2
    ):
        monster.passive_tooltip = {
            "name": (
                "Final Omen: Fulfilled"
                if monster.resonance >= 4
                else "Final Omen"
            ),
            "summary": "Preys on wounded enemies that try to recover.",
            "effects": [
                {
                    "kind": "buff",
                    "text": "When an enemy below [b]50% HP[/b] is healed, gains [color=#70c8ff]Attack Up[/color] for [b]1 turn[/b]."
                }
            ]
        }

        if monster.resonance >= 4:
            monster.passive_tooltip["effects"].append(
                {
                    "kind": "special",
                    "text": "Enemies below [b]50% HP[/b] receive reduced healing."
                }
            )

    if monster.monster_id == "drake_storm":
        var thunderheart_data: Dictionary = {
            "name": (
                "Thunderheart: Overclocked"
                if monster.resonance >= 3
                else "Thunderheart"
            ),
            "summary": "Converts bonus Speed into offensive power.",
            "effects": [
                {
                    "kind": "damage",
                    "text": "Damage increases according to the monster's bonus Speed."
                }
            ]
        }

        if monster.resonance >= 3:
            thunderheart_data["effects"].append(
                {
                    "kind": "special",
                    "text": "Bonus Speed also increases Crit Rate."
                }
            )

        monster.passive_tooltips = [
            thunderheart_data
        ]
        monster.passive_tooltip = thunderheart_data

        if monster.resonance >= 1:
            var short_circuit_data: Dictionary = {
                "name": (
                    "Short Circuit: Chain Reaction"
                    if monster.resonance >= 4
                    else "Short Circuit"
                ),
                "summary": "Turns Speed Up into a chance to disrupt enemies.",
                "effects": [
                    {
                        "kind": "debuff",
                        "text": "While affected by [color=#70c8ff]Speed Up[/color], S1 and S2 hits have a [b]10% chance[/b] to apply [color=#ff7777]Stun[/color] for [b]1 turn[/b]."
                    }
                ]
            }

            if monster.resonance >= 4:
                short_circuit_data["effects"].append(
                    {
                        "kind": "special",
                        "text": "Successfully applying Stun reduces [b]Stormbreak[/b]'s cooldown by [b]1 turn[/b]."
                    }
                )

            monster.passive_tooltips.append(
                short_circuit_data
            )

    if monster.monster_id == "drake_aether":
        var authority_data: Dictionary = {
            "name": (
                "Celestial Authority: Ascendance"
                if monster.resonance >= 2
                else "Celestial Authority"
            ),
            "summary": "Punishes enemies that strike the Aether Drake.",
            "effects": [
                {
                    "kind": "debuff",
                    "text": (
                        "When hit, has a [b]50% chance[/b] to apply [color=#ff7777]Attack Break[/color] to the attacker for [b]2 turns[/b]."
                        if monster.resonance >= 2
                        else "When hit, has a [b]30% chance[/b] to apply [color=#ff7777]Attack Break[/color] to the attacker for [b]2 turns[/b]."
                    )
                }
            ]
        }

        if monster.resonance >= 2:
            authority_data["effects"].append(
                {
                    "kind": "special",
                    "text": "On success, grants [b]20% Action Gauge[/b] to the living ally with the most buffs."
                }
            )

        monster.passive_tooltips = [
            authority_data
        ]
        monster.passive_tooltip = authority_data

        if monster.resonance >= 1:
            var divine_grace_data: Dictionary = {
                "name": (
                    "Divine Grace: Enlightenment"
                    if monster.resonance >= 4
                    else "Divine Grace"
                ),
                "summary": "Blesses allies whenever this monster grants them buffs.",
                "effects": [
                    {
                        "kind": "heal",
                        "text": "Each buff applied by this monster heals the target for [b]5% Max HP[/b]."
                    }
                ]
            }

            if monster.resonance >= 4:
                divine_grace_data["effects"].append(
                    {
                        "kind": "special",
                        "text": "Also grants the caster [b]+25% Accuracy[/b]."
                    }
                )

            monster.passive_tooltips.append(
                divine_grace_data
            )

    if monster.monster_id == "drake_igneous":
        if monster.resonance >= 4:
            monster.passive_tooltip = {
                "name": "Cinderblood: Molten Core",
                "summary": "Ignites enemies more aggressively and feeds the Drake's momentum.",
                "effects": [
                    {
                        "kind": "debuff",
                        "text": "Each landed hit has a [b]65% chance[/b] to apply [color=#ff7777]Burn[/color] for [b]2 turns[/b]."
                    },
                    {
                        "kind": "special",
                        "text": "The first Burn applied by each skill grants [b]10% Action Gauge[/b]."
                    }
                ]
            }
        elif monster.resonance >= 1:
            monster.passive_tooltip = {
                "name": "Cinderblood: Ignite",
                "summary": "Each landed hit can ignite the target.",
                "effects": [
                    {
                        "kind": "debuff",
                        "text": "Each landed hit has a [b]50% chance[/b] to apply [color=#ff7777]Burn[/color] for [b]2 turns[/b]."
                    }
                ]
            }

    if monster.monster_id == "drake_abyssal":
        var frozen_scales_data: Dictionary = {
            "name": (
                "Frozen Scales: Everfrost"
                if monster.resonance >= 3
                else "Frozen Scales"
            ),
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
        }

        if monster.resonance >= 3:
            frozen_scales_data["effects"].append(
                {
                    "kind": "special",
                    "text": "Reaching [b]3 Frozen Scales[/b] resets [b]Glacial Collapse[/b]."
                }
            )

        monster.passive_tooltips = [
            frozen_scales_data
        ]
        monster.passive_tooltip = frozen_scales_data

        if monster.resonance >= 2:
            var frostborne_data: Dictionary = {
                "name": (
                    "Frostborne: Everlasting Winter"
                    if monster.resonance >= 4
                    else "Frostborne"
                ),
                "summary": "Prevents the Drake's frozen targets from being freed by damage.",
                "effects": [
                    {
                        "kind": "special",
                        "text": (
                            "[color=#ff7777]Freeze[/color] applied by this monster cannot be broken by any source of damage."
                            if monster.resonance >= 4
                            else "Damage dealt by this monster does not break [color=#ff7777]Freeze[/color]."
                        )
                    }
                ]
            }

            monster.passive_tooltips.append(
                frostborne_data
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


    if (
        monster.passive_tooltips.is_empty()
        and not monster.passive_tooltip.is_empty()
    ):
        monster.passive_tooltips = [
            monster.passive_tooltip
        ]


static func _scaled(value: float) -> int:
    return int(round(value * LEVEL_ONE_MULTIPLIER))


static func _apply_resonance(monster) -> void:
    if monster.monster_id == "dullahan_aether":
        if monster.resonance >= 2:
            var soul_recall = DamageSkillScript.new(
                (
                    "beyond_the_veil_convergence"
                    if monster.resonance >= 5
                    else "beyond_the_veil_soul_recall"
                ),
                (
                    "Beyond the Veil: Convergence"
                    if monster.resonance >= 5
                    else "Beyond the Veil: Soul Recall"
                ),
                1.25,
                4,
                [],
                "attack",
                6,
                [],
                {},
                {},
                "all_enemies"
            )
            soul_recall.damage_per_soul_charge = 0.10
            soul_recall.max_soul_charges = 5
            soul_recall.use_consumed_soul_charges = true
            monster.skills[2] = soul_recall

        if monster.resonance >= 3:
            var ascension = DamageSkillScript.new(
                "soulpiercer_ascension",
                "Soulpiercer: Ascension",
                4.10,
                1,
                [],
                "attack",
                3,
                []
            )
            ascension.damage_per_soul_charge = 0.08
            ascension.max_soul_charges = 5
            monster.skills[1] = ascension

        return

    if monster.monster_id == "dullahan_void":
        if monster.resonance >= 2:
            var ossuary = DamageSkillScript.new(
                "spinal_scourge_ossuary",
                "Spinal Scourge: Ossuary",
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
            ossuary.damage_per_dead_monster = 0.08
            ossuary.max_dead_monsters = 5
            ossuary.max_dead_monster_bonus = 0.40
            monster.skills[1] = ossuary

        if monster.resonance >= 3:
            var last_name = DamageSkillScript.new(
                "deaths_gaze_last_name",
                "Death's Gaze: Last Name",
                4.70,
                1,
                [],
                "attack",
                5,
                []
            )
            last_name.apply_named_before_hit = true
            last_name.named_turns = 2
            last_name.vulnerability_chance = 1.00
            last_name.vulnerability_turns = 3
            monster.skills[2] = last_name

        return

    if monster.monster_id == "dullahan_abyssal":
        if monster.resonance >= 1:
            var shackles = DamageSkillScript.new(
                (
                    "spectral_shackles_lockdown"
                    if monster.resonance >= 4
                    else "spectral_shackles_binding"
                ),
                (
                    "Spectral Shackles: Lockdown"
                    if monster.resonance >= 4
                    else "Spectral Shackles: Binding"
                ),
                1.95,
                2,
                [],
                "attack",
                4,
                [
                    {
                        "effect_id": "speed_break",
                        "chance": (
                            0.90
                            if monster.resonance >= 4
                            else 0.70
                        ),
                        "turns": 2,
                        "hit_indices": [0]
                    },
                    {
                        "effect_id": "attack_break",
                        "chance": (
                            0.90
                            if monster.resonance >= 4
                            else 0.70
                        ),
                        "turns": 2,
                        "hit_indices": [1]
                    }
                ]
            )
            monster.skills[1] = shackles

        if monster.resonance >= 2:
            var fate = DamageSkillScript.new(
                (
                    "inescapable_fate_ironbound"
                    if monster.resonance >= 5
                    else "inescapable_fate"
                ),
                (
                    "Inescapable Fate: Ironbound"
                    if monster.resonance >= 5
                    else "Inescapable Fate"
                ),
                3.00,
                1,
                [],
                "attack",
                (
                    4
                    if monster.resonance >= 5
                    else 5
                ),
                []
            )

            if monster.resonance >= 5:
                fate.bonus_stat = "defense"
                fate.bonus_stat_scaling = 1.20

            monster.skills.append(fate)

        return

    if monster.monster_id == "dullahan_storm":
        if monster.resonance >= 1:
            var pursuit = DamageSkillScript.new(
                (
                    "gale_pursuit_tempest"
                    if monster.resonance >= 4
                    else "gale_pursuit_crosswind"
                ),
                (
                    "Gale Pursuit: Tempest"
                    if monster.resonance >= 4
                    else "Gale Pursuit: Crosswind"
                ),
                2.25,
                1,
                [],
                "attack",
                4,
                [],
                {},
                {},
                "all_enemies",
                0.25
            )
            pursuit.action_gauge_threshold = 0.50
            pursuit.action_gauge_bonus_reduction = 0.10
            monster.skills[1] = pursuit

        if monster.resonance >= 3:
            var charge = SupportSkillScript.new(
                (
                    "headlong_charge_stampede"
                    if monster.resonance >= 5
                    else "headlong_charge_rally"
                ),
                (
                    "Headlong Charge: Stampede"
                    if monster.resonance >= 5
                    else "Headlong Charge: Rally"
                ),
                5,
                [],
                "self"
            )
            monster.skills[2] = charge

        return

    if monster.monster_id == "drake_void":
        if monster.resonance >= 1:
            var obliterate = DamageSkillScript.new(
                (
                    "null_rend_annihilation"
                    if monster.resonance >= 5
                    else "null_rend_obliterate"
                ),
                (
                    "Null Rend: Annihilation"
                    if monster.resonance >= 5
                    else "Null Rend: Obliterate"
                ),
                2.10,
                2,
                [1.00, 1.30],
                "attack",
                4,
                [
                    {
                        "effect_id": "oblivion",
                        "chance": 0.80,
                        "turns": 2,
                        "hit_indices": [1]
                    }
                ]
            )
            monster.skills[1] = obliterate

        if monster.resonance >= 2:
            monster.combat_resources["voidborn"] = 0
            monster.combat_resource_maximums["voidborn"] = 5

        if monster.resonance >= 4:
            var decimation = DamageSkillScript.new(
                "dismantle_decimation",
                "Dismantle: Decimation",
                1.45,
                3,
                [],
                "attack",
                4,
                [
                    {
                        "effect_id": "defense_break",
                        "chance": 0.50,
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
            monster.skills[2] = decimation

        return

    if monster.monster_id == "dullahan_igneous":
        if monster.resonance >= 1:
            var blood_trail = DamageSkillScript.new(
                "relentless_pursuit_blood_trail",
                "Relentless Pursuit: Blood Trail",
                1.85,
                2,
                [],
                "attack",
                4,
                []
            )
            blood_trail.max_missing_health_bonus = 0.45
            blood_trail.action_gauge_gain_if_target_low_hp_threshold = 0.50
            blood_trail.action_gauge_gain_if_target_low_hp_amount = 0.20
            monster.skills[1] = blood_trail

        if monster.resonance >= 3:
            var execution = DamageSkillScript.new(
                (
                    "death_sentence_massacre"
                    if monster.resonance >= 5
                    else "death_sentence_execution"
                ),
                (
                    "Death Sentence: Massacre"
                    if monster.resonance >= 5
                    else "Death Sentence: Execution"
                ),
                4.60,
                1,
                [],
                "attack",
                4,
                []
            )
            execution.execute_health_threshold = 0.33
            execution.execute_defense_ignore_ratio = 0.50
            monster.skills[2] = execution

        return

    if monster.monster_id == "drake_storm":
        if monster.resonance >= 2:
            var blitz = DamageSkillScript.new(
                "lightning_rush_blitz",
                "Lightning Rush: Blitz",
                1.75,
                2,
                [],
                "attack",
                3,
                []
            )
            monster.skills[1] = blitz

        if monster.resonance >= 5:
            var requiem = DamageSkillScript.new(
                "stormbreak_requiem",
                "Stormbreak: Requiem",
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
            monster.skills[2] = requiem

        return

    if monster.monster_id == "drake_aether":
        if monster.resonance >= 3:
            var subjugation = DamageSkillScript.new(
                "sovereign_breath_subjugation",
                "Sovereign Breath: Subjugation",
                3.00,
                1,
                [],
                "attack",
                3,
                [],
                {},
                {},
                "all_enemies"
            )
            monster.skills[1] = subjugation

        if monster.resonance >= 5:
            var apotheosis = SupportSkillScript.new(
                "heavens_decree_apotheosis",
                "Heaven's Decree: Apotheosis",
                6,
                [
                    {
                        "effect_id": "attack_up",
                        "turns": 3
                    },
                    {
                        "effect_id": "immunity",
                        "turns": 3
                    },
                    {
                        "effect_id": "veil",
                        "turns": 3
                    }
                ],
                "all_allies"
            )
            monster.skills[2] = apotheosis

        return

    if monster.monster_id == "drake_igneous":
        if monster.resonance >= 1:
            monster.on_hit_effects = [
                {
                    "effect_id": "burn",
                    "chance": (
                        0.65
                        if monster.resonance >= 4
                        else 0.50
                    ),
                    "turns": 2,
                    "stacks": 1,
                    "action_gauge": (
                        0.10
                        if monster.resonance >= 4
                        else 0.0
                    ),
                    "action_gauge_once_per_skill": (
                        monster.resonance >= 4
                    )
                }
            ]

        if monster.resonance >= 2:
            var afterburn = DamageSkillScript.new(
                "scorching_breath_afterburn",
                "Scorching Breath: Afterburn",
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
            )
            afterburn.add_burn_if_started_with_burn = true
            afterburn.extra_burn_stacks = 1
            afterburn.extra_burn_turns = 3
            monster.skills[1] = afterburn

        if monster.resonance >= 3:
            var rekindled = DamageSkillScript.new(
                "flame_devourer_rekindled",
                "Flame Devourer: Rekindled",
                4.60,
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
            rekindled.reset_skill_slot_if_burn_stacks = 2
            rekindled.reset_skill_required_burn_stacks = 3
            monster.skills[2] = rekindled

        if monster.resonance >= 5:
            var incineration = DamageSkillScript.new(
                "flame_devourer_incineration",
                "Flame Devourer: Incineration",
                4.60,
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
                    },
                    "ignore_defense_at_stacks": 3
                },
                {
                    "heal_by_stacks": {
                        1: 0.12,
                        2: 0.25,
                        3: 0.40
                    }
                }
            )
            incineration.reset_skill_slot_if_burn_stacks = 2
            incineration.reset_skill_required_burn_stacks = 3
            monster.skills[2] = incineration

        return

    if monster.monster_id == "drake_abyssal":
        if monster.resonance >= 1:
            var frigid = DamageSkillScript.new(
                "rime_breath_frigid",
                "Rime Breath: Frigid",
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
            )
            frigid.action_gauge_reduction_if_debuff_id = (
                "speed_break"
            )
            frigid.action_gauge_reduction_if_debuff_amount = 0.10
            monster.skills[1] = frigid

        if monster.resonance >= 5:
            var absolute_zero = DamageSkillScript.new(
                "glacial_collapse_absolute_zero",
                "Glacial Collapse: Absolute Zero",
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
                        "ignore_resistance": true,
                        "condition": {
                            "type": "target_has_debuff",
                            "effect_id": "speed_break"
                        }
                    },
                    {
                        "effect_id": "freeze",
                        "chance": 0.75,
                        "turns": 1,
                        "trigger": "per_hit",
                        "ignore_resistance": true,
                        "condition": {
                            "type": "target_lacks_debuff",
                            "effect_id": "speed_break"
                        }
                    }
                ],
                {},
                {},
                "all_enemies",
                0.10
            )
            monster.skills[2] = absolute_zero

        return

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
