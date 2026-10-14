extends Control

const PrototypeFactoryScript = preload(
    "res://scripts/factories/prototype_factory.gd"
)

const BattleControllerScript = preload(
    "res://scripts/battle/battle_controller.gd"
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

var battle_controller
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

    battle_controller = BattleControllerScript.new()
    battle_controller.setup(
        allies,
        enemies
    )

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


func start_next_turn() -> void:
    if battle_finished:
        return

    pending_skill_slot = 0
    set_target_selection(false)

    var context: Dictionary = (
        battle_controller.begin_next_turn()
    )

    if context.get("battle_over", false):
        finish_battle(
            context.get("player_won", false)
        )
        return

    if context.has("error"):
        push_error(context["error"])
        return

    update_battle_ui()

    var dot_result: Dictionary = context["dot_result"]

    if dot_result["damage"] > 0:
        turn_label.text = "%s takes %d DoT damage!" % [
            battle_controller.active_monster.monster_name,
            dot_result["damage"]
        ]

        update_battle_ui()

        if not battle_controller.active_monster.is_alive():
            await get_tree().create_timer(0.5).timeout
            battle_controller.clear_active_monster()
            start_next_turn()
            return

        await get_tree().create_timer(0.5).timeout

    if battle_controller.active_monster in allies:
        turn_label.text = "YOUR TURN - %s" % (
            battle_controller.active_monster.monster_name
        )
        update_skill_buttons()
    else:
        disable_skill_buttons()

        turn_label.text = "ENEMY TURN - %s" % (
            battle_controller.active_monster.monster_name
        )

        await get_tree().create_timer(0.5).timeout
        enemy_turn()


func request_player_skill(slot: int) -> void:
    if (
        battle_finished
        or battle_controller.active_monster == null
        or battle_controller.active_monster not in allies
    ):
        return

    var skill = battle_controller.active_monster.get_skill(slot)

    if skill == null or not skill.is_available():
        return

    if skill.target_type == "all_enemies":
        await preview_aoe_targets()
        execute_player_skill(
            skill,
            battle_controller.get_living(enemies)
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

    var skill = battle_controller.active_monster.get_skill(
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

    var result: Dictionary = (
        battle_controller.execute_active_skill(
            skill,
            targets
        )
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

    battle_controller.end_active_turn()
    update_battle_ui()

    if battle_controller.is_battle_over():
        finish_battle(
            battle_controller.player_won()
        )
        return

    await get_tree().create_timer(0.6).timeout

    battle_controller.clear_active_monster()
    start_next_turn()


func enemy_turn() -> void:
    if battle_controller.active_monster == null:
        return

    var skill = battle_controller.active_monster.get_skill(1)
    var target = battle_controller.choose_enemy_target()

    if skill == null or target == null:
        return

    var result: Dictionary = (
        battle_controller.execute_active_skill(
            skill,
            [target]
        )
    )

    turn_label.text = "%s hits %s for %d" % [
        battle_controller.active_monster.monster_name,
        target.monster_name,
        result["damage"]
    ]

    battle_controller.end_active_turn()
    update_battle_ui()

    if battle_controller.is_battle_over():
        finish_battle(
            battle_controller.player_won()
        )
        return

    await get_tree().create_timer(0.6).timeout

    battle_controller.clear_active_monster()
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
            battle_controller.active_monster == allies[index]
        )

    for index in range(enemy_huds.size()):
        enemy_huds[index].refresh(
            battle_controller.active_monster == enemies[index]
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
            battle_controller.active_monster == null
            or battle_controller.active_monster not in allies
        ):
            button.text = "-"
            button.disabled = true
            continue

        var skill = battle_controller.active_monster.get_skill(index + 1)

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
