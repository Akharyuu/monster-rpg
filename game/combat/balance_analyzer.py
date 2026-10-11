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

    for benchmark_id in benchmark_ids:

        simulation = simulate_battles(
            [monster_id],
            [benchmark_id],
            runs=runs,
            verbose=False,
            level=level,
            ascended=ascended,
            max_turns=max_turns
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
        "========================================"
    )



# =========================================================
#                 TEAM SWAP BALANCE ANALYZER
# =========================================================

DEFAULT_TEAM_CORE = [
    "dryad_storm",
    "griffon_igneous"
]


def analyze_team_swap_balance(
    monster_id,
    runs=500,
    benchmark_ids=None,
    core_team_ids=None,
    level=50,
    ascended=True,
    max_turns=200,
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

    if core_team_ids is None:
        core_team_ids = list(
            DEFAULT_TEAM_CORE
        )

    for core_id in core_team_ids:

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

    total_combined_win_rate = 0
    total_draw_rate = 0
    total_turns = 0
    total_team_remaining_hp_percent = 0

    total_direct_damage = 0
    total_dot_damage = 0
    total_healing = 0
    total_shield_generated = 0
    total_shield_absorbed = 0

    for benchmark_id in benchmark_ids:

        candidate_team = [
            monster_id
        ] + list(core_team_ids)

        benchmark_team = [
            benchmark_id
        ] + list(core_team_ids)

        side_a = simulate_battles(
            candidate_team,
            benchmark_team,
            runs=runs,
            verbose=False,
            level=level,
            ascended=ascended,
            max_turns=max_turns
        )

        side_b = simulate_battles(
            benchmark_team,
            candidate_team,
            runs=runs,
            verbose=False,
            level=level,
            ascended=ascended,
            max_turns=max_turns
        )

        candidate_a_telemetry = (
            side_a["team_a_telemetry"][0]
        )

        candidate_b_telemetry = (
            side_b["team_b_telemetry"][0]
        )

        candidate_a_win_rate = (
            side_a["team_a_win_rate"]
        )

        candidate_b_win_rate = (
            side_b["team_b_win_rate"]
        )

        combined_win_rate = (
            candidate_a_win_rate
            + candidate_b_win_rate
        ) / 2

        combined_draw_rate = (
            side_a["draw_rate"]
            + side_b["draw_rate"]
        ) / 2

        average_turns = (
            side_a["average_turns"]
            + side_b["average_turns"]
        ) / 2

        average_team_remaining_hp_percent = (
            side_a[
                "team_a_average_remaining_hp_percent"
            ]
            + side_b[
                "team_b_average_remaining_hp_percent"
            ]
        ) / 2

        average_direct_damage = (
            candidate_a_telemetry[
                "direct_damage"
            ]
            + candidate_b_telemetry[
                "direct_damage"
            ]
        ) / 2

        average_dot_damage = (
            candidate_a_telemetry[
                "dot_damage"
            ]
            + candidate_b_telemetry[
                "dot_damage"
            ]
        ) / 2

        average_healing = (
            candidate_a_telemetry[
                "healing"
            ]
            + candidate_b_telemetry[
                "healing"
            ]
        ) / 2

        average_shield_generated = (
            candidate_a_telemetry[
                "shield_generated"
            ]
            + candidate_b_telemetry[
                "shield_generated"
            ]
        ) / 2

        average_shield_absorbed = (
            candidate_a_telemetry[
                "shield_absorbed"
            ]
            + candidate_b_telemetry[
                "shield_absorbed"
            ]
        ) / 2

        matchup = {
            "opponent_id": benchmark_id,
            "opponent_name": MONSTER_DATA[
                benchmark_id
            ]["name"],
            "candidate_team": list(
                candidate_team
            ),
            "benchmark_team": list(
                benchmark_team
            ),
            "win_rate_as_team_a":
                candidate_a_win_rate,
            "win_rate_as_team_b":
                candidate_b_win_rate,
            "combined_win_rate":
                combined_win_rate,
            "draw_rate":
                combined_draw_rate,
            "average_turns":
                average_turns,
            "average_team_remaining_hp_percent":
                average_team_remaining_hp_percent,
            "direct_damage":
                average_direct_damage,
            "dot_damage":
                average_dot_damage,
            "total_damage": (
                average_direct_damage
                + average_dot_damage
            ),
            "healing":
                average_healing,
            "shield_generated":
                average_shield_generated,
            "shield_absorbed":
                average_shield_absorbed
        }

        matchups.append(
            matchup
        )

        total_combined_win_rate += (
            matchup["combined_win_rate"]
        )

        total_draw_rate += (
            matchup["draw_rate"]
        )

        total_turns += (
            matchup["average_turns"]
        )

        total_team_remaining_hp_percent += (
            matchup[
                "average_team_remaining_hp_percent"
            ]
        )

        total_direct_damage += (
            matchup["direct_damage"]
        )

        total_dot_damage += (
            matchup["dot_damage"]
        )

        total_healing += (
            matchup["healing"]
        )

        total_shield_generated += (
            matchup["shield_generated"]
        )

        total_shield_absorbed += (
            matchup["shield_absorbed"]
        )

    matchup_count = len(matchups)

    overall = {
        "average_win_rate": (
            total_combined_win_rate
            / matchup_count
        ),
        "average_draw_rate": (
            total_draw_rate
            / matchup_count
        ),
        "average_turns": (
            total_turns
            / matchup_count
        ),
        "average_team_remaining_hp_percent": (
            total_team_remaining_hp_percent
            / matchup_count
        ),
        "average_direct_damage": (
            total_direct_damage
            / matchup_count
        ),
        "average_dot_damage": (
            total_dot_damage
            / matchup_count
        ),
        "average_total_damage": (
            (
                total_direct_damage
                + total_dot_damage
            )
            / matchup_count
        ),
        "average_healing": (
            total_healing
            / matchup_count
        ),
        "average_shield_generated": (
            total_shield_generated
            / matchup_count
        ),
        "average_shield_absorbed": (
            total_shield_absorbed
            / matchup_count
        )
    }

    report = {
        "monster_id": monster_id,
        "monster_name": MONSTER_DATA[
            monster_id
        ]["name"],
        "rarity": MONSTER_DATA[
            monster_id
        ]["rarity"],
        "runs_per_side": runs,
        "level": level,
        "ascended": ascended,
        "max_turns": max_turns,
        "core_team_ids": list(
            core_team_ids
        ),
        "benchmark_ids": list(
            benchmark_ids
        ),
        "matchups": matchups,
        "overall": overall
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
        f"Runs per side: "
        f"{report['runs_per_side']}"
    )

    print(
        f"Level: {report['level']}"
    )

    print(
        f"Ascended: {report['ascended']}"
    )

    print(
        "Core team: "
        + ", ".join(
            report["core_team_ids"]
        )
    )

    for matchup in report["matchups"]:

        print()
        print(
            f"vs {matchup['opponent_id']}"
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
            f"  Combined win rate: "
            f"{matchup['combined_win_rate']:.1f}%"
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
            f"  Unit damage: "
            f"{matchup['total_damage']:.1f}"
        )

        print(
            f"  Unit healing: "
            f"{matchup['healing']:.1f}"
        )

        print(
            f"  Unit shield generated: "
            f"{matchup['shield_generated']:.1f}"
        )

        print(
            f"  Unit shield absorbed: "
            f"{matchup['shield_absorbed']:.1f}"
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
        "========================================"
    )
