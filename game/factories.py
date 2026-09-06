from .monster import Monster
from .skills import DamageSkill, HealingSkill
from .monster_data import MONSTER_DATA
from .skill_data import SKILL_DATA
from .enums import SkillType


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

    for skill_id in data.get("skills", []):
        skill = SKILL_DATA[skill_id]

        if skill["type"] == SkillType.DAMAGE:
            skills.append(
                DamageSkill(
                    skill_id,
                    skill["name"], 
                    skill["power"], 
                    skill.get("effects", []),
                    skill["cooldown"]
                )
            )

        elif skill["type"] == SkillType.HEALING:
            skills.append(
                HealingSkill(
                    skill_id,
                    skill["name"],
                    skill["scaling_stat"],
                    skill["base_scaling_ratio"],
                    cooldown=skill["cooldown"]
                )
            )

        elif skill["type"] == SkillType.PASSIVE:
            pass

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

