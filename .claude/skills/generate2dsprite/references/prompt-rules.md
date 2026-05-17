# Prompt Rules

Use this file when writing sprite prompts by hand.

Do not delegate prompt writing to a script unless you specifically need parity with an older generated prompt.

## Global Rules

Always keep these constraints:

- background is 100% solid flat magenta `#FF00FF`
- no gradients in the background
- no text
- no labels
- no UI
- no speech bubbles
- no watermark
- exact grid count only
- no borders or frames between cells
- no visible grid lines or guide marks in the final art
- same asset identity across frames
- same bounding box and same rendered scale across frames
- every frame has enough magenta margin for clean extraction

## Style Rules

Choose style in this order:

1. If the user supplies a reference or project style, preserve that style.
2. If the asset must match a generated map, use `map_style` and reference the map image when available.
3. If the user simply asks for game-ready 2D art, use clean readable HD 2D game art.
4. Use pixel art only when the user explicitly asks for pixel/retro/16-bit style or the project reference clearly requires it.

Do not silently force pixel art for every request.

For `player`, `npc`, and humanoid `character` assets:

- full body visible unless the user asks for portrait/cropped art
- strong readable silhouette
- stable proportions and costume details across frames
- gameplay-readable pose
- enough margin for clean engine rendering

For `creature`, `spell`, `projectile`, `impact`, `summon`, and `fx`:

- strong silhouette or effect shape
- readable body colors, material, or energy shape
- avoid painterly composition drift between frames
- if humanoid, keep it clearly non-player unless the user explicitly wants a player-like unit

For map `prop` assets:

- match the supplied map or project style
- use top-down/front-facing object view for top-down maps
- use side-view object view for platformer/stage objects
- keep the full object visible and centered
- no floor plane or baked cast shadow unless the map style explicitly requires it

## Reference Rules

Use these rules when the user attaches a reference, points to a local image, asks for consistency with an earlier generated image, or asks for an evolution/variant of an existing sprite:

- Make the reference image available to the `codex-gateway-imagegen` skill before generation. If the reference is a local file, pass that file path as a reference image to the gateway skill.
- In the prompt, say `use the supplied reference image as the visual reference`.
- State what must stay fixed: silhouette family, palette, face/eyes, costume or markings, accessories, material language, and art style.
- State what may change: pose, animation phase, action energy, size progression, evolution traits, or FX intensity.
- For animation sheets, preserve the same character identity in every cell and only change the animation pose or effect state.
- For evolution lines, keep visible lineage markers while allowing larger silhouette, added details, or stronger colors per form.
- Keep the normal magenta-background and containment rules even when using a reference.

## Layout Guide Rules

When using a generated layout guide as a reference image:

- Say the guide is for cell layout and safe margins only.
- Say the final output must be a normal magenta-background sprite sheet.
- Say not to copy guide colors, white background, black borders, blue safe boxes, dashed center lines, labels, or any guide marks.
- Restate the exact row/column count and the final `#FF00FF` background.
- Restate that no body part, weapon, projectile, effect, or prop may cross a cell edge.

Prompt addition:

```text
Use the supplied layout guide only to understand the cell grid and safe margins. Do not copy any guide lines, borders, labels, colors, or white background. The final sprite sheet must have only the requested art on a solid flat #FF00FF magenta background with no visible grid lines.
```

## Containment Rules

For any sheet mode, say this explicitly when consistency matters:

- the entire subject must fit fully inside each cell
- no body part, effect, weapon, tail, wing tip, orb, spark, smoke trail, platform edge, or prop fragment may cross a cell edge
- leave magenta margin on all four sides
- use the same silhouette scale in every frame

If detached FX are undesirable, say:

- no floating detached effects outside the main silhouette

If detached FX are required, say:

- detached effects must remain tightly grouped near the main subject and still fit inside the cell

## Body-Only Hero Action Rules

For controllable player/hero `attack`, `shoot`, and `cast` body sheets, write body-only prompts.

Use:

- body pose changes only
- weapon or held item may move with the body
- clothing, hair, hands, feet, and body remain consistent
- no target, enemy, hit victim, UI, text, numbers, or battle backdrop

Forbid:

- slash arcs baked into the body sheet
- muzzle flashes baked into the body sheet
- projectiles baked into the body sheet
- impact explosions baked into the body sheet
- landing dust or smoke trails baked into the body sheet
- full attack scene composition inside each cell

Generate slash, muzzle flash, projectile, impact, and dust as separate `fx`, `projectile`, or `impact` sheets.

## View Rules

