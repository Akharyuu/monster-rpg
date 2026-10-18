class_name MonsterBattleHUD
extends Control

signal target_pressed

@onready var turn_indicator: Panel = $"Turn Indicator"
@onready var target_highlight: Panel = $"Target Highlight"
@onready var target_prompt: Label = $"Target Prompt"
@onready var attribute_label: Label = $"Attribute"
@onready var name_label: Label = $"Name"
@onready var level_label: Label = $"Level"
@onready var hp_bar: ProgressBar = $"HP"
@onready var action_gauge: ProgressBar = $"AG"
@onready var battle_state_container: HBoxContainer = $"Battle States"
@onready var status_container: HBoxContainer = $"Status"
@onready var target_button: Button = $"Target Button"
@onready var sprite_placeholder = $"Sprite Placeholder"
@onready var monster_sprite: TextureRect = $"Monster Sprite"

# Pixel-art previews are static during this visual prototype.
const ALLY_SPRITES := {
    "drake_igneous": "res://assets/monster_sprites/drake_igneous_back.png"
}
const ENEMY_SPRITES := {
    "drake_igneous": "res://assets/monster_sprites/drake_igneous_front.png"
}

# 125% display scale, with each sprite's original center preserved.
const ALLY_PREVIEW_SIZE := Vector2(300.0, 290.0)
const ALLY_PREVIEW_POSITION := Vector2(-81.0, -68.0)
const ENEMY_FRONT_PREVIEW_SIZE := Vector2(281.25, 272.5)
const ENEMY_FRONT_PREVIEW_POSITION := Vector2(-72.625, -57.25)


var bound_monster
var is_enemy := false
var target_mode: String = "none"

# Shared first-frame UI artwork. An individual image is cropped from the
# 6x6 sheet and cached once, rather than keeping 36 frames in the GPU.
const IGNEOUS_BAR_DIRECTORY := "res://assets/ui"
const IGNEOUS_BAR_DATA := "res://assets/ui/sprite-max-px-frames-36-rows-6-cols-6.json"
const IGNEOUS_BAR_FALLBACK_IMAGE := "sprite-max-px-frames-36-rows-6-cols-6.png"
const IGNEOUS_BAR_COLUMNS := 6
const IGNEOUS_BAR_ROWS := 6
const IGNEOUS_BAR_DISPLAY_SIZE := Vector2(284.0, 72.0)
const IGNEOUS_BAR_DISPLAY_POSITION := Vector2(-73.0, -59.0)

static var _igneous_bar_attempted: bool = false
static var _igneous_bar_texture: Texture2D
var _igneous_bar_art: TextureRect


func _ready() -> void:
    target_button.pressed.connect(
        func(): target_pressed.emit()
    )


func bind_monster(monster, enemy_side: bool) -> void:
    bound_monster = monster
    is_enemy = enemy_side
    sprite_placeholder.call(
        "configure", monster.family, monster.attribute, enemy_side
    )
    _configure_monster_sprite()


    name_label.text = monster.monster_name
    level_label.text = "Lv. %d" % monster.level

    _update_attribute(
        monster.attribute
    )

    hp_bar.max_value = monster.max_health
    action_gauge.max_value = 100.0

    _update_turn_style()
    _update_target_style()
    _style_bars()
    _configure_attribute_bar_art()
    refresh(false)


func _apply_sprite_layout(preview_size: Vector2, preview_position: Vector2) -> void:
    monster_sprite.size = preview_size
    monster_sprite.position = preview_position


func _configure_monster_sprite() -> void:
    monster_sprite.visible = false
    monster_sprite.texture = null
    sprite_placeholder.visible = true

    if bound_monster == null:
        return

    var sprite_map: Dictionary = (
        ENEMY_SPRITES if is_enemy else ALLY_SPRITES
    )
    var sprite_path: String = str(
        sprite_map.get(str(bound_monster.monster_id), "")
    )
    if sprite_path.is_empty():
        return

    if not ResourceLoader.exists(sprite_path, "Texture2D"):
        push_warning("Monster artwork not found: %s" % sprite_path)
        return

    var texture: Texture2D = load(sprite_path) as Texture2D
    if texture == null:
        push_warning("Cannot load monster artwork: %s" % sprite_path)
        return

    monster_sprite.texture = texture
    if is_enemy:
        _apply_sprite_layout(
            ENEMY_FRONT_PREVIEW_SIZE,
            ENEMY_FRONT_PREVIEW_POSITION
        )
    else:
        _apply_sprite_layout(
            ALLY_PREVIEW_SIZE,
            ALLY_PREVIEW_POSITION
        )
    monster_sprite.visible = true
    sprite_placeholder.visible = false


