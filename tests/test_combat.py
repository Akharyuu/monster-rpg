import random
import pytest
from game.combat.combat import simulate_battles

from game.factories.monster_factory import create_monster, create_passive, create_skill
from game.factories.status_effect_factory import create_status_effect
from game.data.passive_data import PASSIVE_DATA
from game.systems.resonance import update_resonance_kit
from game.combat.ai_conditions import (
    target_has_debuff,
    AI_CONDITIONS
)
from game.combat.combat import (
    battle,
    begin_turn,
    end_turn,
    simulate_battle,
    simulate_battles
)
from game.combat.enemy_ai import (
    check_setup_requirements,
    choose_skill,
    choose_enemy_target,
    estimate_damage,
    sees_kill
)
from game.combat.passive_modifiers import (
    get_passive_damage_multiplier,
    get_passive_stat_bonus
)
from game.combat.passive_triggers import trigger_passives
from game.combat.combat_events import notify_monster_death
from game.combat.skill_damage_handlers import DAMAGE_HANDLERS
from game.combat.telemetry import (
    create_battle_telemetry,
    serialize_battle_telemetry
)

import game.combat.combat as combat_module



def test_attack_up_is_multiplicative():

    monster = create_monster("drake_igneous")

    attack_before_buff = monster.get_equipped_stat("attack")

    attack_up = create_status_effect(
        effect_id="attack_up",
        duration=2,
        source=monster
    )

    monster.apply_status_effect(attack_up)

    expected_attack = attack_before_buff * 1.30

    assert monster.get_effective_stat("attack") == pytest.approx(
        expected_attack
    )



def test_crit_rate_up_is_additive():

    monster = create_monster("drake_igneous")

    crit_before_buff = monster.get_equipped_stat("crit_rate")

    crit_rate_up = create_status_effect(
        effect_id="crit_rate_up",
        duration=2,
        source=monster
    )

    monster.apply_status_effect(crit_rate_up)

    expected_crit_rate = crit_before_buff + 30

    assert monster.get_effective_stat("crit_rate") == pytest.approx(
        expected_crit_rate
    )



def test_immunity_blocks_debuff():

    monster = create_monster("drake_igneous")

    immunity = create_status_effect(
        effect_id="immunity",
        duration=2,
        source=monster
    )

    monster.apply_status_effect(immunity)

    freeze = create_status_effect(
        effect_id="freeze",
        duration=1
    )

    monster.apply_status_effect(freeze)

    assert immunity in monster.buffs
    assert freeze not in monster.debuffs



def test_action_gauge_is_clamped_between_zero_and_one():

    monster = create_monster("drake_igneous")

    monster.action_gauge = 0.95
    monster.increase_action_gauge(0.20)

    assert monster.action_gauge == pytest.approx(1.0)

    monster.reduce_action_gauge(2.0)

    assert monster.action_gauge == pytest.approx(0.0)



def test_combat_freeze_breaks_on_hit():

    monster = create_monster("drake_igneous")

    freeze = create_status_effect(
        effect_id="freeze",
        duration=1
    )

    monster.apply_status_effect(freeze)

    broken_effects = monster.receive_damage(1)

    assert freeze not in monster.debuffs
    assert freeze in broken_effects



def test_frostborne_preserves_freeze_on_hit():

    abyssal = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    abyssal.resonance = 2
    update_resonance_kit(abyssal)

    freeze = create_status_effect(
        effect_id="freeze",
        duration=1,
        source=abyssal
    )

    target.apply_status_effect(freeze)

    broken_effects = target.receive_damage(
        1,
        source=abyssal
    )

    assert freeze in target.debuffs
    assert broken_effects == []



def test_everlasting_winter_preserves_freeze_from_ally_damage():

    abyssal = create_monster(
        "drake_abyssal"
    )

    ally = create_monster(
        "drake_igneous"
    )

    target = create_monster(
        "drake_storm"
    )

    abyssal.resonance = 4
    update_resonance_kit(
        abyssal
    )

    freeze = create_status_effect(
        effect_id="freeze",
        duration=1,
        source=abyssal
    )

    target.apply_status_effect(
        freeze
    )

    target.receive_damage(
        1,
        source=ally
    )

    assert any(
        debuff.effect_id == "freeze"
        for debuff in target.debuffs
    )


def test_freeze_can_be_resisted(monkeypatch):

    abyssal = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    abyssal.accuracy = 0
    target.resistance = 100

    speed_break = create_status_effect(
        effect_id="speed_break",
        duration=2,
        source=abyssal
    )

    target.apply_status_effect(speed_break)

    # Hace que el 50% de Freeze siempre procée.
    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    # Tirada de resistencia extremadamente baja:
    # debe ser resistida.
    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 0.0
    )

    skill = abyssal.get_skill(3)

    skill.execute(
        abyssal,
        [target]
    )

    debuff_ids = [
        debuff.effect_id
        for debuff in target.debuffs
    ]

    assert "freeze" not in debuff_ids



def test_absolute_zero_ignores_resistance(monkeypatch):

    abyssal = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    abyssal.resonance = 5
    update_resonance_kit(abyssal)

    abyssal.accuracy = 0
    target.resistance = 100

    speed_break = create_status_effect(
        effect_id="speed_break",
        duration=2,
        source=abyssal
    )

    target.apply_status_effect(speed_break)

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    # Si R5 NO ignorase resistencia,
    # esta tirada provocaría resist.
    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 0.0
    )

    skill = abyssal.get_skill(3)

    skill.execute(
        abyssal,
        [target]
    )

    debuff_ids = [
        debuff.effect_id
        for debuff in target.debuffs
    ]

    assert "freeze" in debuff_ids



def test_flame_devourer_consumes_burn_and_heals(monkeypatch):

    igneous = create_monster("drake_igneous")
    target = create_monster("drake_abyssal")

    burn = create_status_effect(
        effect_id="burn",
        duration=3,
        stacks=3,
        source=igneous
    )

    target.apply_status_effect(burn)

    igneous.health = int(
        igneous.max_health * 0.20
    )

    health_before = igneous.health

    # Evita que Cinderblood vuelva a meter Burn
    # durante el propio ataque.
    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.99
    )

    skill = igneous.get_skill(3)

    skill.execute(
        igneous,
        [target]
    )

    burn_ids = [
        debuff.effect_id
        for debuff in target.debuffs
    ]

    assert "burn" not in burn_ids
    assert igneous.health > health_before



def test_flame_devourer_heals_even_if_target_dies(monkeypatch):

    igneous = create_monster("drake_igneous")
    target = create_monster("drake_abyssal")

    burn = create_status_effect(
        effect_id="burn",
        duration=3,
        stacks=3,
        source=igneous
    )

    target.apply_status_effect(burn)

    target.health = 1

    igneous.health = int(
        igneous.max_health * 0.20
    )

    health_before = igneous.health

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.99
    )

    skill = igneous.get_skill(3)

    skill.execute(
        igneous,
        [target]
    )

    assert target.is_alive is False
    assert igneous.health > health_before



def test_multihit_continues_after_target_dies(monkeypatch):

    abyssal = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    target.health = 1

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.99
    )

    skill = abyssal.get_skill(2)

    result = skill.execute(
        abyssal,
        [target]
    )

    target_result = result.target_results[0]

    assert target.is_alive is False

    assert len(
        target_result["hit_results"]
    ) == skill.hits



def test_dead_target_does_not_receive_per_hit_effects(monkeypatch):

    abyssal = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    target.health = 1

    # Fuerza los procs de Speed Break
    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    skill = abyssal.get_skill(2)

    skill.execute(
        abyssal,
        [target]
    )

    debuff_ids = [
        debuff.effect_id
        for debuff in target.debuffs
    ]

    assert "speed_break" not in debuff_ids



def test_cooldowns_reduce_at_start_of_turn():

    monster = create_monster("drake_igneous")

    skill = monster.get_skill(2)

    skill.current_cooldown = 3

    begin_turn(monster)

    assert skill.current_cooldown == 2



def test_effect_applied_during_turn_does_not_lose_duration():

    monster = create_monster("drake_igneous")

    turn_context = begin_turn(monster)

    attack_up = create_status_effect(
        effect_id="attack_up",
        duration=2,
        source=monster
    )

    monster.apply_status_effect(attack_up)

    end_turn(
        monster,
        turn_context
    )

    assert attack_up.remaining_turns == 2



def test_effect_present_at_turn_start_loses_duration():

    monster = create_monster("drake_igneous")

    attack_up = create_status_effect(
        effect_id="attack_up",
        duration=2,
        source=monster
    )

    monster.apply_status_effect(attack_up)

    turn_context = begin_turn(monster)

    end_turn(
        monster,
        turn_context
    )

    assert attack_up.remaining_turns == 1



def test_burn_deals_damage_at_start_of_turn():

    source = create_monster("drake_igneous")
    target = create_monster("drake_abyssal")

    burn = create_status_effect(
        effect_id="burn",
        duration=3,
        stacks=1,
        source=source
    )

    target.apply_status_effect(burn)

    health_before = target.health

    begin_turn(target)

    assert target.health < health_before



def test_reset_combat_state_restores_monster():

    monster = create_monster("drake_igneous")

    monster.health = 100
    monster.action_gauge = 0.8
    monster.combat_resources["test"] = 3

    monster.skills[1].current_cooldown = 2

    monster.reset_combat_state()

    assert monster.health == monster.max_health
    assert monster.action_gauge == 0
    assert monster.buffs == []
    assert monster.debuffs == []
    assert monster.combat_resources == {}

    for skill in monster.skills:
        assert skill.current_cooldown == 0



def test_battle_resets_state_after_run(monkeypatch):

    ally = create_monster("drake_igneous")
    enemy = create_monster("drake_storm")


    def fake_get_ready_combatant(combatants):
        return ally


    def fake_player_turn(active_ally, allies, enemies, upcoming_combatant):

        # Simulamos cosas que podrían haber ocurrido durante el combate.
        active_ally.health = 100
        active_ally.action_gauge = 0.7
        active_ally.combat_resources["test"] = 3

        return "run"


    monkeypatch.setattr(
        combat_module,
        "get_ready_combatant",
        fake_get_ready_combatant
    )

    monkeypatch.setattr(
        combat_module,
        "player_turn",
        fake_player_turn
    )


    outcome = battle(
        [ally],
        [enemy]
    )


    assert outcome == "run"

    assert ally.health == ally.max_health
    assert ally.action_gauge == 0
    assert ally.buffs == []
    assert ally.debuffs == []
    assert ally.combat_resources == {}


# =========================================================
#                        ENEMY AI
# =========================================================

def test_estimate_damage_uses_total_multihit_damage():

    attacker = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    skill = attacker.get_skill(2)

    single_hit_damage = skill.base_damage_calc(
        attacker,
        target,
        1
    )

    estimated_damage = estimate_damage(
        attacker,
        target,
        skill
    )

    assert estimated_damage == pytest.approx(
        single_hit_damage * skill.hits
    )



def test_estimate_damage_ignores_critical_hits():

    attacker = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    attacker.crit_rate = 100

    skill = attacker.get_skill(2)

    estimated_damage = estimate_damage(
        attacker,
        target,
        skill
    )

    normal_damage = 0

    for hit in range(skill.hits):

        multiplier = 1

        if skill.hit_multipliers:
            multiplier = skill.hit_multipliers[hit]

        normal_damage += skill.base_damage_calc(
            attacker,
            target,
            multiplier
        )

    assert estimated_damage == pytest.approx(
        normal_damage
    )



def test_estimate_damage_applies_damage_handler():

    attacker = create_monster("drake_igneous")
    target = create_monster("drake_abyssal")

    skill = attacker.get_skill(2)

    damage_without_burn = estimate_damage(
        attacker,
        target,
        skill
    )

    burn = create_status_effect(
        effect_id="burn",
        duration=3,
        stacks=3,
        source=attacker
    )

    target.apply_status_effect(burn)

    damage_with_burn = estimate_damage(
        attacker,
        target,
        skill
    )

    assert damage_with_burn > damage_without_burn



def test_sees_kill_when_estimated_damage_is_enough():

    attacker = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    skill = attacker.get_skill(2)

    estimated_damage = estimate_damage(
        attacker,
        target,
        skill
    )

    target.health = int(
        estimated_damage
    )

    assert sees_kill(
        attacker,
        target,
        skill
    ) is True



def test_does_not_see_kill_when_damage_is_insufficient():

    attacker = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    skill = attacker.get_skill(2)

    estimated_damage = estimate_damage(
        attacker,
        target,
        skill
    )

    target.health = int(
        estimated_damage
    ) + 1

    assert sees_kill(
        attacker,
        target,
        skill
    ) is False



def test_enemy_target_prioritizes_guaranteed_kill():

    attacker = create_monster("drake_igneous")

    kill_target = create_monster(
        "drake_abyssal"
    )

    attribute_target = create_monster(
        "drake_storm"
    )

    skill = attacker.get_skill(1)

    kill_target.health = 1

    selected_target = choose_enemy_target(
        attacker,
        [
            kill_target,
            attribute_target
        ],
        skill
    )

    assert selected_target is kill_target



def test_enemy_target_prioritizes_attribute_advantage_when_no_kill():

    attacker = create_monster("drake_igneous")

    neutral_target = create_monster(
        "drake_igneous"
    )

    advantage_target = create_monster(
        "drake_storm"
    )

    neutral_target.health = neutral_target.max_health
    advantage_target.health = advantage_target.max_health

    skill = attacker.get_skill(1)

    selected_target = choose_enemy_target(
        attacker,
        [
            neutral_target,
            advantage_target
        ],
        skill
    )

    assert selected_target is advantage_target



