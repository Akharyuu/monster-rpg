"""Contract checks for canonical passive and Resonance data."""
import json
import re
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


def test_godot_resolves_and_consumes_shared_passive_data():
    factory = (
        ROOT / "godot" / "scripts" / "factories" / "prototype_factory.gd"
    ).read_text(encoding="utf-8")
    monster = (
        ROOT / "godot" / "scripts" / "models" / "monster.gd"
    ).read_text(encoding="utf-8")
    battle = (
        ROOT / "godot" / "scripts" / "battle" / "battle_controller.gd"
    ).read_text(encoding="utf-8")

    assert 'res://data/passive_data.json' in factory
    assert 'res://data/resonance_data.json' in factory
    assert 'levels.get(str(level), [])' in factory
    assert 'operation == "replace_passive"' in factory
    assert 'operation == "add_passive"' in factory
    assert "monster.passive_definitions = active" in factory
    assert 'get_passive_by_handler("apply_burn")' in factory
    assert "if not _assign_shared_passives(monster):" in factory
    assert 'get_passive_by_handler("thunderheart")' in monster
    assert 'get_passive_by_handler("natures_grace")' in monster
    assert 'get_passive_by_handler("deathless_rider")' in monster
    assert re.search(
        r'get_passive_by_handler\(\s*"chilling_presence"\s*\)',
        battle,
    )
    assert re.search(
        r'get_passive_by_handler\(\s*"the_hunt"\s*\)',
        battle,
    )


@pytest.mark.parametrize(
    ("monster_id", "level", "expected_passives"),
    (
        ("drake_igneous", 0, {"cinderblood"}),
        ("drake_igneous", 1, {"cinderblood_ignite"}),
        ("drake_igneous", 4, {"cinderblood_molten_core"}),
        ("drake_abyssal", 4, {
            "frozen_scales_everfrost", "frostborne_everlasting_winter"
        }),
        ("drake_storm", 5, {
            "thunderheart_overclocked", "short_circuit_chain_reaction"
        }),
        ("dullahan_aether", 5, {"soul_vessel_requiem"}),
        ("dullahan_void", 5, {"deathless_rider", "death_march"}),
        ("dryad_storm", 5, {"natures_grace_overgrowth"}),
    ),
)
def test_resonance_resolves_expected_passive_kits(
    monster_id, level, expected_passives
):
    active = set(MONSTER_DATA[monster_id].get("passives", []))
    rules = resonance_module.RESONANCE_DATA[monster_id]

    for rank in range(1, level + 1):
        for action in rules.get(rank, []):
            if action["action"] == "add_passive":
                active.add(action["passive"])
            elif action["action"] == "replace_passive":
                active.remove(action["old"])
                active.add(action["new"])

    assert active == expected_passives


def test_passive_resource_caps_handle_top_level_and_nested_data():
    # Frozen Scales stores its cap directly in the passive record.
    # Soul Vessel and Voidborn store caps under handler_data.
    definitions = passive_module.PASSIVE_DATA
    assert definitions["frozen_scales"]["max_scales"] == 3
    assert definitions["frozen_scales_everfrost"]["max_scales"] == 3
    assert definitions["soul_vessel"]["handler_data"]["max_charges"] == 5
    assert definitions["voidborn"]["handler_data"]["max_stacks"] == 5

    factory = (
        ROOT / "godot" / "scripts" / "factories" / "prototype_factory.gd"
    ).read_text(encoding="utf-8")
    assert re.search(
        r'passive\.get\(\s*"handler_data",\s*passive\s*\)',
        factory,
    )
    assert 'monster.combat_resource_maximums[key] = maximum' in factory


def test_shared_passive_combat_parameters_are_used_by_godot():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    source = (
        repo / "godot" / "scripts" / "battle" / "battle_controller.gd"
    ).read_text(encoding="utf-8")
    for handler in (
        "bottomless_hunger", "divine_grace", "apply_self_buff",
        "celestial_authority", "natures_grace"
    ):
        assert f'get_passive_by_handler(\n' in source
        assert f'"{handler}"' in source
    for parameter in (
        "heal_ratio_per_buff", "action_gauge_per_buff",
        "action_gauge_to_most_buffed_ally", "overheal_conversion",
        "max_shield_ratio", "shield_turns"
    ):
        assert parameter in source
