---
name: generate2dmap
description: "Claude Code skill for generating and revising production-oriented 2D game maps. Use for RPG maps, monster-taming maps, tactical arenas, battle backgrounds, side-scroller/parallax stages, tilemaps, layered raster maps, prop packs, collision zones, walkable areas, scene hooks, and map previews. Raw visual asset generation must go through the installed codex-gateway-imagegen skill."
---

# Generate2dmap

Use this skill for production-oriented 2D game maps, scenes, stages, and map asset bundles in Claude Code.

This Claude Code adapter has one hard rule: any raw map, prop sheet, dressed reference, stage reference, tileset, parallax layer, battle background, or other visible map asset must be generated through the installed `codex-gateway-imagegen` skill. Do not call any built-in image generation tool directly from this skill, and do not script-draw final visual art unless the user explicitly asks for placeholders or debug scaffolding.

Build the smallest playable map bundle that satisfies the game. Start by choosing a user-facing `map_mode`, then map it to the lower-level pipeline axes:

1. `map_mode`: `tile_mode` | `scene_mode` | `side_scroll_mode` | `grid_mode` | `room_chunk_mode` | `baked_scene_mode`
2. `visual_model`: `baked_raster` | `layered_raster` | `tilemap` | `layered_tilemap` | `parallax_layers`
3. `runtime_object_model`: `none` | `separate_props` | `platform_objects` | `y_sorted_props` | `interactive_scene_objects` | `foreground_occluders` | `scene_hooks`
4. `collision_model`: `none` | `coarse_shapes` | `precise_shapes` | `tile_collision` | `polygon_walkmesh` | `trigger_zones`
5. `engine_target`: `raw_canvas` | `Phaser` | `Tiled_JSON` | `LDtk` | `Godot_TileMap` | `Unity_Tilemap` | project-native

Use user-specified parameters when present. When the user does not specify them, infer the lightest playable pipeline from the existing game, camera, collision needs, map scale, and editing needs.

For requests that imply a playable game map, level, stage, room, prototype, or engine scene, do not ship a single baked image as the runtime map unless the user explicitly asks for a flat background only. A baked image may be a background, reference, or preview artifact, but the playable deliverable must expose gameplay geometry and objects as separate layers, props, tile/object data, collision, zones, scene hooks, or engine-native scene nodes.

This skill is for scenes and maps. Do not generate character, enemy, boss, projectile, NPC, player, or animation sprite assets as map deliverables. The map may include scene hooks such as player spawns, actor spawn marker metadata, patrol or encounter zones, arena entrances, gates, exits, and camera triggers, but actor artwork, projectiles, and animations belong in `/generate2dsprite`.

Read [references/map-strategies.md](references/map-strategies.md) when the pipeline choice is not obvious. Read [references/layered-map-contract.md](references/layered-map-contract.md) before implementing a layered raster map. Read [references/prop-pack-contract.md](references/prop-pack-contract.md) before batching generated props into a sheet.

## Map Modes

Use `map_mode` as the first decision. It is a product-level preset that chooses the initial pipeline axes and expected deliverables:

- `tile_mode`: editable tile/grid maps for RPGs, monster-taming games, platformers, tactical maps, factory games, and engines/editors that already use tiles. Default axes: `tilemap` or `layered_tilemap` + `interactive_scene_objects + scene_hooks` + `tile_collision + trigger_zones`.
- `scene_mode`: base map plus separate props for tower defense, survivors-like arenas, cozy demos, top-down adventure scenes, and visual showcase maps. Default axes: `layered_raster` + `separate_props` or `y_sorted_props + interactive_scene_objects + scene_hooks` + `precise_shapes + trigger_zones`.
- `side_scroll_mode`: parallax side-scroller stages for action platformers, runners, Metroidvania rooms, side-view shooters, and beat-em-up stages. Default axes: `parallax_layers` + `platform_objects + interactive_scene_objects + foreground_occluders + scene_hooks` + `precise_shapes`.
- `grid_mode`: rule-heavy grid scenes for tactical RPGs, factory/automation games, board/card battlers, build grids, and terrain-cost maps. Default axes: `layered_tilemap` or `tilemap` + `interactive_scene_objects + scene_hooks` + `tile_collision` or grid metadata.
- `room_chunk_mode`: modular rooms/chunks for roguelikes, Metroidvania rooms, dungeon rooms, and procedural level assembly. Default axes: `layered_tilemap` or `parallax_layers` or `layered_raster` + object layers + exits/connection metadata + collision.
- `baked_scene_mode`: fixed battle backgrounds, title/menu screens, boss-room concept art, visual novel scenes, point-and-click backgrounds, or other explicitly flat/non-editable scenes. Default axes: `baked_raster` + `none` or `coarse_shapes`.

