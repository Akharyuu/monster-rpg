"""Contracts for animated textured monster HP and action gauge fills."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUD = ROOT / "godot/scenes/battle/monster_battle_hud.gd"
SHADER = ROOT / "godot/assets/ui/battle_bar_fill.gdshader"
ASSETS = ROOT / "godot/assets/ui"


def test_bar_fill_art_is_versioned_and_used_by_abyssal_preview():
    source = HUD.read_text(encoding="utf-8")
    assert (ASSETS / "hp_fill.png").is_file()
    assert (ASSETS / "gauge_fill.png").is_file()
    assert 'preload("res://assets/ui/hp_fill.png")' in source
    assert 'preload("res://assets/ui/gauge_fill.png")' in source
    assert "func _ensure_dynamic_fills() -> void:" in source
    assert "_position_dynamic_fills()" in source
    assert "HP_FILL_RECT" in source and "GAUGE_FILL_RECT" in source


def test_individual_shaders_clip_without_shrinking_textures():
    source = HUD.read_text(encoding="utf-8")
    material = SHADER.read_text(encoding="utf-8")
    assert "ShaderMaterial.new()" in source
    assert 'mask.set_shader_parameter("fill_ratio", 1.0)' in source
    assert 'material, "shader_parameter/fill_ratio", target, duration' in source
    assert 'uniform float fill_ratio' in material
    assert "COLOR.a *= visible;" in material
    assert "UV.x" in material


def test_damage_has_delayed_trail_healing_and_gauge_animate():
    source = HUD.read_text(encoding="utf-8")
    assert "_hp_fill_tween = _animate_fill(" in source
    assert "_hp_trail_tween = _animate_fill(" in source
    assert "HP_DAMAGE_TRAIL_DELAY" in source
    assert "HP_HEAL_DURATION" in source
    assert "_gauge_fill_tween = _animate_fill(" in source
    assert "bound_monster.health" in source
    assert "bound_monster.max_health" in source
    assert "bound_monster.action_gauge" in source
    assert "if not _fills_initialized:" in source
    assert "_stop_fill_tweens()" in source
    assert "_refresh_dynamic_fills()" in source


def test_legacy_progressbars_still_store_real_values():
    source = HUD.read_text(encoding="utf-8")
    assert "hp_bar.value = bound_monster.health" in source
    assert "bound_monster.action_gauge * 100.0" in source
    assert "hp_bar.visible = not use_art" in source
    assert "action_gauge.visible = not use_art" in source
