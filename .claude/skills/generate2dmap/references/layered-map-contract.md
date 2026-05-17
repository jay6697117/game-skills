# Layered Raster Map Contract

Use this contract for generated or hand-painted 2D exploration maps where actors must walk through the scene, interact with props, sort in front of and behind objects, or trigger gameplay zones.

Default to clean, readable HD 2D game art unless the user explicitly asks for pixel art, retro style, or an existing project style. Preserve the project's native style when the user provides references.

## Layer Types

1. `base`: one raster image containing only terrain, floor, roads, water, cliffs, and ground-level detail.
2. `props`: transparent sprites anchored in map coordinates.
3. `actors`: player, NPCs, enemies, monsters, pickups, and moving objects.
4. `foreground`: optional transparent overlays that must cover actors.
5. `collision`: structured metadata, not pixels.
6. `zones`: structured metadata for encounters, rest, triggers, exits, camera, and dialogue.
7. `preview`: flattened QA artifact only.

Character, enemy, boss, projectile, and animation sprites belong in `/generate2dsprite`, not in the map layer bundle.

## Base Map Prompt Pattern

Use this shape when generating a base map through `codex-gateway-imagegen`:

```text
Create a ground-only top-down 2D game map in clean readable HD game art.
This is a BASE GROUND MAP ONLY.
Include terrain, paths, grass, water, cliffs, ground markings, floor patterns, and flat anchor pads.
Do not include tall collidable objects: no buildings, gates, fences, lanterns, trees, signs, barrels, NPCs, monsters, UI, text, labels, or watermark.
Leave clear empty spaces where props will be placed later.
Make walkable paths, entrances, route edges, and zone boundaries easy to trace.
Use a fixed top-down game camera and keep the whole map visible.
```

If the user asked for pixel art, replace the style line with the requested pixel/retro style. Do not silently force pixel art when the request did not ask for it.

## Visual Reference Handoff

For production layered raster maps, use a dressed reference pass before final prop extraction:

1. Generate the base as ground-only terrain through `codex-gateway-imagegen`.
2. Pass the saved base image path to `codex-gateway-imagegen` as a reference image.
3. Ask for a dressed-reference version of the same map by adding props only.
4. Preserve exact camera, framing, dimensions, terrain, paths, water, anchor pads, collision-relevant boundaries, and map edges.
5. Use the dressed reference to choose prop identities and placement coordinates.
6. Compose the final runtime preview from the original base plus extracted transparent props.

The dressed reference is a planning artifact. Do not ship it as the only runtime map when props need collision, y-sort, occlusion, interaction, or reuse.

Prompt shape:

```text
Use the supplied base image as the exact base map reference.
Create a dressed-reference version of the same map by adding props only.
Preserve exactly: camera, framing, image size, terrain, paths, water, anchor pads, map boundaries, and all walkable routes.
Do not crop, zoom, rotate, repaint, or redesign the terrain.
Add these props naturally on top of the existing map: <list>.
Props should feel intentionally placed along paths, landmarks, encounter-zone edges, rest points, and entrances.
No UI, no text, no labels, no watermark.
```

## Prop Generation

Use `/generate2dsprite` when the map needs reusable transparent props. Choose one of these approaches:

- One-by-one props: safest for large, important, irregular, animated, collision-critical, or identity-critical props.
- Prop packs: faster for small/medium static environmental sets that share style, scale, and perspective.
- Platform/object strips: for side-view stage pieces such as platforms, hazards, pickups, and checkpoint props.

Read [prop-pack-contract.md](prop-pack-contract.md) before batching props.

## One-By-One Prop Prompt Pattern

```text
Create a single <prop> prop for a top-down 2D game map in the same style as the supplied map reference.
Mostly front-facing top-down game object view: upright objects are vertical and centered, with only a small visible top face. Avoid strong isometric diagonal rotation unless the map itself is isometric.
Full object visible, centered, clean readable silhouette.
Background must be 100% solid flat #FF00FF magenta, no gradients, no texture, no shadows, no floor plane.
No text, labels, UI, or watermark.
Entire prop must fit fully inside the image with generous magenta margin on all sides; no part may touch or cross the image edge.
```

