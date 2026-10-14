extends Control

const PrototypeFactoryScript = preload(
    "res://scripts/factories/prototype_factory.gd"
)

@onready var skill_1_button = $"Skill 1 Button"
@onready var skill_2_button = $"Skill 2 Button"
@onready var skill_3_button = $"Skill 3 Button"
@onready var turn_label = $"Turn Label"

@onready var ally_huds: Array = [
    $"Ally HUD 1",
    $"Ally HUD 2"
]

@onready var enemy_huds: Array = [
    $"Enemy HUD 1",
    $"Enemy HUD 2"
]

var allies: Array = []
var enemies: Array = []

var active_monster
var active_turn_effects: Array = []
var pending_skill_slot := 0
var battle_finished := false


func _ready() -> void:
    allies = [
        PrototypeFactoryScript.create_level_one_monster(
            "drake_igneous"
        ),
        PrototypeFactoryScript.create_level_one_monster(
            "slime_abyssal"
        )
    ]

    enemies = [
        PrototypeFactoryScript.create_level_one_monster(
            "slime_storm"
        ),
        PrototypeFactoryScript.create_level_one_monster(
            "slime_igneous"
        )
    ]

    for index in range(ally_huds.size()):
        ally_huds[index].bind_monster(
            allies[index],
            false
        )

    for index in range(enemy_huds.size()):
        enemy_huds[index].bind_monster(
            enemies[index],
            true
        )

        enemy_huds[index].target_pressed.connect(
            func(index_copy = index):
                _on_enemy_target_pressed(index_copy)
        )

    update_battle_ui()

    await get_tree().process_frame
    start_next_turn()


func get_living(team: Array) -> Array:
    return team.filter(
        func(monster): return monster.is_alive()
    )


func get_living_combatants() -> Array:
    return get_living(allies) + get_living(enemies)


func fill_action_gauges() -> void:
    var combatants := get_living_combatants()

    if combatants.is_empty():
        return

    var smallest_time := INF

    for combatant in combatants:
        var speed: float = combatant.get_effective_stat(
            "speed"
        )
        var gauge_gain: float = speed / 2000.0

        if gauge_gain <= 0.0:
            continue

        var remaining_gauge: float = (
            1.0 - combatant.action_gauge
        )

        smallest_time = minf(
            smallest_time,
            remaining_gauge / gauge_gain
        )

    if smallest_time == INF:
        return

    for combatant in combatants:
        var speed: float = combatant.get_effective_stat(
            "speed"
        )
        var gauge_gain: float = speed / 2000.0

        if gauge_gain > 0.0:
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
    var effects_at_turn_start: Array = []

    effects_at_turn_start.append_array(monster.buffs)
    effects_at_turn_start.append_array(monster.debuffs)

    monster.reduce_skill_cooldowns()

    return {
        "effects_at_turn_start":
            effects_at_turn_start,
        "dot_result":
            monster.apply_damage_over_time()
    }


func end_turn(monster) -> void:
    monster.reduce_status_effect_turns(
        active_turn_effects
    )


func start_next_turn() -> void:
    if battle_finished:
        return

    if get_living(allies).is_empty():
        finish_battle(false)
        return

    if get_living(enemies).is_empty():
        finish_battle(true)
        return

    pending_skill_slot = 0
    set_target_selection(false)

    fill_action_gauges()
    active_monster = get_ready_combatant()

    if active_monster == null:
        push_error("No combatant reached full Action Gauge.")
        return

    active_monster.reset_action_gauge()

    var context := begin_turn(active_monster)

    active_turn_effects = context[
        "effects_at_turn_start"
    ]

    update_battle_ui()

    var dot_result: Dictionary = context["dot_result"]

    if dot_result["damage"] > 0:
        turn_label.text = "%s takes %d DoT damage!" % [
            active_monster.monster_name,
            dot_result["damage"]
        ]

        update_battle_ui()

        if not active_monster.is_alive():
            await get_tree().create_timer(0.5).timeout
            active_monster = null
            start_next_turn()
            return

        await get_tree().create_timer(0.5).timeout

    if active_monster in allies:
        turn_label.text = "YOUR TURN - %s" % (
            active_monster.monster_name
        )
        update_skill_buttons()
    else:
        disable_skill_buttons()

        turn_label.text = "ENEMY TURN - %s" % (
            active_monster.monster_name
        )

        await get_tree().create_timer(0.5).timeout
        enemy_turn()


