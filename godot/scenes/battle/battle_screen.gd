extends Control

@onready var enemy_hp_bar = $"Enemy Monster HP bar"
@onready var ally_hp_bar = $"Ally Monster HP bar"

@onready var skill_1_button = $"Skill 1 Button"
@onready var skill_2_button = $"Skill 2 Button"
@onready var skill_3_button = $"Skill 3 Button"

@onready var turn_label = $"Turn Label"


var enemy_max_hp := 2520
var enemy_current_hp := 2520

var ally_max_hp := 3500
var ally_current_hp := 3500

var battle_finished := false


func _ready():

	enemy_hp_bar.max_value = enemy_max_hp
	enemy_hp_bar.value = enemy_current_hp

	ally_hp_bar.max_value = ally_max_hp
	ally_hp_bar.value = ally_current_hp

	turn_label.text = "Your turn"


func _on_skill_1_button_pressed():

	if battle_finished:
		return

	disable_skill_buttons()

	turn_label.text = "Igneous Drake attacks!"

	var damage := 300

	enemy_current_hp -= damage

	if enemy_current_hp < 0:
		enemy_current_hp = 0

	enemy_hp_bar.value = enemy_current_hp

	if enemy_current_hp <= 0:
		finish_battle(true)
		return

	await get_tree().create_timer(0.6).timeout

	enemy_turn()


func enemy_turn():

	turn_label.text = "Storm Slime attacks!"

	var damage := 150

	ally_current_hp -= damage

	if ally_current_hp < 0:
		ally_current_hp = 0

	ally_hp_bar.value = ally_current_hp

	if ally_current_hp <= 0:
		finish_battle(false)
		return

	await get_tree().create_timer(0.6).timeout

	turn_label.text = "Your turn"

	enable_skill_buttons()


func disable_skill_buttons():

	skill_1_button.disabled = true
	skill_2_button.disabled = true
	skill_3_button.disabled = true


func enable_skill_buttons():

	skill_1_button.disabled = false
	skill_2_button.disabled = false
	skill_3_button.disabled = false


func finish_battle(player_won):

	battle_finished = true

	disable_skill_buttons()

	if player_won:
		turn_label.text = "Victory!"
	else:
		turn_label.text = "Defeat!"
