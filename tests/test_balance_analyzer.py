import pytest

import game.combat.balance_analyzer as balance_module

from game.combat.balance_analyzer import (
    analyze_drake_roster_balance,
    analyze_team_matchup_balance,
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
