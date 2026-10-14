from ..factories.status_effect_factory import create_status_effect
from ..combat.combat_events import revive_monster
from ..combat.passive_triggers import trigger_passives
from ..combat.passive_modifiers import get_direct_heal_multiplier, get_overgrowth_shield
from ..combat.telemetry import get_active_shield_value, record_telemetry


# =========================================================
#                     HEALING HANDLERS
# =========================================================

def heal_lowest_hp_ally(caster, skill, data, context, skill_result):

    team = context["team"]

    living_allies = [
        ally
        for ally in team
        if ally.is_alive
    ]

    if not living_allies:
        return None

    target = min(
        living_allies,
        key=lambda ally: ally.health / ally.max_health
    )

    heal_amount = int( caster.get_healing_hp() * data["healing_hp_ratio"] )

    healing_multiplier = get_direct_heal_multiplier(caster, target)

    heal_amount = int( heal_amount * healing_multiplier )

    actual_heal = target.heal(heal_amount)

    record_telemetry(
        context.get("telemetry"),
        caster,
        "healing",
        actual_heal
    )

    shield_amount, shield_turns = get_overgrowth_shield(caster, target, heal_amount, actual_heal)

    if shield_amount > 0:

        shield_before = get_active_shield_value(
            target
        )

        shield = create_status_effect(
            effect_id="shield",
            duration=shield_turns,
            source=caster,
            value=shield_amount
        )

        target.apply_status_effect(shield)

        shield_after = get_active_shield_value(
            target
        )

        record_telemetry(
            context.get("telemetry"),
            caster,
            "shield_generated",
            max(0, shield_after - shield_before)
        )

    return {
        "type": "heal",
        "target": target,
        "value": actual_heal
    }



def heal_all_allies(caster, skill, data, context, skill_result):

    team = context["team"]

    base_heal_amount = int( caster.get_healing_hp() * data["healing_hp_ratio"] )

    heal_results = []

    for ally in team:

        if not ally.is_alive:
            continue

        healing_multiplier = get_direct_heal_multiplier(caster, ally)

        heal_amount = int( base_heal_amount * healing_multiplier )

        actual_heal = ally.heal(heal_amount)

        record_telemetry(
            context.get("telemetry"),
            caster,
            "healing",
            actual_heal
        )

        shield_amount, shield_turns = get_overgrowth_shield(caster, ally, heal_amount, actual_heal)

        if shield_amount > 0:

            shield_before = get_active_shield_value(
                ally
            )

            shield = create_status_effect(
                effect_id="shield",
                duration=shield_turns,
                source=caster,
                value=shield_amount
            )

            ally.apply_status_effect(shield)

            shield_after = get_active_shield_value(
                ally
            )

            record_telemetry(
                context.get("telemetry"),
                caster,
                "shield_generated",
                max(0, shield_after - shield_before)
            )

        heal_results.append({
            "target": ally,
            "value": actual_heal
        })

    return {
        "type": "team_heal",
        "heal_results": heal_results
    }


# =========================================================
#                      BUFF HANDLERS
# =========================================================

def apply_self_buff(caster, skill, data, context, skill_result):

    status_effect = create_status_effect(
        effect_id=data["effect_id"],
        duration=data["turns"],
        stacks=data.get("stacks", 1),
        source=caster
    )

    caster.apply_status_effect(
        status_effect,
        telemetry=context.get("telemetry")
    )



def apply_aoe_buff(caster, skill, data, context, skill_result):

    team = context["team"]

    for ally in team:

        if not ally.is_alive:
            continue

        status_effect = create_status_effect(
            effect_id=data["effect_id"],
            duration=data["turns"],
            stacks=data.get("stacks", 1),
            source=caster
        )

        ally.apply_status_effect(
            status_effect,
            telemetry=context.get("telemetry")
        )


# =========================================================
#                     ATTACK HANDLERS
# =========================================================

