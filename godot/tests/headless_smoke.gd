extends SceneTree

# This is a real runtime smoke test, not a text-only GDScript assertion.
# It is run by: godot --headless --path godot --script res://tests/headless_smoke.gd
const Factory = preload("res://scripts/factories/prototype_factory.gd")
const Battle = preload("res://scripts/battle/battle_controller.gd")

const MONSTER_IDS = [
    "drake_igneous", "drake_abyssal", "drake_storm",
    "drake_aether", "drake_void",
    "dullahan_igneous", "dullahan_abyssal", "dullahan_storm",
    "dullahan_aether", "dullahan_void",
    "griffon_igneous", "dryad_storm",
    "slime_igneous", "slime_abyssal", "slime_storm",
    "sprout_igneous", "sprout_abyssal", "sprout_storm",
    "wisp_igneous", "wisp_abyssal", "wisp_storm",
    "thornet_igneous", "thornet_abyssal", "thornet_storm"
]


func _initialize() -> void:
    call_deferred("_run_smoke")


func _run_smoke() -> void:
    var monster_doc: Variant = JSON.parse_string(
        FileAccess.get_file_as_string("res://data/monster_data.json")
    )
    var resonance_doc: Variant = JSON.parse_string(
        FileAccess.get_file_as_string("res://data/resonance_data.json")
    )
    if not (monster_doc is Dictionary) or not (resonance_doc is Dictionary):
        push_error("HEADLESS SMOKE: invalid shared JSON")
        quit(1)
        return

    var roster: Dictionary = monster_doc.get("monsters", {})
    var resonances: Dictionary = resonance_doc.get("resonances", {})
    var failures: Array[String] = []
    var built: int = 0

    for monster_id in MONSTER_IDS:
        if not roster.has(monster_id):
            failures.append("Missing monster ID: %s" % monster_id)
            continue

        var base: Dictionary = roster[monster_id]
        var levels: Dictionary = resonances.get(monster_id, {})
        var max_rank: int = 5 if resonances.has(monster_id) else 0

        for rank in range(max_rank + 1):
            var monster = Factory.create_level_one_monster(
                monster_id, rank
            )
            if monster == null:
                failures.append("%s R%d: factory returned null" % [
                    monster_id, rank
                ])
                continue

            built += 1
            var expected_skills: Array = base.get(
                "skills", []
            ).duplicate()
            var expected_passives: Array = base.get(
                "passives", []
            ).duplicate()

            for level in range(1, rank + 1):
                for action in levels.get(str(level), []):
                    match str(action.get("action", "")):
                        "replace_skill":
                            var slot: int = int(action["slot"]) - 1
                            if slot < 0 or slot >= expected_skills.size():
                                failures.append(
                                    "%s R%d: bad skill slot %d" % [
                                        monster_id, rank, slot + 1
                                    ]
                                )
                                continue
                            expected_skills[slot] = action["new"]
                        "add_skill":
                            expected_skills.append(action["skill"])
                        "add_passive":
                            expected_passives.append(action["passive"])
                        "replace_passive":
                            var index: int = expected_passives.find(
                                action["old"]
                            )
                            if index < 0:
                                failures.append(
                                    "%s R%d: bad passive replacement" % [
                                        monster_id, rank
                                    ]
                                )
                                continue
                            expected_passives[index] = action["new"]
                        _:
                            failures.append(
                                "%s R%d: unknown Resonance action" % [
                                    monster_id, rank
                                ]
                            )

            if monster.resonance != rank:
                failures.append(
                    "%s R%d: incorrect Resonance" % [monster_id, rank]
                )

            if monster.skills.size() != expected_skills.size():
                failures.append(
                    "%s R%d: skill count mismatch" % [monster_id, rank]
                )
            else:
                for slot in range(expected_skills.size()):
                    var skill = monster.skills[slot]
                    if skill == null:
                        failures.append(
                            "%s R%d: null skill at slot %d" % [
                                monster_id, rank, slot + 1
                            ]
                        )
                        continue
                    if str(skill.skill_id) != str(expected_skills[slot]):
                        failures.append(
                            "%s R%d: incorrect skill at slot %d" % [
                                monster_id, rank, slot + 1
                            ]
                        )
                    if str(skill.tooltip_summary).is_empty():
                        failures.append(
                            "%s R%d: missing skill tooltip" % [
                                monster_id, rank
                            ]
                        )

            # Visual button order is stable even when an R-level
            # replaces the first passive and adds a second one.
            if monster.passive_ids != expected_passives:
                failures.append(
                    "%s R%d: passive order mismatch" % [monster_id, rank]
                )
            if monster.passive_tooltips.size() != expected_passives.size():
                failures.append(
                    "%s R%d: passive tooltip count mismatch"
                    % [monster_id, rank]
                )
            else:
                for slot in range(expected_passives.size()):
                    var tooltip: Dictionary = monster.passive_tooltips[slot]
                    var id: String = str(expected_passives[slot])
                    var definition: Dictionary = monster.passive_definitions.get(
                        id, {}
                    )
                    var expected_name: String = str(definition.get("name", ""))
                    if str(tooltip.get("name", "")) != expected_name:
                        failures.append(
                            "%s R%d: passive tooltip name mismatch (%s)"
                            % [monster_id, rank, id]
                        )
                    if str(tooltip.get("summary", "")).is_empty():
                        failures.append(
                            "%s R%d: empty passive tooltip (%s)"
                            % [monster_id, rank, id]
                        )
                    if not (tooltip.get("effects", null) is Array):
                        failures.append(
                            "%s R%d: invalid passive tooltip effects (%s)"
                            % [monster_id, rank, id]
                        )

            if monster.passive_definitions.size() != expected_passives.size():
                failures.append(
                    "%s R%d: passive count mismatch" % [monster_id, rank]
                )
            for passive_id in expected_passives:
                if not monster.passive_definitions.has(str(passive_id)):
                    failures.append(
                        "%s R%d: missing passive %s" % [
                            monster_id, rank, passive_id
                        ]
                    )

    failures.append_array(_run_combat_regressions())

    if not failures.is_empty():
        for problem in failures:
            push_error("HEADLESS SMOKE: %s" % problem)
        print("GODOT_SMOKE_FAILED: %d issue(s)" % failures.size())
        quit(1)
        return

    print(
        "GODOT_SMOKE_OK: %d monsters, %d instances including Resonances"
        % [MONSTER_IDS.size(), built]
    )
    quit(0)


