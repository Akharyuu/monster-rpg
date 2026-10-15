"""Python compatibility view of the canonical shared monster roster.

Edit godot/data/monster_data.json, NOT this module, to change a monster.
Python callers keep importing MONSTER_DATA and receive Attribute enums.
Godot loads exactly the same JSON file using FileAccess.
"""

import json
from pathlib import Path

from ..models.enums import Attribute


SHARED_MONSTER_DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "godot"
    / "data"
    / "monster_data.json"
)


def load_monster_data():
    with SHARED_MONSTER_DATA_PATH.open(
        encoding="utf-8"
    ) as data_file:
        document = json.load(data_file)

    if document.get("schema_version") != 1:
        raise ValueError(
            "Unsupported shared monster data schema version"
        )

    records = document.get("monsters")

    if not isinstance(records, dict):
        raise ValueError(
            "Shared monster data must contain a 'monsters' object"
        )

    # Convert only the Attribute field back to the existing Python
    # enum. Everything else is sourced directly from the JSON.
    return {
        monster_id: {
            **record,
            "attribute": Attribute(
                record["attribute"].capitalize()
            )
        }
        for monster_id, record in records.items()
    }


MONSTER_DATA = load_monster_data()