When the mode and lower-level axes disagree, the mode's playable/editable contract wins. For example, `side_scroll_mode` always needs separate collision and platform/object data even if it also produces a beautiful full-width preview image.

## Genre Routing

When the user gives a genre instead of a technical map mode, choose the mode conservatively:

- Pokemon-like / monster-taming RPG / top-down RPG town or route -> `tile_mode` with optional separate props, encounter zones, exits, NPC spawn markers, and collision.
- Tower defense / Kingdom Rush-like -> `scene_mode` with path metadata, build slots, props, collision/blockers, spawn/exit hooks, and optional engine scene scaffold.
- Survivors-like / arena survival -> `scene_mode` or `tile_mode` depending on map scale; keep obstacles sparse, define spawn rings/zones, camera bounds, and collision separately.
- Mega Man-like / side-view action platformer / runner / Metroidvania side room -> `side_scroll_mode`.
- Beat-em-up / brawler -> `side_scroll_mode` with a walkable belt polygon instead of jump-platform geometry; use parallax/background depth plus props, enemy wave zones, and camera bounds.
- Tactical RPG / strategy grid / factory automation / board-like game -> `grid_mode`.
- Roguelike dungeon / modular Metroidvania / procedural room assembly -> `room_chunk_mode`.
- Visual novel, title screen, point-and-click, boss arena concept, or non-playable showcase -> `baked_scene_mode` unless gameplay/editability is requested.

## Claude Code Adapter Rules

- Use `codex-gateway-imagegen` as the creative visual source for base maps, in-world reference mockups, dressed references, stage references, prop sheets, prop sprites, tileset art, parallax layers, battle backgrounds, and other visible map assets.
- Write the creative prompts yourself. Do not use scripts to generate final visual art or creative prompts.
- Save every manually written image-generation prompt next to the generated asset as `<asset>.prompt.txt` or in an explicit manifest field.
- Scripts may slice, assemble, chroma-key, validate, compose previews, create metadata, and emit engine files. They must not replace image generation as the creative art source for final map visuals.
- Only use procedural drawing or scripted placeholder art when the user explicitly asks for placeholders, test fixtures, debug maps, or engine scaffolding without final art.
- For local reference images, inspect/read the image in Claude Code when needed, then pass the saved local file path to `codex-gateway-imagegen` as an image reference for edit/reference generation.
- Use `${CLAUDE_SKILL_DIR}` when calling bundled scripts; do not assume the working directory is the skill directory.

## Visual Reference Handoff

When generating an in-world reference mockup from an existing generated base/background, the prior image must be treated as an active visual reference, not just a filename or loose style hint:

1. Save the base/background image first.
2. Inspect the exact saved image in Claude Code when needed so the next prompt can name concrete preserved features.
3. Pass the exact local image path to `codex-gateway-imagegen` as a reference image.
4. In the prompt, explicitly say to use the supplied reference image as the visual reference.
5. Describe concrete features from the image that must be preserved: camera framing, horizon, road or water shapes, terrain boundaries, entrance/exit direction, major silhouettes, empty pads, and landmark positions.
6. Generate an in-world reference mockup, not an annotated diagram. Do not draw circles, arrows, outlines, labels, numbers, UI callouts, text, captions, legends, highlighted boxes, highlighted zones, measurement lines, or explanatory overlays.
7. Render proposed visible gameplay objects as natural game-world objects or subtle in-world blockout geometry. Do not draw non-visual metadata such as spawn points, triggers, camera bounds, or patrol hints; write those later as structured scene-hook metadata.
8. Keep reference mockups sparse enough to drive final asset production. Unless the user explicitly asks for a dense concept sheet, include at most 9 distinct visible runtime prop/object candidates in the mockup. Repeated instances of the same platform, lamp, crate, hazard, pickup, or gate count as one candidate and can be repeated later in placement metadata.

