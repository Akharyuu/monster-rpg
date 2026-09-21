import random

from ..data.monster_data import MONSTER_DATA
from ..data.sealstone_data import SEALSTONE_DATA

from ..factories.monster_factory import create_monster

from ..ui import (
    print_header,
    print_subheader,
    unseal_menu,
    wait_for_input
)


# =========================================================
#                    UNSEALING INTERFACE
# =========================================================

def unseal_interface(
    player,
    forced_monster_id=None,
    required_sealstone_type=None,
    allow_cancel=True
):

    while True:

        print_header("UNSEALING")

        choice, available_sealstones = unseal_menu(
            player.inventory
        )

        try:
            sealstone_choice = int(choice) - 1

            # Last option = Back
            if sealstone_choice == len(available_sealstones):

                if allow_cancel:
                    return None

                print("\nYou must complete this Unsealing.")
                continue

            if (
                sealstone_choice < 0
                or sealstone_choice >= len(available_sealstones)
            ):
                raise IndexError

            sealstone = available_sealstones[sealstone_choice]

            # Used by Campaign tutorials.
            if (
                required_sealstone_type is not None
                and sealstone != required_sealstone_type
            ):
                print(
                    f"\nSelect the "
                    f"{required_sealstone_type.value} Sealstone."
                )
                continue

            if not player.inventory.has_item(sealstone):
                print("\nNot enough Sealstones.")
                continue

            print_subheader("BREAKING THE SEAL")

            monster = unseal(
                player,
                sealstone,
                forced_monster_id
            )

            wait_for_input()

            return monster

        except (ValueError, IndexError):
            print("\nInvalid option.")


# =========================================================
#                        UNSEALING
# =========================================================

def unseal(player, sealstone_type, forced_monster_id=None):

    if forced_monster_id is None: 

        monster_ids = []

        while not monster_ids:

            rarity = roll_rarity(sealstone_type)
            allowed_attributes = SEALSTONE_DATA[sealstone_type]["allowed_attributes"]

            for monster_id, monster_data in MONSTER_DATA.items():

                if monster_data["rarity"] == rarity and monster_data["attribute"] in allowed_attributes:
                    monster_ids.append(monster_id)

        monster_id = random.choice(monster_ids)
        monster = create_monster(monster_id)

    else: 
        monster = create_monster(forced_monster_id)

    player.collection.append(monster)
    player.inventory.remove_item(sealstone_type)

    print(f"{monster.display_name} successfully unsealed.")
    return monster


# =========================================================
#                     RARITY ROLLING
# =========================================================

def roll_rarity(sealstone_type):

    if sealstone_type not in SEALSTONE_DATA:
        raise ValueError(
            f"Unknown Sealstone type: {sealstone_type}"
        )

    data = SEALSTONE_DATA[sealstone_type]

    rarities = []
    weights = []

    for rarity, weight in data["rarities"].items():
        rarities.append(rarity)
        weights.append(weight)

    rolled_rarity = random.choices(
        rarities,
        weights=weights,
        k=1
    )[0]

    return rolled_rarity