# Igneous monsters temporarily use a static preview of the themed HUD.
# All live HP/Action Gauge values continue updating in the hidden ProgressBars.
# Later we can animate their fills without touching the combat/controller API.
func _configure_attribute_bar_art() -> void:
    if _igneous_bar_art == null:
        _igneous_bar_art = TextureRect.new()
        _igneous_bar_art.name = "Igneous HP and Action Gauge"
        _igneous_bar_art.z_index = 10
        _igneous_bar_art.mouse_filter = Control.MOUSE_FILTER_IGNORE
        _igneous_bar_art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
        _igneous_bar_art.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
        _igneous_bar_art.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
        add_child(_igneous_bar_art)
        _igneous_bar_art.position = IGNEOUS_BAR_DISPLAY_POSITION
        _igneous_bar_art.size = IGNEOUS_BAR_DISPLAY_SIZE

    var use_art: bool = false
    if bound_monster != null and str(bound_monster.attribute) == "igneous":
        var artwork: Texture2D = _get_igneous_bar_texture()
        if artwork != null:
            _igneous_bar_art.texture = artwork
            use_art = true

    _igneous_bar_art.visible = use_art
    hp_bar.visible = not use_art
    action_gauge.visible = not use_art


# The source JSON provides frame coordinates for the original 6552x3264
# texture. Some image exports are resized, so also support a uniformly
# scaled 6x6 sheet by calculating its actual first-cell dimensions.
static func _get_igneous_bar_texture() -> Texture2D:
    if _igneous_bar_attempted:
        return _igneous_bar_texture
    _igneous_bar_attempted = true

    if not FileAccess.file_exists(IGNEOUS_BAR_DATA):
        push_warning("Igneous UI sprite metadata not found: %s" % IGNEOUS_BAR_DATA)
        return null

    var metadata: Variant = JSON.parse_string(
        FileAccess.get_file_as_string(IGNEOUS_BAR_DATA)
    )
    if not (metadata is Dictionary):
        push_warning("Igneous UI sprite JSON could not be parsed")
        return null

    var meta: Dictionary = metadata.get("meta", {})
    var image_name: String = str(meta.get("image", IGNEOUS_BAR_FALLBACK_IMAGE)).get_file()
    if not image_name.ends_with(".png"):
        push_warning("Igneous UI metadata does not name a PNG")
        return null

    var image_path: String = IGNEOUS_BAR_DIRECTORY.path_join(image_name)
    if not FileAccess.file_exists(image_path):
        # Accept the common '(1)' filename from duplicated downloads.
        var alternate: String = IGNEOUS_BAR_DIRECTORY.path_join(
            image_name.get_basename() + "(1).png"
        )
        if FileAccess.file_exists(alternate):
            image_path = alternate
        else:
            push_warning("Igneous UI sprite PNG not found: %s" % image_path)
            return null

    var sheet: Image = Image.load_from_file(image_path)
    if sheet == null or sheet.is_empty():
        push_warning("Could not open Igneous UI spritesheet: %s" % image_path)
        return null

    var width: int = sheet.get_width()
    var height: int = sheet.get_height()
    if width < IGNEOUS_BAR_COLUMNS or height < IGNEOUS_BAR_ROWS:
        push_warning("Igneous UI spritesheet is too small")
        return null

    var cell := Rect2i(
        0, 0,
        width / IGNEOUS_BAR_COLUMNS,
        height / IGNEOUS_BAR_ROWS
    )
    var original_size: Dictionary = meta.get("size", {})
    var records: Dictionary = metadata.get("frames", {})
    var first_frame: Dictionary = records.get("frame_000", {})
    var source_rect: Dictionary = first_frame.get("frame", {})

    if (
        int(original_size.get("w", -1)) == width
        and int(original_size.get("h", -1)) == height
        and not source_rect.is_empty()
    ):
        cell = Rect2i(
            int(source_rect.get("x", 0)),
            int(source_rect.get("y", 0)),
            int(source_rect.get("w", 0)),
            int(source_rect.get("h", 0))
        )

    if (
        cell.size.x <= 0 or cell.size.y <= 0
        or cell.position.x < 0 or cell.position.y < 0
        or cell.end.x > width or cell.end.y > height
    ):
        push_warning("Invalid Igneous UI frame boundaries")
        return null

    var frame: Image = sheet.get_region(cell)
    var visible_area: Rect2i = frame.get_used_rect()
    if visible_area.size.x <= 0 or visible_area.size.y <= 0:
        push_warning("Igneous UI frame is empty")
        return null

    # Trim the large transparent space above/below the actual metal frame.
    var painted_frame: Image = frame.get_region(visible_area)
    _igneous_bar_texture = ImageTexture.create_from_image(painted_frame)
    return _igneous_bar_texture


