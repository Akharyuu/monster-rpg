class_name SkillButton
extends Button

var tooltip_skill = null
var tooltip_passive: Dictionary = {}

# Texture is loaded once and automatically replaces the text label.
# Missing optional artwork preserves the existing button appearance.
func set_skill_icon(path: String) -> void:
	if not ResourceLoader.exists(path, "Texture2D"):
		clear_skill_icon()
		return

	var texture: Texture2D = load(path) as Texture2D
	if texture == null:
		clear_skill_icon()
		return

	icon = texture
	expand_icon = true
	icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vertical_icon_alignment = VERTICAL_ALIGNMENT_CENTER
	alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_theme_constant_override("icon_max_width", 72)


func clear_skill_icon() -> void:
	icon = null



func _ready() -> void:
	var tooltip_theme := Theme.new()
	var empty_tooltip_style := StyleBoxEmpty.new()

	tooltip_theme.set_stylebox(
		"panel",
		"TooltipPanel",
		empty_tooltip_style
	)

	theme = tooltip_theme


# Visually distinguish informative passives, cooling passives, and
# locked / ready / selected actions without changing their tooltips.
func set_visual_state(state: String) -> void:
	var background := Color(0.13, 0.12, 0.23)
	var outline := Color(0.38, 0.30, 0.54)
	var foreground := Color(0.88, 0.81, 0.99)

	match state:
		"passive_cooldown":
			background = Color(0.10, 0.105, 0.15)
			outline = Color(0.29, 0.29, 0.35)
			foreground = Color(0.72, 0.73, 0.79)
		"passive_suppressed":
			background = Color(0.085, 0.09, 0.12)
			outline = Color(0.25, 0.25, 0.30)
			foreground = Color(0.67, 0.68, 0.72)
		"active_locked":
			background = Color(0.09, 0.10, 0.15)
			outline = Color(0.28, 0.30, 0.37)
			foreground = Color(0.69, 0.72, 0.79)
		"active_ready":
			background = Color(0.22, 0.16, 0.39)
			outline = Color(0.74, 0.51, 0.96)
			foreground = Color(0.98, 0.93, 1.0)
		"active_selected":
			background = Color(0.30, 0.20, 0.48)
			outline = Color(0.93, 0.77, 1.0)
			foreground = Color(1.0, 0.96, 1.0)

	var base_style := StyleBoxFlat.new()
	base_style.bg_color = background
	base_style.border_color = outline
	base_style.border_width_left = 1
	base_style.border_width_top = 1
	base_style.border_width_right = 1
	base_style.border_width_bottom = 1
	base_style.corner_radius_top_left = 6
	base_style.corner_radius_top_right = 6
	base_style.corner_radius_bottom_left = 6
	base_style.corner_radius_bottom_right = 6
	base_style.content_margin_left = 4
	base_style.content_margin_right = 4

	var hover_style: StyleBoxFlat = (
		base_style.duplicate() as StyleBoxFlat
	)
	hover_style.bg_color = background.lightened(0.13)
	var pressed_style: StyleBoxFlat = (
		base_style.duplicate() as StyleBoxFlat
	)
	pressed_style.bg_color = background.lightened(0.20)

	add_theme_stylebox_override("normal", base_style)
	add_theme_stylebox_override("hover", hover_style)
	add_theme_stylebox_override("pressed", pressed_style)
	add_theme_stylebox_override("disabled", base_style)

	for color_name in [
		"font_color",
		"font_hover_color",
		"font_pressed_color",
        "font_disabled_color"
	]:
		add_theme_color_override(color_name, foreground)


func set_tooltip_skill(skill) -> void:
	tooltip_skill = skill
	tooltip_passive = {}
	tooltip_text = "skill" if skill != null else ""


func set_tooltip_passive(passive_data: Dictionary) -> void:
	tooltip_skill = null
	tooltip_passive = passive_data
	tooltip_text = (
        "passive"
		if not passive_data.is_empty()
		else ""
	)


func _make_custom_tooltip(_for_text: String) -> Object:
	if tooltip_skill != null:
		return _build_skill_card(tooltip_skill)

	if not tooltip_passive.is_empty():
		return _build_passive_card(tooltip_passive)

	return null


