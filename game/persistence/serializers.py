# =========================================================
#                          GLYPHS
# =========================================================

def glyph_to_dict(glyph):

    sub_stat_data = []

    for sub_stat in glyph.sub_stats:

        sub_stat_dict = {
            "stat": sub_stat.stat,
            "rolls": sub_stat.rolls
        }

        sub_stat_data.append(sub_stat_dict)

    glyph_data = {
        "instance_id": glyph.instance_id,
        "slot_id": glyph.slot_id,
        "set_id": glyph.set_id,
        "main_stat": glyph.main_stat,
        "rarity": glyph.rarity,
        "level": glyph.level,
        "sub_stats": sub_stat_data
    }

    return glyph_data


# =========================================================
#                         MONSTERS
# =========================================================

def monster_to_dict(monster):

    monster_glyphs = {}

    for slot, glyph in monster.glyphs.items():

        if glyph is None:
            monster_glyphs[str(slot)] = None

        else:
            monster_glyphs[str(slot)] = glyph.instance_id

    monster_data = {
        "instance_id": monster.instance_id,
        "monster_id": monster.monster_id,
        "level": monster.level,
        "experience": monster.experience,
        "level_limit": monster.level_limit,
        "ascended": monster.ascended,
        "resonance": monster.resonance,

        "glyphs": monster_glyphs
    }

    return monster_data


# =========================================================
#                        INVENTORY
# =========================================================

def inventory_to_dict(inventory):

    glyphs_data = []

    for glyph in inventory.glyphs.values():
        glyphs_data.append(glyph_to_dict(glyph))

    items_data = []

    for item, amount in inventory.items.items():

        item_data = {
            "type": type(item).__name__,
            "id": item.name,
            "amount": amount
        }

        items_data.append(item_data)

    inventory_data = {
        "items": items_data,
        "glyphs": glyphs_data
    }

    return inventory_data


# =========================================================
#                        COLLECTION
# =========================================================


def collection_to_dict(collection):

    monsters_data = []

    for monster in collection:

        monster_data = monster_to_dict(monster)
        monsters_data.append(monster_data)

    collection_data = {
        "monsters": monsters_data
    }

    return collection_data


# =========================================================
#                          PLAYER
# =========================================================

def player_to_dict(player):

    player_data = {
        "name": player.name,
        "collection": collection_to_dict(player.collection),
        "inventory": inventory_to_dict(player.inventory)
    }

    return player_data