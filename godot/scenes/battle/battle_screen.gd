extends Control

const PrototypeFactoryScript = preload(
    "res://scripts/factories/prototype_factory.gd"
)

@onready var enemy_hp_bar = $"Enemy Monster HP bar"
@onready var ally_hp_bar = $"Ally Monster HP bar"

@onready var enemy_action_gauge = $"Enemy Action Gauge"
@onready var ally_action_gauge = $"Ally Action Gauge"

@onready var enemy_name_label = $"Enemy Monster Name"
@onready var ally_name_label = $"Ally Monster Name"
@onready var enemy_status_label = $"Enemy Status Label"

@onready var skill_1_button = $"Skill 1 Button"
@onready var skill_2_button = $"Skill 2 Button"
@onready var skill_3_button = $"Skill 3 Button"

@onready var turn_label = $"Turn Label"


var player_monster
var enemy_monster

var active_monster
var active_turn_effects: Array = []

var battle_finished := false


func _ready() -> void:
    player_monster = PrototypeFactoryScript.create_level_one_monster(
        "drake_igneous"
    )

    enemy_monster = PrototypeFactoryScript.create_level_one_monster(
        "slime_storm"
    )

    enemy_name_label.text = enemy_monster.monster_name
    ally_name_label.text = "Igneous Drake"

    enemy_hp_bar.max_value = enemy_monster.max_health
    ally_hp_bar.max_value = player_monster.max_health

    enemy_action_gauge.max_value = 100.0
    ally_action_gauge.max_value = 100.0

    update_battle_ui()

    # Action Gauge now decides who actually gets the first turn.
    await get_tree().process_frame
    start_next_turn()


func get_living_combatants() -> Array:
    var combatants: Array = []

    if player_monster.is_alive():
        combatants.append(player_monster)

    if enemy_monster.is_alive():
        combatants.append(enemy_monster)

    return combatants


func fill_action_gauges() -> void:
    var combatants := get_living_combatants()

    if combatants.is_empty():
        return

    var smallest_time := INF

    for combatant in combatants:
        var speed: float = combatant.get_effective_stat("speed")
        var gauge_gain: float = speed / 2000.0

        if gauge_gain <= 0.0:
            continue

        var remaining_gauge: float = (
            1.0 - combatant.action_gauge
        )

        var time_needed: float = (
            remaining_gauge / gauge_gain
        )

        smallest_time = minf(
            smallest_time,
            time_needed
        )

    if smallest_time == INF:
        return

    for combatant in combatants:
        var speed: float = combatant.get_effective_stat("speed")
        var gauge_gain: float = speed / 2000.0

        if gauge_gain <= 0.0:
            continue

        combatant.increase_action_gauge(
            gauge_gain * smallest_time
        )


func get_ready_combatant():
    var ready: Array = []

    for combatant in get_living_combatants():
        if combatant.action_gauge >= 0.999999:
            ready.append(combatant)

    if ready.is_empty():
        return null

    var chosen = ready[0]

    for combatant in ready:
        if (
            combatant.get_effective_stat("speed")
            > chosen.get_effective_stat("speed")
        ):
            chosen = combatant

    return chosen


func begin_turn(monster) -> Dictionary:
    # Match Python: remember which effects existed before the turn so
    # effects applied during the action do not immediately lose duration.
    var effects_at_turn_start: Array = []

    effects_at_turn_start.append_array(monster.buffs)
    effects_at_turn_start.append_array(monster.debuffs)

    # Match Python: cooldowns and DoT resolve at the beginning
    # of this monster's own turn.
    monster.reduce_skill_cooldowns()

    var dot_result: Dictionary = (
        monster.apply_damage_over_time()
    )

    return {
        "effects_at_turn_start": effects_at_turn_start,
        "dot_result": dot_result
    }


func end_turn(monster, turn_context: Dictionary) -> void:
    monster.reduce_status_effect_turns(
        turn_context["effects_at_turn_start"]
    )


