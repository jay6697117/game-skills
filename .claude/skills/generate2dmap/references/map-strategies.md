# Map Pipeline Selection

Choose the map pipeline in this order. Do not start from a raw visual model, because playable maps usually combine art, object placement, collision, and engine metadata.

1. `map_mode`: what kind of map the user actually needs.
2. `visual_model`: how the visible map is represented.
3. `runtime_object_model`: which non-character map objects need runtime behavior.
4. `collision_model`: how walkability, blockers, platforms, and triggers are represented.
5. `engine_target`: how the result should fit the project.

For any playable game map, level, stage, room, prototype, or engine scene, do not ship only a single baked image unless the user explicitly asks for a flat background only.

## Map Mode

### `tile_mode`

Use when the user asks for tiles, tilesets, autotiling, tile collision, Tiled, LDtk, Phaser tilemaps, Godot TileMap, Unity Tilemap, procedural maps, large editable maps, or grid-perfect editor workflows.

Typical bundle:

- tileset image or project-native tiles
- tile layers
- object layers for entities, triggers, exits, and blockers
- tile collision or object collision
- preview image

### `scene_mode`

Use for top-down or fixed-camera exploration scenes where a generated or painted base map is useful, but props, collision, occlusion, and triggers still matter.

Typical bundle:

- ground-only base map
- transparent prop sprites or prop pack
- prop placement JSON
- collision and trigger JSON
- flattened QA preview

### `side_scroll_mode`

Use for platformers, side-scrollers, runners, shooters, scrolling battle stages, and parallax backgrounds.

Typical bundle:

- background, midground, gameplay plane, and foreground parallax layers
- platform/hazard object metadata
- spawn/checkpoint/exit markers
- platform collision or engine-native collider metadata
- preview image

The gameplay plane must remain readable. Do not let decorative parallax art hide platform silhouettes, hazard boundaries, or player routes.

### `grid_mode`

Use for tactical arenas, board-like RPG battles, placement grids, turn-based combat layouts, and maps whose primary runtime model is discrete cells.

Typical bundle:

- arena/background image or tilemap
- grid dimensions and cell size
- blocked cells, cover cells, spawn cells, objective cells
- optional decorative props that do not obscure grid readability

### `room_chunk_mode`

Use for roguelike rooms, modular interiors, prefab rooms, encounter chunks, and reusable map pieces.

Typical bundle:

- one or more room images or tile chunks
- door/socket metadata
- blockers, triggers, spawn points, and room tags
- optional prop placement metadata

### `baked_scene_mode`

Use only when the output is visual-first: battle background, menu backdrop, title scene, cutscene image, concept preview, poster-like location art, or a prototype where runtime collision is not required.

Typical bundle:

- one PNG
- optional rough zones or notes

## Genre Routing

Use the user's genre words to choose defaults quickly:

- monster-taming route, town, shrine, grassland, dungeon room -> `scene_mode` + `layered_raster` + `y_sorted_props` + `precise_shapes + trigger_zones`
- tactical arena, chess-like board, grid battle -> `grid_mode` + `baked_raster` or `tilemap` + cell metadata
- side-scroller, platformer, runner, parallax stage -> `side_scroll_mode` + `parallax_layers` + `platform_objects`
- tile editor, Tiled, LDtk, autotile, procedural -> `tile_mode` + `tilemap` or `layered_tilemap`
- battle background, visual backdrop, menu scene -> `baked_scene_mode` + `baked_raster` + `none`
- roguelike room, reusable chamber, prefab -> `room_chunk_mode` + `tilemap` or `layered_raster` + socket metadata

## Visual Model

### `baked_raster`

Use when the scene is static, decorative, fixed-screen, or visual-first. Deliver one image plus optional rough collision/zones metadata.

### `layered_raster`

Use when a generated or painted base map is best, but tall objects need collision, occlusion, interaction, reuse, or later editing. Deliver a ground-only base image, separate props, placement metadata, collision/zones metadata, and a flattened preview.

### `tilemap`

Use when the engine/editor already uses grid maps or when editable grid-perfect data matters. Deliver engine-native map data, tileset images, tile layers, object layers, and tile/object collision.

### `layered_tilemap`

Use when the game needs multiple tile layers such as ground, decor, walls, overhead, and foreground. Deliver layered tile data and a render-order contract.

### `parallax_layers`

Use for side-scrolling stages or scrolling backdrops. Deliver background, midground, gameplay plane, foreground, and scroll-speed metadata.

## Runtime Object Model

- `none`: the map is only a background or tile layers.
- `separate_props`: props are independent sprites but do not need y-sort.
- `platform_objects`: platforms, hazards, pickups, checkpoints, doors, and stage objects in side-view maps.
- `y_sorted_props`: props and actors sort by base `y`; use for top-down RPG scenes.
- `interactive_scene_objects`: objects need dialogue, pickups, doors, destructibles, state, or scripted behavior.
- `foreground_occluders`: selected overlays always draw over actors.
- `scene_hooks`: invisible runtime anchors for encounters, exits, camera zones, cutscenes, or scripted events.