func refresh(is_active: bool) -> void:
    if bound_monster == null:
        return

    name_label.text = bound_monster.monster_name
    level_label.text = "Lv. %d" % bound_monster.level

    hp_bar.value = bound_monster.health
    hp_bar.tooltip_text = "%d / %d HP" % [
        bound_monster.health, bound_monster.max_health
    ]
    action_gauge.value = (
        bound_monster.action_gauge * 100.0
    )
    action_gauge.tooltip_text = "Action Gauge %.0f%%" % (
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
        target_prompt.visible = false
        target_highlight.visible = false

    _populate_battle_states()
    _populate_statuses()


func set_target_enabled(enabled: bool) -> void:
    set_target_mode(
        "single" if enabled else "none"
    )


func set_target_mode(mode: String) -> void:
    target_mode = mode

    var can_target := false

    if target_mode == "single":
        can_target = (
            bound_monster != null
            and bound_monster.is_alive()
            and is_enemy
        )
    elif target_mode == "team":
        # The parent scene assigns this mode only to the selected side.
        can_target = bound_monster != null and bound_monster.is_alive()
    elif target_mode in ["single_ally", "self"]:
        can_target = (
            bound_monster != null
            and bound_monster.is_alive()
            and not is_enemy
        )
    elif target_mode == "dead_ally":
        can_target = (
            bound_monster != null
            and not bound_monster.is_alive()
            and not bound_monster.banished
            and not is_enemy
        )

    target_button.disabled = not can_target
    target_button.visible = can_target
    target_prompt.visible = can_target
    target_highlight.visible = can_target

    if target_mode == "dead_ally":
        target_prompt.text = "REVIVE"
    elif target_mode == "team":
        target_prompt.text = "TEAM"
    elif target_mode == "self":
        target_prompt.text = "SELF"
    else:
        target_prompt.text = "TARGET"

    _update_target_style()


func _update_target_style() -> void:
    var style := StyleBoxFlat.new()

    if target_mode in ["aoe", "team"]:
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
    var attribute_color := Color.WHITE

    match attribute:
        "igneous":
            attribute_color = Color(1.0, 0.42, 0.22)
        "abyssal":
            attribute_color = Color(0.30, 0.56, 1.0)
        "storm":
            attribute_color = Color(0.90, 0.82, 0.24)
        "aether":
            attribute_color = Color(1.0, 0.93, 0.68)
        "void":
            attribute_color = Color(0.72, 0.40, 0.90)

    attribute_label.text = "◆"
    attribute_label.tooltip_text = attribute.capitalize()
    attribute_label.add_theme_color_override(
        "font_color", attribute_color
    )


func _style_bars() -> void:
    var background := StyleBoxFlat.new()
    background.bg_color = Color(0.06, 0.09, 0.12, 0.90)
    background.corner_radius_top_left = 3
    background.corner_radius_top_right = 3
    background.corner_radius_bottom_left = 3
    background.corner_radius_bottom_right = 3

    var health_fill := StyleBoxFlat.new()
    health_fill.bg_color = (
        Color(0.93, 0.36, 0.39, 1.0)
        if is_enemy
        else Color(0.28, 0.84, 0.57, 1.0)
    )
    health_fill.corner_radius_top_left = 3
    health_fill.corner_radius_top_right = 3
    health_fill.corner_radius_bottom_left = 3
    health_fill.corner_radius_bottom_right = 3

    var gauge_fill := StyleBoxFlat.new()
    gauge_fill.bg_color = Color(0.91, 0.75, 0.39, 1.0)
    gauge_fill.corner_radius_top_left = 2
    gauge_fill.corner_radius_top_right = 2
    gauge_fill.corner_radius_bottom_left = 2
    gauge_fill.corner_radius_bottom_right = 2

    hp_bar.add_theme_stylebox_override("background", background)
    hp_bar.add_theme_stylebox_override("fill", health_fill)
    action_gauge.add_theme_stylebox_override(
        "background", background
    )
    action_gauge.add_theme_stylebox_override("fill", gauge_fill)


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
        "poison":
            return "PSN"
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
        "invincibility":
            return "INV"
        "shield":
            return "SHD"
        "regrowth":
            return "RGW"
        "stun":
            return "STN"
        "freeze":
            return "FRZ"
        "silence":
            return "SIL"
        "oblivion":
            return "OBL"
        "heal_block":
            return "HEAL✕"
        "vulnerability":
            return "VULN"
        _:
            return effect_id.left(4).to_upper()


func _create_status_badge(effect) -> Label:
    var badge := Label.new()

    badge.custom_minimum_size = Vector2(25.0, 12.0)
    badge.add_theme_font_size_override("font_size", 7)
    badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    badge.vertical_alignment = VERTICAL_ALIGNMENT_CENTER

    var text: String = _status_short_name(
        str(effect.effect_id)
    )

    if effect.max_stacks > 1:
        text += " x%d" % effect.stacks

    badge.text = "%s%d" % [text.left(3), effect.remaining_turns]

    badge.tooltip_text = "%s — %d turn(s)" % [
        effect.effect_name,
        effect.remaining_turns
    ]

    var style := StyleBoxFlat.new()

    if effect.effect_type == "buff":
        style.bg_color = Color(0.20, 0.46, 0.78, 0.92)
    elif effect.effect_id == "burn":
        style.bg_color = Color(0.78, 0.25, 0.12, 0.92)
    elif effect.effect_id == "poison":
        style.bg_color = Color(0.42, 0.24, 0.62, 0.92)
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


func _battle_state_display_name(state_id: String) -> String:
    match state_id:
        "frozen_scales":
            return "Frozen Scales"
        "soul_charges":
            return "Soul Charges"
        "voidborn":
            return "Voidborn"
        "bottomless_hunger":
            return "Bottomless Hunger"
        "named":
            return "Named"
        "headless":
            return "Headless"
        "banished":
            return "Banished"
        _:
            return state_id.replace("_", " ").capitalize()


func _create_battle_state_badge(
    state_id: String,
    value,
    maximum = null
) -> Label:
    var badge := Label.new()

    badge.custom_minimum_size = Vector2(46.0, 12.0)
    badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    badge.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    badge.add_theme_font_size_override(
        "font_size",
        7
    )

    var display_name: String = (
        _battle_state_display_name(state_id)
    )

    display_name = "SOUL" if state_id == "soul_charges" else display_name.left(4).to_upper()

    if maximum != null:
        badge.text = "%s %d/%d" % [
            display_name,
            int(value),
            int(maximum)
        ]
    elif value is bool:
        badge.text = display_name
    else:
        badge.text = "%s %s" % [
            display_name,
            str(value)
        ]

    badge.tooltip_text = badge.text

    var style := StyleBoxFlat.new()
    style.bg_color = Color(0.22, 0.22, 0.34, 0.92)
    style.border_color = Color(0.58, 0.68, 1.0, 0.95)
    style.border_width_left = 1
    style.border_width_top = 1
    style.border_width_right = 1
    style.border_width_bottom = 1
    style.corner_radius_top_left = 5
    style.corner_radius_top_right = 5
    style.corner_radius_bottom_left = 5
    style.corner_radius_bottom_right = 5

    badge.add_theme_stylebox_override(
        "normal",
        style
    )

    return badge


func _populate_battle_states() -> void:
    for child in battle_state_container.get_children():
        child.queue_free()

    for resource_id in bound_monster.combat_resources:
        var value = bound_monster.combat_resources[
            resource_id
        ]

        var maximum = (
            bound_monster.combat_resource_maximums.get(
                resource_id,
                null
            )
        )

        battle_state_container.add_child(
            _create_battle_state_badge(
                str(resource_id),
                value,
                maximum
            )
        )

    for state_id in bound_monster.special_states:
        var state_value = bound_monster.special_states[
            state_id
        ]

        if state_value is bool and not state_value:
            continue

        battle_state_container.add_child(
            _create_battle_state_badge(
                str(state_id),
                state_value
            )
        )

    if bound_monster.banished:
        battle_state_container.add_child(
            _create_battle_state_badge(
                "banished",
                true
            )
        )


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


func play_attack_feedback() -> void:
    if bound_monster == null or not bound_monster.is_alive():
        return

    var start_position: Vector2 = position
    var direction: float = 1.0 if is_enemy else -1.0
    var attack_position := start_position + Vector2(
        0.0, 12.0 * direction
    )

    var tween := create_tween()
    tween.set_trans(Tween.TRANS_QUAD)
    tween.set_ease(Tween.EASE_OUT)

    tween.tween_property(
        self,
        "position",
        attack_position,
        0.09
    )

    tween.tween_property(
        self,
        "position",
        start_position,
        0.13
    )

    await tween.finished


func play_damage_feedback(
    damage: int,
    critical: bool = false,
    is_dot: bool = false
) -> void:
    if damage <= 0:
        return

    var current_alpha: float = modulate.a
    var flash_color := Color(
        1.0,
        0.38 if not is_dot else 0.58,
        0.38 if not is_dot else 0.18,
        current_alpha
    )

    var flash_tween := create_tween()
    flash_tween.tween_property(
        self,
        "modulate",
        flash_color,
        0.05
    )
    flash_tween.tween_property(
        self,
        "modulate",
        Color(1.0, 1.0, 1.0, current_alpha),
        0.16
    )

    var damage_label := Label.new()
    damage_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
    damage_label.z_index = 20
    damage_label.text = "-%d" % damage
    damage_label.horizontal_alignment = (
        HORIZONTAL_ALIGNMENT_CENTER
    )

    if critical:
        damage_label.text += "  CRIT!"
        damage_label.add_theme_font_size_override(
            "font_size",
            24
        )
        damage_label.add_theme_color_override(
            "font_color",
            Color(1.0, 0.82, 0.20)
        )
    elif is_dot:
        damage_label.add_theme_font_size_override(
            "font_size",
            19
        )
        damage_label.add_theme_color_override(
            "font_color",
            Color(1.0, 0.48, 0.16)
        )
    else:
        damage_label.add_theme_font_size_override(
            "font_size",
            20
        )
        damage_label.add_theme_color_override(
            "font_color",
            Color(1.0, 0.32, 0.26)
        )

    add_child(damage_label)

    damage_label.position = Vector2(-11.0, 66.0)
    damage_label.size = Vector2(160.0, 26.0)

    var label_start: Vector2 = damage_label.position
    var label_end := label_start + Vector2(
        0.0,
        -34.0
    )

    var number_tween := create_tween()
    number_tween.set_parallel(true)

    number_tween.tween_property(
        damage_label,
        "position",
        label_end,
        0.55
    )

    number_tween.tween_property(
        damage_label,
        "modulate:a",
        0.0,
        0.55
    )

    await number_tween.finished
    damage_label.queue_free()


func play_status_feedback(
    text_value: String,
    feedback_type: String = "debuff"
) -> void:
    var status_label := Label.new()

    status_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
    status_label.z_index = 21
    status_label.text = text_value
    status_label.horizontal_alignment = (
        HORIZONTAL_ALIGNMENT_CENTER
    )
    status_label.add_theme_font_size_override(
        "font_size",
        18
    )

    match feedback_type:
        "burn":
            status_label.add_theme_color_override(
                "font_color",
                Color(1.0, 0.48, 0.16)
            )
        "resist":
            status_label.add_theme_color_override(
                "font_color",
                Color(0.72, 0.82, 1.0)
            )
        "buff":
            status_label.add_theme_color_override(
                "font_color",
                Color(0.42, 0.78, 1.0)
            )
        _:
            status_label.add_theme_color_override(
                "font_color",
                Color(1.0, 0.42, 0.42)
            )

    add_child(status_label)

    status_label.position = Vector2(-11.0, 90.0)
    status_label.size = Vector2(160.0, 24.0)

    var start_position: Vector2 = status_label.position
    var end_position := start_position + Vector2(
        0.0,
        -24.0
    )

    var tween := create_tween()
    tween.set_parallel(true)

    tween.tween_property(
        status_label,
        "position",
        end_position,
        0.50
    )

    tween.tween_property(
        status_label,
        "modulate:a",
        0.0,
        0.50
    )

    await tween.finished
    status_label.queue_free()
