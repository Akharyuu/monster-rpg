from uuid import uuid4

from ..data.monster_data import MONSTER_DATA
from ..data.passive_data import PASSIVE_DATA
from ..data.skill_data import SKILL_DATA

from ..models.enums import SkillType
from ..models.monster import Monster
from ..models.skills import (
    DamageSkill,
    HealingSkill,
    PassiveSkill
)


# =========================================================
#                    MONSTER CREATION
# =========================================================

def create_monster(monster_id, instance_id=None):

    if monster_id not in MONSTER_DATA:
        raise ValueError(
            f"Unknown monster id: {monster_id}"
        )

    data = MONSTER_DATA[monster_id]

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

    monster = Monster(
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

    monster.update_level_stats()
    
    return monster


# =========================================================
#                      SKILL CREATION
# =========================================================

def create_skill(skill_id):

    if skill_id not in SKILL_DATA:
        raise ValueError(
            f"Unknown skill id: {skill_id}"
        )

    skill = SKILL_DATA[skill_id]

    if skill["type"] == SkillType.DAMAGE:

        return DamageSkill(
            skill_id=skill_id,
            name=skill["name"],
            multiplier=skill["multiplier"],
            hits=skill.get("hits", 1),
            hit_multipliers=skill.get("hit_multipliers", []),
            target_type=skill["target_type"],
            scaling_stat=skill.get("scaling_stat", "attack"),
            cooldown=skill["cooldown"],
            damage_handler=skill.get("damage_handler"),
            damage_handler_data=skill.get("damage_handler_data"),
            on_hit_handlers=skill.get("on_hit_handlers"),
            after_skill_handlers=skill.get("after_skill_handlers"),
            after_use_handlers=skill.get("after_use_handlers"),
            effects=skill.get("effects", [])
        )

    if skill["type"] == SkillType.HEALING:

        return HealingSkill(
            skill_id=skill_id,
            name=skill["name"],
            scaling_stat=skill["scaling_stat"],
            base_scaling_ratio=skill["base_scaling_ratio"],
            target_type=skill["target_type"],
            cooldown=skill["cooldown"]
        )

    raise ValueError(
        f"Unsupported skill type for {skill_id}: "
        f"{skill['type']}"
    )


# =========================================================
#                    PASSIVE CREATION
# =========================================================

def create_passive(passive_id):
    
    if passive_id not in PASSIVE_DATA:
        raise ValueError(
            f"Unknown passive id: {passive_id}"
        )

    passive = PASSIVE_DATA[passive_id]

    return PassiveSkill(
        skill_id=passive_id,
        name=passive["name"],
        trigger=passive.get("trigger"),
        handler=passive.get("handler")
    )


