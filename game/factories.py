from .entities import Monster, Skill
from .monster_data import MONSTER_DATA


def create_monster(monster_id):

    try: 
        data = MONSTER_DATA[monster_id]
    except KeyError:
        return None

    name = data["name"]
    family = data["family"]
    attribute = data["attribute"]
    rarity = data["rarity"]

    max_health = data["max_health"]
    health = data["max_health"]
    attack = data["attack"]
    defense = data["defense"]
    speed = data["speed"]

    skills = []

    for skill in data.get("skills", []):
        skills.append(
            Skill(
                skill["name"], 
                skill["power"], 
                skill["cooldown"]
            )
        )

    new = Monster(
        monster_id=monster_id,
        name=name, 
        family=family, 
        attribute=attribute, 
        rarity=rarity, 
        health=health, 
        max_health=max_health, 
        attack=attack, 
        defense=defense, 
        speed=speed,
        skills=skills
    )

    return new

