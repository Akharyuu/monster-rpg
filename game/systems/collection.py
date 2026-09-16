from ..models.enums import Attribute, EssenceType

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


def get_compatible_dupes(target, collection):
    dupe_list = []

    for monster in collection:
        if target.can_resonate_with(monster):
            dupe_list.append(monster)

    return dupe_list