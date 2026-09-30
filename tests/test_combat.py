import random
import pytest

from game.factories.monster_factory import create_monster, create_passive, create_skill
from game.factories.status_effect_factory import create_status_effect
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



def test_shattered_fury_buffs_ally_that_breaks_freeze(monkeypatch):

    abyssal = create_monster("drake_abyssal")
    ally = create_monster("drake_igneous")
    target = create_monster("drake_igneous")

    abyssal.resonance = 4
    update_resonance_kit(abyssal)

    freeze = create_status_effect(
        effect_id="freeze",
        duration=1,
        source=abyssal
    )

    target.apply_status_effect(freeze)

    ally.action_gauge = 0

    # Evitamos otros procs aleatorios como Cinderblood
    monkeypatch.setattr(
        random,
        "random",
        lambda: 0.99
    )

    skill = ally.get_skill(1)

    skill.execute(
        ally,
        [target]
    )

    buff_ids = [
        buff.effect_id
        for buff in ally.buffs
    ]

    assert "attack_up" in buff_ids
    assert "crit_rate_up" in buff_ids

    assert ally.action_gauge == pytest.approx(0.15)



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



def test_estimate_damage_ignores_damage_handler():

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

    assert damage_with_burn == pytest.approx(
        damage_without_burn
    )



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