def test_enemy_target_favors_lowest_hp_target(monkeypatch):

    attacker = create_monster("drake_igneous")

    low_hp_target = create_monster(
        "drake_abyssal"
    )

    high_hp_target = create_monster(
        "drake_abyssal"
    )

    low_hp_target.health = int(
        low_hp_target.max_health * 0.40
    )

    high_hp_target.health = int(
        high_hp_target.max_health * 0.90
    )

    skill = attacker.get_skill(1)

    def fake_choices(
        population,
        weights,
        k
    ):
        return [population[0]]

    monkeypatch.setattr(
        random,
        "choices",
        fake_choices
    )

    selected_target = choose_enemy_target(
        attacker,
        [
            high_hp_target,
            low_hp_target
        ],
        skill
    )

    assert selected_target is low_hp_target



def test_choose_skill_uses_s1_when_silenced():

    enemy = create_monster("drake_igneous")
    target = create_monster("drake_abyssal")

    silence = create_status_effect(
        effect_id="silence",
        duration=2,
        source=target
    )

    enemy.apply_status_effect(silence)

    selected_skill = choose_skill(
        enemy,
        [enemy],
        [target]
    )

    assert selected_skill is enemy.get_skill(1)



def test_choose_skill_prioritizes_aoe_kill():

    enemy = create_monster("drake_igneous")
    target = create_monster("drake_abyssal")

    # At 1 HP, every damage skill can guarantee the kill.
    target.health = 1

    selected_skill = choose_skill(
        enemy,
        [enemy],
        [target]
    )

    # S2 is AoE, while S1 and S3 are single-target.
    assert selected_skill is enemy.get_skill(2)



def test_choose_skill_prioritizes_lowest_cooldown_between_aoe_kills():

    enemy = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    target.health = 1

    selected_skill = choose_skill(
        enemy,
        [enemy],
        [target]
    )

    # Both S2 and S3 are AoE kill skills.
    # S2 has CD 4 and S3 has CD 5.
    assert selected_skill is enemy.get_skill(2)



def test_choose_skill_uses_default_weights_when_no_kill(monkeypatch):

    enemy = create_monster("drake_igneous")
    target = create_monster("drake_abyssal")

    target.health = target.max_health

    captured_weights = []

    def fake_choices(population, weights, k):

        captured_weights.extend(weights)

        return [population[0]]

    monkeypatch.setattr(
        random,
        "choices",
        fake_choices
    )

    choose_skill(
        enemy,
        [enemy],
        [target]
    )

    assert captured_weights == [
        10,
        55,
        35
    ]



def test_choose_skill_uses_two_skill_weights_when_one_is_on_cooldown(
    monkeypatch
):

    enemy = create_monster("drake_igneous")
    target = create_monster("drake_abyssal")

    target.health = target.max_health

    enemy.get_skill(3).current_cooldown = 2

    captured_weights = []

    def fake_choices(population, weights, k):

        captured_weights.extend(weights)

        return [population[0]]

    monkeypatch.setattr(
        random,
        "choices",
        fake_choices
    )

    choose_skill(
        enemy,
        [enemy],
        [target]
    )

    assert captured_weights == [
        20,
        80
    ]



def test_choose_skill_does_not_select_skill_on_cooldown():

    enemy = create_monster("drake_igneous")
    target = create_monster("drake_abyssal")

    # Make every usable damage skill see a kill.
    target.health = 1

    # S2 would normally be preferred because it is AoE.
    enemy.get_skill(2).current_cooldown = 2

    selected_skill = choose_skill(
        enemy,
        [enemy],
        [target]
    )

    assert selected_skill is not enemy.get_skill(2)



def test_choose_skill_prioritizes_setup_skill():

    enemy = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    # No target has Speed Break yet.
    selected_skill = choose_skill(
        enemy,
        [enemy],
        [target]
    )

    assert selected_skill is enemy.get_skill(2)



def test_choose_skill_does_not_prepare_if_setup_is_ready(monkeypatch):

    enemy = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    speed_break = create_status_effect(
        effect_id="speed_break",
        duration=2,
        source=enemy
    )

    target.apply_status_effect(speed_break)

    def fake_choices(population, weights, k):
        return [population[-1]]

    monkeypatch.setattr(
        random,
        "choices",
        fake_choices
    )

    selected_skill = choose_skill(
        enemy,
        [enemy],
        [target]
    )

    assert selected_skill is enemy.get_skill(3)



def test_choose_skill_does_not_use_setup_skill_on_cooldown(monkeypatch):

    enemy = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    enemy.get_skill(2).current_cooldown = 2

    def fake_choices(population, weights, k):
        return [population[-1]]

    monkeypatch.setattr(
        random,
        "choices",
        fake_choices
    )

    selected_skill = choose_skill(
        enemy,
        [enemy],
        [target]
    )

    assert selected_skill is not enemy.get_skill(2)



def test_choose_skill_kill_priority_over_setup():

    enemy = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    # Prevent Rime Breath from being a kill candidate.
    enemy.get_skill(2).current_cooldown = 2

    target.health = 1

    selected_skill = choose_skill(
        enemy,
        [enemy],
        [target]
    )

    assert selected_skill is enemy.get_skill(3)



def test_fever_sting_gets_15_percent_bonus_if_target_starts_poisoned(
    monkeypatch
):

    thornet = create_monster("thornet_igneous")
    target = create_monster("drake_abyssal")

    skill = thornet.get_skill(2)

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    result_without_poison = skill.execute(
        thornet,
        [target]
    )

    damage_without_poison = (
        result_without_poison
        .target_results[0]
        ["total_damage"]
    )

    target.reset_combat_state()

    poison = create_status_effect(
        effect_id="poison",
        duration=2,
        stacks=1,
        source=thornet
    )

    target.apply_status_effect(poison)

    result_with_poison = skill.execute(
        thornet,
        [target]
    )

    damage_with_poison = (
        result_with_poison
        .target_results[0]
        ["total_damage"]
    )

    assert damage_with_poison == pytest.approx(
        damage_without_poison * 1.15,
        rel=0.02
    )



def test_numbing_sting_does_not_stun_if_no_new_poison_is_applied(
    monkeypatch
):

    thornet = create_monster("thornet_abyssal")
    target = create_monster("drake_igneous")

    skill = thornet.get_skill(2)

    # Force Poison and Stun proc rolls to succeed.
    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    # Force resistance checks to succeed.
    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )

    skill.execute(
        thornet,
        [target]
    )

    assert any(
        debuff.effect_id == "poison"
        for debuff in target.debuffs
    )

    assert any(
        debuff.effect_id == "stun"
        for debuff in target.debuffs
    )



def test_numbing_sting_can_stun_if_it_applies_new_poison(
    monkeypatch
):

    thornet = create_monster("thornet_abyssal")
    target = create_monster("drake_igneous")

    skill = thornet.get_skill(2)

    # Force Poison and Stun chance rolls to succeed.
    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )

    skill.execute(
        thornet,
        [target]
    )

    assert any(
        debuff.effect_id == "poison"
        for debuff in target.debuffs
    )

    assert any(
        debuff.effect_id == "stun"
        for debuff in target.debuffs
    )



def test_swarm_pierce_uses_normal_damage_without_starting_debuff(
    monkeypatch
):

    thornet = create_monster("thornet_storm")
    target = create_monster("drake_igneous")

    skill = thornet.get_skill(2)

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    result = skill.execute(
        thornet,
        [target]
    )

    hit_results = (
        result.target_results[0]["hit_results"]
    )

    damages = [
        hit["damage"]
        for hit in hit_results
    ]

    assert damages[0] == damages[1]
    assert damages[1] == damages[2]



def test_swarm_pierce_increases_damage_per_hit_if_target_starts_debuffed(
    monkeypatch
):

    thornet = create_monster("thornet_storm")
    target = create_monster("drake_igneous")

    skill = thornet.get_skill(2)

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    poison = create_status_effect(
        effect_id="poison",
        duration=2,
        stacks=1,
        source=thornet
    )

    target.apply_status_effect(poison)

    result = skill.execute(
        thornet,
        [target]
    )

    hit_results = (
        result.target_results[0]["hit_results"]
    )

    first_hit = hit_results[0]["damage"]
    second_hit = hit_results[1]["damage"]
    third_hit = hit_results[2]["damage"]

    assert second_hit == pytest.approx(
        first_hit * 1.15,
        rel=0.02
    )

    assert third_hit == pytest.approx(
        first_hit * 1.30,
        rel=0.02
    )



def test_swarm_pierce_does_not_gain_bonus_from_debuff_applied_during_skill(
    monkeypatch
):

    thornet = create_monster("thornet_storm")
    target = create_monster("drake_igneous")

    skill = thornet.get_skill(2)

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    # Simulate a debuff being added after the first hit.
    original_receive_damage = target.receive_damage
    hit_count = 0

    def receive_damage_and_apply_debuff(
        damage,
        source=None
    ):

        nonlocal hit_count

        result = original_receive_damage(
            damage,
            source=source
        )

        hit_count += 1

        if hit_count == 1:

            poison = create_status_effect(
                effect_id="poison",
                duration=2,
                stacks=1,
                source=thornet
            )

            target.apply_status_effect(poison)

        return result

    monkeypatch.setattr(
        target,
        "receive_damage",
        receive_damage_and_apply_debuff
    )

    result = skill.execute(
        thornet,
        [target]
    )

    hit_results = (
        result.target_results[0]["hit_results"]
    )

    damages = [
        hit["damage"]
        for hit in hit_results
    ]

    assert damages[0] == damages[1]
    assert damages[1] == damages[2]



def test_meteor_dive_scales_damage_with_speed(
    monkeypatch
):

    griffon = create_monster("griffon_igneous")
    target = create_monster("drake_abyssal")

    skill = griffon.get_skill(3)

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    result = skill.execute(
        griffon,
        [target]
    )

    actual_damage = (
        result.target_results[0]["total_damage"]
    )

    effective_speed = griffon.get_effective_stat(
        "speed"
    )

    expected_multiplier = (
        1 + effective_speed * 0.001
    )

    base_damage = skill.base_damage_calc(
        griffon,
        target,
        1.0
    )

    expected_damage = int(
        base_damage * expected_multiplier
    )

    assert actual_damage == expected_damage



def test_meteor_dive_deals_more_damage_with_more_speed(
    monkeypatch
):

    griffon = create_monster("griffon_igneous")
    target = create_monster("drake_abyssal")

    skill = griffon.get_skill(3)

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    result_normal = skill.execute(
        griffon,
        [target]
    )

    damage_normal = (
        result_normal.target_results[0]["total_damage"]
    )

    target.reset_combat_state()

    griffon.speed += 100

    result_faster = skill.execute(
        griffon,
        [target]
    )

    damage_faster = (
        result_faster.target_results[0]["total_damage"]
    )

    assert damage_faster > damage_normal



def test_meteor_dive_uses_effective_speed(
    monkeypatch
):

    griffon = create_monster("griffon_igneous")
    target = create_monster("drake_abyssal")

    skill = griffon.get_skill(3)

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    normal_result = skill.execute(
        griffon,
        [target]
    )

    normal_damage = (
        normal_result.target_results[0]["total_damage"]
    )

    target.reset_combat_state()

    original_get_effective_stat = (
        griffon.get_effective_stat
    )

    def boosted_effective_stat(stat):

        if stat == "speed":
            return (
                original_get_effective_stat("speed")
                + 100
            )

        return original_get_effective_stat(stat)

    monkeypatch.setattr(
        griffon,
        "get_effective_stat",
        boosted_effective_stat
    )

    boosted_result = skill.execute(
        griffon,
        [target]
    )

    boosted_damage = (
        boosted_result.target_results[0]["total_damage"]
    )

    assert boosted_damage > normal_damage


# =========================================================
#                     AI CONDITIONS
# =========================================================

def test_target_has_debuff_returns_true_when_alive_enemy_has_debuff():

    target = create_monster("drake_igneous")

    speed_break = create_status_effect(
        effect_id="speed_break",
        duration=2
    )

    target.apply_status_effect(speed_break)

    requirement = {
        "condition": "target_has_debuff",
        "effect_id": "speed_break",
        "scope": "any_enemy"
    }

    context = {
        "caster": None,
        "team": [],
        "opponents": [target]
    }

    result = target_has_debuff(
        requirement,
        context
    )

    assert result is True



def test_target_has_debuff_returns_false_when_no_enemy_has_debuff():

    target = create_monster("drake_igneous")

    requirement = {
        "condition": "target_has_debuff",
        "effect_id": "speed_break",
        "scope": "any_enemy"
    }

    context = {
        "caster": None,
        "team": [],
        "opponents": [target]
    }

    result = target_has_debuff(
        requirement,
        context
    )

    assert result is False



def test_target_has_debuff_ignores_dead_enemies():

    target = create_monster("drake_igneous")

    speed_break = create_status_effect(
        effect_id="speed_break",
        duration=2
    )

    target.apply_status_effect(speed_break)

    target.health = 0

    requirement = {
        "condition": "target_has_debuff",
        "effect_id": "speed_break",
        "scope": "any_enemy"
    }

    context = {
        "caster": None,
        "team": [],
        "opponents": [target]
    }

    result = target_has_debuff(
        requirement,
        context
    )

    assert result is False



def test_target_has_debuff_raises_error_for_unsupported_scope():

    target = create_monster("drake_igneous")

    requirement = {
        "condition": "target_has_debuff",
        "effect_id": "speed_break",
        "scope": "all_enemies"
    }

    with pytest.raises(
        ValueError,
        match="Unsupported AI scope"
    ):
        context = {
            "caster": None,
            "team": [],
            "opponents": [target]
        }

        target_has_debuff(
            requirement,
            context
        )



