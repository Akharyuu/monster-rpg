import math
import random

from ..combat.enemy_ai import (
    choose_enemy_target,
    choose_healing_target,
    choose_skill
)

from ..factories.monster_factory import create_monster

from ..combat.telemetry import (
    add_team_telemetry,
    average_team_telemetry,
    create_battle_telemetry,
    create_team_telemetry_totals,
    serialize_battle_telemetry
)

from ..models.enums import TargetType
from ..models.skills import SkillType

from ..ui import (
    select_ally,
    select_enemy,
    select_skill,
    show_battle_state,
    show_damage_skill_result
)


# =========================================================
#                       BATTLE LOOP
# =========================================================

def battle(allies, enemies):

    all_combatants = allies + enemies

    # Clean last battle combat_state
    for monster in all_combatants:
        monster.reset_combat_state()

    try:
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

            # Predict which combatant is currently closest to the next turn.
            upcoming_combatant = get_upcoming_combatant(
                combatants
            )

            # Determine which turn logic to use based on team membership.
            if active_combatant in allies:
                outcome = player_turn(
                    active_combatant,
                    allies,
                    enemies,
                    upcoming_combatant
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

    finally:
        for monster in all_combatants:
            monster.reset_combat_state()       


# =========================================================
#                       PLAYER TURN
# =========================================================

def player_turn(active_ally, allies, enemies, upcoming_combatant):

    turn_context = begin_turn(active_ally)

    # DoT may defeat the active monster before it can act.
    if not active_ally.is_alive:
        print(
            f"Ally {active_ally.display_name} "
            f"was defeated by damage over time."
        )

        if all(not ally.is_alive for ally in allies):
            return "defeat"

        return None

    print(
        f"\n--- YOUR TURN: "
        f"{active_ally.display_name} ---"
    )

    show_battle_state(
        allies,
        enemies,
        active_ally, 
        upcoming_combatant
    )

    if handle_incapacitated_turn(
        active_ally,
        turn_context
    ):
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
                        skill,
                        combat_context={
                            "team": allies,
                            "opponents": enemies
                        }
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
                        skill,
                        combat_context={
                            "team": allies,
                            "opponents": enemies
                        }
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
                end_turn(
                    active_ally,
                    turn_context
                )

                return outcome

        elif decision == "r":
            return "run"

        else:
            print("Invalid option.")
            continue


# =========================================================
#                        ENEMY TURN
# =========================================================

def enemy_turn(active_enemy, enemies, allies):

    turn_context = begin_turn(active_enemy)

    # DoT may defeat the enemy before it can act.
    if not active_enemy.is_alive:
        print(
            f"Enemy {active_enemy.display_name} "
            f"was defeated by damage over time."
        )

        if all(not enemy.is_alive for enemy in enemies):
            return "victory"

        return None

    print(
        f"\n--- ENEMY TURN: "
        f"{active_enemy.display_name} ---"
    )

    if handle_incapacitated_turn(
        active_enemy,
        turn_context
    ):
        return None

    enemy_skill = choose_skill(active_enemy, enemies, allies)

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

                targets = [choose_enemy_target(active_enemy, allies, enemy_skill)]

            elif enemy_skill.target_type == TargetType.SINGLE_ALLY:

                targets = [choose_healing_target(enemies)]

        match enemy_skill.skill_type:

            case SkillType.DAMAGE:

                skill_result = active_enemy.use_skill(
                    targets,
                    enemy_skill,
                    combat_context={
                        "team": enemies,
                        "opponents": allies
                    }
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
                    enemy_skill,
                    combat_context={
                        "team": enemies,
                        "opponents": allies
                    }
                )

                if skill_result.success:

                    for target_result in skill_result.target_results:
                        target = target_result["target"]
                        heal_value = target_result["heal_value"]

                        print(
                            f"Enemy {target.display_name} "
                            f"recovered {heal_value} HP."
                        )

    end_turn(
        active_enemy,
        turn_context
    )

    return outcome


# =========================================================
#                      SIMULATE BATTLE
# =========================================================

def simulate_battle(team_a, team_b):

    turns = 0

    all_combatants = team_a + team_b

    telemetry = create_battle_telemetry(
        team_a,
        team_b
    )

    for monster in all_combatants:
        monster.reset_combat_state()

    try:
        while (
            any(monster_a.is_alive for monster_a in team_a)
            and any(monster_b.is_alive for monster_b in team_b)
        ):

            living_team_a = [
                monster for monster in team_a
                if monster.is_alive
            ]

            living_team_b = [
                monster for monster in team_b
                if monster.is_alive
            ]

            combatants = living_team_a + living_team_b

            fill_action_gauges(combatants)

            active_combatant = get_ready_combatant(combatants)

            if active_combatant is None:
                continue

            active_combatant.reset_action_gauge()

            turns += 1

            if active_combatant in team_a:

                outcome = auto_turn(
                    active_combatant,
                    team_a,
                    team_b,
                    telemetry
                )

                team_a_remaining_hp = sum(
                    monster.health
                    for monster in team_a
                )

                team_b_remaining_hp = sum(
                    monster.health
                    for monster in team_b
                )

                if outcome == "team_wins":

                    return {
                        "outcome": "team_a_wins",
                        "turns": turns,
                        "team_a_remaining_hp": team_a_remaining_hp,
                        "team_b_remaining_hp": team_b_remaining_hp,
                        "telemetry": serialize_battle_telemetry(
                            telemetry
                        )
                    }
                
                elif outcome == "opponents_win":

                    return {
                        "outcome": "team_b_wins",
                        "turns": turns,
                        "team_a_remaining_hp": team_a_remaining_hp,
                        "team_b_remaining_hp": team_b_remaining_hp,
                        "telemetry": serialize_battle_telemetry(
                            telemetry
                        )
                    }

            else:

                outcome = auto_turn(
                    active_combatant,
                    team_b,
                    team_a,
                    telemetry
                )

                team_a_remaining_hp = sum(
                    monster.health
                    for monster in team_a
                )

                team_b_remaining_hp = sum(
                    monster.health
                    for monster in team_b
                )

                if outcome == "team_wins":

                    return {
                        "outcome": "team_b_wins",
                        "turns": turns,
                        "team_a_remaining_hp": team_a_remaining_hp,
                        "team_b_remaining_hp": team_b_remaining_hp,
                        "telemetry": serialize_battle_telemetry(
                            telemetry
                        )
                    }

                elif outcome == "opponents_win":

                    return {
                        "outcome": "team_a_wins",
                        "turns": turns,
                        "team_a_remaining_hp": team_a_remaining_hp,
                        "team_b_remaining_hp": team_b_remaining_hp,
                        "telemetry": serialize_battle_telemetry(
                            telemetry
                        )
                    }

        team_a_remaining_hp = sum(
            monster.health
            for monster in team_a
        )

        team_b_remaining_hp = sum(
            monster.health
            for monster in team_b
        )

        if all(not monster.is_alive for monster in team_a):

            return {
                "outcome": "team_b_wins",
                "turns": turns,
                "team_a_remaining_hp": team_a_remaining_hp,
                "team_b_remaining_hp": team_b_remaining_hp,
                "telemetry": serialize_battle_telemetry(
                    telemetry
                )
            }

        return {
            "outcome": "team_a_wins",
            "turns": turns,
            "team_a_remaining_hp": team_a_remaining_hp,
            "team_b_remaining_hp": team_b_remaining_hp,
            "telemetry": serialize_battle_telemetry(
                telemetry
            )
        }

    finally:
        for monster in all_combatants:
            monster.reset_combat_state()       



def simulate_battles(team_a_ids, team_b_ids, runs):

    wins_a = 0
    wins_b = 0

    total_turns = 0
    minimum_turns = None
    maximum_turns = None

    team_a_remaining_hp = 0
    team_b_remaining_hp = 0

    team_a_remaining_hp_percent = 0
    team_b_remaining_hp_percent = 0

    team_a_telemetry_totals = (
        create_team_telemetry_totals(
            team_a_ids
        )
    )

    team_b_telemetry_totals = (
        create_team_telemetry_totals(
            team_b_ids
        )
    )


    for _ in range(runs):

        team_a = []
        team_b = []

        for monster_id in team_a_ids:

            monster = create_monster(monster_id)

            team_a.append(monster)


        for monster_id in team_b_ids:

            monster = create_monster(monster_id)

            team_b.append(monster)


        # Total Max HP before the battle.
        team_a_max_hp = sum(
            monster.max_health
            for monster in team_a
        )

        team_b_max_hp = sum(
            monster.max_health
            for monster in team_b
        )


        battle_result = simulate_battle(team_a, team_b)

        add_team_telemetry(
            team_a_telemetry_totals,
            battle_result["telemetry"]["team_a"]
        )

        add_team_telemetry(
            team_b_telemetry_totals,
            battle_result["telemetry"]["team_b"]
        )


        # =========================================================
        #                         WINS
        # =========================================================

        if battle_result["outcome"] == "team_a_wins":
            wins_a += 1

        else:
            wins_b += 1


        # =========================================================
        #                         TURNS
        # =========================================================

        battle_turns = battle_result["turns"]

        total_turns += battle_turns


        if (
            minimum_turns is None
            or battle_turns < minimum_turns
        ):
            minimum_turns = battle_turns


        if (
            maximum_turns is None
            or battle_turns > maximum_turns
        ):
            maximum_turns = battle_turns


        # =========================================================
        #                     REMAINING HP
        # =========================================================

        team_a_final_hp = battle_result["team_a_remaining_hp"]

        team_b_final_hp = battle_result["team_b_remaining_hp"]


        team_a_remaining_hp += (team_a_final_hp)

        team_b_remaining_hp += (team_b_final_hp)


        team_a_remaining_hp_percent += ( team_a_final_hp / team_a_max_hp * 100 )

        team_b_remaining_hp_percent += ( team_b_final_hp / team_b_max_hp * 100 )


    # =========================================================
    #                        RESULTS
    # =========================================================

    team_a_win_rate = ( wins_a / runs * 100 )

    team_b_win_rate = ( wins_b / runs * 100 )


    average_turns = ( total_turns / runs )


    team_a_average_remaining_hp = ( team_a_remaining_hp / runs )

    team_b_average_remaining_hp = ( team_b_remaining_hp / runs )

    team_a_average_remaining_hp_percent = ( team_a_remaining_hp_percent / runs )

    team_b_average_remaining_hp_percent = ( team_b_remaining_hp_percent / runs )

    team_a_average_telemetry = (
        average_team_telemetry(
            team_a_telemetry_totals,
            runs
        )
    )

    team_b_average_telemetry = (
        average_team_telemetry(
            team_b_telemetry_totals,
            runs
        )
    )


    print(
        f"Team A win rate: "
        f"{team_a_win_rate:.1f}%.\n"

        f"Team B win rate: "
        f"{team_b_win_rate:.1f}%.\n"

        f"Average turns: "
        f"{average_turns:.2f}.\n"

        f"Minimum turns: "
        f"{minimum_turns}.\n"

        f"Maximum turns: "
        f"{maximum_turns}.\n"

        f"Team A average remaining HP: "
        f"{team_a_average_remaining_hp:.2f} "
        f"({team_a_average_remaining_hp_percent:.1f}%).\n"

        f"Team B average remaining HP: "
        f"{team_b_average_remaining_hp:.2f} "
        f"({team_b_average_remaining_hp_percent:.1f}%)."
    )


    return {
        "team_a_win_rate": team_a_win_rate,
        "team_b_win_rate": team_b_win_rate,
        "average_turns": average_turns,
        "minimum_turns": minimum_turns,
        "maximum_turns": maximum_turns,
        "team_a_average_remaining_hp": team_a_average_remaining_hp,
        "team_b_average_remaining_hp": team_b_average_remaining_hp,
        "team_a_average_remaining_hp_percent": team_a_average_remaining_hp_percent,
        "team_b_average_remaining_hp_percent": team_b_average_remaining_hp_percent,
        "team_a_telemetry": team_a_average_telemetry,
        "team_b_telemetry": team_b_average_telemetry
    }




# =========================================================
#                       AUTO TURN
# =========================================================

def auto_turn(active_monster, team, opponents, telemetry=None):

    turn_context = begin_turn(
        active_monster,
        telemetry
    )

    if not active_monster.is_alive:

        if all(not monster.is_alive for monster in team):
            return "opponents_win"

        return None

    if handle_incapacitated_turn(active_monster, turn_context):
        return None

    monster_skill = choose_skill(active_monster, team, opponents)

    outcome = None

    if monster_skill is not None:

        targets = resolve_targets(
            monster_skill,
            active_monster,
            team,
            opponents
        )

        if targets is None:

            if monster_skill.target_type == TargetType.SINGLE_ENEMY:

                targets = [choose_enemy_target(active_monster, opponents, monster_skill)]

            elif monster_skill.target_type == TargetType.SINGLE_ALLY:

                targets = [choose_healing_target(team)]

        match monster_skill.skill_type:

            case SkillType.DAMAGE:

                skill_result = active_monster.use_skill(
                    targets,
                    monster_skill,
                    combat_context={
                        "team": team,
                        "opponents": opponents,
                        "telemetry": telemetry
                    }
                )

                if skill_result.success:

                    if all(
                        not opponent.is_alive
                        for opponent in opponents
                    ):
                        outcome = "team_wins"

            case SkillType.HEALING:

                skill_result = active_monster.use_skill(
                    targets,
                    monster_skill,
                    combat_context={
                        "team": team,
                        "opponents": opponents,
                        "telemetry": telemetry
                    }
                )

    end_turn(
        active_monster,
        turn_context
    )

    return outcome   


# =========================================================
#                      TURN LIFECYCLE
# =========================================================

def begin_turn(monster, telemetry=None):

    # Prepares a monster's turn and returns temporary turn data.

    # Effects present at the start of the turn are remembered so effects
    # applied during this same turn do not immediately lose duration.

    effects_at_turn_start = {
        id(effect)
        for effect in monster.buffs + monster.debuffs
    }

    # Cooldowns and damage-over-time are processed
    # before the monster can take its action.
    monster.reduce_skill_cooldowns()
    monster.apply_damage_over_time(
        telemetry
    )
    monster.apply_healing_over_time(
        telemetry
    )

    return {
        "effects_at_turn_start": effects_at_turn_start
    }



def end_turn(monster, turn_context):

    # Resolves mechanics that happen when the monster's turn ends.

    monster.reduce_remaining_turns(
        turn_context["effects_at_turn_start"]
    )



def handle_incapacitated_turn(monster, turn_context):

    # Ends the turn immediately if the monster cannot act.
    # Returns True when the turn was consumed.

    if not monster.cannot_act:
        return False

    if monster.is_stunned:
        print(
            f"{monster.display_name} "
            f"is stunned and loses the turn."
        )

    elif monster.is_frozen:
        print(
            f"{monster.display_name} "
            f"is frozen and loses the turn."
        )

    end_turn(
        monster,
        turn_context
    )

    return True


# =========================================================
#                       ACTION GAUGE
# =========================================================

def fill_action_gauges(combatants):

    time_to_ready = []

    for combatant in combatants:

        speed = combatant.get_effective_stat("speed")

        gauge_gain = speed / 2000

        if gauge_gain <= 0:
            continue

        remaining_gauge = ( 1 - combatant.action_gauge )

        time_needed = ( remaining_gauge / gauge_gain )

        time_to_ready.append(time_needed)

    if not time_to_ready:
        return

    smallest_time = min(time_to_ready)

    for combatant in combatants:

        speed = combatant.get_effective_stat("speed")

        gauge_gain = speed / 2000

        if gauge_gain <= 0:
            continue

        combatant.increase_action_gauge( gauge_gain * smallest_time )



def get_ready_combatant(combatants):

    ready = [
        combatant
        for combatant in combatants
        if combatant.is_alive
        and combatant.action_gauge >= 1
    ]

    if not ready:
        return None

    highest_speed = max(
        combatant.get_effective_stat("speed")
        for combatant in ready
    )

    speed_tied = [
        combatant
        for combatant in ready
        if combatant.get_effective_stat("speed")
        == highest_speed
    ]

    return random.choice(speed_tied)



def get_upcoming_combatant(combatants):

    candidates = []

    for combatant in combatants:

        if not combatant.is_alive:
            continue

        speed = combatant.get_effective_stat("speed")
        gauge_gain = speed / 2000

        if gauge_gain <= 0:
            continue

        if combatant.action_gauge >= 1:
            ticks_needed = 0

        else:
            remaining_gauge = (
                1 - combatant.action_gauge
            )

            ticks_needed = math.ceil(
                remaining_gauge / gauge_gain
            )

        candidates.append(
            (
                ticks_needed,
                speed,
                combatant
            )
        )

    if not candidates:
        return None

    minimum_ticks = min(
        candidate[0]
        for candidate in candidates
    )

    next_candidates = [
        candidate
        for candidate in candidates
        if candidate[0] == minimum_ticks
    ]

    highest_speed = max(
        candidate[1]
        for candidate in next_candidates
    )

    speed_tied = [
        candidate
        for candidate in next_candidates
        if candidate[1] == highest_speed
    ]

    if len(speed_tied) > 1:
        return None

    return speed_tied[0][2]


# =========================================================
#                    TARGET RESOLUTION
# =========================================================

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

