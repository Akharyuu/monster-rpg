from .ui import select_skill, show_battle_state, show_damage_skill_result, select_enemy, select_ally
from .skills import SkillType
from .enums import TargetType
import random

def battle(allies, enemies):

    # Clean last battle combat_resources
    for monster in allies + enemies:
        monster.reset_combat_resources()

    # Combat continues while both teams have at least one living monster.
    while (
        any(ally.is_alive for ally in allies)
        and any(enemy.is_alive for enemy in enemies)
    ):

        # Only living monsters participate in Action Gauge calculations.
        living_allies = [
            ally for ally in allies
            if ally.is_alive
        ]

        living_enemies = [
            enemy for enemy in enemies
            if enemy.is_alive
        ]

        # Action Gauge treats every living monster as a combatant, regardless of which team it belongs to.
        combatants = living_allies + living_enemies

        fill_action_gauges(combatants)

        # Select the monster whose Action Gauge is ready to take a turn.
        active_combatant = get_ready_combatant(combatants)

        # If nobody reached full Action Gauge yet, advance another tick.
        if active_combatant is None:
            continue

        # Gauge resets before the turn so any gauge gained during the action is preserved for the next turn.
        active_combatant.reset_action_gauge()

        # Determine which turn logic to use based on team membership.
        if active_combatant in allies:
            outcome = player_turn(
                active_combatant,
                allies,
                enemies
            )

        else:
            outcome = enemy_turn(
                active_combatant,
                enemies,
                allies
            )

        # player_turn/enemy_turn may detect victory, defeat or run.
        if outcome is not None:
            return outcome

    # Reaching this point means one of the two teams has no living monsters.
    if all(not ally.is_alive for ally in allies):
        return "defeat"

    return "victory"


def player_turn(active_ally, allies, enemies):

    effects_at_turn_start = {
        id(effect)
        for effect in active_ally.buffs + active_ally.debuffs
    }

    active_ally.reduce_skill_cooldowns()
    active_ally.apply_damage_over_time()

    # DoT only causes defeat if the entire ally team is dead.
    if not active_ally.is_alive:
        print(
            f"Ally {active_ally.display_name} "
            f"was defeated by damage over time."
        )

        if all(not ally.is_alive for ally in allies):
            return "defeat"

        return None

    print(f"\n--- YOUR TURN: {active_ally.display_name} ---")
    show_battle_state(allies, enemies, active_ally)

    # Stun/Freeze consume the turn.
    if active_ally.cannot_act:
        if active_ally.is_stunned:
            print(
                f"{active_ally.display_name} "
                f"is stunned and loses the turn."
            )

        elif active_ally.is_frozen:
            print(
                f"{active_ally.display_name} "
                f"is frozen and loses the turn."
            )

        active_ally.reduce_remaining_turns(effects_at_turn_start)
        return None

    while True:

        decision = input(
            "What to do? (Use skill: 's' / Run: 'r')\n> "
        ).strip().lower()

        turn_finished = False
        outcome = None

        if decision == "s":
            skill = select_skill(active_ally)

            # First try to resolve targets automatically.
            targets = resolve_targets(
                skill,
                active_ally,
                allies,
                enemies
            )

            # Single-target skills require player selection.
            if targets is None:

                if skill.target_type == TargetType.SINGLE_ENEMY:
                    selected_enemy = select_enemy(enemies)
                    targets = [selected_enemy]

                elif skill.target_type == TargetType.SINGLE_ALLY:
                    selected_ally = select_ally(allies)
                    targets = [selected_ally]

            match skill.skill_type:

                case SkillType.DAMAGE:

                    skill_result = active_ally.use_skill(
                        targets,
                        skill
                    )

                    if skill_result.success:

                        show_damage_skill_result(
                            active_ally,
                            skill,
                            skill_result
                        )

                        if all(
                            not enemy.is_alive
                            for enemy in enemies
                        ):
                            print("All enemies were defeated.")
                            outcome = "victory"

                        turn_finished = True

                    else:
                        continue

                case SkillType.HEALING:

                    skill_result = active_ally.use_skill(
                        targets,
                        skill
                    )

                    if skill_result.success:

                        for target_result in skill_result.target_results:
                            target = target_result["target"]
                            heal_value = target_result["heal_value"]

                            print(
                                f"Ally {target.display_name} "
                                f"recovered {heal_value} HP."
                            )

                        turn_finished = True

                    else:
                        continue

            if turn_finished:
                active_ally.reduce_remaining_turns(effects_at_turn_start)
                return outcome

        elif decision == "r":
            return "run"

        else:
            print("Invalid option.")
            continue


