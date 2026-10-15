"""Contract checks for shared skill definitions and Python compatibility."""
import json
from pathlib import Path

import pytest

from game.data import skill_data as skill_module
from game.data.monster_data import MONSTER_DATA
from game.data.resonance_data import RESONANCE_DATA
from game.models.enums import SkillType, TargetType


ROOT = Path(__file__).resolve().parents[1]
SHARED_JSON = ROOT / "godot" / "data" / "skill_data.json"
GODOT_FACTORY = ROOT / "godot" / "scripts" / "factories" / "prototype_factory.gd"


def _as_json(value):
    if isinstance(value, (SkillType, TargetType)):
        return value.name.lower()
    if isinstance(value, dict):
        return {str(key): _as_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_as_json(item) for item in value]
    return value


def test_python_loads_identical_shared_skill_records():
    document = json.loads(SHARED_JSON.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    definitions = document["skills"]
    assert definitions
    assert set(definitions) == set(skill_module.SKILL_DATA)
    for skill_id, raw in definitions.items():
        loaded = skill_module.SKILL_DATA[skill_id]
        assert loaded["type"] is SkillType[raw["type"].upper()]
        assert loaded["target_type"] is TargetType[raw["target_type"].upper()]
        assert _as_json(loaded) == raw, skill_id
        assert raw["name"] and isinstance(raw["cooldown"], int)
        assert raw["cooldown"] >= 0
        if raw["type"] == "damage":
            assert raw["multiplier"] > 0


def test_numeric_lookup_keys_preserve_python_semantics():
    skills = skill_module.SKILL_DATA
    assert 1 in skills["scorching_breath"]["damage_handler_data"]["multipliers_by_stacks"]
    assert 3 in skills["flame_devourer"]["after_skill_handlers"][0]["data"]["heal_by_stacks"]
    assert 2 in skills["swarm_pierce"]["damage_handler_data"]["multipliers_by_hit"]


# Pre-existing prototype/demo monsters retained in monster_data.json, but
# not yet implemented in either skill_data.json or Godot's prototype factory.
# Keep their exact unresolved IDs explicit so future broken references are
# not silently ignored.
LEGACY_UNIMPLEMENTED_SKILLS = {
    "goblin_igneous": {"drake_claw"},
    "golem_storm": {"heavy_slam", "earths_echo"},
    "piñata": {"drake_claw"},
}


def test_monster_and_resonance_skill_ids_exist():
    ids = set(skill_module.SKILL_DATA)

    assert set(LEGACY_UNIMPLEMENTED_SKILLS).issubset(MONSTER_DATA)

    for monster_id, monster in MONSTER_DATA.items():
        missing = set(monster.get("skills", [])) - ids
        assert missing == LEGACY_UNIMPLEMENTED_SKILLS.get(
            monster_id, set()
        ), (monster_id, missing)

    for monster_id, levels in RESONANCE_DATA.items():
        for level, actions in levels.items():
            for action in actions:
                if action["action"] == "replace_skill":
                    assert action["new"] in ids, (monster_id, level)


def test_path_does_not_depend_on_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert skill_module.load_skill_data() == skill_module.SKILL_DATA


def test_rejects_unknown_schema(monkeypatch, tmp_path):
    file = tmp_path / "skill_data.json"
    file.write_text(json.dumps({"schema_version": 999, "skills": {}}))
    monkeypatch.setattr(skill_module, "SHARED_SKILL_DATA_PATH", file)
    with pytest.raises(ValueError, match="schema version"):
        skill_module.load_skill_data()


def test_godot_syncs_core_values_from_same_file():
    source = GODOT_FACTORY.read_text(encoding="utf-8")
    assert 'res://data/skill_data.json' in source
    assert 'parsed.get("skills", {})' in source
    assert 'if not _sync_monster_skills(monster):' in source
    for line in (
        'skill.skill_name = str(entry["name"])',
        'skill.cooldown = int(entry["cooldown"])',
        'skill.target_type = str(entry["target_type"])',
        'skill.multiplier = float(entry["multiplier"])',
    ):
        assert line in source


def test_simple_families_have_only_supported_shared_skill_handlers():
    simple_families = {"Slime", "Sprout", "Wisp", "Thornet"}
    known_ids = set()
    for monster in MONSTER_DATA.values():
        if monster["family"] not in simple_families:
            continue
        known_ids.update(monster["skills"])

    assert len(known_ids) == 7
    for skill_id in known_ids:
        record = skill_module.SKILL_DATA[skill_id]
        assert record["type"] is SkillType.DAMAGE
        for config in record.get("on_hit_handlers", []):
            assert config["handler"] == "reduce_action_gauge"
        for config in record.get("after_use_handlers", []):
            assert config["handler"] == "heal_lowest_hp_ally"
        if record.get("damage_handler"):
            assert record["damage_handler"] == "damage_if_condition"
            assert record["damage_handler_data"]["condition"]["type"] in {
                "target_has_debuff", "target_has_any_debuff"
            }


def test_basic_godot_monsters_use_shared_skill_factory():
    source = GODOT_FACTORY.read_text(encoding="utf-8")
    assert "static func _create_shared_damage_skill(" in source
    assert "static func _create_shared_damage_monster(" in source
    assert "for skill_id in monsters[monster_id].get(\"skills\", []):" in source
    assert source.count(
        "monster = _create_shared_damage_monster(monster_id)"
    ) == 12
    for removed_constructor in (
        "_create_thornet(", "_create_wisp(", "_create_sprout(",
        "_create_storm_slime(", "_create_abyssal_slime(",
        "_create_igneous_slime(",
    ):
        assert removed_constructor not in source


def test_godot_uses_shared_lowest_ally_heal_ratios():
    factory = GODOT_FACTORY.read_text(encoding="utf-8")
    damage = (
        ROOT / "godot" / "scripts" / "models" / "damage_skill.gd"
    ).read_text(encoding="utf-8")
    controller = (
        ROOT / "godot" / "scripts" / "battle" / "battle_controller.gd"
    ).read_text(encoding="utf-8")

    assert 'handler_config.get("handler", "")) == "heal_lowest_hp_ally"' in factory
    assert "var heal_lowest_hp_ally_ratio: float = 0.0" in damage
    assert "skill.heal_lowest_hp_ally_ratio > 0.0" in controller
    assert 'skill.skill_id == "vine_barrage"' not in controller


DRAKE_IDS = (
    "drake_igneous", "drake_abyssal", "drake_storm",
    "drake_aether", "drake_void",
)

DRAKE_RESONANCE_SKILL_IDS = (
    "scorching_breath_afterburn",
    "flame_devourer_rekindled",
    "flame_devourer_incineration",
    "rime_breath_frigid",
    "glacial_collapse_absolute_zero",
    "lightning_rush_blitz",
    "stormbreak_requiem",
    "sovereign_breath_subjugation",
    "heavens_decree_apotheosis",
    "null_rend_obliterate",
    "null_rend_annihilation",
    "dismantle_decimation",
)


def test_all_drakes_and_resonance_skills_use_canonical_json():
    definitions = skill_module.SKILL_DATA
    for monster_id in DRAKE_IDS:
        for skill_id in MONSTER_DATA[monster_id]["skills"]:
            assert skill_id in definitions

    assert set(DRAKE_RESONANCE_SKILL_IDS).issubset(definitions)

    source = GODOT_FACTORY.read_text(encoding="utf-8")
    assert source.count("monster = _create_shared_drake(monster_id)") == 5
    assert "static func _create_shared_drake(" in source
    assert "static func _create_shared_skill(" in source
    for obsolete in (
        "static func _create_igneous_drake(",
        "static func _create_abyssal_drake(",
        "static func _create_storm_drake(",
        "static func _create_aether_drake(",
        "static func _create_void_drake(",
    ):
        assert obsolete not in source


def test_godot_drake_skill_adapters_cover_shared_handlers():
    source = GODOT_FACTORY.read_text(encoding="utf-8")
    for handler in (
        "apply_debuff_on_hit_indices",
        "strip_buffs_on_hit",
        "damage_for_burn_stacks",
        "damage_for_removed_buffs",
        "consume_burn_and_heal",
        "add_burn_if_target_started_with_burn",
        "reset_cooldown_by_burn_stacks",
        "reduce_action_gauge_if_debuff",
    ):
        assert handler in source

    # JSON map keys must become integers: Godot's Burn stack damage and
    # healing code looks up stack counts as integers.
    assert "values[int(key)] = float(raw[key])" in source
    assert "_int_keyed_skill_values(" in source


def test_drake_resonance_skill_variants_share_base_core_schema():
    for skill_id in DRAKE_RESONANCE_SKILL_IDS:
        record = skill_module.SKILL_DATA[skill_id]
        assert record["type"] in {SkillType.DAMAGE, SkillType.SUPPORT}
        assert record["target_type"] in TargetType
        assert isinstance(record["cooldown"], int)
        if record["type"] is SkillType.DAMAGE:
            assert record["hits"] >= 1
            assert record["multiplier"] > 0


ADVANCED_MONSTERS = (
    "dullahan_igneous", "dullahan_abyssal", "dullahan_storm",
    "dullahan_aether", "dullahan_void",
    "griffon_igneous", "dryad_storm",
)

ADVANCED_RESONANCE_SKILLS = (
    "beyond_the_veil_convergence",
    "beyond_the_veil_soul_recall",
    "soulpiercer_ascension",
    "spinal_scourge_ossuary",
    "deaths_gaze_last_name",
    "spectral_shackles_lockdown",
    "spectral_shackles_binding",
    "inescapable_fate_ironbound",
    "inescapable_fate",
    "gale_pursuit_tempest",
    "gale_pursuit_crosswind",
    "headlong_charge_stampede",
    "headlong_charge_rally",
    "relentless_pursuit_blood_trail",
    "death_sentence_massacre",
    "death_sentence_execution",
    "breath_of_the_grove_sanctuary",
    "vine_barrage_nourishment",
    "breath_of_the_grove_evergreen",
    "meteor_dive_violent_crash",
    "searing_gale_turbulence",
    "meteor_dive_terminal_impact",
    "searing_gale_heatstorm"
)


def test_advanced_monsters_use_canonical_skill_constructors():
    source = GODOT_FACTORY.read_text(encoding="utf-8")
    assert source.count(
        "monster = _create_shared_advanced_monster(monster_id)"
    ) == 7
    assert "static func _create_shared_advanced_monster(" in source
    for monster_id in ADVANCED_MONSTERS:
        for skill_id in MONSTER_DATA[monster_id]["skills"]:
            assert skill_id in skill_module.SKILL_DATA
    referenced = {
        action["new"] if action["action"] == "replace_skill"
        else action["skill"]
        for levels in RESONANCE_DATA.values()
        for actions in levels.values()
        for action in actions
        if action["action"] in {"replace_skill", "add_skill"}
    }
    for skill_id in ADVANCED_RESONANCE_SKILLS:
        assert skill_id in skill_module.SKILL_DATA
        assert skill_id in referenced
    assert source.count("DamageSkillScript.new(") == 1
    assert source.count("SupportSkillScript.new(") == 1
    assert source.count("MonsterScript.new(") == 1


def test_advanced_damage_handler_adapters_are_present():
    source = GODOT_FACTORY.read_text(encoding="utf-8")
    for handler in (
        "damage_by_missing_health", "execute_below_health_threshold",
        "damage_for_soul_charges", "damage_for_dead_monsters",
        "damage_with_bonus_stat", "damage_with_speed_scaling",
        "reduce_action_gauge_with_threshold_bonus",
        "gain_action_gauge_if_target_low_hp",
        "apply_named_and_vulnerability",
    ):
        assert handler in source
    assert "skill.apply_named_before_hit = true" in source
    assert "skill.use_consumed_soul_charges = bool(" in source
    # Soul Charges are initialized by the shared passive adapter,
    # not by a hand-written Aether Dullahan constructor.
    assert '"soul_vessel": "soul_charges"' in source
    assert 'maximum_key = "max_charges"' in source
    assert 'monster.combat_resources[key] = 0' in source
    assert 'monster.combat_resource_maximums[key] = maximum' in source


def test_special_revival_and_turn_rules_remain_canonical():
    skills = skill_module.SKILL_DATA
    assert skills["beyond_the_veil_soul_recall"]["active_action"][
        "id"
    ] == "soul_recall"
    assert skills["beyond_the_veil_convergence"]["active_action"][
        "id"
    ] == "soul_recall_convergence"
    assert skills["headlong_charge_stampede"][
        "after_use_handlers"
    ][0]["data"]["force_next_turn"] is True


def test_godot_uses_shared_skill_resonance_rules():
    source = GODOT_FACTORY.read_text(encoding="utf-8")
    assert "static func _apply_resonance(monster) -> bool:" in source
    selector = source.split(
        "static func _apply_resonance(monster) -> bool:"
    )[1]
    assert "var rules: Dictionary = _get_shared_resonances()" in selector
    assert "for rank in range(1, monster.resonance + 1):" in selector
    assert "for action in levels.get(str(rank), []):" in selector
    assert 'operation == "replace_skill"' in selector
    assert 'operation == "add_skill"' in selector
    assert 'int(action.get("slot", 0)) - 1' in selector
    assert "monster.skills[slot] = replacement" in selector
    assert "monster.skills.append(extra_skill)" in selector
    assert "if not _apply_resonance(monster):" in source
    assert 'if monster.monster_id == "' not in selector
    assert "if not _assign_shared_passives(monster):" in source


@pytest.mark.parametrize(
    ("monster_id", "resonance", "expected"),
    (
        ("drake_igneous",0,["draconic_claw","scorching_breath","flame_devourer"]),
        ("drake_igneous",2,["draconic_claw","scorching_breath_afterburn","flame_devourer"]),
        ("drake_igneous",5,["draconic_claw","scorching_breath_afterburn","flame_devourer_incineration"]),
        ("drake_void",1,["draconic_claw","null_rend_obliterate","dismantle"]),
        ("drake_void",4,["draconic_claw","null_rend_obliterate","dismantle_decimation"]),
        ("drake_void",5,["draconic_claw","null_rend_annihilation","dismantle_decimation"]),
        ("dullahan_abyssal",0,["severing_blade","spectral_shackles"]),
        ("dullahan_abyssal",2,["severing_blade","spectral_shackles_binding","inescapable_fate"]),
        ("dullahan_abyssal",4,["severing_blade","spectral_shackles_lockdown","inescapable_fate"]),
        ("dullahan_abyssal",5,["severing_blade","spectral_shackles_lockdown","inescapable_fate_ironbound"]),
        ("dullahan_aether",2,["severing_blade","soulpiercer","beyond_the_veil_soul_recall"]),
        ("dullahan_aether",5,["severing_blade","soulpiercer_ascension","beyond_the_veil_convergence"]),
        ("dullahan_storm",5,["severing_blade","gale_pursuit_tempest","headlong_charge_stampede"]),
        ("dryad_storm",5,["vine_barrage_nourishment","breath_of_the_grove_evergreen"]),
        ("griffon_igneous",5,["rending_talons","searing_gale_heatstorm","meteor_dive_terminal_impact"]),
    ),
)
def test_resonance_skill_kits_preserve_previous_godot_behavior(
    monster_id, resonance, expected
):
    # Explicit snapshots of representative kits from the old selector.
    current = list(MONSTER_DATA[monster_id]["skills"])
    for rank in range(1, resonance + 1):
        for action in RESONANCE_DATA[monster_id][rank]:
            if action["action"] == "replace_skill":
                current[action["slot"] - 1] = action["new"]
            elif action["action"] == "add_skill":
                current.append(action["skill"])
    assert current == list(expected)


def test_resonance_action_totals_remain_stable():
    actions = [
        action
        for levels in RESONANCE_DATA.values()
        for changes in levels.values()
        for action in changes
    ]
    assert len(actions) == 60
    assert sum(a["action"] == "replace_skill" for a in actions) == 34
    assert sum(a["action"] == "add_skill" for a in actions) == 1


def test_godot_skills_resolve_combat_handlers_from_json():
    root = GODOT_FACTORY.parents[3]
    base = (root / "godot" / "scripts" / "models" / "skill.gd"
            ).read_text(encoding="utf-8")
    battle = (root / "godot" / "scripts" / "battle" /
              "battle_controller.gd").read_text(encoding="utf-8")
    assert "var shared_definition: Dictionary = {}" in base
    assert "func get_handler_data(" in base
    assert "func has_handler(" in base
    assert "skill.shared_definition = entry" in GODOT_FACTORY.read_text(
        encoding="utf-8"
    )
    for handler_id in (
        "reduce_action_gauge_if_both_debuffs_applied",
        "extend_target_debuffs", "apply_team_buff",
        "apply_self_buff", "increase_action_gauge",
        "apply_scaling_silence", "grant_extra_turn",
    ):
        assert handler_id in battle
        assert any(
            item["handler"] == handler_id
            for record in skill_module.SKILL_DATA.values()
            for item in (record.get("after_use_handlers", []) +
                         record.get("after_skill_handlers", []))
        )


def test_godot_soul_recall_uses_canonical_active_action():
    source = (
        GODOT_FACTORY.parents[3]
        / "godot" / "scripts" / "battle" / "battle_controller.gd"
    ).read_text(encoding="utf-8")
    assert "func _soul_recall_action(caster) -> Dictionary:" in source
    assert 'skill.shared_definition.get(' in source
    assert 'action.get("required_charges", 0)' in source
    assert 'action.get("consume_charges", 0)' in source
    assert '"revive_health_ratio", 0.0' in source
    assert '"charges_per_damage_skill"' in source
    assert '"charges_per_death"' in source
    assert '"last_rites_threshold"' in source


def test_headlong_charge_support_parameters_stay_in_json():
    records = skill_module.SKILL_DATA
    for skill_id, expected_gauge in (
        ("headlong_charge", 0.20),
        ("headlong_charge_rally", 0.30),
        ("headlong_charge_stampede", 0.30),
    ):
        skill = records[skill_id]
        handler = next(
            x["data"] for x in skill["after_use_handlers"]
            if x["handler"] == "support_lowest_gauge_ally"
        )
        assert handler["ally_action_gauge"] == expected_gauge
        assert len(handler["self_buffs"]) == 2

    controller = (
        GODOT_FACTORY.parents[3] / "godot" / "scripts"
        / "battle" / "battle_controller.gd"
    ).read_text(encoding="utf-8")
    assert 'skill.has_handler("support_lowest_gauge_ally")' in controller
    assert 'support_data.get("self_buffs", [])' in controller
    assert 'support_data.get("ally_buffs", [])' in controller
    assert 'support_data.get("force_next_turn", false)' in controller
