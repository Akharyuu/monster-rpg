"""Compatibility view of shared Python/Godot Resonance upgrade rules.

Edit godot/data/resonance_data.json, not this file. Numeric level keys
are converted back to integers for compatibility with Python callers.
"""
import json
from pathlib import Path

SHARED_RESONANCE_DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "godot" / "data" / "resonance_data.json"
)


def load_resonance_data():
    with SHARED_RESONANCE_DATA_PATH.open(encoding="utf-8") as source:
        document = json.load(source)

    if document.get("schema_version") != 1:
        raise ValueError("Unsupported shared resonance data schema version")

    records = document.get("resonances")
    if not isinstance(records, dict):
        raise ValueError("Shared resonance data must contain 'resonances'")

    return {
        monster_id: {int(level): actions for level, actions in levels.items()}
        for monster_id, levels in records.items()
    }


RESONANCE_DATA = load_resonance_data()
