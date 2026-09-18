from game.factories.glyph_factory import create_glyph
from game.factories.monster_factory import create_monster
from game.persistence.serializers import glyph_to_dict, inventory_to_dict, monster_to_dict, collection_to_dict, player_to_dict
from game.persistence.deserializers import glyph_from_dict, inventory_from_dict, monster_from_dict, collection_from_dict, player_from_dict
from game.systems.inventory import Inventory
from game.models.enums import EssenceType, SealstoneType
from game.systems.player import Player
from game.persistence.save_manager import save_player, load_player
from game.systems.resonance import update_resonance_kit

import pytest

def test_glyph_serialization_round_trip():

    original = create_glyph("legendary")
    original.glyph_level_upgrade(15)

    data = glyph_to_dict(original)

    loaded = glyph_from_dict(data)

    assert loaded is not original

    assert loaded.instance_id == original.instance_id
    assert loaded.slot_id == original.slot_id
    assert loaded.set_id == original.set_id
    assert loaded.main_stat == original.main_stat
    assert loaded.rarity == original.rarity
    assert loaded.level == original.level

    assert len(loaded.sub_stats) == len(original.sub_stats)

    for original_sub, loaded_sub in zip(
        original.sub_stats,
        loaded.sub_stats
    ):
        assert loaded_sub.stat == original_sub.stat
        assert loaded_sub.rolls == original_sub.rolls



def test_inventory_serialization_round_trip():

    original = Inventory()

    glyph_a = create_glyph("legendary")
    glyph_b = create_glyph("epic")

    original.add_glyph(glyph_a)
    original.add_glyph(glyph_b)

    data = inventory_to_dict(original)

    loaded = inventory_from_dict(data)

    assert len(loaded.glyphs) == 2

    loaded_a = loaded.get_glyph(glyph_a.instance_id)
    loaded_b = loaded.get_glyph(glyph_b.instance_id)

    assert loaded_a is not None
    assert loaded_b is not None

    assert loaded_a.instance_id == glyph_a.instance_id
    assert loaded_b.instance_id == glyph_b.instance_id

    assert glyph_a.instance_id in loaded.glyphs
    assert glyph_b.instance_id in loaded.glyphs


def test_inventory_items_serialization_round_trip():

    original = Inventory()

    original.add_item(
        EssenceType.RADIANT,
        7
    )

    original.add_item(
        SealstoneType.TWILIGHT,
        3
    )

    data = inventory_to_dict(original)

    loaded = inventory_from_dict(data)

    assert loaded.get_amount(EssenceType.RADIANT) == 7
    assert loaded.get_amount(SealstoneType.TWILIGHT) == 3


def test_monster_serialization_round_trip_with_glyph():

    inventory = Inventory()

    glyph = create_glyph("legendary")
    inventory.add_glyph(glyph)

    original = create_monster("drake_igneous")

    original.level = 12
    original.experience = 450
    original.resonance = 2

    original.equip_glyph(glyph)

    data = monster_to_dict(original)

    loaded = monster_from_dict(data, inventory)

    assert loaded.instance_id == original.instance_id
    assert loaded.monster_id == original.monster_id
    assert loaded.level == 12
    assert loaded.experience == 450
    assert loaded.resonance == 2

    loaded_glyph = loaded.glyphs[glyph.slot_id]

    assert loaded_glyph is glyph
    assert loaded_glyph is inventory.get_glyph(glyph.instance_id)


def test_collection_serialization_round_trip():

    inventory = Inventory()

    monster_a = create_monster("drake_igneous")
    monster_b = create_monster("drake_abyssal")

    original = [
        monster_a,
        monster_b
    ]

    data = collection_to_dict(original)

    loaded = collection_from_dict(
        data,
        inventory
    )

    assert len(loaded) == 2

    assert loaded[0].instance_id == monster_a.instance_id
    assert loaded[1].instance_id == monster_b.instance_id

    assert loaded[0].monster_id == monster_a.monster_id
    assert loaded[1].monster_id == monster_b.monster_id


def test_player_serialization_round_trip():

    original = Player("Ryuu")

    glyph = create_glyph("legendary")
    original.inventory.add_glyph(glyph)

    original.inventory.add_item(
        EssenceType.RADIANT,
        7
    )

    original.inventory.add_item(
        SealstoneType.TWILIGHT,
        3
    )

    monster = create_monster("drake_igneous")

    monster.level = 15
    monster.experience = 800

    monster.equip_glyph(glyph)

    original.collection.append(monster)

    data = player_to_dict(original)

    loaded = player_from_dict(data)

    assert loaded is not original

    assert loaded.name == "Ryuu"

    assert len(loaded.collection) == 1
    assert len(loaded.inventory.glyphs) == 1

    assert loaded.inventory.get_amount(
        EssenceType.RADIANT
    ) == 7

    assert loaded.inventory.get_amount(
        SealstoneType.TWILIGHT
    ) == 3

    loaded_monster = loaded.collection[0]

    assert loaded_monster.instance_id == monster.instance_id
    assert loaded_monster.monster_id == monster.monster_id
    assert loaded_monster.level == 15
    assert loaded_monster.experience == 800

    loaded_glyph = loaded.inventory.get_glyph(
        glyph.instance_id
    )

    assert loaded_glyph is not None

    assert (
        loaded_monster.glyphs[glyph.slot_id]
        is loaded_glyph
    )


def test_save_and_load_player_from_file(tmp_path):

    original = Player("Ryuu")

    monster = create_monster("drake_igneous")
    original.collection.append(monster)

    glyph = create_glyph("epic")
    original.inventory.add_glyph(glyph)

    monster.equip_glyph(glyph)

    save_path = tmp_path / "save.json"

    save_player(
        original,
        save_path
    )

    assert save_path.exists()

    loaded = load_player(save_path)

    assert loaded.name == original.name

    assert len(loaded.collection) == 1
    assert len(loaded.inventory.glyphs) == 1

    loaded_monster = loaded.collection[0]

    assert loaded_monster.instance_id == monster.instance_id

    loaded_glyph = loaded.inventory.get_glyph(
        glyph.instance_id
    )

    assert loaded_glyph is not None

    assert (
        loaded_monster.glyphs[glyph.slot_id]
        is loaded_glyph
    )


def test_monster_load_fails_if_glyph_does_not_exist():

    monster = create_monster("drake_igneous")

    data = monster_to_dict(monster)

    data["glyphs"]["1"] = "missing-glyph-id"

    inventory = Inventory()

    with pytest.raises(ValueError):
        monster_from_dict(
            data,
            inventory
        )


def test_monster_resonance_kit_is_restored():

    inventory = Inventory()

    original = create_monster("drake_igneous")

    original.resonance = 3
    update_resonance_kit(original)

    data = monster_to_dict(original)

    loaded = monster_from_dict(
        data,
        inventory
    )

    assert loaded.resonance == 3

    original_skills = [
        skill.skill_id
        for skill in original.skills
    ]

    loaded_skills = [
        skill.skill_id
        for skill in loaded.skills
    ]

    original_passives = [
        passive.skill_id
        for passive in original.passives
    ]

    loaded_passives = [
        passive.skill_id
        for passive in loaded.passives
    ]

    assert loaded_skills == original_skills
    assert loaded_passives == original_passives