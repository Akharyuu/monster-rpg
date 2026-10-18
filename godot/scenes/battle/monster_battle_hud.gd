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
const IGNEOUS_BAR_FRAME_COUNT := 36
const IGNEOUS_BAR_WIDTH := 182.4
# Width stays at its current 80% preview size. Compress the existing
# art height a further 10% independently, without moving it off the sprite.
const BAR_ORIGINAL_WIDTH := 227.2
const BAR_HEIGHT_SCALE := 0.90
const IGNEOUS_BAR_GAP := 8.0

# All monster HUDs share one texture atlas and frame timing data.
static var _igneous_bar_attempted: bool = false
static var _igneous_bar_frames: Array[Texture2D] = []
static var _igneous_bar_durations_ms: Array[float] = []
static var _igneous_bar_preview_size: Vector2 = Vector2.ZERO
static var _sprite_alpha_bounds: Dictionary = {}
var _igneous_bar_art: TextureRect
var _igneous_frame_index: int = 0
var _igneous_elapsed_ms: float = 0.0

# Abyssal artwork is the shared test frame for both teams. Its real-time
# HP/action-gauge fills are separate art layers (one material per monster).
const ABYSSAL_BAR_PATH := "res://assets/Abyssal HP bar.png"
const ABYSSAL_BAR_WIDTH := 182.4
const ABYSSAL_BAR_GAP := 8.0
const ABYSSAL_PREVIEW_SCALE := 0.90
const HP_FILL_TEXTURE: Texture2D = preload("res://assets/ui/hp_fill.png")
const GAUGE_FILL_TEXTURE: Texture2D = preload("res://assets/ui/gauge_fill.png")
const BAR_FILL_SHADER: Shader = preload("res://assets/ui/battle_bar_fill.gdshader")
# Interior slots measured against the transparent-trimmed Abyssal frame.
# These are normalized rectangles, so changing the frame size scales
# everything consistently without stretching the filling over time.
# Fills extend ~2.4 logical pixels toward the frame's right interior
# edge. Keep the left edge fixed so partial HP still drains correctly.
# A 0.0061 relative-width reduction is ~1px at this frame's 164px size.
const HP_FILL_RECT := Rect2(0.226, 0.274, 0.7369, 0.213)
const GAUGE_FILL_RECT := Rect2(0.226, 0.564, 0.7369, 0.188)
const HP_FILL_VERTICAL_OFFSET := -1.0
const ENEMY_GAUGE_VERTICAL_OFFSET := -1.0
const HP_DAMAGE_DURATION := 0.22
const HP_HEAL_DURATION := 0.35
const HP_DAMAGE_TRAIL_DELAY := 0.18
const HP_DAMAGE_TRAIL_DURATION := 0.45
const GAUGE_CHANGE_DURATION := 0.25
# Nudge the bar rows toward the battle center without moving the sprites.
const ALLY_BAR_HORIZONTAL_OFFSET := 15.0
const ENEMY_BAR_HORIZONTAL_OFFSET := -15.0
# Temporary 4v4 comparison: display Abyssal on every monster at its
# own previously established size (not the larger Igneous preview size).
# Turn off to restore element-specific artwork.
const FORCE_ABYSSAL_BAR_PREVIEW := true
static var _abyssal_bar_texture: Texture2D
static var _abyssal_bar_attempted: bool = false
var _abyssal_bar_art: TextureRect
var _hp_fill_art: TextureRect
var _hp_trail_art: TextureRect
var _gauge_fill_art: TextureRect
var _hp_fill_tween: Tween
var _hp_trail_tween: Tween
var _gauge_fill_tween: Tween
var _fills_initialized := false
var _hp_target_ratio := 1.0
var _gauge_target_ratio := 0.0


func _ready() -> void:
    target_button.pressed.connect(
        func(): target_pressed.emit()
    )


func bind_monster(monster, enemy_side: bool) -> void:
    # A HUD can be rebound during future battles; old tweens must never
    # animate a different monster's data.
    _stop_fill_tweens()
    _fills_initialized = false
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


