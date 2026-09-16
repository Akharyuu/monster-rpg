from .enums import SealstoneType, EssenceType

#MAIN MENU:
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


#BATTLE UI:
def show_battle_state(allies, enemies, active_ally):
    print("\n==============================")
    print("            BATTLE")
    print("==============================")

    # Show all living allies.
    for i, ally in enumerate(allies, start=1):
        if not ally.is_alive:
            continue

        if ally is active_ally:
            print(f"\nALLY {i} [ACTIVE]")
        else:
            print(f"\nALLY {i}")
            
        show_combat(ally)
        show_status_effects(ally)
        show_combat_resources(ally)

    # Show all living enemies.
    for i, enemy in enumerate(enemies, start=1):
        if not enemy.is_alive:
            continue

        print(f"\nENEMY {i}")
        show_combat(enemy)
        show_status_effects(enemy)
        show_combat_resources(enemy)

    print("------------------------------")


def show_combat(monster):
    print(
        f"{monster.display_name} | "
        f"Lvl {monster.level} | "
        f"HP: {monster.health}/{monster.max_health}"
    )

    print(f"[{draw_hp_bar(monster.health, monster.max_health)}]")

    skill_texts = []

    for i, skill in enumerate(monster.skills, start=1):
        skill_texts.append(f"[{i}] {skill.name} CD:{skill.current_cooldown}")

    print("Skills:", " | ".join(skill_texts))


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


def draw_hp_bar(health, max_health):
    filled = int((health / max_health) * 20)
    empty = 20 - filled

    return (filled * "█") + (empty * "-")


def select_skill(monster):

    while True:
        number = input("Que habilidad quieres usar?\n> ")

        try: 
            number = int(number)

            chosen_skill = monster.get_skill(number)
            if chosen_skill is None: 
                print("El número seleccionado no existe.")
                continue

            if monster.is_silenced and number != 1:
                print("Silence prevents using this skill.")
                continue
            
            return chosen_skill

        except ValueError: 
            print("El valor introducido no es un número.")
            continue


def select_enemy(enemies):
    alive_enemies = [enemy for enemy in enemies if enemy.is_alive]

    print("\nChoose target:")

    for i, enemy in enumerate(alive_enemies, start=1):
        print(
            f"[{i}] {enemy.display_name} "
            f"HP: {enemy.health}/{enemy.max_health}"
        )

    while True:
        choice = input("> ")

        if choice.isdigit():
            index = int(choice) - 1

            if 0 <= index < len(alive_enemies):
                return alive_enemies[index]

        print("Invalid target.")


def select_ally(allies):
    alive_allies = [
        ally for ally in allies
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

        if choice.isdigit():
            index = int(choice) - 1

            if 0 <= index < len(alive_allies):
                return alive_allies[index]

        print("Invalid target.")


def show_combat_event(actor_name, skill_name, messages):
    print(f"{actor_name} used {skill_name}!")

    for message in messages:
        print(f"→ {message}")

    print()


def show_damage_skill_result(actor, skill, skill_result):
    messages = []

    for target_index, target_result in enumerate(skill_result.target_results, start=1):
        target = target_result["target"]
        hit_results = target_result["hit_results"]
        any_critical = target_result["any_critical"]
        total_damage = target_result["total_damage"]
        effects_applied = target_result["effects_applied"] 

        if len(skill_result.target_results) > 1:
            target_prefix = f"Enemy {target_index}: "
        else:
            target_prefix = ""

        #Damage/hits
        if len(hit_results) > 1:
            for i, hit in enumerate(hit_results, start=1):
                if hit["critical"]:
                    messages.append(
                        f"{target_prefix}Hit {i}: CRITICAL! {target.display_name} took {hit['damage']} damage"
                    )
                else:
                    messages.append(
                        f"{target_prefix}Hit {i}: {target.display_name} took {hit['damage']} damage"
                    )

            messages.append(
                f"{target_prefix}Total: {total_damage} damage"
            )

        else:
            if any_critical:
                messages.append(
                    f"{target_prefix}CRITICAL! {target.display_name} took {total_damage} damage"
                )
            else:
                messages.append(
                    f"{target_prefix}{target.display_name} took {total_damage} damage"
                )

        #Effects
        shown_effect_ids = []

        for effect in effects_applied:
            if effect.effect_id in shown_effect_ids:
                continue

            shown_effect_ids.append(effect.effect_id)

            text = f"{target_prefix}{effect.name}"

            if effect.max_stacks > 1:
                text += f" x{effect.stacks}"

            text += f" ({effect.remaining_turns} turns)"

            messages.append(text)

    show_combat_event(
        actor.display_name,
        skill.name,
        messages
    )


def show_combat_resources(monster):
    if not monster.combat_resources:
        return

    resources = []

    for name, value in monster.combat_resources.items():
        display_name = name.replace("_", " ").title()
        resources.append(f"{display_name}: {value}")

    print("Resources:", " | ".join(resources))


#INVENTORY UI:
def show_sealstones(inventory):
    for sealstone in SealstoneType:
        amount = inventory.get_amount(sealstone)
        print(f"{sealstone.value} Sealstone x{amount}")


def show_essences(inventory):
    for essence in EssenceType:
        amount = inventory.get_amount(essence)
        print(f"{essence.value} Essence x{amount}")


