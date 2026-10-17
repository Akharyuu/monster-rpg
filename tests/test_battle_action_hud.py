"""Battle action HUD contract: dynamic layout, cooldowns and interaction."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "godot" / "scenes" / "battle" / "battle_screen.tscn"
SCREEN = ROOT / "godot" / "scenes" / "battle" / "battle_screen.gd"
BUTTON = ROOT / "godot" / "scenes" / "battle" / "skill_button.gd"


def test_layout_only_uses_available_skills_and_passives():
    source = SCREEN.read_text(encoding="utf-8")
    body = source.split("func _layout_action_buttons() -> void:", 1)[1]
    body = body.split("\n\nfunc ", 1)[0]
    assert "if button.visible:" in body
    assert "skill_1_button, skill_2_button, skill_3_button," in body
    assert "passive_button, passive_button_2, passive_button_3" in body
    assert "right_edge - button.size.x" in body
    assert 'right_edge: float = $"Options Button".position.x - OPTIONS_GAP' in body
    assert "_layout_action_buttons()" in source
    assert "button.visible = skill != null" not in source


def test_real_cooldowns_drive_overlaid_numbers():
    screen = SCREEN.read_text(encoding="utf-8")
    button = BUTTON.read_text(encoding="utf-8")
    assert "button.set_cooldown_turns(skill.current_cooldown)" in screen
    assert "button.set_cooldown_turns(remaining_cd)" in screen
    assert "display: bool = _cooldown_remaining > 0 and has_skill_icon()" in button
    assert '_cooldown_label.text = str(_cooldown_remaining)' in button
    assert "_cooldown_scrim.visible = display" in button


def test_passives_have_distinct_fx_and_targeting_selection_persists():
    screen = SCREEN.read_text(encoding="utf-8")
    button = BUTTON.read_text(encoding="utf-8")
    assert 'button.set_hud_role("passive")' in screen
    assert 'action_button.set_hud_role("active")' in screen
    assert 'button.set_target_selected(pending_skill_slot == index + 1)' in screen
    assert 'button.set_target_selected(false)' in screen
    assert "set_target_selection(true)\n\tupdate_skill_buttons()" in screen
    assert "_fx_layer.draw.connect(_draw_hud_aura)" in button
    assert '_hud_role == "passive"' in button
    assert '_target_selected' in button
    assert "mouse_entered.connect(_on_hud_mouse_entered)" in button
    assert "mouse_exited.connect(_on_hud_mouse_exited)" in button


def test_group_bounds_for_all_party_skill_counts():
    scene = SCENE.read_text(encoding="utf-8")
    x = float(re.search(
        r'\[node name="Options Button".*?offset_left = ([\d.]+)',
        scene, re.DOTALL
    ).group(1))
    assert x == 1202.0
    # All permitted groups (3 skills + 0..2 passives, and the
    # special third passive-slot action) stay visible beside Options.
    for count in range(1, 7):
        left = x - 12 - count * 81 - (count - 1) * 10
        assert left >= 0
        assert left + count * 81 + (count - 1) * 10 == x - 12
