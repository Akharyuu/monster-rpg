"""The 4v4 enemy formation moves full monster HUDs, not just their bars."""
import re
from pathlib import Path

SCREEN = Path(__file__).resolve().parents[1] / "godot/scenes/battle/battle_screen.gd"


def test_enemy_4v4_shifts_are_cumulative_and_preserve_enemy_four():
    source = SCREEN.read_text(encoding="utf-8")
    enemy_arcs = source.split("const ENEMY_ARCS := {", 1)[1]
    positions = enemy_arcs.split("\n\t4: [", 1)[1].split("\n\t]", 1)[0]
    actual = [
        tuple(map(int, coordinates))
        for coordinates in re.findall(r"Vector2\((\d+), (\d+)\)", positions)
    ]
    assert actual == [
        (548, 142),  # enemy 1: 578 - 15 - 15
        (724, 124),  # enemy 2: 754 - 15 - 15
        (896, 124),  # enemy 3: 911 - 15
        (1063, 174),  # enemy 4: unchanged
    ]


def test_formation_moves_parent_huds_so_sprites_and_bars_follow():
    source = SCREEN.read_text(encoding="utf-8")
    assert "_layout_team_huds(enemy_huds, enemies.size())" in source
    assert "combat_hud.position = positions[index]" in source
    assert "enemy_huds[index].bind_monster(" in source
