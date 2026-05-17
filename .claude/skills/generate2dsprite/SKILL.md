---
name: generate2dsprite
description: "Claude Code skill for planning, generating, and postprocessing 2D pixel-art assets and animation sheets. Use for creatures, characters, NPCs, spells, projectiles, impacts, props, summons, transparent sheets, and GIF exports. Raw image generation must go through the installed codex-gateway-imagegen skill, then this skill uses local Python processing for chroma-key cleanup, frame extraction, alignment, QC, and transparent exports."
---

# Generate2dsprite

Use this skill for self-contained 2D sprite assets, animation sheets, transparent props, spell effects, projectiles, impacts, and GIF exports in Claude Code.

This Claude Code adapter has one hard rule: raw image generation and image editing must be performed through the installed `codex-gateway-imagegen` skill. Do not call any built-in image generation tool directly from this skill.

## Parameters

Infer these from the user request:

- `asset_type`: `player` | `npc` | `creature` | `character` | `spell` | `projectile` | `impact` | `prop` | `summon` | `fx`
- `action`: `single` | `idle` | `cast` | `attack` | `hurt` | `combat` | `walk` | `run` | `hover` | `charge` | `projectile` | `impact` | `explode` | `death`
- `view`: `topdown` | `side` | `3/4`
- `sheet`: `auto` | `1x4` | `2x2` | `2x3` | `3x3` | `4x4`
- `frames`: `auto` or explicit count
- `bundle`: `single_asset` | `unit_bundle` | `spell_bundle` | `combat_bundle` | `line_bundle`
- `effect_policy`: `all` | `largest`
- `anchor`: `center` | `bottom` | `feet`
- `margin`: `tight` | `normal` | `safe`
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
- Use this skill's Python script only as a deterministic processor: magenta cleanup, frame splitting, component filtering, scaling, alignment, QC metadata, transparent sheet export, and GIF export.
- Use `${CLAUDE_SKILL_DIR}` when calling bundled scripts; do not assume the working directory is the skill directory.
- Treat script flags as execution primitives chosen by the agent, not user-facing hardcoded workflow.
- If a generated sheet touches cell edges, drifts in scale, or breaks a projectile / impact loop, either reprocess with better primitive settings or regenerate the raw sheet through `codex-gateway-imagegen`.
- Keep the solid `#FF00FF` background rule unless the user explicitly wants a different processing workflow.

## Workflow

### 1. Infer the asset plan

Pick the smallest useful output.

Examples:

- controllable hero with four directions -> `player` + `player_sheet`
- healer overworld NPC -> `npc` + `single_asset` or `unit_bundle`
- large boss idle loop -> `creature` + `idle` + `3x3`
- wizard throwing a magic orb -> `spell_bundle`
  - caster cast sheet
  - projectile loop
  - impact burst
- monster line request -> `line_bundle`
  - plan 1-3 forms
  - per form, make the sheets the request actually needs

### 2. Write the prompt manually

Use [references/prompt-rules.md](references/prompt-rules.md).

If a reference is involved:

- Make the reference available to `codex-gateway-imagegen` as a local image path.
- State the reference role explicitly: preserve identity/style, create an animation sheet for the same subject, create an evolution/variant, or derive a matching prop/FX.
- Preserve the stable identity markers from the reference: silhouette, palette, face/eye features, costume marks, major accessories, and material language.
- Let only the requested action or evolution change. Do not redesign the subject unless the user asks.
- Still require exact sheet shape, solid magenta background, frame containment, and same scale across frames.

Keep the strict parts:

- solid `#FF00FF` background
- exact sheet shape
- same character or asset identity across frames
- same bounding box and pixel scale across frames
- explicit containment: nothing may cross cell edges

### 3. Generate the raw image through `codex-gateway-imagegen`

Invoke the installed `codex-gateway-imagegen` skill and choose a workspace output path, for example:

```text
assets/sprites/<name>/raw-sheet.png
```

The gateway prompt must include the production art prompt plus the technical constraints: exact sheet grid, solid `#FF00FF` background, no labels/text/watermarks, same identity, same scale, and no edge crossing.

After generation:

- keep the raw generated PNG in the output folder
- record the prompt as `prompt-used.txt` or pass it through `--prompt-file`
- use the saved local image path as `--input` for postprocessing

### 4. Postprocess locally

Run the bundled processor from the skill directory.

Example for a normal animation sheet:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/generate2dsprite.py" process \
  --input "assets/sprites/<name>/raw-sheet.png" \
  --target creature \
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

The processor is intentionally low-level. The agent chooses:

- `rows` / `cols`
- `fit_scale`
- `align`
- `shared_scale`
- `component_mode`
- `component_padding`
- `edge_touch` rejection strategy

Use the processor to gather QC metadata, not to make aesthetic decisions for you.

### 5. QC the result

Check:

- did any frame touch the cell edge
- did any frame resize differently than intended
- did detached effects become noise
- does the sheet still read as one coherent animation
- does `pipeline-meta.json` match the requested target, mode, rows, and cols

If not, rerun with different processor settings or regenerate the raw sheet through `codex-gateway-imagegen`.

### 6. Return the right bundle

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

For `spell_bundle` or `unit_bundle`, create one folder per asset in the bundle.

## Defaults

- `idle`
  - small or medium actor -> `2x2`
  - large creature or boss -> `3x3`
- `cast` -> prefer `2x3`
- `projectile` -> prefer `1x4`
- `impact` / `explode` -> prefer `2x2`
- `walk`
  - topdown actor -> `4x4` for four-direction walk
  - side-view asset -> `2x2`
- use `shared_scale` by default for any multi-frame asset where frame-to-frame consistency matters
- use `largest` component mode when detached sparkles or edge debris make the main body unstable

## Resources

- `references/modes.md`: asset, action, bundle, and sheet selection
- `references/prompt-rules.md`: manual prompt patterns and containment rules
- `scripts/generate2dsprite.py`: postprocess primitive for cleanup, extraction, alignment, QC, and GIF export
