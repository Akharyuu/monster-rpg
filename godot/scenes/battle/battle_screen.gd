extends Control

const PrototypeFactoryScript = preload(
    "res://scripts/factories/prototype_factory.gd"
)

const BattleControllerScript = preload(
    "res://scripts/battle/battle_controller.gd"
)

const StatusEffectFactoryScript = preload(
    "res://scripts/factories/status_effect_factory.gd"
)

@onready var passive_button = $"Passive Button"
@onready var passive_button_2 = $"Passive Button 2"
@onready var passive_button_3 = $"Passive Button 3"
@onready var skill_1_button = $"Skill 1 Button"
@onready var skill_2_button = $"Skill 2 Button"
@onready var skill_3_button = $"Skill 3 Button"
@onready var turn_label = $"Turn Label"
@onready var options_overlay: ColorRect = $"Options Overlay"
@onready var battle_background: TextureRect = $"Background"
@onready var background_upper_layer: TextureRect = $"Background Upper Layer"

@onready var ally_huds: Array = [
	$"Ally HUD 1", $"Ally HUD 2",
	$"Ally HUD 3", $"Ally HUD 4"
]

@onready var enemy_huds: Array = [
	$"Enemy HUD 1", $"Enemy HUD 2",
	$"Enemy HUD 3", $"Enemy HUD 4"
]

var allies: Array = []
var enemies: Array = []

var battle_controller
var pending_skill_slot := 0
var pending_special_action: String = ""
var battle_finished := false
var action_in_progress := true


func _ready() -> void:
	_update_background_layers()
	# Visual 4v4 comparison: allied Kaelgors use the static back-side art;
	# enemy Kaelgors play the front-view idle animation.
	allies = [
		PrototypeFactoryScript.create_level_one_monster(
            "drake_igneous"
		),
		PrototypeFactoryScript.create_level_one_monster(
            "drake_igneous"
		),
		PrototypeFactoryScript.create_level_one_monster(
            "drake_igneous"
		),
		PrototypeFactoryScript.create_level_one_monster(
            "drake_igneous"
		)
	]

	enemies = [
		PrototypeFactoryScript.create_level_one_monster(
            "drake_igneous"
		),
		PrototypeFactoryScript.create_level_one_monster(
            "drake_igneous"
		),
		PrototypeFactoryScript.create_level_one_monster(
            "drake_igneous"
		),
		PrototypeFactoryScript.create_level_one_monster(
            "drake_igneous"
		)
	]

	# The old 100,000-HP dummy enemies made a full 4v4 unnecessarily long.
	# A modest HP boost allows repeated attacks without making the test
	# battle unreasonably slow. This does NOT modify canonical monster data.
	for enemy in enemies:
		enemy.max_health = int(round(enemy.max_health * 2.0))
		enemy.health = enemy.max_health

	_layout_team_huds(ally_huds, allies.size())
	_layout_team_huds(enemy_huds, enemies.size())

	battle_controller = BattleControllerScript.new()
	battle_controller.setup(
		allies,
		enemies
	)

	for index in range(mini(ally_huds.size(), allies.size())):
		ally_huds[index].bind_monster(
			allies[index],
			false
		)

		ally_huds[index].target_pressed.connect(
			func(index_copy = index):
				_on_ally_target_pressed(index_copy)
		)

	for index in range(mini(enemy_huds.size(), enemies.size())):
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


# A matching *_upper_layer.png is optional for any battle background.
# Keep the exact same stretch settings and rectangle as the base layer.
func _update_background_layers() -> void:
	background_upper_layer.visible = false
	background_upper_layer.texture = null

	if battle_background.texture == null:
		return

	var source_path: String = battle_background.texture.resource_path
	if source_path.is_empty():
		return

	var extension_index: int = source_path.rfind(".")
	if extension_index < 0:
		return

	var overlay_path: String = (
		source_path.substr(0, extension_index)
		+ "_upper_layer"
		+ source_path.substr(extension_index)
	)

	if not ResourceLoader.exists(overlay_path, "Texture2D"):
		return

	var overlay_texture: Texture2D = load(overlay_path) as Texture2D
	if overlay_texture == null:
		push_warning("Failed to load background upper layer: %s" % overlay_path)
		return

	background_upper_layer.texture = overlay_texture
	background_upper_layer.visible = true


