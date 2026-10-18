"""Abyssal visual comparison in Godot's four-versus-four test battle."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BATTLE = ROOT / "godot/scenes/battle/battle_screen.gd"
HUD = ROOT / "godot/scenes/battle/monster_battle_hud.gd"


def test_only_fourth_enemy_becomes_vharak():
    source = BATTLE.read_text(encoding="utf-8")
    match = re.search(r"\tenemies = \[(.*?)\n\t\]", source, re.DOTALL)
    assert match is not None
    assert match.group(1).count('"drake_igneous"') == 3
    assert match.group(1).count('"drake_abyssal"') == 1
    assert match.group(1).strip().endswith('''"drake_abyssal"
        )'''.replace("        ", "\t\t"))
    assert source.count("enemies = [") == 1


def test_static_abyssal_art_scales_down_in_both_dimensions():
    source = HUD.read_text(encoding="utf-8")
    assert 'ABYSSAL_BAR_PATH := "res://assets/Abyssal HP bar.png"' in source
    assert "ABYSSAL_BAR_WIDTH := 182.4" in source
    assert "BAR_ORIGINAL_WIDTH := 227.2" in source
    assert "BAR_ORIGINAL_WIDTH *" in source
    assert '"abyssal":' in source
    assert "float(abyssal.get_height())" in source
    assert "float(abyssal.get_width()) * BAR_HEIGHT_SCALE" in source
    assert "BAR_HEIGHT_SCALE := 0.90" in source
    assert "image.get_used_rect()" in source
    assert "ImageTexture.create_from_image(" in source
    assert "_position_abyssal_bar()" in source
    assert "_abyssal_bar_art.visible = true" in source


def test_igneous_still_animates_and_fallback_values_are_preserved():
    source = HUD.read_text(encoding="utf-8")
    assert "_load_igneous_bar_animation()" in source
    assert '_igneous_bar_art.texture = _igneous_bar_frames[0]' in source
    assert "func _process(delta: float) -> void:" in source
    assert "hp_bar.visible = not use_art" in source
    assert "action_gauge.visible = not use_art" in source
    assert "hp_bar.value = bound_monster.health" in source
    assert "bound_monster.action_gauge * 100.0" in source


def test_preview_shows_original_sized_abyssal_bar_for_every_attribute():
    source = HUD.read_text(encoding="utf-8")
    assert "const FORCE_ABYSSAL_BAR_PREVIEW := true" in source
    assert "if FORCE_ABYSSAL_BAR_PREVIEW:" in source
    assert "use_art = _show_abyssal_bar()" in source
    assert "func _show_abyssal_bar() -> bool:" in source
    assert "ABYSSAL_BAR_WIDTH := 182.4" in source
    assert "float(abyssal.get_width()) * BAR_HEIGHT_SCALE" in source
    assert "_abyssal_bar_art.size = _igneous_bar_preview_size" not in source
    assert "hp_bar.visible = not use_art" in source
    assert "action_gauge.visible = not use_art" in source

def test_abyssal_preview_is_ten_percent_smaller_in_both_dimensions():
    source = HUD.read_text(encoding="utf-8")
    assert "const ABYSSAL_PREVIEW_SCALE := 0.90" in source
    assert "ABYSSAL_BAR_WIDTH * ABYSSAL_PREVIEW_SCALE" in source
    assert "float(abyssal.get_width()) * BAR_HEIGHT_SCALE *" in source
    assert "ABYSSAL_PREVIEW_SCALE" in source
    assert "use_art = _show_abyssal_bar()" in source