Do not rely on a path string, filename, or generic wording like "based on the map" as the whole reference handoff. If the base/background has not been inspected enough to describe what must be preserved, inspect it before generating the dressed reference or stage reference.

## Layer Separation Contract

For any playable or editable layered map, the first generated base/background/foundation image must not bake in objects that the runtime should control separately. This applies across perspectives and styles: top-down RPG maps, monster-taming maps, tactical arenas, tower-defense lanes, side-view platformers, parallax stages, tile/editor workflows, clean HD, pixel-inspired, and retro pixel art.

The base/background/foundation layer may contain only stable non-interactive foundation art:

- top-down or 3/4 maps: ground material, paths, roads, water, cliffs, low terrain markings, floor patterns, and terrain boundaries
- tactical or tower-defense maps: ground, lanes, roads, build pads, lane markings, terrain zones, and non-interactive floor detail
- side-view stages: sky, far/mid scenery, distant buildings, distant terrain silhouettes, atmosphere, and non-colliding depth
- tilemaps: tileset art and tile layers arranged as editable engine data, not a flattened full-scene background

The base/background/foundation layer must not contain runtime-controlled objects unless the user explicitly asked for a single baked image:

- tall props, buildings, trees, rocks, crates, signs, doors, gates, pickups, chests, checkpoints, hazards, traps, turrets, tower objects, ladders, foreground occluders, destructibles, actors, enemies, NPCs, bosses, player characters, UI, labels, or any object that needs collision, interaction, replacement, reuse, y-sorting, animation, engine editing, or independent render order

If a generated base/background already contains those runtime objects, do not use it as the runtime base. Regenerate a cleaner foundation-only base or demote that image to a concept/reference artifact. Proposed objects belong in the in-world reference mockup, then in final separate props, platform objects, object layers, tile layers, collision, zones, and scene-hook metadata.

## Parameter Contract

User-facing parameters may be stated in natural language:

- `map_mode`: tile_mode | scene_mode | side_scroll_mode | grid_mode | room_chunk_mode | baked_scene_mode
- `map_kind`: overworld | town | dungeon | shrine | arena | battle_bg | side_scroller | side_view_action | platformer | metroidvania | brawler | tower_defense | survivors_like | tactical | factory | card_board | room_chunk
- `visual_model`: baked raster | layered raster | tilemap | layered tilemap | parallax
- `size`: pixel dimensions, tile dimensions, or camera-relative size
- `stage_canvas`: exact pixel dimensions and aspect ratio for side-scroll/parallax layers, references, and previews
- `perspective`: top-down | 3/4 top-down | side-view | isometric-like
- `art_style`: clean_hd | pixel_inspired | retro_pixel | hand_painted | project-native
- `visual_asset_source`: codex-gateway-imagegen | existing_assets | procedural_placeholder
- `collision_precision`: none | coarse | precise | tile | walkmesh
- `prop_generation`: none | one_by_one | prop_pack_2x2 | prop_pack_3x3 | prop_pack_4x4 | platform_strip_1x3 | platform_strip_1x4 | custom_wide_pack
- `output_format`: PNG only | layered preview | manifest JSON | engine-native map data

When unspecified:

- Use `codex-gateway-imagegen` as the visual asset source.
- Infer `map_mode` from genre and editing needs before selecting lower-level axes.
- Use `tile_mode` for Pokemon-like, top-down RPG, monster-taming, editor/grid-perfect, or tilemap requests.
- Use `scene_mode` for tower defense, survivors-like, cozy/top-down showcase maps, and base-map-plus-props requests.
- Use `side_scroll_mode` for side-scrollers, platformers, runners, side-view action, brawlers, Metroidvania side rooms, Mega Man-like, Castlevania-like, Contra-like, and parallax background requests.
- For `side_scroll_mode`, choose a canonical `stage_canvas` before image generation. Use the project camera/viewport aspect when available; otherwise default to a 16:9 side-scroller canvas such as `1536x864`. All primary parallax plates, stage references, and previews must preserve this same size/aspect.
- Use `grid_mode` for tactical RPGs, factory/automation maps, board/card battlers, build grids, and terrain-cost maps.
- Use `room_chunk_mode` for modular rooms, roguelike rooms, procedural room assembly, or Metroidvania room-chunk planning.
- Use `baked_scene_mode` only for non-playable visual scenes or explicitly flat images.
- Use `baked_raster + coarse_shapes` only for battle backgrounds, title/menu scenes, cutscenes, decorative backdrops, non-playable previews, or when the user explicitly asks for a single flat image.
- Use `layered_raster + y_sorted_props + precise_shapes` for top-down RPG exploration with tall props, occlusion, interactables, or reusable props; the base must be foundation-only and the props/interactables must remain separate.
- Use `tilemap` or `layered_tilemap` only when the engine/editor already uses tiles or the user asks for editable tiles; do not flatten gameplay objects into one background image.
- Use `parallax_layers + platform_objects + interactive_scene_objects + scene_hooks + precise_shapes` for playable side-view scrolling stages, platformers, runners, shooters, and horizontal action scenes; the parallax/background image is scenery-only and is not the runtime map by itself.
- Use square prop packs only when 4 or more compact small/medium static props share one style and fit comfortably inside equal square cells.
- Use one-by-one, platform strips, tile/object layers, or custom wide packs for hero props, buildings, gates, irregular large props, wide/tall props, platforms, terrain chunks, bridges, walls, ladders, long hazards, animated props, or props needing strong identity or collision alignment.
- Use `clean_hd` for generated exploration maps unless the project or user asks for pixel art. This means clean hand-painted top-down 2D RPG game map, HD game asset style, sharp readable terrain shapes, low texture noise, and no chunky pixels.
- Use `pixel_inspired` only when the user wants a pixel-adjacent look without retro chunkiness.
- Use `retro_pixel` only when the user explicitly asks for 16-bit, retro JRPG, or classic pixel-art maps.

## Workflow

1. Inspect the target game.
   - Find camera size, map dimensions, coordinate system, render order, asset loading, collision support, zone data, and existing map formats.
   - Preserve the engine's existing style and data contracts.

2. Choose the pipeline axes.
   - Choose `map_mode` first. Use the genre routing table when the user describes a game type instead of a technical map format.
   - Select `visual_model`, `runtime_object_model`, `collision_model`, and `engine_target`.
   - If the request is for a playable map, stage, level, room, prototype, or game scene, choose a pipeline with explicit runtime objects. Do not downgrade to `baked_raster` unless the user asked for a background-only image.
   - If the request implies a playable side-view scrolling/action stage, lock the map pipeline to `parallax_layers + platform_objects + interactive_scene_objects + scene_hooks + precise_shapes` unless the engine already requires a tilemap.
   - Select `art_style`. Prefer readable gameplay shapes over decorative texture density.
   - Select `visual_asset_source`. Default to `codex-gateway-imagegen`; use `existing_assets` only when the project already has suitable art; use `procedural_placeholder` only when explicitly requested.
   - Treat `hybrid` as a result of combining axes, not as a primary category.