def test_ai_setup_condition_registry_contains_target_has_debuff():

    assert (
        AI_CONDITIONS["target_has_debuff"]
        is target_has_debuff
    )


# =========================================================
#                   SETUP REQUIREMENTS
# =========================================================

def test_setup_requirements_are_met_when_required_debuff_exists():

    enemy = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    speed_break = create_status_effect(
        effect_id="speed_break",
        duration=2,
        source=enemy
    )

    target.apply_status_effect(speed_break)

    skill = enemy.get_skill(3)

    context = {
        "caster": enemy,
        "team": [enemy],
        "opponents": [target]
    }

    assert check_setup_requirements(
        skill,
        context
    ) is True



def test_setup_requirements_are_not_met_without_required_debuff():

    enemy = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    skill = enemy.get_skill(3)

    context = {
        "caster": enemy,
        "team": [enemy],
        "opponents": [target]
    }

    assert check_setup_requirements(
        skill,
        context
    ) is False



def test_skill_without_ai_metadata_has_setup_ready():

    enemy = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    skill = enemy.get_skill(1)

    context = {
        "caster": enemy,
        "team": [enemy],
        "opponents": [target]
    }

    assert check_setup_requirements(
        skill,
        context
    ) is True



def test_setup_requirements_raise_error_for_unknown_condition(
    monkeypatch
):

    enemy = create_monster("drake_abyssal")
    target = create_monster("drake_igneous")

    skill = enemy.get_skill(3)

    fake_metadata = {
        skill.skill_id: {
            "setup_requirements": [
                {
                    "condition": "unknown_condition",
                    "scope": "any_enemy"
                }
            ]
        }
    }

    monkeypatch.setattr(
        "game.combat.enemy_ai.SKILL_AI_DATA",
        fake_metadata
    )

    with pytest.raises(
        ValueError,
        match="Unsupported AI setup condition"
    ):
        context = {
            "caster": enemy,
            "team": [enemy],
            "opponents": [target]
        }
        
        check_setup_requirements(
            skill,
            context
        )


# =========================================================
#                   BATTLE SIMULATION
# =========================================================

def test_simulate_battle_returns_valid_outcome():

    team_a = [
        create_monster("griffon_igneous")
    ]

    team_b = [
        create_monster("slime_storm")
    ]

    result = simulate_battle(
        team_a,
        team_b
    )

    assert result["outcome"] in (
        "team_a_wins",
        "team_b_wins"
    )

    assert result["turns"] > 0
    assert result["team_a_remaining_hp"] >= 0
    assert result["team_b_remaining_hp"] >= 0



def test_simulate_battle_resets_combat_state_after_battle():

    team_a = [
        create_monster("griffon_igneous")
    ]

    team_b = [
        create_monster("slime_storm")
    ]

    simulate_battle(
        team_a,
        team_b
    )

    for monster in team_a + team_b:

        assert monster.health == monster.max_health
        assert monster.action_gauge == 0
        assert monster.buffs == []
        assert monster.debuffs == []

        for skill in monster.skills:
            assert skill.current_cooldown == 0



def test_simulate_battles_returns_expected_data():

    result = simulate_battles(
        ["griffon_igneous"],
        ["slime_storm"],
        runs=10
    )

    assert "team_a_win_rate" in result
    assert "team_b_win_rate" in result
    assert "average_turns" in result
    assert "team_a_average_remaining_hp" in result
    assert "team_b_average_remaining_hp" in result



def test_simulate_battles_win_rates_add_up_to_100():

    result = simulate_battles(
        ["griffon_igneous"],
        ["slime_storm"],
        runs=20
    )

    total_win_rate = (
        result["team_a_win_rate"]
        + result["team_b_win_rate"]
    )

    assert total_win_rate == pytest.approx(100)



def test_simulate_battles_returns_valid_averages():

    result = simulate_battles(
        ["griffon_igneous"],
        ["slime_storm"],
        runs=10
    )

    assert result["average_turns"] > 0

    assert (
        result["team_a_average_remaining_hp"]
        >= 0
    )

    assert (
        result["team_b_average_remaining_hp"]
        >= 0
    )


# =========================================================
#                    STORM DRAKE TESTS
# =========================================================


def test_lightning_rush_applies_speed_up_after_use(
    monkeypatch
):

    drake = create_monster("drake_storm")
    target = create_monster("drake_igneous")

    skill = create_skill("lightning_rush")

    # Avoid critical noise.
    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    skill.execute(
        drake,
        [target],
        context={
            "team": [drake],
            "opponents": [target]
        }
    )

    assert any(
        buff.effect_id == "speed_up"
        for buff in drake.buffs
    )



def test_lightning_rush_blitz_applies_speed_up_and_action_gauge(
    monkeypatch
):

    drake = create_monster("drake_storm")
    target = create_monster("drake_igneous")

    skill = create_skill(
        "lightning_rush_blitz"
    )

    drake.action_gauge = 0

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    skill.execute(
        drake,
        [target],
        context={
            "team": [drake],
            "opponents": [target]
        }
    )

    assert any(
        buff.effect_id == "speed_up"
        for buff in drake.buffs
    )

    assert drake.action_gauge == pytest.approx(
        0.15
    )

    assert skill.cooldown == 3



def test_stormbreak_hits_every_enemy_at_least_once(
    monkeypatch
):

    drake = create_monster("drake_storm")

    target_1 = create_monster("drake_igneous")
    target_2 = create_monster("drake_abyssal")
    target_3 = create_monster("griffon_igneous")

    skill = create_skill("stormbreak")

    # Prevent targets from dying during the test.
    monkeypatch.setattr(
        skill,
        "damage_calc",
        lambda *args, **kwargs: (1, False)
    )

    result = skill.execute(
        drake,
        [
            target_1,
            target_2,
            target_3
        ]
    )

    total_hits = sum(
        len(target_result["hit_results"])
        for target_result
        in result.target_results
    )

    assert total_hits == 10

    for target_result in result.target_results:

        assert (
            len(target_result["hit_results"])
            >= 1
        )



def test_stormbreak_only_attempts_stun_on_target_with_three_hits(
    monkeypatch
):

    drake = create_monster("drake_storm")

    target_1 = create_monster("drake_igneous")
    target_2 = create_monster("drake_abyssal")

    skill = create_skill("stormbreak")

    monkeypatch.setattr(
        skill,
        "damage_calc",
        lambda *args, **kwargs: (1, False)
    )

    # Keep guaranteed target order predictable.
    monkeypatch.setattr(
        random,
        "shuffle",
        lambda values: None
    )

    # After one guaranteed hit per enemy,
    # send all remaining random hits to target_1.
    monkeypatch.setattr(
        random,
        "choice",
        lambda values: values[0]
    )

    # Force Stun proc.
    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    # Force resistance check to fail to resist.
    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )

    result = skill.execute(
        drake,
        [target_1, target_2]
    )

    target_1_result = next(
        result
        for result in result.target_results
        if result["target"] is target_1
    )

    target_2_result = next(
        result
        for result in result.target_results
        if result["target"] is target_2
    )

    assert (
        len(target_1_result["hit_results"])
        >= 3
    )

    assert (
        len(target_2_result["hit_results"])
        < 3
    )

    assert any(
        debuff.effect_id == "stun"
        for debuff in target_1.debuffs
    )

    assert not any(
        debuff.effect_id == "stun"
        for debuff in target_2.debuffs
    )



def test_stormbreak_requiem_adds_aoe_follow_up(
    monkeypatch
):

    drake = create_monster("drake_storm")

    target_1 = create_monster("drake_igneous")
    target_2 = create_monster("drake_abyssal")
    target_3 = create_monster("griffon_igneous")

    skill = create_skill(
        "stormbreak_requiem"
    )

    monkeypatch.setattr(
        skill,
        "damage_calc",
        lambda *args, **kwargs: (1, False)
    )

    result = skill.execute(
        drake,
        [
            target_1,
            target_2,
            target_3
        ],
        context={
            "team": [drake],
            "opponents": [
                target_1,
                target_2,
                target_3
            ]
        }
    )

    follow_up = next(
        event
        for event in result.events
        if event["type"]
        == "aoe_follow_up_attack"
    )

    assert len(
        follow_up["target_results"]
    ) == 3

    for target_result in follow_up[
        "target_results"
    ]:

        assert len(
            target_result["hit_results"]
        ) == 1



def test_short_circuit_does_not_stun_without_speed_up(
    monkeypatch
):

    drake = create_monster("drake_storm")
    target = create_monster("drake_igneous")

    drake.passives = [
        create_passive("short_circuit")
    ]

    skill = create_skill("lightning_rush")

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    skill.execute(
        drake,
        [target],
        context={
            "team": [drake],
            "opponents": [target]
        }
    )

    assert not any(
        debuff.effect_id == "stun"
        for debuff in target.debuffs
    )



def test_short_circuit_can_stun_while_speed_up_is_active(
    monkeypatch
):

    drake = create_monster("drake_storm")
    target = create_monster("drake_igneous")

    drake.passives = [
        create_passive("short_circuit")
    ]

    speed_up = create_status_effect(
        effect_id="speed_up",
        duration=2,
        source=drake
    )

    drake.apply_status_effect(
        speed_up
    )

    skill = create_skill("lightning_rush")

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    skill.execute(
        drake,
        [target],
        context={
            "team": [drake],
            "opponents": [target]
        }
    )

    assert any(
        debuff.effect_id == "stun"
        for debuff in target.debuffs
    )



def test_chain_reaction_reduces_requiem_cooldown(
    monkeypatch
):

    drake = create_monster("drake_storm")
    target = create_monster("drake_igneous")

    drake.passives = [
        create_passive(
            "short_circuit_chain_reaction"
        )
    ]

    drake.skills = [
        create_skill("draconic_claw"),
        create_skill("lightning_rush_blitz"),
        create_skill("stormbreak_requiem")
    ]

    stormbreak = drake.get_skill(3)

    stormbreak.current_cooldown = 4

    speed_up = create_status_effect(
        effect_id="speed_up",
        duration=2,
        source=drake
    )

    drake.apply_status_effect(
        speed_up
    )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    drake.get_skill(1).execute(
        drake,
        [target]
    )

    assert (
        stormbreak.current_cooldown
        == 3
    )



def test_thunderheart_damage_uses_only_bonus_speed(
    monkeypatch
):

    drake = create_monster("drake_storm")

    drake.passives = [
        create_passive("thunderheart")
    ]

    base_speed = drake.speed

    original_get_effective_stat = (
        drake.get_effective_stat
    )

    def mocked_effective_stat(stat):

        if stat == "speed":
            return base_speed + 50

        return original_get_effective_stat(
            stat
        )

    monkeypatch.setattr(
        drake,
        "get_effective_stat",
        mocked_effective_stat
    )

    multiplier = (
        get_passive_damage_multiplier(
            drake
        )
    )

    expected = (
        1
        + 50
        * drake.passives[0]
        .handler_data[
            "damage_per_bonus_speed"
        ]
    )

    assert multiplier == pytest.approx(
        expected
    )



def test_thunderheart_gives_no_bonus_at_base_speed():

    drake = create_monster("drake_storm")

    drake.passives = [
        create_passive("thunderheart")
    ]

    multiplier = (
        get_passive_damage_multiplier(
            drake
        )
    )

    assert multiplier == 1.0



def test_overclocked_crit_rate_uses_integer_speed_breakpoints(
    monkeypatch
):

    drake = create_monster("drake_storm")

    drake.passives = [
        create_passive(
            "thunderheart_overclocked"
        )
    ]

    base_speed = drake.speed

    original_get_effective_stat = (
        drake.get_effective_stat
    )

    def mocked_effective_stat(stat):

        if stat == "speed":
            return base_speed + 49

        return original_get_effective_stat(
            stat
        )

    monkeypatch.setattr(
        drake,
        "get_effective_stat",
        mocked_effective_stat
    )

    bonus = get_passive_stat_bonus(
        drake,
        "crit_rate"
    )

    speed_per_crit = (
        drake.passives[0]
        .handler_data["speed_per_crit"]
    )

    assert bonus == (
        49 // speed_per_crit
    )

    assert isinstance(
        bonus,
        int
    )



def test_overclocked_crit_rate_caps_at_30(
    monkeypatch
):

    drake = create_monster("drake_storm")

    drake.passives = [
        create_passive(
            "thunderheart_overclocked"
        )
    ]

    base_speed = drake.speed

    original_get_effective_stat = (
        drake.get_effective_stat
    )

    def mocked_effective_stat(stat):

        if stat == "speed":
            return base_speed + 1000

        return original_get_effective_stat(
            stat
        )

    monkeypatch.setattr(
        drake,
        "get_effective_stat",
        mocked_effective_stat
    )

    bonus = get_passive_stat_bonus(
        drake,
        "crit_rate"
    )

    assert bonus == 30


# =========================================================
#                    STORM DRYAD TESTS
# =========================================================


def test_vine_barrage_heals_lowest_hp_ally_once(
    monkeypatch
):

    dryad = create_monster("dryad_storm")
    ally_1 = create_monster("drake_igneous")
    ally_2 = create_monster("drake_abyssal")
    enemy = create_monster("drake_storm")

    ally_1.health = int(
        ally_1.max_health * 0.30
    )

    ally_2.health = int(
        ally_2.max_health * 0.70
    )

    skill = create_skill("vine_barrage")

    monkeypatch.setattr(
        skill,
        "damage_calc",
        lambda *args, **kwargs: (1, False)
    )

    health_before = ally_1.health

    expected_heal = int(
        dryad.get_healing_hp() * 0.08
    )

    skill.execute(
        dryad,
        [enemy],
        context={
            "team": [
                dryad,
                ally_1,
                ally_2
            ],
            "opponents": [enemy]
        }
    )

    assert ally_1.health == (
        health_before + expected_heal
    )

    assert ally_2.health == int(
        ally_2.max_health * 0.70
    )



