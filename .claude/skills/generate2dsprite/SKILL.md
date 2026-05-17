---
name: generate2dsprite
description: "Claude Code skill for planning, generating, and postprocessing 2D game sprites, transparent props, animation sheets, hero action bundles, projectiles, impacts, spell FX, engine atlases, and GIF previews. Raw image generation must go through the installed codex-gateway-imagegen skill; this skill uses local Python scripts for layout guides, chroma-key cleanup, frame extraction, alignment, QC, transparent exports, and GIF export."
---

# Generate2dsprite

Use this skill for self-contained 2D sprite assets, animation sheets, transparent props, spell effects, projectiles, impacts, hero action bundles, engine atlases, and GIF exports in Claude Code.

This Claude Code adapter has one hard rule: raw image generation and image editing must be performed through the installed `codex-gateway-imagegen` skill. Do not call any built-in image generation tool directly from this skill.

## Parameters

Infer these from the user request:

- `asset_type`: `player` | `npc` | `creature` | `character` | `spell` | `projectile` | `impact` | `prop` | `summon` | `fx`
- `action`: `single` | `idle` | `cast` | `attack` | `shoot` | `jump` | `hurt` | `combat` | `walk` | `run` | `hover` | `charge` | `projectile` | `impact` | `explode` | `death`
- `view`: `topdown` | `side` | `3/4`
- `sheet`: `auto` | `strip_1x3` | `strip_1x4` | `1x4` | `2x2` | `2x3` | `2x4` | `3x3` | `3x4` | `4x4` | `5x5` | `custom_grid`
- `frames`: `auto` or explicit count
- `bundle`: `single_asset` | `unit_bundle` | `spell_bundle` | `combat_bundle` | `hero_action_bundle` | `line_bundle`
- `output_mode`: `single_sheet` | `separate_sheets` | `engine_atlas`
- `art_style`: `project_native` | `clean_hd` | `pixel_art` | `map_style`
- `effect_policy`: `all` | `largest` | `split_fx`
- `anchor`: `center` | `bottom` | `feet`
- `margin`: `tight` | `normal` | `safe`
- `layout_guide`: `none` | `generated` | `provided`
- `reference`: `none` | `attached_image` | `generated_image` | `local_file`
- `prompt`: the user's theme or visual direction
- `role`: only when the asset is clearly an NPC role
- `name`: optional output slug

Read [references/modes.md](references/modes.md) when the request is ambiguous.

## Claude Code Adapter Rules

- Decide the asset plan yourself. Do not force the user to spell out sheet size, frame count, or bundle structure when the request already implies them.
- Write the art prompt yourself. Do not default to the prompt-builder script.
- Generate every raw PNG through `codex-gateway-imagegen` and save it into the current workspace before postprocessing.
- For local reference images, inspect/read the image in Claude Code when needed, then pass the local file path to `codex-gateway-imagegen` as a reference image for edit/reference generation.
- Use this skill's Python scripts only as deterministic processors: layout guide creation, magenta cleanup, frame splitting, component filtering, scaling, alignment, QC metadata, transparent sheet export, and GIF export.
- Use `${CLAUDE_SKILL_DIR}` when calling bundled scripts; do not assume the working directory is the skill directory.
- Treat script flags as execution primitives chosen by the agent, not user-facing hardcoded workflow.
- If a generated sheet touches cell edges, drifts in scale, breaks a loop, copies layout-guide lines, or mixes unrelated assets, regenerate the raw sheet through `codex-gateway-imagegen` with stricter constraints.
- Keep the solid `#FF00FF` background rule unless the user explicitly wants a different processing workflow.

## Style Defaults

- Use the supplied project/reference style first.
- Use `map_style` for map props that must match a generated map.
- Use `clean_hd` when the user asks for game-ready 2D art but does not request pixel art.
- Use `pixel_art` only when the user explicitly asks for pixel/retro/16-bit style or the project reference clearly requires it.

## Hard Production Rules

### Controllable hero actions are body-only

