# =========================================================
#                    DAMAGE MODIFIERS
# =========================================================

def get_passive_damage_multiplier(owner):

    damage_multiplier = 1.0

    for passive in owner.passives:

        if passive.handler != "thunderheart":
            continue

        data = passive.handler_data

        bonus_speed = max( 0, owner.get_effective_stat("speed") - owner.speed )

        damage_multiplier *= ( 1 + bonus_speed * data["damage_per_bonus_speed"] )

    return damage_multiplier


# =========================================================
#                    HEALING MODIFIERS
# =========================================================

def get_direct_heal_multiplier(owner, target):

    healing_multiplier = 1.0

    for passive in owner.passives:

        if passive.handler != "natures_grace":
            continue

        data = passive.handler_data

        target_hp_ratio = ( target.health / target.max_health )

        if target_hp_ratio < data["hp_threshold"]:

            healing_multiplier *= data["healing_multiplier"]

    return healing_multiplier


# =========================================================
#                   OVERHEAL MODIFIERS
# =========================================================

def get_overgrowth_shield(owner, target, intended_heal, actual_heal):

    for passive in owner.passives:

        if passive.handler != "natures_grace":
            continue

        data = passive.handler_data
        overgrowth = data.get("overgrowth")

        if overgrowth is None:
            continue

        overheal = max( 0, intended_heal - actual_heal)

        if overheal == 0:
            return 0, 0

        shield_amount = int( overheal * overgrowth["overheal_conversion"] )

        max_shield = int( target.max_health * overgrowth["max_shield_ratio"] )

        shield_amount = min( shield_amount, max_shield )

        return shield_amount, overgrowth["shield_turns"]

    return 0, 0


# =========================================================
#                     STAT MODIFIERS
# =========================================================

def get_passive_stat_bonus(owner, stat):

    bonus = 0

    if stat != "crit_rate":
        return bonus

    for passive in owner.passives:

        if passive.handler != "thunderheart":
            continue

        data = passive.handler_data

        if "speed_per_crit" not in data:
            continue

        bonus_speed = max( 0, owner.get_effective_stat("speed") - owner.speed )

        crit_rate_bonus = ( bonus_speed // data["speed_per_crit"] )

        crit_rate_bonus = min( crit_rate_bonus, data["max_crit_rate_bonus"] )

        bonus += crit_rate_bonus

    return bonus

