import pytest

import game.combat.balance_analyzer as balance_module

from game.combat.balance_analyzer import (
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
        verbose=True
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
