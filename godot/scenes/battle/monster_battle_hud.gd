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

# Static artwork for the allied team (back view until its idle is ready).
const ALLY_SPRITES := {
    "drake_igneous": "res://assets/monster_sprites/drake_igneous.png"
}

# Atlas metadata and image are optional local assets. When missing, the
# existing static sprite (or the placeholder) is used instead.
const ENEMY_FRONT_IDLE_ANIMATIONS := {
    "drake_igneous": {
        "image": "res://assets/monster_sprites/drake_igneous_idle_front.png",
        "metadata": "res://assets/monster_sprites/drake_igneous_idle_front.json"
    }
}

# Local layout coordinates of the compact 138 x 185 monster HUD.
const ALLY_PREVIEW_SIZE := Vector2(240.0, 232.0)
const ALLY_PREVIEW_POSITION := Vector2(-51.0, -39.0)

const ENEMY_FRONT_PREVIEW_SIZE := Vector2(225.0, 218.0)
const ENEMY_FRONT_PREVIEW_POSITION := Vector2(-44.5, -30.0)


var bound_monster
var is_enemy := false
var target_mode: String = "none"
var _idle_atlas_texture: AtlasTexture
var _idle_frames: Array = []
var _idle_frame_index: int = 0
var _idle_elapsed_ms: float = 0.0



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
    refresh(false)


func _apply_sprite_layout(preview_size: Vector2, preview_position: Vector2) -> void:
    monster_sprite.size = preview_size
    monster_sprite.position = preview_position


func _configure_monster_sprite() -> void:
    _idle_atlas_texture = null
    _idle_frames.clear()
    _idle_frame_index = 0
    _idle_elapsed_ms = 0.0

    monster_sprite.visible = false
    monster_sprite.texture = null
    sprite_placeholder.visible = true

    if bound_monster == null:
        return

    # The front-view idle belongs to the enemy side only.
    if is_enemy:
        _configure_idle_animation()
        return

    # Allies retain the static back-side placeholder artwork.
    var sprite_path: String = str(
        ALLY_SPRITES.get(str(bound_monster.monster_id), "")
    )
    if sprite_path.is_empty():
        return

    if not ResourceLoader.exists(sprite_path, "Texture2D"):
        push_warning("Ally artwork not found: %s" % sprite_path)
        return

    var texture: Texture2D = load(sprite_path) as Texture2D
    if texture == null:
        push_warning("Cannot load ally artwork: %s" % sprite_path)
        return

    monster_sprite.texture = texture
    _apply_sprite_layout(
        ALLY_PREVIEW_SIZE,
        ALLY_PREVIEW_POSITION
    )
    monster_sprite.visible = true
    sprite_placeholder.visible = false


# Read Ludo's frame rectangles and per-frame durations directly from JSON.
# This avoids assuming a fixed FPS or sprite sheet column count.
func _configure_idle_animation() -> bool:
    var monster_id: String = str(bound_monster.monster_id)
    if not ENEMY_FRONT_IDLE_ANIMATIONS.has(monster_id):
        return false

    var paths: Dictionary = ENEMY_FRONT_IDLE_ANIMATIONS[monster_id]
    var image_path: String = str(paths["image"])
    var metadata_path: String = str(paths["metadata"])

    if not ResourceLoader.exists(image_path, "Texture2D"):
        return false
    if not FileAccess.file_exists(metadata_path):
        return false

    var sheet: Texture2D = load(image_path) as Texture2D
    if sheet == null:
        return false

    var json_text: String = FileAccess.get_file_as_string(
        metadata_path
    )
    var document: Variant = JSON.parse_string(json_text)
    if not (document is Dictionary):
        push_warning("Invalid idle animation JSON: %s" % metadata_path)
        return false

    var definitions: Variant = document.get("frames", {})
    if not (definitions is Dictionary) or definitions.is_empty():
        push_warning("Idle animation has no frames: %s" % metadata_path)
        return false

    var keys: Array = definitions.keys()
    keys.sort()
    var parsed_frames: Array = []
    for frame_key in keys:
        var item: Dictionary = definitions[frame_key]
        var rect: Dictionary = item.get("frame", {})
        var frame_region := Rect2(
            float(rect.get("x", 0)),
            float(rect.get("y", 0)),
            float(rect.get("w", 0)),
            float(rect.get("h", 0))
        )
        if (
            frame_region.size.x <= 0
            or frame_region.size.y <= 0
            or frame_region.end.x > sheet.get_width()
            or frame_region.end.y > sheet.get_height()
        ):
            push_warning(
                "Idle animation frame outside image: %s" % frame_key
            )
            return false
        parsed_frames.append({
            "region": frame_region,
            "duration_ms": maxf(
                1.0, float(item.get("duration", 91))
            )
        })

    _idle_frames = parsed_frames
    _idle_atlas_texture = AtlasTexture.new()
    _idle_atlas_texture.atlas = sheet
    _idle_atlas_texture.region = _idle_frames[0]["region"]
    monster_sprite.texture = _idle_atlas_texture
    _apply_sprite_layout(
        ENEMY_FRONT_PREVIEW_SIZE,
        ENEMY_FRONT_PREVIEW_POSITION
    )
    monster_sprite.visible = true
    sprite_placeholder.visible = false
    return true


func _process(delta: float) -> void:
    if _idle_atlas_texture == null or _idle_frames.is_empty():
        return

    _idle_elapsed_ms += delta * 1000.0
    var current: Dictionary = _idle_frames[_idle_frame_index]
    while _idle_elapsed_ms >= float(current["duration_ms"]):
        _idle_elapsed_ms -= float(current["duration_ms"])
        _idle_frame_index = (
            _idle_frame_index + 1
        ) % _idle_frames.size()
        current = _idle_frames[_idle_frame_index]

    _idle_atlas_texture.region = current["region"]


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

    target_prompt.text = (
        "REVIVE"
        if target_mode == "dead_ally"
        else "TARGET"
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
