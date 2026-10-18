shader_type canvas_item;

// Left-to-right mask with a subpixel-soft leading edge. Each monster
// owns a separate ShaderMaterial so its fill can be animated independently.
uniform float fill_ratio : hint_range(0.0, 1.0) = 1.0;

void fragment() {
    float edge = max(fwidth(UV.x), 0.002);
    float visible = smoothstep(UV.x - edge, UV.x + edge, fill_ratio);
    // A fully depleted bar is truly invisible (including its left cap).
    if (fill_ratio <= 0.0) {
        visible = 0.0;
    }
    COLOR.a *= visible;
}