# Use visible pixels, not the padded PNG edges, to align the bar.
# Monster Sprite is drawn using STRETCH_KEEP_ASPECT_CENTERED.
func _sprite_visual_top_center() -> Vector2:
    var fallback := Vector2(
        monster_sprite.position.x + monster_sprite.size.x / 2.0,
        monster_sprite.position.y
    )
    if not monster_sprite.visible or monster_sprite.texture == null:
        return fallback

    var texture: Texture2D = monster_sprite.texture
    var image_size: Vector2 = texture.get_size()
    if image_size.x <= 0.0 or image_size.y <= 0.0:
        return fallback

    var texture_id: String = texture.resource_path
    var used: Rect2i
    if _sprite_alpha_bounds.has(texture_id):
        used = _sprite_alpha_bounds[texture_id]
    else:
        var pixels: Image = texture.get_image()
        if pixels == null or pixels.is_empty():
            return fallback
        used = pixels.get_used_rect()
        _sprite_alpha_bounds[texture_id] = used
    if used.size.x <= 0 or used.size.y <= 0:
        return fallback

    var scale: float = minf(
        monster_sprite.size.x / image_size.x,
        monster_sprite.size.y / image_size.y
    )
    var inset: Vector2 = (monster_sprite.size - image_size * scale) / 2.0
    return Vector2(
        monster_sprite.position.x + inset.x +
        (float(used.position.x) + float(used.size.x) / 2.0) * scale,
        monster_sprite.position.y + inset.y +
        float(used.position.y) * scale
    )


func _bar_horizontal_offset() -> float:
    return ENEMY_BAR_HORIZONTAL_OFFSET if is_enemy else ALLY_BAR_HORIZONTAL_OFFSET


func _position_igneous_bar() -> void:
    if _igneous_bar_art == null:
        return
    var visual_top: Vector2 = _sprite_visual_top_center()
    _igneous_bar_art.position = Vector2(
        visual_top.x - _igneous_bar_art.size.x / 2.0 +
        _bar_horizontal_offset(),
        visual_top.y - _igneous_bar_art.size.y - IGNEOUS_BAR_GAP
    )


# Cosmetic art only: the hidden original ProgressBars still hold the
# real health and action gauge. Dynamic fill will be added separately.
func _configure_attribute_bar_art() -> void:
    if _igneous_bar_art == null:
        _igneous_bar_art = TextureRect.new()
        _igneous_bar_art.name = "Igneous HP and Action Gauge"
        _igneous_bar_art.z_index = 10
        _igneous_bar_art.mouse_filter = Control.MOUSE_FILTER_IGNORE
        _igneous_bar_art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
        _igneous_bar_art.stretch_mode = TextureRect.STRETCH_SCALE
        _igneous_bar_art.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
        add_child(_igneous_bar_art)

    if _abyssal_bar_art == null:
        _abyssal_bar_art = TextureRect.new()
        _abyssal_bar_art.name = "Abyssal HP and Action Gauge"
        _abyssal_bar_art.z_index = 10
        _abyssal_bar_art.mouse_filter = Control.MOUSE_FILTER_IGNORE
        _abyssal_bar_art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
        _abyssal_bar_art.stretch_mode = TextureRect.STRETCH_SCALE
        _abyssal_bar_art.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
        add_child(_abyssal_bar_art)

    _igneous_bar_art.visible = false
    _abyssal_bar_art.visible = false
    _igneous_bar_art.texture = null
    _abyssal_bar_art.texture = null

    var use_art: bool = false
    if bound_monster != null:
        if FORCE_ABYSSAL_BAR_PREVIEW:
            # Same original Abyssal layout for every element.
            use_art = _show_abyssal_bar()
        else:
            match str(bound_monster.attribute):
                "igneous":
                    if _load_igneous_bar_animation():
                        _igneous_frame_index = 0
                        _igneous_elapsed_ms = 0.0
                        _igneous_bar_art.texture = _igneous_bar_frames[0]
                        _igneous_bar_art.size = _igneous_bar_preview_size
                        _position_igneous_bar()
                        _igneous_bar_art.visible = true
                        use_art = true
                "abyssal":
                    use_art = _show_abyssal_bar()

    # The real ProgressBars remain the authoritative data fallback.
    hp_bar.visible = not use_art
    action_gauge.visible = not use_art
    _set_dynamic_fills_visible(
        use_art and _abyssal_bar_art.visible
    )


func _show_abyssal_bar() -> bool:
    var abyssal: Texture2D = _load_abyssal_bar()
    if abyssal == null:
        return false

    _abyssal_bar_art.texture = abyssal
    _abyssal_bar_art.size = Vector2(
        ABYSSAL_BAR_WIDTH * ABYSSAL_PREVIEW_SCALE,
        BAR_ORIGINAL_WIDTH *
        float(abyssal.get_height()) /
        float(abyssal.get_width()) * BAR_HEIGHT_SCALE *
        ABYSSAL_PREVIEW_SCALE
    )
    _position_abyssal_bar()
    _abyssal_bar_art.visible = true
    _ensure_dynamic_fills()
    _position_dynamic_fills()
    return true


