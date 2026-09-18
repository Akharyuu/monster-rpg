from ..models.enums import EssenceType

class Inventory: 
    def __init__(self, glyphs=None):
        self.items = {}

        if glyphs is None:
            self.glyphs = {}
        else:
            self.glyphs = glyphs


    def add_item(self, item, amount=1):
        if item in self.items:
            self.items[item] += amount
        else:
            self.items[item] = amount


    def get_amount(self, item):
        if item in self.items:
            return self.items[item]
        
        return 0


    def has_item(self, item, amount=1):
        return self.get_amount(item) >= amount
        

    def remove_item(self, item, amount=1):
        if self.has_item(item, amount):
            self.items[item] -= amount
            if self.items[item] == 0:
                del self.items[item]
            return True
        return False


    def add_glyph(self, glyph):

        self.glyphs[glyph.instance_id] = glyph


    def get_glyph(self, instance_id):

        return self.glyphs.get(instance_id)


    def remove_glyph(self, instance_id):
        return self.glyphs.pop(instance_id, None)



