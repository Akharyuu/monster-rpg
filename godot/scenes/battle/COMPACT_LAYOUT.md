# Battle layout: 640x360 prototype

The main Godot combat scene uses a **640x360 internal viewport**, displayed
at 1280x720 (2x) by default. This is a layout pass, not final pixel art.

- Enemies: row y=24. Allies: row y=141.
- Up to four 110x105 combatant HUDs on either side, separated by 30px.
- Occupied slots will center dynamically; the two-monster demo remains playable.
- The turn/message strip spans y=246-263.
- Bottom action HUD spans y=263-360. Three compact skill buttons use
  S1/S2/S3 labels, while their full descriptions remain in tooltips.
- Three passive/special-action slots support Soul Recall alongside passives;
  tooltips retain full detail.
- Options gear provides Continue and Restart Demo.
- Each monster has an attribute-tinted **temporary sprite placeholder**,
  HP, AG, name, level and status/resource badges. Replace the placeholder
  when pixel art is ready.

Verification after pulling: open Godot, play the main battle scene, inspect
skill/passive tooltips, attack an enemy, try area attacks, and check targeting,
Soul Recall and the options menu. Run `python -m pytest -q` too.