# Same sprite-alignment behavior as the Igneous version.
func _position_abyssal_bar() -> void:
    if _abyssal_bar_art == null:
        return
    var visual_top: Vector2 = _sprite_visual_top_center()
    _abyssal_bar_art.position = Vector2(
        visual_top.x - _abyssal_bar_art.size.x / 2.0 +
        _bar_horizontal_offset(),
        visual_top.y - _abyssal_bar_art.size.y - ABYSSAL_BAR_GAP
    )


# Shared artwork, independent shader instances: drawing one unit's
# HP or action gauge never changes the fill of any other monster.
func _make_fill_texture(name: String, texture: Texture2D) -> TextureRect:
    var fill := TextureRect.new()
    fill.name = name
    fill.texture = texture
    fill.z_index = 11
    fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
    fill.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
    fill.stretch_mode = TextureRect.STRETCH_SCALE
    fill.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR

    var mask := ShaderMaterial.new()
    mask.shader = BAR_FILL_SHADER
    mask.set_shader_parameter("fill_ratio", 1.0)
    fill.material = mask
    add_child(fill)
    return fill


func _ensure_dynamic_fills() -> void:
    if _hp_fill_art != null:
        return
    # The delayed damage trail goes underneath the current green HP.
    _hp_trail_art = _make_fill_texture(
        "HP Damage Trail", HP_FILL_TEXTURE
    )
    _hp_trail_art.modulate = Color(1.0, 0.40, 0.25, 0.55)
    _hp_fill_art = _make_fill_texture("Current HP", HP_FILL_TEXTURE)
    _gauge_fill_art = _make_fill_texture(
        "Action Gauge Fill", GAUGE_FILL_TEXTURE
    )


func _position_dynamic_fills() -> void:
    if _hp_fill_art == null or _abyssal_bar_art == null:
        return
    var frame_pos: Vector2 = _abyssal_bar_art.position
    var frame_size: Vector2 = _abyssal_bar_art.size
    var hp_pos: Vector2 = (
        frame_pos + frame_size * HP_FILL_RECT.position +
        Vector2(0.0, HP_FILL_VERTICAL_OFFSET)
    )
    var hp_size: Vector2 = frame_size * HP_FILL_RECT.size
    for layer in [_hp_trail_art, _hp_fill_art]:
        layer.position = hp_pos
        layer.size = hp_size
    _gauge_fill_art.position = (
        frame_pos + frame_size * GAUGE_FILL_RECT.position +
        Vector2(
            0.0,
            ENEMY_GAUGE_VERTICAL_OFFSET if is_enemy else 0.0
        )
    )
    _gauge_fill_art.size = frame_size * GAUGE_FILL_RECT.size


func _set_dynamic_fills_visible(show: bool) -> void:
    if _hp_fill_art == null:
        return
    _hp_fill_art.visible = show
    _hp_trail_art.visible = show
    _gauge_fill_art.visible = show


func _stop_fill_tweens() -> void:
    for animation in [
        _hp_fill_tween, _hp_trail_tween, _gauge_fill_tween
    ]:
        if animation != null and animation.is_valid():
            animation.kill()
    _hp_fill_tween = null
    _hp_trail_tween = null
    _gauge_fill_tween = null


func _set_fill_ratio(fill: TextureRect, ratio: float) -> void:
    if fill == null:
        return
    var material: ShaderMaterial = fill.material as ShaderMaterial
    material.set_shader_parameter("fill_ratio", clampf(ratio, 0.0, 1.0))


func _animate_fill(
    fill: TextureRect,
    previous_tween: Tween,
    target: float,
    duration: float,
    delay: float = 0.0
) -> Tween:
    if previous_tween != null and previous_tween.is_valid():
        previous_tween.kill()

    var material: ShaderMaterial = fill.material as ShaderMaterial
    var current: float = float(
        material.get_shader_parameter("fill_ratio")
    )
    if is_equal_approx(current, target):
        _set_fill_ratio(fill, target)
        return null

    var animation := create_tween()
    if delay > 0.0:
        animation.tween_interval(delay)
    animation.tween_property(
        material, "shader_parameter/fill_ratio", target, duration
    ).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
    return animation


