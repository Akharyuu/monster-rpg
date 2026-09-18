from game.ui import main_menu, collection_menu, summon_menu, inventory_menu, show_essences, show_sealstones
from game.factories.monster_factory import create_monster
from game.factories.glyph_factory import create_glyph
from game.systems.summoning import summon
from game.models.enums import SealstoneType
from game.systems.collection import get_compatible_dupes
from game.systems.player import Player
from game.combat.combat import battle
from game.persistence.save_manager import save_player, load_player
from pathlib import Path


def show_collection(collection):
    for i, monster in enumerate(collection, start=1):
        print(f"{i}. {monster.display_name} | Lvl {monster.level} | {'★' * monster.rarity} | R{monster.resonance}")


SAVE_PATH = Path("save.json")


if SAVE_PATH.exists():
    player = load_player(SAVE_PATH)
else:
    player = Player("Ryuu")


#Menú Loop

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
                            player.collection[choice].show()
                            input("\nPress any key to go back...\n")

                        except ValueError: 
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
                                
                                confirm = input(f"Use {dupe_list[material_monster].display_name} as material for Resonance? (y/n)\n> ")
                                if confirm == "y":
                                    if player.resonate_monster(target, dupe_list[material_monster]):
                                        print(f"{target.display_name} resonance is now Lvl {target.resonance}")

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
                            
                            confirm = input(f"\nDismantle {player.collection[choice].display_name} into Essence? (y/n)\n> ")
                            if confirm == "y":
                                essence = player.dismantle_monster(player.collection[choice])
                                if essence is not None: 
                                    print(f"{essence.value} Essence added to your inventory.\n")
                                else: 
                                    print("This monster cannot be dismantled into Essence.")

                        except (ValueError, IndexError): 
                            print("Invalid option.")

                    case "5":
                        break

                    case _:
                        print("Invalid option.")

        case "2":
                show_sealstones(player.inventory)
                sealstones = list(SealstoneType)

                while True:
                    try: 
                        sealstone_choice = int(summon_menu()) - 1

                        if sealstone_choice == len(sealstones):
                            break

                        if sealstone_choice < 0 or sealstone_choice >= len(sealstones):
                            raise IndexError
                        
                        sealstone = sealstones[sealstone_choice]
                        if player.inventory.has_item(sealstone):
                            summon(player, sealstone)
                            break

                        else:
                            print("Not enough Sealstones.")

                    except (ValueError, IndexError):
                        print("Invalid option.")

        case "3":
            print("Battle")

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