# The teams face each other diagonally across the battlefield.
# Every size has its own arc: 1-3 units do NOT inherit the first N
# positions of the four-unit formation.
# Both formations sit lower on the forest path. The allied team shifts
# right while the enemy team moves left; the gaps grow toward ally 4.
const ALLY_ARCS := {
	1: [Vector2(310, 414)],
	2: [
		Vector2(137, 384),
		Vector2(408, 454)
	],
	3: [
		Vector2(81, 364),
		Vector2(265, 424),
		Vector2(492, 454)
	],
	4: [
		Vector2(57, 404),
		Vector2(204, 454),
		Vector2(374, 454),
		Vector2(559, 439)
	]
}

const ENEMY_ARCS := {
	1: [Vector2(855, 184)],
	2: [
		Vector2(697, 184),
		Vector2(953, 209)
	],
	3: [
		Vector2(626, 159),
		Vector2(805, 124),
		Vector2(994, 184)
	],
	4: [
		Vector2(578, 142),
		Vector2(754, 124),
		Vector2(911, 124),
		Vector2(1063, 174)
	]
}


func _layout_team_huds(huds: Array, team_size: int) -> void:
	var count: int = mini(team_size, huds.size())
	var positions: Array = (
		ALLY_ARCS.get(count, [])
		if huds == ally_huds
		else ENEMY_ARCS.get(count, [])
	)

	for index in range(huds.size()):
		var combat_hud: Control = huds[index]
		combat_hud.visible = index < count
		if index < count:
			combat_hud.position = positions[index]


func _on_options_button_pressed() -> void:
	options_overlay.visible = not options_overlay.visible


func _on_resume_button_pressed() -> void:
	options_overlay.visible = false


func _on_restart_button_pressed() -> void:
	get_tree().reload_current_scene()


func start_next_turn() -> void:
	if battle_finished:
		return

	action_in_progress = true
	pending_skill_slot = 0
	pending_special_action = ""
	set_target_selection(false)
	set_revive_target_selection(false)

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

	var hot_result: Dictionary = context.get(
		"hot_result",
		{"healing": 0}
	)

	if hot_result["healing"] > 0:
		turn_label.text = "%s recovers %d HP from Regrowth!" % [
			battle_controller.active_monster.monster_name,
			hot_result["healing"]
		]

		update_battle_ui()

		var hot_hud = get_hud_for_monster(
			battle_controller.active_monster
		)

		if hot_hud != null:
			await hot_hud.play_status_feedback(
				"+%d HP" % hot_result["healing"],
                "buff"
			)

		await get_tree().create_timer(0.35).timeout

	var dot_result: Dictionary = context["dot_result"]

	if dot_result["damage"] > 0:
		turn_label.text = "%s takes %d DoT damage!" % [
			battle_controller.active_monster.monster_name,
			dot_result["damage"]
		]

		update_battle_ui()

		var dot_hud = get_hud_for_monster(
			battle_controller.active_monster
		)

		if dot_hud != null:
			await dot_hud.play_damage_feedback(
				int(dot_result["damage"]),
				false,
				true
			)

		if not battle_controller.active_monster.is_alive():
			await get_tree().create_timer(0.5).timeout
			battle_controller.clear_active_monster()
			start_next_turn()
			return

		await get_tree().create_timer(0.5).timeout

	if battle_controller.active_monster_cannot_act():
		await handle_incapacitated_turn()
		return

	if battle_controller.active_monster in allies:
		turn_label.text = "YOUR TURN - %s" % (
			battle_controller.active_monster.monster_name
		)
		action_in_progress = false
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
		or action_in_progress
		or battle_controller.active_monster == null
		or battle_controller.active_monster not in allies
	):
		return

	var skill = battle_controller.active_monster.get_skill(slot)

	if (
		battle_controller.active_monster.is_silenced()
		and slot != 1
	):
		turn_label.text = "Silence: only S1 can be used"
		return

	if skill == null or not skill.is_available():
		return

	if skill.target_type == "all_enemies":
		action_in_progress = true
		await preview_aoe_targets()
		execute_player_skill(
			skill,
			battle_controller.get_living(enemies)
		)
		return

	if skill.target_type == "random_enemies":
		action_in_progress = true
		set_aoe_preview(true)
		turn_label.text = "10 hits will strike random enemies"

		await get_tree().create_timer(0.35).timeout
		set_aoe_preview(false)

		execute_player_skill(
			skill,
			battle_controller.get_living(enemies)
		)
		return

	if skill.target_type == "all_allies":
		action_in_progress = true
		turn_label.text = "All allies will be affected"
		await get_tree().create_timer(0.25).timeout

		execute_player_skill(
			skill,
			battle_controller.get_living(allies)
		)
		return

	if skill.target_type == "self":
		action_in_progress = true
		turn_label.text = "Self-targeting skill"
		await get_tree().create_timer(0.2).timeout

		execute_player_skill(
			skill,
			[battle_controller.active_monster]
		)
		return

	action_in_progress = true
	pending_skill_slot = slot
	set_target_selection(true)
	update_skill_buttons()
	turn_label.text = "Choose an enemy target"


