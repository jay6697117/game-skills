# Game Character Sprites

Human-facing README for the `game-character-sprites` Claude Code skill.

This file is documentation for maintainers and users. Claude Code uses `SKILL.md` as the actual skill entrypoint and trigger source.

## Purpose

`game-character-sprites` helps Claude Code create game-ready fixed-cell pixel-art character animation assets from text concepts, reference images, or existing character art.

It is designed for:

- `32x32`, `64x64`, and `128x128` native pixel-art cells
- single-direction, 4-way, or 8-way character animation packs
- idle, walk/run, jump, attack, archer, caster, and similar action strips
- transparent atlas PNG outputs
- GIF/WebP preview exports
- reference-grounded generation with provenance checks
- targeted regeneration of weak directions or weak animation rows

## Important Runtime Rule

The skill must use `codex-gateway-imagegen` as the only real visual generation backend.

Do not replace it with:

- local drawing code
- procedural placeholder sprites
- text-only identity notes
- unrelated third-party art services
- a generic image generator without local file handoff

Generated art must become local files before the cleanup, assembly, validation, and preview scripts can process it.

## Skill Entry Point

Claude Code should load and follow:

```text
.claude/skills/game-character-sprites/SKILL.md
```

The README is not the skill trigger. Keep trigger wording and agent-facing workflow rules in `SKILL.md`.

## Supported Reference Inputs

The skill supports these reference sources:

1. Local image file path
2. Image URL
3. Visible image attachment in the current Claude Code conversation

If a chat attachment is used, the run manifest should record it as:

```json
{
  "source_type": "chat_attachment",
  "source": "attached image #1",
  "used_for_generation": true,
  "identity_notes": [
    "visible character details preserved from the reference"
  ]
}
```

Do not claim reference-grounded generation if the image was not actually used by `codex-gateway-imagegen`.

## Default Output Layout

A typical run should produce a workspace folder like this:

```text
run/
  run-manifest.json
  source/
    <generated-source-files>.png
  32/
    generated/
    frames/
    final/
    qa/
  64/
    generated/
    frames/
    final/
    qa/
  128/
    generated/
    frames/
    final/
    qa/
```

Exact folders depend on the requested sizes, actions, and directions.

## Native Size Rule

Requested sizes are hard deliverables.

If the user asks for `32x32`, `64x64`, and `128x128`, the skill should create native output sets for each requested size:

```text
run/32/...
run/64/...
run/128/...
```

Do not present scaled variants as native assets. A downscaled `64x64` sheet is not a native `32x32` sheet. An upscaled `64x64` sheet is not a native `128x128` sheet.

## Recommended Workflow

1. Confirm requested cell sizes, actions, directions, frame counts, and reference details.
2. Use `codex-gateway-imagegen` to generate reference-grounded source art as local PNG files.
3. Create `run/run-manifest.json` before generation and keep it updated.
4. Generate one action-direction-size strip at a time.
5. Assemble strips into action atlases.
6. Clean chroma-key backgrounds and pixel edges.
7. Validate sheet geometry, residue, motion, and provenance.
8. Export transparent WebP/GIF and checkerboard previews.
9. Manually inspect contact sheets and previews before final delivery.
10. Regenerate only weak rows or directions unless the user asks for a full redo.

## Bundled Resources

### `scripts/`

Reusable processing and validation scripts:

- `assemble_action_sheet.py` — assemble per-direction strips into action sheets
- `audit_sprite_motion.py` — detect weak motion and near-duplicate frames
- `export_animation_previews.py` — export GIF/WebP previews
- `import_imagegen_contact_sheet.py` — rescue diagnostic multi-size contact sheets when explicitly accepted
- `pixel_snap.py` — chroma-key cleanup, alpha cleanup, palette quantization, pixel snapping
- `validate_64_sheet.py` — legacy 64px validation helper
- `validate_resolution_hierarchy.py` — check structure consistency across 32/64/128 outputs
- `validate_run_manifest.py` — verify provenance, scope, visual review, and backend method
- `validate_sheet.py` — validate atlas geometry, residue, contact sheets, and frame occupancy
- `validate_sheet_impl.py` — shared validation implementation

When documenting or running bundled scripts from the skill, prefer:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/<script-name>.py" ...
```

### `references/`

Reference material loaded only when needed:

- `sheet-spec.md` — sprite sheet contract, provenance rules, validation expectations
- `visual-review-template.json` — template for manual visual QA results

### `assets/`

Static assets used for demonstration or packaging:

- `showcase-720p.mp4`

## Validation Checklist

Before calling a sprite pack complete, verify:

- `run/run-manifest.json` exists
- reference source is recorded
- `reference.used_for_generation` is `true`
- `generation.method` is `codex-gateway-imagegen`
- every generated strip records `method: "codex-gateway-imagegen"`
- `imagegen_output_path` points to real local files
- requested sizes, actions, and directions are present
- atlas dimensions match rows, columns, and cell size
- chroma-key residue is removed
- previews do not smear or accumulate transparency
- walk/run/jump frames have readable motion
- multi-size outputs preserve the same primary silhouette
- `qa/visual-review.json` exists and is accepted only after manual inspection

## Example Validation Commands

Syntax check all bundled Python scripts:

```bash
python3 -c 'import ast,pathlib; root=pathlib.Path(".claude/skills/game-character-sprites/scripts"); [ast.parse(p.read_text(encoding="utf-8"), filename=str(p)) for p in sorted(root.glob("*.py"))]; print("python syntax ok")'
```

Run a manifest validation after producing a run:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/validate_run_manifest.py" \
  --manifest path/to/run/run-manifest.json \
  --required-sizes 32,64,128 \
  --required-actions walk \
  --required-directions south \
  --require-visual-review
```

Export animation previews:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/export_animation_previews.py" \
  --atlas path/to/final/walk-sheet-clean.png \
  --rows 1 \
  --columns 6 \
  --cell 64 \
  --row-names south \
  --prefix walk \
  --out-dir path/to/qa/previews \
  --scale 4
```

## Maintenance Notes

When updating this skill:

- Keep `SKILL.md` as the source of agent-facing workflow rules.
- Keep README content human-facing and avoid duplicating every detail from `SKILL.md`.
- Do not loosen provenance validation unless the backend contract changes intentionally.
- Do not replace `codex-gateway-imagegen` with a generic backend name.
- Keep script examples compatible with Claude Code by using `${CLAUDE_SKILL_DIR}`.
- Keep generated or temporary files out of the skill directory.

## Quick Usage Example

Example user request:

```text
Use game-character-sprites to create a native 64x64 8-direction walk cycle from this reference image, with transparent GIF/WebP previews.
```

Expected high-level result:

```text
run/
  run-manifest.json
  source/
  64/generated/
  64/final/
  64/qa/
```

The final response should point to workspace paths for the final atlas, metadata, validation output, contact sheet, and preview files.
