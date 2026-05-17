# Modes

Use this file when the user's wording leaves room for multiple valid asset plans.

## Asset Types

- `player`: controllable overworld hero or playable character
- `npc`: role-readable town or field character
- `creature`: monster, beast, spirit, boss, summon-like unit
- `character`: side-view or non-overworld humanoid unit that is not specifically a player or NPC
- `spell`: castable magic or skill sequence
- `projectile`: loopable traveling object such as orb, arrow, fireball, bullet, beam segment
- `impact`: hit burst, explosion, contact FX
- `prop`: item, weapon, shrine object, pickup, deployable, map object
- `summon`: conjured unit or creature entrance asset
- `fx`: generic visual effect sheet

## Actions

- `single`: one static sprite
- `idle`: looped breathing / stance / aura cycle
- `cast`: spell or skill wind-up / release
- `attack`: body-only attack motion for heroes; attack motion or attack FX for non-hero assets
- `shoot`: body-only ranged firing motion for heroes; projectile emission motion for non-hero assets
- `jump`: takeoff / air / landing motion
- `hurt`: damage reaction
- `combat`: compact combined attack + hurt sheet for non-hero or legacy requests
- `walk`: travel loop
- `run`: faster travel loop
- `hover`: airborne idle / travel loop
- `charge`: power-up or dash prep
- `projectile`: loopable travel motion
- `impact`: contact burst
- `explode`: stronger impact or destruction burst
- `death`: defeat / vanish / collapse sequence

## Bundle Presets

- `single_asset`: one sprite or one sheet
- `unit_bundle`
  - default: `idle` + `combat`
  - optional: `walk`
- `spell_bundle`
  - default: body/caster `cast` + `projectile` + `impact`
  - keep projectile and impact separate from the caster body sheet
- `combat_bundle`
  - default: `idle` + `attack` + `hurt`
- `hero_action_bundle`
  - default: `idle` + `walk` + requested body actions
  - optional: `run`, `jump`, `attack`, `shoot`, `cast`, `hurt`, `death`
  - for `attack`, `shoot`, and `cast`, keep body sheets separate from slash, muzzle flash, projectile, impact, and dust FX
- `line_bundle`
  - default: 1-3 forms
  - per form, choose only the needed sheets
- `engine_atlas`
  - package processed outputs after QC
  - do not use one unvalidated raw mixed-action sheet as the final atlas

## Sheet Presets

- `strip_1x3`
  - simple projectiles, simple FX, existing engine strips
  - avoid for character body animation unless explicitly required
- `strip_1x4` / `1x4`
  - projectiles
  - simple looping FX
  - impact strips
  - existing engine strips
- `2x2`
  - standard idle
  - compact body attack / shoot
  - hurt / impact
  - compact side-view walk
- `2x3`
  - cast sequences
  - jump takeoff-air-land sequences
  - death sequences
  - richer body attack / shoot
- `2x4`
  - richer side-view walk/run/jump
  - compact 8-frame action
  - small prop/object packs
- `3x3`
  - large creature idle
  - boss aura loops
  - high-value showcase idles
- `3x4`
  - 12-frame body action or non-directional action sheet
  - use a layout guide when consistency matters
- `4x4`
  - topdown 4-direction player walk sheet
  - 16-frame non-directional action sheet only when explicitly planned
- `5x5`
  - large custom action sheets or showcase sequences
  - always use a layout guide
- `custom_grid`
  - use when the engine or request gives exact rows/columns
  - use a layout guide

## Agent-First Mapping Hints

- `"make a 4-direction main hero"` -> `player` + `player_sheet`
- `"make a hero attack animation"` -> `player` + `attack` body-only, usually `2x2` or `2x3`; split slash/impact FX if needed
- `"make a hero shooting animation"` -> `player` + `shoot` body-only + separate projectile/muzzle FX if needed
- `"make a hero jump"` -> `player` + `jump`, usually `2x3` or `2x4`
- `"make all hero actions"` -> `hero_action_bundle`; separate sheets per action, layout guide for custom grids
- `"make a healer npc"` -> `npc` + `single_asset`, `role=healer`
- `"make a healer npc walk sheet"` -> `npc` + `walk`
- `"make a boss idle"` -> `creature` + `idle`; prefer `3x3`
- `"make a wizard throwing a magic orb"` -> `spell_bundle`
- `"make a fireball projectile"` -> `projectile` + `projectile`; prefer `1x4`
- `"make a hit explosion"` -> `impact` + `impact`; prefer `2x2`
- `"make a summon entrance"` -> `summon` + `cast` or `impact`
- `"make a full fire samurai creature line"` -> `line_bundle`; plan 1-3 forms, then choose sheets per form
- `"make props matching this map"` -> `prop` + `map_style`; use prop pack only for small static props
- `"make a Phaser/Unity/Godot atlas"` -> process sheets first, then package as `engine_atlas`

## Legacy Compatibility

Keep these mappings working:

- `player_sheet`: 4-direction overworld walk
- `player_walk`: 2x2 down-facing walk
- `npc_walk`: 2x2 down-facing walk
- `combat`: 2x2 attack + hurt
- `evolution`: legacy concept sheet

## Layout Guide Hints

Use `scripts/make_layout_guide.py` when:

- the sheet is `5x5` or `custom_grid`
- the request is a hero action bundle
- a `3x4` or `4x4` sheet is non-directional action rather than a classic 4-way walk sheet
- a prop pack keeps breaking cell boundaries
- previous generations touched edges or changed scale between frames

A layout guide is only a reference image for cell size and safe margins. The final generated art must not contain visible grid lines, labels, borders, or guide colors.

## Processor Defaults

- use `shared_scale=true` for any multi-frame sheet unless inconsistent scale is intentional
- use `align=bottom` or `feet` for grounded actors
- use `align=center` for floating effects, projectiles, and detached FX
- use `component_mode=largest` when raw sheets contain detached sparkles or edge debris that are not part of the main asset
- use `component_mode=all` when detached effects are an intentional part of the asset silhouette
- pass explicit `rows` and `cols` for `shoot`, `jump`, `5x5`, `3x4`, `2x4`, and `custom_grid` modes

## Output Shape

- any sheet mode: transparent sheet + per-frame PNGs + GIF
- `player_sheet`: plus direction strips and four GIFs
- `single_asset`: cleaned transparent PNG
- `hero_action_bundle`: one output folder per body action plus separate FX/projectile/impact folders as needed
- `spell_bundle`: caster body, projectile, and impact folders
- `engine_atlas`: processed transparent assets plus atlas metadata after QC
- bundles: one output folder per asset inside the bundle root
