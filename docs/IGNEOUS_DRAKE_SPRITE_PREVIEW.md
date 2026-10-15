# Igneous Drake — ally sprite preview

A temporary visual test scene is configured as the Godot project's main
scene. Press **F5** to start the battle: **Igneous Drake R0** occupies Ally
HUD 1, Dullahan Void R5 occupies Ally HUD 2, and two Slimes are opponents.
The old Dullahan test roster remains available in
`res://scenes/battle/battle_screen.tscn` (open and press **F6**).

## Required local artwork

Place this file at:

`godot/assets/monster_sprites/drake_igneous.png`

The sprite is loaded at runtime only when monster ID `drake_igneous`
occupies an **ally** slot. It floats above the first ally HUD and follows
its attack/damage/death feedback. It does not change skill combat logic.

The image currently exists only on your Windows computer, not in GitHub:
`git pull` downloads the scene and scripts but **does not download the
PNG**. Keep that file in its current location, allow Godot to import it
on opening, then play the scene.

## Adjust the sprite

Edit `ALLY_SPRITE_CONFIG` in
`godot/scenes/battle/monster_battle_hud.gd`:

- `position`: sprite origin relative to the ally HUD (negative Y raises it).
- `size`: displayed bounding box; preserves image aspect ratio.
- `scale`: additional scale factor.
- `flip_h`: flips the texture horizontally.

The scene uses a `TextureRect` with nearest filtering, aspect-fit and
`MOUSE_FILTER_IGNORE`, so it does not interfere with targeting.

When the final sprite is approved, use `git add
godot/assets/monster_sprites/drake_igneous.png` and commit the PNG so
other computers can display it too.