For controllable player or hero `attack`, `shoot`, and `cast` sheets, the body animation must contain only the character body, weapon pose, clothing, and held item. Do not bake slash arcs, muzzle flashes, projectiles, impact bursts, dust clouds, target hits, UI, numbers, or text into the body sheet.

Generate those as separate assets:

- slash or swing trail -> `fx` or `impact`
- muzzle flash -> `fx`
- bullet/arrow/fireball -> `projectile`
- hit burst/explosion -> `impact`
- landing dust -> `fx`

### Do not use single-row body sheets by default

Do not generate raw `strip_1x3` or `strip_1x4` body sheets for player, NPC, creature, or humanoid character actions unless the user explicitly needs an existing engine strip format. Single-row strips are acceptable for projectiles, simple FX, impact strips, and already-established engine assets.

For body actions, prefer `2x2`, `2x3`, `2x4`, `3x4`, `4x4`, `5x5`, or a custom grid with a layout guide.

### Avoid mixed-action raw atlases

Do not force idle, walk, jump, attack, shoot, cast, hurt, and death into one giant raw generated sheet unless the user explicitly asks for an engine atlas and the layout is controlled by a guide. For quality, generate separate raw sheets per action, process them, then package the processed outputs into the requested bundle or atlas structure.

## Workflow

### 1. Infer the asset plan

Pick the smallest useful output.

Examples:

- controllable hero with four directions -> `player` + `player_sheet`
- hero with idle, walk, jump, attack, shoot -> `hero_action_bundle` with separate body sheets and separate FX/projectile sheets
- healer overworld NPC -> `npc` + `single_asset` or `unit_bundle`
- large boss idle loop -> `creature` + `idle` + `3x3`
- wizard throwing a magic orb -> `spell_bundle`
  - caster body cast sheet
  - projectile loop
  - impact burst
- monster line request -> `line_bundle`
  - plan 1-3 forms
  - per form, make the sheets the request actually needs
- map prop request -> `prop` + `single` or a prop pack matching the map style

### 2. Create a layout guide when the grid is fragile

Use a layout guide for hero action bundles, custom grids, 5x5 sheets, 3x4/4x4 non-directional action sheets, crowded prop packs, or any generation that previously broke cell boundaries.

```bash
python "${CLAUDE_SKILL_DIR}/scripts/make_layout_guide.py" \
  --rows 5 \
  --cols 5 \
  --cell-width 384 \
  --cell-height 384 \
  --safe-margin-x 52 \
  --safe-margin-y 52 \
  --output "assets/sprites/<name>/layout-guide.png"
```

Pass the layout guide to `codex-gateway-imagegen` as a reference image and say it is a layout-only guide. The final image must not contain visible grid lines, borders, labels, guide marks, or white guide background.

### 3. Write the prompt manually

Use [references/prompt-rules.md](references/prompt-rules.md).

If a reference is involved:

- Make the reference available to `codex-gateway-imagegen` as a local image path.
- State the reference role explicitly: preserve identity/style, create an animation sheet for the same subject, create an evolution/variant, or derive a matching prop/FX.
- Preserve the stable identity markers from the reference: silhouette, palette, face/eye features, costume marks, major accessories, and material language.
- Let only the requested action, animation phase, or evolution change. Do not redesign the subject unless the user asks.
- Still require exact sheet shape, solid magenta background, frame containment, and same scale across frames.

Keep the strict parts:

- solid `#FF00FF` background
- exact sheet shape
- same character or asset identity across frames
- same bounding box and rendered scale across frames
- explicit containment: nothing may cross cell edges
- no text, labels, UI, watermark, frame borders, or grid lines

### 4. Generate the raw image through `codex-gateway-imagegen`

Invoke the installed `codex-gateway-imagegen` skill and choose a workspace output path, for example:

```text
assets/sprites/<name>/raw-sheet.png
```

The gateway prompt must include the production art prompt plus the technical constraints: exact sheet grid, solid `#FF00FF` background, no labels/text/watermarks, same identity, same scale, and no edge crossing.