def test_breath_of_the_grove_heals_all_allies():

    dryad = create_monster("dryad_storm")
    ally_1 = create_monster("drake_igneous")
    ally_2 = create_monster("drake_abyssal")

    dryad.health = int(
        dryad.max_health * 0.50
    )

    ally_1.health = int(
        ally_1.max_health * 0.50
    )

    ally_2.health = int(
        ally_2.max_health * 0.50
    )

    skill = create_skill(
        "breath_of_the_grove"
    )

    heal_amount = int(
        dryad.get_healing_hp() * 0.25
    )

    dryad_before = dryad.health
    ally_1_before = ally_1.health
    ally_2_before = ally_2.health

    skill.execute(
        dryad,
        [dryad, ally_1, ally_2],
        context={
            "team": [
                dryad,
                ally_1,
                ally_2
            ],
            "opponents": []
        }
    )

    assert dryad.health == (
        dryad_before + heal_amount
    )

    assert ally_1.health == (
        ally_1_before + heal_amount
    )

    assert ally_2.health == (
        ally_2_before + heal_amount
    )



def test_sanctuary_heals_35_percent_and_applies_immunity():

    dryad = create_monster("dryad_storm")
    ally = create_monster("drake_igneous")

    dryad.health = int(
        dryad.max_health * 0.50
    )

    ally.health = int(
        ally.max_health * 0.50
    )

    skill = create_skill(
        "breath_of_the_grove_sanctuary"
    )

    heal_amount = int(
        dryad.get_healing_hp() * 0.35
    )

    health_before = ally.health

    skill.execute(
        dryad,
        [dryad, ally],
        context={
            "team": [dryad, ally],
            "opponents": []
        }
    )

    assert ally.health == (
        health_before + heal_amount
    )

    immunity = next(
        (
            buff
            for buff in ally.buffs
            if buff.effect_id == "immunity"
        ),
        None
    )

    assert immunity is not None
    assert immunity.remaining_turns == 1



def test_evergreen_applies_immunity_and_regrowth():

    dryad = create_monster("dryad_storm")
    ally = create_monster("drake_igneous")

    skill = create_skill(
        "breath_of_the_grove_evergreen"
    )

    skill.execute(
        dryad,
        [dryad, ally],
        context={
            "team": [dryad, ally],
            "opponents": []
        }
    )

    immunity = next(
        (
            buff
            for buff in ally.buffs
            if buff.effect_id == "immunity"
        ),
        None
    )

    regrowth = next(
        (
            buff
            for buff in ally.buffs
            if buff.effect_id == "regrowth"
        ),
        None
    )

    assert immunity is not None
    assert immunity.remaining_turns == 1

    assert regrowth is not None
    assert regrowth.remaining_turns == 2

    assert skill.cooldown == 4



def test_regrowth_heals_8_percent_max_hp_at_turn_start():

    monster = create_monster(
        "drake_igneous"
    )

    monster.health = int(
        monster.max_health * 0.50
    )

    regrowth = create_status_effect(
        effect_id="regrowth",
        duration=2,
        source=monster
    )

    monster.apply_status_effect(
        regrowth
    )

    health_before = monster.health

    expected_heal = int(
        monster.max_health * 0.08
    )

    begin_turn(monster)

    assert monster.health == (
        health_before + expected_heal
    )



def test_regrowth_heals_for_two_turns_then_expires():

    monster = create_monster(
        "drake_igneous"
    )

    monster.health = int(
        monster.max_health * 0.30
    )

    regrowth = create_status_effect(
        effect_id="regrowth",
        duration=2,
        source=monster
    )

    monster.apply_status_effect(
        regrowth
    )

    heal_per_turn = int(
        monster.max_health * 0.08
    )

    health_before = monster.health

    turn_context = begin_turn(monster)
    end_turn(monster, turn_context)

    assert monster.health == (
        health_before + heal_per_turn
    )

    active_regrowth = next(
        buff
        for buff in monster.buffs
        if buff.effect_id == "regrowth"
    )

    assert active_regrowth.remaining_turns == 1

    turn_context = begin_turn(monster)
    end_turn(monster, turn_context)

    assert monster.health == (
        health_before
        + heal_per_turn * 2
    )

    assert not any(
        buff.effect_id == "regrowth"
        for buff in monster.buffs
    )



def test_natures_grace_increases_direct_heal_below_50_percent():

    dryad = create_monster("dryad_storm")
    ally = create_monster("drake_igneous")

    dryad.passives = [
        create_passive("natures_grace")
    ]

    ally.health = int(
        ally.max_health * 0.40
    )

    skill = create_skill(
        "breath_of_the_grove"
    )

    base_heal = int(
        dryad.get_healing_hp() * 0.25
    )

    expected_heal = int(
        base_heal * 1.20
    )

    health_before = ally.health

    skill.execute(
        dryad,
        [ally],
        context={
            "team": [ally],
            "opponents": []
        }
    )

    assert ally.health == (
        health_before + expected_heal
    )



def test_natures_grace_does_not_activate_at_exactly_50_percent():

    dryad = create_monster("dryad_storm")
    ally = create_monster("drake_igneous")

    dryad.passives = [
        create_passive("natures_grace")
    ]

    ally.health = (
        ally.max_health // 2
    )

    skill = create_skill(
        "breath_of_the_grove"
    )

    expected_heal = int(
        dryad.get_healing_hp() * 0.25
    )

    health_before = ally.health

    skill.execute(
        dryad,
        [ally],
        context={
            "team": [ally],
            "opponents": []
        }
    )

    assert ally.health == (
        health_before + expected_heal
    )



def test_natures_grace_is_calculated_individually_per_ally():

    dryad = create_monster("dryad_storm")

    low_hp_ally = create_monster(
        "drake_igneous"
    )

    high_hp_ally = create_monster(
        "drake_abyssal"
    )

    dryad.passives = [
        create_passive("natures_grace")
    ]

    low_hp_ally.health = int(
        low_hp_ally.max_health * 0.40
    )

    high_hp_ally.health = int(
        high_hp_ally.max_health * 0.60
    )

    skill = create_skill(
        "breath_of_the_grove"
    )

    base_heal = int(
        dryad.get_healing_hp() * 0.25
    )

    boosted_heal = int(
        base_heal * 1.20
    )

    low_before = low_hp_ally.health
    high_before = high_hp_ally.health

    skill.execute(
        dryad,
        [
            low_hp_ally,
            high_hp_ally
        ],
        context={
            "team": [
                low_hp_ally,
                high_hp_ally
            ],
            "opponents": []
        }
    )

    assert low_hp_ally.health == (
        low_before + boosted_heal
    )

    assert high_hp_ally.health == (
        high_before + base_heal
    )



def test_overgrowth_converts_half_overheal_into_shield():

    dryad = create_monster("dryad_storm")
    ally = create_monster("drake_igneous")

    dryad.passives = [
        create_passive(
            "natures_grace_overgrowth"
        )
    ]

    missing_health = 100

    ally.health = (
        ally.max_health
        - missing_health
    )

    skill = create_skill(
        "breath_of_the_grove"
    )

    intended_heal = int(
        dryad.get_healing_hp() * 0.25
    )

    overheal = (
        intended_heal
        - missing_health
    )

    expected_shield = int(
        overheal * 0.50
    )

    expected_shield = min(
        expected_shield,
        int(ally.max_health * 0.10)
    )

    skill.execute(
        dryad,
        [ally],
        context={
            "team": [ally],
            "opponents": []
        }
    )

    shield = next(
        (
            buff
            for buff in ally.buffs
            if buff.effect_id == "shield"
        ),
        None
    )

    assert shield is not None

    assert shield.value == (
        expected_shield
    )

    assert shield.remaining_turns == 2



def test_overgrowth_shield_is_capped_at_10_percent_target_max_hp():

    dryad = create_monster("dryad_storm")
    ally = create_monster("drake_igneous")

    dryad.passives = [
        create_passive(
            "natures_grace_overgrowth"
        )
    ]

    ally.max_health = 1000
    ally.health = 999

    skill = create_skill(
        "breath_of_the_grove_evergreen"
    )

    skill.execute(
        dryad,
        [ally],
        context={
            "team": [ally],
            "opponents": []
        }
    )

    shield = next(
        buff
        for buff in ally.buffs
        if buff.effect_id == "shield"
    )

    assert shield.value == 100



def test_overgrowth_does_not_create_shield_without_overheal():

    dryad = create_monster("dryad_storm")
    ally = create_monster("drake_igneous")

    dryad.passives = [
        create_passive(
            "natures_grace_overgrowth"
        )
    ]

    ally.health = 1

    skill = create_skill(
        "breath_of_the_grove"
    )

    skill.execute(
        dryad,
        [ally],
        context={
            "team": [ally],
            "opponents": []
        }
    )

    assert not any(
        buff.effect_id == "shield"
        for buff in ally.buffs
    )



def test_regrowth_does_not_trigger_overgrowth():

    dryad = create_monster("dryad_storm")
    ally = create_monster("drake_igneous")

    dryad.passives = [
        create_passive(
            "natures_grace_overgrowth"
        )
    ]

    ally.health = (
        ally.max_health - 1
    )

    regrowth = create_status_effect(
        effect_id="regrowth",
        duration=2,
        source=dryad
    )

    ally.apply_status_effect(
        regrowth
    )

    begin_turn(ally)

    assert not any(
        buff.effect_id == "shield"
        for buff in ally.buffs
    )



def test_shield_absorbs_damage_before_health():

    monster = create_monster(
        "drake_igneous"
    )

    shield = create_status_effect(
        effect_id="shield",
        duration=2,
        source=monster,
        value=1000
    )

    monster.apply_status_effect(
        shield
    )

    health_before = monster.health

    monster.receive_damage(600)

    assert monster.health == health_before

    active_shield = next(
        buff
        for buff in monster.buffs
        if buff.effect_id == "shield"
    )

    assert active_shield.value == 400



def test_damage_over_shield_spills_into_health():

    monster = create_monster(
        "drake_igneous"
    )

    shield = create_status_effect(
        effect_id="shield",
        duration=2,
        source=monster,
        value=1000
    )

    monster.apply_status_effect(
        shield
    )

    health_before = monster.health

    monster.receive_damage(1400)

    assert monster.health == (
        health_before - 400
    )

    assert not any(
        buff.effect_id == "shield"
        for buff in monster.buffs
    )



# =========================================================
#                    COMBAT TELEMETRY TESTS
# =========================================================

def test_direct_damage_is_recorded_in_telemetry(
    monkeypatch
):

    attacker = create_monster(
        "griffon_igneous"
    )

    defender = create_monster(
        "slime_storm"
    )

    telemetry = create_battle_telemetry(
        [attacker],
        [defender]
    )

    skill = attacker.get_skill(1)

    monkeypatch.setattr(
        skill,
        "damage_calc",
        lambda *args, **kwargs: (
            100,
            False
        )
    )

    skill.execute(
        attacker,
        [defender],
        context={
            "team": [attacker],
            "opponents": [defender],
            "telemetry": telemetry
        }
    )

    result = serialize_battle_telemetry(
        telemetry
    )

    assert (
        result["team_a"][0]["direct_damage"]
        == 100
    )



def test_healing_is_recorded_in_telemetry():

    dryad = create_monster(
        "dryad_storm"
    )

    ally = create_monster(
        "drake_igneous"
    )

    enemy = create_monster(
        "drake_abyssal"
    )

    ally.health = int(
        ally.max_health * 0.50
    )

    telemetry = create_battle_telemetry(
        [dryad, ally],
        [enemy]
    )

    skill = create_skill(
        "breath_of_the_grove"
    )

    skill.execute(
        dryad,
        [dryad, ally],
        context={
            "team": [dryad, ally],
            "opponents": [enemy],
            "telemetry": telemetry
        }
    )

    result = serialize_battle_telemetry(
        telemetry
    )

    assert (
        result["team_a"][0]["healing"]
        > 0
    )



def test_shield_absorption_is_credited_to_shield_source():

    dryad = create_monster(
        "dryad_storm"
    )

    ally = create_monster(
        "drake_igneous"
    )

    enemy = create_monster(
        "drake_abyssal"
    )

    telemetry = create_battle_telemetry(
        [dryad, ally],
        [enemy]
    )

    shield = create_status_effect(
        effect_id="shield",
        duration=2,
        source=dryad,
        value=500
    )

    ally.apply_status_effect(
        shield
    )

    ally.receive_damage(
        300,
        source=enemy,
        telemetry=telemetry
    )

    result = serialize_battle_telemetry(
        telemetry
    )

    assert (
        result["team_a"][0]["shield_absorbed"]
        == 300
    )



def test_simulate_battle_returns_monster_telemetry():

    team_a = [
        create_monster(
            "griffon_igneous"
        )
    ]

    team_b = [
        create_monster(
            "slime_storm"
        )
    ]

    result = simulate_battle(
        team_a,
        team_b
    )

    assert "telemetry" in result

    assert len(
        result["telemetry"]["team_a"]
    ) == 1

    assert len(
        result["telemetry"]["team_b"]
    ) == 1

    assert (
        result["telemetry"]["team_a"][0]
        ["monster_id"]
        == "griffon_igneous"
    )



def test_simulate_battles_returns_average_telemetry():

    result = simulate_battles(
        ["griffon_igneous"],
        ["slime_storm"],
        runs=3
    )

    assert "team_a_telemetry" in result
    assert "team_b_telemetry" in result

    assert (
        result["team_a_telemetry"][0]
        ["direct_damage"]
        >= 0
    )



