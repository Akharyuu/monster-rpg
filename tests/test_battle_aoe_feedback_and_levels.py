"""AoE HUD damage timing and level numeral placement on elemental orbs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATTLE = ROOT / "godot/scenes/battle/battle_screen.gd"
HUD = ROOT / "godot/scenes/battle/monster_battle_hud.gd"


def test_aoe_is_distinguished_from_random_multihits():
    screen = BATTLE.read_text(encoding="utf-8")
    assert screen.count('str(skill.target_type) == "all_enemies"') == 2
    assert "simultaneous_aoe: bool = false" in screen
    assert "if simultaneous_aoe:" in screen
    assert "await _play_aoe_target_feedback(target_results)" in screen
    assert "await hud.play_damage_feedback(" in screen


def test_all_aoe_damage_numbers_start_before_the_shared_wait():
    screen = BATTLE.read_text(encoding="utf-8")
    aoe = screen.split("func _play_aoe_target_feedback(", 1)[1]
    aoe = aoe.split("func play_caster_feedback(", 1)[0]
    launch = aoe.split("for target_result in target_results:", 1)[1]
    launch = launch.split("if has_damage:", 1)[0]
    assert "hud.play_damage_feedback(" in launch
    assert "await hud.play_damage_feedback(" not in launch
    assert "MonsterBattleHUD.DAMAGE_FEEDBACK_SECONDS" in aoe
    assert "MonsterBattleHUD.STATUS_FEEDBACK_SECONDS" in aoe
    assert "for wave_index in range(max_notifications):" in aoe


def test_orb_levels_are_centred_and_fit_two_digits():
    hud = HUD.read_text(encoding="utf-8")
    assert "func _position_level_in_orb() -> void:" in hud
    assert "_position_level_in_orb()" in hud
    assert "level_label.visible = bar != null" in hud
    assert "level_label.text = str(bound_monster.level)" in hud
    assert "level_label.z_index = 12" in hud
    assert "digits.length() == 1" in hud
    assert "digits.length() == 2" in hud
    assert "orb_center - level_label.size / 2.0" in hud
    assert '"font_outline_color"' in hud


def test_existing_battle_bar_tuning_is_unchanged():
    hud = HUD.read_text(encoding="utf-8")
    assert "ABYSSAL_PREVIEW_SCALE := 0.90" in hud
    assert "FORCE_ABYSSAL_BAR_PREVIEW := true" in hud
    assert "HP_FILL_RECT := Rect2(0.226, 0.274, 0.7369, 0.213)" in hud
    assert "ENEMY_GAUGE_VERTICAL_OFFSET := -1.0" in hud
    assert "hp_bar.value = bound_monster.health" in hud
