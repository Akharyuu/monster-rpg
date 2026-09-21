from .collection import get_essence_type
from .inventory import Inventory
from .resonance import update_resonance_kit


class Player:

    # =========================================================
    #                       INITIALIZATION
    # =========================================================

    def __init__(self, name):
        self.name = name
        self.collection = []
        self.inventory = Inventory()


    # =========================================================
    #                       RESONANCE
    # =========================================================

    def resonate_monster(self, target, dupe):

        if not target.can_resonate_with(dupe):
            return False

        target.increase_resonance()

        update_resonance_kit(target)

        self.collection.remove(dupe)

        return True



    def dismantle_monster(self, monster):

        essence_type = get_essence_type(monster)

        if essence_type is None:
            return None

        if monster not in self.collection:
            return None

        self.collection.remove(monster)

        self.inventory.add_item(essence_type)

        return essence_type

    