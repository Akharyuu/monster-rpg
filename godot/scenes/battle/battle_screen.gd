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
var action_in_progress := true


func _ready() -> void:
    allies = [
        PrototypeFactoryScript.create_level_one_monster(
            "drake_igneous",
            5
        ),
        PrototypeFactoryScript.create_level_one_monster(
            "drake_abyssal",
            5
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

    # Temporary training dummies for resonance testing.
    # This only affects this battle scene, not canonical monster data.
    for enemy in enemies:
        enemy.max_health = 100000
        enemy.health = enemy.max_health

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

    action_in_progress = true
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
    _update_passive_button()

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
            button.set_tooltip_skill(null)
            button.disabled = true
            continue

        var skill = battle_controller.active_monster.get_skill(index + 1)

        if skill == null:
            button.text = "-"
            button.set_tooltip_skill(null)
            button.disabled = true
            continue

        button.text = skill.skill_name
        button.set_tooltip_skill(skill)

        if skill.current_cooldown > 0:
            button.text += "\nCD %d" % (
                skill.current_cooldown
            )

        var blocked_by_silence: bool = (
            battle_controller.active_monster.is_silenced()
            and index > 0
        )

        button.disabled = (
            battle_finished
            or blocked_by_silence
            or not skill.is_available()
        )


func _update_passive_button() -> void:
    var buttons := [
        passive_button,
        passive_button_2
    ]

    for button in buttons:
        button.text = "PASSIVE"
        button.set_tooltip_passive({})
        button.visible = false

    if (
        battle_controller.active_monster == null
        or battle_controller.active_monster not in allies
    ):
        return

    var passive_list: Array = (
        battle_controller.active_monster.passive_tooltips
    )

    if passive_list.is_empty():
        var legacy: Dictionary = (
            battle_controller.active_monster.passive_tooltip
        )

        if not legacy.is_empty():
            passive_list = [legacy]

    for index in range(
        mini(buttons.size(), passive_list.size())
    ):
        var button = buttons[index]
        var passive_data: Dictionary = passive_list[index]

        button.visible = true
        button.text = str(
            passive_data.get("name", "PASSIVE")
        )
        button.set_tooltip_passive(passive_data)


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
    action_in_progress = true
    pending_skill_slot = 0

    disable_skill_buttons()
    set_target_selection(false)
    set_aoe_preview(false)
    update_battle_ui()

    turn_label.text = (
        "Victory!" if player_won else "Defeat!"
    )