func _refresh_dynamic_fills() -> void:
    if _hp_fill_art == null or bound_monster == null:
        return
    if not _abyssal_bar_art.visible:
        return

    var hp_ratio: float = clampf(
        float(bound_monster.health) /
        maxf(1.0, float(bound_monster.max_health)),
        0.0, 1.0
    )
    var gauge_ratio: float = clampf(
        float(bound_monster.action_gauge), 0.0, 1.0
    )

    # Initialize from battle state. Do not animate from an arbitrary
    # full/empty bar when the scene or a monster first appears.
    if not _fills_initialized:
        _stop_fill_tweens()
        _set_fill_ratio(_hp_fill_art, hp_ratio)
        _set_fill_ratio(_hp_trail_art, hp_ratio)
        _set_fill_ratio(_gauge_fill_art, gauge_ratio)
        _hp_target_ratio = hp_ratio
        _gauge_target_ratio = gauge_ratio
        _fills_initialized = true
        return

    if not is_equal_approx(hp_ratio, _hp_target_ratio):
        var taking_damage: bool = hp_ratio < _hp_target_ratio
        _hp_fill_tween = _animate_fill(
            _hp_fill_art, _hp_fill_tween, hp_ratio,
            HP_DAMAGE_DURATION if taking_damage else HP_HEAL_DURATION
        )
        if taking_damage:
            # A delayed tinted remainder makes the lost HP readable.
            _hp_trail_tween = _animate_fill(
                _hp_trail_art, _hp_trail_tween, hp_ratio,
                HP_DAMAGE_TRAIL_DURATION, HP_DAMAGE_TRAIL_DELAY
            )
        else:
            if _hp_trail_tween != null and _hp_trail_tween.is_valid():
                _hp_trail_tween.kill()
            _hp_trail_tween = null
            _set_fill_ratio(_hp_trail_art, hp_ratio)
        _hp_target_ratio = hp_ratio

    if not is_equal_approx(gauge_ratio, _gauge_target_ratio):
        if _gauge_target_ratio > 0.95 and gauge_ratio < 0.20:
            # Spending a turn resets gauge; don't visually drain the
            # whole track backwards over the next character's turn.
            if _gauge_fill_tween != null and _gauge_fill_tween.is_valid():
                _gauge_fill_tween.kill()
            _gauge_fill_tween = null
            _set_fill_ratio(_gauge_fill_art, gauge_ratio)
        else:
            _gauge_fill_tween = _animate_fill(
                _gauge_fill_art, _gauge_fill_tween, gauge_ratio,
                GAUGE_CHANGE_DURATION
            )
        _gauge_target_ratio = gauge_ratio


# Cache the static image. Trim transparent padding so 284px measures
# the painted bar rather than the original export's empty canvas.
static func _load_abyssal_bar() -> Texture2D:
    if _abyssal_bar_attempted:
        return _abyssal_bar_texture
    _abyssal_bar_attempted = true

    if not ResourceLoader.exists(ABYSSAL_BAR_PATH, "Texture2D"):
        push_warning("Abyssal HP bar PNG not found: %s" % ABYSSAL_BAR_PATH)
        return null

    var source: Texture2D = load(ABYSSAL_BAR_PATH) as Texture2D
    if source == null:
        push_warning("Abyssal HP bar could not load: %s" % ABYSSAL_BAR_PATH)
        return null

    var image: Image = source.get_image()
    if image == null or image.is_empty():
        return null

    var painted: Rect2i = image.get_used_rect()
    if painted.size.x <= 0 or painted.size.y <= 0:
        push_warning("Abyssal HP bar has no visible pixels")
        return null

    _abyssal_bar_texture = ImageTexture.create_from_image(
        image.get_region(painted)
    )
    return _abyssal_bar_texture


func _process(delta: float) -> void:
    if (
        not is_instance_valid(_igneous_bar_art)
        or not _igneous_bar_art.visible
        or _igneous_bar_frames.is_empty()
    ):
        return

    _igneous_elapsed_ms += delta * 1000.0
    var advances: int = 0
    while advances < IGNEOUS_BAR_FRAME_COUNT:
        var delay_ms: float = _igneous_bar_durations_ms[_igneous_frame_index]
        if _igneous_elapsed_ms < delay_ms:
            break
        _igneous_elapsed_ms -= delay_ms
        _igneous_frame_index = (
            _igneous_frame_index + 1
        ) % _igneous_bar_frames.size()
        advances += 1
    if advances > 0:
        _igneous_bar_art.texture = _igneous_bar_frames[_igneous_frame_index]


