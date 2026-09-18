from game.factories.glyph_factory import create_glyph
from game.systems.inventory import Inventory


def test_inventory_add_get_and_remove_glyph():

    inventory = Inventory()
    glyph = create_glyph("legendary")

    # ADD
    inventory.add_glyph(glyph)

    assert glyph.instance_id in inventory.glyphs
    assert inventory.glyphs[glyph.instance_id] is glyph

    # GET
    found_glyph = inventory.get_glyph(glyph.instance_id)

    assert found_glyph is glyph

    # REMOVE
    removed_glyph = inventory.remove_glyph(glyph.instance_id)

    assert removed_glyph is glyph
    assert inventory.get_glyph(glyph.instance_id) is None
    assert glyph.instance_id not in inventory.glyphs