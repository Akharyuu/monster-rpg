from game.ui import main_menu, collection_menu, summon_menu, inventory_menu, show_essences, show_sealstones
from game.factories import create_monster
from game.summoning import summon
from game.enums import SealstoneType, EssenceType
from game.collection import dismantle_monster, resonate_monster, get_compatible_dupes
from game.inventory import Inventory

collection = []
inventory = Inventory()

monster = create_monster("drake_abyssal")
collection.append(monster)
inventory.add_item(SealstoneType.ARCANE, 10)

def show_collection(collection):
    for i, monster in enumerate(collection, start=1):
        print(f"{i}. {monster.display_name} | Lvl {monster.level} | {'★' * monster.rarity} | R{monster.resonance}")




#Menú Loop

while True: 
    choice = main_menu()

    match choice:
        case "1":
            while True:
                collection_choice = collection_menu()

                match collection_choice:
                    case "1":
                        show_collection(collection)
                        print("\n")

                    case "2": 
                        show_collection(collection)

                        try:
                            choice = int(input("\n> ")) - 1
                            collection[choice].show()
                            input("\nPress any key to go back...\n")

                        except ValueError: 
                            print("Invalid option.")

                    case "3":
                        show_collection(collection)

                        try:
                            choice = int(input("\n> ")) - 1
                            if choice < 0 or choice >= len(collection):
                                raise IndexError

                            target = collection[choice]

                            dupe_list = get_compatible_dupes(target, collection)

                            if dupe_list:
                                show_collection(dupe_list)

                                material_monster = int(input("Select the monster to be used as material:\n> ")) - 1
                                if material_monster < 0 or material_monster >= len(dupe_list):
                                    raise IndexError
                                
                                confirm = input(f"Use {dupe_list[material_monster].display_name} as material for Resonance? (y/n)\n> ")
                                if confirm == "y":
                                    if resonate_monster(target, dupe_list[material_monster], collection):
                                        print(f"{target.display_name} resonance is now Lvl {target.resonance}")

                            else:
                                print("No compatible dupes available.")
                            
                        except (ValueError, IndexError): 
                            print("Invalid option.")

                    case "4":
                        show_collection(collection)

                        try:
                            choice = int(input("\n> ")) - 1
                            if choice < 0 or choice >= len(collection):
                                raise IndexError
                            
                            confirm = input(f"\nDismantle {collection[choice].display_name} into Essence? (y/n)\n> ")
                            if confirm == "y":
                                essence = dismantle_monster(collection[choice], collection, inventory)
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
                show_sealstones(inventory)
                sealstones = list(SealstoneType)

                while True:
                    try: 
                        sealstone_choice = int(summon_menu()) - 1

                        if sealstone_choice == len(sealstones):
                            break
                        
                        if sealstone_choice < 0 or sealstone_choice >= len(sealstones):
                            raise IndexError
                        
                        sealstone = sealstones[sealstone_choice]
                        if inventory.has_item(sealstone):
                            inventory.remove_item(sealstone)
                            summon(collection, sealstone)
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
                        show_sealstones(inventory)

                    case "2":
                        show_essences(inventory)

                    case "3":
                        break

                    case _:
                        print("Invalid option.")

        case "6":
            break

        case _:
            print("Invalid option.")