func _build_skill_card(skill) -> Control:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(390.0, 0.0)

	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = Color(0.055, 0.065, 0.12, 0.985)
	panel_style.border_color = Color(0.34, 0.43, 0.72, 0.95)
	panel_style.border_width_left = 1
	panel_style.border_width_top = 1
	panel_style.border_width_right = 1
	panel_style.border_width_bottom = 1
	panel_style.corner_radius_top_left = 10
	panel_style.corner_radius_top_right = 10
	panel_style.corner_radius_bottom_left = 10
	panel_style.corner_radius_bottom_right = 10
	panel_style.content_margin_left = 16.0
	panel_style.content_margin_top = 14.0
	panel_style.content_margin_right = 16.0
	panel_style.content_margin_bottom = 14.0
	panel.add_theme_stylebox_override("panel", panel_style)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 9)
	panel.add_child(root)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 8)
	root.add_child(header)

	var title := Label.new()
	title.text = skill.skill_name
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override(
		"font_color",
		Color(0.97, 0.98, 1.0)
	)
	header.add_child(title)

	header.add_child(
		_make_badge(
			"CD %d" % skill.cooldown if skill.cooldown > 0 else "NO CD",
			Color(0.20, 0.28, 0.50, 0.96),
			Color(0.72, 0.80, 1.0)
		)
	)

	var meta_row := HBoxContainer.new()
	meta_row.add_theme_constant_override("separation", 6)
	root.add_child(meta_row)

	meta_row.add_child(
		_make_badge(
			_target_label(skill.target_type),
			Color(0.13, 0.21, 0.32, 0.95),
			Color(0.65, 0.82, 1.0)
		)
	)

	if skill.has_method("get_tooltip_hit_count"):
		var hit_count: int = skill.get_tooltip_hit_count()

		if hit_count > 0:
			meta_row.add_child(
				_make_badge(
					"%d HIT%s" % [
						hit_count,
						"" if hit_count == 1 else "S"
					],
					Color(0.18, 0.16, 0.30, 0.95),
					Color(0.84, 0.72, 1.0)
				)
			)

	var separator := HSeparator.new()
	separator.modulate = Color(0.55, 0.62, 0.82, 0.38)
	root.add_child(separator)

	if not skill.tooltip_summary.is_empty():
		var summary := Label.new()
		summary.text = skill.tooltip_summary
		summary.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		summary.custom_minimum_size = Vector2(350.0, 0.0)
		summary.add_theme_font_size_override("font_size", 14)
		summary.add_theme_color_override(
			"font_color",
			Color(0.82, 0.85, 0.93)
		)
		root.add_child(summary)

	if not skill.tooltip_effects.is_empty():
		var effects_title := Label.new()
		effects_title.text = "EFFECTS"
		effects_title.add_theme_font_size_override("font_size", 11)
		effects_title.add_theme_color_override(
			"font_color",
			Color(0.48, 0.58, 0.82)
		)
		root.add_child(effects_title)

		var effects_box := VBoxContainer.new()
		effects_box.add_theme_constant_override("separation", 5)
		root.add_child(effects_box)

		for effect_data in skill.tooltip_effects:
			effects_box.add_child(
				_make_effect_row(effect_data)
			)

	return panel