# Run real, deterministic battle actions so CI checks more than scene import
# and roster construction. Random criticals/debuffs are not asserted.
func _run_combat_regressions() -> Array[String]:
    var errors: Array[String] = []
    var battle = Battle.new()

    # Damage: first skill must reduce enemy HP and report damage.
    var attacker = Factory.create_level_one_monster("drake_igneous", 0)
    var defender = Factory.create_level_one_monster("drake_abyssal", 0)
    if attacker == null or defender == null:
        errors.append("Damage fixture could not be constructed")
        return errors

    battle.setup([attacker], [defender])
    battle.active_monster = attacker
    var before_hp: int = defender.health
    var attack_result: Dictionary = battle.execute_active_skill(
        attacker.skills[0], [defender]
    )
    if (
        not bool(attack_result.get("success", false))
        or int(attack_result.get("damage", 0)) <= 0
        or defender.health >= before_hp
    ):
        errors.append("Draconic Claw did not deal damage")

    # Healing: the shared healing handler must restore wounded ally HP.
    var dryad = Factory.create_level_one_monster("dryad_storm", 0)
    var ally = Factory.create_level_one_monster("slime_igneous", 0)
    var foe = Factory.create_level_one_monster("slime_storm", 0)
    if dryad == null or ally == null or foe == null:
        errors.append("Healing fixture could not be constructed")
        return errors

    ally.health = maxi(1, int(ally.max_health * 0.3))
    var injured_hp: int = ally.health
    battle.setup([dryad, ally], [foe])
    battle.active_monster = dryad
    var healing_result: Dictionary = battle.execute_active_skill(
        dryad.skills[1], [ally]
    )
    if (
        not bool(healing_result.get("success", false))
        or ally.health <= injured_hp
        or int(healing_result.get("healing", 0)) <= 0
    ):
        errors.append("Breath of the Grove did not heal")

    # Resurrection: Soul Recall spends its resource, revives, and grants AG.
    var dullahan = Factory.create_level_one_monster("dullahan_aether", 5)
    var fallen = Factory.create_level_one_monster("slime_abyssal", 0)
    if dullahan == null or fallen == null:
        errors.append("Soul Recall fixture could not be constructed")
        return errors

    fallen.health = 0
    battle.setup([dullahan, fallen], [foe])
    battle.active_monster = dullahan
    dullahan.combat_resources["soul_charges"] = 5
    if not battle.can_use_soul_recall(dullahan):
        errors.append("Soul Recall should be available at 5 charges")
    else:
        var recall: Dictionary = battle.execute_soul_recall(fallen)
        if (
            not bool(recall.get("success", false))
            or fallen.health <= 0
            or fallen.action_gauge < 0.999
            or dullahan.get_combat_resource("soul_charges") != 0
        ):
            errors.append("Soul Recall did not revive and spend charges")

    # Frozen Scales: spending a full stack pool grants the JSON buffs.
    var abyssal = Factory.create_level_one_monster("drake_abyssal", 3)
    var freeze_target = Factory.create_level_one_monster(
        "drake_igneous", 0
    )
    if abyssal == null or freeze_target == null:
        errors.append("Frozen Scales fixture could not be constructed")
        return errors
    battle.setup([abyssal], [freeze_target])
    battle.active_monster = abyssal
    abyssal.combat_resources["frozen_scales"] = 3
    var freeze_result: Dictionary = battle.execute_active_skill(
        abyssal.get_skill(3), [freeze_target]
    )
    if (
        not bool(freeze_result.get("success", false))
        or abyssal.get_combat_resource("frozen_scales") != 0
        or not abyssal.has_buff("defense_up")
        or not abyssal.has_buff("immunity")
    ):
        errors.append("Frozen Scales did not consume stacks and grant buffs")

    # Headlong Charge: JSON-driven ally buffs, Action Gauge, forced turn.
    var storm_rider = Factory.create_level_one_monster(
        "dullahan_storm", 5
    )
    var supported_ally = Factory.create_level_one_monster(
        "slime_igneous", 0
    )
    var storm_target = Factory.create_level_one_monster(
        "drake_abyssal", 0
    )
    if (
        storm_rider == null
        or supported_ally == null
        or storm_target == null
    ):
        errors.append("Headlong Charge fixture could not be constructed")
        return errors
    battle.setup([storm_rider, supported_ally], [storm_target])
    battle.active_monster = storm_rider
    supported_ally.action_gauge = 0.0
    var headlong_result: Dictionary = battle.execute_active_skill(
        storm_rider.get_skill(3), [storm_target]
    )
    if (
        not bool(headlong_result.get("success", false))
        or not supported_ally.has_buff("attack_up")
        or not supported_ally.has_buff("speed_up")
        or supported_ally.action_gauge < 0.29
        or battle.forced_next_monster != supported_ally
    ):
        errors.append("Headlong Charge did not grant ally support")

    # RefCounted monsters retain team references through combat_opponents.
    # Break those cycles before the headless engine exits.
    for participant in [
        attacker, defender, dryad, ally, foe, dullahan, fallen,
        abyssal, freeze_target, storm_rider, supported_ally, storm_target
    ]:
        if participant != null:
            participant.combat_opponents = []
    battle.active_monster = null
    battle.setup([], [])

    if errors.is_empty():
        print(
            "GODOT_COMBAT_OK: damage, healing, Soul Recall, "
            + "Frozen Scales and Headlong Charge"
        )
    return errors
