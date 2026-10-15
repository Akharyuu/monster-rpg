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