func _on_ally_target_pressed(index: int) -> void:
	if pending_special_action != "soul_recall":
		return

	if index < 0 or index >= allies.size():
		return

	var target = allies[index]

	if target.is_alive() or target.banished:
		return

	pending_special_action = ""
	set_revive_target_selection(false)
	disable_skill_buttons()

	var result: Dictionary = (
		battle_controller.execute_soul_recall(
			target
		)
	)

	if not result.get("success", false):
		action_in_progress = false
		update_skill_buttons()
		return

	update_battle_ui()
	await play_caster_feedback(result)

	turn_label.text = "%s revives %s" % [
		battle_controller.active_monster.monster_name,
		target.monster_name
	]

	battle_controller.end_active_turn()
	update_battle_ui()

	await get_tree().create_timer(0.6).timeout

	battle_controller.clear_active_monster()
	start_next_turn()


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

	var attacker = battle_controller.active_monster
	var attacker_hud = get_hud_for_monster(attacker)

	if attacker_hud != null:
		await attacker_hud.play_attack_feedback()

	var result: Dictionary = (
		battle_controller.execute_active_skill(
			skill,
			targets
		)
	)

	update_battle_ui()
	await play_result_feedback(result)
	await play_caster_feedback(result)

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

	var attacker_hud = get_hud_for_monster(
		battle_controller.active_monster
	)

	if attacker_hud != null:
		await attacker_hud.play_attack_feedback()

	var result: Dictionary = (
		battle_controller.execute_active_skill(
			skill,
			[target]
		)
	)

	update_battle_ui()
	await play_result_feedback(result)
	await play_caster_feedback(result)

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


func handle_incapacitated_turn() -> void:
	var monster = battle_controller.active_monster

	if monster == null:
		return

	disable_skill_buttons()
	set_target_selection(false)

	var effect_id: String = (
		battle_controller.get_active_control_effect_id()
	)

	var message: String = "cannot act and loses the turn"

	if effect_id == "stun":
		message = "is STUNNED and loses the turn!"
	elif effect_id == "freeze":
		message = "is FROZEN and loses the turn!"

	turn_label.text = "%s %s" % [
		monster.monster_name,
		message
	]

	var hud = get_hud_for_monster(monster)

	if hud != null:
		await hud.play_status_feedback(
			"STUNNED!" if effect_id == "stun" else "FROZEN!",
            "debuff"
		)

	battle_controller.end_active_turn()
	update_battle_ui()

	await get_tree().create_timer(0.55).timeout

	battle_controller.clear_active_monster()
	start_next_turn()


func _on_skill_1_button_pressed() -> void:
	request_player_skill(1)


func _on_skill_2_button_pressed() -> void:
	request_player_skill(2)


func _on_skill_3_button_pressed() -> void:
	request_player_skill(3)


func get_hud_for_monster(monster):
	var ally_index: int = allies.find(monster)

	if ally_index >= 0 and ally_index < ally_huds.size():
		return ally_huds[ally_index]

	var enemy_index: int = enemies.find(monster)

	if enemy_index >= 0 and enemy_index < enemy_huds.size():
		return enemy_huds[enemy_index]

	return null


