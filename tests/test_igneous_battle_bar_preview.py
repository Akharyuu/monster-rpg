"""Contracts for optional, shared 36-frame Igneous monster HUD art."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUD = ROOT / "godot" / "scenes" / "battle" / "monster_battle_hud.gd"


def test_igneous_sprite_only_replaces_igneous_attribute_bars():
    source = HUD.read_text(encoding="utf-8")
    assert '"res://assets/ui/sprite-max-px-frames-36-rows-6-cols-6.json"' in source
    assert 'str(bound_monster.attribute) == "igneous"' in source
    assert "_load_igneous_bar_animation()" in source
    assert "hp_bar.visible = not use_art" in source
    assert "action_gauge.visible = not use_art" in source


def test_animation_uses_all_frames_and_json_durations():
    source = HUD.read_text(encoding="utf-8")
    assert 'IGNEOUS_BAR_FRAME_COUNT := 36' in source
    assert '"frame_%03d" % i' in source
    assert 'float(item.get("duration", 104))' in source
    assert "ratio_x" in source and "ratio_y" in source
    assert "AtlasTexture.new()" in source
    assert "atlas.atlas = sheet" in source
    assert "crop_top" in source and "crop_bottom" in source
    assert "func _process(delta: float) -> void:" in source
    assert "_igneous_elapsed_ms += delta * 1000.0" in source
    assert "_igneous_bar_art.texture = _igneous_bar_frames[_igneous_frame_index]" in source
    assert "_igneous_bar_width" not in source  # constants are immutable


def test_bar_is_centered_above_actual_opaque_sprite_pixels():
    source = HUD.read_text(encoding="utf-8")
    assert "func _sprite_visual_top_center() -> Vector2:" in source
    assert "pixels.get_used_rect()" in source
    assert "monster_sprite.size - image_size * scale" in source
    assert "func _position_igneous_bar() -> void:" in source
    assert "visual_top.y - _igneous_bar_art.size.y - IGNEOUS_BAR_GAP" in source
    assert "IGNEOUS_BAR_WIDTH := 228.0" in source
    assert "BAR_ORIGINAL_WIDTH := 284.0" in source
    assert "BAR_ORIGINAL_WIDTH * float(common_height)" in source
    assert "_position_igneous_bar()" in source


def test_hp_and_gauge_values_still_update_despite_cosmetic_animated_art():
    source = HUD.read_text(encoding="utf-8")
    assert "hp_bar.value = bound_monster.health" in source
    assert "bound_monster.action_gauge * 100.0" in source
    assert "hp_bar.max_value = monster.max_health" in source
    assert "action_gauge.max_value = 100.0" in source
