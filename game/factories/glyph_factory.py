import random

from math import ceil
from uuid import uuid4

from ..data.glyph_set_data import GLYPH_SET_DATA
from ..data.glyph_slot_data import GLYPH_SLOT_DATA
from ..data.glyph_stat_data import (
    GLYPH_STAT_DATA,
    GLYPH_SUBSTATS
)

from ..models.glyphs import (
    Glyph,
    GlyphSubstat
)


# =========================================================
#                     GLYPH CREATION
# =========================================================

def create_glyph(rarity, instance_id=None):

    if instance_id is None:
        instance_id = str(uuid4())

    slot_id = random.choice(list(GLYPH_SLOT_DATA.keys()))

    set_id = random.choice(list(GLYPH_SET_DATA.keys()))

    main_stat = random.choice(GLYPH_SLOT_DATA[slot_id]["main_stats"])

    glyph = Glyph(
        instance_id=instance_id,
        slot_id=slot_id,
        set_id=set_id,
        main_stat=main_stat,
        sub_stats=create_sub_stats(main_stat, rarity),
        rarity=rarity
    )

    return glyph


# =========================================================
#                    SUBSTAT CREATION
# =========================================================

def create_sub_stats(main_stat, rarity):
    sub_stats = []

    stat_pool = GLYPH_SUBSTATS.copy()
    stat_pool.remove(main_stat)

    for _ in range(4):
        random_stat = random.choice(stat_pool)

        max_roll = GLYPH_STAT_DATA[random_stat]["sub_roll_max"][rarity]
        min_roll = ceil(max_roll / 2)

        random_roll = random.randint(min_roll, max_roll)

        sub_stat = GlyphSubstat(
            stat=random_stat,
            rolls=[random_roll]
        )

        stat_pool.remove(random_stat)

        sub_stats.append(sub_stat)

    return sub_stats