# =========================================================
#                 CONTROL TELEMETRY TESTS
# =========================================================

def test_denied_turn_is_credited_to_control_source():

    controller = create_monster(
        "drake_abyssal"
    )

    target = create_monster(
        "drake_storm"
    )

    telemetry = create_battle_telemetry(
        [controller],
        [target]
    )

    stun = create_status_effect(
        effect_id="stun",
        duration=1,
        source=controller
    )

    target.apply_status_effect(
        stun
    )

    turn_context = begin_turn(
        target,
        telemetry
    )

    was_denied = (
        combat_module.handle_incapacitated_turn(
            target,
            turn_context,
            telemetry
        )
    )

    result = serialize_battle_telemetry(
        telemetry
    )

    assert was_denied is True

    assert (
        result["team_a"][0]["turns_denied"]
        == 1
    )

    assert (
        result["team_b"][0]["turns_denied"]
        == 0
    )



def test_neutral_targeting_ignores_attribute_priority(
    monkeypatch
):

    attacker = create_monster(
        "drake_igneous"
    )

    advantaged_target = create_monster(
        "drake_storm"
    )

    neutral_target = create_monster(
        "drake_igneous"
    )

    skill = attacker.get_skill(1)

    monkeypatch.setattr(
        random,
        "choices",
        lambda population, weights, k: [
            population[-1]
        ]
    )

    attribute_target = choose_enemy_target(
        attacker,
        [
            advantaged_target,
            neutral_target
        ],
        skill,
        attribute_targeting=True
    )

    neutral_ai_target = choose_enemy_target(
        attacker,
        [
            advantaged_target,
            neutral_target
        ],
        skill,
        attribute_targeting=False
    )

    assert attribute_target is advantaged_target
    assert neutral_ai_target is neutral_target



def test_freeze_application_and_break_before_turn_are_tracked(
    monkeypatch
):

    controller = create_monster(
        "drake_abyssal"
    )

    ally = create_monster(
        "thornet_igneous"
    )

    target = create_monster(
        "drake_igneous"
    )

    telemetry = create_battle_telemetry(
        [controller, ally],
        [target]
    )

    freeze_skill = controller.get_skill(3)

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )

    applied = freeze_skill.try_apply_effect(
        {
            "effect_id": "freeze",
            "chance": 1.0,
            "turns": 1
        },
        controller,
        target,
        telemetry=telemetry
    )

    assert applied is not None

    attack = ally.get_skill(1)

    monkeypatch.setattr(
        attack,
        "damage_calc",
        lambda *args, **kwargs: (
            100,
            False
        )
    )

    attack.execute(
        ally,
        [target],
        context={
            "team": [
                controller,
                ally
            ],
            "opponents": [
                target
            ],
            "telemetry": telemetry
        }
    )

    result = serialize_battle_telemetry(
        telemetry
    )

    controller_data = (
        result["team_a"][0]
    )

    assert controller_data[
        "freezes_applied"
    ] == 1

    assert controller_data[
        "freeze_turns_denied"
    ] == 0

    assert controller_data[
        "freezes_broken_before_turn"
    ] == 1



def test_freeze_denied_turn_is_tracked_by_type():

    controller = create_monster(
        "drake_abyssal"
    )

    target = create_monster(
        "drake_storm"
    )

    telemetry = create_battle_telemetry(
        [controller],
        [target]
    )

    freeze = create_status_effect(
        effect_id="freeze",
        duration=1,
        source=controller
    )

    freeze.denied_turns_since_application = 0

    target.apply_status_effect(
        freeze
    )

    turn_context = begin_turn(
        target,
        telemetry
    )

    combat_module.handle_incapacitated_turn(
        target,
        turn_context,
        telemetry
    )

    result = serialize_battle_telemetry(
        telemetry
    )

    controller_data = (
        result["team_a"][0]
    )

    assert controller_data[
        "turns_denied"
    ] == 1

    assert controller_data[
        "freeze_turns_denied"
    ] == 1

    assert controller_data[
        "stun_turns_denied"
    ] == 0



def test_stormbreak_reduces_damage_after_five_hits_on_same_target(
    monkeypatch
):

    storm = create_monster(
        "drake_storm"
    )

    target = create_monster(
        "drake_abyssal"
    )

    stormbreak = next(
        skill
        for skill in storm.skills
        if skill.skill_id == "stormbreak"
    )

    received_multipliers = []

    def fake_damage_calc(
        attacker,
        defender,
        hit_multiplier,
        snapshot,
        hit_index
    ):

        received_multipliers.append(
            hit_multiplier
        )

        return 1, False

    monkeypatch.setattr(
        stormbreak,
        "damage_calc",
        fake_damage_calc
    )

    stormbreak.execute(
        storm,
        [target],
        context={
            "team": [storm],
            "opponents": [target]
        }
    )

    assert received_multipliers == [
        1.0,
        1.0,
        1.0,
        1.0,
        1.0,
        0.25,
        0.25,
        0.25,
        0.25,
        0.25
    ]



def test_stormbreak_keeps_original_base_multiplier():

    storm = create_monster(
        "drake_storm"
    )

    stormbreak = next(
        skill
        for skill in storm.skills
        if skill.skill_id == "stormbreak"
    )

    assert stormbreak.multiplier == 1.60

    assert stormbreak.repeated_target_damage == {
        "full_damage_hits": 5,
        "later_hit_multiplier": 0.25,
        "first_hit_bonus_if_caster_buff": {
            "effect_id": "speed_up",
            "multiplier": 1.50
        }
    }



def test_stormbreak_first_hit_per_target_is_boosted_by_speed_up(
    monkeypatch
):

    storm = create_monster(
        "drake_storm"
    )

    target_1 = create_monster(
        "drake_abyssal"
    )

    target_2 = create_monster(
        "drake_igneous"
    )

    target_3 = create_monster(
        "drake_storm"
    )

    stormbreak = next(
        skill
        for skill in storm.skills
        if skill.skill_id == "stormbreak"
    )

    speed_up = create_status_effect(
        effect_id="speed_up",
        duration=2,
        source=storm
    )

    storm.apply_status_effect(
        speed_up
    )

    received = {}

    def fake_damage_calc(
        attacker,
        defender,
        hit_multiplier,
        snapshot,
        hit_index
    ):

        received.setdefault(
            defender,
            []
        ).append(
            hit_multiplier
        )

        return 1, False

    monkeypatch.setattr(
        stormbreak,
        "damage_calc",
        fake_damage_calc
    )

    monkeypatch.setattr(
        random,
        "choice",
        lambda population: population[0]
    )

    monkeypatch.setattr(
        random,
        "shuffle",
        lambda values: None
    )

    stormbreak.execute(
        storm,
        [
            target_1,
            target_2,
            target_3
        ],
        context={
            "team": [storm],
            "opponents": [
                target_1,
                target_2,
                target_3
            ]
        }
    )

    assert received[target_1][0] == 1.50
    assert received[target_2][0] == 1.50
    assert received[target_3][0] == 1.50



def test_stormbreak_has_no_first_hit_bonus_without_speed_up(
    monkeypatch
):

    storm = create_monster(
        "drake_storm"
    )

    target = create_monster(
        "drake_abyssal"
    )

    stormbreak = next(
        skill
        for skill in storm.skills
        if skill.skill_id == "stormbreak"
    )

    received_multipliers = []

    def fake_damage_calc(
        attacker,
        defender,
        hit_multiplier,
        snapshot,
        hit_index
    ):

        received_multipliers.append(
            hit_multiplier
        )

        return 1, False

    monkeypatch.setattr(
        stormbreak,
        "damage_calc",
        fake_damage_calc
    )

    stormbreak.execute(
        storm,
        [target],
        context={
            "team": [storm],
            "opponents": [target]
        }
    )

    assert received_multipliers[0] == 1.0



# =========================================================
#                 DRAKE RESONANCE REGRESSION
# =========================================================

def test_frigid_reduces_action_gauge_against_slowed_target(
    monkeypatch
):

    drake = create_monster(
        "drake_abyssal"
    )

    target = create_monster(
        "drake_igneous"
    )

    skill = create_skill(
        "rime_breath_frigid"
    )

    slow = create_status_effect(
        effect_id="speed_break",
        duration=2,
        source=drake
    )

    target.apply_status_effect(
        slow
    )

    target.action_gauge = 1.0

    monkeypatch.setattr(
        skill,
        "damage_calc",
        lambda *args, **kwargs: (
            1,
            False
        )
    )

    skill.execute(
        drake,
        [target],
        context={
            "team": [drake],
            "opponents": [target]
        }
    )

    assert target.action_gauge == pytest.approx(
        0.80
    )



def test_short_circuit_still_works_with_blitz(
    monkeypatch
):

    drake = create_monster(
        "drake_storm"
    )

    target = create_monster(
        "drake_igneous"
    )

    drake.passives = [
        create_passive(
            "short_circuit"
        )
    ]

    speed_up = create_status_effect(
        effect_id="speed_up",
        duration=2,
        source=drake
    )

    drake.apply_status_effect(
        speed_up
    )

    skill = create_skill(
        "lightning_rush_blitz"
    )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    skill.execute(
        drake,
        [target],
        context={
            "team": [drake],
            "opponents": [target]
        }
    )

    assert any(
        debuff.effect_id == "stun"
        for debuff in target.debuffs
    )



def test_requiem_keeps_current_stormbreak_target_scaling():

    skill = create_skill(
        "stormbreak_requiem"
    )

    assert skill.repeated_target_damage == {
        "full_damage_hits": 5,
        "later_hit_multiplier": 0.25,
        "first_hit_bonus_if_caster_buff": {
            "effect_id": "speed_up",
            "multiplier": 1.50
        }
    }



def test_r5_drake_kit_can_be_built():

    for monster_id in (
        "drake_igneous",
        "drake_abyssal",
        "drake_storm"
    ):

        monster = create_monster(
            monster_id
        )

        monster.resonance = 5

        update_resonance_kit(
            monster
        )

        assert monster.resonance == 5
        assert len(monster.skills) == 3



def test_everfrost_resets_s3_when_max_scales_are_reached(
    monkeypatch
):

    drake = create_monster(
        "drake_abyssal"
    )

    drake.passives = [
        create_passive(
            "frozen_scales_everfrost"
        )
    ]

    drake.skills = [
        create_skill("draconic_claw"),
        create_skill("rime_breath_frigid"),
        create_skill(
            "glacial_collapse_absolute_zero"
        )
    ]

    targets = [
        create_monster("drake_igneous"),
        create_monster("drake_storm"),
        create_monster("griffon_igneous")
    ]

    for target in targets:
        slow = create_status_effect(
            effect_id="speed_break",
            duration=2,
            source=drake
        )
        target.apply_status_effect(
            slow
        )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )

    s3 = drake.get_skill(3)
    s3.current_cooldown = 4

    context = {
        "skill": s3,
        "targets": targets,
        "team": [drake],
        "opponents": targets
    }

    trigger_passives(
        "before_skill",
        drake,
        context
    )

    result = s3.execute(
        drake,
        targets,
        context
    )

    context["skill_result"] = result

    trigger_passives(
        "after_skill",
        drake,
        context
    )

    assert (
        drake.get_combat_resource(
            "frozen_scales"
        )
        == 3
    )

    assert s3.current_cooldown == 0



def test_molten_core_gains_action_gauge_only_once_per_skill(
    monkeypatch
):

    drake = create_monster(
        "drake_igneous"
    )

    drake.resonance = 4
    update_resonance_kit(
        drake
    )

    targets = [
        create_monster("thornet_igneous"),
        create_monster("thornet_abyssal"),
        create_monster("thornet_storm")
    ]

    skill = drake.get_skill(2)

    monkeypatch.setattr(
        skill,
        "damage_calc",
        lambda *args, **kwargs: (
            1,
            False
        )
    )

    # Force every Cinderblood proc to succeed.
    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    drake.use_skill(
        targets,
        skill,
        combat_context={
            "team": [drake],
            "opponents": targets
        }
    )

    assert drake.action_gauge == pytest.approx(
        0.10
    )


def test_afterburn_adds_one_burn_to_burning_target(
    monkeypatch
):

    drake = create_monster(
        "drake_igneous"
    )

    target = create_monster(
        "drake_abyssal"
    )

    burn = create_status_effect(
        effect_id="burn",
        duration=3,
        stacks=1,
        source=drake
    )

    target.apply_status_effect(
        burn
    )

    skill = create_skill(
        "scorching_breath_afterburn"
    )

    monkeypatch.setattr(
        skill,
        "damage_calc",
        lambda *args, **kwargs: (
            1,
            False
        )
    )

    # Prevent Cinderblood from adding random Burn stacks.
    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.99
    )

    skill.execute(
        drake,
        [target],
        context={
            "team": [drake],
            "opponents": [target]
        }
    )

    active_burn = next(
        debuff
        for debuff in target.debuffs
        if debuff.effect_id == "burn"
    )

    assert active_burn.stacks == 2



def test_afterburn_does_not_self_enable_from_burn_gained_during_skill(
    monkeypatch
):

    drake = create_monster(
        "drake_igneous"
    )

    drake.resonance = 2
    update_resonance_kit(
        drake
    )

    target = create_monster(
        "drake_abyssal"
    )

    skill = drake.get_skill(2)

    monkeypatch.setattr(
        skill,
        "damage_calc",
        lambda *args, **kwargs: (
            1,
            False
        )
    )

    # Force Cinderblood: Ignite to apply Burn on both hits.
    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    skill.execute(
        drake,
        [target],
        context={
            "team": [drake],
            "opponents": [target]
        }
    )

    active_burn = next(
        debuff
        for debuff in target.debuffs
        if debuff.effect_id == "burn"
    )

    # Two Burns come from the two Cinderblood procs.
    # Afterburn must not add a third stack because the target
    # did not have Burn when the skill started.
    assert active_burn.stacks == 2


