import pytest
from game.factories.glyph_factory import create_glyph
from game.data.glyph_stat_data import GLYPH_STAT_DATA
from game.data.glyph_slot_data import GLYPH_SLOT_DATA
from game.models.glyphs import Glyph, GlyphSubstat
from game.factories.monster_factory import create_monster
from game.factories.status_effect_factory import create_status_effect
from math import ceil

RARITIES = ["common", "rare", "epic", "legendary"]


@pytest.mark.parametrize("rarity", RARITIES)
def test_glyph_starts_at_level_zero_with_four_substats(rarity):

    glyph = create_glyph(rarity)

    assert glyph.level == 0
    assert len(glyph.sub_stats) == 4


@pytest.mark.parametrize("rarity", RARITIES)
def test_glyph_substats_are_unique(rarity):

    glyph = create_glyph(rarity)

    sub_stats = []

    for sub_stat in glyph.sub_stats:
        sub_stats.append(sub_stat.stat)

    unique_sub_stats = set(sub_stats)

    assert len(unique_sub_stats) == 4


@pytest.mark.parametrize("rarity", RARITIES)
def test_glyph_main_stat_not_in_sub_stats(rarity):

    glyph = create_glyph(rarity)

    sub_stats = []

    for sub_stat in glyph.sub_stats:
        sub_stats.append(sub_stat.stat)

    assert glyph.main_stat not in sub_stats


@pytest.mark.parametrize("rarity", RARITIES)
def test_glyph_sub_stat_initial_roll_in_range_for_rarity(rarity):

    glyph = create_glyph(rarity)

    for sub_stat in glyph.sub_stats:

        max_roll = GLYPH_STAT_DATA[sub_stat.stat]["sub_roll_max"][glyph.rarity]
        min_roll = ceil(max_roll / 2)

        assert min_roll <= sub_stat.rolls[0] <= max_roll


@pytest.mark.parametrize("rarity", RARITIES)
def test_glyph_cannot_upgrade_above_level_15(rarity):

    glyph = create_glyph(rarity)

    glyph.glyph_level_upgrade(20)

    assert glyph.level == 15


@pytest.mark.parametrize("rarity", RARITIES)
def test_glyph_has_ten_total_rolls_at_level_15(rarity):

    glyph = create_glyph(rarity)

    glyph.glyph_level_upgrade(15)

    total_rolls = 0

    for sub_stat in glyph.sub_stats:
        total_rolls += len(sub_stat.rolls)

    assert total_rolls == 10


@pytest.mark.parametrize("rarity", RARITIES)
def test_glyph_last_sub_stat_roll_is_double(rarity):

    glyph = create_glyph(rarity)

    glyph.glyph_level_upgrade(14)

    sub_stat_rolls_14 = {}
    sub_stat_rolls_15 = {}

    for sub_stat in glyph.sub_stats:
        sub_stat_rolls_14[sub_stat.stat] = len(sub_stat.rolls)

    glyph.glyph_level_upgrade(15)

    for sub_stat in glyph.sub_stats:
        sub_stat_rolls_15[sub_stat.stat] = len(sub_stat.rolls)

    roll_differences = []

    for stat in sub_stat_rolls_14:
        difference = (
            sub_stat_rolls_15[stat]
            - sub_stat_rolls_14[stat]
        )

        roll_differences.append(difference)

    assert sorted(roll_differences) == [0, 0, 0, 2]


@pytest.mark.parametrize("rarity", RARITIES)
def test_glyph_main_stat_in_valid_slot(rarity):

    glyph = create_glyph(rarity)

    assert glyph.main_stat in GLYPH_SLOT_DATA[glyph.slot_id]["main_stats"]


@pytest.mark.parametrize("rarity", RARITIES)
def test_glyph_main_stat_reaches_main_max_at_15(rarity):

    glyph = create_glyph(rarity)

    glyph.glyph_level_upgrade(15)

    assert glyph.main_value == GLYPH_STAT_DATA[glyph.main_stat]["main_max"][glyph.rarity]


@pytest.mark.parametrize("rarity", RARITIES)
def test_glyph_sub_stat_rolls_happen_at_designed_levels(rarity):

    glyph = create_glyph(rarity)

    expected_pattern = {
        0: 4,
        1: 4,
        2: 4,
        3: 5,
        4: 5,
        5: 5,
        6: 6,
        7: 6,
        8: 6,
        9: 7,
        10: 7,
        11: 7,
        12: 8,
        13: 8,
        14: 8,
        15: 10
    }

    actual_pattern = {}

    while True:

        total_rolls = 0

        for sub_stat in glyph.sub_stats:
            total_rolls += len(sub_stat.rolls)

        actual_pattern[glyph.level] = total_rolls

        if glyph.level == 15:
            break

        glyph.glyph_level_upgrade(1)

    assert actual_pattern == expected_pattern


