from ..data.glyph_stat_data import GLYPH_STAT_DATA
from ..data.glyph_level_data import GLYPH_LEVEL_DATA
from math import ceil
import random

class Glyph:
    def __init__(self, instance_id, slot_id, set_id, main_stat, sub_stats, rarity, level=0):
        self.instance_id = instance_id
        self.slot_id = slot_id
        self.set_id = set_id
        self.main_stat = main_stat
        self.sub_stats = sub_stats
        self.rarity = rarity
        self.level = level

    @property
    def main_value(self):
        max_value = GLYPH_STAT_DATA[self.main_stat]["main_max"][self.rarity]
        level_multiplier = GLYPH_LEVEL_DATA[self.level]["level_multiplier"]

        return ceil(max_value * level_multiplier)


    def level_up(self):
        if self.level < 15:
            self.level +=1
            return True

        return False


    def glyph_level_upgrade(self, amount=1):
        for i in range(amount):
            if self.level_up():

                data = GLYPH_LEVEL_DATA[self.level]

                if data.get("substat_rolls", False):
                    self.roll_substat(data["substat_rolls"])
             

    def roll_substat(self, rolls):
        
        sub_stat = random.choice(self.sub_stats)

        for i in range(rolls):

            max_roll = GLYPH_STAT_DATA[sub_stat.stat]["sub_roll_max"][self.rarity]
            min_roll = ceil(max_roll / 2)

            new_roll = random.randint(min_roll, max_roll)

            sub_stat.rolls.append(new_roll)



class GlyphSubstat:
    def __init__(self, stat, rolls):
        self.stat = stat
        self.rolls = rolls

    @property
    def total_value(self):
        return sum(self.rolls)

    