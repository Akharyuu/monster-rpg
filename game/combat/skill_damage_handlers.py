from ..combat.skill_effect_conditions import EFFECT_CONDITIONS


# =========================================================
#                     CONDITION DAMAGE
# =========================================================

def damage_if_condition(attacker, target, skill, snapshot, hit_index):

    data = skill.damage_handler_data
    condition = data["condition"]

    condition_handler = EFFECT_CONDITIONS[condition["type"]]

    condition_met = condition_handler(
        attacker,
        target,
        skill,
        condition,
        snapshot
    )

    if not condition_met:
        return {
            "damage_multiplier": 1
        }

    # Case 1: same multiplier for every hit.
    if "damage_multiplier" in data:
        return {
            "damage_multiplier": data["damage_multiplier"]
        }

    # Case 2: different multiplier depending on the hit.
    if "multipliers_by_hit" in data:

        hit_number = hit_index + 1

        return {
            "damage_multiplier": data["multipliers_by_hit"][hit_number]
        }

    return {
        "damage_multiplier": 1
    }


# =========================================================
#                    BURN STACKS DAMAGE
# =========================================================

def damage_for_burn_stacks(attacker, target, skill, snapshot, hit_index):

    for debuff in target.debuffs:

        if debuff.effect_id != "burn":
            continue

        multiplier = skill.damage_handler_data["multipliers_by_stacks"][debuff.stacks]

        result = {
            "damage_multiplier": multiplier
        }

        ignore_defense_at = (skill.damage_handler_data.get("ignore_defense_at_stacks"))

        if (
            ignore_defense_at is not None
            and debuff.stacks >= ignore_defense_at
        ):
            result["ignore_defense"] = True

        return result

    return {
        "damage_multiplier": 1
    }


# =========================================================
#                       STAT SCALING
# =========================================================

def damage_with_speed_scaling(attacker, target, skill, snapshot, hit_index):

    data = skill.damage_handler_data

    effective_speed = attacker.get_effective_stat("speed")

    damage_multiplier = ( 1 + effective_speed * data["speed_scaling"] )

    return {
        "damage_multiplier": damage_multiplier
    }


# =========================================================
#                  REMOVED BUFFS DAMAGE
# =========================================================

def damage_for_removed_buffs(
    attacker,
    target,
    skill,
    snapshot,
    hit_index
):

    data = skill.damage_handler_data

    if hit_index not in data[
        "affected_hit_indices"
    ]:
        return {
            "damage_multiplier": 1
        }

    if not getattr(
        skill,
        "_is_executing",
        False
    ):
        return {
            "damage_multiplier": 1
        }

    removed_buffs = getattr(
        skill,
        "_removed_buffs_this_use",
        0
    )

    voidborn_damage_bonus = getattr(
        skill,
        "_voidborn_damage_bonus_this_use",
        0
    )

    damage_multiplier = (
        1
        + removed_buffs
        * data["damage_per_removed_buff"]
        + voidborn_damage_bonus
    )

    return {
        "damage_multiplier":
            damage_multiplier
    }



# =========================================================
#                   DULLAHAN DAMAGE
# =========================================================

def damage_by_missing_health(
    attacker,
    target,
    skill,
    snapshot,
    hit_index
):

    data = skill.damage_handler_data

    health_ratio = snapshot.get(
        "health_ratio",
        (
            target.health
            / target.max_health
        )
    )

    missing_health_ratio = max(
        0,
        1 - health_ratio
    )

    bonus = (
        missing_health_ratio
        * data["max_bonus_damage"]
    )

    bonus = min(
        bonus,
        data["max_bonus_damage"]
    )

    return {
        "damage_multiplier":
            1 + bonus
    }



def execute_below_health_threshold(
    attacker,
    target,
    skill,
    snapshot,
    hit_index
):

    data = skill.damage_handler_data

    health_ratio = snapshot.get(
        "health_ratio",
        (
            target.health
            / target.max_health
        )
    )

    if health_ratio >= data[
        "health_threshold"
    ]:
        return {
            "damage_multiplier": 1
        }

    return {
        "damage_multiplier": 1,
        "defense_ignore_ratio":
            data.get(
                "defense_ignore_ratio",
                0
            )
    }



def damage_for_soul_charges(
    attacker,
    target,
    skill,
    snapshot,
    hit_index
):

    data = skill.damage_handler_data

    if data.get(
        "use_consumed_charges",
        False
    ):
        charges = getattr(
            skill,
            "_soul_charges_consumed",
            0
        )
    else:
        charges = attacker.get_combat_resource(
            "soul_charges"
        )

    charges = min(
        charges,
        data.get(
            "max_charges",
            5
        )
    )

    if (
        data.get(
            "disable_bonus_if_ally_dead",
            False
        )
        and any(
            not ally.is_alive
            for ally in getattr(
                attacker,
                "_combat_team",
                []
            )
            if ally is not attacker
        )
    ):

        allow_convergence = (
            data.get(
                "allow_bonus_with_dead_at_max",
                False
            )
            and charges
            >= data.get(
                "max_charges",
                5
            )
        )

        if not allow_convergence:
            charges = 0

    return {
        "damage_multiplier": (
            1
            + charges
            * data[
                "damage_per_charge"
            ]
        )
    }



def damage_for_dead_monsters(
    attacker,
    target,
    skill,
    snapshot,
    hit_index
):

    data = skill.damage_handler_data

    battle_state = getattr(
        attacker,
        "_battle_state",
        {}
    )

    deaths = battle_state.get(
        "death_counter",
        0
    )

    deaths = min(
        deaths,
        data.get(
            "max_dead_monsters",
            5
        )
    )

    bonus = (
        deaths
        * data[
            "damage_per_dead_monster"
        ]
    )

    bonus = min(
        bonus,
        data[
            "max_bonus_damage"
        ]
    )

    return {
        "damage_multiplier":
            1 + bonus
    }


# =========================================================
#                     HANDLER REGISTRY
# =========================================================

DAMAGE_HANDLERS = {
    "damage_for_burn_stacks": damage_for_burn_stacks,
    "damage_if_condition": damage_if_condition,
    "damage_with_speed_scaling": damage_with_speed_scaling,
    "damage_for_removed_buffs": damage_for_removed_buffs,
    "damage_by_missing_health": damage_by_missing_health,
    "execute_below_health_threshold":
        execute_below_health_threshold,
    "damage_for_soul_charges":
        damage_for_soul_charges,
    "damage_for_dead_monsters":
        damage_for_dead_monsters
}

