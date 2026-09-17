from .models.glyphs import Glyph, GlyphSubstat
from .data.glyph_stat_data import GLYPH_SUBSTATS, GLYPH_STAT_DATA
from .data.glyph_set_data import GLYPH_SET_DATA
from .data.glyph_slot_data import GLYPH_SLOT_DATA
import random
from math import ceil

def create_glyph(rarity):

    slot_id = random.choice(list(GLYPH_SLOT_DATA.keys()))

    set_id = random.choice(list(GLYPH_SET_DATA.keys()))

    main_stat = random.choice(GLYPH_SLOT_DATA[slot_id]["main_stats"])

    glyph = Glyph(
        slot_id=slot_id,
        set_id=set_id,
        main_stat=main_stat,
        sub_stats=create_sub_stats(main_stat, rarity),
        rarity=rarity
    )

    return glyph


def create_sub_stats(main_stat, rarity):
    sub_stats = []

    stat_pool = GLYPH_SUBSTATS.copy()
    stat_pool.remove(main_stat)

    for i in range(4):
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


if __name__ == "__main__":
    glyph = create_glyph("legendary")

    print("\n=== GLYPH INICIAL ===")
    print("Slot:", glyph.slot_id)
    print("Set:", glyph.set_id)
    print("Main:", glyph.main_stat, glyph.main_value)
    print("Level:", glyph.level)

    print("Subs:")
    for sub_stat in glyph.sub_stats:
        print(sub_stat.stat, sub_stat.rolls)

    for target_level in [2, 3, 6, 9, 12, 15]:
        glyph.glyph_level_upgrade(target_level - glyph.level)

        print(f"\n=== GLYPH +{glyph.level} ===")
        print("Main:", glyph.main_stat, glyph.main_value)

        for sub_stat in glyph.sub_stats:
            print(
                sub_stat.stat,
                sub_stat.rolls,
                "Total:", sub_stat.total_value
            )