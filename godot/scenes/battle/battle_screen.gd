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

    var player_s1 = player_monster.get_skill(1)

    if player_s1 != null:
        skill_1_button.text = player_s1.skill_name

    skill_2_button.text = "S2 (soon)"
    skill_3_button.text = "S3 (soon)"
    skill_2_button.disabled = true
    skill_3_button.disabled = true

    update_status_display()
    turn_label.text = "Your turn"


func _on_skill_1_button_pressed() -> void:
    if battle_finished:
        return

    disable_skill_buttons()

    var skill = player_monster.get_skill(1)

    if skill == null:
        return

    var result: Dictionary = skill.execute(
        player_monster,
        enemy_monster
    )

    enemy_hp_bar.value = enemy_monster.health
    update_status_display()

    if not result["success"]:
        turn_label.text = "Skill unavailable."
        enable_skill_buttons()
        return

    var message := "%s uses %s: %d damage" % [
        ally_name_label.text,
        skill.skill_name,
        result["damage"]
    ]

    if result["critical_hits"] > 0:
        message += " - CRITICAL!"

    if not result["effects_applied"].is_empty():
        var applied = result["effects_applied"][0]
        message += " - %s!" % applied.effect_name

    turn_label.text = message

    if not enemy_monster.is_alive():
        finish_battle(true)
        return

    await get_tree().create_timer(0.6).timeout

    enemy_turn()


func enemy_turn() -> void:
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

    # Status effects lose duration at the end of the affected
    # monster's own turn, matching the Python combat flow.
    enemy_monster.reduce_status_effect_turns()
    update_status_display()

    await get_tree().create_timer(0.6).timeout

    player_monster.reduce_skill_cooldowns()
    enemy_monster.reduce_skill_cooldowns()

    turn_label.text = "Your turn"

    enable_skill_buttons()


func update_status_display() -> void:
    if enemy_monster.debuffs.is_empty():
        enemy_status_label.text = ""
        return

    var texts: Array[String] = []

    for debuff in enemy_monster.debuffs:
        texts.append(
            "%s (%d)" % [
                debuff.effect_name,
                debuff.remaining_turns
            ]
        )

    enemy_status_label.text = " | ".join(texts)


func disable_skill_buttons() -> void:
    skill_1_button.disabled = true
    skill_2_button.disabled = true
    skill_3_button.disabled = true


func enable_skill_buttons() -> void:
    var s1 = player_monster.get_skill(1)

    skill_1_button.disabled = (
        s1 == null
        or not s1.is_available()
    )

    skill_2_button.disabled = true
    skill_3_button.disabled = true


func finish_battle(player_won: bool) -> void:
    battle_finished = true

    disable_skill_buttons()

    if player_won:
        turn_label.text = "Victory!"
    else:
        turn_label.text = "Defeat!"