func request_player_skill(slot: int) -> void:
    if (
        battle_finished
        or active_monster == null
        or active_monster not in allies
    ):
        return

    var skill = active_monster.get_skill(slot)

    if skill == null or not skill.is_available():
        return

    if skill.target_type == "all_enemies":
        await preview_aoe_targets()
        execute_player_skill(
            skill,
            get_living(enemies)
        )
        return

    pending_skill_slot = slot
    set_target_selection(true)
    turn_label.text = "Choose an enemy target"


func _on_enemy_target_pressed(index: int) -> void:
    if pending_skill_slot <= 0:
        return

    if index < 0 or index >= enemies.size():
        return

    var target = enemies[index]

    if not target.is_alive():
        return

    var skill = active_monster.get_skill(
        pending_skill_slot
    )

    pending_skill_slot = 0
    set_target_selection(false)

    execute_player_skill(
        skill,
        [target]
    )


func execute_player_skill(
    skill,
    targets: Array
) -> void:
    disable_skill_buttons()
    set_target_selection(false)

    var result: Dictionary = skill.execute_targets(
        active_monster,
        targets
    )

    update_battle_ui()

    turn_label.text = "%s: %d total damage" % [
        skill.skill_name,
        result["damage"]
    ]

    if result["critical_hits"] > 0:
        turn_label.text += " - %d CRIT" % (
            result["critical_hits"]
        )

    if result["healing"] > 0:
        turn_label.text += " - healed %d" % (
            result["healing"]
        )

    end_turn(active_monster)
    update_battle_ui()

    if get_living(enemies).is_empty():
        finish_battle(true)
        return

    await get_tree().create_timer(0.6).timeout

    active_monster = null
    start_next_turn()


func enemy_turn() -> void:
    if active_monster == null:
        return

    var skill = active_monster.get_skill(1)
    var living_allies := get_living(allies)

    if skill == null or living_allies.is_empty():
        return

    var target = living_allies.pick_random()

    var result: Dictionary = skill.execute_targets(
        active_monster,
        [target]
    )

    turn_label.text = "%s hits %s for %d" % [
        active_monster.monster_name,
        target.monster_name,
        result["damage"]
    ]

    end_turn(active_monster)
    update_battle_ui()

    if get_living(allies).is_empty():
        finish_battle(false)
        return

    await get_tree().create_timer(0.6).timeout

    active_monster = null
    start_next_turn()


func _on_skill_1_button_pressed() -> void:
    request_player_skill(1)


func _on_skill_2_button_pressed() -> void:
    request_player_skill(2)


func _on_skill_3_button_pressed() -> void:
    request_player_skill(3)


func update_battle_ui() -> void:
    for index in range(ally_huds.size()):
        ally_huds[index].refresh(
            active_monster == allies[index]
        )

    for index in range(enemy_huds.size()):
        enemy_huds[index].refresh(
            active_monster == enemies[index]
        )

    update_skill_buttons()


func update_skill_buttons() -> void:
    var buttons := [
        skill_1_button,
        skill_2_button,
        skill_3_button
    ]

    for index in range(buttons.size()):
        var button = buttons[index]

        if (
            active_monster == null
            or active_monster not in allies
        ):
            button.text = "-"
            button.disabled = true
            continue

        var skill = active_monster.get_skill(index + 1)

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
            or not skill.is_available()
        )


func set_target_selection(enabled: bool) -> void:
    for hud in enemy_huds:
        hud.set_target_mode(
            "single" if enabled else "none"
        )


func set_aoe_preview(enabled: bool) -> void:
    for hud in enemy_huds:
        hud.set_target_mode(
            "aoe" if enabled else "none"
        )


func preview_aoe_targets() -> void:
    disable_skill_buttons()
    set_aoe_preview(true)
    turn_label.text = "All enemies will be hit"

    await get_tree().create_timer(0.35).timeout

    set_aoe_preview(false)


func disable_skill_buttons() -> void:
    skill_1_button.disabled = true
    skill_2_button.disabled = true
    skill_3_button.disabled = true


func finish_battle(player_won: bool) -> void:
    battle_finished = true
    pending_skill_slot = 0

    disable_skill_buttons()
    set_target_selection(false)
    set_aoe_preview(false)
    update_battle_ui()

    turn_label.text = (
        "Victory!" if player_won else "Defeat!"
    )
