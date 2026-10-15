"""Data and Godot UI contracts for the shared tooltip migration."""
import json
from pathlib import Path

from game.data.skill_data import SKILL_DATA
from game.data.passive_data import PASSIVE_DATA
from game.data.monster_data import MONSTER_DATA

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "godot" / "data" / "skill_data.json"
PASSIVES = ROOT / "godot" / "data" / "passive_data.json"
FACTORY = ROOT / "godot" / "scripts" / "factories" / "prototype_factory.gd"

EFFECT_KINDS = {"damage", "heal", "buff", "debuff", "control", "special"}


def _valid_tooltip(value):
    assert isinstance(value, dict)
    assert isinstance(value["summary"], str) and value["summary"]
    effects = value["effects"]
    assert isinstance(effects, list)
    for effect in effects:
        assert effect["kind"] in EFFECT_KINDS
        assert isinstance(effect["text"], str) and effect["text"]


def test_all_skill_tooltips_are_stored_in_shared_skill_json():
    records = json.loads(SKILLS.read_text(encoding="utf-8"))["skills"]
    assert len(records) == 68
    assert set(records) == set(SKILL_DATA)
    for skill_id, record in records.items():
        assert record["tooltip"] == SKILL_DATA[skill_id]["tooltip"]
        _valid_tooltip(record["tooltip"])


def test_base_passive_tooltips_live_in_passive_json():
    records = json.loads(PASSIVES.read_text(encoding="utf-8"))["passives"]
    ids = {
        mid: monster["passives"][0]
        for mid, monster in MONSTER_DATA.items()
        if monster.get("passives")
    }
    assert len(ids) == 8
    for mid, passive_id in ids.items():
        record = records[passive_id]
        assert record["tooltip"] == PASSIVE_DATA[passive_id]["tooltip"]
        assert record["tooltip"]["name"] == record["name"]
        _valid_tooltip(record["tooltip"])


def test_godot_tooltips_use_canonical_records_without_manual_maps():
    source = FACTORY.read_text(encoding="utf-8")
    skill_code = source.split(
        "static func _attach_skill_descriptions(monster) -> void:"
    )[1].split("static func _attach_passive_description(")[0]
    passive_code = source.split(
        "static func _attach_passive_description(monster) -> void:"
    )[1].split("static func _scaled(")[0]

    assert 'var definitions: Dictionary = _get_shared_skills()' in skill_code
    assert 'entry.get("tooltip", {})' in skill_code
    assert "skill.tooltip_effects = effects.duplicate(true)" in skill_code
    assert "skill.description = skill.tooltip_summary" in skill_code
    assert "var tooltip_data := {" not in source

    assert '_get_shared_monsters().get(' in passive_code
    assert '_get_shared_passives().get(' in passive_code
    assert 'passive_record.get("tooltip", {})' in passive_code
    assert "monster.passive_tooltip = tooltip.duplicate(true)" in passive_code
    assert "var passive_data := {" not in source
    assert 'if monster.monster_id == "dullahan_aether":' in passive_code


def test_existing_combat_fields_stay_separate_from_tooltips():
    data = SKILL_DATA
    assert data["draconic_claw"]["effects"][0]["effect_id"] == "defense_break"
    assert data["draconic_claw"]["tooltip"]["effects"][0]["kind"] == "debuff"
    assert data["flame_devourer"]["damage_handler"] == "damage_for_burn_stacks"
    assert data["flame_devourer"]["tooltip"]["summary"]


def test_important_tooltip_wording_preserved():
    assert "[b]30% chance[/b]" in (
        SKILL_DATA["draconic_claw"]["tooltip"]["effects"][0]["text"]
    )
    assert "Soul Charges" in (
        SKILL_DATA["beyond_the_veil"]["tooltip"]["effects"][0]["text"]
    )
    assert "Scorching" in (
        SKILL_DATA["flame_devourer_rekindled"]["tooltip"]["effects"][-1]["text"]
    )
    assert "Frozen Scales" in PASSIVE_DATA["frozen_scales"]["tooltip"]["summary"]


def test_void_drake_tooltip_uses_shared_base_passive():
    source = FACTORY.read_text(encoding="utf-8")
    passive_block = source.split(
        "static func _attach_passive_description(monster) -> void:"
    )[1].split("static func _scaled(")[0]

    # The local passive_data map was removed when base tooltips
    # migrated to JSON; no dynamic tooltip may reference it.
    assert "passive_data.get(" not in passive_block
    assert 'if monster.monster_id == "drake_void":' in passive_block
    assert "monster.passive_tooltip.duplicate(true)" in passive_block
    assert 'monster.passive_tooltips.append(' in passive_block

    base_id = MONSTER_DATA["drake_void"]["passives"][0]
    assert base_id == "bottomless_hunger"
    assert PASSIVE_DATA[base_id]["tooltip"]["name"] == "Bottomless Hunger"