def test_everlasting_winter_preserves_abyssal_freeze_from_ally_damage():

    abyssal = create_monster(
        "drake_abyssal"
    )

    abyssal.passives = [
        create_passive(
            "frostborne_everlasting_winter"
        )
    ]

    ally = create_monster(
        "drake_igneous"
    )

    target = create_monster(
        "drake_storm"
    )

    freeze = create_status_effect(
        effect_id="freeze",
        duration=1,
        source=abyssal
    )

    target.apply_status_effect(
        freeze
    )

    target.receive_damage(
        1,
        source=ally
    )

    assert any(
        debuff.effect_id == "freeze"
        for debuff in target.debuffs
    )



def test_requiem_follow_up_uses_rebalanced_multiplier(
    monkeypatch
):

    drake = create_monster(
        "drake_storm"
    )

    target = create_monster(
        "drake_igneous"
    )

    skill = create_skill(
        "stormbreak_requiem"
    )

    received_multipliers = []

    def fake_damage_calc(
        attacker,
        defender,
        hit_multiplier,
        snapshot,
        hit_index
    ):

        received_multipliers.append(
            hit_multiplier
        )

        return 1, False

    monkeypatch.setattr(
        skill,
        "damage_calc",
        fake_damage_calc
    )

    skill.execute(
        drake,
        [target],
        context={
            "team": [drake],
            "opponents": [target]
        }
    )

    assert received_multipliers[-1] == pytest.approx(
        0.75
    )



def test_incineration_ignores_defense_at_three_burn_stacks():

    igneous = create_monster(
        "drake_igneous"
    )

    target = create_monster(
        "drake_abyssal"
    )

    skill = create_skill(
        "flame_devourer_incineration"
    )

    burn = create_status_effect(
        effect_id="burn",
        duration=3,
        stacks=3,
        source=igneous
    )

    target.apply_status_effect(
        burn
    )

    snapshot = skill.get_target_snapshot(
        target
    )

    damage_data = (
        skill.damage_handler_data
    )

    assert (
        damage_data[
            "ignore_defense_at_stacks"
        ]
        == 3
    )

    handler = DAMAGE_HANDLERS[
        skill.damage_handler
    ]

    result = handler(
        igneous,
        target,
        skill,
        snapshot,
        0
    )

    assert result[
        "ignore_defense"
    ] is True



def test_absolute_zero_can_freeze_without_slow(
    monkeypatch
):

    abyssal = create_monster(
        "drake_abyssal"
    )

    target = create_monster(
        "drake_igneous"
    )

    abyssal.resonance = 5

    update_resonance_kit(
        abyssal
    )

    abyssal.accuracy = 0
    target.resistance = 100

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 0.0
    )

    skill = abyssal.get_skill(3)

    skill.execute(
        abyssal,
        [target]
    )

    assert any(
        debuff.effect_id == "freeze"
        for debuff in target.debuffs
    )



def test_incineration_resets_s2_at_three_burn_stacks():

    igneous = create_monster(
        "drake_igneous"
    )

    igneous.resonance = 5

    update_resonance_kit(
        igneous
    )

    target = create_monster(
        "drake_abyssal"
    )

    burn = create_status_effect(
        effect_id="burn",
        duration=3,
        stacks=3,
        source=igneous
    )

    target.apply_status_effect(
        burn
    )

    s2 = igneous.get_skill(2)
    s3 = igneous.get_skill(3)

    s2.current_cooldown = 3

    s3.execute(
        igneous,
        [target]
    )

    assert s2.current_cooldown == 0



def test_incineration_ai_waits_for_three_burn_stacks(
    monkeypatch
):

    igneous = create_monster(
        "drake_igneous"
    )

    igneous.resonance = 5
    update_resonance_kit(
        igneous
    )

    target = create_monster(
        "drake_abyssal"
    )

    # Ensure no skill is treated as a guaranteed kill.
    monkeypatch.setattr(
        "game.combat.enemy_ai.sees_kill",
        lambda *args, **kwargs: False
    )

    selected_skill = choose_skill(
        igneous,
        [igneous],
        [target]
    )

    assert (
        selected_skill.skill_id
        != "flame_devourer_incineration"
    )

    burn = create_status_effect(
        effect_id="burn",
        duration=3,
        stacks=3,
        source=igneous
    )

    target.apply_status_effect(
        burn
    )

    # Make the weighted selection deterministic toward S3.
    monkeypatch.setattr(
        random,
        "choices",
        lambda population, weights, k: [
            population[-1]
        ]
    )

    selected_skill = choose_skill(
        igneous,
        [igneous],
        [target]
    )

    assert (
        selected_skill.skill_id
        == "flame_devourer_incineration"
    )



def test_estimate_damage_applies_incineration_ignore_defense():

    igneous = create_monster(
        "drake_igneous"
    )

    target = create_monster(
        "drake_storm"
    )

    skill = create_skill(
        "flame_devourer_incineration"
    )

    burn = create_status_effect(
        effect_id="burn",
        duration=3,
        stacks=3,
        source=igneous
    )

    target.apply_status_effect(
        burn
    )

    estimated_damage = estimate_damage(
        igneous,
        target,
        skill
    )

    expected_damage = (
        skill.base_damage_calc(
            igneous,
            target,
            1,
            1.45,
            True
        )
    )

    assert estimated_damage == pytest.approx(
        expected_damage
    )



def test_incineration_targeting_prefers_three_burn_target():

    igneous = create_monster(
        "drake_igneous"
    )

    skill = create_skill(
        "flame_devourer_incineration"
    )

    burned_target = create_monster(
        "drake_storm"
    )

    unburned_target = create_monster(
        "drake_abyssal"
    )

    burn = create_status_effect(
        effect_id="burn",
        duration=3,
        stacks=3,
        source=igneous
    )

    burned_target.apply_status_effect(
        burn
    )

    target = choose_enemy_target(
        igneous,
        [
            unburned_target,
            burned_target
        ],
        skill,
        attribute_targeting=False
    )

    assert target is burned_target



def test_absolute_zero_ai_does_not_require_slow(
    monkeypatch
):

    abyssal = create_monster(
        "drake_abyssal"
    )

    abyssal.resonance = 5

    update_resonance_kit(
        abyssal
    )

    target = create_monster(
        "drake_storm"
    )

    monkeypatch.setattr(
        "game.combat.enemy_ai.sees_kill",
        lambda *args, **kwargs: False
    )

    monkeypatch.setattr(
        random,
        "choices",
        lambda population, weights, k: [
            population[-1]
        ]
    )

    selected_skill = choose_skill(
        abyssal,
        [abyssal],
        [target]
    )

    assert (
        selected_skill.skill_id
        == "glacial_collapse_absolute_zero"
    )



def test_absolute_zero_without_slow_uses_seventy_five_percent_freeze(
    monkeypatch
):

    abyssal = create_monster(
        "drake_abyssal"
    )

    target = create_monster(
        "drake_storm"
    )

    abyssal.resonance = 5

    update_resonance_kit(
        abyssal
    )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.80
    )

    skill = abyssal.get_skill(3)

    skill.execute(
        abyssal,
        [target]
    )

    assert not any(
        debuff.effect_id == "freeze"
        for debuff in target.debuffs
    )



def test_absolute_zero_with_slow_guarantees_freeze(
    monkeypatch
):

    abyssal = create_monster(
        "drake_abyssal"
    )

    target = create_monster(
        "drake_storm"
    )

    abyssal.resonance = 5

    update_resonance_kit(
        abyssal
    )

    slow = create_status_effect(
        effect_id="speed_break",
        duration=2,
        source=abyssal
    )

    target.apply_status_effect(
        slow
    )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.99
    )

    skill = abyssal.get_skill(3)

    skill.execute(
        abyssal,
        [target]
    )

    assert any(
        debuff.effect_id == "freeze"
        for debuff in target.debuffs
    )



def test_molten_core_uses_tempo_rebalance():

    data = PASSIVE_DATA[
        "cinderblood_molten_core"
    ]

    assert data["chance"] == pytest.approx(
        0.65
    )

    assert data["stacks"] == 1

    assert data["action_gauge"] == pytest.approx(
        0.10
    )

    assert data[
        "action_gauge_once_per_skill"
    ] is True


def test_simulate_battles_accepts_resonance_per_team_slot(
    monkeypatch
):

    captured = {}

    def fake_simulate_battle(
        team_a,
        team_b,
        max_turns=200,
        attribute_targeting=True,
        team_a_initial_buffs=None,
        team_b_initial_buffs=None
    ):

        captured["team_a"] = [
            monster.resonance
            for monster in team_a
        ]

        captured["team_b"] = [
            monster.resonance
            for monster in team_b
        ]

        return {
            "outcome": "draw",
            "turns": 1,
            "team_a_remaining_hp": sum(
                monster.health
                for monster in team_a
            ),
            "team_b_remaining_hp": sum(
                monster.health
                for monster in team_b
            ),
            "telemetry": {
                "team_a": {},
                "team_b": {}
            }
        }

    monkeypatch.setattr(
        "game.combat.combat.simulate_battle",
        fake_simulate_battle
    )

    monkeypatch.setattr(
        "game.combat.combat.add_team_telemetry",
        lambda *args, **kwargs: None
    )

    simulate_battles(
        [
            "drake_igneous",
            "drake_storm"
        ],
        [
            "drake_igneous",
            "drake_abyssal"
        ],
        runs=1,
        verbose=False,
        level=50,
        ascended=True,
        team_a_resonances=[5, 5],
        team_b_resonances=[5, 5]
    )

    assert captured["team_a"] == [5, 5]
    assert captured["team_b"] == [5, 5]


def test_simulate_battles_rejects_wrong_resonance_list_length():

    with pytest.raises(ValueError):

        simulate_battles(
            [
                "drake_igneous",
                "drake_storm"
            ],
            [
                "drake_igneous",
                "drake_abyssal"
            ],
            runs=1,
            team_a_resonances=[5],
            team_b_resonances=[5, 5]
        )


# =========================================================
#                  AETHER DRAKE TESTS
# =========================================================

def test_heavens_decree_applies_three_team_buffs():

    aether = create_monster("drake_aether")
    ally = create_monster("drake_igneous")

    aether.use_skill(
        [aether, ally],
        aether.get_skill(3),
        combat_context={
            "team": [aether, ally],
            "opponents": []
        }
    )

    for monster in [aether, ally]:
        buff_ids = {
            buff.effect_id
            for buff in monster.buffs
        }

        assert buff_ids == {
            "attack_up",
            "immunity",
            "veil"
        }

        assert all(
            buff.remaining_turns == 2
            for buff in monster.buffs
        )


def test_divine_grace_heals_five_percent_per_buff():

    aether = create_monster("drake_aether")
    aether.resonance = 1
    update_resonance_kit(aether)

    ally = create_monster("drake_igneous")
    ally.health = int(ally.max_health * 0.50)
    health_before = ally.health

    aether.use_skill(
        [aether, ally],
        aether.get_skill(3),
        combat_context={
            "team": [aether, ally],
            "opponents": []
        }
    )

    expected_heal = int(
        ally.max_health * 0.15
    )

    assert ally.health == (
        health_before + expected_heal
    )


def test_sovereign_breath_scales_silence_with_buffs(
    monkeypatch
):

    aether = create_monster("drake_aether")
    target = create_monster("drake_igneous")

    for effect_id in [
        "attack_up",
        "immunity",
        "veil"
    ]:
        aether.apply_status_effect(
            create_status_effect(
                effect_id=effect_id,
                duration=2,
                source=aether
            )
        )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.55
    )
    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )

    aether.get_skill(2).execute(
        aether,
        [target],
        {
            "team": [aether],
            "opponents": [target]
        }
    )

    assert any(
        debuff.effect_id == "silence"
        for debuff in target.debuffs
    )


def test_celestial_authority_ascendance_gives_gauge_to_most_buffed_ally(
    monkeypatch
):

    aether = create_monster("drake_aether")
    aether.resonance = 2
    update_resonance_kit(aether)

    ally = create_monster("drake_igneous")
    attacker = create_monster("drake_storm")

    aether._combat_team = [aether, ally]

    for effect_id in [
        "attack_up",
        "immunity"
    ]:
        ally.apply_status_effect(
            create_status_effect(
                effect_id=effect_id,
                duration=2,
                source=aether
            )
        )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )
    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )

    trigger_passives(
        "on_receive_hit",
        aether,
        {"attacker": attacker}
    )

    assert any(
        debuff.effect_id == "attack_break"
        for debuff in attacker.debuffs
    )

    assert ally.action_gauge == pytest.approx(
        0.20
    )


def test_subjugation_upgrades_silence_and_cooldown():

    aether = create_monster("drake_aether")
    aether.resonance = 3
    update_resonance_kit(aether)

    skill = aether.get_skill(2)

    assert skill.cooldown == 3

    data = skill.after_use_handlers[0][
        "data"
    ]

    assert data["base_chance"] == pytest.approx(
        0.50
    )

    assert data["max_chance"] == pytest.approx(
        1.00
    )


def test_divine_grace_enlightenment_adds_accuracy():

    aether = create_monster("drake_aether")
    aether.resonance = 4
    update_resonance_kit(aether)

    assert aether.get_effective_stat(
        "accuracy"
    ) == pytest.approx(50)


def test_apotheosis_uses_three_turn_buffs_and_grants_extra_turn():

    aether = create_monster("drake_aether")
    aether.resonance = 5
    update_resonance_kit(aether)

    aether.use_skill(
        [aether],
        aether.get_skill(3),
        combat_context={
            "team": [aether],
            "opponents": []
        }
    )

    assert len(aether.buffs) == 3

    assert all(
        buff.remaining_turns == 3
        for buff in aether.buffs
    )

    assert aether.extra_turn_pending is True