3. Produce assets through `codex-gateway-imagegen` when pixels are needed.
   - Write creative prompts manually and save prompt metadata.
   - For baked raster maps, generate or edit one background and optional collision/zones metadata.
   - For playable or editable layered maps, generate a foundation-only base/background first. The base must not contain runtime-controlled props, interactables, hazards, doors, gates, pickups, actors, or foreground occluders.
   - For layered raster maps, generate a ground-only/foundation-only base map first. Then perform the visual reference handoff and generate an in-world dressed reference mockup from that base before making final props and placements.
   - For tilemaps, generate or reuse tileset art first, then follow the engine/editor format for layers, objects, collision, and scene files.
   - For `grid_mode`, generate or reuse grid/tileset visual art first, then write cell metadata such as walkable/buildable flags, move cost, terrain effects, resource nodes, and object layers.
   - For `room_chunk_mode`, define chunk dimensions, exits, connection sockets, collision contract, and spawn/trigger metadata before final art assembly.
   - For playable side-view scrolling/action stages, define the canonical `stage_canvas` before generating art. Generate named scenery-only parallax layers first: `sky`, `far_bg`, `mid_bg`, `near_bg`, and optional `foreground_overlay`. Every primary parallax layer must use the same pixel dimensions, aspect ratio, camera framing, horizon line, and top-left anchor as the `stage_canvas`.
   - Treat dressed references and stage references as checkpoints, not deliverables. After the relevant reference exists, continue into the post-reference object production gate.

4. Build metadata.
   - Store prop placement, player spawns, actor spawn marker metadata, interactable scene objects, blockers, walk bounds, encounter zones, exits, camera bounds, and triggers as structured data.
   - For `grid_mode`, store grid dimensions, cell size, tile ids, terrain types, walkable/buildable flags, movement cost, collision, resource nodes, and object/entity slots.
   - For `room_chunk_mode`, store chunk id, size, entrances/exits, connection sockets, collision, spawn markers, camera bounds, and validation hints for seam alignment.
   - For `side_scroll_mode`, store `stage_canvas`, parallax layer source size, display size, anchor, render order, scroll factors, loop/repeat policy, camera bounds, platform collision, hazards, exits, checkpoints, and actor spawn marker metadata.
   - Keep collision independent from pixels unless the target engine explicitly uses tile collision.

5. Validate and preview.
   - Compose a flattened preview for layered maps.
   - Validate image sizes, alpha channels, prop pack extraction metadata, JSON parseability, and critical walkability points when collision matters.
   - For `side_scroll_mode`, reject or normalize mismatched primary parallax layer sizes before runtime integration. The stage reference and QA preview must match `stage_canvas` exactly.

## Prop Generation Rules

Use `/generate2dsprite` for reusable transparent props and visible scene objects when that local skill is available, but write the prop prompt yourself using the selected map `art_style`. Do not use a script to generate the creative prompt. For `clean_hd` maps, explicitly request clean hand-painted HD 2D game assets and explicitly forbid pixel art. For `pixel_inspired`, request clean modern pixel-art-inspired props without retro chunkiness. For `retro_pixel`, request 16-bit or retro JRPG pixel art.

Before any prop/object image generation, classify each visible runtime object from the reference mockup:

- `compact_prop`: small/medium, roughly square or vertical, decorative or simple blocker, no exact alignment requirement
- `wide_or_long_object`: expected aspect ratio wider than about `1.6:1`, such as platforms, floor pieces, bridges, wall runs, fence rows, long traps, long signs, pipes, rails, ledges, or roads
- `tall_or_large_object`: expected aspect ratio taller than about `1.6:1` or visually dominant, such as large trees, gates, towers, buildings, banners, doors, statues, or boss-room props
- `collision_bearing_object`: must line up with collision, walkable edges, build pads, doors, checkpoints, gates, hazards, or engine editor handles
- `tileset_or_strip_piece`: should repeat seamlessly or assemble from left/middle/right caps, corners, slopes, tops, sides, or tile pieces

Generation strategy is determined by that classification:

- Only `compact_prop` objects may use square `prop_pack_2x2`, `prop_pack_3x3`, or `prop_pack_4x4`.
- Do not put `wide_or_long_object`, `tall_or_large_object`, `collision_bearing_object`, or `tileset_or_strip_piece` into square prop packs.
- Use `one_by_one` for important, large, tall, irregular, identity-sensitive, or collision-aligned objects.
- Use `platform_strip_1x3` or `platform_strip_1x4` for repeatable floors/platforms: left cap, middle repeat, right cap, plus optional corner/slope/end variant.
- Use `custom_wide_pack` only for several similar wide objects that share one category and can use wide cells such as `768x256`, `1024x384`, or another explicit non-square cell size.
- Never mix compact decorative props with platforms, terrain chunks, gates, doors, hazards, or other collision-critical objects in the same generated sheet.

