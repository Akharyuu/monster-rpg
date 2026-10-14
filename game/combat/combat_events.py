from ..combat.passive_triggers import trigger_passives


# =========================================================
#                       DEATH EVENTS
# =========================================================

def notify_monster_death(monster, telemetry=None):

    if getattr(
        monster,
        "_death_recorded",
        False
    ):
        return

    monster._death_recorded = True

    battle_state = getattr(
        monster,
        "_battle_state",
        None
    )

    if battle_state is not None:
        battle_state["death_counter"] = (
            battle_state.get(
                "death_counter",
                0
            )
            + 1
        )

        monster.death_order = (
            battle_state[
                "death_counter"
            ]
        )

        dead_monster_ids = battle_state.setdefault(
            "dead_monster_ids",
            set()
        )

        dead_monster_ids.add(
            monster.instance_id
        )

    named_by = monster.special_states.get(
        "named_by"
    )

    if named_by is not None:
        monster.banished = True

    combatants = []

    for combatant in (
        getattr(
            monster,
            "_combat_team",
            []
        )
        + getattr(
            monster,
            "_combat_opponents",
            []
        )
    ):
        if combatant not in combatants:
            combatants.append(
                combatant
            )

    for combatant in combatants:

        if not combatant.is_alive:
            continue

        trigger_passives(
            "on_any_death",
            combatant,
            {
                "dead_monster": monster,
                "telemetry": telemetry
            }
        )

    # A normal Named mark disappears when its target dies.
    # Death March may already have transferred it during the death event.
    if (
        named_by is not None
        and named_by.special_states.get(
            "named_target"
        ) is monster
    ):
        named_by.clear_named_target()



# =========================================================
#                       REVIVE EVENTS
# =========================================================

def revive_monster(
    monster,
    health_ratio,
    action_gauge=0
):

    if monster.is_alive:
        return False

    if monster.banished:
        return False

    monster.health = max(
        1,
        int(
            monster.max_health
            * health_ratio
        )
    )

    monster._death_recorded = False
    monster.death_order = None

    if action_gauge > 0:
        monster.increase_action_gauge(
            action_gauge
        )

    return True
