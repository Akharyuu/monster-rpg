import random

from ..combat.combat import simulate_battles
from ..data.monster_data import MONSTER_DATA
from ..data.skill_data import SKILL_DATA
from ..data.stat_growth_data import (
    ASCENDED_STAT_MULTIPLIER,
    LEVEL_STAT_MULTIPLIER
)


# =========================================================
#                   BALANCE ANALYZER
# =========================================================

BALANCE_EXCLUDED_MONSTERS = {
    "goblin_igneous",
    "golem_storm",
    "piñata"
}


def get_default_balance_benchmarks(monster_id):

    if monster_id not in MONSTER_DATA:
        raise ValueError(
            f"Unknown monster_id: {monster_id}"
        )

    monster_rarity = MONSTER_DATA[
        monster_id
    ]["rarity"]

    benchmark_ids = []

    for candidate_id, data in MONSTER_DATA.items():

        if candidate_id == monster_id:
            continue

        if candidate_id in BALANCE_EXCLUDED_MONSTERS:
            continue

        if data["rarity"] != monster_rarity:
            continue

        benchmark_ids.append(
            candidate_id
        )

    return benchmark_ids



def analyze_unit_balance(
    monster_id,
    runs=500,
    benchmark_ids=None,
    level=50,
    ascended=True,
    max_turns=200,
    neutral_attributes=False,
    resonance=0,
    verbose=True
):

    if monster_id not in MONSTER_DATA:
        raise ValueError(
            f"Unknown monster_id: {monster_id}"
        )

    if runs <= 0:
        raise ValueError(
            "runs must be greater than 0"
        )

    valid_levels = (
        ASCENDED_STAT_MULTIPLIER
        if ascended
        else LEVEL_STAT_MULTIPLIER
    )

    if level not in valid_levels:
        state_name = (
            "ascended"
            if ascended
            else "non-ascended"
        )

        raise ValueError(
            f"Level {level} is not valid for "
            f"a {state_name} monster."
        )

    if benchmark_ids is None:
        benchmark_ids = (
            get_default_balance_benchmarks(
                monster_id
            )
        )

    if not benchmark_ids:
        raise ValueError(
            f"No balance benchmarks available "
            f"for {monster_id}. "
            f"Pass benchmark_ids manually."
        )

    for benchmark_id in benchmark_ids:

        if benchmark_id not in MONSTER_DATA:
            raise ValueError(
                f"Unknown benchmark monster_id: "
                f"{benchmark_id}"
            )

        if benchmark_id == monster_id:
            raise ValueError(
                "A monster cannot be used as its "
                "own balance benchmark."
            )

    monster_data = MONSTER_DATA[
        monster_id
    ]

    matchups = []

    total_win_rate = 0
    total_draw_rate = 0
    total_turns = 0
    total_remaining_hp_percent = 0

    total_direct_damage = 0
    total_dot_damage = 0
    total_healing = 0
    total_shield_generated = 0
    total_shield_absorbed = 0
    total_turns_denied = 0

    for benchmark_id in benchmark_ids:

        simulation_kwargs = {
            "runs": runs,
            "verbose": False,
            "level": level,
            "ascended": ascended,
            "max_turns": max_turns,
            "neutral_all_attributes":
                neutral_attributes
        }

        if resonance > 0:
            simulation_kwargs[
                "primary_resonance"
            ] = resonance

        simulation = simulate_battles(
            [monster_id],
            [benchmark_id],
            **simulation_kwargs
        )

        unit_telemetry = (
            simulation["team_a_telemetry"][0]
        )

        matchup = {
            "opponent_id": benchmark_id,
            "opponent_name": MONSTER_DATA[
                benchmark_id
            ]["name"],
            "win_rate": simulation[
                "team_a_win_rate"
            ],
            "average_turns": simulation[
                "average_turns"
            ],
            "draw_rate": simulation[
                "draw_rate"
            ],
            "average_remaining_hp_percent":
                simulation[
                    "team_a_average_remaining_hp_percent"
                ],
            "direct_damage": unit_telemetry[
                "direct_damage"
            ],
            "dot_damage": unit_telemetry[
                "dot_damage"
            ],
            "total_damage": (
                unit_telemetry["direct_damage"]
                + unit_telemetry["dot_damage"]
            ),
            "healing": unit_telemetry[
                "healing"
            ],
            "shield_generated": unit_telemetry[
                "shield_generated"
            ],
            "shield_absorbed": unit_telemetry[
                "shield_absorbed"
            ],
            "turns_denied": unit_telemetry[
                "turns_denied"
            ]
        }

        matchups.append(
            matchup
        )

        total_win_rate += matchup[
            "win_rate"
        ]

        total_draw_rate += matchup[
            "draw_rate"
        ]

        total_turns += matchup[
            "average_turns"
        ]

        total_remaining_hp_percent += matchup[
            "average_remaining_hp_percent"
        ]

        total_direct_damage += matchup[
            "direct_damage"
        ]

        total_dot_damage += matchup[
            "dot_damage"
        ]

        total_healing += matchup[
            "healing"
        ]

        total_shield_generated += matchup[
            "shield_generated"
        ]

        total_shield_absorbed += matchup[
            "shield_absorbed"
        ]

        total_turns_denied += matchup[
            "turns_denied"
        ]

    matchup_count = len(matchups)

    overall = {
        "average_win_rate": (
            total_win_rate / matchup_count
        ),
        "average_draw_rate": (
            total_draw_rate / matchup_count
        ),
        "average_turns": (
            total_turns / matchup_count
        ),
        "average_remaining_hp_percent": (
            total_remaining_hp_percent
            / matchup_count
        ),
        "average_direct_damage": (
            total_direct_damage / matchup_count
        ),
        "average_dot_damage": (
            total_dot_damage / matchup_count
        ),
        "average_total_damage": (
            (
                total_direct_damage
                + total_dot_damage
            )
            / matchup_count
        ),
        "average_healing": (
            total_healing / matchup_count
        ),
        "average_shield_generated": (
            total_shield_generated
            / matchup_count
        ),
        "average_shield_absorbed": (
            total_shield_absorbed
            / matchup_count
        ),
        "average_turns_denied": (
            total_turns_denied
            / matchup_count
        )
    }

    report = {
        "monster_id": monster_id,
        "monster_name": monster_data["name"],
        "rarity": monster_data["rarity"],
        "runs_per_matchup": runs,
        "level": level,
        "ascended": ascended,
        "max_turns": max_turns,
        "neutral_attributes": neutral_attributes,
        "resonance": resonance,
        "benchmark_ids": list(
            benchmark_ids
        ),
        "matchups": matchups,
        "overall": overall
    }

    if verbose:
        print_balance_report(
            report
        )

    return report



def print_balance_report(report):

    print()
    print(
        "========================================"
    )
    print(
        "            UNIT BALANCE REPORT"
    )
    print(
        "========================================"
    )

    print(
        f"Monster: {report['monster_id']}"
    )

    print(
        f"Rarity: {report['rarity']}★"
    )

    print(
        f"Runs per matchup: "
        f"{report['runs_per_matchup']}"
    )

    print(
        f"Level: {report['level']}"
    )

    print(
        f"Ascended: {report['ascended']}"
    )

    print(
        "Attributes: "
        + (
            "neutral"
            if report["neutral_attributes"]
            else "normal"
        )
    )

    print(
        f"Resonance: R{report['resonance']}"
    )

    for matchup in report["matchups"]:

        print()
        print(
            f"vs {matchup['opponent_id']}"
        )

        print(
            f"  Win rate: "
            f"{matchup['win_rate']:.1f}%"
        )

        print(
            f"  Draw rate: "
            f"{matchup['draw_rate']:.1f}%"
        )

        print(
            f"  Remaining HP: "
            f"{matchup['average_remaining_hp_percent']:.1f}%"
        )

        print(
            f"  Average turns: "
            f"{matchup['average_turns']:.2f}"
        )

        print(
            f"  Damage: "
            f"{matchup['total_damage']:.1f}"
        )

        print(
            f"  Healing: "
            f"{matchup['healing']:.1f}"
        )

        print(
            f"  Shield generated: "
            f"{matchup['shield_generated']:.1f}"
        )

        print(
            f"  Shield absorbed: "
            f"{matchup['shield_absorbed']:.1f}"
        )

        print(
            f"  Enemy turns denied: "
            f"{matchup['turns_denied']:.2f}"
        )

    overall = report["overall"]

    print()
    print(
        "--------------- OVERALL ----------------"
    )

    print(
        f"Average win rate: "
        f"{overall['average_win_rate']:.1f}%"
    )

    print(
        f"Average draw rate: "
        f"{overall['average_draw_rate']:.1f}%"
    )

    print(
        f"Average remaining HP: "
        f"{overall['average_remaining_hp_percent']:.1f}%"
    )

    print(
        f"Average turns: "
        f"{overall['average_turns']:.2f}"
    )

    print(
        f"Average damage: "
        f"{overall['average_total_damage']:.1f}"
    )

    print(
        f"Average healing: "
        f"{overall['average_healing']:.1f}"
    )

    print(
        f"Average shield generated: "
        f"{overall['average_shield_generated']:.1f}"
    )

    print(
        f"Average shield absorbed: "
        f"{overall['average_shield_absorbed']:.1f}"
    )

    print(
        f"Average enemy turns denied: "
        f"{overall['average_turns_denied']:.2f}"
    )

    print(
        "========================================"
    )