Use the bundled prop extractor after generating a solid-magenta prop sheet:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/extract_prop_pack.py" \
  --input "assets/props/<pack>/raw-prop-pack.png" \
  --rows 2 \
  --cols 2 \
  --output-dir "assets/props/<pack>" \
  --labels "rock,crate,barrel,sign" \
  --reject-edge-touch
```

Use the bundled preview composer to verify placement over the base map:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/compose_layered_preview.py" \
  --base "assets/map/<name>-base.png" \
  --placements "data/<name>-props.json" \
  --output "assets/map/<name>-layered-preview.png" \
  --report "assets/map/<name>-layered-preview.report.json" \
  --project-root "."
```

## Post-Reference Object Production Gate

An in-world reference mockup is never the final deliverable by itself. After generating `dressed-reference` or `stage-reference`, continue with:

1. Inspect both the original `base` or `background` and the generated `dressed-reference` or `stage-reference` mockup before object/prop generation when needed.
2. Create a concrete object list from the reference mockup while cross-checking the original base/background: object id, type, approximate position, approximate size, render layer, collision role, and asset strategy.
3. If the reference contains more than 9 distinct visible runtime object candidates, reduce the generated asset list to the 9 most gameplay-relevant candidates first, then represent extra repeats or low-value decorations through placement metadata or a later asset pass.
4. Classify every object before generation. Compact decorative props may be batched; wide/long, tall/large, collision-bearing, and tileset/strip objects must use one-by-one, strip, custom wide pack, tile/object-layer, or engine-native strategies.
5. For each visible runtime object, choose exactly one asset strategy: generate a separate transparent asset with `/generate2dsprite` or `codex-gateway-imagegen`, extract it from a generated pack, or represent it as a tile/object layer if the engine/editor pipeline is tile-based.
6. For every object/prop image prompt, explicitly state that the supplied original base/background and supplied reference mockup are the visual context. The generated asset must match the original map style and correspond to an object visible in the reference mockup.
7. Generate or define the final platforms, terrain chunks, props, hazards, pickups, doors, gates, checkpoints, exits, foreground occluders, and other visible scene objects. Do not skip this step just because the reference mockup already contains them visually.
8. Write placement metadata such as `data/<name>-props.json`, `data/<name>-objects.json`, engine-native object layers, or tile/object data.
9. Write collision, zones, scene hooks, camera bounds, and exits as structured metadata.
10. Compose a QA preview from the original base/background plus final runtime objects.

Reference-only output is incomplete for any playable map, layered map with props, side-view stage, engine scene, or request that asks for separate props/editable objects. Only stop at a reference mockup if the user explicitly asks for a reference-only concept image.

## Playable Stage Reference Rules

For playable side-view scrolling/action maps, an in-world stage reference mockup is mandatory before generating final scene objects or scene metadata:

1. Choose and record one `stage_canvas`, for example `1536x864` for a default 16:9 HD side-scroller when the project has no explicit camera size. Use the engine's existing viewport aspect ratio when it exists. All primary parallax layers, the stage reference, and the stage preview must share this exact size unless a layer is explicitly marked as a repeatable strip.
2. Generate named parallax scenery layers as separate runtime images: `assets/map/<name>-sky.png`, `assets/map/<name>-far-bg.png`, `assets/map/<name>-mid-bg.png`, `assets/map/<name>-near-bg.png`, and optional `assets/map/<name>-foreground-overlay.png`.
   - These layers are scenery only, not playable foreground.
   - They must not contain walkable floors, platform tops, terrain chunks, spike traps, pickups, crates, doors, gates, checkpoints, ladders, near fences, near stone walls, enemies, player characters, UI, labels, or any object that should later be edited, collided with, reused, or layered independently.
