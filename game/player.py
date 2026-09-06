from .inventory import Inventory
from .collection import get_essence_type

class Player():
    def __init__(self, name):
        self.name = name
        self.collection = []
        self.inventory = Inventory()


    def resonate_monster(self, target, dupe):
        if target.can_resonate_with(dupe):
            target.increase_resonance()
            self.collection.remove(dupe)
            return True
        
        return False


    def dismantle_monster(self, monster):
        essence_type = get_essence_type(monster)

        if essence_type is None:
            return None

        if monster in self.collection:
            self.collection.remove(monster)
            self.inventory.add_item(essence_type)
            return essence_type
        
        return None

    