from game.factories.monster_factory import create_monster

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