# =========================================================
#                   VOID DRAKE TESTS
# =========================================================

def test_null_rend_applies_oblivion_only_on_second_hit(
    monkeypatch
):

    void = create_monster("drake_void")
    target = create_monster("drake_igneous")
    skill = void.get_skill(2)

    target_result = skill.create_target_result(
        target
    )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )
    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )
    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    skill.resolve_hit(
        void,
        target,
        0,
        target_result
    )

    assert not any(
        debuff.effect_id == "oblivion"
        for debuff in target.debuffs
    )

    skill.resolve_hit(
        void,
        target,
        1,
        target_result
    )

    assert any(
        debuff.effect_id == "oblivion"
        for debuff in target.debuffs
    )


def test_obliterate_second_hit_has_thirty_percent_bonus_damage():

    void = create_monster("drake_void")
    void.resonance = 1
    update_resonance_kit(void)

    target = create_monster("drake_igneous")
    skill = void.get_skill(2)

    first_hit = skill.base_damage_calc(
        void,
        target,
        1.00
    )

    second_hit = skill.base_damage_calc(
        void,
        target,
        1.30
    )

    assert second_hit == pytest.approx(
        first_hit * 1.30
    )


def test_null_rend_uses_original_base_multiplier():

    void = create_monster(
        "drake_void"
    )

    assert (
        void.get_skill(2).multiplier
        == pytest.approx(2.10)
    )


def test_veil_blocks_strip_and_is_consumed():

    void = create_monster("drake_void")
    target = create_monster("drake_aether")

    for effect_id in [
        "attack_up",
        "immunity",
        "veil"
    ]:
        target.apply_status_effect(
            create_status_effect(
                effect_id=effect_id,
                duration=2,
                source=target
            )
        )

    skill = void.get_skill(3)
    target_result = skill.create_target_result(
        target
    )

    skill.resolve_hit(
        void,
        target,
        0,
        target_result
    )

    buff_ids = {
        buff.effect_id
        for buff in target.buffs
    }

    assert "veil" not in buff_ids
    assert "attack_up" in buff_ids
    assert "immunity" in buff_ids


def test_bottomless_hunger_counts_each_removed_buff():

    void = create_monster("drake_void")
    target = create_monster("drake_igneous")

    void.health = int(
        void.max_health * 0.50
    )
    health_before = void.health

    for effect_id in [
        "attack_up",
        "immunity"
    ]:
        target.apply_status_effect(
            create_status_effect(
                effect_id=effect_id,
                duration=2,
                source=target
            )
        )

    skill = void.get_skill(3)
    target_result = skill.create_target_result(
        target
    )

    skill.resolve_hit(
        void,
        target,
        0,
        target_result
    )

    assert target.buffs == []

    assert void.health == (
        health_before
        + int(void.max_health * 0.20)
    )

    assert void.action_gauge == pytest.approx(
        0.16
    )


def test_voidborn_activates_at_five_removed_buffs():

    void = create_monster("drake_void")
    void.resonance = 2
    update_resonance_kit(void)

    trigger_passives(
        "on_remove_enemy_buff",
        void,
        {"removed_count": 5}
    )

    assert void.get_combat_resource(
        "voidborn"
    ) == 0

    assert any(
        buff.effect_id == "invincibility"
        and buff.remaining_turns == 2
        for buff in void.buffs
    )


def test_voidborn_extra_activations_extend_invincibility_and_damage():

    void = create_monster("drake_void")
    void.resonance = 5
    update_resonance_kit(void)

    skill = void.get_skill(3)

    trigger_passives(
        "on_remove_enemy_buff",
        void,
        {
            "removed_count": 15,
            "skill": skill
        }
    )

    invincibility = next(
        buff
        for buff in void.buffs
        if buff.effect_id == "invincibility"
    )

    assert invincibility.remaining_turns == 4

    assert (
        skill._voidborn_activations_this_use
        == 3
    )

    assert (
        skill._voidborn_damage_bonus_this_use
        == pytest.approx(0.40)
    )


def test_voidborn_bonus_empowers_remaining_dismantle_hits(
    monkeypatch
):

    void = create_monster("drake_void")
    void.resonance = 5
    update_resonance_kit(void)

    target = create_monster(
        "drake_igneous"
    )

    skill = void.get_skill(3)

    skill._is_executing = True
    skill._removed_buffs_this_use = 10
    skill._voidborn_damage_bonus_this_use = 0.20

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    snapshot = skill.get_target_snapshot(
        target
    )

    damage, critical = skill.damage_calc(
        void,
        target,
        1.0,
        snapshot,
        1
    )

    expected = int(
        skill.base_damage_calc(
            void,
            target,
            1.0,
            damage_multiplier=2.0
        )
    )

    assert critical is False
    assert damage == expected


def test_voidborn_transcendence_full_cleanses_on_activation():

    void = create_monster("drake_void")
    void.resonance = 3
    update_resonance_kit(void)

    void.apply_status_effect(
        create_status_effect(
            effect_id="poison",
            duration=2,
            source=void
        )
    )

    trigger_passives(
        "on_remove_enemy_buff",
        void,
        {"removed_count": 5}
    )

    assert void.debuffs == []

    assert any(
        buff.effect_id == "invincibility"
        for buff in void.buffs
    )


def test_dismantle_decimation_has_upgraded_proc_and_cooldown():

    void = create_monster("drake_void")
    void.resonance = 4
    update_resonance_kit(void)

    skill = void.get_skill(3)

    assert skill.cooldown == 4

    handler_data = (
        skill.on_hit_handlers[1][
            "data"
        ]
    )

    assert handler_data["chance"] == pytest.approx(
        0.50
    )


def test_annihilation_banishes_killed_oblivion_target(
    monkeypatch
):

    void = create_monster("drake_void")
    void.resonance = 5
    update_resonance_kit(void)

    target = create_monster("drake_igneous")

    target.apply_status_effect(
        create_status_effect(
            effect_id="oblivion",
            duration=2,
            source=void
        )
    )

    target.health = 1

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    void.use_skill(
        [target],
        void.get_skill(2),
        combat_context={
            "team": [void],
            "opponents": [target]
        }
    )

    assert target.is_alive is False
    assert target.banished is True


def test_oblivion_prevents_passive_activation(
    monkeypatch
):

    aether = create_monster("drake_aether")
    attacker = create_monster("drake_storm")

    aether.apply_status_effect(
        create_status_effect(
            effect_id="oblivion",
            duration=2,
            source=attacker
        )
    )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )
    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )

    trigger_passives(
        "on_receive_hit",
        aether,
        {"attacker": attacker}
    )

    assert not any(
        debuff.effect_id == "attack_break"
        for debuff in attacker.debuffs
    )


def test_invincibility_prevents_direct_damage():

    void = create_monster("drake_void")
    attacker = create_monster("drake_igneous")

    void.apply_status_effect(
        create_status_effect(
            effect_id="invincibility",
            duration=2,
            source=void
        )
    )

    health_before = void.health

    void.receive_damage(
        1000,
        source=attacker
    )

    assert void.health == health_before


# =========================================================
#                    VOID DRAKE AI TESTS
# =========================================================

def test_void_ai_prioritizes_dismantle_when_enemy_has_buff(
    monkeypatch
):

    void = create_monster(
        "drake_void"
    )

    void.resonance = 5
    update_resonance_kit(
        void
    )

    target = create_monster(
        "drake_igneous"
    )

    target.apply_status_effect(
        create_status_effect(
            effect_id="attack_up",
            duration=2,
            source=target
        )
    )

    monkeypatch.setattr(
        "game.combat.enemy_ai.sees_kill",
        lambda *args, **kwargs: False
    )

    selected_skill = choose_skill(
        void,
        [void],
        [target]
    )

    assert (
        selected_skill.skill_id
        == "dismantle_decimation"
    )


def test_void_ai_does_not_force_dismantle_without_enemy_buffs(
    monkeypatch
):

    void = create_monster(
        "drake_void"
    )

    void.resonance = 5
    update_resonance_kit(
        void
    )

    target = create_monster(
        "drake_igneous"
    )

    monkeypatch.setattr(
        "game.combat.enemy_ai.sees_kill",
        lambda *args, **kwargs: False
    )

    monkeypatch.setattr(
        random,
        "choices",
        lambda population, weights, k: [
            population[1]
        ]
    )

    selected_skill = choose_skill(
        void,
        [void],
        [target]
    )

    assert (
        selected_skill.skill_id
        == "null_rend_annihilation"
    )


def test_dismantle_later_hits_scale_with_all_buffs_devoured(
    monkeypatch
):

    void = create_monster(
        "drake_void"
    )

    void.resonance = 5
    update_resonance_kit(
        void
    )

    targets = [
        create_monster(
            "drake_igneous"
        )
        for _ in range(3)
    ]

    for target in targets:

        for effect_id in (
            "attack_up",
            "speed_up",
            "crit_rate_up"
        ):

            target.apply_status_effect(
                create_status_effect(
                    effect_id=effect_id,
                    duration=3,
                    source=target
                )
            )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 1.0
    )

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    skill = void.get_skill(3)

    result = skill.execute(
        void,
        targets,
        context={
            "team": [void],
            "opponents": targets
        }
    )

    for target_result in result.target_results:

        first_hit_damage = (
            target_result[
                "hit_results"
            ][0]["damage"]
        )

        second_hit_damage = (
            target_result[
                "hit_results"
            ][1]["damage"]
        )

        assert second_hit_damage == pytest.approx(
            first_hit_damage * 1.72,
            abs=2
        )

    assert all(
        len(target.buffs) == 0
        for target in targets
    )


def test_dismantle_has_no_devour_damage_bonus_without_buffs(
    monkeypatch
):

    void = create_monster(
        "drake_void"
    )

    void.resonance = 5
    update_resonance_kit(
        void
    )

    targets = [
        create_monster(
            "drake_igneous"
        )
        for _ in range(3)
    ]

    monkeypatch.setattr(
        random,
        "random",
        lambda: 1.0
    )

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    skill = void.get_skill(3)

    result = skill.execute(
        void,
        targets,
        context={
            "team": [void],
            "opponents": targets
        }
    )

    for target_result in result.target_results:

        first_hit_damage = (
            target_result[
                "hit_results"
            ][0]["damage"]
        )

        second_hit_damage = (
            target_result[
                "hit_results"
            ][1]["damage"]
        )

        assert second_hit_damage == first_hit_damage


# =========================================================
#                       DULLAHANS
# =========================================================

def test_heal_block_prevents_all_healing():

    target = create_monster(
        "dullahan_igneous"
    )

    target.health = int(
        target.max_health
        * 0.50
    )

    heal_block = create_status_effect(
        effect_id="heal_block",
        duration=2
    )

    target.apply_status_effect(
        heal_block
    )

    health_before = target.health

    actual_heal = target.heal(
        5000
    )

    assert actual_heal == 0
    assert target.health == health_before



def test_vulnerability_increases_direct_damage_by_fifteen_percent(
    monkeypatch
):

    attacker = create_monster(
        "dullahan_igneous"
    )

    target = create_monster(
        "dullahan_abyssal"
    )

    skill = create_skill(
        "severing_blade"
    )

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    snapshot = skill.get_target_snapshot(
        target
    )

    base_damage, _ = skill.damage_calc(
        attacker,
        target,
        1,
        snapshot,
        0
    )

    vulnerability = create_status_effect(
        effect_id="vulnerability",
        duration=2,
        source=attacker
    )

    target.apply_status_effect(
        vulnerability
    )

    vulnerable_damage, _ = skill.damage_calc(
        attacker,
        target,
        1,
        snapshot,
        0
    )

    # Both results are floored independently after applying
    # the damage multipliers to the unrounded base damage.
    # Comparing two truncated results allows 1 HP of difference.
    assert abs(
        vulnerable_damage - int(base_damage * 1.15)
    ) <= 1



def test_chilling_presence_does_not_extend_hard_incapacitation(
    monkeypatch
):

    abyssal = create_monster(
        "dullahan_abyssal"
    )

    target = create_monster(
        "dullahan_igneous"
    )

    abyssal._combat_opponents = [
        target
    ]

    slow = create_status_effect(
        effect_id="speed_break",
        duration=2,
        source=abyssal
    )

    stun = create_status_effect(
        effect_id="stun",
        duration=1,
        source=abyssal
    )

    target.apply_status_effect(
        slow
    )

    target.apply_status_effect(
        stun
    )

    monkeypatch.setattr(
        random,
        "shuffle",
        lambda values: None
    )

    trigger_passives(
        "after_turn",
        abyssal,
        {
            "opponents": [
                target
            ]
        }
    )

    assert slow.remaining_turns == 3
    assert stun.remaining_turns == 1



def test_chilling_presence_suffocation_extends_two_distinct_debuffs(
    monkeypatch
):

    abyssal = create_monster(
        "dullahan_abyssal"
    )

    abyssal.resonance = 3
    update_resonance_kit(
        abyssal
    )

    target = create_monster(
        "dullahan_igneous"
    )

    slow = create_status_effect(
        effect_id="speed_break",
        duration=2,
        source=abyssal
    )

    attack_break = create_status_effect(
        effect_id="attack_break",
        duration=2,
        source=abyssal
    )

    target.apply_status_effect(
        slow
    )

    target.apply_status_effect(
        attack_break
    )

    monkeypatch.setattr(
        random,
        "shuffle",
        lambda values: None
    )

    trigger_passives(
        "after_turn",
        abyssal,
        {
            "opponents": [
                target
            ]
        }
    )

    assert slow.remaining_turns == 3
    assert attack_break.remaining_turns == 3



