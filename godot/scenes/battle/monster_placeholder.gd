# Temporary readable silhouettes; the actual pixel sprites will replace
# this one node later without changing combat HUD or party layout.
extends Control

var _family: String = ""
var _attribute: String = "storm"
var _enemy_side: bool = false


func configure(
    family: String,
    attribute: String,
    enemy_side: bool
) -> void:
    _family = family.to_lower()
    _attribute = attribute
    _enemy_side = enemy_side
    queue_redraw()


func _tint() -> Color:
    match _attribute:
        "igneous":
            return Color(0.96, 0.39, 0.25)
        "abyssal":
            return Color(0.35, 0.56, 0.95)
        "storm":
            return Color(0.95, 0.78, 0.26)
        "aether":
            return Color(0.88, 0.86, 0.73)
        "void":
            return Color(0.58, 0.35, 0.82)
    return Color(0.62, 0.79, 0.90)


func _poly(coords: Array, tint: Color) -> void:
    var points := PackedVector2Array()
    for point in coords:
        points.append(point)
    draw_colored_polygon(points, tint)


func _draw() -> void:
    var tint: Color = _tint()
    var dark: Color = tint.darkened(0.56)
    var light: Color = tint.lightened(0.30)

    # Soft contact shadow to anchor the sprite to its position.
    draw_circle(Vector2(60, 106), 35, Color(0, 0, 0, 0.14))

    if "slime" in _family:
        # Rounded blob silhouette, not a labeled rectangle.
        _poly([
            Vector2(19, 100), Vector2(19, 83), Vector2(26, 66),
            Vector2(40, 51), Vector2(60, 44), Vector2(79, 51),
            Vector2(96, 67), Vector2(103, 84), Vector2(101, 100),
            Vector2(85, 104), Vector2(40, 104)
        ], dark)
        _poly([
            Vector2(23, 98), Vector2(25, 81), Vector2(32, 65),
            Vector2(47, 53), Vector2(61, 49), Vector2(78, 56),
            Vector2(94, 73), Vector2(97, 95),
            Vector2(82, 99), Vector2(39, 99)
        ], tint)
        draw_circle(Vector2(48, 77), 4.1, dark)
        draw_circle(Vector2(75, 77), 4.1, dark)
        draw_circle(Vector2(48, 76), 1.4, Color.WHITE)
        draw_circle(Vector2(75, 76), 1.4, Color.WHITE)
        draw_circle(Vector2(43, 62), 10.0, Color(1, 1, 1, 0.12))
        return

    if "dullahan" in _family:
        # Headless armoured rider: shoulders, cloak and breastplate.
        _poly([
            Vector2(12, 103), Vector2(25, 65), Vector2(40, 43),
            Vector2(48, 39), Vector2(73, 39),
            Vector2(88, 47), Vector2(103, 69),
            Vector2(111, 103)
        ], dark)
        _poly([
            Vector2(25, 101), Vector2(37, 64), Vector2(49, 52),
            Vector2(73, 52), Vector2(87, 65), Vector2(96, 101)
        ], tint)
        _poly([
            Vector2(43, 56), Vector2(62, 66),
            Vector2(80, 56), Vector2(76, 88),
            Vector2(61, 99), Vector2(46, 88)
        ], dark)
        draw_circle(Vector2(61, 35), 7, light)
        draw_circle(Vector2(61, 35), 4, dark)
        draw_line(Vector2(60, 66), Vector2(60, 92), light, 2)
        draw_line(Vector2(18, 96), Vector2(35, 72), light, 3)
        draw_line(Vector2(105, 91), Vector2(88, 66), light, 3)
        return

    if "drake" in _family:
        _poly([
            Vector2(12, 47), Vector2(47, 56), Vector2(59, 70),
            Vector2(88, 46), Vector2(106, 34), Vector2(89, 86),
            Vector2(71, 99), Vector2(37, 93)
        ], dark)
        _poly([
            Vector2(28, 71), Vector2(57, 55), Vector2(76, 69),
            Vector2(87, 91), Vector2(46, 98)
        ], tint)
        draw_circle(Vector2(61, 51), 11, light)
        draw_circle(Vector2(65, 50), 3, dark)
        return

    # A lightweight generic icon for future monster families.
    draw_circle(Vector2(60, 75), 37, dark)
    draw_circle(Vector2(60, 71), 32, tint)
    _poly([
        Vector2(60, 44), Vector2(78, 70),
        Vector2(60, 98), Vector2(42, 70)
    ], light)
