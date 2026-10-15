class_name SkillButton
extends Button

var tooltip_skill = null


func set_tooltip_skill(skill) -> void:
    tooltip_skill = skill
    tooltip_text = "skill" if skill != null else ""


func _make_custom_tooltip(_for_text: String) -> Object:
    if tooltip_skill == null:
        return null

    return _build_skill_card(tooltip_skill)


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
            return Color(0.64, 0.78, 1.0)
        "special":
            return Color(0.82, 0.63, 1.0)
        "heal":
            return Color(0.46, 0.90, 0.66)
        _:
            return Color(0.72, 0.76, 0.86)
