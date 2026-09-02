from .enums import SealstoneType, EssenceType

def main_menu():
    print(
        "     Monster RPG\n\n"
        "1. Collection\n"
        "2. Summon\n"
        "3. Battle\n"
        "4. Codex\n"
        "5. Inventory\n"
        "6. Exit\n"
    )

    return input("> ")


def collection_menu():
    print(
        "1. View monsters\n"
        "2. Monster details\n"
        "3. Resonance\n"
        "4. Dismantle\n"
        "5. Back\n"
    )

    return input("> ")


def summon_menu():
    sealstones = list(SealstoneType)

    print("Select a Sealstone to use for the summon:\n")
    for i, sealstone in enumerate(SealstoneType, start=1): 
        print(f"{i}. {sealstone.value}")

    print(f"{len(sealstones) + 1}. Back")

    return input("\n> ")


def inventory_menu():
    print(
        "1. Sealstones\n"
        "2. Essences\n"
        "3. Back\n"
    )

    return input("> ")

    




def select_skill(monster):

    while True:
        number = input("Que habilidad quieres usar?\n> ")

        try: 
            number = int(number)

            chosen_skill = monster.get_skill(number)
            if chosen_skill is None: 
                print("El número seleccionado no existe.")
                continue
            
            return chosen_skill

        except ValueError: 
            print("El valor introducido no es un número.")
            continue


def show_sealstones(inventory):
    for sealstone in SealstoneType:
        amount = inventory.get_amount(sealstone)
        print(f"{sealstone.value} Sealstone x{amount}")


def show_essences(inventory):
    for essence in EssenceType:
        amount = inventory.get_amount(essence)
        print(f"{essence.value} Essence x{amount}")


