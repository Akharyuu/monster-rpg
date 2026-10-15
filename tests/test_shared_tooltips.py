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

    assert "for passive_id in monster.passive_ids:" in passive_code
    assert 'record.get("tooltip", {})' in passive_code
    assert 'record.get("tooltip_rank_additions", {})' in passive_code
    assert "monster.passive_tooltip = monster.passive_tooltips[0]" in passive_code
    assert "var passive_data := {" not in source
    assert "if monster.monster_id ==" not in passive_code


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
    assert "if monster.monster_id ==" not in passive_block
    assert "for passive_id in monster.passive_ids:" in passive_block
    assert 'monster.passive_tooltips.append(' in passive_block

    base_id = MONSTER_DATA["drake_void"]["passives"][0]
    assert base_id == "bottomless_hunger"
    assert PASSIVE_DATA[base_id]["tooltip"]["name"] == "Bottomless Hunger"


def test_all_passive_variants_have_canonical_tooltips():
    doc = json.loads(PASSIVES.read_text(encoding="utf-8"))
    records = doc["passives"]
    assert len(records) == 34
    for passive_id, record in records.items():
        assert PASSIVE_DATA[passive_id]["tooltip"] == record["tooltip"]
        tooltip = record["tooltip"]
        assert tooltip["name"] == record["name"], passive_id
        _valid_tooltip(tooltip)
        for rank, additions in record.get("tooltip_rank_additions", {}).items():
            assert rank in {"1", "2", "3", "4", "5"}
            assert additions
            for effect in additions:
                assert effect["kind"] in EFFECT_KINDS
                assert isinstance(effect["text"], str) and effect["text"]


def test_dynamic_passive_descriptions_no_longer_embed_monster_branches():
    source = FACTORY.read_text(encoding="utf-8")
    dynamic = source.split(
        "static func _attach_passive_description(monster) -> void:"
    )[1].split("static func _scaled(")[0]
    assert "for passive_id in monster.passive_ids:" in dynamic
    assert 'record.get("tooltip", {})' in dynamic
    assert 'record.get("tooltip_rank_additions", {})' in dynamic
    assert 'rank_additions.get(str(rank), [])' in dynamic
    assert "monster.passive_tooltips.append(visible)" in dynamic
    assert "monster.passive_tooltip = monster.passive_tooltips[0]" in dynamic
    assert "if monster.monster_id ==" not in dynamic
    assert "passive_data.get(" not in dynamic

    resolver = source.split(
        "static func _assign_shared_passives(monster) -> bool:"
    )[1].split("static func _sync_skill_from_shared_data(")[0]
    assert "ordered_ids[index] = new_id" in resolver
    assert "monster.passive_ids = ordered_ids" in resolver


def test_soul_vessel_recall_and_deathless_cooldown_tooltips_are_preserved():
    soul = PASSIVE_DATA["soul_vessel_last_rites"]
    assert soul["tooltip"]["name"] == "Soul Vessel: Last Rites"
    assert len(soul["tooltip"]["effects"]) == 3
    recall = soul["tooltip_rank_additions"]["2"]
    assert len(recall) == 1
    assert "Soul Recall" in recall[0]["text"]
    assert "Soul Recall" in PASSIVE_DATA["soul_vessel_requiem"]["tooltip"][
        "effects"
    ][-1]["text"]

    deathless = PASSIVE_DATA["deathless_rider"]["tooltip"]
    assert deathless["internal_cooldown_id"] == "deathless_rider"


def test_godot_smoke_checks_passive_tooltip_order_and_rank():
    script = (
        ROOT / "godot" / "tests" / "headless_smoke.gd"
    ).read_text(encoding="utf-8")
    assert "monster.passive_ids != expected_passives" in script
    assert "monster.passive_tooltips.size() != expected_passives.size()" in script
    assert "passive tooltip name mismatch" in script