func play_result_feedback(result: Dictionary) -> void:
	var target_results: Array = result.get(
		"target_results",
		[]
	)

	if target_results.is_empty():
		return

	for target_result in target_results:
		var target = target_result["target"]
		var hud = get_hud_for_monster(target)

		if hud == null:
			continue

		await hud.play_damage_feedback(
			int(target_result["damage"]),
			int(target_result["critical_hits"]) > 0,
			false
		)

		var shown_effects: Array[String] = []

		for effect in target_result.get(
			"effects_applied",
			[]
		):
			var effect_id: String = str(
				effect.effect_id
			)

			if effect_id in shown_effects:
				continue

			shown_effects.append(effect_id)

			await hud.play_status_feedback(
				get_status_feedback_text(effect_id),
				"burn" if effect_id == "burn" else "debuff"
			)

		var buffs_removed: int = int(
			target_result.get("buffs_removed", 0)
		)

		if buffs_removed > 0:
			await hud.play_status_feedback(
				"STRIP x%d!" % buffs_removed,
                "debuff"
			)

		if not target_result.get(
			"resisted_effects",
			[]
		).is_empty():
			await hud.play_status_feedback(
				"RESIST!",
                "resist"
			)

	for survivor in result.get(
		"deathless_survivors",
		[]
	):
		var survivor_hud = get_hud_for_monster(
			survivor
		)

		if survivor_hud != null:
			await survivor_hud.play_status_feedback(
				"DEATHLESS RIDER - 1 HP!",
                "buff"
			)


func play_caster_feedback(result: Dictionary) -> void:
	var feedback: Array = result.get(
		"caster_feedback",
		[]
	)

	if feedback.is_empty():
		return

	var hud = get_hud_for_monster(
		battle_controller.active_monster
	)

	if hud == null:
		return

	for message in feedback:
		await hud.play_status_feedback(
			str(message),
            "buff"
		)


func get_status_feedback_text(effect_id: String) -> String:
	match effect_id:
		"burn":
			return "BURN!"
		"poison":
			return "POISON!"
		"defense_break":
			return "DEF DOWN!"
		"attack_break":
			return "ATK DOWN!"
		"speed_break":
			return "SPD DOWN!"
		"stun":
			return "STUN!"
		"freeze":
			return "FREEZE!"
		"silence":
			return "SILENCE!"
		"oblivion":
			return "OBLIVION!"
		"heal_block":
			return "HEAL BLOCK!"
		"vulnerability":
			return "VULNERABLE!"
		_:
			return effect_id.to_upper()


func update_battle_ui() -> void:
	for index in range(mini(ally_huds.size(), allies.size())):
		ally_huds[index].refresh(
			battle_controller.active_monster == allies[index]
		)

	for index in range(mini(enemy_huds.size(), enemies.size())):
		enemy_huds[index].refresh(
			battle_controller.active_monster == enemies[index]
		)

	update_skill_buttons()


func _set_action_button_state(
	button: Button,
	unavailable: bool,
	interactive: bool = true
) -> void:
	# Informational passives keep mouse hover for their tooltips.
	# Actionable skills/actions are also disabled when unavailable.
	button.disabled = unavailable if interactive else false
	button.modulate = (
		Color(0.52, 0.55, 0.62, 1.0)
		if unavailable
		else Color.WHITE
	)


# Icons are optional and keyed by monster_id and canonical skill_id.
# Missing artwork keeps the regular text button unchanged.
func _update_skill_icon(button: SkillButton, monster_id: String, skill_id: String) -> void:
	var icon_path: String = "res://assets/skill_icons/%s/%s.png" % [
		monster_id, skill_id
	]
	button.set_skill_icon(icon_path)


func update_skill_buttons() -> void:
	_update_passive_button()

	var buttons := [
		skill_1_button,
		skill_2_button,
		skill_3_button
	]

	for index in range(buttons.size()):
		var button: SkillButton = buttons[index]
		button.set_hud_role("active")
		button.set_target_selected(pending_skill_slot == index + 1)
		button.set_cooldown_turns(0)

		if (
			battle_controller.active_monster == null
			or battle_controller.active_monster not in allies
		):
			button.visible = false
			button.text = "-"
			button.set_tooltip_skill(null)
			button.clear_skill_icon()
			_set_action_button_state(button, true)
			continue

		var active = battle_controller.active_monster
		var skill = active.get_skill(index + 1)

		if skill == null:
			button.visible = false
			button.text = "-"
			button.set_tooltip_skill(null)
			button.clear_skill_icon()
			_set_action_button_state(button, true)
			continue

		button.visible = true
		button.text = "S%d" % (index + 1)
		button.set_tooltip_skill(skill)
		_update_skill_icon(button, str(active.monster_id), str(skill.skill_id))
		button.set_cooldown_turns(skill.current_cooldown)
		if button.has_skill_icon():
			button.text = ""

		if skill.current_cooldown > 0 and not button.has_skill_icon():
			button.text += "\nCD %d" % (
				skill.current_cooldown
			)

		# Silence prevents active skills S2/S3, but S1 remains usable.
		# Oblivion suppresses passives, not ordinary active skills.
		var blocked_by_silence: bool = (
			active.is_silenced()
			and index > 0
		)

		_set_action_button_state(
			button,
			battle_finished
			or action_in_progress
			or blocked_by_silence
			or not skill.is_available()
		)
		if pending_skill_slot == index + 1:
			# Keep a selected skill bright even while input is locked
			# awaiting a target click.
			button.modulate = Color.WHITE

	_layout_action_buttons()


