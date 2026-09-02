from .enums import Attribute, EssenceType

def resonate_monster(target, dupe, collection):
    if target.can_resonate_with(dupe):
        target.increase_resonance()
        collection.remove(dupe)
        return True
    
    return False


def get_essence_type(monster):
    if monster.attribute in (
        Attribute.IGNEOUS,
        Attribute.ABYSSAL,
        Attribute.STORM
    ):
        if monster.rarity == 4:
            return EssenceType.GLIMMERING
    
        elif monster.rarity == 5:
            return EssenceType.RADIANT
    
    elif monster.attribute in (
        Attribute.AETHER,
        Attribute.VOID
    ):
        if monster.rarity == 4:
            return EssenceType.TWILIGHT
    
        elif monster.rarity == 5:
            return EssenceType.ECLIPSE

    return None


def dismantle_monster(monster, collection, inventory):
    essence_type = get_essence_type(monster)

    if essence_type is None:
        return None

    if monster in collection:
        collection.remove(monster)
        inventory.add_item(essence_type)
        return essence_type
    
    return None


def get_compatible_dupes(target, collection):
    dupe_list = []

    for monster in collection:
        if target.can_resonate_with(monster):
            dupe_list.append(monster)

    return dupe_list