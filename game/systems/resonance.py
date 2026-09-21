from ..data.monster_data import MONSTER_DATA
from ..data.resonance_data import RESONANCE_DATA

from ..factories.monster_factory import (
    create_passive,
    create_skill
)


# =========================================================
#                     KIT MODIFICATIONS
# =========================================================

def replace_skill(monster, slot, new_skill_id):

    monster.skills[slot - 1] = create_skill(new_skill_id)

    return True



def replace_passive(monster, old_passive_id, new_passive_id):

    for i, passive in enumerate(monster.passives):

        if passive.skill_id == old_passive_id:

            monster.passives[i] = create_passive(new_passive_id)

            return True

    return False



def add_passive(monster, new_skill_id):

    monster.passives.append(create_passive(new_skill_id))

    return True


# =========================================================
#                    RESONANCE ACTIONS
# =========================================================

def apply_resonance_action(monster, action):

    match action["action"]:

        case "replace_skill":
            return replace_skill(monster, action["slot"], action["new"])

        case "replace_passive":
            return replace_passive(monster, action["old"], action["new"])

        case "add_passive":
            return add_passive(monster, action["passive"])

        case _:
            return False


# =========================================================
#                       KIT RESET
# =========================================================

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

    resonance_data = RESONANCE_DATA.get(monster.monster_id)

    if resonance_data is None:

        if monster.resonance > 0:
            raise ValueError(
                f"{monster.monster_id} has resonance level "
                f"{monster.resonance}, but no resonance data exists."
            )

        return

    for resonance_number, actions in resonance_data.items():

        if resonance_number > monster.resonance:
            continue

        for action in actions:
            apply_resonance_action(monster, action)