Use a larger cell or one-by-one generation for buildings, trees, gates, statues, bridges, large signs, and foreground occluders.

## Prop Metadata

Use explicit map-space dimensions:

```json
{
  "props": [
    {
      "id": "torii",
      "image": "assets/props/torii/prop.png",
      "x": 836,
      "y": 850,
      "w": 380,
      "h": 306,
      "sortY": 850,
      "layer": "props"
    }
  ]
}
```

Anchor conventions:

- `x`: center of the prop's base/feet.
- `y`: bottom of the prop in map coordinates.
- `w`, `h`: rendered size in map units.
- `sortY`: y-depth used for render ordering. Use base `y` for normal props.
- `layer`: `props` for y-sorted objects, `foreground` for always-over-actor overlays.

## Render Order

Recommended order:

```text
base map
ground effects / zone glimmers
renderables sorted by sortY:
  props
  actors
foreground overlays
debug collision
HUD/UI
```

If an NPC must always appear above the player, draw that NPC after the y-sorted pass or set a high `sortY`.

## Collision Metadata

Keep collision readable and hand-editable:

```json
{
  "mapSize": { "width": 1672, "height": 941 },
  "spawn": { "x": 836, "y": 782 },
  "walkBounds": [
    { "id": "main-courtyard", "type": "ellipse", "x": 838, "y": 548, "rx": 604, "ry": 304 }
  ],
  "blockers": [
    { "id": "torii-left-pillar", "type": "rect", "x": 704, "y": 668, "w": 52, "h": 176 }
  ],
  "zones": {
    "grass": { "type": "rect", "x": 180, "y": 306, "w": 382, "h": 302 },
    "rest": { "type": "circle", "x": 760, "y": 548, "radius": 122 }
  }
}
```

Guidelines:

- Use blockers for prop bases, not full sprite silhouettes.
- Keep entrances open by testing path centers.
- Use ellipses for lanterns, rocks, trees, and basins.
- Use rectangles for fences, walls, buildings, gates, bridges, and posts.
- Use polygons only when rects/ellipses produce poor walkability.
- Add trigger zones separately from blockers.

## Preview Composition

Use the bundled `compose_layered_preview.py` to flatten a base map and placement JSON:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/compose_layered_preview.py" \
  --base "assets/map/shrine-base.png" \
  --placements "data/shrine-props.json" \
  --output "assets/map/shrine-layered-preview.png" \
  --report "assets/map/shrine-layered-preview.report.json" \
  --project-root "."
```

The script assumes prop placement uses center-bottom anchoring unless a prop explicitly sets another anchor.

## Post-Reference Object Gate

After the dressed reference exists, decide which objects must become separate runtime assets:

- separate any object that blocks movement
- separate any object actors can pass behind
- separate any object that can be interacted with, destroyed, picked up, opened, animated, or reused
- separate foreground occluders that should draw above actors
- leave only purely painted ground-level details in the base

If an object affects gameplay, it should not remain only baked into the dressed reference.

## QA Checklist

- Spawn point is walkable.
- Main path centers are walkable.
- Gate centers are walkable if the player should pass through.
- Gate pillars block.
- Fences block but entrances remain open.
- Interactables block at their base but can be approached.
- Encounter/rest/exit zones are reachable.
- Actors sort correctly when walking in front of and behind tall props.
- The flattened preview matches the in-game layered render closely enough for visual review.
- The base map still has no baked actors, enemies, text, UI, or tall collidable props.

## Anti-Patterns

Avoid:

- Cutting props out of a fully baked generated map when clean separate prop generation is possible.
- Using a complete flattened map as the only source when collision/occlusion matters.
- Baking text, signs, UI, NPCs, enemies, monsters, or projectiles into the base.
- Letting prop sprites touch image edges.
- Treating transparent PNG bounding boxes as collision automatically.
- Updating art without updating collision and critical point tests.
