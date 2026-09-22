from .models.enums import SealstoneType, EssenceType


# =========================================================
#                        CONSTANTS
# =========================================================

UI_WIDTH = 54
BAR_WIDTH = 20



# =========================================================
#                       MAIN MENU
# =========================================================

def main_menu():
    print(
        "     Monster RPG\n\n"
        "1. Collection\n"
        "2. Unseal\n"
        "3. Battle\n"
        "4. Codex\n"
        "5. Inventory\n"
        "6. Save & Exit\n"
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



def unseal_menu(inventory):

    available_sealstones = []

    for sealstone in SealstoneType:
        if inventory.get_amount(sealstone) > 0:
            available_sealstones.append(sealstone)

    print("Select a Sealstone to unseal:\n")

    for i, sealstone in enumerate(available_sealstones, start=1):
        amount = inventory.get_amount(sealstone)

        print(
            f"{i}. {sealstone.value} "
            f"x{amount}"
        )

    print(f"{len(available_sealstones) + 1}. Back")

    return input("\n> "), available_sealstones



def inventory_menu():
    print(
        "1. Sealstones\n"
        "2. Essences\n"
        "3. Back\n"
    )

    return input("> ")


# =========================================================
#                       BATTLE STATE
# =========================================================

def show_battle_state(allies, enemies, active_monster=None, upcoming_monster=None):

    print("\n==============================")
    print("            BATTLE")
    print("==============================")

    # Allies
    for i, ally in enumerate(allies, start=1):
        if not ally.is_alive:
            continue

        markers = []

        if ally is active_monster:
            markers.append("ACTIVE")

        if ally is upcoming_monster:
            markers.append("UP NEXT")

        marker_text = f" [{' | '.join(markers)}]" if markers else ""

        print(f"\nALLY {i}{marker_text}")

        show_combat(ally, active_monster)
        show_status_effects(ally)
        show_combat_resources(ally)

    # Enemies
    for i, enemy in enumerate(enemies, start=1):
        if not enemy.is_alive:
            continue

        markers = []

        if enemy is active_monster:
            markers.append("ACTIVE")

        if enemy is upcoming_monster:
            markers.append("UP NEXT")

        marker_text = f" [{' | '.join(markers)}]" if markers else ""

        print(f"\nENEMY {i}{marker_text}")

        show_combat(enemy, active_monster)
        show_status_effects(enemy)
        show_combat_resources(enemy)

    print("\n------------------------------")


# =========================================================
#                   MONSTER COMBAT INFO
# =========================================================

def show_combat(monster, active_monster=None):

    print(
        f"{monster.display_name} | "
        f"Lvl {monster.level} | "
        f"HP: {monster.health}/{monster.max_health}"
    )

    health_percentage = (monster.health / monster.max_health * 100)

    print(
        f"HP [{draw_hp_bar(monster.health, monster.max_health)}] "
        f"{health_percentage:.0f}%"
    )

    action_gauge = monster.action_gauge

    if monster is active_monster:
        action_gauge = 1

    print(
        f"AG [{draw_action_gauge(action_gauge)} ] "
        f"{action_gauge * 100:.0f}%"
    )

    skill_texts = []

    for i, skill in enumerate(monster.skills, start=1):

        if skill.current_cooldown > 0:
            status = f"[CD:{skill.current_cooldown}]"
        else:
            status = "[READY]"

        skill_texts.append(
            f"[{i}] {skill.name} {status}"
        )

    print("Skills:", " | ".join(skill_texts))


# =========================================================
#                     STATUS EFFECTS
# =========================================================

def show_status_effects(monster):

    if monster.buffs:
        buffs = []

        for buff in monster.buffs:
            text = buff.name

            if buff.max_stacks > 1:
                text += f" x{buff.stacks}"

            text += f" ({buff.remaining_turns})"

            buffs.append(text)

        print("Buffs:", ", ".join(buffs))

    else:
        print("Buffs: -")


    if monster.debuffs:
        debuffs = []

        for debuff in monster.debuffs:
            text = debuff.name

            if debuff.max_stacks > 1:
                text += f" x{debuff.stacks}"

            text += f" ({debuff.remaining_turns})"

            debuffs.append(text)

        print("Debuffs:", ", ".join(debuffs))

    else:
        print("Debuffs: -")


# =========================================================
#                    COMBAT RESOURCES
# =========================================================

def show_combat_resources(monster):

    if not monster.combat_resources:
        return

    resources = []

    for name, value in monster.combat_resources.items():
        display_name = name.replace("_", " ").title()

        resources.append(
            f"{display_name}: {value}"
        )

    print("Resources:", " | ".join(resources))


# =========================================================
#                       COMBAT BARS
# =========================================================

def draw_hp_bar(health, max_health):

    if max_health <= 0:
        return "-" * BAR_WIDTH

    ratio = health / max_health
    ratio = max(0, min(ratio, 1))

    filled = int(ratio * BAR_WIDTH)
    empty = BAR_WIDTH - filled

    return ("█" * filled) + ("-" * empty)



def draw_action_gauge(action_gauge):

    action_gauge = max(0, min(action_gauge, 1))

    filled = int(action_gauge * BAR_WIDTH)
    empty = BAR_WIDTH - filled

    return ("▮" * filled) + ("·" * empty)


# =========================================================
#                      PLAYER INPUT
# =========================================================

def select_skill(monster):

    while True:

        choice = input("Choose skill:\n> ")

        if not choice.isdigit():
            print("The value entered is not a number.")
            continue

        number = int(choice)

        chosen_skill = monster.get_skill(number)

        if chosen_skill is None:
            print("That skill does not exist.")
            continue

        if monster.is_silenced and number != 1:
            print("Silence prevents using this skill.")
            continue

        if not chosen_skill.is_available():
            print(
                f"{chosen_skill.name} is on cooldown "
                f"({chosen_skill.current_cooldown} turns remaining)."
            )
            continue

        return chosen_skill



def select_enemy(enemies):

    alive_enemies = [
        enemy
        for enemy in enemies
        if enemy.is_alive
    ]

    print("\nChoose target:")

    for i, enemy in enumerate(alive_enemies, start=1):
        print(
            f"[{i}] {enemy.display_name} "
            f"HP: {enemy.health}/{enemy.max_health}"
        )

    while True:

        choice = input("> ")

        if not choice.isdigit():
            print("Invalid target.")
            continue

        index = int(choice) - 1

        if 0 <= index < len(alive_enemies):
            return alive_enemies[index]

        print("Invalid target.")



def select_ally(allies):

    alive_allies = [
        ally
        for ally in allies
        if ally.is_alive
    ]

    print("\nChoose ally:")

    for i, ally in enumerate(alive_allies, start=1):
        print(
            f"[{i}] {ally.display_name} "
            f"HP: {ally.health}/{ally.max_health}"
        )

    while True:

        choice = input("> ")

        if not choice.isdigit():
            print("Invalid target.")
            continue

        index = int(choice) - 1

        if 0 <= index < len(alive_allies):
            return alive_allies[index]

        print("Invalid target.")


# =========================================================
#                      COMBAT EVENTS
# =========================================================

def show_combat_event(actor_name, skill_name, messages):

    print(f"\n{actor_name} used {skill_name}!")

    for message in messages:
        print(f"→ {message}")

    print()



def show_damage_skill_result(actor, skill, skill_result):

    messages = []

    multiple_targets = len(skill_result.target_results) > 1

    for target_index, target_result in enumerate(
        skill_result.target_results,
        start=1
    ):

        target = target_result["target"]
        hit_results = target_result["hit_results"]
        total_damage = target_result["total_damage"]
        effects_applied = target_result["effects_applied"]

        if multiple_targets:
            target_prefix = f"{target.display_name}: "
        else:
            target_prefix = ""

        # Damage / hits
        if len(hit_results) > 1:

            for hit_index, hit in enumerate(hit_results, start=1):

                if hit["critical"]:
                    messages.append(
                        f"{target_prefix}"
                        f"Hit {hit_index}: CRITICAL! "
                        f"{hit['damage']} damage"
                    )

                else:
                    messages.append(
                        f"{target_prefix}"
                        f"Hit {hit_index}: "
                        f"{hit['damage']} damage"
                    )

            messages.append(
                f"{target_prefix}Total: {total_damage} damage"
            )

        else:

            if hit_results[0]["critical"]:
                messages.append(
                    f"{target_prefix}"
                    f"CRITICAL! {total_damage} damage"
                )

            else:
                messages.append(
                    f"{target_prefix}"
                    f"{total_damage} damage"
                )

        # Effects
        shown_effect_ids = set()

        for effect in effects_applied:

            if effect.effect_id in shown_effect_ids:
                continue

            shown_effect_ids.add(effect.effect_id)

            text = f"{target_prefix}{effect.name}"

            if effect.max_stacks > 1:
                text += f" x{effect.stacks}"

            text += f" ({effect.remaining_turns} turns)"

            messages.append(text)

    for event in skill_result.events:

        if event["type"] == "heal":

            target = event["target"]
            value = event["value"]

            messages.append(
                f"{target.display_name} recovered "
                f"{value} HP"
            )

    show_combat_event(
        actor.display_name,
        skill.name,
        messages
    )


# =========================================================
#                      COLLECTION UI
# =========================================================

def show_collection(collection):

    for i, monster in enumerate(collection, start=1):
        print(
            f"{i}. {monster.display_name} | Lvl {monster.level} | {'★' * monster.rarity} | R{monster.resonance}"
        )


# =========================================================
#                      INVENTORY UI
# =========================================================

def show_sealstones(inventory):
    for sealstone in SealstoneType:
        amount = inventory.get_amount(sealstone)
        print(f"{sealstone.value} Sealstone x{amount}")



def show_essences(inventory):
    for essence in EssenceType:
        amount = inventory.get_amount(essence)
        print(f"{essence.value} Essence x{amount}")


# =========================================================
#                       DIALOG UI
# =========================================================

def print_header(title):
    print()
    print("=" * UI_WIDTH)
    print(title.center(UI_WIDTH))
    print("=" * UI_WIDTH)



def print_subheader(title):
    print()
    print("-" * UI_WIDTH)
    print(title.center(UI_WIDTH))
    print("-" * UI_WIDTH)



def wait_for_input(message="[ENTER] Continue"):
    input(f"\n{message} ")



def display_dialog(dialog, player):

    for line in dialog:

        if line["speaker"] == "player":
            speaker = player.name
        else:
            speaker = line["speaker"].replace("_", " ").title()

        print(f"\n{speaker.upper()}")
        print(f"  {line['text']}")

        input("\n  ▸ ")