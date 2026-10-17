"""Contract tests for reversible targeting in Godot's player battle HUD."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATTLE = ROOT / "godot" / "scenes" / "battle" / "battle_screen.gd"
MONSTER_HUD = ROOT / "godot" / "scenes" / "battle" / "monster_battle_hud.gd"


def _block(source, start, end):
    return source.split(start, 1)[1].split(end, 1)[0]


def test_skill_selection_never_auto_executes():
    source = BATTLE.read_text(encoding="utf-8")
    select = _block(
        source, "func request_player_skill(slot: int) -> void:",
        "func _cancel_pending_targeting() -> void:"
    )
    for forbidden in (
        "execute_player_skill(", "action_in_progress = true",
        "await ", "preview_aoe_targets(", "execute_active_skill("
    ):
        assert forbidden not in select
    assert "_show_skill_target_choices(target_type)" in select
    assert "if pending_skill_slot == slot" in select
    assert "_cancel_pending_targeting()" in select
    assert "pending_special_action = \"\"" in select


def test_reselection_and_cancellation_do_not_consume_turn():
    source = BATTLE.read_text(encoding="utf-8")
    cancel = _block(
        source, "func _cancel_pending_targeting() -> void:",
        "func _clear_target_modes() -> void:"
    )
    assert "pending_skill_slot = 0" in cancel
    assert "pending_special_action = \"\"" in cancel
    assert "_clear_target_modes()" in cancel
    assert "update_skill_buttons()" in cancel
    assert "battle_controller.end_active_turn()" not in cancel
    confirm = _block(
        source, "func _confirm_pending_skill(targets: Array) -> void:",
        "func _on_ally_target_pressed(index: int) -> void:"
    )
    assert "action_in_progress = true" in confirm
    assert "pending_skill_slot = 0" in confirm
    assert "execute_player_skill(skill, targets)" in confirm


def test_all_skill_target_types_require_explicit_click():
    source = BATTLE.read_text(encoding="utf-8")
    choices = _block(
        source, "func _show_skill_target_choices(target_type: String) -> void:",
        "func _target_selection_message(target_type: String) -> String:"
    )
    for kind in (
        '"single_enemy"', '"all_enemies"', '"random_enemies"',
        '"all_allies"', '"single_ally"', '"self"'
    ):
        assert kind in choices

    enemy_click = _block(
        source, "func _on_enemy_target_pressed(index: int) -> void:",
        "func execute_player_skill("
    )
    ally_click = _block(
        source, "func _on_ally_target_pressed(index: int) -> void:",
        "func _on_enemy_target_pressed(index: int) -> void:"
    )
    assert '"all_enemies", "random_enemies"' in enemy_click
    assert "_confirm_pending_skill(battle_controller.get_living(enemies))" in enemy_click
    assert "_confirm_pending_skill(battle_controller.get_living(allies))" in ally_click
    assert "if target == battle_controller.active_monster:" in ally_click


def test_team_target_mode_accepts_a_click_on_any_living_member():
    source = MONSTER_HUD.read_text(encoding="utf-8")
    target = _block(
        source, "func set_target_mode(mode: String) -> void:",
        "func _update_target_style() -> void:"
    )
    assert 'target_mode == "team"' in target
    assert "bound_monster.is_alive()" in target
    assert 'target_prompt.text = "TEAM"' in target
    assert "target_button.visible = can_target" in target


def test_soul_recall_stays_reversible_and_can_be_switched():
    source = BATTLE.read_text(encoding="utf-8")
    recall = _block(
        source, "func _on_soul_recall_pressed(button_index: int) -> void:",
        "func set_target_selection(enabled: bool) -> void:"
    )
    assert "_cancel_pending_targeting()" in recall
    assert 'pending_special_action = "soul_recall"' in recall
    assert "action_in_progress = true" not in recall
    assert "set_revive_target_selection(true)" in recall
