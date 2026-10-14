class_name MonsterBattleHUD
extends Control

signal target_pressed

@onready var turn_indicator: Panel = $"Turn Indicator"
@onready var target_highlight: Panel = $"Target Highlight"
@onready var attribute_label: Label = $"Attribute"
@onready var name_label: Label = $"Name"
@onready var level_label: Label = $"Level"
@onready var hp_bar: ProgressBar = $"HP"
@onready var action_gauge: ProgressBar = $"AG"
@onready var status_container: HBoxContainer = $"Status"
@onready var target_button: Button = $"Target Button"

var bound_monster
var is_enemy := false
var target_mode: String = "none"


func _ready() -> void:
    target_button.pressed.connect(
        func(): target_pressed.emit()
    )


func bind_monster(monster, enemy_side: bool) -> void:
    bound_monster = monster
    is_enemy = enemy_side

    name_label.text = monster.monster_name
    level_label.text = "Lv. %d" % monster.level

    _update_attribute(
        monster.attribute
    )

    hp_bar.max_value = monster.max_health
    action_gauge.max_value = 100.0

    _update_turn_style()
    _update_target_style()
    refresh(false)


func refresh(is_active: bool) -> void:
    if bound_monster == null:
        return

    name_label.text = bound_monster.monster_name
    level_label.text = "Lv. %d" % bound_monster.level

    hp_bar.value = bound_monster.health
    action_gauge.value = (
        bound_monster.action_gauge * 100.0
    )

    turn_indicator.visible = (
        is_active
        and bound_monster.is_alive()
    )

    modulate.a = (
        1.0 if bound_monster.is_alive() else 0.35
    )

    if not bound_monster.is_alive():
        target_button.visible = false
        target_button.disabled = true
        target_highlight.visible = false

    _populate_statuses()


func set_target_enabled(enabled: bool) -> void:
    set_target_mode(
        "single" if enabled else "none"
    )


func set_target_mode(mode: String) -> void:
    target_mode = mode

    var can_target := (
        bound_monster != null
        and bound_monster.is_alive()
        and is_enemy
    )

    target_button.disabled = (
        target_mode != "single"
        or not can_target
    )

    target_button.visible = (
        target_mode == "single"
        and can_target
    )

    target_highlight.visible = (
        target_mode != "none"
        and can_target
    )

    _update_target_style()


func _update_target_style() -> void:
    var style := StyleBoxFlat.new()

    if target_mode == "aoe":
        style.bg_color = Color(0.78, 0.30, 0.12, 0.12)
        style.border_color = Color(1.0, 0.58, 0.20, 1.0)
    else:
        style.bg_color = Color(0.85, 0.75, 0.18, 0.10)
        style.border_color = Color(1.0, 0.90, 0.28, 1.0)

    style.border_width_left = 3
    style.border_width_top = 3
    style.border_width_right = 3
    style.border_width_bottom = 3

    style.corner_radius_top_left = 10
    style.corner_radius_top_right = 10
    style.corner_radius_bottom_left = 10
    style.corner_radius_bottom_right = 10

    target_highlight.add_theme_stylebox_override(
        "panel",
        style
    )


func _update_attribute(attribute: String) -> void:
    var display_name: String = attribute.to_upper()
    var attribute_color := Color.WHITE

    match attribute:
        "igneous":
            display_name = "IGN"
            attribute_color = Color(1.0, 0.42, 0.22)
        "abyssal":
            display_name = "ABY"
            attribute_color = Color(0.30, 0.56, 1.0)
        "storm":
            display_name = "STM"
            attribute_color = Color(0.90, 0.82, 0.24)
        "aether":
            display_name = "AET"
            attribute_color = Color(0.72, 0.58, 1.0)
        "void":
            display_name = "VOI"
            attribute_color = Color(0.72, 0.40, 0.90)

    attribute_label.text = "◆ %s" % display_name
    attribute_label.add_theme_color_override(
        "font_color",
        attribute_color
    )


func _update_turn_style() -> void:
    var style := StyleBoxFlat.new()

    if is_enemy:
        style.bg_color = Color(0.55, 0.18, 0.16, 0.12)
        style.border_color = Color(1.0, 0.5, 0.35, 1.0)
    else:
        style.bg_color = Color(0.10, 0.45, 0.55, 0.12)
        style.border_color = Color(0.35, 0.9, 1.0, 1.0)

    style.border_width_left = 2
    style.border_width_top = 2
    style.border_width_right = 2
    style.border_width_bottom = 2

    style.corner_radius_top_left = 8
    style.corner_radius_top_right = 8
    style.corner_radius_bottom_left = 8
    style.corner_radius_bottom_right = 8

    turn_indicator.add_theme_stylebox_override(
        "panel",
        style
    )


func _status_short_name(effect_id: String) -> String:
    match effect_id:
        "burn":
            return "BRN"
        "defense_break":
            return "DEF↓"
        "attack_break":
            return "ATK↓"
        "speed_break":
            return "SPD↓"
        "attack_up":
            return "ATK↑"
        "defense_up":
            return "DEF↑"
        "speed_up":
            return "SPD↑"
        "immunity":
            return "IMM"
        "shield":
            return "SHD"
        "stun":
            return "STN"
        "freeze":
            return "FRZ"
        "silence":
            return "SIL"
        _:
            return effect_id.left(4).to_upper()


func _create_status_badge(effect) -> Label:
    var badge := Label.new()

    badge.custom_minimum_size = Vector2(58.0, 25.0)
    badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    badge.vertical_alignment = VERTICAL_ALIGNMENT_CENTER

    var text: String = _status_short_name(
        str(effect.effect_id)
    )

    if effect.max_stacks > 1:
        text += " x%d" % effect.stacks

    badge.text = "%s · %d" % [
        text,
        effect.remaining_turns
    ]

    badge.tooltip_text = "%s — %d turn(s)" % [
        effect.effect_name,
        effect.remaining_turns
    ]

    var style := StyleBoxFlat.new()

    if effect.effect_type == "buff":
        style.bg_color = Color(0.20, 0.46, 0.78, 0.92)
    elif effect.effect_id == "burn":
        style.bg_color = Color(0.78, 0.25, 0.12, 0.92)
    else:
        style.bg_color = Color(0.65, 0.22, 0.18, 0.92)

    style.corner_radius_top_left = 5
    style.corner_radius_top_right = 5
    style.corner_radius_bottom_left = 5
    style.corner_radius_bottom_right = 5

    badge.add_theme_stylebox_override(
        "normal",
        style
    )

    return badge


func _populate_statuses() -> void:
    for child in status_container.get_children():
        child.queue_free()

    for buff in bound_monster.buffs:
        status_container.add_child(
            _create_status_badge(buff)
        )

    for debuff in bound_monster.debuffs:
        status_container.add_child(
            _create_status_badge(debuff)
        )
