from ..models.enums import Attribute, EssenceType


# =========================================================
#                      ESSENCE REWARDS
# =========================================================

def get_essence_type(monster):

    if monster.rarity not in (4, 5):
        return None

    if monster.attribute in (
        Attribute.IGNEOUS,
        Attribute.ABYSSAL,
        Attribute.STORM
    ):
        if monster.rarity == 4:
            return EssenceType.GLIMMERING

        return EssenceType.RADIANT

    if monster.attribute in (
        Attribute.AETHER,
        Attribute.VOID
    ):
        if monster.rarity == 4:
            return EssenceType.TWILIGHT

        return EssenceType.ECLIPSE

    return None


# =========================================================
#                    RESONANCE DUPES
# =========================================================

def get_compatible_dupes(target, collection):

    compatible_dupes = []

    for monster in collection:

        if target.can_resonate_with(monster):
            compatible_dupes.append(monster)

    return compatible_dupes

