from game.ui import main_menu, collection_menu, summon_menu, inventory_menu, show_essences, show_sealstones
from game.monster_factory import create_monster
from game.systems.summoning import summon
from game.models.enums import SealstoneType
from game.systems.collection import get_compatible_dupes
from game.systems.player import Player
from game.combat.combat import battle


def show_collection(collection):
    for i, monster in enumerate(collection, start=1):
        print(f"{i}. {monster.display_name} | Lvl {monster.level} | {'★' * monster.rarity} | R{monster.resonance}")


from game.models.glyphs import Glyph

def test_glyph_sets(monster):

    def clear_glyphs():
        for slot in range(1, 6):
            monster.unequip_glyph(slot)

    def make_glyph(slot, set_id, main_stat):
        return Glyph(
            slot_id=slot,
            set_id=set_id,
            main_stat=main_stat,
            sub_stats=[],
            rarity="legendary",
            level=0
        )

    print("\n==============================")
    print("TEST 1: 2 FURY")
    print("==============================")

    clear_glyphs()

    # Usamos mains que NO modifican ATK,
    # para aislar exclusivamente el bonus de Fury.
    monster.equip_glyph(
        make_glyph(1, "fury", "HP")
    )

    monster.equip_glyph(
        make_glyph(2, "fury", "DEF%")
    )

    print("Active sets:", monster.get_active_sets())

    expected_attack = monster.attack * 1.15
    actual_attack = monster.get_equipped_stat("attack")

    print("Base ATK:", monster.attack)
    print(f"Expected ATK: {expected_attack:.2f}")
    print(f"Actual ATK:   {actual_attack:.2f}")


    print("\n==============================")
    print("TEST 2: 4 FURY")
    print("==============================")

    clear_glyphs()

    monster.equip_glyph(
        make_glyph(1, "fury", "HP")
    )

    monster.equip_glyph(
        make_glyph(2, "fury", "DEF%")
    )

    monster.equip_glyph(
        make_glyph(3, "fury", "DEF")
    )

    monster.equip_glyph(
        make_glyph(4, "fury", "CR")
    )

    print("Active sets:", monster.get_active_sets())

    # 4 Fury = 2 activaciones
    # 15% + 15% = 30%
    expected_attack = monster.attack * 1.30
    actual_attack = monster.get_equipped_stat("attack")

    print("Base ATK:", monster.attack)
    print(f"Expected ATK: {expected_attack:.2f}")
    print(f"Actual ATK:   {actual_attack:.2f}")


    print("\n==================================")
    print("TEST 3: FORTITUDE + VELOCITY")
    print("==================================")

    clear_glyphs()

    # También usamos mains que no alteran
    # HP, DEF ni SPD.
    monster.equip_glyph(
        make_glyph(1, "fortitude", "ATK")
    )

    monster.equip_glyph(
        make_glyph(2, "fortitude", "ATK%")
    )

    monster.equip_glyph(
        make_glyph(3, "velocity", "ATK")
    )

    monster.equip_glyph(
        make_glyph(4, "velocity", "CR")
    )

    print("Active sets:", monster.get_active_sets())

    expected_hp = monster.health * 1.08
    expected_def = monster.defense * 1.05
    expected_speed = monster.speed + 10

    actual_hp = monster.get_equipped_stat("health")
    actual_def = monster.get_equipped_stat("defense")
    actual_speed = monster.get_equipped_stat("speed")

    print("\nHP")
    print("Base:", monster.health)
    print(f"Expected: {expected_hp:.2f}")
    print(f"Actual:   {actual_hp:.2f}")

    print("\nDEF")
    print("Base:", monster.defense)
    print(f"Expected: {expected_def:.2f}")
    print(f"Actual:   {actual_def:.2f}")

    print("\nSPD")
    print("Base:", monster.speed)
    print(f"Expected: {expected_speed:.2f}")
    print(f"Actual:   {actual_speed:.2f}")

    clear_glyphs()

player = Player("Ryuu")
player.collection.append(create_monster("drake_igneous"))
player.collection.append(create_monster("drake_abyssal"))
allies = [
    player.collection[0],
    player.collection[1]
]
enemies = [
    create_monster("piñata"),
    create_monster("drake_storm")
]

test_glyph_sets(player.collection[0])


#battle(allies, enemies)
player.inventory.add_item(SealstoneType.ARCANE, 20)


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
            break

        case _:
            print("Invalid option.")