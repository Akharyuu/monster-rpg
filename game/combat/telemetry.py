# =========================================================
#                    COMBAT TELEMETRY
# =========================================================

TELEMETRY_METRICS = (
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
    "freezes_broken_before_turn",
    "buffs_removed",
    "strip_events",
    "veil_blocks",
    "bottomless_hunger_activations",
    "action_gauge_from_bottomless_hunger",
    "voidborn_activations",
    "oblivions_applied",
    "defense_breaks_applied",
    "null_rend_uses",
    "dismantle_uses",
    "null_rend_damage",
    "dismantle_damage"
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
                "shield_absorbed": 0,
                "turns_denied": 0,
                "stuns_applied": 0,
                "freezes_applied": 0,
                "stun_turns_denied": 0,
                "freeze_turns_denied": 0,
                "freezes_broken_before_turn": 0,
                "buffs_removed": 0,
                "strip_events": 0,
                "veil_blocks": 0,
                "bottomless_hunger_activations": 0,
                "action_gauge_from_bottomless_hunger": 0,
                "voidborn_activations": 0,
                "oblivions_applied": 0,
                "defense_breaks_applied": 0,
                "null_rend_uses": 0,
                "dismantle_uses": 0,
                "null_rend_damage": 0,
                "dismantle_damage": 0
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
