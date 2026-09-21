from game.factories.monster_factory import create_monster
from game.persistence.serializers import monster_to_dict
from game.persistence.deserializers import monster_from_dict
from game.systems.inventory import Inventory
from game.data.monster_data import MONSTER_DATA
from game.data.stat_growth_data import LEVEL_STAT_MULTIPLIER, ASCENDED_STAT_MULTIPLIER
from game.data.experience_data import RARITY_EXP_MULTIPLIER, BASE_EXP_YIELD

import pytest

def test_monsters_have_unique_instance_ids():

    monster_a = create_monster("drake_igneous")
    monster_b = create_monster("drake_igneous")

    assert monster_a.instance_id != monster_b.instance_id


def test_existing_instance_id_is_preserved():
    saved_id = "test_saved_instance"

    monster = create_monster(
        "drake_igneous",
        instance_id=saved_id
    )

    assert monster.instance_id == saved_id


def test_monster_without_resonance_data_can_load_at_r0():

    original = create_monster("drake_storm")

    data = monster_to_dict(original)

    inventory = Inventory()

    loaded = monster_from_dict(
        data,
        inventory
    )

    assert loaded.monster_id == "drake_storm"
    assert loaded.resonance == 0


def test_monster_without_resonance_data_cannot_load_above_r0():

    original = create_monster("drake_storm")

    data = monster_to_dict(original)
    data["resonance"] = 1

    inventory = Inventory()

    with pytest.raises(ValueError):
        monster_from_dict(
            data,
            inventory
        )


def test_gain_exp_without_level_up():

    monster = create_monster("drake_igneous")

    monster.gain_exp(60)

    assert monster.level == 1
    assert monster.experience == 60


def test_gain_exp_levels_up():

    monster = create_monster("drake_igneous")

    monster.gain_exp(100)

    assert monster.level == 2
    assert monster.experience == 0


def test_gain_exp_keeps_overflow_after_level_up():

    monster = create_monster("drake_igneous")

    monster.experience = 60

    monster.gain_exp(100)

    # Lvl 1 needs 100 XP.
    # Already has 60, so 40 XP causes the level up.
    # The remaining 60 XP goes into level 2.

    assert monster.level == 2
    assert monster.experience == 60


def test_gain_exp_can_level_up_multiple_times():

    monster = create_monster("drake_igneous")

    monster.gain_exp(250)

    # Lvl 1 -> 2 = 100 XP
    # Remaining = 150
    #
    # Lvl 2 -> 3 = 110 XP
    # Remaining = 40

    assert monster.level == 3
    assert monster.experience == 40


def test_gain_exp_discards_overflow_when_reaching_level_limit():

    monster = create_monster("drake_igneous")

    monster.level = 9
    monster.experience = 250
    monster.level_limit = 10

    monster.gain_exp(200)

    # Lvl 9 needs 310 XP.
    # Already has 250, so only 60 are needed.
    #
    # 140 XP remain, but reaching the cap discards them.

    assert monster.level == 10
    assert monster.experience == 0


def test_gain_exp_does_nothing_when_at_level_limit():

    monster = create_monster("drake_igneous")

    monster.level = 10
    monster.level_limit = 10

    monster.gain_exp(1000)

    assert monster.level == 10
    assert monster.experience == 0


def test_gain_exp_can_continue_after_level_limit_is_unlocked():

    monster = create_monster("drake_igneous")

    monster.level = 10
    monster.level_limit = 20

    monster.gain_exp(400)

    # Lvl 10 -> 11 requires 350 XP.
    # The remaining 50 XP is kept.

    assert monster.level == 11
    assert monster.experience == 50


def test_gain_exp_does_nothing_at_max_level():

    monster = create_monster("drake_igneous")

    monster.level = 50
    monster.level_limit = 50

    monster.gain_exp(100000)

    assert monster.level == 50
    assert monster.experience == 0


def test_new_monster_starts_with_level_one_stats():

    monster = create_monster("drake_storm")
    data = MONSTER_DATA["drake_storm"]

    multiplier = LEVEL_STAT_MULTIPLIER[1]

    assert monster.max_health == round(data["max_health"] * multiplier)
    assert monster.attack == round(data["attack"] * multiplier)
    assert monster.defense == round(data["defense"] * multiplier)
    assert monster.speed == round(data["speed"] * multiplier)


def test_level_up_updates_monster_stats():

    monster = create_monster("drake_storm")

    old_attack = monster.attack

    monster.level_up()

    expected_attack = round(
        MONSTER_DATA["drake_storm"]["attack"]
        * LEVEL_STAT_MULTIPLIER[2]
    )

    assert monster.level == 2
    assert monster.attack == expected_attack
    assert monster.attack > old_attack


def test_ascended_level_50_has_full_base_stats():

    monster = create_monster("drake_storm")

    monster.level = 50
    monster.level_limit = 50
    monster.ascended = True

    monster.update_level_stats()

    data = MONSTER_DATA["drake_storm"]

    assert ASCENDED_STAT_MULTIPLIER[50] == 1.0

    assert monster.max_health == data["max_health"]
    assert monster.attack == data["attack"]
    assert monster.defense == data["defense"]
    assert monster.speed == data["speed"]


def test_exp_yield_uses_level_and_rarity():

    monster = create_monster("drake_storm")

    monster.level = 30

    expected = round(
        BASE_EXP_YIELD[30]
        * RARITY_EXP_MULTIPLIER[5]
    )

    assert monster.get_exp_yield() == expected


def test_battle_exp_can_level_up_monster():

    monster = create_monster("drake_storm")

    monster.gain_exp(100)

    assert monster.level == 2
    assert monster.attack > 0