from ..combat.combat import simulate_battles
from ..data.monster_data import MONSTER_DATA


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
            ascended=ascended
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
