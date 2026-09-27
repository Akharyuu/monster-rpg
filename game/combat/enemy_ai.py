import random

from ..combat.ai_conditions import AI_CONDITIONS
from ..data.ai_metadata import SKILL_AI_DATA
from ..models.enums import (
    SkillType,
    TargetType
)


# =========================================================
#                     SKILL SELECTION
# =========================================================

def choose_skill(active_enemy, enemies, allies):

    context = {
        "caster": active_enemy,
        "team": enemies,
        "opponents": allies
    }


    base_skill = active_enemy.get_skill(1)

    # Silence forces the use of S1.
    if active_enemy.is_silenced:
        return base_skill

    available_skills = []

    teammate_needs_healing = any(
        enemy.health / enemy.max_health < 0.75
        for enemy in enemies
    )

    # Filter skills that can currently be used.
    for skill in active_enemy.skills:

        if skill.current_cooldown == 0:

            if (
                skill.skill_type == SkillType.HEALING
                and not teammate_needs_healing
            ):
                continue

            if not check_use_conditions(
                skill,
                context
            ):
                continue

            available_skills.append(skill)

    if len(available_skills) <= 1:

        return base_skill

    kill_skills = []

    # Look for skills that guarantee a kill.
    for skill in available_skills: 

        if skill.skill_type != SkillType.DAMAGE:
            continue

        if any(
            sees_kill(active_enemy, target, skill) 
            for target in allies 
            if target.is_alive
        ):
            kill_skills.append(skill)

    # Prioritize AoE kill skills, then lowest cooldown.
    if kill_skills:

        aoe_skills = []

        for skill in kill_skills:

            if skill.target_type == TargetType.ALL_ENEMIES:
                aoe_skills.append(skill)

        if aoe_skills:
            skill_pool = aoe_skills
        else:
            skill_pool = kill_skills

        cooldowns = []
        lowest_cooldown_skills = []

        for skill in skill_pool:
            cooldowns.append(skill.cooldown)

        min_cooldown = min(cooldowns)

        for skill in skill_pool:

            if skill.cooldown == min_cooldown:
                lowest_cooldown_skills.append(skill)

        return random.choice(lowest_cooldown_skills)

    # Prepare skills whose setup requirements are not ready yet.
    setup_skills = []

    for skill in available_skills:

        if check_setup_requirements(skill, context):
            continue

        setup_skill = find_setup_skill(
            available_skills,
            skill
        )

        if setup_skill is not None:
            setup_skills.append(setup_skill)

    if setup_skills:
        return random.choice(setup_skills)

    # Default weighted skill selection.
    if len(available_skills) == 2:

        selected_skills = random.choices(
            available_skills,
            weights=[20, 80],
            k=1
        ) 

    elif len(available_skills) == 3:

        selected_skills = random.choices(
            available_skills,
            weights=[10, 55, 35],
            k=1
        ) 

    return selected_skills[0]


# =========================================================
#                    TARGET SELECTION
# =========================================================

def choose_enemy_target(active_enemy, allies, skill):

    alive_targets = []

    for target in allies:

        if target.is_alive:
            alive_targets.append(target)

    if len(alive_targets) == 1:
        return alive_targets[0]

    kill_range_targets = []

    for target in alive_targets:

        if sees_kill(active_enemy, target, skill):
            kill_range_targets.append(target)

    if kill_range_targets:
        return random.choice(kill_range_targets)
    
    great_targets = []
    normal_targets = []
    bad_targets = []

    for target in alive_targets:

        modifier = active_enemy.get_attribute_modifier(target)

        if modifier == 1.2:
            great_targets.append(target)

        elif modifier == 1:
            normal_targets.append(target)

        else:
            bad_targets.append(target)

    if great_targets:
        target_pool = great_targets

    elif normal_targets:
        target_pool = normal_targets

    elif bad_targets:
        target_pool = bad_targets

    if len(target_pool) == 1:
        return target_pool[0]

    lowest_hp_target = min(
        target_pool,
        key=lambda target: target.health / target.max_health
    )

    final_pool = [lowest_hp_target]

    for target in target_pool:

        if target not in final_pool:
            final_pool.append(target)

    other_targets = len(final_pool) - 1

    weights = [
        75
    ]

    for _ in range(other_targets):
        weights.append(25 / other_targets)

    selected_target = random.choices(
        final_pool,
        weights=weights,
        k=1
    )

    return selected_target[0]



def choose_healing_target(enemies):

    alive_targets = []

    for enemy in enemies:

        if enemy.is_alive:
            alive_targets.append(enemy)

    return min(
        alive_targets,
        key=lambda target: target.health / target.max_health
    )


# =========================================================
#                    DAMAGE ESTIMATION
# =========================================================


def estimate_damage(active_enemy, target, skill):

    total_damage = 0

    for hit in range(skill.hits):

        multiplier = 1

        if skill.hit_multipliers:
            multiplier = skill.hit_multipliers[hit]

        total_damage += skill.base_damage_calc(active_enemy, target, multiplier)

    return total_damage



def sees_kill(active_enemy, target, skill):

    damage = estimate_damage(active_enemy, target, skill)

    return damage >= target.health


# =========================================================
#                      SETUP LOGIC
# =========================================================

def check_setup_requirements(skill, context):

    skill_metadata = SKILL_AI_DATA.get(skill.skill_id)

    if not skill_metadata:
        return True

    setup_requirements = skill_metadata.get("setup_requirements")

    if not setup_requirements:
        return True

    for requirement in setup_requirements:

        condition_name = requirement["condition"]
        handler = AI_CONDITIONS.get(condition_name)

        if handler is None: 
            raise ValueError(
                f"Unsupported AI setup condition: {condition_name}"
            )
        
        requirement_met = handler(requirement, context)
        
        if not requirement_met:
            return False

    return True



def find_setup_skill(available_skills, skill):

    skill_metadata = SKILL_AI_DATA.get(skill.skill_id)

    if not skill_metadata:
        return None

    setup_requirements = skill_metadata.get("setup_requirements")

    if not setup_requirements:
        return None

    for requirement in setup_requirements:

        required_effect_id = requirement["effect_id"]

        for candidate_skill in available_skills:

            if candidate_skill is skill:
                continue
            
            for effect in candidate_skill.effects:

                if effect["effect_id"] == required_effect_id:
                    return candidate_skill

    return None



def check_use_conditions(skill, context):

    skill_metadata = SKILL_AI_DATA.get(
        skill.skill_id
    )

    if not skill_metadata:
        return True

    use_conditions = skill_metadata.get(
        "use_conditions"
    )

    if not use_conditions:
        return True

    for condition in use_conditions:

        condition_name = condition["condition"]

        handler = AI_CONDITIONS.get(
            condition_name
        )

        if handler is None:
            raise ValueError(
                f"Unsupported AI condition: {condition_name}"
            )

        condition_met = handler(
            condition,
            context
        )

        if not condition_met:
            return False

    return True
