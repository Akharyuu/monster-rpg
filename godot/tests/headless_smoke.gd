extends SceneTree

# This is a real runtime smoke test, not a text-only GDScript assertion.
# It is run by: godot --headless --path godot --script res://tests/headless_smoke.gd
const Factory = preload("res://scripts/factories/prototype_factory.gd")

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
