"""Smoke-contract for the optional ally sprite preview scene."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "godot"


def test_ally_sprite_is_bound_by_monster_id_and_side():
    script = (
        GODOT / "scenes" / "battle" / "monster_battle_hud.gd"
    ).read_text(encoding="utf-8")
    scene = (
        GODOT / "scenes" / "battle" / "monster_battle_hud.tscn"
    ).read_text(encoding="utf-8")
    assert '"drake_igneous"' in script
    assert 'res://assets/monster_sprites/drake_igneous.png' in script
    assert 'bound_monster == null or is_enemy' in script
    assert 'ResourceLoader.exists(sprite_path, "Texture2D")' in script
    assert '_update_monster_sprite()' in script
    assert '[node name="Monster Sprite" type="TextureRect"' in scene
    assert 'mouse_filter = 2' in scene


def test_preview_is_main_scene_without_overwriting_original_roster():
    project = (GODOT / "project.godot").read_text(encoding="utf-8")
    preview = (
        GODOT / "scenes" / "battle" / "igneous_drake_preview.tscn"
    ).read_text(encoding="utf-8")
    battle = (
        GODOT / "scenes" / "battle" / "battle_screen.gd"
    ).read_text(encoding="utf-8")
    assert 'igneous_drake_preview.tscn' in project
    assert 'battle_screen.tscn' in preview
    assert 'preview_igneous_drake = true' in preview
    assert '@export var preview_igneous_drake: bool = false' in battle
    assert '"drake_igneous" if preview_igneous_drake' in battle
    assert '"dullahan_aether"' in battle
