import pytest

import game.combat.balance_analyzer as balance_module

from game.combat.balance_analyzer import (
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
        ascended=False
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
                    "shield_absorbed": 250
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
                    "shield_absorbed": 0
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
        ascended=False
    ):

        received["level"] = level
        received["ascended"] = ascended

        return {
            "team_a_win_rate": 50,
            "team_b_win_rate": 50,
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
                    "shield_absorbed": 0
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
                    "shield_absorbed": 0
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
        ascended=False
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
                        "shield_absorbed": 0
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
                        "shield_absorbed": 0
                    }
                ]
            }

        return {
            "team_a_win_rate": 45,
            "team_b_win_rate": 55,
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
                    "shield_absorbed": 0
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
                    "shield_absorbed": 0
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
        "average_turns"
    ] == pytest.approx(14)

    assert matchup[
        "average_team_remaining_hp_percent"
    ] == pytest.approx(45)

    assert matchup[
        "total_damage"
    ] == pytest.approx(1300)

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