Use the simplest model that can express collision, occlusion, and interaction correctly.

## Collision Model

- `none`: visual-only maps and simple backgrounds.
- `coarse_shapes`: a few rectangles/ellipses for fixed arenas or decorative maps.
- `precise_shapes`: explicit blockers and walk bounds for layered RPG maps.
- `tile_collision`: collision stored per tile or tile layer.
- `polygon_walkmesh`: irregular walkable regions or constrained path maps.
- `trigger_zones`: encounter/rest/exit/dialogue areas; often combined with another collision model.

Do not infer collision from prop PNG bounds automatically. Use explicit blockers for prop bases, platform surfaces, walls, hazards, and walkable zones.

## Engine Target

- `raw_canvas`: PNG assets, JSON metadata, and project-specific render code.
- `Phaser`: atlas/tilemap JSON when the project already uses Phaser loaders.
- `Tiled_JSON`: Tiled-compatible tilesets, layers, objects, and custom properties.
- `LDtk`: layer/entity concepts matching LDtk when the project uses it.
- `Godot_TileMap`: tile layers and scene metadata matching Godot's structure.
- `Unity_Tilemap`: tileset/sprite assets and placement data for Unity workflows.
- project-native: preserve the existing schema when a game already has one.

## Visual Reference Handoff

When a generated base map is useful but runtime props still need to be separate:

1. Generate the ground-only base through `codex-gateway-imagegen`.
2. Generate a dressed reference through `codex-gateway-imagegen` using the base image as a reference image.
3. Use the dressed reference to decide prop identities and placements.
4. Generate or extract transparent props separately.
5. Compose the runtime preview from the original base plus transparent props and metadata.

The dressed reference is not the runtime map if props need collision, y-sort, occlusion, interaction, or reuse.

## Presets

### Fixed Battle Background

- `map_mode`: `baked_scene_mode`
- `visual_model`: `baked_raster`
- `runtime_object_model`: `none`
- `collision_model`: `none` or `coarse_shapes`
- Typical deliverables: one PNG, optional zones.

### RPG Exploration Scene

- `map_mode`: `scene_mode`
- `visual_model`: `layered_raster`
- `runtime_object_model`: `y_sorted_props + scene_hooks`
- `collision_model`: `precise_shapes + trigger_zones`
- Typical deliverables: base map, prop images, placement JSON, collision JSON, preview.

### Monster Grassland

- `map_mode`: `scene_mode`
- `visual_model`: `layered_raster`
- `runtime_object_model`: `y_sorted_props + interactive_scene_objects + scene_hooks`
- `collision_model`: `precise_shapes + trigger_zones`
- Good prop-pack candidates: rocks, shrubs, flowers, signs, small logs.

### Tactical Grid Arena

- `map_mode`: `grid_mode`
- `visual_model`: `baked_raster` or `tilemap`
- `runtime_object_model`: `scene_hooks`
- `collision_model`: grid blocked/cover/spawn/objective cells
- Typical deliverables: arena image, grid metadata, blocked cells, spawn cells, objective cells.

### Tile-Based Dungeon

- `map_mode`: `tile_mode`
- `visual_model`: `layered_tilemap`
- `runtime_object_model`: `interactive_scene_objects`
- `collision_model`: `tile_collision + trigger_zones`
- Use when the engine/editor supports tilemaps.

### Side-Scroller Stage

- `map_mode`: `side_scroll_mode`
- `visual_model`: `parallax_layers`
- `runtime_object_model`: `platform_objects + scene_hooks`
- `collision_model`: platform collision plus hazard and trigger zones
- Typical deliverables: parallax layers, gameplay plane, platforms, hazards, spawn/checkpoints, preview.

### Room Chunk

- `map_mode`: `room_chunk_mode`
- `visual_model`: `tilemap` or `layered_raster`
- `runtime_object_model`: `interactive_scene_objects + scene_hooks`
- `collision_model`: `tile_collision` or `precise_shapes + trigger_zones`
- Typical deliverables: room art, socket metadata, blockers, exits, encounter tags.

## Escalation Heuristic

Start with the smallest bundle that satisfies runtime needs:

1. `baked_scene_mode + baked_raster` only for visual backgrounds.
2. `baked_scene_mode + coarse_shapes` for simple non-layered prototypes.
3. `scene_mode + layered_raster + a few props` for playable top-down maps.
4. `scene_mode + layered_raster + y_sorted_props + precise_shapes` for RPG-style exploration.
5. `tile_mode` or `layered_tilemap` only when editor, engine, procedural, or grid-perfect requirements justify it.
6. `side_scroll_mode + parallax_layers + platform_objects` for side-view playable stages.
