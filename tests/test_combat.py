import random
import pytest

from game.factories.monster_factory import create_monster
from game.factories.status_effect_factory import create_status_effect
from game.systems.resonance import update_resonance_kit
from game.combat.combat import (
    battle,
    begin_turn,
    end_turn,
    choose_skill,
    choose_enemy_target,
    estimate_damage,
    sees_kill
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