def enemy_turn(active_enemy, enemies, allies):

    effects_at_turn_start = {
        id(effect)
        for effect in active_enemy.buffs + active_enemy.debuffs
    }

    active_enemy.reduce_skill_cooldowns()
    active_enemy.apply_damage_over_time()

    # If DoT kills this enemy, only return victory if the whole enemy team is dead.
    if not active_enemy.is_alive:
        print(
            f"Enemy {active_enemy.display_name} "
            f"was defeated by damage over time."
        )

        if all(not enemy.is_alive for enemy in enemies):
            return "victory"

        return None

    print(f"\n--- ENEMY TURN: {active_enemy.display_name} ---")

    # Stun/Freeze consume the turn.
    if active_enemy.cannot_act:
        if active_enemy.is_stunned:
            print(
                f"{active_enemy.display_name} "
                f"is stunned and loses the turn."
            )

        elif active_enemy.is_frozen:
            print(
                f"{active_enemy.display_name} "
                f"is frozen and loses the turn."
            )

        active_enemy.reduce_remaining_turns(effects_at_turn_start)
        return None

    # TODO: Replace with real enemy AI.
    if active_enemy.is_silenced:
        enemy_skill = active_enemy.get_skill(1)
    else:
        enemy_skill = active_enemy.get_skill(1)

    outcome = None

    if enemy_skill is not None:

        # First try automatic target resolution.
        targets = resolve_targets(
            enemy_skill,
            active_enemy,
            enemies,
            allies
        )

        # Single-target skills require an AI decision.
        if targets is None:

            if enemy_skill.target_type == TargetType.SINGLE_ENEMY:

                alive_allies = [
                    ally for ally in allies
                    if ally.is_alive
                ]

                targets = [
                    random.choice(alive_allies)
                ]

            elif enemy_skill.target_type == TargetType.SINGLE_ALLY:

                alive_teammates = [
                    enemy for enemy in enemies
                    if enemy.is_alive
                ]

                targets = [
                    random.choice(alive_teammates)
                ]

        match enemy_skill.skill_type:

            case SkillType.DAMAGE:

                skill_result = active_enemy.use_skill(
                    targets,
                    enemy_skill
                )

                if skill_result.success:

                    show_damage_skill_result(
                        active_enemy,
                        enemy_skill,
                        skill_result
                    )

                    if all(
                        not ally.is_alive
                        for ally in allies
                    ):
                        print("All allies were defeated.")
                        outcome = "defeat"

            case SkillType.HEALING:

                skill_result = active_enemy.use_skill(
                    targets,
                    enemy_skill
                )

                if skill_result.success:

                    for target_result in skill_result.target_results:
                        target = target_result["target"]
                        heal_value = target_result["heal_value"]

                        print(
                            f"Enemy {target.display_name} "
                            f"recovered {heal_value} HP."
                        )

    active_enemy.reduce_remaining_turns(effects_at_turn_start)

    return outcome


#Action Gauges
def fill_action_gauges(combatants):
    for combatant in combatants:
        speed = combatant.get_effective_stat("speed")
        combatant.increase_action_gauge(speed / 1000)


def get_ready_combatant(combatants):
    ready = [
        combatant
        for combatant in combatants
        if combatant.is_alive and combatant.action_gauge >= 1
    ]

    if not ready:
        return None

    highest_gauge = max(
        combatant.action_gauge
        for combatant in ready
    )

    gauge_tied = [
        combatant
        for combatant in ready
        if combatant.action_gauge == highest_gauge
    ]

    highest_speed = max(
        combatant.get_effective_stat("speed")
        for combatant in gauge_tied
    )

    speed_tied = [
        combatant
        for combatant in gauge_tied
        if combatant.get_effective_stat("speed") == highest_speed
    ]

    return random.choice(speed_tied)


#Auxiliar
def resolve_targets(skill, actor, team, opponents):

    alive_team = [
        monster for monster in team
        if monster.is_alive
    ]

    alive_opponents = [
        monster for monster in opponents
        if monster.is_alive
    ]

    match skill.target_type:

        case TargetType.SELF:
            return [actor]

        case TargetType.ALL_ALLIES:
            return alive_team

        case TargetType.ALL_ENEMIES:
            return alive_opponents

        case TargetType.RANDOM_ENEMIES:
            return alive_opponents

    return None