# Fill from the options button LEFTWARD, using only the actions
# actually present in the current monster's kit. Skills always precede
# informational passives and special passive-slot actions.
func _layout_action_buttons() -> void:
	var ordered: Array[Control] = []
	for button in [
		skill_1_button, skill_2_button, skill_3_button,
		passive_button, passive_button_2, passive_button_3
	]:
		if button.visible:
			ordered.append(button)

	const GAP: float = 10.0
	const OPTIONS_GAP: float = 12.0
	const BUTTON_Y: float = 619.0

	var right_edge: float = $"Options Button".position.x - OPTIONS_GAP
	for index in range(ordered.size() - 1, -1, -1):
		var button: Control = ordered[index]
		button.position = Vector2(
			right_edge - button.size.x, BUTTON_Y
		)
		right_edge = button.position.x - GAP





func _update_passive_button() -> void:
	var buttons := [
		passive_button,
		passive_button_2,
		passive_button_3
	]

	for button in buttons:
		button.set_hud_role("passive")
		button.set_target_selected(false)
		button.set_cooldown_turns(0)
		button.text = "PASSIVE"
		button.set_tooltip_passive({})
		button.clear_skill_icon()
		button.visible = false
		_set_action_button_state(button, false, false)

	if (
		battle_controller.active_monster == null
		or battle_controller.active_monster not in allies
	):
		return

	var active = battle_controller.active_monster
	var passive_list: Array = active.passive_tooltips

	if passive_list.is_empty():
		var legacy: Dictionary = active.passive_tooltip

		if not legacy.is_empty():
			passive_list = [legacy]

	var visible_count: int = mini(
		buttons.size(),
		passive_list.size()
	)

	# Informational passives are always visible. An internal CD only
	# mutes the portion of the passive that is on cooldown.
	for index in range(visible_count):
		var button = buttons[index]
		var passive_data: Dictionary = passive_list[index]
		# Tooltip names are presentation text and may change by language.
		# Canonical passive IDs follow the same stable naming convention as skills.
		var passive_id: String = ""
		if index < active.passive_ids.size():
			passive_id = str(active.passive_ids[index])
		var cooldown_id: String = str(
			passive_data.get("internal_cooldown_id", "")
		)
		var remaining_cd: int = 0

		if not cooldown_id.is_empty():
			remaining_cd = active.get_internal_cooldown(
				cooldown_id
			)

		button.visible = true
		button.text = "P%d" % (index + 1)

		if remaining_cd > 0:
			button.text += "\nCD %d" % remaining_cd

		var tooltip_data: Dictionary = (
			passive_data.duplicate(true)
		)
		tooltip_data["cooldown_remaining"] = remaining_cd
		button.set_tooltip_passive(tooltip_data)
		button.set_cooldown_turns(remaining_cd)

		# Passive artwork shares the same optional PNG lookup and renderer
		# as active skills. Without artwork, the P1/CD text remains.
		if not passive_id.is_empty():
			_update_skill_icon(
				button, str(active.monster_id), passive_id
			)
			if button.has_skill_icon():
				button.text = ""

		var suppressed: bool = active.has_oblivion()
		var recharging: bool = remaining_cd > 0

		_set_action_button_state(
			button,
			suppressed or recharging,
			false
		)

		if suppressed:
			button.set_visual_state("passive_suppressed")
		elif recharging:
			button.set_visual_state("passive_cooldown")
		else:
			button.set_visual_state("passive_ready")

	# Soul Recall is a separate active action beside Soul Vessel.
	# It stays visible and shows charge progress even before 5/5.
	if (
		active.monster_id == "dullahan_aether"
		and active.resonance >= 2
		and visible_count < buttons.size()
	):
		var action_button = buttons[visible_count]
		var charges: int = active.get_combat_resource(
            "soul_charges"
		)
		var unlocked: bool = charges >= 5
		var selected: bool = (
			pending_special_action == "soul_recall"
		)

		var blocked: bool = (
			battle_finished
			or active.has_oblivion()
			or active.is_silenced()
			or (action_in_progress and not selected)
		)

		var action_data: Dictionary = {
			"name": "Soul Recall",
			"badge": (
                "ACTIVE"
				if unlocked and not blocked
				else "LOCKED"
			),
			"summary": "Calls a fallen ally back from beyond the veil.",
			"effects": [
				{
					"kind": "special",
					"text": "Consumes [b]5 Soul Charges[/b] to revive a selected fallen ally with [b]50% HP[/b] and [b]100% Action Gauge[/b]."
				},
				{
					"kind": "special",
					"text": "A [color=#d9a6ff]Banished[/color] ally cannot be revived."
				}
			]
		}

		action_button.visible = true
		action_button.set_hud_role("active")
		action_button.set_target_selected(selected)
		action_button.set_cooldown_turns(0)
		action_button.set_tooltip_passive(action_data)
		action_button.mouse_default_cursor_shape = (
			Control.CURSOR_POINTING_HAND
			if unlocked and (selected or not blocked)
			else Control.CURSOR_ARROW
		)

		# Soul Charges are already displayed in the monster HUD.
		# Availability is conveyed by the button's visual state.
		action_button.text = "RECALL"
		_update_skill_icon(
			action_button, str(active.monster_id), "soul_recall"
		)
		if action_button.has_skill_icon():
			action_button.text = ""

		if selected:
			action_button.set_visual_state("active_selected")
			_set_action_button_state(action_button, false)
		elif unlocked:
			action_button.set_visual_state(
				"active_locked" if blocked else "active_ready"
			)
			# Keep tooltip hover available when blocked.
			_set_action_button_state(
				action_button,
				blocked,
				false
			)
		else:
			action_button.set_visual_state("active_locked")
			_set_action_button_state(
				action_button,
				true,
				false
			)

		visible_count += 1


