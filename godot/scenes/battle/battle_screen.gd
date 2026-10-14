extends Control

const PrototypeFactoryScript = preload(
    "res://scripts/factories/prototype_factory.gd"
)

@onready var enemy_hp_bar = $"Enemy Monster HP bar"
@onready var ally_hp_bar = $"Ally Monster HP bar"

@onready var enemy_name_label = $"Enemy Monster Name"
@onready var ally_name_label = $"Ally Monster Name"
@onready var enemy_status_label = $"Enemy Status Label"

@onready var skill_1_button = $"Skill 1 Button"
@onready var skill_2_button = $"Skill 2 Button"
@onready var skill_3_button = $"Skill 3 Button"

@onready var turn_label = $"Turn Label"


var player_monster
var enemy_monster

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
    enemy_hp_bar.value = enemy_monster.health

    ally_hp_bar.max_value = player_monster.max_health
    ally_hp_bar.value = player_monster.health

    update_skill_buttons()
    update_status_display()

    turn_label.text = "Your turn"


func use_player_skill(slot: int) -> void:
    if battle_finished:
        return

    var skill = player_monster.get_skill(slot)

    if skill == null or not skill.is_available():
        return

    disable_skill_buttons()

    var result: Dictionary = skill.execute(
        player_monster,
        enemy_monster
    )

    enemy_hp_bar.value = enemy_monster.health
    ally_hp_bar.value = player_monster.health

    update_status_display()

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

    await get_tree().create_timer(0.6).timeout

    enemy_turn()


func _on_skill_1_button_pressed() -> void:
    use_player_skill(1)


func _on_skill_2_button_pressed() -> void:
    use_player_skill(2)


func _on_skill_3_button_pressed() -> void:
    use_player_skill(3)


func enemy_turn() -> void:
    # Burn and future DoTs resolve at the start of the affected
    # monster's turn, matching the Python combat system.
    var dot_result: Dictionary = (
        enemy_monster.apply_damage_over_time()
    )

    if dot_result["damage"] > 0:
        enemy_hp_bar.value = enemy_monster.health

        turn_label.text = "%s takes %d Burn damage!" % [
            enemy_monster.monster_name,
            dot_result["damage"]
        ]

        if not enemy_monster.is_alive():
            finish_battle(true)
            return

        await get_tree().create_timer(0.6).timeout

    var skill = enemy_monster.get_skill(1)

    if skill == null:
        return

    var result: Dictionary = skill.execute(
        enemy_monster,
        player_monster
    )

    ally_hp_bar.value = player_monster.health

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

    enemy_monster.reduce_status_effect_turns()

    # Cooldowns tick before the player's next turn.
    player_monster.reduce_skill_cooldowns()
    enemy_monster.reduce_skill_cooldowns()

    update_status_display()
    update_skill_buttons()

    await get_tree().create_timer(0.6).timeout

    turn_label.text = "Your turn"


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
            button.text += "
CD %d" % skill.current_cooldown

        button.disabled = (
            battle_finished
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
