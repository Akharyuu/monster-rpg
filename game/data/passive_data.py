"""Compatibility view of shared Python/Godot passive definitions.

Edit godot/data/passive_data.json, not this file.
"""
import json
from pathlib import Path

SHARED_PASSIVE_DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "godot" / "data" / "passive_data.json"
)


def load_passive_data():
    with SHARED_PASSIVE_DATA_PATH.open(encoding="utf-8") as source:
        document = json.load(source)

    if document.get("schema_version") != 1:
        raise ValueError("Unsupported shared passive data schema version")

    records = document.get("passives")
    if not isinstance(records, dict):
        raise ValueError("Shared passive data must contain 'passives'")

    for passive_id, record in records.items():
        if not isinstance(record, dict) or not record.get("name"):
            raise ValueError(f"Invalid passive definition: {passive_id}")
    return records


PASSIVE_DATA = load_passive_data()
