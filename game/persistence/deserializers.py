from ..models.enums import EssenceType, SealstoneType
from ..models.glyphs import Glyph, GlyphSubstat

from ..factories.monster_factory import create_monster

from ..systems.inventory import Inventory
from ..systems.player import Player
from ..systems.resonance import update_resonance_kit


# =========================================================
#                         MAPPINGS
# =========================================================

ITEM_TYPE_MAP = {
    "EssenceType": EssenceType,
    "SealstoneType": SealstoneType
}


# =========================================================
#                          GLYPHS
# =========================================================

def glyph_from_dict(data):

    sub_stats = []

    for sub_stat_data in data["sub_stats"]:

        sub_stat = GlyphSubstat(
            stat=sub_stat_data["stat"],
            rolls=sub_stat_data["rolls"]
        )

        sub_stats.append(sub_stat)

    glyph = Glyph(
        instance_id=data["instance_id"],
        slot_id=data["slot_id"],
        set_id=data["set_id"],
        main_stat=data["main_stat"],
        sub_stats=sub_stats,
        rarity=data["rarity"],
        level=data["level"]
    )

    return glyph


# =========================================================
#                        INVENTORY
# =========================================================

def inventory_from_dict(data):

    inventory = Inventory()

    for item_data in data["items"]:

        enum_class = ITEM_TYPE_MAP[item_data["type"]]

        item = enum_class[item_data["id"]]

        inventory.add_item(
            item,
            item_data["amount"]
        )

    for glyph_data in data["glyphs"]:
        glyph = glyph_from_dict(glyph_data)
        inventory.add_glyph(glyph)

    return inventory


# =========================================================
#                         MONSTERS
# =========================================================

def monster_from_dict(data, inventory):

    monster = create_monster(
        data["monster_id"],
        instance_id=data["instance_id"]
    )

    monster.level = data["level"]
    monster.experience = data["experience"]
    monster.level_limit = data["level_limit"]
    monster.ascended = data["ascended"]
    monster.update_level_stats()
    
    monster.resonance = data["resonance"]
    update_resonance_kit(monster)


    for slot, glyph_id in data["glyphs"].items():

        if glyph_id is None:
            continue

        glyph = inventory.get_glyph(glyph_id)

        if glyph is None:
            raise ValueError(
                f"Glyph {glyph_id} not found in inventory"
            )

        monster.glyphs[int(slot)] = glyph

    return monster



def collection_from_dict(data, inventory):

    collection = []

    for monster_data in data["monsters"]:
        monster = monster_from_dict(monster_data, inventory)
        collection.append(monster)

    return collection


# =========================================================
#                          PLAYER
# =========================================================

def player_from_dict(data):

    inventory = inventory_from_dict(data["inventory"])

    collection = collection_from_dict(data["collection"], inventory)

    player = Player(data["name"])

    player.inventory = inventory
    player.collection = collection

    return player