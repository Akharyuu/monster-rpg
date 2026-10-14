import pytest

import game.combat.balance_analyzer as balance_module

from game.combat.balance_analyzer import (
    analyze_drake_roster_balance,
    analyze_team_matchup_balance,
    analyze_void_buff_sensitivity,
    analyze_void_diagnostics,
    analyze_void_null_rend_ab,
    analyze_team_swap_balance,
    analyze_unit_balance,
    get_default_balance_benchmarks
)


# =========================================================
#                  BALANCE ANALYZER TESTS
# =========================================================

def test_default_benchmarks_use_same_rarity():

    benchmarks = (
        get_default_balance_benchmarks(
            "drake_storm"
        )
    )

    assert "drake_igneous" in benchmarks
    assert "drake_abyssal" in benchmarks

    assert "drake_storm" not in benchmarks
    assert "piñata" not in benchmarks



def test_analyze_unit_balance_aggregates_matchups(
    monkeypatch
):

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        runs,
        verbose=True,
        level=1,
        ascended=False,
        max_turns=200,
        attribute_targeting=True,
        neutral_core_attributes=False,
        neutral_all_attributes=False
    ):

        opponent_id = team_b_ids[0]

        if opponent_id == "drake_igneous":

            win_rate = 60
            turns = 10
            remaining_hp = 30
            damage = 1000

        else:

            win_rate = 40
            turns = 20
            remaining_hp = 10
            damage = 2000

        return {
            "team_a_win_rate": win_rate,
            "team_b_win_rate": 100 - win_rate,
            "draw_rate": 0,
            "average_turns": turns,
            "minimum_turns": turns,
            "maximum_turns": turns,
            "team_a_average_remaining_hp": 100,
            "team_b_average_remaining_hp": 100,
            "team_a_average_remaining_hp_percent":
                remaining_hp,
            "team_b_average_remaining_hp_percent":
                20,
            "team_a_telemetry": [
                {
                    "slot": 0,
                    "monster_id": team_a_ids[0],
                    "direct_damage": damage,
                    "dot_damage": 100,
                    "healing": 200,
                    "shield_generated": 300,
                    "shield_absorbed": 250,
                    "turns_denied": 2
                }
            ],
            "team_b_telemetry": [
                {
                    "slot": 0,
                    "monster_id": opponent_id,
                    "direct_damage": 0,
                    "dot_damage": 0,
                    "healing": 0,
                    "shield_generated": 0,
                    "shield_absorbed": 0,
                    "turns_denied": 0
                }
            ]
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    report = analyze_unit_balance(
        "drake_storm",
        runs=100,
        benchmark_ids=[
            "drake_igneous",
            "drake_abyssal"
        ],
        verbose=False
    )

    assert len(
        report["matchups"]
    ) == 2

    assert report["overall"][
        "average_win_rate"
    ] == pytest.approx(50)

    assert report["overall"][
        "average_turns"
    ] == pytest.approx(15)

    assert report["overall"][
        "average_remaining_hp_percent"
    ] == pytest.approx(20)

    assert report["overall"][
        "average_total_damage"
    ] == pytest.approx(1600)

    assert report["overall"][
        "average_draw_rate"
    ] == pytest.approx(0)

    assert report["level"] == 50
    assert report["ascended"] is True



def test_analyze_requires_manual_benchmarks_when_none_exist():

    with pytest.raises(ValueError):

        analyze_unit_balance(
            "griffon_igneous",
            runs=10,
            verbose=False
        )



def test_analyze_rejects_non_positive_runs():

    with pytest.raises(ValueError):

        analyze_unit_balance(
            "drake_storm",
            runs=0,
            verbose=False
        )



def test_analyze_passes_requested_level_to_simulator(
    monkeypatch
):

    received = {}

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        runs,
        verbose=True,
        level=1,
        ascended=False,
        max_turns=200,
        attribute_targeting=True,
        neutral_core_attributes=False,
        neutral_all_attributes=False
    ):

        received["level"] = level
        received["ascended"] = ascended

        return {
            "team_a_win_rate": 50,
            "team_b_win_rate": 50,
            "draw_rate": 0,
            "average_turns": 10,
            "minimum_turns": 10,
            "maximum_turns": 10,
            "team_a_average_remaining_hp": 100,
            "team_b_average_remaining_hp": 100,
            "team_a_average_remaining_hp_percent": 25,
            "team_b_average_remaining_hp_percent": 25,
            "team_a_telemetry": [
                {
                    "slot": 0,
                    "monster_id": team_a_ids[0],
                    "direct_damage": 1000,
                    "dot_damage": 0,
                    "healing": 0,
                    "shield_generated": 0,
                    "shield_absorbed": 0,
                    "turns_denied": 0
                }
            ],
            "team_b_telemetry": [
                {
                    "slot": 0,
                    "monster_id": team_b_ids[0],
                    "direct_damage": 1000,
                    "dot_damage": 0,
                    "healing": 0,
                    "shield_generated": 0,
                    "shield_absorbed": 0,
                    "turns_denied": 0
                }
            ]
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    analyze_unit_balance(
        "drake_storm",
        runs=10,
        benchmark_ids=[
            "drake_igneous"
        ],
        level=40,
        ascended=False,
        verbose=False
    )

    assert received["level"] == 40
    assert received["ascended"] is False






def test_analyze_unit_balance_can_neutralize_attributes(
    monkeypatch
):

    received = []

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        runs,
        verbose=True,
        level=1,
        ascended=False,
        max_turns=200,
        attribute_targeting=True,
        neutral_core_attributes=False,
        neutral_all_attributes=False
    ):

        received.append(
            neutral_all_attributes
        )

        entry_a = {
            "slot": 0,
            "monster_id": team_a_ids[0],
            "direct_damage": 0,
            "dot_damage": 0,
            "healing": 0,
            "shield_generated": 0,
            "shield_absorbed": 0,
            "turns_denied": 0
        }

        entry_b = {
            "slot": 0,
            "monster_id": team_b_ids[0],
            "direct_damage": 0,
            "dot_damage": 0,
            "healing": 0,
            "shield_generated": 0,
            "shield_absorbed": 0,
            "turns_denied": 0
        }

        return {
            "team_a_win_rate": 50,
            "team_b_win_rate": 50,
            "draw_rate": 0,
            "average_turns": 10,
            "minimum_turns": 10,
            "maximum_turns": 10,
            "team_a_average_remaining_hp": 100,
            "team_b_average_remaining_hp": 100,
            "team_a_average_remaining_hp_percent": 25,
            "team_b_average_remaining_hp_percent": 25,
            "team_a_telemetry": [entry_a],
            "team_b_telemetry": [entry_b]
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    report = analyze_unit_balance(
        "drake_storm",
        runs=1,
        benchmark_ids=[
            "drake_igneous"
        ],
        neutral_attributes=True,
        verbose=False
    )

    assert received == [True]
    assert report["neutral_attributes"] is True
# =========================================================
#               TEAM SWAP ANALYZER TESTS
# =========================================================

def test_team_swap_averages_both_sides(
    monkeypatch
):

    calls = []

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        runs,
        verbose=True,
        level=1,
        ascended=False,
        max_turns=200,
        attribute_targeting=True,
        neutral_core_attributes=False
    ):

        calls.append(
            (
                list(team_a_ids),
                list(team_b_ids)
            )
        )

        candidate_is_team_a = (
            team_a_ids[0]
            == "drake_storm"
        )

        if candidate_is_team_a:

            return {
                "team_a_win_rate": 70,
                "team_b_win_rate": 30,
                "draw_rate": 0,
                "average_turns": 12,
                "minimum_turns": 10,
                "maximum_turns": 14,
                "team_a_average_remaining_hp": 100,
                "team_b_average_remaining_hp": 80,
                "team_a_average_remaining_hp_percent": 40,
                "team_b_average_remaining_hp_percent": 20,
                "team_a_telemetry": [
                    {
                        "slot": 0,
                        "monster_id": "drake_storm",
                        "direct_damage": 1200,
                        "dot_damage": 100,
                        "healing": 50,
                        "shield_generated": 0,
                        "shield_absorbed": 0,
                    "turns_denied": 0
                    }
                ],
                "team_b_telemetry": [
                    {
                        "slot": 0,
                        "monster_id": "drake_igneous",
                        "direct_damage": 900,
                        "dot_damage": 0,
                        "healing": 0,
                        "shield_generated": 0,
                        "shield_absorbed": 0,
                    "turns_denied": 0
                    }
                ]
            }

        return {
            "team_a_win_rate": 45,
            "team_b_win_rate": 55,
            "draw_rate": 0,
            "average_turns": 16,
            "minimum_turns": 14,
            "maximum_turns": 18,
            "team_a_average_remaining_hp": 90,
            "team_b_average_remaining_hp": 120,
            "team_a_average_remaining_hp_percent": 30,
            "team_b_average_remaining_hp_percent": 50,
            "team_a_telemetry": [
                {
                    "slot": 0,
                    "monster_id": "drake_igneous",
                    "direct_damage": 950,
                    "dot_damage": 0,
                    "healing": 0,
                    "shield_generated": 0,
                    "shield_absorbed": 0,
                    "turns_denied": 0
                }
            ],
            "team_b_telemetry": [
                {
                    "slot": 0,
                    "monster_id": "drake_storm",
                    "direct_damage": 1000,
                    "dot_damage": 300,
                    "healing": 150,
                    "shield_generated": 0,
                    "shield_absorbed": 0,
                    "turns_denied": 0
                }
            ]
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    report = analyze_team_swap_balance(
        "drake_storm",
        runs=100,
        benchmark_ids=[
            "drake_igneous"
        ],
        core_team_ids=[
            "dryad_storm",
            "griffon_igneous"
        ],
        verbose=False
    )

    matchup = report["matchups"][0]

    assert matchup[
        "win_rate_as_team_a"
    ] == pytest.approx(70)

    assert matchup[
        "win_rate_as_team_b"
    ] == pytest.approx(55)

    assert matchup[
        "combined_win_rate"
    ] == pytest.approx(62.5)

    assert matchup[
        "draw_rate"
    ] == pytest.approx(0)

    assert matchup[
        "average_turns"
    ] == pytest.approx(14)

    assert matchup[
        "average_team_remaining_hp_percent"
    ] == pytest.approx(45)

    assert matchup[
        "total_damage"
    ] == pytest.approx(1300)

    assert matchup[
        "benchmark_total_damage"
    ] == pytest.approx(925)

    assert matchup[
        "benchmark_dot_damage"
    ] == pytest.approx(0)

    assert matchup[
        "turns_denied"
    ] == pytest.approx(0)

    assert matchup[
        "benchmark_turns_denied"
    ] == pytest.approx(0)

    assert len(calls) == 2

    assert calls[0][0] == [
        "drake_storm",
        "dryad_storm",
        "griffon_igneous"
    ]

    assert calls[1][1] == [
        "drake_storm",
        "dryad_storm",
        "griffon_igneous"
    ]



def test_team_swap_rejects_unknown_core_monster():

    with pytest.raises(ValueError):

        analyze_team_swap_balance(
            "drake_storm",
            runs=10,
            benchmark_ids=[
                "drake_igneous"
            ],
            core_team_ids=[
                "not_a_monster"
            ],
            verbose=False
        )



def test_team_swap_uses_three_neutral_cores_by_default(
    monkeypatch
):

    calls = []

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        runs,
        verbose=True,
        level=1,
        ascended=False,
        max_turns=200,
        attribute_targeting=True,
        neutral_core_attributes=False
    ):

        calls.append(
            (
                list(team_a_ids),
                list(team_b_ids)
            )
        )

        team_a_candidate = (
            team_a_ids[0]
            == "drake_storm"
        )

        team_a_entry = {
            "slot": 0,
            "monster_id": team_a_ids[0],
            "direct_damage": 1000,
            "dot_damage": 0,
            "healing": 0,
            "shield_generated": 0,
            "shield_absorbed": 0,
            "turns_denied": 0
        }

        team_b_entry = {
            "slot": 0,
            "monster_id": team_b_ids[0],
            "direct_damage": 1000,
            "dot_damage": 0,
            "healing": 0,
            "shield_generated": 0,
            "shield_absorbed": 0,
            "turns_denied": 0
        }

        return {
            "team_a_win_rate":
                60 if team_a_candidate else 40,
            "team_b_win_rate":
                40 if team_a_candidate else 60,
            "draw_rate": 0,
            "average_turns": 10,
            "team_a_average_remaining_hp_percent": 25,
            "team_b_average_remaining_hp_percent": 25,
            "team_a_telemetry": [
                team_a_entry
            ],
            "team_b_telemetry": [
                team_b_entry
            ]
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    report = analyze_team_swap_balance(
        "drake_storm",
        runs=10,
        benchmark_ids=[
            "drake_igneous"
        ],
        verbose=False
    )

    assert len(
        report["core_team_sets"]
    ) == 3

    assert len(
        report["matchups"][0][
            "core_results"
        ]
    ) == 3

    assert len(calls) == 6

    used_cores = {
        tuple(call[0][1:])
        for call in calls[::2]
    }

    assert used_cores == {
        (
            "thornet_igneous",
            "thornet_abyssal"
        ),
        (
            "thornet_abyssal",
            "thornet_storm"
        ),
        (
            "thornet_storm",
            "thornet_igneous"
        )
    }



def test_team_swap_disables_attribute_targeting_by_default(
    monkeypatch
):

    received = []

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        runs,
        verbose=True,
        level=1,
        ascended=False,
        max_turns=200,
        attribute_targeting=True,
        neutral_core_attributes=False
    ):

        received.append(
            attribute_targeting
        )

        entry_a = {
            "slot": 0,
            "monster_id": team_a_ids[0],
            "direct_damage": 0,
            "dot_damage": 0,
            "healing": 0,
            "shield_generated": 0,
            "shield_absorbed": 0,
            "turns_denied": 0
        }

        entry_b = {
            "slot": 0,
            "monster_id": team_b_ids[0],
            "direct_damage": 0,
            "dot_damage": 0,
            "healing": 0,
            "shield_generated": 0,
            "shield_absorbed": 0,
            "turns_denied": 0
        }

        return {
            "team_a_win_rate": 50,
            "team_b_win_rate": 50,
            "draw_rate": 0,
            "average_turns": 10,
            "team_a_average_remaining_hp_percent": 25,
            "team_b_average_remaining_hp_percent": 25,
            "team_a_telemetry": [entry_a],
            "team_b_telemetry": [entry_b]
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    analyze_team_swap_balance(
        "drake_storm",
        runs=1,
        benchmark_ids=[
            "drake_igneous"
        ],
        core_team_ids=[
            "thornet_igneous",
            "thornet_abyssal"
        ],
        verbose=False
    )

    assert received == [
        False,
        False
    ]



def test_team_swap_neutralizes_core_attributes_by_default(
    monkeypatch
):

    received = []

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        runs,
        verbose=True,
        level=1,
        ascended=False,
        max_turns=200,
        attribute_targeting=True,
        neutral_core_attributes=False
    ):

        received.append(
            neutral_core_attributes
        )

        entry_a = {
            "slot": 0,
            "monster_id": team_a_ids[0],
            "direct_damage": 0,
            "dot_damage": 0,
            "healing": 0,
            "shield_generated": 0,
            "shield_absorbed": 0,
            "turns_denied": 0
        }

        entry_b = {
            "slot": 0,
            "monster_id": team_b_ids[0],
            "direct_damage": 0,
            "dot_damage": 0,
            "healing": 0,
            "shield_generated": 0,
            "shield_absorbed": 0,
            "turns_denied": 0
        }

        return {
            "team_a_win_rate": 50,
            "team_b_win_rate": 50,
            "draw_rate": 0,
            "average_turns": 10,
            "team_a_average_remaining_hp_percent": 25,
            "team_b_average_remaining_hp_percent": 25,
            "team_a_telemetry": [entry_a],
            "team_b_telemetry": [entry_b]
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    analyze_team_swap_balance(
        "drake_storm",
        runs=1,
        benchmark_ids=[
            "drake_igneous"
        ],
        core_team_ids=[
            "thornet_igneous",
            "thornet_abyssal"
        ],
        verbose=False
    )

    assert received == [
        True,
        True
    ]



def test_simulate_battle_draws_at_turn_limit():

    from game.combat.combat import simulate_battle
    from game.factories.monster_factory import create_monster

    team_a = [
        create_monster(
            "dryad_storm"
        )
    ]

    team_b = [
        create_monster(
            "dryad_storm"
        )
    ]

    result = simulate_battle(
        team_a,
        team_b,
        max_turns=1
    )

    assert result["outcome"] == "draw"
    assert result["turns"] == 1



def test_team_swap_can_use_independent_primary_resonances(
    monkeypatch
):

    received = []

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        runs,
        verbose=True,
        level=1,
        ascended=False,
        max_turns=200,
        attribute_targeting=True,
        neutral_core_attributes=False,
        team_a_primary_resonance=None,
        team_b_primary_resonance=None
    ):

        received.append(
            (
                team_a_primary_resonance,
                team_b_primary_resonance
            )
        )

        entry_a = {
            "slot": 0,
            "monster_id": team_a_ids[0],
            "direct_damage": 0,
            "dot_damage": 0,
            "healing": 0,
            "shield_generated": 0,
            "shield_absorbed": 0,
            "turns_denied": 0
        }

        entry_b = {
            "slot": 0,
            "monster_id": team_b_ids[0],
            "direct_damage": 0,
            "dot_damage": 0,
            "healing": 0,
            "shield_generated": 0,
            "shield_absorbed": 0,
            "turns_denied": 0
        }

        return {
            "team_a_win_rate": 50,
            "team_b_win_rate": 50,
            "draw_rate": 0,
            "average_turns": 10,
            "team_a_average_remaining_hp_percent": 25,
            "team_b_average_remaining_hp_percent": 25,
            "team_a_telemetry": [entry_a],
            "team_b_telemetry": [entry_b]
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    report = analyze_team_swap_balance(
        "drake_storm",
        runs=1,
        benchmark_ids=[
            "drake_igneous"
        ],
        core_team_ids=[
            "thornet_igneous",
            "thornet_abyssal"
        ],
        candidate_resonance=5,
        benchmark_resonance=4,
        verbose=False
    )

    assert received == [
        (5, 4),
        (4, 5)
    ]

    assert report[
        "candidate_resonance"
    ] == 5

    assert report[
        "benchmark_resonance"
    ] == 4


def test_team_matchup_balance_averages_both_sides(
    monkeypatch
):

    calls = []

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        runs,
        verbose=True,
        level=1,
        ascended=False,
        max_turns=200,
        attribute_targeting=True,
        neutral_core_attributes=False,
        neutral_all_attributes=False,
        primary_resonance=0,
        team_a_primary_resonance=None,
        team_b_primary_resonance=None,
        team_a_resonances=None,
        team_b_resonances=None
    ):

        calls.append(
            (
                list(team_a_ids),
                list(team_b_ids)
            )
        )

        first_order = (
            team_a_ids[1]
            == "drake_storm"
        )

        if first_order:
            return {
                "team_a_win_rate": 40,
                "team_b_win_rate": 60,
                "draw_rate": 0,
                "average_turns": 10,
                "team_a_average_remaining_hp_percent": 15,
                "team_b_average_remaining_hp_percent": 25
            }

        return {
            "team_a_win_rate": 55,
            "team_b_win_rate": 45,
            "draw_rate": 0,
            "average_turns": 12,
            "team_a_average_remaining_hp_percent": 22,
            "team_b_average_remaining_hp_percent": 18
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    report = analyze_team_matchup_balance(
        [
            "drake_igneous",
            "drake_storm"
        ],
        [
            "drake_igneous",
            "drake_abyssal"
        ],
        runs=10,
        team_a_resonances=[5, 5],
        team_b_resonances=[5, 5],
        verbose=False
    )

    assert calls == [
        (
            [
                "drake_igneous",
                "drake_storm"
            ],
            [
                "drake_igneous",
                "drake_abyssal"
            ]
        ),
        (
            [
                "drake_igneous",
                "drake_abyssal"
            ],
            [
                "drake_igneous",
                "drake_storm"
            ]
        )
    ]

    assert report["team_a_win_rate"] == pytest.approx(
        42.5
    )

    assert report["team_b_win_rate"] == pytest.approx(
        57.5
    )


def test_drake_roster_balance_builds_symmetric_pair_matrix(
    monkeypatch
):

    calls = []

    def fake_team_swap_balance(
        monster_id,
        runs=500,
        benchmark_ids=None,
        core_team_ids=None,
        core_team_sets=None,
        level=50,
        ascended=True,
        max_turns=200,
        attribute_targeting=False,
        neutral_core_attributes=True,
        resonance=0,
        candidate_resonance=None,
        benchmark_resonance=None,
        verbose=True
    ):

        benchmark_id = benchmark_ids[0]

        calls.append(
            (
                monster_id,
                benchmark_id,
                resonance
            )
        )

        return {
            "matchups": [
                {
                    "combined_win_rate": 60.0,
                    "draw_rate": 5.0
                }
            ]
        }

    monkeypatch.setattr(
        balance_module,
        "analyze_team_swap_balance",
        fake_team_swap_balance
    )

    report = analyze_drake_roster_balance(
        runs=10,
        resonances=(0,),
        verbose=False
    )

    resonance_report = report[
        "resonance_reports"
    ][0]

    matrix = resonance_report[
        "matrix"
    ]

    assert len(calls) == 10

    assert matrix[
        "drake_igneous"
    ][
        "drake_abyssal"
    ] == pytest.approx(
        60.0
    )

    assert matrix[
        "drake_abyssal"
    ][
        "drake_igneous"
    ] == pytest.approx(
        35.0
    )

    assert matrix[
        "drake_igneous"
    ][
        "drake_igneous"
    ] is None



def test_drake_roster_balance_rejects_invalid_resonance():

    with pytest.raises(ValueError):

        analyze_drake_roster_balance(
            resonances=(6,),
            verbose=False
        )


# =========================================================
#                 VOID DIAGNOSTIC TESTS
# =========================================================

def test_void_diagnostics_averages_both_sides(
    monkeypatch
):

    calls = []

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        **kwargs
    ):

        calls.append(
            (
                list(team_a_ids),
                list(team_b_ids)
            )
        )

        void_is_team_a = (
            "drake_void" in team_a_ids
        )

        void_entry = {
            "slot": 0,
            "monster_id": "drake_void",
            "direct_damage": (
                1000
                if void_is_team_a
                else 3000
            ),
            "healing": 200,
            "null_rend_damage": 400,
            "dismantle_damage": 500,
            "null_rend_uses": 1,
            "dismantle_uses": 2,
            "buffs_removed": (
                2
                if void_is_team_a
                else 4
            ),
            "strip_events": 1,
            "veil_blocks": 1,
            "bottomless_hunger_activations": 1,
            "action_gauge_from_bottomless_hunger": 0.16,
            "voidborn_activations": 0.5,
            "oblivions_applied": 1,
            "defense_breaks_applied": 2
        }

        filler_entry = {
            key: 0
            for key in void_entry
            if key not in (
                "slot",
                "monster_id"
            )
        }

        filler_entry.update(
            {
                "slot": 0,
                "monster_id": "drake_igneous"
            }
        )

        if void_is_team_a:

            team_a_telemetry = [
                void_entry
            ]

            team_b_telemetry = [
                filler_entry
            ]

            team_a_win_rate = 40
            team_b_win_rate = 60

        else:

            team_a_telemetry = [
                filler_entry
            ]

            team_b_telemetry = [
                void_entry
            ]

            team_a_win_rate = 55
            team_b_win_rate = 45

        return {
            "team_a_win_rate":
                team_a_win_rate,
            "team_b_win_rate":
                team_b_win_rate,
            "draw_rate": 0,
            "average_turns": 10,
            "team_a_telemetry":
                team_a_telemetry,
            "team_b_telemetry":
                team_b_telemetry
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    report = analyze_void_diagnostics(
        runs=10,
        scenarios=[
            {
                "name": "Test",
                "void_team": [
                    "drake_void"
                ],
                "benchmark_team": [
                    "drake_igneous"
                ]
            }
        ],
        verbose=False
    )

    scenario = report[
        "scenarios"
    ][0]

    metrics = scenario[
        "void_metrics"
    ]

    assert len(calls) == 2

    assert scenario[
        "void_win_rate"
    ] == pytest.approx(
        42.5
    )

    assert metrics[
        "direct_damage"
    ] == pytest.approx(
        2000
    )

    assert metrics[
        "buffs_removed"
    ] == pytest.approx(
        3
    )


def test_void_diagnostics_requires_void_team():

    with pytest.raises(ValueError):

        analyze_void_diagnostics(
            scenarios=[
                {
                    "name": "Invalid",
                    "void_team": [
                        "drake_igneous"
                    ],
                    "benchmark_team": [
                        "drake_storm"
                    ]
                }
            ],
            verbose=False
        )


def test_void_diagnostics_forwards_controlled_initial_buffs(
    monkeypatch
):

    calls = []

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        **kwargs
    ):

        calls.append(
            {
                "team_a_ids": list(team_a_ids),
                "team_b_ids": list(team_b_ids),
                "team_a_initial_buffs":
                    kwargs.get(
                        "team_a_initial_buffs"
                    ),
                "team_b_initial_buffs":
                    kwargs.get(
                        "team_b_initial_buffs"
                    )
            }
        )

        void_is_team_a = (
            "drake_void" in team_a_ids
        )

        void_entry = {
            "slot": 0,
            "monster_id": "drake_void",
            "direct_damage": 0,
            "healing": 0,
            "null_rend_damage": 0,
            "dismantle_damage": 0,
            "null_rend_uses": 0,
            "dismantle_uses": 0,
            "buffs_removed": 0,
            "strip_events": 0,
            "veil_blocks": 0,
            "bottomless_hunger_activations": 0,
            "action_gauge_from_bottomless_hunger": 0,
            "voidborn_activations": 0,
            "oblivions_applied": 0,
            "defense_breaks_applied": 0
        }

        filler_entry = dict(
            void_entry
        )

        filler_entry[
            "monster_id"
        ] = "drake_igneous"

        return {
            "team_a_win_rate": 50,
            "team_b_win_rate": 50,
            "draw_rate": 0,
            "average_turns": 10,
            "team_a_telemetry": (
                [void_entry]
                if void_is_team_a
                else [filler_entry]
            ),
            "team_b_telemetry": (
                [filler_entry]
                if void_is_team_a
                else [void_entry]
            )
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    void_buffs = [
        [
            {
                "effect_id": "attack_up",
                "turns": 3
            }
        ]
    ]

    benchmark_buffs = [
        [
            {
                "effect_id": "speed_up",
                "turns": 3
            }
        ]
    ]

    analyze_void_diagnostics(
        runs=10,
        scenarios=[
            {
                "name": "Controlled",
                "void_team": [
                    "drake_void"
                ],
                "benchmark_team": [
                    "drake_igneous"
                ],
                "void_team_initial_buffs":
                    void_buffs,
                "benchmark_team_initial_buffs":
                    benchmark_buffs
            }
        ],
        verbose=False
    )

    assert (
        calls[0][
            "team_a_initial_buffs"
        ]
        == void_buffs
    )

    assert (
        calls[0][
            "team_b_initial_buffs"
        ]
        == benchmark_buffs
    )

    assert (
        calls[1][
            "team_a_initial_buffs"
        ]
        == benchmark_buffs
    )

    assert (
        calls[1][
            "team_b_initial_buffs"
        ]
        == void_buffs
    )


# =========================================================
#             VOID BUFF SENSITIVITY TESTS
# =========================================================

def test_void_buff_sensitivity_builds_six_buff_levels(
    monkeypatch
):

    captured_scenarios = []

    def fake_void_diagnostics(
        runs=1000,
        resonance=5,
        scenarios=None,
        level=50,
        ascended=True,
        max_turns=200,
        attribute_targeting=False,
        neutral_all_attributes=False,
        verbose=True
    ):

        captured_scenarios.extend(
            scenarios
        )

        scenario_reports = []

        for index, scenario in enumerate(
            scenarios
        ):

            scenario_reports.append(
                {
                    "name": scenario["name"],
                    "void_win_rate":
                        25 + index * 10,
                    "benchmark_win_rate":
                        75 - index * 10,
                    "draw_rate": 0,
                    "average_turns": 10,
                    "void_metrics": {
                        "direct_damage": 1000,
                        "healing": 100,
                        "null_rend_damage": 200,
                        "dismantle_damage": 600,
                        "null_rend_uses": 0.5,
                        "dismantle_uses": 1.0,
                        "buffs_removed": index * 2,
                        "strip_events": index,
                        "veil_blocks": 0,
                        "bottomless_hunger_activations":
                            index,
                        "action_gauge_from_bottomless_hunger":
                            index * 0.08,
                        "voidborn_activations":
                            index * 0.25,
                        "oblivions_applied": 0.25,
                        "defense_breaks_applied": 1
                    }
                }
            )

        return {
            "scenarios":
                scenario_reports
        }

    monkeypatch.setattr(
        balance_module,
        "analyze_void_diagnostics",
        fake_void_diagnostics
    )

    report = analyze_void_buff_sensitivity(
        runs=10,
        verbose=False
    )

    assert len(
        captured_scenarios
    ) == 6

    assert [
        result["buff_count"]
        for result in report["results"]
    ] == [
        0,
        1,
        2,
        3,
        4,
        5
    ]

    assert (
        len(
            captured_scenarios[5][
                "benchmark_team_initial_buffs"
            ][0]
        )
        == 5
    )


def test_void_buff_sensitivity_calculates_null_rend_contribution(
    monkeypatch
):

    def fake_void_diagnostics(
        **kwargs
    ):

        scenario_reports = []

        for scenario in kwargs[
            "scenarios"
        ]:

            scenario_reports.append(
                {
                    "name": scenario["name"],
                    "void_win_rate": 50,
                    "benchmark_win_rate": 50,
                    "draw_rate": 0,
                    "average_turns": 10,
                    "void_metrics": {
                        "direct_damage": 2000,
                        "healing": 0,
                        "null_rend_damage": 500,
                        "dismantle_damage": 1000,
                        "null_rend_uses": 0.5,
                        "dismantle_uses": 1,
                        "buffs_removed": 2,
                        "strip_events": 1,
                        "veil_blocks": 0,
                        "bottomless_hunger_activations": 1,
                        "action_gauge_from_bottomless_hunger": 0.16,
                        "voidborn_activations": 0.25,
                        "oblivions_applied": 0.2,
                        "defense_breaks_applied": 1
                    }
                }
            )

        return {
            "scenarios":
                scenario_reports
        }

    monkeypatch.setattr(
        balance_module,
        "analyze_void_diagnostics",
        fake_void_diagnostics
    )

    report = analyze_void_buff_sensitivity(
        runs=10,
        verbose=False
    )

    result = report[
        "results"
    ][0]

    assert result[
        "null_rend_damage_per_use"
    ] == pytest.approx(
        1000
    )

    assert result[
        "null_rend_damage_share"
    ] == pytest.approx(
        25
    )

    assert result[
        "oblivions_per_null_rend"
    ] == pytest.approx(
        0.4
    )


# =========================================================
#               NULL REND SEEDED A/B TESTS
# =========================================================

def test_void_null_rend_ab_compares_original_and_buffed(
    monkeypatch
):

    calls = []

    def fake_simulate_battles(
        team_a_ids,
        team_b_ids,
        **kwargs
    ):

        calls.append(
            (
                list(team_a_ids),
                list(team_b_ids)
            )
        )

        void_is_team_a = (
            "drake_void" in team_a_ids
        )

        void_entry = {
            "slot": 0,
            "monster_id": "drake_void",
            "direct_damage": 2000,
            "healing": 0,
            "null_rend_damage": 600,
            "dismantle_damage": 1200,
            "null_rend_uses": 0.5,
            "dismantle_uses": 1,
            "buffs_removed": 0,
            "strip_events": 0,
            "veil_blocks": 0,
            "bottomless_hunger_activations": 0,
            "action_gauge_from_bottomless_hunger": 0,
            "voidborn_activations": 0,
            "oblivions_applied": 0.25,
            "defense_breaks_applied": 1
        }

        filler = dict(
            void_entry
        )

        filler[
            "monster_id"
        ] = "drake_igneous"

        return {
            "team_a_win_rate": (
                55
                if void_is_team_a
                else 45
            ),
            "team_b_win_rate": (
                45
                if void_is_team_a
                else 55
            ),
            "draw_rate": 0,
            "average_turns": 10,
            "team_a_telemetry": (
                [void_entry]
                if void_is_team_a
                else [filler]
            ),
            "team_b_telemetry": (
                [filler]
                if void_is_team_a
                else [void_entry]
            )
        }

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    report = analyze_void_null_rend_ab(
        runs=10,
        verbose=False
    )

    assert len(
        report["results"]
    ) == 4

    assert len(calls) == 16

    for result in report[
        "results"
    ]:

        assert (
            result["original"][
                "null_rend_damage_per_use"
            ]
            == pytest.approx(1200)
        )

        assert (
            result["buffed"][
                "null_rend_damage_per_use"
            ]
            == pytest.approx(1200)
        )


def test_void_null_rend_ab_restores_skill_data(
    monkeypatch
):

    original_multiplier = (
        balance_module.SKILL_DATA[
            "null_rend"
        ]["multiplier"]
    )

    original_hit_multipliers = list(
        balance_module.SKILL_DATA[
            "null_rend_annihilation"
        ]["hit_multipliers"]
    )

    def fake_simulate_battles(
        *args,
        **kwargs
    ):

        raise RuntimeError(
            "forced failure"
        )

    monkeypatch.setattr(
        balance_module,
        "simulate_battles",
        fake_simulate_battles
    )

    with pytest.raises(RuntimeError):

        analyze_void_null_rend_ab(
            runs=1,
            verbose=False
        )

    assert (
        balance_module.SKILL_DATA[
            "null_rend"
        ]["multiplier"]
        == pytest.approx(
            original_multiplier
        )
    )

    assert (
        balance_module.SKILL_DATA[
            "null_rend_annihilation"
        ]["hit_multipliers"]
        == original_hit_multipliers
    )


def test_void_buff_sensitivity_can_use_neutral_benchmark_buffs(
    monkeypatch
):

    captured_scenarios = []

    def fake_void_diagnostics(
        **kwargs
    ):

        captured_scenarios.extend(
            kwargs["scenarios"]
        )

        scenario_reports = []

        for scenario in kwargs[
            "scenarios"
        ]:

            scenario_reports.append(
                {
                    "name": scenario["name"],
                    "void_win_rate": 50,
                    "benchmark_win_rate": 50,
                    "draw_rate": 0,
                    "average_turns": 10,
                    "void_metrics": {
                        "direct_damage": 1000,
                        "healing": 0,
                        "null_rend_damage": 200,
                        "dismantle_damage": 600,
                        "null_rend_uses": 0.5,
                        "dismantle_uses": 1,
                        "buffs_removed": 0,
                        "strip_events": 0,
                        "veil_blocks": 0,
                        "bottomless_hunger_activations": 0,
                        "action_gauge_from_bottomless_hunger": 0,
                        "voidborn_activations": 0,
                        "oblivions_applied": 0.2,
                        "defense_breaks_applied": 1
                    }
                }
            )

        return {
            "scenarios":
                scenario_reports
        }

    monkeypatch.setattr(
        balance_module,
        "analyze_void_diagnostics",
        fake_void_diagnostics
    )

    report = analyze_void_buff_sensitivity(
        runs=10,
        neutral_buffs=True,
        verbose=False
    )

    assert report[
        "neutral_buffs"
    ] is True

    five_buff_scenario = (
        captured_scenarios[5]
    )

    first_monster_buffs = (
        five_buff_scenario[
            "benchmark_team_initial_buffs"
        ][0]
    )

    assert len(
        first_monster_buffs
    ) == 5

    assert all(
        buff[
            "benchmark_neutral"
        ] is True
        for buff in first_monster_buffs
    )
