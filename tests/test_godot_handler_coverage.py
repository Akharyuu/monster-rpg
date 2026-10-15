"""Port gate: every active JSON handler needs a Godot execution adapter.

This is a conservative static contract, NOT proof that every mechanic has
full Python/Godot behavioral parity. The headless combat smoke covers
representative execution paths.
"""
from pathlib import Path

from game.data.monster_data import MONSTER_DATA
from game.data.passive_data import PASSIVE_DATA
from game.data.resonance_data import RESONANCE_DATA
from game.data.skill_data import SKILL_DATA


ROOT = Path(__file__).resolve().parents[1]
GODOT_CODE = (
    "godot/scripts/models/skill.gd",
    "godot/scripts/models/damage_skill.gd",
    "godot/scripts/models/support_skill.gd",
    "godot/scripts/models/monster.gd",
    "godot/scripts/factories/prototype_factory.gd",
    "godot/scripts/battle/battle_controller.gd",
)


def _gd_source():
    return "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in GODOT_CODE
    )


def test_all_canonical_skill_handler_types_have_godot_adapters():
    defined = set()
    for record in SKILL_DATA.values():
        if record.get("damage_handler"):
            defined.add(record["damage_handler"])
        for phase in (
            "before_hit_handlers", "on_hit_handlers",
            "after_skill_handlers", "after_use_handlers"
        ):
            defined.update(
                config["handler"] for config in record.get(phase, [])
            )

    assert len(defined) >= 33
    source = _gd_source()
    missing = sorted(handler for handler in defined if handler not in source)
    assert not missing, (
        "Handler names have no Godot adapter reference; implement and "
        f"test them before using the new JSON schema: {missing}"
    )


def _active_passive_ids():
    active = set()
    for monster in MONSTER_DATA.values():
        active.update(monster.get("passives", []))

    for monster_id, levels in RESONANCE_DATA.items():
        current = list(MONSTER_DATA[monster_id].get("passives", []))
        for rank in range(1, 6):
            for action in levels.get(rank, []):
                if action["action"] == "add_passive":
                    current.append(action["passive"])
                elif action["action"] == "replace_passive":
                    index = current.index(action["old"])
                    current[index] = action["new"]
            active.update(current)
    return active


def test_all_active_passive_handler_types_have_godot_adapters():
    active_ids = _active_passive_ids()
    assert len(active_ids) >= 24
    handlers = {
        PASSIVE_DATA[passive_id]["handler"]
        for passive_id in active_ids
        if PASSIVE_DATA[passive_id].get("handler")
    }
    source = _gd_source()
    missing = sorted(handler for handler in handlers if handler not in source)
    assert not missing, (
        "A playable passive handler is not mentioned in Godot code: "
        f"{missing}"
    )


def test_inactive_passive_is_not_claimed_playable():
    # Existing old definitions may have no current upgrade path.
    assert "frostborne_shattered_fury" not in _active_passive_ids()