@pytest.mark.parametrize("rarity", RARITIES)
def test_all_glyph_rolls_stay_in_rarity_range(rarity):

    glyph = create_glyph(rarity)
    glyph.glyph_level_upgrade(15)

    for sub_stat in glyph.sub_stats:

        max_roll = GLYPH_STAT_DATA[sub_stat.stat]["sub_roll_max"][rarity]
        min_roll = ceil(max_roll / 2)

        for roll in sub_stat.rolls:
            assert min_roll <= roll <= max_roll


def test_equip_glyph_places_it_in_correct_slot():

    monster = create_monster("drake_igneous")
    glyph = create_glyph("legendary")

    monster.equip_glyph(glyph)

    assert monster.glyphs[glyph.slot_id] is glyph


def test_replace_and_unequip_glyph():

    monster = create_monster("drake_igneous")

    glyph_a = Glyph(
        instance_id="test_glyph_1",
        slot_id=1,
        set_id="fury",
        main_stat="HP",
        sub_stats=[],
        rarity="legendary"
    )

    glyph_b = Glyph(
        instance_id="test_glyph_2",
        slot_id=1,
        set_id="velocity",
        main_stat="ATK",
        sub_stats=[],
        rarity="legendary"
    )

    first_replaced = monster.equip_glyph(glyph_a)

    assert first_replaced is None
    assert monster.glyphs[1] is glyph_a

    replaced_glyph = monster.equip_glyph(glyph_b)

    assert replaced_glyph is glyph_a
    assert monster.glyphs[1] is glyph_b

    unequipped_glyph = monster.unequip_glyph(1)

    assert unequipped_glyph is glyph_b
    assert monster.glyphs[1] is None


def test_equipped_stats_include_flat_percent_and_direct_bonuses():

    monster = create_monster("drake_igneous")

    glyph_1 = Glyph(
        instance_id="test_glyph_1",
        slot_id=1,
        set_id="predator",
        main_stat="ATK",
        sub_stats=[
            GlyphSubstat("ATK%", [8]),
            GlyphSubstat("SPD", [6]),
            GlyphSubstat("CR", [5]),
            GlyphSubstat("HP%", [7])
        ],
        rarity="legendary",
        level=15
    )

    glyph_2 = Glyph(
        instance_id="test_glyph_2",
        slot_id=2,
        set_id="predator",
        main_stat="ATK%",
        sub_stats=[
            GlyphSubstat("ATK", [70]),
            GlyphSubstat("SPD", [5]),
            GlyphSubstat("CR", [4]),
            GlyphSubstat("CDM", [8])
        ],
        rarity="legendary",
        level=15
    )

    monster.equip_glyph(glyph_1)
    monster.equip_glyph(glyph_2)

    expected_attack = monster.attack * 1.78 + 670
    expected_speed = monster.speed + 11
    expected_crit_rate = monster.crit_rate + 9

    assert monster.get_equipped_stat("attack") == pytest.approx(expected_attack)
    assert monster.get_equipped_stat("speed") == pytest.approx(expected_speed)
    assert monster.get_equipped_stat("crit_rate") == pytest.approx(expected_crit_rate)


def test_effective_stat_applies_buff_after_glyph_stats():

    monster = create_monster("drake_igneous")

    glyph = Glyph(
        instance_id="test_glyph_1",
        slot_id=2,
        set_id="predator",
        main_stat="ATK%",
        sub_stats=[
            GlyphSubstat("ATK", [70]),
            GlyphSubstat("SPD", [5]),
            GlyphSubstat("CR", [4]),
            GlyphSubstat("CDM", [8])
        ],
        rarity="legendary",
        level=15
    )

    monster.equip_glyph(glyph)

    equipped_attack = monster.get_equipped_stat("attack")

    attack_up = create_status_effect(
        "attack_up",
        duration=2,
        source=monster
    )

    monster.apply_status_effect(attack_up)

    expected_attack = equipped_attack * 1.30

    assert monster.get_effective_stat("attack") == pytest.approx(expected_attack)


def test_glyphs_have_unique_instance_ids():
    glyph_a = create_glyph("legendary")
    glyph_b = create_glyph("legendary")

    assert glyph_a.instance_id != glyph_b.instance_id