# =========================================================
#                 TEAM SWAP BALANCE ANALYZER
# =========================================================

DEFAULT_NEUTRAL_CORE_SETS = [
    [
        "thornet_igneous",
        "thornet_abyssal"
    ],
    [
        "thornet_abyssal",
        "thornet_storm"
    ],
    [
        "thornet_storm",
        "thornet_igneous"
    ]
]


def _average_values(values):

    return sum(values) / len(values)



def _average_metric(entries, metric):

    return _average_values(
        [
            entry[metric]
            for entry in entries
        ]
    )



def analyze_team_swap_balance(
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

    if candidate_resonance is None:
        candidate_resonance = resonance

    if benchmark_resonance is None:
        benchmark_resonance = resonance

    if monster_id not in MONSTER_DATA:
        raise ValueError(
            f"Unknown monster_id: {monster_id}"
        )

    if runs <= 0:
        raise ValueError(
            "runs must be greater than 0"
        )

    valid_levels = (
        ASCENDED_STAT_MULTIPLIER
        if ascended
        else LEVEL_STAT_MULTIPLIER
    )

    if level not in valid_levels:
        state_name = (
            "ascended"
            if ascended
            else "non-ascended"
        )

        raise ValueError(
            f"Level {level} is not valid for "
            f"a {state_name} monster."
        )

    if benchmark_ids is None:
        benchmark_ids = (
            get_default_balance_benchmarks(
                monster_id
            )
        )

    if not benchmark_ids:
        raise ValueError(
            f"No balance benchmarks available "
            f"for {monster_id}. "
            f"Pass benchmark_ids manually."
        )

    if (
        core_team_ids is not None
        and core_team_sets is not None
    ):
        raise ValueError(
            "Pass either core_team_ids or "
            "core_team_sets, not both."
        )

    if core_team_ids is not None:
        core_team_sets = [
            list(core_team_ids)
        ]

    elif core_team_sets is None:
        core_team_sets = [
            list(core)
            for core in DEFAULT_NEUTRAL_CORE_SETS
        ]

    else:
        core_team_sets = [
            list(core)
            for core in core_team_sets
        ]

    if not core_team_sets:
        raise ValueError(
            "At least one core team is required."
        )

    for core_team in core_team_sets:

        if not core_team:
            raise ValueError(
                "Core teams cannot be empty."
            )

        for core_id in core_team:

            if core_id not in MONSTER_DATA:
                raise ValueError(
                    f"Unknown core team monster_id: "
                    f"{core_id}"
                )

    for benchmark_id in benchmark_ids:

        if benchmark_id not in MONSTER_DATA:
            raise ValueError(
                f"Unknown benchmark monster_id: "
                f"{benchmark_id}"
            )

        if benchmark_id == monster_id:
            raise ValueError(
                "A monster cannot be used as its "
                "own balance benchmark."
            )

    matchups = []

    for benchmark_id in benchmark_ids:

        core_results = []

        for core_team in core_team_sets:

            candidate_team = [
                monster_id
            ] + list(core_team)

            benchmark_team = [
                benchmark_id
            ] + list(core_team)

            simulation_kwargs = {
                "runs": runs,
                "verbose": False,
                "level": level,
                "ascended": ascended,
                "max_turns": max_turns,
                "attribute_targeting":
                    attribute_targeting,
                "neutral_core_attributes":
                    neutral_core_attributes
            }

            if (
                candidate_resonance
                == benchmark_resonance
            ):

                if candidate_resonance > 0:
                    simulation_kwargs[
                        "primary_resonance"
                    ] = candidate_resonance

                side_a = simulate_battles(
                    candidate_team,
                    benchmark_team,
                    **simulation_kwargs
                )

                side_b = simulate_battles(
                    benchmark_team,
                    candidate_team,
                    **simulation_kwargs
                )

            else:

                side_a = simulate_battles(
                    candidate_team,
                    benchmark_team,
                    team_a_primary_resonance=
                        candidate_resonance,
                    team_b_primary_resonance=
                        benchmark_resonance,
                    **simulation_kwargs
                )

                side_b = simulate_battles(
                    benchmark_team,
                    candidate_team,
                    team_a_primary_resonance=
                        benchmark_resonance,
                    team_b_primary_resonance=
                        candidate_resonance,
                    **simulation_kwargs
                )

            candidate_a = (
                side_a["team_a_telemetry"][0]
            )

            candidate_b = (
                side_b["team_b_telemetry"][0]
            )

            benchmark_a = (
                side_a["team_b_telemetry"][0]
            )

            benchmark_b = (
                side_b["team_a_telemetry"][0]
            )

            candidate_metrics = {}

            benchmark_metrics = {}

            for metric in (
                "direct_damage",
                "dot_damage",
                "healing",
                "shield_generated",
                "shield_absorbed",
                "turns_denied",
                "stuns_applied",
                "freezes_applied",
                "stun_turns_denied",
                "freeze_turns_denied",
                "freezes_broken_before_turn"
            ):

                candidate_metrics[metric] = (
                    candidate_a.get(metric, 0)
                    + candidate_b.get(metric, 0)
                ) / 2

                benchmark_metrics[metric] = (
                    benchmark_a.get(metric, 0)
                    + benchmark_b.get(metric, 0)
                ) / 2

            core_result = {
                "core_team_ids":
                    list(core_team),
                "win_rate_as_team_a":
                    side_a["team_a_win_rate"],
                "win_rate_as_team_b":
                    side_b["team_b_win_rate"],
                "combined_win_rate": (
                    side_a["team_a_win_rate"]
                    + side_b["team_b_win_rate"]
                ) / 2,
                "draw_rate": (
                    side_a["draw_rate"]
                    + side_b["draw_rate"]
                ) / 2,
                "average_turns": (
                    side_a["average_turns"]
                    + side_b["average_turns"]
                ) / 2,
                "average_team_remaining_hp_percent": (
                    side_a[
                        "team_a_average_remaining_hp_percent"
                    ]
                    + side_b[
                        "team_b_average_remaining_hp_percent"
                    ]
                ) / 2,
                "candidate_metrics":
                    candidate_metrics,
                "benchmark_metrics":
                    benchmark_metrics
            }

            core_results.append(
                core_result
            )

        candidate_direct_damage = (
            _average_values(
                [
                    core[
                        "candidate_metrics"
                    ]["direct_damage"]
                    for core in core_results
                ]
            )
        )

        candidate_dot_damage = (
            _average_values(
                [
                    core[
                        "candidate_metrics"
                    ]["dot_damage"]
                    for core in core_results
                ]
            )
        )

        benchmark_direct_damage = (
            _average_values(
                [
                    core[
                        "benchmark_metrics"
                    ]["direct_damage"]
                    for core in core_results
                ]
            )
        )

        benchmark_dot_damage = (
            _average_values(
                [
                    core[
                        "benchmark_metrics"
                    ]["dot_damage"]
                    for core in core_results
                ]
            )
        )

        matchup = {
            "opponent_id":
                benchmark_id,
            "opponent_name":
                MONSTER_DATA[
                    benchmark_id
                ]["name"],
            "core_results":
                core_results,
            "win_rate_as_team_a":
                _average_metric(
                    core_results,
                    "win_rate_as_team_a"
                ),
            "win_rate_as_team_b":
                _average_metric(
                    core_results,
                    "win_rate_as_team_b"
                ),
            "combined_win_rate":
                _average_metric(
                    core_results,
                    "combined_win_rate"
                ),
            "draw_rate":
                _average_metric(
                    core_results,
                    "draw_rate"
                ),
            "average_turns":
                _average_metric(
                    core_results,
                    "average_turns"
                ),
            "average_team_remaining_hp_percent":
                _average_metric(
                    core_results,
                    "average_team_remaining_hp_percent"
                ),
            "direct_damage":
                candidate_direct_damage,
            "dot_damage":
                candidate_dot_damage,
            "total_damage": (
                candidate_direct_damage
                + candidate_dot_damage
            ),
            "healing":
                _average_values(
                    [
                        core[
                            "candidate_metrics"
                        ]["healing"]
                        for core in core_results
                    ]
                ),
            "shield_generated":
                _average_values(
                    [
                        core[
                            "candidate_metrics"
                        ]["shield_generated"]
                        for core in core_results
                    ]
                ),
            "shield_absorbed":
                _average_values(
                    [
                        core[
                            "candidate_metrics"
                        ]["shield_absorbed"]
                        for core in core_results
                    ]
                ),
            "turns_denied":
                _average_values(
                    [
                        core[
                            "candidate_metrics"
                        ]["turns_denied"]
                        for core in core_results
                    ]
                ),
            "benchmark_direct_damage":
                benchmark_direct_damage,
            "benchmark_dot_damage":
                benchmark_dot_damage,
            "benchmark_total_damage": (
                benchmark_direct_damage
                + benchmark_dot_damage
            ),
            "benchmark_healing":
                _average_values(
                    [
                        core[
                            "benchmark_metrics"
                        ]["healing"]
                        for core in core_results
                    ]
                ),
            "benchmark_shield_generated":
                _average_values(
                    [
                        core[
                            "benchmark_metrics"
                        ]["shield_generated"]
                        for core in core_results
                    ]
                ),
            "benchmark_shield_absorbed":
                _average_values(
                    [
                        core[
                            "benchmark_metrics"
                        ]["shield_absorbed"]
                        for core in core_results
                    ]
                ),
            "benchmark_turns_denied":
                _average_values(
                    [
                        core[
                            "benchmark_metrics"
                        ]["turns_denied"]
                        for core in core_results
                    ]
                ),
            "stuns_applied":
                _average_values(
                    [
                        core[
                            "candidate_metrics"
                        ]["stuns_applied"]
                        for core in core_results
                    ]
                ),
            "freezes_applied":
                _average_values(
                    [
                        core[
                            "candidate_metrics"
                        ]["freezes_applied"]
                        for core in core_results
                    ]
                ),
            "stun_turns_denied":
                _average_values(
                    [
                        core[
                            "candidate_metrics"
                        ]["stun_turns_denied"]
                        for core in core_results
                    ]
                ),
            "freeze_turns_denied":
                _average_values(
                    [
                        core[
                            "candidate_metrics"
                        ]["freeze_turns_denied"]
                        for core in core_results
                    ]
                ),
            "freezes_broken_before_turn":
                _average_values(
                    [
                        core[
                            "candidate_metrics"
                        ]["freezes_broken_before_turn"]
                        for core in core_results
                    ]
                ),
            "benchmark_stuns_applied":
                _average_values(
                    [
                        core[
                            "benchmark_metrics"
                        ]["stuns_applied"]
                        for core in core_results
                    ]
                ),
            "benchmark_freezes_applied":
                _average_values(
                    [
                        core[
                            "benchmark_metrics"
                        ]["freezes_applied"]
                        for core in core_results
                    ]
                ),
            "benchmark_stun_turns_denied":
                _average_values(
                    [
                        core[
                            "benchmark_metrics"
                        ]["stun_turns_denied"]
                        for core in core_results
                    ]
                ),
            "benchmark_freeze_turns_denied":
                _average_values(
                    [
                        core[
                            "benchmark_metrics"
                        ]["freeze_turns_denied"]
                        for core in core_results
                    ]
                ),
            "benchmark_freezes_broken_before_turn":
                _average_values(
                    [
                        core[
                            "benchmark_metrics"
                        ]["freezes_broken_before_turn"]
                        for core in core_results
                    ]
                )
        }

        matchups.append(
            matchup
        )

    matchup_count = len(matchups)

    overall = {
        "average_win_rate":
            _average_metric(
                matchups,
                "combined_win_rate"
            ),
        "average_draw_rate":
            _average_metric(
                matchups,
                "draw_rate"
            ),
        "average_turns":
            _average_metric(
                matchups,
                "average_turns"
            ),
        "average_team_remaining_hp_percent":
            _average_metric(
                matchups,
                "average_team_remaining_hp_percent"
            ),
        "average_total_damage":
            _average_metric(
                matchups,
                "total_damage"
            ),
        "average_healing":
            _average_metric(
                matchups,
                "healing"
            ),
        "average_shield_generated":
            _average_metric(
                matchups,
                "shield_generated"
            ),
        "average_shield_absorbed":
            _average_metric(
                matchups,
                "shield_absorbed"
            ),
        "average_turns_denied":
            _average_metric(
                matchups,
                "turns_denied"
            )
    }

    report = {
        "monster_id":
            monster_id,
        "monster_name":
            MONSTER_DATA[
                monster_id
            ]["name"],
        "rarity":
            MONSTER_DATA[
                monster_id
            ]["rarity"],
        "runs_per_side":
            runs,
        "level":
            level,
        "ascended":
            ascended,
        "max_turns":
            max_turns,
        "attribute_targeting":
            attribute_targeting,
        "neutral_core_attributes":
            neutral_core_attributes,
        "candidate_resonance":
            candidate_resonance,
        "benchmark_resonance":
            benchmark_resonance,
        "core_team_sets":
            [
                list(core)
                for core in core_team_sets
            ],
        "benchmark_ids":
            list(benchmark_ids),
        "matchups":
            matchups,
        "overall":
            overall
    }

    if verbose:
        print_team_swap_report(
            report
        )

    return report



def print_team_swap_report(report):

    print()
    print(
        "========================================"
    )
    print(
        "          TEAM SWAP BALANCE REPORT"
    )
    print(
        "========================================"
    )

    print(
        f"Monster: {report['monster_id']}"
    )

    print(
        f"Rarity: {report['rarity']}★"
    )

    print(
        f"Runs per side/core: "
        f"{report['runs_per_side']}"
    )

    print(
        f"Level: {report['level']}"
    )

    print(
        f"Ascended: {report['ascended']}"
    )

    print(
        "Target AI: "
        + (
            "attribute-aware"
            if report["attribute_targeting"]
            else "neutral"
        )
    )

    print(
        "Core attributes: "
        + (
            "neutral"
            if report[
                "neutral_core_attributes"
            ]
            else "normal"
        )
    )

    print(
        "Resonance: "
        f"R{report['candidate_resonance']} "
        "vs "
        f"R{report['benchmark_resonance']}"
    )

    print(
        f"Neutral cores: "
        f"{len(report['core_team_sets'])}"
    )

    for index, core in enumerate(
        report["core_team_sets"],
        start=1
    ):

        print(
            f"  Core {index}: "
            + ", ".join(core)
        )

    for matchup in report["matchups"]:

        print()
        print(
            f"vs {matchup['opponent_id']}"
        )

        for index, core_result in enumerate(
            matchup["core_results"],
            start=1
        ):

            print(
                f"  Core {index} win rate: "
                f"{core_result['combined_win_rate']:.1f}% "
                f"(draws "
                f"{core_result['draw_rate']:.1f}%)"
            )

        print(
            f"  Average win rate: "
            f"{matchup['combined_win_rate']:.1f}%"
        )

        print(
            f"  Win rate as Team A: "
            f"{matchup['win_rate_as_team_a']:.1f}%"
        )

        print(
            f"  Win rate as Team B: "
            f"{matchup['win_rate_as_team_b']:.1f}%"
        )

        print(
            f"  Draw rate: "
            f"{matchup['draw_rate']:.1f}%"
        )

        print(
            f"  Team remaining HP: "
            f"{matchup['average_team_remaining_hp_percent']:.1f}%"
        )

        print(
            f"  Average turns: "
            f"{matchup['average_turns']:.2f}"
        )

        print(
            "  Contribution comparison:"
        )

        print(
            f"    Damage: "
            f"{report['monster_id']} "
            f"{matchup['total_damage']:.1f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_total_damage']:.1f}"
        )

        print(
            f"    DoT damage: "
            f"{report['monster_id']} "
            f"{matchup['dot_damage']:.1f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_dot_damage']:.1f}"
        )

        print(
            f"    Healing: "
            f"{report['monster_id']} "
            f"{matchup['healing']:.1f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_healing']:.1f}"
        )

        print(
            f"    Shield generated: "
            f"{report['monster_id']} "
            f"{matchup['shield_generated']:.1f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_shield_generated']:.1f}"
        )

        print(
            f"    Shield absorbed: "
            f"{report['monster_id']} "
            f"{matchup['shield_absorbed']:.1f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_shield_absorbed']:.1f}"
        )

        print(
            f"    Enemy turns denied: "
            f"{report['monster_id']} "
            f"{matchup['turns_denied']:.2f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_turns_denied']:.2f}"
        )

        print(
            f"    Stuns applied: "
            f"{report['monster_id']} "
            f"{matchup['stuns_applied']:.2f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_stuns_applied']:.2f}"
        )

        print(
            f"    Freezes applied: "
            f"{report['monster_id']} "
            f"{matchup['freezes_applied']:.2f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_freezes_applied']:.2f}"
        )

        print(
            f"    Stun turns denied: "
            f"{report['monster_id']} "
            f"{matchup['stun_turns_denied']:.2f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_stun_turns_denied']:.2f}"
        )

        print(
            f"    Freeze turns denied: "
            f"{report['monster_id']} "
            f"{matchup['freeze_turns_denied']:.2f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_freeze_turns_denied']:.2f}"
        )

        print(
            f"    Freezes broken before turn: "
            f"{report['monster_id']} "
            f"{matchup['freezes_broken_before_turn']:.2f} | "
            f"{matchup['opponent_id']} "
            f"{matchup['benchmark_freezes_broken_before_turn']:.2f}"
        )

    overall = report["overall"]

    print()
    print(
        "--------------- OVERALL ----------------"
    )

    print(
        f"Average win rate: "
        f"{overall['average_win_rate']:.1f}%"
    )

    print(
        f"Average draw rate: "
        f"{overall['average_draw_rate']:.1f}%"
    )

    print(
        f"Average team remaining HP: "
        f"{overall['average_team_remaining_hp_percent']:.1f}%"
    )

    print(
        f"Average turns: "
        f"{overall['average_turns']:.2f}"
    )

    print(
        f"Average unit damage: "
        f"{overall['average_total_damage']:.1f}"
    )

    print(
        f"Average unit healing: "
        f"{overall['average_healing']:.1f}"
    )

    print(
        f"Average unit shield generated: "
        f"{overall['average_shield_generated']:.1f}"
    )

    print(
        f"Average unit shield absorbed: "
        f"{overall['average_shield_absorbed']:.1f}"
    )

    print(
        f"Average unit enemy turns denied: "
        f"{overall['average_turns_denied']:.2f}"
    )

    print(
        "========================================"
    )



# =========================================================
#                DRAKE TRIANGLE ANALYZER
# =========================================================

DRAKE_TRIANGLE_IDS = [
    "drake_igneous",
    "drake_abyssal",
    "drake_storm"
]


def analyze_drake_triangle_balance(
    runs=500,
    core_team_sets=None,
    level=50,
    ascended=True,
    max_turns=200,
    attribute_targeting=False,
    neutral_core_attributes=True,
    resonance=0,
    verbose=True
):

    pairings = [
        (
            "drake_igneous",
            "drake_abyssal"
        ),
        (
            "drake_abyssal",
            "drake_storm"
        ),
        (
            "drake_storm",
            "drake_igneous"
        )
    ]

    pair_results = []

    for candidate_id, benchmark_id in pairings:

        report = analyze_team_swap_balance(
            candidate_id,
            runs=runs,
            benchmark_ids=[
                benchmark_id
            ],
            core_team_sets=core_team_sets,
            level=level,
            ascended=ascended,
            max_turns=max_turns,
            attribute_targeting=attribute_targeting,
            neutral_core_attributes=neutral_core_attributes,
            resonance=resonance,
            verbose=False
        )

        matchup = report["matchups"][0]

        pair_results.append(
            {
                "candidate_id":
                    candidate_id,
                "benchmark_id":
                    benchmark_id,
                "candidate_win_rate":
                    matchup[
                        "combined_win_rate"
                    ],
                "benchmark_win_rate": (
                    100
                    - matchup[
                        "combined_win_rate"
                    ]
                    - matchup[
                        "draw_rate"
                    ]
                ),
                "draw_rate":
                    matchup[
                        "draw_rate"
                    ],
                "candidate_damage":
                    matchup[
                        "total_damage"
                    ],
                "benchmark_damage":
                    matchup[
                        "benchmark_total_damage"
                    ],
                "candidate_turns_denied":
                    matchup[
                        "turns_denied"
                    ],
                "benchmark_turns_denied":
                    matchup[
                        "benchmark_turns_denied"
                    ],
                "candidate_stuns_applied":
                    matchup[
                        "stuns_applied"
                    ],
                "benchmark_stuns_applied":
                    matchup[
                        "benchmark_stuns_applied"
                    ],
                "candidate_freezes_applied":
                    matchup[
                        "freezes_applied"
                    ],
                "benchmark_freezes_applied":
                    matchup[
                        "benchmark_freezes_applied"
                    ],
                "candidate_stun_turns_denied":
                    matchup[
                        "stun_turns_denied"
                    ],
                "benchmark_stun_turns_denied":
                    matchup[
                        "benchmark_stun_turns_denied"
                    ],
                "candidate_freeze_turns_denied":
                    matchup[
                        "freeze_turns_denied"
                    ],
                "benchmark_freeze_turns_denied":
                    matchup[
                        "benchmark_freeze_turns_denied"
                    ],
                "candidate_freezes_broken_before_turn":
                    matchup[
                        "freezes_broken_before_turn"
                    ],
                "benchmark_freezes_broken_before_turn":
                    matchup[
                        "benchmark_freezes_broken_before_turn"
                    ],
                "core_results":
                    matchup[
                        "core_results"
                    ]
            }
        )

    report = {
        "runs_per_side_core":
            runs,
        "level":
            level,
        "ascended":
            ascended,
        "max_turns":
            max_turns,
        "attribute_targeting":
            attribute_targeting,
        "neutral_core_attributes":
            neutral_core_attributes,
        "resonance":
            resonance,
        "pair_results":
            pair_results
    }

    if verbose:
        print_drake_triangle_report(
            report
        )

    return report



def print_drake_triangle_report(report):

    print()
    print(
        "========================================"
    )
    print(
        "        DRAKE TRIANGLE BALANCE"
    )
    print(
        "========================================"
    )

    print(
        f"Runs per side/core: "
        f"{report['runs_per_side_core']}"
    )

    print(
        f"Level: {report['level']}"
    )

    print(
        f"Ascended: {report['ascended']}"
    )

    print(
        "Target AI: "
        + (
            "attribute-aware"
            if report["attribute_targeting"]
            else "neutral"
        )
    )

    print(
        "Core attributes: "
        + (
            "neutral"
            if report[
                "neutral_core_attributes"
            ]
            else "normal"
        )
    )

    print(
        f"Resonance: R{report['resonance']}"
    )

    for result in report["pair_results"]:

        print()
        print(
            f"{result['candidate_id']} "
            f"vs {result['benchmark_id']}"
        )

        print(
            f"  Win rate: "
            f"{result['candidate_win_rate']:.1f}% "
            f"| "
            f"{result['benchmark_win_rate']:.1f}%"
        )

        print(
            f"  Draw rate: "
            f"{result['draw_rate']:.1f}%"
        )

        print(
            f"  Damage: "
            f"{result['candidate_damage']:.1f} "
            f"| "
            f"{result['benchmark_damage']:.1f}"
        )

        print(
            f"  Enemy turns denied: "
            f"{result['candidate_turns_denied']:.2f} "
            f"| "
            f"{result['benchmark_turns_denied']:.2f}"
        )

        print(
            f"  Stuns applied: "
            f"{result['candidate_stuns_applied']:.2f} "
            f"| "
            f"{result['benchmark_stuns_applied']:.2f}"
        )

        print(
            f"  Freezes applied: "
            f"{result['candidate_freezes_applied']:.2f} "
            f"| "
            f"{result['benchmark_freezes_applied']:.2f}"
        )

        print(
            f"  Stun turns denied: "
            f"{result['candidate_stun_turns_denied']:.2f} "
            f"| "
            f"{result['benchmark_stun_turns_denied']:.2f}"
        )

        print(
            f"  Freeze turns denied: "
            f"{result['candidate_freeze_turns_denied']:.2f} "
            f"| "
            f"{result['benchmark_freeze_turns_denied']:.2f}"
        )

        print(
            f"  Freezes broken before turn: "
            f"{result['candidate_freezes_broken_before_turn']:.2f} "
            f"| "
            f"{result['benchmark_freezes_broken_before_turn']:.2f}"
        )

        for index, core in enumerate(
            result["core_results"],
            start=1
        ):

            print(
                f"    Core {index}: "
                f"{core['combined_win_rate']:.1f}% "
                f"(draws "
                f"{core['draw_rate']:.1f}%)"
            )

    print()
    print(
        "========================================"
    )


# =========================================================
#                DIRECT TEAM MATCHUP ANALYZER
# =========================================================

def analyze_team_matchup_balance(
    team_a_ids,
    team_b_ids,
    runs=500,
    team_a_resonances=None,
    team_b_resonances=None,
    level=50,
    ascended=True,
    max_turns=200,
    attribute_targeting=False,
    neutral_all_attributes=False,
    verbose=True
):

    side_a = simulate_battles(
        team_a_ids,
        team_b_ids,
        runs=runs,
        verbose=False,
        level=level,
        ascended=ascended,
        max_turns=max_turns,
        attribute_targeting=attribute_targeting,
        neutral_all_attributes=neutral_all_attributes,
        team_a_resonances=team_a_resonances,
        team_b_resonances=team_b_resonances
    )

    side_b = simulate_battles(
        team_b_ids,
        team_a_ids,
        runs=runs,
        verbose=False,
        level=level,
        ascended=ascended,
        max_turns=max_turns,
        attribute_targeting=attribute_targeting,
        neutral_all_attributes=neutral_all_attributes,
        team_a_resonances=team_b_resonances,
        team_b_resonances=team_a_resonances
    )

    team_a_win_rate = (
        side_a["team_a_win_rate"]
        + side_b["team_b_win_rate"]
    ) / 2

    team_b_win_rate = (
        side_a["team_b_win_rate"]
        + side_b["team_a_win_rate"]
    ) / 2

    draw_rate = (
        side_a["draw_rate"]
        + side_b["draw_rate"]
    ) / 2

    average_turns = (
        side_a["average_turns"]
        + side_b["average_turns"]
    ) / 2

    team_a_remaining_hp = (
        side_a[
            "team_a_average_remaining_hp_percent"
        ]
        + side_b[
            "team_b_average_remaining_hp_percent"
        ]
    ) / 2

    team_b_remaining_hp = (
        side_a[
            "team_b_average_remaining_hp_percent"
        ]
        + side_b[
            "team_a_average_remaining_hp_percent"
        ]
    ) / 2

    report = {
        "team_a_ids": list(team_a_ids),
        "team_b_ids": list(team_b_ids),
        "team_a_resonances": (
            list(team_a_resonances)
            if team_a_resonances is not None
            else None
        ),
        "team_b_resonances": (
            list(team_b_resonances)
            if team_b_resonances is not None
            else None
        ),
        "runs_per_side": runs,
        "level": level,
        "ascended": ascended,
        "attribute_targeting": attribute_targeting,
        "neutral_all_attributes": neutral_all_attributes,
        "team_a_win_rate": team_a_win_rate,
        "team_b_win_rate": team_b_win_rate,
        "draw_rate": draw_rate,
        "average_turns": average_turns,
        "team_a_average_remaining_hp_percent":
            team_a_remaining_hp,
        "team_b_average_remaining_hp_percent":
            team_b_remaining_hp
    }

    if verbose:
        print_team_matchup_report(
            report
        )

    return report



def print_team_matchup_report(report):

    print()
    print(
        "========================================"
    )
    print(
        "          TEAM MATCHUP REPORT"
    )
    print(
        "========================================"
    )

    print(
        "Team A: "
        + ", ".join(report["team_a_ids"])
    )

    print(
        "Team B: "
        + ", ".join(report["team_b_ids"])
    )

    if report["team_a_resonances"] is not None:
        print(
            "Team A Resonances: "
            + ", ".join(
                f"R{value}"
                for value in report[
                    "team_a_resonances"
                ]
            )
        )

    if report["team_b_resonances"] is not None:
        print(
            "Team B Resonances: "
            + ", ".join(
                f"R{value}"
                for value in report[
                    "team_b_resonances"
                ]
            )
        )

    print(
        f"Runs per side: "
        f"{report['runs_per_side']}"
    )

    print(
        f"Win rate: "
        f"{report['team_a_win_rate']:.1f}% "
        f"| "
        f"{report['team_b_win_rate']:.1f}%"
    )

    print(
        f"Draw rate: "
        f"{report['draw_rate']:.1f}%"
    )

    print(
        f"Average turns: "
        f"{report['average_turns']:.2f}"
    )

    print(
        f"Remaining HP: "
        f"{report['team_a_average_remaining_hp_percent']:.1f}% "
        f"| "
        f"{report['team_b_average_remaining_hp_percent']:.1f}%"
    )

    print(
        "========================================"
    )


# =========================================================
#                 FIVE DRAKE ROSTER BENCHMARK
# =========================================================

DRAKE_ROSTER_IDS = [
    "drake_igneous",
    "drake_abyssal",
    "drake_storm",
    "drake_aether",
    "drake_void"
]


DRAKE_ROSTER_LABELS = {
    "drake_igneous": "Igneous",
    "drake_abyssal": "Abyssal",
    "drake_storm": "Storm",
    "drake_aether": "Aether",
    "drake_void": "Void"
}



def analyze_drake_roster_balance(
    runs=300,
    resonances=(0, 5),
    core_team_sets=None,
    level=50,
    ascended=True,
    max_turns=200,
    attribute_targeting=False,
    neutral_core_attributes=True,
    verbose=True
):

    if not resonances:
        raise ValueError(
            "At least one resonance value is required."
        )

    for resonance in resonances:

        if resonance < 0 or resonance > 5:
            raise ValueError(
                "Resonance values must be between 0 and 5."
            )

    resonance_reports = []

    for resonance in resonances:

        matrix = {}

        for monster_id in DRAKE_ROSTER_IDS:
            matrix[monster_id] = {
                monster_id: None
            }

        pair_results = []

        for candidate_index in range(
            len(DRAKE_ROSTER_IDS)
        ):

            candidate_id = DRAKE_ROSTER_IDS[
                candidate_index
            ]

            for benchmark_index in range(
                candidate_index + 1,
                len(DRAKE_ROSTER_IDS)
            ):

                benchmark_id = DRAKE_ROSTER_IDS[
                    benchmark_index
                ]

                report = analyze_team_swap_balance(
                    candidate_id,
                    runs=runs,
                    benchmark_ids=[
                        benchmark_id
                    ],
                    core_team_sets=core_team_sets,
                    level=level,
                    ascended=ascended,
                    max_turns=max_turns,
                    attribute_targeting=attribute_targeting,
                    neutral_core_attributes=
                        neutral_core_attributes,
                    resonance=resonance,
                    verbose=False
                )

                matchup = report[
                    "matchups"
                ][0]

                candidate_win_rate = matchup[
                    "combined_win_rate"
                ]

                draw_rate = matchup[
                    "draw_rate"
                ]

                benchmark_win_rate = (
                    100
                    - candidate_win_rate
                    - draw_rate
                )

                matrix[candidate_id][
                    benchmark_id
                ] = candidate_win_rate

                matrix[benchmark_id][
                    candidate_id
                ] = benchmark_win_rate

                pair_results.append(
                    {
                        "candidate_id":
                            candidate_id,
                        "benchmark_id":
                            benchmark_id,
                        "candidate_win_rate":
                            candidate_win_rate,
                        "benchmark_win_rate":
                            benchmark_win_rate,
                        "draw_rate":
                            draw_rate
                    }
                )

        average_win_rates = {}

        for monster_id in DRAKE_ROSTER_IDS:

            values = [
                value
                for opponent_id, value
                in matrix[monster_id].items()
                if (
                    opponent_id != monster_id
                    and value is not None
                )
            ]

            average_win_rates[monster_id] = (
                _average_values(values)
            )

        resonance_reports.append(
            {
                "resonance": resonance,
                "matrix": matrix,
                "average_win_rates":
                    average_win_rates,
                "pair_results":
                    pair_results
            }
        )

    report = {
        "runs_per_side_core": runs,
        "level": level,
        "ascended": ascended,
        "max_turns": max_turns,
        "attribute_targeting":
            attribute_targeting,
        "neutral_core_attributes":
            neutral_core_attributes,
        "drake_ids":
            list(DRAKE_ROSTER_IDS),
        "resonance_reports":
            resonance_reports
    }

    if verbose:
        print_drake_roster_report(
            report
        )

    return report



def print_drake_roster_report(report):

    print()
    print(
        "=============================================================="
    )
    print(
        "                 FIVE DRAKE ROSTER BALANCE"
    )
    print(
        "=============================================================="
    )

    print(
        f"Runs per side/core: "
        f"{report['runs_per_side_core']}"
    )

    print(
        f"Level: {report['level']} "
        f"| Ascended: {report['ascended']}"
    )

    print(
        "Target AI: "
        + (
            "attribute-aware"
            if report["attribute_targeting"]
            else "neutral"
        )
    )

    print(
        "Core attributes: "
        + (
            "neutral"
            if report[
                "neutral_core_attributes"
            ]
            else "normal"
        )
    )

    labels = [
        DRAKE_ROSTER_LABELS[
            monster_id
        ]
        for monster_id in report[
            "drake_ids"
        ]
    ]

    for resonance_report in report[
        "resonance_reports"
    ]:

        print()
        print(
            f"-------------------------- "
            f"R{resonance_report['resonance']} "
            f"--------------------------"
        )

        header = (
            f"{'Drake':<10}"
            + "".join(
                f"{label:>10}"
                for label in labels
            )
            + f"{'AVG':>10}"
        )

        print(
            header
        )

        for monster_id in report[
            "drake_ids"
        ]:

            row = (
                f"{DRAKE_ROSTER_LABELS[monster_id]:<10}"
            )

            for opponent_id in report[
                "drake_ids"
            ]:

                value = resonance_report[
                    "matrix"
                ][monster_id].get(
                    opponent_id
                )

                if value is None:
                    cell = "--"
                else:
                    cell = f"{value:.1f}%"

                row += f"{cell:>10}"

            average = resonance_report[
                "average_win_rates"
            ][monster_id]

            row += f"{average:.1f}%".rjust(
                10
            )

            print(
                row
            )

    print()
    print(
        "Each cell is the row Drake's mirrored win rate "
        "against the column Drake."
    )

    print(
        "AVG is only a rough roster reference, not a role "
        "power ranking."
    )

    print(
        "=============================================================="
    )


# =========================================================
#                  VOID DRAKE DIAGNOSTICS
# =========================================================

DEFAULT_VOID_DIAGNOSTIC_SCENARIOS = [
    {
        "name": "Generic flex slot",
        "void_team": [
            "drake_igneous",
            "drake_storm",
            "drake_void"
        ],
        "benchmark_team": [
            "drake_igneous",
            "drake_storm",
            "drake_abyssal"
        ]
    },
    {
        "name": "Directly into Aether",
        "void_team": [
            "drake_igneous",
            "drake_abyssal",
            "drake_void"
        ],
        "benchmark_team": [
            "drake_igneous",
            "drake_abyssal",
            "drake_aether"
        ]
    },
    {
        "name": "Buff-heavy environment",
        "void_team": [
            "drake_storm",
            "drake_void",
            "drake_aether"
        ],
        "benchmark_team": [
            "drake_storm",
            "drake_igneous",
            "drake_aether"
        ]
    },
    {
        "name": "Control plus support",
        "void_team": [
            "drake_abyssal",
            "drake_void",
            "drake_aether"
        ],
        "benchmark_team": [
            "drake_abyssal",
            "drake_igneous",
            "drake_aether"
        ]
    },
    {
        "name": "Controlled buffs without Veil",
        "void_team": [
            "drake_storm",
            "drake_void",
            "drake_abyssal"
        ],
        "benchmark_team": [
            "drake_storm",
            "drake_igneous",
            "drake_abyssal"
        ],
        "void_team_initial_buffs": [
            [
                {
                    "effect_id": "attack_up",
                    "turns": 3
                },
                {
                    "effect_id": "defense_up",
                    "turns": 3
                },
                {
                    "effect_id": "speed_up",
                    "turns": 3
                }
            ],
            [
                {
                    "effect_id": "attack_up",
                    "turns": 3
                },
                {
                    "effect_id": "defense_up",
                    "turns": 3
                },
                {
                    "effect_id": "speed_up",
                    "turns": 3
                }
            ],
            [
                {
                    "effect_id": "attack_up",
                    "turns": 3
                },
                {
                    "effect_id": "defense_up",
                    "turns": 3
                },
                {
                    "effect_id": "speed_up",
                    "turns": 3
                }
            ]
        ],
        "benchmark_team_initial_buffs": [
            [
                {
                    "effect_id": "attack_up",
                    "turns": 3
                },
                {
                    "effect_id": "defense_up",
                    "turns": 3
                },
                {
                    "effect_id": "speed_up",
                    "turns": 3
                }
            ],
            [
                {
                    "effect_id": "attack_up",
                    "turns": 3
                },
                {
                    "effect_id": "defense_up",
                    "turns": 3
                },
                {
                    "effect_id": "speed_up",
                    "turns": 3
                }
            ],
            [
                {
                    "effect_id": "attack_up",
                    "turns": 3
                },
                {
                    "effect_id": "defense_up",
                    "turns": 3
                },
                {
                    "effect_id": "speed_up",
                    "turns": 3
                }
            ]
        ]
    }
]


VOID_DIAGNOSTIC_METRICS = (
    "direct_damage",
    "healing",
    "null_rend_damage",
    "dismantle_damage",
    "null_rend_uses",
    "dismantle_uses",
    "buffs_removed",
    "strip_events",
    "veil_blocks",
    "bottomless_hunger_activations",
    "action_gauge_from_bottomless_hunger",
    "voidborn_activations",
    "oblivions_applied",
    "defense_breaks_applied"
)



def _get_monster_telemetry(
    telemetry_entries,
    monster_id
):

    for entry in telemetry_entries:

        if entry["monster_id"] == monster_id:
            return entry

    raise ValueError(
        f"Telemetry entry not found for {monster_id}."
    )



def analyze_void_diagnostics(
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

    if resonance < 0 or resonance > 5:
        raise ValueError(
            "resonance must be between 0 and 5."
        )

    if scenarios is None:
        scenarios = DEFAULT_VOID_DIAGNOSTIC_SCENARIOS

    scenario_reports = []

    for scenario in scenarios:

        void_team = list(
            scenario["void_team"]
        )

        benchmark_team = list(
            scenario["benchmark_team"]
        )

        if "drake_void" not in void_team:
            raise ValueError(
                "Every Void diagnostic scenario must "
                "include drake_void in void_team."
            )

        void_resonances = [
            resonance
            for _ in void_team
        ]

        benchmark_resonances = [
            resonance
            for _ in benchmark_team
        ]

        side_a = simulate_battles(
            void_team,
            benchmark_team,
            runs=runs,
            verbose=False,
            level=level,
            ascended=ascended,
            max_turns=max_turns,
            attribute_targeting=attribute_targeting,
            neutral_all_attributes=
                neutral_all_attributes,
            team_a_resonances=
                void_resonances,
            team_b_resonances=
                benchmark_resonances,
            team_a_initial_buffs=
                scenario.get(
                    "void_team_initial_buffs"
                ),
            team_b_initial_buffs=
                scenario.get(
                    "benchmark_team_initial_buffs"
                )
        )

        side_b = simulate_battles(
            benchmark_team,
            void_team,
            runs=runs,
            verbose=False,
            level=level,
            ascended=ascended,
            max_turns=max_turns,
            attribute_targeting=attribute_targeting,
            neutral_all_attributes=
                neutral_all_attributes,
            team_a_resonances=
                benchmark_resonances,
            team_b_resonances=
                void_resonances,
            team_a_initial_buffs=
                scenario.get(
                    "benchmark_team_initial_buffs"
                ),
            team_b_initial_buffs=
                scenario.get(
                    "void_team_initial_buffs"
                )
        )

        void_telemetry_a = (
            _get_monster_telemetry(
                side_a["team_a_telemetry"],
                "drake_void"
            )
        )

        void_telemetry_b = (
            _get_monster_telemetry(
                side_b["team_b_telemetry"],
                "drake_void"
            )
        )

        void_metrics = {}

        for metric in VOID_DIAGNOSTIC_METRICS:

            void_metrics[metric] = (
                void_telemetry_a.get(
                    metric,
                    0
                )
                + void_telemetry_b.get(
                    metric,
                    0
                )
            ) / 2

        void_win_rate = (
            side_a["team_a_win_rate"]
            + side_b["team_b_win_rate"]
        ) / 2

        benchmark_win_rate = (
            side_a["team_b_win_rate"]
            + side_b["team_a_win_rate"]
        ) / 2

        draw_rate = (
            side_a["draw_rate"]
            + side_b["draw_rate"]
        ) / 2

        average_turns = (
            side_a["average_turns"]
            + side_b["average_turns"]
        ) / 2

        scenario_reports.append(
            {
                "name": scenario["name"],
                "void_team": void_team,
                "benchmark_team":
                    benchmark_team,
                "void_win_rate":
                    void_win_rate,
                "benchmark_win_rate":
                    benchmark_win_rate,
                "draw_rate":
                    draw_rate,
                "average_turns":
                    average_turns,
                "void_metrics":
                    void_metrics
            }
        )

    report = {
        "runs_per_side": runs,
        "resonance": resonance,
        "level": level,
        "ascended": ascended,
        "attribute_targeting":
            attribute_targeting,
        "neutral_all_attributes":
            neutral_all_attributes,
        "scenarios":
            scenario_reports
    }

    if verbose:
        print_void_diagnostics_report(
            report
        )

    return report



def print_void_diagnostics_report(report):

    print()
    print(
        "=============================================================="
    )
    print(
        "                    VOID DRAKE DIAGNOSTICS"
    )
    print(
        "=============================================================="
    )

    print(
        f"Runs per side: {report['runs_per_side']} "
        f"| Resonance: R{report['resonance']}"
    )

    print(
        f"Level: {report['level']} "
        f"| Ascended: {report['ascended']}"
    )

    for scenario in report["scenarios"]:

        metrics = scenario[
            "void_metrics"
        ]

        print()
        print(
            "--------------------------------------------------------------"
        )

        print(
            scenario["name"].upper()
        )

        print(
            "Void team: "
            + ", ".join(
                scenario["void_team"]
            )
        )

        print(
            "Benchmark: "
            + ", ".join(
                scenario["benchmark_team"]
            )
        )

        print(
            f"Win rate: "
            f"{scenario['void_win_rate']:.1f}% "
            f"| "
            f"{scenario['benchmark_win_rate']:.1f}% "
            f"(draws {scenario['draw_rate']:.1f}%)"
        )

        print(
            f"Average turns: "
            f"{scenario['average_turns']:.2f}"
        )

        print()
        print(
            "VOID OUTPUT PER BATTLE"
        )

        print(
            f"  Direct damage: "
            f"{metrics['direct_damage']:.1f}"
        )

        print(
            f"    Null Rend damage: "
            f"{metrics['null_rend_damage']:.1f} "
            f"| uses: "
            f"{metrics['null_rend_uses']:.2f}"
        )

        print(
            f"    Dismantle damage: "
            f"{metrics['dismantle_damage']:.1f} "
            f"| uses: "
            f"{metrics['dismantle_uses']:.2f}"
        )

        print(
            f"  Healing: "
            f"{metrics['healing']:.1f}"
        )

        print()
        print(
            "STRIP / TEMPO"
        )

        print(
            f"  Buffs removed: "
            f"{metrics['buffs_removed']:.2f}"
        )

        print(
            f"  Successful strip targets: "
            f"{metrics['strip_events']:.2f}"
        )

        print(
            f"  Veil blocks: "
            f"{metrics['veil_blocks']:.2f}"
        )

        print(
            f"  Bottomless Hunger activations: "
            f"{metrics['bottomless_hunger_activations']:.2f}"
        )

        print(
            f"  AG gained from strips: "
            f"{metrics['action_gauge_from_bottomless_hunger'] * 100:.1f}%"
        )

        print(
            f"  Voidborn activations: "
            f"{metrics['voidborn_activations']:.2f}"
        )

        print()
        print(
            "DEBUFF PRESSURE"
        )

        print(
            f"  Oblivions applied: "
            f"{metrics['oblivions_applied']:.2f}"
        )

        print(
            f"  Defense Breaks applied by Dismantle: "
            f"{metrics['defense_breaks_applied']:.2f}"
        )

    print()
    print(
        "=============================================================="
    )


# =========================================================
#              VOID BUFF SENSITIVITY BENCHMARK
# =========================================================

VOID_SENSITIVITY_BUFF_ORDER = [
    "attack_up",
    "defense_up",
    "speed_up",
    "crit_rate_up",
    "immunity"
]



def _build_team_initial_buffs(
    team_size,
    buff_count,
    turns=3
):

    selected_buffs = (
        VOID_SENSITIVITY_BUFF_ORDER[
            :buff_count
        ]
    )

    team_buffs = []

    for _ in range(team_size):

        monster_buffs = []

        for effect_id in selected_buffs:

            monster_buffs.append(
                {
                    "effect_id": effect_id,
                    "turns": turns
                }
            )

        team_buffs.append(
            monster_buffs
        )

    return team_buffs



def analyze_void_buff_sensitivity(
    runs=1000,
    resonance=5,
    level=50,
    ascended=True,
    max_turns=200,
    attribute_targeting=False,
    verbose=True
):

    void_team = [
        "drake_storm",
        "drake_void",
        "drake_abyssal"
    ]

    benchmark_team = [
        "drake_storm",
        "drake_igneous",
        "drake_abyssal"
    ]

    scenarios = []

    for buff_count in range(
        len(VOID_SENSITIVITY_BUFF_ORDER)
        + 1
    ):

        initial_buffs = (
            _build_team_initial_buffs(
                len(void_team),
                buff_count
            )
        )

        scenarios.append(
            {
                "name":
                    f"{buff_count} buffs per monster",
                "buff_count":
                    buff_count,
                "void_team":
                    list(void_team),
                "benchmark_team":
                    list(benchmark_team),
                "void_team_initial_buffs":
                    initial_buffs,
                "benchmark_team_initial_buffs":
                    _build_team_initial_buffs(
                        len(benchmark_team),
                        buff_count
                    )
            }
        )

    diagnostic_report = (
        analyze_void_diagnostics(
            runs=runs,
            resonance=resonance,
            scenarios=scenarios,
            level=level,
            ascended=ascended,
            max_turns=max_turns,
            attribute_targeting=
                attribute_targeting,
            verbose=False
        )
    )

    sensitivity_results = []

    for buff_count, scenario in enumerate(
        diagnostic_report["scenarios"]
    ):

        metrics = scenario[
            "void_metrics"
        ]

        null_rend_uses = metrics[
            "null_rend_uses"
        ]

        dismantle_uses = metrics[
            "dismantle_uses"
        ]

        direct_damage = metrics[
            "direct_damage"
        ]

        if null_rend_uses > 0:
            null_rend_damage_per_use = (
                metrics[
                    "null_rend_damage"
                ]
                / null_rend_uses
            )

            oblivions_per_null_rend = (
                metrics[
                    "oblivions_applied"
                ]
                / null_rend_uses
            )

        else:
            null_rend_damage_per_use = 0
            oblivions_per_null_rend = 0

        if dismantle_uses > 0:
            dismantle_damage_per_use = (
                metrics[
                    "dismantle_damage"
                ]
                / dismantle_uses
            )

            buffs_removed_per_dismantle = (
                metrics[
                    "buffs_removed"
                ]
                / dismantle_uses
            )

        else:
            dismantle_damage_per_use = 0
            buffs_removed_per_dismantle = 0

        if direct_damage > 0:
            null_rend_damage_share = (
                metrics[
                    "null_rend_damage"
                ]
                / direct_damage
                * 100
            )

        else:
            null_rend_damage_share = 0

        sensitivity_results.append(
            {
                "buff_count": buff_count,
                "void_win_rate":
                    scenario[
                        "void_win_rate"
                    ],
                "benchmark_win_rate":
                    scenario[
                        "benchmark_win_rate"
                    ],
                "draw_rate":
                    scenario[
                        "draw_rate"
                    ],
                "average_turns":
                    scenario[
                        "average_turns"
                    ],
                "direct_damage":
                    direct_damage,
                "healing":
                    metrics[
                        "healing"
                    ],
                "null_rend_uses":
                    null_rend_uses,
                "null_rend_damage":
                    metrics[
                        "null_rend_damage"
                    ],
                "null_rend_damage_per_use":
                    null_rend_damage_per_use,
                "null_rend_damage_share":
                    null_rend_damage_share,
                "oblivions_applied":
                    metrics[
                        "oblivions_applied"
                    ],
                "oblivions_per_null_rend":
                    oblivions_per_null_rend,
                "dismantle_uses":
                    dismantle_uses,
                "dismantle_damage":
                    metrics[
                        "dismantle_damage"
                    ],
                "dismantle_damage_per_use":
                    dismantle_damage_per_use,
                "buffs_removed":
                    metrics[
                        "buffs_removed"
                    ],
                "buffs_removed_per_dismantle":
                    buffs_removed_per_dismantle,
                "action_gauge_from_strips":
                    metrics[
                        "action_gauge_from_bottomless_hunger"
                    ],
                "voidborn_activations":
                    metrics[
                        "voidborn_activations"
                    ]
            }
        )

    report = {
        "runs_per_side": runs,
        "resonance": resonance,
        "level": level,
        "ascended": ascended,
        "void_team": void_team,
        "benchmark_team":
            benchmark_team,
        "results":
            sensitivity_results
    }

    if verbose:
        print_void_buff_sensitivity_report(
            report
        )

    return report



def print_void_buff_sensitivity_report(
    report
):

    print()
    print(
        "=============================================================="
    )
    print(
        "                 VOID BUFF SENSITIVITY"
    )
    print(
        "=============================================================="
    )

    print(
        f"Runs per side: "
        f"{report['runs_per_side']} "
        f"| Resonance: "
        f"R{report['resonance']}"
    )

    print(
        "Void team: "
        + ", ".join(
            report["void_team"]
        )
    )

    print(
        "Benchmark: "
        + ", ".join(
            report[
                "benchmark_team"
            ]
        )
    )

    print()
    print(
        "WIN RATE / STRIP CURVE"
    )

    print(
        f"{'Buffs':>5} "
        f"{'Void WR':>9} "
        f"{'Removed':>9} "
        f"{'AG':>8} "
        f"{'Voidborn':>9} "
        f"{'Healing':>10}"
    )

    for result in report[
        "results"
    ]:

        print(
            f"{result['buff_count']:>5} "
            f"{result['void_win_rate']:>8.1f}% "
            f"{result['buffs_removed']:>9.2f} "
            f"{result['action_gauge_from_strips'] * 100:>7.1f}% "
            f"{result['voidborn_activations']:>9.2f} "
            f"{result['healing']:>10.1f}"
        )

    print()
    print(
        "NULL REND CONTRIBUTION"
    )

    print(
        f"{'Buffs':>5} "
        f"{'Uses':>7} "
        f"{'Damage':>10} "
        f"{'Dmg/Use':>10} "
        f"{'Dmg Share':>10} "
        f"{'Obliv/Use':>10}"
    )

    for result in report[
        "results"
    ]:

        print(
            f"{result['buff_count']:>5} "
            f"{result['null_rend_uses']:>7.2f} "
            f"{result['null_rend_damage']:>10.1f} "
            f"{result['null_rend_damage_per_use']:>10.1f} "
            f"{result['null_rend_damage_share']:>9.1f}% "
            f"{result['oblivions_per_null_rend']:>10.2f}"
        )

    print()
    print(
        "DISMANTLE CONTRIBUTION"
    )

    print(
        f"{'Buffs':>5} "
        f"{'Uses':>7} "
        f"{'Damage':>10} "
        f"{'Dmg/Use':>10} "
        f"{'Buffs/Use':>10}"
    )

    for result in report[
        "results"
    ]:

        print(
            f"{result['buff_count']:>5} "
            f"{result['dismantle_uses']:>7.2f} "
            f"{result['dismantle_damage']:>10.1f} "
            f"{result['dismantle_damage_per_use']:>10.1f} "
            f"{result['buffs_removed_per_dismantle']:>10.2f}"
        )

    print()
    print(
        "=============================================================="
    )


# =========================================================
#               NULL REND SEEDED A/B BENCHMARK
# =========================================================

NULL_REND_VARIANTS = {
    "original": {
        "multiplier": 2.10,
        "second_hit_multiplier": 1.30
    },
    "buffed": {
        "multiplier": 2.25,
        "second_hit_multiplier": 1.35
    }
}



def _set_null_rend_variant(
    multiplier,
    second_hit_multiplier
):

    for skill_id in (
        "null_rend",
        "null_rend_obliterate",
        "null_rend_annihilation"
    ):

        SKILL_DATA[
            skill_id
        ]["multiplier"] = multiplier

    for skill_id in (
        "null_rend_obliterate",
        "null_rend_annihilation"
    ):

        SKILL_DATA[
            skill_id
        ]["hit_multipliers"] = [
            1.00,
            second_hit_multiplier
        ]



def _capture_null_rend_state():

    state = {}

    for skill_id in (
        "null_rend",
        "null_rend_obliterate",
        "null_rend_annihilation"
    ):

        skill_data = SKILL_DATA[
            skill_id
        ]

        state[skill_id] = {
            "multiplier":
                skill_data[
                    "multiplier"
                ],
            "hit_multipliers": (
                list(
                    skill_data[
                        "hit_multipliers"
                    ]
                )
                if skill_data.get(
                    "hit_multipliers"
                ) is not None
                else None
            )
        }

    return state



def _restore_null_rend_state(state):

    for skill_id, skill_state in state.items():

        SKILL_DATA[
            skill_id
        ]["multiplier"] = (
            skill_state[
                "multiplier"
            ]
        )

        hit_multipliers = skill_state[
            "hit_multipliers"
        ]

        if hit_multipliers is None:

            SKILL_DATA[
                skill_id
            ].pop(
                "hit_multipliers",
                None
            )

        else:

            SKILL_DATA[
                skill_id
            ]["hit_multipliers"] = list(
                hit_multipliers
            )



def _combine_void_seeded_sides(
    side_a,
    side_b
):

    void_telemetry_a = (
        _get_monster_telemetry(
            side_a[
                "team_a_telemetry"
            ],
            "drake_void"
        )
    )

    void_telemetry_b = (
        _get_monster_telemetry(
            side_b[
                "team_b_telemetry"
            ],
            "drake_void"
        )
    )

    metrics = {}

    for metric in VOID_DIAGNOSTIC_METRICS:

        metrics[metric] = (
            void_telemetry_a.get(
                metric,
                0
            )
            + void_telemetry_b.get(
                metric,
                0
            )
        ) / 2

    null_rend_uses = metrics[
        "null_rend_uses"
    ]

    if null_rend_uses > 0:

        null_rend_damage_per_use = (
            metrics[
                "null_rend_damage"
            ]
            / null_rend_uses
        )

        oblivions_per_use = (
            metrics[
                "oblivions_applied"
            ]
            / null_rend_uses
        )

    else:

        null_rend_damage_per_use = 0
        oblivions_per_use = 0

    return {
        "void_win_rate": (
            side_a[
                "team_a_win_rate"
            ]
            + side_b[
                "team_b_win_rate"
            ]
        ) / 2,
        "draw_rate": (
            side_a[
                "draw_rate"
            ]
            + side_b[
                "draw_rate"
            ]
        ) / 2,
        "null_rend_uses":
            null_rend_uses,
        "null_rend_damage":
            metrics[
                "null_rend_damage"
            ],
        "null_rend_damage_per_use":
            null_rend_damage_per_use,
        "oblivions_per_null_rend":
            oblivions_per_use
    }



def analyze_void_null_rend_ab(
    runs=5000,
    resonance=5,
    seed=20261013,
    level=50,
    ascended=True,
    max_turns=200,
    attribute_targeting=False,
    verbose=True
):

    void_team = [
        "drake_storm",
        "drake_void",
        "drake_abyssal"
    ]

    benchmark_team = [
        "drake_storm",
        "drake_igneous",
        "drake_abyssal"
    ]

    resonances = [
        resonance
        for _ in void_team
    ]

    original_state = (
        _capture_null_rend_state()
    )

    results = []

    try:

        for buff_count in range(4):

            initial_buffs = (
                _build_team_initial_buffs(
                    len(void_team),
                    buff_count
                )
            )

            variant_results = {}

            for (
                variant_name,
                variant_data
            ) in NULL_REND_VARIANTS.items():

                _set_null_rend_variant(
                    variant_data[
                        "multiplier"
                    ],
                    variant_data[
                        "second_hit_multiplier"
                    ]
                )

                side_a_seed = (
                    seed
                    + buff_count * 100
                )

                side_b_seed = (
                    side_a_seed
                    + 1
                )

                random.seed(
                    side_a_seed
                )

                side_a = simulate_battles(
                    void_team,
                    benchmark_team,
                    runs=runs,
                    verbose=False,
                    level=level,
                    ascended=ascended,
                    max_turns=max_turns,
                    attribute_targeting=
                        attribute_targeting,
                    team_a_resonances=
                        resonances,
                    team_b_resonances=
                        resonances,
                    team_a_initial_buffs=
                        initial_buffs,
                    team_b_initial_buffs=
                        _build_team_initial_buffs(
                            len(
                                benchmark_team
                            ),
                            buff_count
                        )
                )

                random.seed(
                    side_b_seed
                )

                side_b = simulate_battles(
                    benchmark_team,
                    void_team,
                    runs=runs,
                    verbose=False,
                    level=level,
                    ascended=ascended,
                    max_turns=max_turns,
                    attribute_targeting=
                        attribute_targeting,
                    team_a_resonances=
                        resonances,
                    team_b_resonances=
                        resonances,
                    team_a_initial_buffs=
                        _build_team_initial_buffs(
                            len(
                                benchmark_team
                            ),
                            buff_count
                        ),
                    team_b_initial_buffs=
                        initial_buffs
                )

                variant_results[
                    variant_name
                ] = (
                    _combine_void_seeded_sides(
                        side_a,
                        side_b
                    )
                )

            original = variant_results[
                "original"
            ]

            buffed = variant_results[
                "buffed"
            ]

            results.append(
                {
                    "buff_count":
                        buff_count,
                    "original":
                        original,
                    "buffed":
                        buffed,
                    "win_rate_delta": (
                        buffed[
                            "void_win_rate"
                        ]
                        - original[
                            "void_win_rate"
                        ]
                    ),
                    "damage_per_use_delta": (
                        buffed[
                            "null_rend_damage_per_use"
                        ]
                        - original[
                            "null_rend_damage_per_use"
                        ]
                    )
                }
            )

    finally:

        _restore_null_rend_state(
            original_state
        )

    report = {
        "runs_per_side": runs,
        "resonance": resonance,
        "seed": seed,
        "void_team": void_team,
        "benchmark_team":
            benchmark_team,
        "results": results
    }

    if verbose:
        print_void_null_rend_ab_report(
            report
        )

    return report



def print_void_null_rend_ab_report(
    report
):

    print()
    print(
        "=============================================================="
    )
    print(
        "                 NULL REND SEEDED A/B"
    )
    print(
        "=============================================================="
    )

    print(
        f"Runs per side: "
        f"{report['runs_per_side']} "
        f"| Resonance: "
        f"R{report['resonance']} "
        f"| Seed: "
        f"{report['seed']}"
    )

    print()
    print(
        "WIN RATE"
    )

    print(
        f"{'Buffs':>5} "
        f"{'Original':>10} "
        f"{'Buffed':>10} "
        f"{'Delta':>9}"
    )

    for result in report[
        "results"
    ]:

        print(
            f"{result['buff_count']:>5} "
            f"{result['original']['void_win_rate']:>9.1f}% "
            f"{result['buffed']['void_win_rate']:>9.1f}% "
            f"{result['win_rate_delta']:>+8.1f}"
        )

    print()
    print(
        "NULL REND OUTPUT"
    )

    print(
        f"{'Buffs':>5} "
        f"{'Old use':>8} "
        f"{'New use':>8} "
        f"{'Old dmg/use':>12} "
        f"{'New dmg/use':>12} "
        f"{'Delta':>10}"
    )

    for result in report[
        "results"
    ]:

        original = result[
            "original"
        ]

        buffed = result[
            "buffed"
        ]

        print(
            f"{result['buff_count']:>5} "
            f"{original['null_rend_uses']:>8.2f} "
            f"{buffed['null_rend_uses']:>8.2f} "
            f"{original['null_rend_damage_per_use']:>12.1f} "
            f"{buffed['null_rend_damage_per_use']:>12.1f} "
            f"{result['damage_per_use_delta']:>+10.1f}"
        )

    print()
    print(
        "OBLIVION PER NULL REND"
    )

    print(
        f"{'Buffs':>5} "
        f"{'Original':>10} "
        f"{'Buffed':>10}"
    )

    for result in report[
        "results"
    ]:

        print(
            f"{result['buff_count']:>5} "
            f"{result['original']['oblivions_per_null_rend']:>10.2f} "
            f"{result['buffed']['oblivions_per_null_rend']:>10.2f}"
        )

    print()
    print(
        "=============================================================="
    )
