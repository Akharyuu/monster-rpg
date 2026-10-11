from ..combat.combat import simulate_battles
from ..data.monster_data import MONSTER_DATA
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

            if resonance > 0:
                simulation_kwargs[
                    "primary_resonance"
                ] = resonance

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
