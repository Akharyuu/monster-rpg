import random
from .monster_data import MONSTER_DATA
from .sealstone_data import SEALSTONE_DATA
from .factories import create_monster

def summon(collection, sealstone_type):
    monster_ids = []

    while not monster_ids:

        rarity = roll_rarity(sealstone_type)
        allowed_attributes = SEALSTONE_DATA[sealstone_type]["allowed_attributes"]

        for monster_id, monster_data in MONSTER_DATA.items():
            if monster_data["rarity"] == rarity and monster_data["attribute"] in allowed_attributes:
                monster_ids.append(monster_id)

    monster_id = random.choice(monster_ids)
    monster = create_monster(monster_id)

    collection.append(monster)

    print(f"{monster.display_name} successfully summoned.")
    return monster


def roll_rarity(sealstone_type):

    try:
        data = SEALSTONE_DATA[sealstone_type]

    except KeyError: 
        return None
    
    rarities = []
    weights = []

    for rarity, weight in data["rarities"].items():
        rarities.append(rarity)
        weights.append(weight)

    rolled_rarity = random.choices(
        rarities,
        weights=weights,
        k=1
    )[0]

    return rolled_rarity



