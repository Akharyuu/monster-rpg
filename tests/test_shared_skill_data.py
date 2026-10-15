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


def test_monster_and_resonance_skill_ids_exist():
    ids = set(skill_module.SKILL_DATA)
    for monster_id, monster in MONSTER_DATA.items():
        for skill_id in monster.get("skills", []):
            assert skill_id in ids, (monster_id, skill_id)
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
