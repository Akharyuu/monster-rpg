# Diagonal arc battle layout

- Godot's *real* design viewport is **1280 × 720** (no upscaling from
  640 × 360). Text, combat UI and future sprites render at native resolution.
- Allies occupy the **lower-left** in a four-slot upward-curving formation.
- Enemies occupy the **upper-right** in a mirrored, curved formation.
- Formations for 1, 2 and 3 units use their own coordinates to keep the team
  balanced instead of cropping a four-unit row.
- Both groups have a separate area for four 138×185 HUD footprints, with
  up to 120×116 temporary sprite canvases. The entire screen is not covered
  in panels. Slot overlays are transparent except target/current-turn feedback.
- A small name and elemental diamond, resources/status icons, thin HP and
  Action Gauge bars are attached to the monster. The level is preserved in
  code but hidden visually.
- Bottom-left: three action/skill buttons. Beside them: up to three
  passive/special buttons with Soul Recall. Full descriptions remain
  hover tooltips. Settings stays at bottom-right.
- No big ENEMIES / ALLIES / SPRITE / SELECT A SKILL labels.

Manual verification in Godot is still necessary: launch the game, test
single-target and AoE attacks, turn transitions, damage/status overlays,
Soul Recall and the options menu. Python tests can be run separately.
