from .ui import select_skill, show_battle_state
import random
from .skills import SkillType

def battle(ally, enemy):

    while ally.is_alive and enemy.is_alive:

        ally_speed = ally.get_effective_stat("speed")
        enemy_speed = enemy.get_effective_stat("speed")

        #Orden de turno
        if ally_speed > enemy_speed:
            first = ally
            second = enemy

        elif ally_speed < enemy_speed:
            first = enemy
            second = ally

        else:
            first = random.choice([ally, enemy])
            if first == ally:
                second = enemy
            else:
                second = ally

        #Primero
        if first == ally:
            outcome = player_turn(ally, enemy)
        else: 
            outcome = enemy_turn(enemy, ally)

        if outcome is not None:
            return outcome

        #Segundo
        if second == ally:
            outcome = player_turn(ally, enemy)
        else: 
            outcome = enemy_turn(enemy, ally)

        if outcome is not None:
            return outcome



def player_turn(ally, enemy):

    ally.reduce_skill_cooldowns()

    ally.apply_damage_over_time()

    if not ally.is_alive:
        print(f"Ally {ally.display_name} was defeated by damage over time.")
        return "defeat"

    show_battle_state(ally, enemy)

    if ally.cannot_act:
        if ally.is_stunned:
            print(f"{ally.display_name} is stunned and loses the turn.")
    
        elif ally.is_frozen:
            print(f"{ally.display_name} is frozen and loses the turn.")
                
        ally.reduce_remaining_turns()
        return None

    while True:

        decision = input("What to do? (Use skill: 's' / Run: 'r')\n> ")
        turn_finished = False
        outcome = None

        #Use Skill
        if decision == "s":
            skill = select_skill(ally)

            match skill.skill_type:
                case SkillType.DAMAGE:
                    skill_result = ally.use_skill(enemy, skill)
                    if skill_result.success:
                        if skill_result.critical: 
                            print(f"CRITICAL! Enemy {enemy.display_name} received {skill_result.value} damage.")
                        else: 
                            print(f"Enemy {enemy.display_name} received {skill_result.value} damage.")

                        if not enemy.is_alive:
                            print(f"Enemy {enemy.display_name} defeated.")
                            outcome = "victory"

                        turn_finished = True

                    else:
                        continue

                case SkillType.HEALING:
                    skill_result = ally.use_skill(ally, skill)
                    if skill_result.success:
                        print(f"Ally {ally.display_name} recovered {skill_result.value} HP.")

                        turn_finished = True

                    else:
                        continue

            if turn_finished:
                ally.reduce_remaining_turns()
                return outcome

        #Run
        elif decision == "r":
            return "run"

        else:
            print("Invalid option.")
            continue


def enemy_turn(enemy, ally):

    enemy.reduce_skill_cooldowns()

    enemy.apply_damage_over_time()

    if not enemy.is_alive:
        print(f"Enemy {enemy.display_name} was defeated by damage over time.")
        return "victory"

    if enemy.cannot_act:
        if enemy.is_stunned:
            print(f"{enemy.display_name} is stunned and loses the turn.")

        elif enemy.is_frozen:
            print(f"{enemy.display_name} is frozen and loses the turn.")

        enemy.reduce_remaining_turns()
        return None

    if enemy.is_silenced:
        enemy_skill = enemy.get_skill(1) #TODO: Replace with Enemy AI Skill Selection.
    else:
        enemy_skill = enemy.get_skill(1)

    outcome = None

    if enemy_skill is not None:
        match enemy_skill.skill_type:
            case SkillType.DAMAGE:
                skill_result = enemy.use_skill(ally, enemy_skill)
                if skill_result.success:
                    if skill_result.critical:
                        print(f"CRITICAL! Ally {ally.display_name} received {skill_result.value} damage.")
                    else:
                        print(f"Ally {ally.display_name} received {skill_result.value} damage.")

                    if not ally.is_alive:
                        print(f"Ally {ally.display_name} was defeated.")
                        outcome = "defeat"
            
            case SkillType.HEALING:
                skill_result = enemy.use_skill(enemy, enemy_skill)
                if skill_result.success:
                    print(f"Enemy {enemy.display_name} recovered {skill_result.value} HP.")

    enemy.reduce_remaining_turns()

    return outcome
               
