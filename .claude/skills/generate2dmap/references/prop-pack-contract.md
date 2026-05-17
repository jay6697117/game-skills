# Prop Pack Contract

Prop packs batch multiple small static map props into one generated sheet, then extract each cell into a transparent prop PNG.

Use prop packs to reduce repeated image-generation calls and prompt overhead. They trade per-prop control for speed, so use them only when the props can share one style, scale, perspective, and quality bar.

Default to the active map style or clean readable HD 2D game art. Use pixel art only when the user or project style explicitly requires it.

## Object Classification Gate

Before batching, classify each requested object:

- `pack_candidate`: small or medium static environmental prop that fits comfortably in an equal cell.
- `single_prop`: large, important, wide, tall, collision-critical, identity-critical, or irregular object.
- `platform_object`: side-view platform, hazard, pickup, checkpoint, door, ladder, spring, or stage object.
- `foreground_occluder`: object that must render above actors.
- `not_map_prop`: character, enemy, NPC, boss, projectile, impact, UI, icon, or animation sprite.

Only `pack_candidate` objects belong in a normal prop pack. Send `not_map_prop` assets to `/generate2dsprite` with the correct asset type instead of hiding them inside a map prop sheet.

## When To Use

Good candidates:

- rocks, shrubs, flowers, mushrooms, grass tufts, logs
- crates, barrels, sacks, pots
- small signs, lamps, lanterns, fences, posts
- floor ornaments, small statues, ruins, debris
- repeated environmental dressing for one biome

Avoid prop packs for:

- buildings, gates, bridges, trees with wide canopies
- hero objects, key story artifacts, readable statues
- animated props or props with multiple states
- props requiring exact silhouette, scale, collision alignment, or identity
- props that are too wide/tall for equal cells
- actors, enemies, NPCs, projectiles, impacts, spell effects, and UI

## Sheet Size Selection

- `2x2`: 4 props, safest batch size.
- `2x4`: 8 props, useful for small repeated decorations.
- `3x3`: 9 props, best default for small/medium environmental sets.
- `4x4`: 16 props, only for very simple small props with strong margins.
- `custom_grid`: only when the user's exact count or layout requires it.
- wide strip: use for platform pieces or side-view object families only when every item has enough horizontal room.

Use `3x3` by default when the user asks for a set of map props and does not specify count. Use one-by-one generation instead of a pack for hero props, wide gates, buildings, wide trees, bridges, foreground overlays, or anything that must line up exactly with collision.

## Layout Guidance

For large batches, strict cell layout matters more than prompt creativity. If the model repeatedly breaks the grid, create a layout guide with `/generate2dsprite`'s `make_layout_guide.py`, pass it as a reference image to `codex-gateway-imagegen`, and explicitly say the final sheet must not contain visible grid lines, borders, labels, or guide marks.

## Prompt Pattern

```text
Create exactly one <ROWS>x<COLS> prop sheet for a 2D game map in <map/project style>.
Each cell contains one separate static environmental prop from this list, in row-major order:
1. <prop>
2. <prop>
...
All props share the same biome, palette, camera angle, lighting, material language, and rendered scale.
Mostly front-facing top-down game object view: upright objects are vertical and centered, with only a small visible top face. Avoid strong isometric diagonal rotation unless the map itself is isometric.
Full object visible, centered in its own cell, clean readable silhouette.
Each prop must fit fully inside the central 50% to 60% of its cell with generous flat magenta gutters on all four sides.
No prop, branch, roof, sign, smoke, sparkle, shadow, or fragment may touch or cross a cell edge.
Background must be 100% solid flat #FF00FF magenta in every cell, no gradients, no texture, no shadows, no floor plane.
No text, labels, UI, watermark, numbers, arrows, borders, or grid lines.
```

If a cell should stay empty, explicitly say `empty magenta cell`.

For side-view platform objects, replace the view line with:

```text
Side-view platformer object view, readable from a side-scrolling camera. Keep the walkable top edge clear and horizontal when the object is a platform.
```

## Extraction

Use the bundled extractor. Do not rely on Codex-only helper paths or external system skill scripts.

```bash
python "${CLAUDE_SKILL_DIR}/scripts/extract_prop_pack.py" \
  --input "assets/props/raw/forest-props-sheet.png" \
  --rows 3 \
  --cols 3 \
  --labels "mossy-rock,shrub,fallen-log,small-lantern,wooden-sign,flower-patch,stump,crate,grass-tuft" \
  --output-dir "assets/props" \
  --manifest "assets/props/forest-prop-pack.json" \
  --component-mode largest \
  --component-padding 8 \
  --min-component-area 200 \
  --reject-edge-touch
```

Output shape:

```text
assets/props/<label>/prop.png
assets/props/forest-prop-pack.json
```

The manifest contains source cell coordinates, crop boxes, alpha bounds, extracted image size, component counts, and `edge_touch` flags.

If magenta fringe is obvious after extraction, first try stricter prompt wording and regeneration: solid flat `#FF00FF`, no antialiasing into the background, no shadows, no glow spilling into the background. If only one or two props fail, regenerate those as one-by-one props instead of relaxing pack QC.

If the first pack fails because large props touch cell edges, regenerate with stricter occupancy wording such as `each prop must fit inside the central 50% of its cell`. Do not pass a failed pack by relaxing QC unless the clipped asset is intentionally discarded.

## Placement

After extraction, create placement JSON:

```json
{
  "props": [
    {
      "id": "mossy-rock-1",
      "image": "assets/props/mossy-rock/prop.png",
      "x": 420,
      "y": 512,
      "w": 96,
      "h": 72,
      "sortY": 512,
      "layer": "props"
    }
  ]
}
```

Then compose a QA preview with `compose_layered_preview.py` from the map skill.

## QC Rules

Reject or regenerate the pack when:

- any accepted prop has `edge_touch: true`
- labels do not match the requested cells
- the sheet includes visible grid lines, borders, numbers, labels, UI, or watermark
- a prop has shadows or a floor plane baked into the transparent asset area
- prop identity drifts into character/NPC/enemy-like art
- a prop is too large for the intended placement scale
- the style no longer matches the base map or project reference

For noisy particles or edge debris, reprocess with `--component-mode largest`. For intentional multi-part props, use `--component-mode all` and increase the prompt margin.
