"""Contract checks for canonical passive and Resonance data."""
import json
from pathlib import Path

import pytest

from game.data import passive_data as passive_module
from game.data import resonance_data as resonance_module
from game.data.monster_data import MONSTER_DATA
from game.data.skill_data import SKILL_DATA

ROOT = Path(__file__).resolve().parents[1]
PASSIVE_JSON = ROOT / "godot" / "data" / "passive_data.json"
RESONANCE_JSON = ROOT / "godot" / "data" / "resonance_data.json"


def test_passive_records_are_the_python_source_of_truth():
    document = json.loads(PASSIVE_JSON.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert len(document["passives"]) == 34
    assert document["passives"] == passive_module.PASSIVE_DATA


def test_resonance_records_preserve_integer_level_keys():
    document = json.loads(RESONANCE_JSON.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert len(document["resonances"]) == 12
    assert set(document["resonances"]) == set(resonance_module.RESONANCE_DATA)
    for mid, levels in document["resonances"].items():
        for level, actions in levels.items():
            assert level in ("1", "2", "3", "4", "5")
            assert resonance_module.RESONANCE_DATA[mid][int(level)] == actions


def test_all_passive_skill_resonance_references_are_valid():
    passive_ids = set(passive_module.PASSIVE_DATA)
    for mid, monster in MONSTER_DATA.items():
        assert set(monster.get("passives", [])).issubset(passive_ids), mid

    for mid, levels in resonance_module.RESONANCE_DATA.items():
        current_skills = list(MONSTER_DATA[mid]["skills"])
        current_passives = list(MONSTER_DATA[mid].get("passives", []))
        for level in range(1, 6):
            for change in levels.get(level, []):
                action = change["action"]
                if action == "add_passive":
                    assert change["passive"] in passive_ids
                    assert change["passive"] not in current_passives
                    current_passives.append(change["passive"])
                elif action == "replace_passive":
                    assert change["new"] in passive_ids
                    assert change["old"] in current_passives
                    current_passives[current_passives.index(change["old"])] = change["new"]
                elif action == "replace_skill":
                    assert change["new"] in SKILL_DATA
                    slot = change["slot"]
                    assert 1 <= slot <= len(current_skills)
                    current_skills[slot - 1] = change["new"]
                elif action == "add_skill":
                    assert change["skill"] in SKILL_DATA
                    current_skills.append(change["skill"])
                else:
                    pytest.fail(f"Unknown Resonance action: {action}")


def test_loads_shared_data_without_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert passive_module.load_passive_data() == passive_module.PASSIVE_DATA
    assert resonance_module.load_resonance_data() == resonance_module.RESONANCE_DATA


@pytest.mark.parametrize(
    ("module", "path_attr", "loader", "filename"),
    (
        (passive_module, "SHARED_PASSIVE_DATA_PATH", "load_passive_data",
         "passive_data.json"),
        (resonance_module, "SHARED_RESONANCE_DATA_PATH", "load_resonance_data",
         "resonance_data.json"),
    ),
)
def test_rejects_bad_schema_versions(
    monkeypatch, tmp_path, module, path_attr, loader, filename
):
    file = tmp_path / filename
    file.write_text(json.dumps({"schema_version": 999}), encoding="utf-8")
    monkeypatch.setattr(module, path_attr, file)
    with pytest.raises(ValueError, match="schema version"):
        getattr(module, loader)()
