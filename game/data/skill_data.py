"""Python compatibility view of shared skill data; edit godot/data/skill_data.json."""
import json
from pathlib import Path

from ..models.enums import SkillType, TargetType


SHARED_SKILL_DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "godot"
    / "data"
    / "skill_data.json"
)

_INTEGER_KEYED_FIELDS = frozenset({
    "multipliers_by_hit",
    "multipliers_by_stacks",
    "heal_by_stacks",
})


def _restore_integer_keys(value):
    """Convert JSON lookup-map keys back to Python integers."""
    if isinstance(value, list):
        return [_restore_integer_keys(item) for item in value]

    if not isinstance(value, dict):
        return value

    result = {}
    for key, item in value.items():
        if key in _INTEGER_KEYED_FIELDS and isinstance(item, dict):
            result[key] = {
                int(number): _restore_integer_keys(nested)
                for number, nested in item.items()
            }
        else:
            result[key] = _restore_integer_keys(item)

    return result


def load_skill_data():
    with SHARED_SKILL_DATA_PATH.open(encoding="utf-8") as data_file:
        document = json.load(data_file)

    if document.get("schema_version") != 1:
        raise ValueError("Unsupported shared skill data schema version")

    records = document.get("skills")
    if not isinstance(records, dict):
        raise ValueError("Shared skill data must contain a 'skills' object")

    loaded = {}
    for skill_id, raw in records.items():
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid shared skill definition: {skill_id}")
        entry = _restore_integer_keys(raw)
        entry["type"] = SkillType[raw["type"].upper()]
        entry["target_type"] = TargetType[raw["target_type"].upper()]
        loaded[skill_id] = entry

    return loaded


SKILL_DATA = load_skill_data()