# Load 36 frames with the individual durations from Ludo's JSON.
# Normalized source coordinates support both original and resized PNGs.
static func _load_igneous_bar_animation() -> bool:
    if _igneous_bar_attempted:
        return not _igneous_bar_frames.is_empty()
    _igneous_bar_attempted = true

    if not FileAccess.file_exists(IGNEOUS_BAR_DATA):
        push_warning("Missing Igneous UI JSON: %s" % IGNEOUS_BAR_DATA)
        return false
    var parsed: Variant = JSON.parse_string(
        FileAccess.get_file_as_string(IGNEOUS_BAR_DATA)
    )
    if not (parsed is Dictionary):
        push_warning("Invalid Igneous UI JSON")
        return false

    var meta: Dictionary = parsed.get("meta", {})
    var records: Dictionary = parsed.get("frames", {})
    var image_name: String = str(
        meta.get("image", IGNEOUS_BAR_FALLBACK_IMAGE)
    ).get_file()
    var path: String = IGNEOUS_BAR_DIRECTORY.path_join(image_name)
    if not ResourceLoader.exists(path, "Texture2D"):
        var alt: String = IGNEOUS_BAR_DIRECTORY.path_join(
            image_name.get_basename() + "(1).png"
        )
        if ResourceLoader.exists(alt, "Texture2D"):
            path = alt
        else:
            push_warning("Missing Igneous UI PNG: %s" % path)
            return false
    var sheet: Texture2D = load(path) as Texture2D
    if sheet == null:
        return false

    var image: Image = sheet.get_image()
    if image == null or image.is_empty():
        return false
    var sheet_size: Vector2 = sheet.get_size()
    var original: Dictionary = meta.get("size", {})
    var original_w: float = float(original.get("w", 0))
    var original_h: float = float(original.get("h", 0))
    if original_w <= 0.0 or original_h <= 0.0:
        return false
    var ratio_x: float = sheet_size.x / original_w
    var ratio_y: float = sheet_size.y / original_h

    var frames: Array[Rect2i] = []
    var delays: Array[float] = []
    var crop_top: int = int(sheet_size.y)
    var crop_bottom: int = 0

    # Calculate one shared crop for every frame, otherwise the
    # animated flames would shift the body of the bar up and down.
    for i in range(IGNEOUS_BAR_FRAME_COUNT):
        var item: Dictionary = records.get("frame_%03d" % i, {})
        var raw: Dictionary = item.get("frame", {})
        if raw.is_empty():
            push_warning("Missing frame %d in Igneous UI JSON" % i)
            return false

        var x1: int = roundi(float(raw.get("x", 0)) * ratio_x)
        var y1: int = roundi(float(raw.get("y", 0)) * ratio_y)
        var x2: int = roundi(
            (float(raw.get("x", 0)) + float(raw.get("w", 0))) * ratio_x
        )
        var y2: int = roundi(
            (float(raw.get("y", 0)) + float(raw.get("h", 0))) * ratio_y
        )
        var cell := Rect2i(x1, y1, x2 - x1, y2 - y1)
        if (
            cell.size.x <= 0 or cell.size.y <= 0
            or cell.position.x < 0 or cell.position.y < 0
            or cell.end.x > int(sheet_size.x) or cell.end.y > int(sheet_size.y)
        ):
            push_warning("Invalid Igneous UI frame %d" % i)
            return false
        var bbox: Rect2i = image.get_region(cell).get_used_rect()
        if bbox.size.y > 0:
            crop_top = mini(crop_top, bbox.position.y)
            crop_bottom = maxi(crop_bottom, bbox.end.y)
        frames.append(cell)
        delays.append(maxf(16.0, float(item.get("duration", 104))))

    if crop_bottom <= crop_top:
        return false
    var common_height: int = crop_bottom - crop_top
    for cell in frames:
        var atlas := AtlasTexture.new()
        atlas.atlas = sheet
        atlas.region = Rect2(
            float(cell.position.x), float(cell.position.y + crop_top),
            float(cell.size.x), float(common_height)
        )
        _igneous_bar_frames.append(atlas)
    _igneous_bar_durations_ms = delays
    _igneous_bar_preview_size = Vector2(
        IGNEOUS_BAR_WIDTH,
        BAR_ORIGINAL_WIDTH * float(common_height) /
        float(frames[0].size.x) * BAR_HEIGHT_SCALE
    )
    return true


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
    _refresh_dynamic_fills()

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
