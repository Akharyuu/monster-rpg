
class Inventory: 

    # =========================================================
    #                       INITIALIZATION
    # =========================================================

    def __init__(self, glyphs=None):
        self.items = {}

        self.glyphs = glyphs if glyphs is not None else {}


    # =========================================================
    #                          ITEMS
    # =========================================================

    def add_item(self, item, amount=1):

        self.items[item] = (
            self.get_amount(item)
            + amount
        )



    def get_amount(self, item):

        return self.items.get(
            item,
            0
        )



    def has_item(self, item, amount=1):
        return self.get_amount(item) >= amount
        


    def remove_item(self, item, amount=1):

        if not self.has_item(item, amount):
            return False

        self.items[item] -= amount

        if self.items[item] == 0:
            del self.items[item]

        return True


    # =========================================================
    #                          GLYPHS
    # =========================================================

    def add_glyph(self, glyph):

        self.glyphs[glyph.instance_id] = glyph



    def get_glyph(self, instance_id):

        return self.glyphs.get(instance_id)



    def remove_glyph(self, instance_id):
        return self.glyphs.pop(instance_id, None)



