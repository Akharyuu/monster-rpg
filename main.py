from pathlib import Path

from game.combat.combat import battle
from game.data.campaign_data import CAMPAIGN_DATA
from game.factories.monster_factory import create_monster
from game.persistence.save_manager import (
    load_player,
    save_player
)
from game.systems.campaign import mission_handler
from game.systems.collection import get_compatible_dupes
from game.systems.new_game import create_new_game
from game.systems.unsealing import unseal_interface

from game.ui import (
    collection_menu,
    inventory_menu,
    main_menu,
    show_collection,
    show_essences,
    show_sealstones
)


# =========================================================
#                       CONFIGURATION
# =========================================================

SAVE_PATH = Path("save.json")


# =========================================================
#                      GAME STARTUP
# =========================================================

if SAVE_PATH.exists():
    player = load_player(SAVE_PATH)

else:
    player = create_new_game("Ryuu")


# TEMPORARY: Run first mission for campaign testing.
mission_handler(CAMPAIGN_DATA[1][1], player)


# =========================================================
#                       MAIN MENU
# =========================================================

while True: 

    choice = main_menu()

    match choice:

        case "1":

            while True:

                collection_choice = collection_menu()

                match collection_choice:

                    case "1":

                        show_collection(player.collection)
                        print("\n")

                    case "2": 

                        show_collection(player.collection)

                        try:
                            choice = int(input("\n> ")) - 1

                            if (
                                choice < 0
                                or choice >= len(player.collection)
                            ):
                                raise IndexError

                            player.collection[choice].show()

                            input(
                                "\nPress any key to go back...\n"
                            )

                        except (ValueError, IndexError):
                            print("Invalid option.")

                    case "3":
                        show_collection(player.collection)

                        try:
                            choice = int(input("\n> ")) - 1

                            if choice < 0 or choice >= len(player.collection):
                                raise IndexError

                            target = player.collection[choice]

                            dupe_list = get_compatible_dupes(target, player.collection)

                            if dupe_list:
                                
                                show_collection(dupe_list)
                                material_monster = int(input("Select the monster to be used as material:\n> ")) - 1

                                if material_monster < 0 or material_monster >= len(dupe_list):
                                    raise IndexError
                                
                                confirm = input(
                                    f"Use {dupe_list[material_monster].display_name} as material for Resonance? (y/n)\n> "
                                    ).strip().lower()
                                
                                if confirm == "y":

                                    if player.resonate_monster(target, dupe_list[material_monster]):

                                        print(
                                            f"{target.display_name} resonance is now Lvl {target.resonance}"
                                        )

                            else:
                                print("No compatible dupes available.")
                            
                        except (ValueError, IndexError): 
                            print("Invalid option.")

                    case "4":
                        show_collection(player.collection)

                        try:
                            choice = int(input("\n> ")) - 1

                            if choice < 0 or choice >= len(player.collection):
                                raise IndexError
                            
                            confirm = input(
                                f"\nDismantle {player.collection[choice].display_name} into Essence? (y/n)\n> "
                            )

                            if confirm == "y":

                                essence = player.dismantle_monster(player.collection[choice])

                                if essence is not None: 
                                    print(
                                        f"{essence.value} Essence added to your inventory.\n"
                                    )

                                else: 
                                    print(
                                        "This monster cannot be dismantled into Essence."
                                    )

                        except (ValueError, IndexError): 
                            print("Invalid option.")

                    case "5":
                        break

                    case _:
                        print("Invalid option.")

        case "2":
            unseal_interface(
                player
            )

        case "3":
            show_collection(player.collection)

            try:
                choice = int(input("\n> ")) - 1

                if choice < 0 or choice >= len(player.collection):
                    raise IndexError

                ally_monsters = [player.collection[choice]]

                enemy_monsters = [create_monster("drake_abyssal")]

                outcome = battle(ally_monsters, enemy_monsters)

                if outcome == "victory":
                    print(f"{player.name} wins.")

                    exp_reward = sum(
                        enemy.get_exp_yield()
                        for enemy in enemy_monsters
                    )

                    monster = ally_monsters[0]

                    old_level = monster.level

                    monster.gain_exp(exp_reward)

                    print(f"{monster.display_name} gained {exp_reward} EXP.")

                    if monster.level > old_level:
                        print(
                            f"{monster.display_name} reached "
                            f"Lvl {monster.level}!"
                        )

                elif outcome == "run":
                    print(
                        f"{player.name} ran away."
                    )

                elif outcome == "defeat":
                    print(
                        f"{player.name} was defeated."
                    )

            except (ValueError, IndexError):
                print("Invalid option.")

        case "4":
            print("Codex")

        case "5":

            while True:

                inventory_choice = inventory_menu()

                match inventory_choice:

                    case "1":
                        show_sealstones(player.inventory)

                    case "2":
                        show_essences(player.inventory)

                    case "3":
                        break

                    case _:
                        print("Invalid option.")

        case "6":

            save_player(
                player,
                SAVE_PATH
            )

            break

        case _:
            print("Invalid option.")