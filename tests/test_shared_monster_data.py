"""Contract checks for the shared Python/Godot monster roster."""

import json
import re
from pathlib import Path

import pytest

from game.data import monster_data as monster_module
from game.models.enums import Attribute


ROOT = Path(__file__).resolve().parents[1]
SHARED_JSON = ROOT / "godot" / "data" / "monster_data.json"
GODOT_FACTORY = (
    ROOT / "godot" / "scripts" / "factories"
    / "prototype_factory.gd"
)

REQUIRED_STATS = (
    "max_health",
    "attack",
    "defense",
    "speed"
)


def test_shared_monster_roster_is_the_python_source_of_truth():
    document = json.loads(SHARED_JSON.read_text(encoding="utf-8"))

    assert document["schema_version"] == 1
    raw_records = document["monsters"]
    assert raw_records
    assert set(monster_module.MONSTER_DATA) == set(raw_records)

    for monster_id, raw in raw_records.items():
        loaded = monster_module.MONSTER_DATA[monster_id]

        assert loaded["attribute"] is Attribute(
            raw["attribute"].capitalize()
        )

        # The enum is the only intentional representation difference.
        for key, value in raw.items():
            if key != "attribute":
                assert loaded[key] == value, (monster_id, key)

        assert raw["name"]
        assert raw["family"]
        assert isinstance(raw["rarity"], int)
        assert raw["rarity"] >= 1
        assert isinstance(raw["skills"], list)

        for stat in REQUIRED_STATS:
            assert isinstance(raw[stat], int), (
                monster_id, stat
            )
            assert raw[stat] > 0, (monster_id, stat)

        if "passives" in raw:
            assert isinstance(raw["passives"], list)


def test_shared_monster_data_resolves_independently_of_cwd(
    monkeypatch,
    tmp_path
):
    monkeypatch.chdir(tmp_path)

    reloaded = monster_module.load_monster_data()

    assert reloaded == monster_module.MONSTER_DATA


def test_shared_monster_schema_version_is_validated(
    monkeypatch,
    tmp_path
):
    incompatible_file = tmp_path / "monster_data.json"
    incompatible_file.write_text(
        json.dumps({"schema_version": 999, "monsters": {}}),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        monster_module,
        "SHARED_MONSTER_DATA_PATH",
        incompatible_file
    )

    with pytest.raises(ValueError, match="schema version"):
        monster_module.load_monster_data()


def test_godot_factory_uses_same_roster_and_no_stat_copies():
    source = GODOT_FACTORY.read_text(encoding="utf-8")

    # Every Godot construction goes through the shared-data helper.
    assert 'res://data/monster_data.json' in source
    assert source.count("MonsterScript.new(") == 1
    assert "_make_monster_from_data(" in source

    supported_ids = set(
        re.findall(
            r'^        "([a-z]+_[a-z]+)":$',
            source.split("static func create_level_one_monster(")[1]
            .split("static func _attach_skill_descriptions(")[0],
            flags=re.MULTILINE
        )
    )

    assert supported_ids
    assert supported_ids.issubset(monster_module.MONSTER_DATA)
