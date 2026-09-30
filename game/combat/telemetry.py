# =========================================================
#                    COMBAT TELEMETRY
# =========================================================

TELEMETRY_METRICS = (
    "direct_damage",
    "dot_damage",
    "healing",
    "shield_generated",
    "shield_absorbed"
)


def create_battle_telemetry(team_a, team_b):

    entries = {}

    for team_name, team in (
        ("team_a", team_a),
        ("team_b", team_b)
    ):

        for slot, monster in enumerate(team):

            entries[id(monster)] = {
                "team": team_name,
                "slot": slot,
                "monster_id": monster.monster_id,
                "display_name": monster.display_name,
                "direct_damage": 0,
                "dot_damage": 0,
                "healing": 0,
                "shield_generated": 0,
                "shield_absorbed": 0
            }

    return {
        "entries": entries
    }



def record_telemetry(telemetry, monster, metric, amount):

    if telemetry is None:
        return

    if monster is None:
        return

    if metric not in TELEMETRY_METRICS:
        raise ValueError(
            f"Unknown telemetry metric: {metric}"
        )

    monster_entry = telemetry["entries"].get(
        id(monster)
    )

    if monster_entry is None:
        return

    monster_entry[metric] += amount



def get_active_shield(monster):

    for buff in monster.buffs:

        if buff.effect_id == "shield":
            return buff

    return None



def get_active_shield_value(monster):

    shield = get_active_shield(monster)

    if shield is None:
        return 0

    return shield.value



def serialize_battle_telemetry(telemetry):

    result = {
        "team_a": [],
        "team_b": []
    }

    for entry in telemetry["entries"].values():

        serialized_entry = dict(entry)

        team_name = serialized_entry.pop("team")

        result[team_name].append(
            serialized_entry
        )

    result["team_a"].sort(
        key=lambda entry: entry["slot"]
    )

    result["team_b"].sort(
        key=lambda entry: entry["slot"]
    )

    return result



def create_team_telemetry_totals(monster_ids):

    totals = []

    for slot, monster_id in enumerate(monster_ids):

        entry = {
            "slot": slot,
            "monster_id": monster_id
        }

        for metric in TELEMETRY_METRICS:
            entry[metric] = 0

        totals.append(entry)

    return totals



def add_team_telemetry(totals, battle_entries):

    for battle_entry in battle_entries:

        slot = battle_entry["slot"]

        for metric in TELEMETRY_METRICS:

            totals[slot][metric] += (
                battle_entry[metric]
            )



def average_team_telemetry(totals, runs):

    averages = []

    for total_entry in totals:

        average_entry = {
            "slot": total_entry["slot"],
            "monster_id": total_entry["monster_id"]
        }

        for metric in TELEMETRY_METRICS:

            average_entry[metric] = (
                total_entry[metric] / runs
            )

        averages.append(
            average_entry
        )

    return averages