def test_final_omen_fulfilled_reduces_healing_and_grants_attack_up():

    igneous = create_monster(
        "dullahan_igneous"
    )

    igneous.resonance = 4
    update_resonance_kit(
        igneous
    )

    target = create_monster(
        "dullahan_abyssal"
    )

    target.health = int(
        target.max_health
        * 0.40
    )

    target._combat_opponents = [
        igneous
    ]

    actual_heal = target.heal(
        1000
    )

    assert actual_heal == 700

    assert any(
        buff.effect_id == "attack_up"
        for buff in igneous.buffs
    )



def test_massacre_follow_up_does_not_change_s2_cooldown(
    monkeypatch
):

    igneous = create_monster(
        "dullahan_igneous"
    )

    igneous.resonance = 5
    update_resonance_kit(
        igneous
    )

    first_target = create_monster(
        "slime_storm"
    )

    second_target = create_monster(
        "slime_abyssal"
    )

    first_target.health = 1

    igneous._combat_opponents = [
        first_target,
        second_target
    ]

    igneous._combat_team = [
        igneous
    ]

    s2 = igneous.get_skill(
        2
    )

    s3 = igneous.get_skill(
        3
    )

    s2.current_cooldown = 3

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    igneous.use_skill(
        [
            first_target
        ],
        s3,
        combat_context={
            "team": [
                igneous
            ],
            "opponents": [
                first_target,
                second_target
            ]
        }
    )

    assert not first_target.is_alive
    assert second_target.health < (
        second_target.max_health
    )
    assert s2.current_cooldown == 3



def test_storm_r2_unlocks_the_hunt_and_steals_action_gauge():

    storm = create_monster(
        "dullahan_storm"
    )

    storm.resonance = 2
    update_resonance_kit(
        storm
    )

    low = create_monster(
        "slime_igneous"
    )

    high = create_monster(
        "slime_abyssal"
    )

    low.action_gauge = 0.30
    high.action_gauge = 0.80

    trigger_passives(
        "after_turn",
        storm,
        {
            "opponents": [
                low,
                high
            ]
        }
    )

    assert high.action_gauge == pytest.approx(
        0.60
    )

    assert storm.action_gauge == pytest.approx(
        0.20
    )



def test_stampede_forces_lowest_gauge_ally_turn_without_consuming_gauge():

    storm = create_monster(
        "dullahan_storm"
    )

    storm.resonance = 5
    update_resonance_kit(
        storm
    )

    ally_low = create_monster(
        "slime_igneous"
    )

    ally_high = create_monster(
        "slime_abyssal"
    )

    ally_low.action_gauge = 0.10
    ally_high.action_gauge = 0.60

    skill = storm.get_skill(
        3
    )

    storm.use_skill(
        [
            storm
        ],
        skill,
        combat_context={
            "team": [
                storm,
                ally_low,
                ally_high
            ],
            "opponents": []
        }
    )

    assert ally_low.action_gauge == pytest.approx(
        0.40
    )

    assert ally_low.forced_turn_pending is True

    assert any(
        buff.effect_id == "attack_up"
        for buff in ally_low.buffs
    )

    assert any(
        buff.effect_id == "speed_up"
        for buff in ally_low.buffs
    )



@pytest.mark.parametrize("resonance", [2, 5])
def test_aether_soul_recall_is_a_separate_selected_revive(resonance):
    aether = create_monster("dullahan_aether")
    aether.resonance = resonance
    update_resonance_kit(aether)

    older_dead = create_monster("slime_igneous")
    recent_dead = create_monster("slime_abyssal")
    enemy = create_monster("slime_storm")

    older_dead.health = 0
    older_dead.death_order = 1
    older_dead._death_recorded = True
    older_dead.action_gauge = 0.70

    recent_dead.health = 0
    recent_dead.death_order = 2
    recent_dead._death_recorded = True

    team = [aether, older_dead, recent_dead]
    opponents = [enemy]

    aether._combat_team = team
    aether._combat_opponents = opponents

    skill = aether.get_skill(3)

    # Three charges cannot be exchanged for a revive.
    aether.add_combat_resource("soul_charges", 3, 5)
    assert not aether.can_use_soul_recall()
    assert not aether.use_soul_recall(recent_dead)
    assert aether.get_combat_resource("soul_charges") == 3

    # Beyond the Veil remains offensive, even with dead allies.
    aether.use_skill(
        opponents,
        skill,
        combat_context={
            "team": team,
            "opponents": opponents
        }
    )

    assert not older_dead.is_alive
    assert not recent_dead.is_alive

    # Even at full charges, S3 remains an offensive option:
    # it consumes charges for damage and never auto-revives.
    skill.current_cooldown = 0
    aether.add_combat_resource("soul_charges", 5, 5)
    assert aether.can_use_soul_recall()

    aether.use_skill(
        opponents,
        skill,
        combat_context={
            "team": team,
            "opponents": opponents
        }
    )

    assert not older_dead.is_alive
    assert not recent_dead.is_alive
    assert aether.get_combat_resource("soul_charges") < 5

    # The player can instead spend 5 charges to revive either ally.
    aether.add_combat_resource("soul_charges", 5, 5)
    assert aether.can_use_soul_recall()
    assert aether.can_use_soul_recall(older_dead)
    assert aether.use_soul_recall(older_dead)

    assert older_dead.is_alive
    assert not recent_dead.is_alive
    assert older_dead.health == int(older_dead.max_health * 0.50)
    assert older_dead.action_gauge == pytest.approx(1.00)
    assert older_dead.death_order is None
    assert older_dead._death_recorded is False
    assert aether.get_combat_resource("soul_charges") == 0
    assert not aether.can_use_soul_recall()


def test_aether_soul_recall_is_ready_without_a_dead_ally():
    aether = create_monster("dullahan_aether")
    aether.resonance = 2
    update_resonance_kit(aether)

    living_ally = create_monster("slime_igneous")
    aether._combat_team = [aether, living_ally]
    aether.add_combat_resource("soul_charges", 5, 5)

    # Players can select the action with 5 charges. Only fallen,
    # non-Banished teammates become legal targets.
    assert aether.can_use_soul_recall()
    assert not aether.can_use_soul_recall(living_ally)
    assert not aether.use_soul_recall(living_ally)
    assert aether.get_combat_resource("soul_charges") == 5



def test_aether_soul_recall_rejects_banished_targets_and_enemies():
    aether = create_monster("dullahan_aether")
    aether.resonance = 2
    update_resonance_kit(aether)

    dead_ally = create_monster("slime_igneous")
    dead_ally.health = 0
    dead_ally.banished = True

    enemy = create_monster("slime_storm")
    enemy.health = 0

    aether._combat_team = [aether, dead_ally]
    aether._combat_opponents = [enemy]
    aether.add_combat_resource("soul_charges", 5, 5)

    assert not aether.can_use_soul_recall(dead_ally)
    assert not aether.use_soul_recall(dead_ally)
    assert not aether.can_use_soul_recall(enemy)
    assert not aether.use_soul_recall(enemy)
    assert aether.get_combat_resource("soul_charges") == 5


def test_aether_soul_recall_requires_resonance_two_and_no_oblivion():
    aether = create_monster("dullahan_aether")
    dead_ally = create_monster("slime_igneous")
    dead_ally.health = 0
    aether._combat_team = [aether, dead_ally]
    aether.add_combat_resource("soul_charges", 5, 5)

    aether.resonance = 1
    update_resonance_kit(aether)
    assert not aether.use_soul_recall(dead_ally)

    aether.resonance = 2
    update_resonance_kit(aether)
    aether.apply_status_effect(
        create_status_effect(
            effect_id="oblivion",
            duration=2,
            source=dead_ally
        )
    )

    assert not aether.can_use_soul_recall(dead_ally)
    assert not aether.use_soul_recall(dead_ally)
    assert aether.get_combat_resource("soul_charges") == 5



def test_deaths_gaze_named_ignores_immunity_but_vulnerability_does_not(
    monkeypatch
):

    void = create_monster(
        "dullahan_void"
    )

    target = create_monster(
        "dullahan_aether"
    )

    immunity = create_status_effect(
        effect_id="immunity",
        duration=2,
        source=target
    )

    target.apply_status_effect(
        immunity
    )

    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.0
    )

    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    skill = void.get_skill(
        3
    )

    void.use_skill(
        [
            target
        ],
        skill,
        combat_context={
            "team": [
                void
            ],
            "opponents": [
                target
            ]
        }
    )

    assert target.special_states.get(
        "named_by"
    ) is void

    assert void.is_headless is True

    assert all(
        debuff.effect_id
        != "vulnerability"
        for debuff in target.debuffs
    )



def test_headless_rider_grants_speed_and_blocks_silence():

    void = create_monster(
        "dullahan_void"
    )

    target = create_monster(
        "slime_igneous"
    )

    base_speed = void.get_effective_stat(
        "speed"
    )

    void.apply_named(
        target,
        turns=2
    )

    assert void.get_effective_stat(
        "speed"
    ) == pytest.approx(
        base_speed
        + void.speed * 0.20
    )

    silence = create_status_effect(
        effect_id="silence",
        duration=2,
        source=target
    )

    applied = void.apply_status_effect(
        silence
    )

    assert applied is None
    assert void.is_silenced is False



@pytest.mark.parametrize(
    "resonance, expected_skill_ids, expected_passive_ids",
    [
        (
            0,
            ["severing_blade", "spinal_scourge", "deaths_gaze"],
            ["headless_rider"]
        ),
        (
            1,
            ["severing_blade", "spinal_scourge", "deaths_gaze"],
            ["headless_rider_unbound"]
        ),
        (
            2,
            ["severing_blade", "spinal_scourge_ossuary", "deaths_gaze"],
            ["headless_rider_unbound"]
        ),
        (
            3,
            ["severing_blade", "spinal_scourge_ossuary", "deaths_gaze_last_name"],
            ["headless_rider_unbound"]
        ),
        (
            4,
            ["severing_blade", "spinal_scourge_ossuary", "deaths_gaze_last_name"],
            ["deathless_rider"]
        ),
        (
            5,
            ["severing_blade", "spinal_scourge_ossuary", "deaths_gaze_last_name"],
            ["deathless_rider", "death_march"]
        )
    ]
)
def test_void_dullahan_resonance_progression_has_at_most_two_passives(
    resonance,
    expected_skill_ids,
    expected_passive_ids
):
    void = create_monster("dullahan_void")
    void.resonance = resonance
    update_resonance_kit(void)

    assert [skill.skill_id for skill in void.skills] == expected_skill_ids
    assert [passive.skill_id for passive in void.passives] == expected_passive_ids
    assert len(void.passives) <= 2


def test_deathless_rider_keeps_unbound_speed_bonus():
    void = create_monster("dullahan_void")
    void.resonance = 4
    update_resonance_kit(void)

    target = create_monster("slime_igneous")
    base_speed = void.get_effective_stat("speed")

    void.apply_named(target, turns=2)

    assert void.get_effective_stat("speed") == pytest.approx(
        base_speed + void.speed * 0.30
    )


def test_deathless_rider_survives_full_multihit_skill_then_enters_cooldown(
    monkeypatch
):

    void = create_monster(
        "dullahan_void"
    )

    void.resonance = 4
    update_resonance_kit(
        void
    )

    named_target = create_monster(
        "slime_igneous"
    )

    void.apply_named(
        named_target,
        turns=2
    )

    poison = create_status_effect(
        effect_id="poison",
        duration=2,
        source=named_target
    )

    void.apply_status_effect(
        poison
    )

    attacker = create_monster(
        "drake_storm"
    )

    attack = create_skill(
        "stormbreak"
    )

    void.health = 1

    monkeypatch.setattr(
        random,
        "randint",
        lambda a, b: 100
    )

    attack.execute(
        attacker,
        [
            void
        ],
        {
            "team": [
                attacker
            ],
            "opponents": [
                void
            ]
        }
    )

    assert void.health == 1

    assert void.is_headless is False

    assert void.debuffs == []

    assert void.get_internal_cooldown(
        "deathless_rider"
    ) == 6



def test_death_march_transfers_named_to_lowest_hp_enemy(
    monkeypatch
):

    void = create_monster(
        "dullahan_void"
    )

    void.resonance = 5
    update_resonance_kit(
        void
    )

    dead_target = create_monster(
        "slime_igneous"
    )

    low_target = create_monster(
        "slime_abyssal"
    )

    high_target = create_monster(
        "slime_storm"
    )

    low_target.health = int(
        low_target.max_health
        * 0.30
    )

    high_target.health = int(
        high_target.max_health
        * 0.80
    )

    void._combat_team = [
        void
    ]

    void._combat_opponents = [
        dead_target,
        low_target,
        high_target
    ]

    dead_target._combat_team = [
        dead_target,
        low_target,
        high_target
    ]

    dead_target._combat_opponents = [
        void
    ]

    low_target._combat_team = (
        dead_target._combat_team
    )

    low_target._combat_opponents = [
        void
    ]

    high_target._combat_team = (
        dead_target._combat_team
    )

    high_target._combat_opponents = [
        void
    ]

    void.apply_named(
        dead_target,
        turns=2
    )

    dead_target.health = 0

    monkeypatch.setattr(
        random,
        "uniform",
        lambda a, b: 100
    )

    notify_monster_death(
        dead_target
    )

    assert void.special_states.get(
        "named_target"
    ) is low_target

    assert low_target.special_states.get(
        "named_by"
    ) is void

    assert any(
        debuff.effect_id
        == "vulnerability"
        for debuff in low_target.debuffs
    )

    assert low_target.health == int(
        low_target.max_health
        * 0.30
    )