func start_next_turn() -> void:
    if battle_finished:
        return

    if not player_monster.is_alive():
        finish_battle(false)
        return

    if not enemy_monster.is_alive():
        finish_battle(true)
        return

    fill_action_gauges()
    update_action_gauges()

    active_monster = get_ready_combatant()

    if active_monster == null:
        push_error("No combatant reached a full Action Gauge.")
        return

    # The acting monster spends its gauge before the action, just like
    # the Python battle loop.
    active_monster.reset_action_gauge()
    update_action_gauges()

    var turn_context: Dictionary = begin_turn(
        active_monster
    )

    active_turn_effects = turn_context[
        "effects_at_turn_start"
    ]

    update_battle_ui()

    var dot_result: Dictionary = turn_context[
        "dot_result"
    ]

    if dot_result["damage"] > 0:
        turn_label.text = "%s takes %d Burn damage!" % [
            active_monster.monster_name,
            dot_result["damage"]
        ]

        if not active_monster.is_alive():
            if active_monster == player_monster:
                finish_battle(false)
            else:
                finish_battle(true)
            return

        await get_tree().create_timer(0.6).timeout

    if active_monster == player_monster:
        turn_label.text = "YOUR TURN - %s" % (
            player_monster.monster_name
        )
        update_skill_buttons()
    else:
        disable_skill_buttons()
        turn_label.text = "ENEMY TURN - %s" % (
            enemy_monster.monster_name
        )

        await get_tree().create_timer(0.6).timeout
        enemy_turn()


func use_player_skill(slot: int) -> void:
    if (
        battle_finished
        or active_monster != player_monster
    ):
        return

    var skill = player_monster.get_skill(slot)

    if skill == null or not skill.is_available():
        return

    disable_skill_buttons()

    var result: Dictionary = skill.execute(
        player_monster,
        enemy_monster
    )

    update_battle_ui()

    var message := "%s: %d damage" % [
        skill.skill_name,
        result["damage"]
    ]

    if result["critical_hits"] > 0:
        message += " - CRITICAL!"

    if result["healing"] > 0:
        message += " - healed %d HP" % result["healing"]

    turn_label.text = message

    if not enemy_monster.is_alive():
        finish_battle(true)
        return

    end_turn(
        player_monster,
        {
            "effects_at_turn_start":
                active_turn_effects
        }
    )

    update_battle_ui()

    await get_tree().create_timer(0.6).timeout

    active_monster = null
    start_next_turn()


func _on_skill_1_button_pressed() -> void:
    use_player_skill(1)


func _on_skill_2_button_pressed() -> void:
    use_player_skill(2)


func _on_skill_3_button_pressed() -> void:
    use_player_skill(3)


func enemy_turn() -> void:
    if (
        battle_finished
        or active_monster != enemy_monster
    ):
        return

    var skill = enemy_monster.get_skill(1)

    if skill == null:
        return

    var result: Dictionary = skill.execute(
        enemy_monster,
        player_monster
    )

    update_battle_ui()

    var message := "%s uses %s: %d damage" % [
        enemy_monster.monster_name,
        skill.skill_name,
        result["damage"]
    ]

    if result["critical_hits"] > 0:
        message += " - CRITICAL!"

    turn_label.text = message

    if not player_monster.is_alive():
        finish_battle(false)
        return

    end_turn(
        enemy_monster,
        {
            "effects_at_turn_start":
                active_turn_effects
        }
    )

    update_battle_ui()

    await get_tree().create_timer(0.6).timeout

    active_monster = null
    start_next_turn()


func update_battle_ui() -> void:
    enemy_hp_bar.value = enemy_monster.health
    ally_hp_bar.value = player_monster.health

    update_action_gauges()
    update_status_display()
    update_skill_buttons()


func update_action_gauges() -> void:
    enemy_action_gauge.value = (
        enemy_monster.action_gauge * 100.0
    )

    ally_action_gauge.value = (
        player_monster.action_gauge * 100.0
    )


func update_status_display() -> void:
    if enemy_monster.debuffs.is_empty():
        enemy_status_label.text = ""
        return

    var texts: Array[String] = []

    for debuff in enemy_monster.debuffs:
        var text: String = str(debuff.effect_name)

        if debuff.max_stacks > 1:
            text += " x%d" % debuff.stacks

        text += " (%d)" % debuff.remaining_turns
        texts.append(text)

    enemy_status_label.text = " | ".join(texts)


func update_skill_buttons() -> void:
    var buttons := [
        skill_1_button,
        skill_2_button,
        skill_3_button
    ]

    for index in range(buttons.size()):
        var button = buttons[index]
        var skill = player_monster.get_skill(index + 1)

        if skill == null:
            button.text = "-"
            button.disabled = true
            continue

        button.text = skill.skill_name

        if skill.current_cooldown > 0:
            button.text += "\nCD %d" % (
                skill.current_cooldown
            )

        button.disabled = (
            battle_finished
            or active_monster != player_monster
            or not skill.is_available()
        )


func disable_skill_buttons() -> void:
    skill_1_button.disabled = true
    skill_2_button.disabled = true
    skill_3_button.disabled = true


func finish_battle(player_won: bool) -> void:
    battle_finished = true

    disable_skill_buttons()

    if player_won:
        turn_label.text = "Victory!"
    else:
        turn_label.text = "Defeat!"
