from .factories import create_skill, create_passive
from .resonance_data import RESONANCE_DATA
from .monster_data import MONSTER_DATA

def replace_skill(monster, slot, new_skill_id):
    new_skill = create_skill(new_skill_id)
    monster.skills[slot - 1] = new_skill
    return True


def replace_passive(monster, old_passive_id, new_passive_id):
    for i, passive in enumerate(monster.passives):
        if passive.skill_id == old_passive_id:
            monster.passives[i] = create_passive(new_passive_id)
            return True

    return False


def add_passive(monster, new_skill_id):
    new_passive = create_passive(new_skill_id)
    monster.passives.append(new_passive)
    return True


def apply_resonance_action(monster, action):
    match action["action"]:
        case "replace_skill":
            result = replace_skill(monster, action["slot"], action["new"])

        case "replace_passive":
            result = replace_passive(monster, action["old"], action["new"])

        case "add_passive":
            result = add_passive(monster, action["passive"])

        case _:
            result = False

    return result


def reset_to_base_kit(monster):
    new_skills = []
    new_passives = []

    monster_data = MONSTER_DATA[monster.monster_id]

    for skill in monster_data.get("skills", []):
        new_skills.append(create_skill(skill))

    for passive in monster_data.get("passives", []):
        new_passives.append(create_passive(passive))

    monster.skills = new_skills
    monster.passives = new_passives


def update_resonance_kit(monster):
    reset_to_base_kit(monster)
    data = RESONANCE_DATA[monster.monster_id]

    for resonance_number, actions in data.items():
        if resonance_number <= monster.resonance:
            for action in actions:
                apply_resonance_action(monster, action)