After generation:

- keep the raw generated PNG in the output folder
- record the prompt as `prompt-used.txt` or pass it through `--prompt-file`
- use the saved local image path as `--input` for postprocessing

### 5. Postprocess locally

Run the bundled processor from the skill directory.

Example for a normal animation sheet:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/generate2dsprite.py" process \
  --input "assets/sprites/<name>/raw-sheet.png" \
  --target asset \
  --mode idle \
  --output-dir "assets/sprites/<name>" \
  --rows 2 \
  --cols 2 \
  --shared-scale \
  --reject-edge-touch
```

Example for a 4-direction player walk sheet:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/generate2dsprite.py" process \
  --input "assets/sprites/<name>/raw-sheet.png" \
  --target player \
  --mode player_sheet \
  --output-dir "assets/sprites/<name>" \
  --shared-scale \
  --align feet \
  --reject-edge-touch
```

Example for a body-only hero shoot sheet:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/generate2dsprite.py" process \
  --input "assets/sprites/<name>/raw-shoot-body.png" \
  --target player \
  --mode shoot \
  --output-dir "assets/sprites/<name>/shoot-body" \
  --rows 2 \
  --cols 2 \
  --shared-scale \
  --align feet \
  --reject-edge-touch
```

The processor is intentionally low-level. The agent chooses:

- `rows` / `cols`
- `fit_scale`
- `align`
- `shared_scale`
- `component_mode`
- `component_padding`
- `edge_touch` rejection strategy

Use the processor to gather QC metadata, not to make aesthetic decisions for you.

### 6. QC the result

Check:

- did any frame touch the cell edge
- did any frame resize differently than intended
- did detached effects become noise
- does the sheet still read as one coherent animation
- did the final sheet accidentally include grid lines, labels, UI, or text
- does `pipeline-meta.json` match the requested target, mode, rows, and cols
- for hero actions, are projectiles/impacts/slashes/dust split into separate assets

If not, rerun with different processor settings or regenerate the raw sheet through `codex-gateway-imagegen`.

### 7. Return the right bundle

For a single sheet, expect:

- `raw-sheet.png`
- `raw-sheet-clean.png`
- `sheet-transparent.png`
- frame PNGs
- `animation.gif`
- `prompt-used.txt`
- `pipeline-meta.json`

For `player_sheet`, expect:

- transparent 4x4 sheet
- 16 frame PNGs
- direction strips
- 4 direction GIFs

For `hero_action_bundle`, `spell_bundle`, `unit_bundle`, or `line_bundle`, create one output folder per asset/action inside the bundle root.

For `engine_atlas`, package processed transparent outputs and metadata after individual sheet QC. Do not use an unvalidated raw mixed atlas as the final engine asset.

## Defaults

- `idle`
  - small or medium actor -> `2x2`
  - large creature or boss -> `3x3`
- `cast` -> prefer `2x3`
- `attack` / `shoot` body -> prefer `2x2` or `2x3`, body-only
- `jump` -> prefer `2x3` or `2x4`
- `projectile` -> prefer `1x4` or `strip_1x4`
- `impact` / `explode` -> prefer `2x2` or `strip_1x4`
- `walk`
  - topdown actor -> `4x4` for four-direction walk
  - side-view asset -> `2x2` or `2x4`
- use `shared_scale` by default for any multi-frame asset where frame-to-frame consistency matters
- use `largest` component mode when detached sparkles or edge debris make the main body unstable
- use a layout guide for `5x5`, `custom_grid`, and hero action bundles

## Resources

- `references/modes.md`: asset, action, bundle, sheet, and layout selection
- `references/prompt-rules.md`: manual prompt patterns, style defaults, body-only actions, and containment rules
- `scripts/make_layout_guide.py`: deterministic layout-only guide generator
- `scripts/generate2dsprite.py`: postprocess primitive for cleanup, extraction, alignment, QC, and GIF export