- `topdown`: for overworld actors and player / NPC sheets
- `side`: for projectiles, side-view units, platform props, impacts, side-scroller characters
- `3/4`: for creature battle sprites, bosses, showcase idles, side-view spellcasters

## Action Rules

### `idle`

Use:

- neutral stance
- subtle motion
- weight shift or aura pulse
- strongest idle accent before looping

Prefer:

- `2x2` for standard actors
- `3x3` for large creatures and showcase idles

### `cast`

A `2x3` cast is often the best default:

- readiness
- energy gather
- stronger gather
- release start
- release peak
- settle or hold

For a controllable hero, keep the caster body separate from projectile and impact art.

### `attack`

For a compact body-only hero attack sheet, describe:

- ready stance
- wind-up
- strike pose
- follow-through or recovery

For a non-hero attack/impact FX sheet, describe the actual slash or hit burst as a separate `fx` or `impact` asset.

### `shoot`

For a compact body-only hero shoot sheet, describe:

- ready / aim
- recoil or release pose
- follow-through
- recovery

Do not include bullet, arrow, projectile trail, muzzle flash, impact, target, or smoke in the body sheet. Generate those separately.

### `jump`

A `2x3` or `2x4` jump is often best:

- crouch / anticipation
- takeoff
- rising
- apex
- falling
- landing / recovery

For platformers, keep the feet and body aligned consistently and leave enough bottom margin for landing frames.

### `hurt`

For a hurt-only sheet, describe:

- impact
- recoil
- stagger
- recovery

### `combat`

For a compact combined non-hero sheet:

- top-left: attack wind-up
- top-right: attack strike
- bottom-left: hurt impact
- bottom-right: hurt recovery

Do not use `combat` for controllable hero body actions when separate action sheets are needed.

### `projectile`

Usually prefer `1x4` or `strip_1x4`.

Describe:

- same projectile identity in all frames
- travel direction stays consistent
- shape changes are small and loopable
- glow or trail stays inside the frame

### `impact` / `explode`

Usually prefer `2x2` or `strip_1x4`.

Describe:

- ignition or contact
- expansion
- peak burst
- fade or collapse

### `walk` / `run` / `hover`

State the travel behavior clearly:

- grounded stride
- hover bob
- crawl
- slither
- mechanical glide

## Sheet-Specific Rules

### `4x4` player sheet

Use:

- row 1: down
- row 2: left
- row 3: right
- row 4: up
- column 1: neutral
- column 2: left foot forward
- column 3: neutral again
- column 4: right foot forward

### `4x4` non-directional action sheet

Use only when explicitly planned as a 16-frame action sequence or engine atlas piece. State row-major frame order and use a layout guide. Do not let the model interpret it as four directions unless that is intended.

### `5x5` or `custom_grid`

Use a layout guide. State:

- exact row and column count
- row-major frame order
- one action or one asset family only
- no unrelated mixed actions unless this is an explicitly planned engine atlas
- final output must not contain guide lines or labels

### `3x3` large idle

Say:

- exactly 9 equal cells in a `3x3` grid
- same bounding box in all 9 cells
- subject fills only about 55% to 65% of each cell
- no edge crossing anywhere

### `1x4` projectile

Say:

- exactly 4 equal cells in one row
- same projectile size in every frame
- only the internal energy or shape pulse changes

## Mixed-Action Atlas Guardrail

Avoid prompts like `make one sheet with idle, walk, attack, shoot, cast, hurt, jump, death all together` unless the user explicitly needs an engine atlas and you have a layout guide.

Safer default:

- generate each action as its own raw sheet
- process each sheet independently
- QC each transparent output
- package the processed assets into the final bundle or engine atlas

If an atlas is required, describe every region by row/column range and use a layout guide.

## Bundle Prompting

When generating a bundle, write each asset prompt independently.

Good default decomposition:

- hero body cast sheet
- projectile
- impact

or:

- idle body sheet
- walk body sheet
- attack body sheet
- separate slash FX
- separate impact FX

or:

- map-matching prop pack
- one-by-one large prop
- foreground occluder prop

Do not try to force unrelated assets into one giant raw sheet.

## Quick Prompt Pattern

1. state the asset type and sheet shape
2. state the style source: project-native, map-matching, clean HD, or explicit pixel art
3. describe the subject identity
4. if applicable, state the reference role and invariants
5. if applicable, state the layout guide role and forbid copied guide marks
6. describe frame-by-frame motion
7. restate same-scale and containment rules
8. restate magenta background and no-text/no-grid rules