def aoe_follow_up_attack(caster, skill, data, context, skill_result):

    opponents = context["opponents"]

    living_opponents = [
        opponent
        for opponent in opponents
        if opponent.is_alive
    ]

    if not living_opponents:
        return None

    target_results = []

    for target in living_opponents:

        target_result = skill.create_target_result(target)

        target_result["telemetry"] = (
            context.get("telemetry")
        )

        skill.resolve_hit(
            caster,
            target,
            skill.hits,
            target_result,
            hit_multiplier_override=data.get(
                "damage_multiplier",
                1
            ),
            apply_repeated_target_damage=False
        )

        if target.is_alive:

            for effect in data.get("effects", []):

                applied_effect = skill.try_apply_effect(
                    effect,
                    caster,
                    target,
                    target_result["snapshot"]
                )

                if applied_effect is not None:
                    target_result["effects_applied"].append(applied_effect)

        target_results.append(target_result)

    return {
        "type": "aoe_follow_up_attack",
        "target_results": target_results
    }


# =========================================================
#                     ATTACK HANDLERS
# =========================================================

def increase_action_gauge(caster, skill, data, context, skill_result):
    caster.increase_action_gauge(data["amount"])




# =========================================================
#                    AETHER DRAKE HANDLERS
# =========================================================

def apply_scaling_silence(
    caster,
    skill,
    data,
    context,
    skill_result
):

    buff_count = len(
        caster.buffs
    )

    chance = (
        data["base_chance"]
        + buff_count
        * data["chance_per_buff"]
    )

    chance = min(
        chance,
        data["max_chance"]
    )

    applied_targets = []

    for target_result in skill_result.target_results:

        target = target_result["target"]

        if not target.is_alive:
            continue

        effect = {
            "effect_id": "silence",
            "chance": chance,
            "turns": data["turns"]
        }

        applied_effect = skill.try_apply_effect(
            effect,
            caster,
            target,
            target_result["snapshot"],
            target_result.get("telemetry")
        )

        if applied_effect is not None:
            target_result[
                "effects_applied"
            ].append(
                applied_effect
            )

            applied_targets.append(
                target
            )

    return {
        "type": "scaling_silence",
        "targets": applied_targets,
        "chance": chance
    }



def grant_extra_turn(
    caster,
    skill,
    data,
    context,
    skill_result
):

    caster.extra_turn_pending = True

    return {
        "type": "extra_turn"
    }


# =========================================================
#                     VOID DRAKE HANDLERS
# =========================================================

def banish_killed_oblivion_targets(
    caster,
    skill,
    data,
    context,
    skill_result
):

    banished_targets = []

    for target_result in skill_result.target_results:

        target = target_result["target"]

        if target.is_alive:
            continue

        starting_debuffs = (
            target_result
            .get("snapshot", {})
            .get("debuffs", {})
        )

        if "oblivion" not in starting_debuffs:
            continue

        target.banished = True

        banished_targets.append(
            target
        )

    return {
        "type": "banish",
        "targets": banished_targets
    }



# =========================================================
#                  DULLAHAN SUPPORT HANDLERS
# =========================================================

def support_lowest_gauge_ally(
    caster,
    skill,
    data,
    context,
    skill_result
):

    living_allies = [
        ally
        for ally in context.get(
            "team",
            []
        )
        if ally.is_alive
        and ally is not caster
    ]

    if not living_allies:
        living_allies = [
            caster
        ]

    target = min(
        living_allies,
        key=lambda ally:
            ally.action_gauge
    )

    for buff_config in data.get(
        "self_buffs",
        []
    ):

        buff = create_status_effect(
            effect_id=buff_config[
                "effect_id"
            ],
            duration=buff_config[
                "turns"
            ],
            source=caster
        )

        caster.apply_status_effect(
            buff
        )

    for buff_config in data.get(
        "ally_buffs",
        []
    ):

        buff = create_status_effect(
            effect_id=buff_config[
                "effect_id"
            ],
            duration=buff_config[
                "turns"
            ],
            source=caster
        )

        target.apply_status_effect(
            buff
        )

    target.increase_action_gauge(
        data.get(
            "ally_action_gauge",
            0
        )
    )

    if data.get(
        "force_next_turn",
        False
    ):
        target.forced_turn_pending = True

    return {
        "type":
            "support_lowest_gauge_ally",
        "target":
            target
    }



