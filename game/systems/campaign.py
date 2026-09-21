from ..combat.combat import battle

from ..factories.monster_factory import create_monster

from ..systems.unsealing import unseal_interface

from ..ui import (
    print_header,
    print_subheader,
    wait_for_input,
    display_dialog
)


# =========================================================
#                     MISSION HANDLING
# =========================================================

def mission_handler(mission, player):

    print_header(mission["name"])

    battle_number = 0

    total_battles = sum(
        1
        for event in mission["events"]
        if "battle" in event
    )

    for event in mission["events"]:

        if len(event) != 1:
            raise ValueError(
                "Campaign events must contain exactly one event type."
            )

        event_type, event_data = next(iter(event.items()))

        match event_type:

            case "dialog":
                display_dialog(event_data, player)

            case "battle":
                battle_number += 1

                print_subheader(
                    f"ENCOUNTER {battle_number}/{total_battles}"
                )

                enemies = build_enemies(event_data)

                outcome = battle(
                    [player.collection[0]],
                    enemies
                )

                if outcome == "defeat":
                    print_header("MISSION FAILED")
                    return "defeat"

                if outcome == "run":
                    print_header("MISSION ABANDONED")
                    return "run"

            case "reward":
                give_rewards(event_data, player)

            case "unseal":
                unseal_interface(
                    player,
                    forced_monster_id=event_data.get(
                        "forced_monster_id"
                    ),
                    required_sealstone_type=event_data.get(
                        "sealstone_type"
                    ),
                    allow_cancel=False
                )

            case "unlock":
                # Future implementation.
                pass

            case _:
                raise ValueError(
                    f"Unknown campaign event: {event_type}"
                )

    print_header("MISSION COMPLETE")
    print(f"{mission['name']}\n")

    return "completed"


# =========================================================
#                     ENEMY BUILDING
# =========================================================

def build_enemies(monster_data):

    enemies = []

    for enemy_data in monster_data["enemies"]:

        enemy = create_monster(enemy_data["monster_id"])
        enemy.level = enemy_data["level"]
        enemy.update_level_stats()

        enemies.append(enemy)

    return enemies


# =========================================================
#                         REWARDS
# =========================================================

def give_rewards(reward_data, player):

    print_subheader("REWARDS")

    for reward in reward_data["items"]:

        item = reward["item"]
        amount = reward["amount"]

        player.inventory.add_item(item, amount)

        print(f"  + {item.value} x{amount}")

    wait_for_input()
