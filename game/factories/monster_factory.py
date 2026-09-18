from ..models.monster import Monster
from ..models.skills import DamageSkill, HealingSkill, PassiveSkill
from ..data.monster_data import MONSTER_DATA
from ..data.skill_data import SKILL_DATA
from ..models.enums import SkillType
from ..data.passive_data import PASSIVE_DATA

from uuid import uuid4


def create_monster(monster_id, instance_id=None):

    try: 
        data = MONSTER_DATA[monster_id]
    except KeyError:
        return None

    if instance_id is None:
        instance_id = str(uuid4())

    name = data["name"]
    family = data["family"]
    attribute = data["attribute"]
    rarity = data["rarity"]

    max_health = data["max_health"]
    health = max_health
    attack = data["attack"]
    defense = data["defense"]
    speed = data["speed"]

    skills = []
    passives = []

    for skill_id in data.get("skills", []):
        skills.append(create_skill(skill_id))

    for passive_id in data.get("passives", []):
        passives.append(create_passive(passive_id))

    new = Monster(
        instance_id=instance_id,
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
        skills=skills,
        passives=passives
    )

    return new


def create_skill(skill_id):
    skill = SKILL_DATA[skill_id]
    new = None

    if skill["type"] == SkillType.DAMAGE:
        new = DamageSkill(
            skill_id,
            skill["name"], 
            skill["multiplier"], 
            skill.get("hits", 1),
            skill.get("hit_multipliers", []),
            skill["target_type"],
            skill.get("scaling_stat", "attack"),
            skill["cooldown"],
            skill.get("damage_handler", None),
            skill.get("damage_handler_data", None),
            skill.get("on_hit_handlers", None),
            skill.get("after_skill_handlers", None),
            skill.get("effects", [])
        )
  
    elif skill["type"] == SkillType.HEALING:
        new = HealingSkill(
            skill_id,
            skill["name"],
            skill["scaling_stat"],
            skill["base_scaling_ratio"],
            skill["target_type"],
            cooldown=skill["cooldown"]
        )

    return new


def create_passive(passive_id):
    passive = PASSIVE_DATA[passive_id]

    new = PassiveSkill(
        skill_id=passive_id,
        name=passive["name"],
        trigger=passive.get("trigger"),
        handler=passive.get("handler")
    )

    return new