3. Generate `assets/map/<name>-stage-reference.png` from the scenery/background reference. It should visually place the intended scene layout as natural game-world objects or subtle blockout geometry: platforms or walkable lanes, terrain chunks, foreground occluders, hazards, pickups, doors, checkpoints, gates, and exits.
4. Use at most 9 distinct visible runtime object candidates in the stage reference unless the user explicitly asks for a larger object pass. Repeated placements of the same platform, terrain chunk, hazard, pickup, checkpoint, door, gate, or occluder count as one candidate and should be repeated later in metadata.
5. Do not draw spawn markers, actor markers, arena trigger zones, camera bounds, arrows, labels, circles, outlines, numbered callouts, text, legends, or UI overlays in the reference image.
6. Continue through the post-reference object production gate: generate or define final platforms, terrain chunks, hazards, pickups, doors, checkpoints, foreground occluders, and other visible scene objects as separate assets, tile layers, or object layers.

The stage reference is an in-world reference mockup. Do not ship it as the runtime map, infer collision from its pixels, or cut platform objects out of the baked reference image. If a platform must be reusable or collidable, generate it as a separate platform object, terrain chunk, tile, or engine-native object.

Scene hooks are metadata only. Do not generate enemy, boss, NPC, player, projectile, or animation sprites inside `generate2dmap`; call `/generate2dsprite` separately when the game needs those assets.

## Expected Deliverables

For a baked raster map:

- `assets/map/<name>.png`
- optional `<name>.prompt.txt`
- optional `data/<name>-collision.json` or `data/<name>-zones.json`
- code changes that load/use the image

Use this deliverable only for non-playable backgrounds or explicitly requested flat images.

For a layered raster map:

- `assets/map/<name>-base.png`
- `assets/map/<name>-base.prompt.txt`
- optional `assets/map/<name>-dressed-reference.png` for prop planning
- `assets/props/<prop>/prop.png` folders, from one-by-one props or extracted prop packs
- `data/<name>-props.json` placement metadata
- `data/<name>-collision.json` and/or `data/<name>-zones.json` when gameplay needs them
- `assets/map/<name>-layered-preview.png`
- code changes that load the base, props, y-sorted renderables, collision, and zones

For a tilemap or layered tilemap:

- image-generated or user-supplied `assets/tilesets/<name>.png`
- optional tile slicing/atlas metadata
- engine-native tile layer data such as Tiled JSON, LDtk data, Godot TileMap scene data, Unity tile placement data, or project-native JSON
- object layers for spawns, exits, interactables, blockers, and zones
- a flattened preview assembled from the visual tileset and layer data
- no script-drawn final tileset art unless the user explicitly asked for procedural placeholders

For a playable side-view scrolling/action stage:

- image-generated parallax scenery layers such as `assets/map/<name>-sky.png`, `assets/map/<name>-far-bg.png`, `assets/map/<name>-mid-bg.png`, `assets/map/<name>-near-bg.png`, and optional `assets/map/<name>-foreground-overlay.png`
- one recorded `stage_canvas` shared by the primary parallax layers, `stage-reference`, and `stage-preview`
- prompt files/manifests for generated visual assets
- `assets/map/<name>-stage-reference.png` as an in-world reference mockup for platform/object placement
- separate image-generated platform, terrain-chunk, foreground-occluder, hazard, door, pickup, checkpoint, gate, and exit sprites when these are visible scene objects
- `data/<name>-objects.json` or engine-native object layers for platforms, terrain chunks, hazards, pickups, doors, checkpoints, gates, exits, and foreground occluders
- `data/<name>-scene-hooks.json` or engine-native metadata for player spawns, actor spawn marker metadata, encounter/arena triggers, camera bounds, and exit links
- `data/<name>-collision.json` with explicit platform/solid geometry independent from the background pixels
- `assets/map/<name>-stage-preview.png` composed from the background plus objects for QA only
- code or scene changes that load the background, render object layers, and use the collision/object data as runtime gameplay data