func _build_passive_card(passive_data: Dictionary) -> Control:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(390.0, 0.0)

	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = Color(0.055, 0.065, 0.12, 0.985)
	panel_style.border_color = Color(0.58, 0.40, 0.82, 0.95)
	panel_style.border_width_left = 1
	panel_style.border_width_top = 1
	panel_style.border_width_right = 1
	panel_style.border_width_bottom = 1
	panel_style.corner_radius_top_left = 10
	panel_style.corner_radius_top_right = 10
	panel_style.corner_radius_bottom_left = 10
	panel_style.corner_radius_bottom_right = 10
	panel_style.content_margin_left = 16.0
	panel_style.content_margin_top = 14.0
	panel_style.content_margin_right = 16.0
	panel_style.content_margin_bottom = 14.0
	panel.add_theme_stylebox_override("panel", panel_style)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 9)
	panel.add_child(root)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 8)
	root.add_child(header)

	var title := Label.new()
	title.text = str(passive_data.get("name", "Passive"))
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override(
		"font_color",
		Color(0.97, 0.98, 1.0)
	)
	header.add_child(title)

	header.add_child(
		_make_badge(
			str(passive_data.get("badge", "PASSIVE")),
			Color(0.30, 0.18, 0.43, 0.96),
			Color(0.89, 0.74, 1.0)
		)
	)

	var remaining_cd: int = int(
		passive_data.get("cooldown_remaining", 0)
	)

	if remaining_cd > 0:
		header.add_child(
			_make_badge(
				"CD %d" % remaining_cd,
				Color(0.27, 0.29, 0.38, 0.96),
				Color(0.78, 0.80, 0.88)
			)
		)

	var separator := HSeparator.new()
	separator.modulate = Color(0.65, 0.50, 0.86, 0.38)
	root.add_child(separator)

	var summary_text: String = str(
		passive_data.get("summary", "")
	)

	if not summary_text.is_empty():
		var summary := Label.new()
		summary.text = summary_text
		summary.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		summary.custom_minimum_size = Vector2(350.0, 0.0)
		summary.add_theme_font_size_override("font_size", 14)
		summary.add_theme_color_override(
			"font_color",
			Color(0.82, 0.85, 0.93)
		)
		root.add_child(summary)

	var effects: Array = passive_data.get("effects", [])

	if not effects.is_empty():
		var effects_title := Label.new()
		effects_title.text = "EFFECTS"
		effects_title.add_theme_font_size_override("font_size", 11)
		effects_title.add_theme_color_override(
			"font_color",
			Color(0.66, 0.52, 0.88)
		)
		root.add_child(effects_title)

		var effects_box := VBoxContainer.new()
		effects_box.add_theme_constant_override("separation", 5)
		root.add_child(effects_box)

		for effect_data in effects:
			effects_box.add_child(
				_make_effect_row(effect_data)
			)

	return panel


func _make_badge(
	text_value: String,
	background: Color,
	foreground: Color
) -> Label:
	var badge := Label.new()
	badge.text = text_value
	badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	badge.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	badge.custom_minimum_size = Vector2(66.0, 24.0)
	badge.add_theme_font_size_override("font_size", 11)
	badge.add_theme_color_override("font_color", foreground)

	var style := StyleBoxFlat.new()
	style.bg_color = background
	style.corner_radius_top_left = 5
	style.corner_radius_top_right = 5
	style.corner_radius_bottom_left = 5
	style.corner_radius_bottom_right = 5
	style.content_margin_left = 8.0
	style.content_margin_right = 8.0

	badge.add_theme_stylebox_override("normal", style)
	return badge


func _make_effect_row(effect_data: Dictionary) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)

	var dot := Label.new()
	dot.text = "◆"
	dot.custom_minimum_size = Vector2(14.0, 0.0)
	dot.add_theme_font_size_override("font_size", 10)
	dot.add_theme_color_override(
		"font_color",
		_effect_color(
			str(effect_data.get("kind", "neutral"))
		)
	)
	row.add_child(dot)

	var line := RichTextLabel.new()
	line.bbcode_enabled = true
	line.fit_content = true
	line.scroll_active = false
	line.custom_minimum_size = Vector2(328.0, 0.0)
	line.add_theme_font_size_override("normal_font_size", 13)
	line.add_theme_font_size_override("bold_font_size", 13)
	line.add_theme_font_size_override("italics_font_size", 13)
	line.add_theme_font_size_override("bold_italics_font_size", 13)
	line.add_theme_color_override(
		"default_color",
		Color(0.88, 0.90, 0.96)
	)
	line.text = str(effect_data.get("text", ""))
	row.add_child(line)

	return row


func _target_label(target_type: String) -> String:
	match target_type:
		"single_enemy":
			return "SINGLE"
		"all_enemies":
			return "ALL ENEMIES"
		"random_enemies":
			return "RANDOM"
		"all_allies":
			return "ALL ALLIES"
		_:
			return target_type.replace("_", " ").to_upper()


func _effect_color(kind: String) -> Color:
	match kind:
		"debuff":
			return Color(1.0, 0.42, 0.42)
		"buff":
			return Color(0.40, 0.78, 1.0)
		"damage":
			return Color(1.0, 0.67, 0.30)
		"control":
			return Color(1.0, 0.42, 0.42)
		"special":
			return Color(0.82, 0.63, 1.0)
		"heal":
			return Color(0.46, 0.90, 0.66)
		_:
			return Color(0.72, 0.76, 0.86)
