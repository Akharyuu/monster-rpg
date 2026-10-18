"""Static Godot compatibility checks for optional Igneous battle bars."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUD = ROOT / "godot" / "scenes" / "battle" / "monster_battle_hud.gd"


def test_igneous_uses_optional_ui_sprite_sheet_only_for_igneous():
    source = HUD.read_text(encoding="utf-8")
    assert '"res://assets/ui/sprite-max-px-frames-36-rows-6-cols-6.json"' in source
    assert 'str(bound_monster.attribute) == "igneous"' in source
    assert "_get_igneous_bar_texture()" in source
    assert "hp_bar.visible = not use_art" in source
    assert "action_gauge.visible = not use_art" in source


def test_preview_uses_only_first_frame_and_respects_resized_sheets():
    source = HUD.read_text(encoding="utf-8")
    assert 'records.get("frame_000", {})' in source
    assert "width / IGNEOUS_BAR_COLUMNS" in source
    assert "height / IGNEOUS_BAR_ROWS" in source
    assert "sheet.get_region(cell)" in source
    assert "frame.get_used_rect()" in source
    assert "ImageTexture.create_from_image(painted_frame)" in source
    assert "IGNEOUS_BAR_DISPLAY_SIZE := Vector2(142.0, 36.0)" in source


def test_existing_combat_data_progress_is_preserved():
    source = HUD.read_text(encoding="utf-8")
    assert "hp_bar.value = bound_monster.health" in source
    assert "bound_monster.action_gauge * 100.0" in source
    assert "hp_bar.max_value = monster.max_health" in source
    assert "action_gauge.max_value = 100.0" in source