Do not accept a single generated side-view action/platformer stage image plus collision rectangles as the final playable map. Runtime `background` fields must point to scenery-only background or parallax layers, never to `stage-reference` or `stage-preview`; previews are QA artifacts only.

For `grid_mode`:

- image-generated or user-supplied tileset/grid art
- grid dimensions, cell size, and map data in project-native JSON, Tiled JSON, LDtk, Godot TileMap, Unity Tilemap, or equivalent
- cell metadata for walkable/buildable, movement cost, terrain effects, resources, collision, and placement rules
- object layers for units, buildings, machines, cards/board slots, exits, spawns, and triggers
- a QA preview that can show optional debug grid/collision overlays

For `room_chunk_mode`:

- reusable chunk art or tile/object layers
- chunk metadata with `chunk_id`, size, entrances/exits, connection sockets, spawn markers, blockers, hazards, and camera bounds
- collision and seam validation metadata
- a chunk preview and, when multiple chunks exist, an assembled layout preview

For `scene_mode`:

- foundation-only `assets/map/<name>-base.png`
- in-world `assets/map/<name>-dressed-reference.png`
- separate props/interactables/blockers from one-by-one assets or compact prop packs
- placement, collision, zones, exits, camera bounds, and scene-hook metadata
- a QA preview composed from the base plus final runtime objects

For a prop pack:

- raw generated sheet with solid `#FF00FF` background
- extracted `assets/props/<prop>/prop.png` files
- `prop-pack.json` extraction manifest
- no `edge_touch` entries for accepted props

## Validation

Always validate what the chosen pipeline requires:

- map files exist and have expected dimensions
- prompt files or prompt manifest fields exist for generated visible assets
- transparent props contain alpha
- prop pack manifests parse and accepted props do not touch cell edges
- placement JSON parses and referenced prop files exist
- collision/zones JSON parses when present
- critical spawn, path, entrance, blocker, and zone points behave as expected
- playable/editable layered maps use a foundation-only base/background and do not bake runtime-controlled props, interactables, hazards, doors, gates, pickups, actors, foreground occluders, or reusable scene objects into the base
- playable stages have explicit runtime objects or metadata for every gameplay-relevant platform or walkable lane, blocker, hazard, door, pickup, checkpoint, gate, exit, player spawn, actor spawn marker, encounter/arena trigger, and camera bound
- playable side-view backgrounds are scenery-only and do not contain baked-in foreground gameplay platforms, hazards, pickups, doors, gates, checkpoints, or other reusable runtime objects
- `side_scroll_mode` primary parallax layers, stage references, and stage previews match the recorded `stage_canvas`; any repeatable strips or differently sized foreground sprites declare display size, anchor, scale, and repeat policy
- `side_scroll_mode` parallax layers have explicit render order, scroll factors, dimensions, loop/repeat policy, and are not used as collision sources
- `grid_mode` outputs include grid dimensions, cell size, cell metadata, object layers, and validation of critical walkable/buildable cells
- `room_chunk_mode` outputs include chunk dimensions, exits/connection sockets, seam validation, collision, and at least one assembled or per-chunk preview
- stage-reference maps preserve the background dimensions and their object plan matches the final object/collision metadata
- stage-reference and dressed-reference mockups contain no more than 9 distinct visible runtime prop/object candidates unless the user explicitly requested a larger pass
- reference mockups are followed by final props/objects, placement metadata, collision/scene-hook metadata, and a QA preview unless the user explicitly requested reference-only output
- flattened preview looks coherent at the game's camera size

## Dependencies

Bundled scripts require Python 3 and Pillow. If the environment lacks Pillow, install the project requirement before running prop extraction or preview composition.

## Resources

- `references/map-strategies.md`: map modes, genre routing, playable map contracts, parallax stage rules
- `references/layered-map-contract.md`: layered raster base/prop/collision/preview contract
- `references/prop-pack-contract.md`: prop/object classification, prop pack prompts, extraction and QC
- `scripts/extract_prop_pack.py`: extract transparent props from solid-magenta prop sheets
- `scripts/compose_layered_preview.py`: compose QA previews from base maps and placement JSON