def revive_most_recent_ally(
    caster,
    skill,
    data,
    context,
    skill_result
):

    charges = getattr(
        skill,
        "_soul_charges_consumed",
        0
    )

    if charges <= 0:
        return None

    dead_allies = [
        ally
        for ally in context.get(
            "team",
            []
        )
        if not ally.is_alive
        and not ally.banished
        and ally.death_order is not None
    ]

    if not dead_allies:
        return None

    target = max(
        dead_allies,
        key=lambda ally:
            ally.death_order
    )

    charge_to_ratio = data[
        "health_ratio_by_charges"
    ]

    used_charges = min(
        charges,
        max(
            charge_to_ratio
        )
    )

    health_ratio = charge_to_ratio[
        used_charges
    ]

    revived = revive_monster(
        target,
        health_ratio,
        action_gauge=data.get(
            "action_gauge",
            0
        )
    )

    if not revived:
        return None

    return {
        "type": "revive",
        "target": target,
        "health_ratio":
            health_ratio
    }



def apply_team_buff(
    caster,
    skill,
    data,
    context,
    skill_result
):

    for ally in context.get(
        "team",
        []
    ):

        if not ally.is_alive:
            continue

        buff = create_status_effect(
            effect_id=data[
                "effect_id"
            ],
            duration=data[
                "turns"
            ],
            source=caster
        )

        ally.apply_status_effect(
            buff
        )



def follow_up_skill_on_kill(
    caster,
    skill,
    data,
    context,
    skill_result
):

    killed_target = any(
        not result["target"].is_alive
        for result in skill_result.target_results
    )

    if not killed_target:
        return None

    opponents = [
        opponent
        for opponent in context.get(
            "opponents",
            []
        )
        if opponent.is_alive
    ]

    if not opponents:
        return None

    target = min(
        opponents,
        key=lambda opponent:
            opponent.health
            / opponent.max_health
    )

    follow_up = caster.get_skill(
        data["skill_slot"]
    )

    if follow_up is None:
        return None

    follow_context = dict(
        context
    )

    follow_context[
        "skill"
    ] = follow_up

    follow_context[
        "targets"
    ] = [
        target
    ]

    trigger_passives(
        "before_skill",
        caster,
        follow_context
    )

    result = follow_up.execute(
        caster,
        [
            target
        ],
        follow_context
    )

    follow_context[
        "skill_result"
    ] = result

    trigger_passives(
        "after_skill",
        caster,
        follow_context
    )

    return {
        "type": "follow_up_skill",
        "target": target,
        "skill": follow_up,
        "result": result
    }


# =========================================================
#                      HANDLER REGISTRY
# =========================================================

AFTER_USE_HANDLERS = {
    "heal_lowest_hp_ally": heal_lowest_hp_ally,
    "heal_all_allies": heal_all_allies,
    "apply_self_buff": apply_self_buff,
    "apply_aoe_buff": apply_aoe_buff,
    "aoe_follow_up_attack": aoe_follow_up_attack,
    "increase_action_gauge": increase_action_gauge,
    "apply_scaling_silence": apply_scaling_silence,
    "grant_extra_turn": grant_extra_turn,
    "banish_killed_oblivion_targets":
        banish_killed_oblivion_targets,
    "support_lowest_gauge_ally":
        support_lowest_gauge_ally,
    "revive_most_recent_ally":
        revive_most_recent_ally,
    "apply_team_buff":
        apply_team_buff,
    "follow_up_skill_on_kill":
        follow_up_skill_on_kill
}