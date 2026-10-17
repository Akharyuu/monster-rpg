"""Keep shared battle skill/passive icon sizing and spacing consistent."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "godot/scenes/battle/battle_screen.tscn"
BUTTON_SCRIPT = ROOT / "godot/scenes/battle/skill_button.gd"

BUTTON_NAMES = (
    "Skill 1 Button",
    "Skill 2 Button",
    "Skill 3 Button",
    "Passive Button",
    "Passive Button 2",
    "Passive Button 3",
)


def _rect(scene: str, name: str):
    match = re.search(
        r'^\[node name="' + re.escape(name) + r'".*?\]$(.*?)(?=^\[node |\Z)',
        scene, re.MULTILINE | re.DOTALL
    )
    assert match is not None, name
    body = match.group(1)
    return [
        float(re.search(r"^" + key + r" = ([-.\d]+)$", body, re.MULTILINE).group(1))
        for key in ("offset_left", "offset_top", "offset_right", "offset_bottom")
    ]


def test_skill_passive_buttons_reduced_by_twenty_five_percent():
    scene = SCENE.read_text(encoding="utf-8")
    for name in BUTTON_NAMES:
        x1, y1, x2, y2 = _rect(scene, name)
        assert x2 - x1 == 81
        assert y2 - y1 == 81


def test_skill_passive_artwork_scales_and_does_not_overlap():
    scene = SCENE.read_text(encoding="utf-8")
    script = BUTTON_SCRIPT.read_text(encoding="utf-8")

    # A 4.5px overhang on either side gives 90px painted artwork.
    assert "_icon_preview.offset_left = -4.5" in script
    assert "_icon_preview.offset_top = -4.5" in script
    assert "_icon_preview.offset_right = 4.5" in script
    assert "_icon_preview.offset_bottom = 4.5" in script

    left_edges = []
    right_edges = []
    for name in BUTTON_NAMES:
        x1, y1, x2, y2 = _rect(scene, name)
        left_edges.append(x1 - 4.5)
        right_edges.append(x2 + 4.5)
        assert y2 + 4.5 <= 720

    assert all(a < b for a, b in zip(right_edges, left_edges[1:]))
    options_x1 = _rect(scene, "Options Button")[0]
    assert right_edges[-1] < options_x1