func _on_soul_recall_button_2_pressed() -> void:
	_on_soul_recall_pressed(1)


func _on_soul_recall_button_3_pressed() -> void:
	_on_soul_recall_pressed(2)


func _on_soul_recall_pressed(button_index: int) -> void:
	if (
		battle_finished
		or battle_controller.active_monster == null
		or battle_controller.active_monster not in allies
	):
		return

	var active = battle_controller.active_monster

	if (
		active.monster_id != "dullahan_aether"
		or active.resonance < 2
		or button_index != mini(
			2,
			active.passive_tooltips.size()
		)
	):
		return

	# The action can be selected even without a fallen ally. Clicking
	# it again cancels targeting, leaving other skills usable.
	if pending_special_action == "soul_recall":
		pending_special_action = ""
		set_revive_target_selection(false)
		action_in_progress = false
		update_skill_buttons()
		turn_label.text = "Soul Recall selection cancelled"
		return

	if (
		action_in_progress
		or active.get_combat_resource("soul_charges") < 5
		or active.has_oblivion()
		or active.is_silenced()
		or not battle_controller.can_use_soul_recall(active)
	):
		return

	action_in_progress = true
	pending_skill_slot = 0
	pending_special_action = "soul_recall"
	set_target_selection(false)
	set_revive_target_selection(true)
	update_skill_buttons()

	var fallen_allies: int = 0

	for ally in allies:
		if not ally.is_alive() and not ally.banished:
			fallen_allies += 1

	if fallen_allies > 0:
		turn_label.text = "Choose a fallen ally (Soul Recall to cancel)"
	else:
		turn_label.text = (
            "No fallen allies - Soul Recall to cancel"
		)

func set_target_selection(enabled: bool) -> void:
	for hud in enemy_huds:
		hud.set_target_mode(
			"single" if enabled else "none"
		)


func set_revive_target_selection(enabled: bool) -> void:
	for hud in ally_huds:
		hud.set_target_mode(
			"dead_ally" if enabled else "none"
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
	for button in [skill_1_button, skill_2_button, skill_3_button]:
		button.set_target_selected(false)
		_set_action_button_state(button, true)


func finish_battle(player_won: bool) -> void:
	battle_finished = true
	action_in_progress = true
	pending_skill_slot = 0

	disable_skill_buttons()
	set_target_selection(false)
	set_revive_target_selection(false)
	set_aoe_preview(false)
	update_battle_ui()

	turn_label.text = (
		"Victory!" if player_won else "Defeat!"
	)
