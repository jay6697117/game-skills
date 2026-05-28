# Codex Skills 使用说明

本文档说明 `.codex/skills` 目录下的 Codex skill。它面向使用者和维护者，重点解释每个 skill 的定位、适用场景、使用方式、交付物、验证重点，以及功能相近 skill 之间的重叠与边界。

## 总览

`.codex/skills` 是 Codex 运行时版本。这里的 skill 与 `.claude/skills` 基本同源，但 Codex 版本有两个重要差异：

- 视觉资产默认使用 Codex 内置 `image_gen`，而不是强制经由 gateway helper。
- 每个 skill 额外包含 `agents/openai.yaml`，用于 Codex UI 展示、默认提示和隐式调用策略。

| Skill | 路径 | 核心定位 | Codex 特有点 |
|---|---|---|---|
| `codex-gateway-imagegen` | `.codex/skills/codex-gateway-imagegen` | 通过 Responses-compatible gateway 生成或编辑图片，并保存到工作区 | 可作为内置 `image_gen` 不可用时的 fallback |
| `generate2dmap` | `.codex/skills/generate2dmap` | 生成可玩 2D 地图、场景、关卡、props、collision 和 scene metadata | 默认用内置 `image_gen` 做视觉资产 |
| `generate2dsprite` | `.codex/skills/generate2dsprite` | 生成通用 2D sprite、props、FX、hero bundles、engine atlas | 默认用内置 `image_gen` 生成 raw sheet |
| `game-character-sprites` | `.codex/skills/game-character-sprites` | 固定 cell pixel-art 角色动画生产线 | 通过 Codex 图片输出路径做本地文件 handoff |

## Codex 运行时约定

- 显式调用时使用 `$skill-name` 形式，例如 `$generate2dmap`、`$generate2dsprite`、`$game-character-sprites`。
- `agents/openai.yaml` 的 `default_prompt` 是 Codex 侧 UI 和隐式调用的重要入口，不应随意删改。
- `generate2dmap` 和 `generate2dsprite` 默认使用内置 `image_gen` 生成视觉资产。
- `codex-gateway-imagegen` 是 gateway helper，在需要直接调用配置好的 Responses-compatible gateway 并保存本地文件时使用。
- Codex 侧文档和说明应优先引用 `.codex/skills/...`，不要把 `.claude/skills/...` 当作主路径。

## `codex-gateway-imagegen`

### 详细介绍

`codex-gateway-imagegen` 在 Codex 目录中扮演“直接走 configured gateway 的图片生成 helper”。它不是通用地图或 sprite 工作流，而是把 prompt、reference images、mask 和尺寸参数发送到 gateway，然后保存 PNG。

它读取：

- `~/.codex/config.toml` 中的 `base_url`
- `~/.codex/auth.json` 中的 `OPENAI_API_KEY`

并调用 `/responses`，通过 `image_generation` tool 完成生成或编辑。

### 使用场景

适合使用它的情况：

- 用户明确要求通过 gateway 生成图片并保存到当前 workspace。
- 内置 `image_gen` 路径不可用，或当前任务需要直接验证 gateway。
- 需要 image editing：本地参考图、远程参考图、多参考图或 mask。
- 需要把生成结果作为后续脚本输入，例如 sprite 切图或地图 prop extraction。

不适合使用它的情况：

- 任务本身是地图规划、sprite pipeline、animation QA，应优先调用对应的上层 skill。
- 只需要解释 prompt、写 JSON 或做代码集成，不需要生成 PNG。

### 使用指南

文生图：

```bash
python3 scripts/generate_gateway_image.py --prompt "<prompt>" --out "<output-path>" --size 1024x1024
```

参考图编辑：

```bash
python3 scripts/generate_gateway_image.py --prompt "<prompt>" --image "<reference-image>" --action edit --out "<output-path>" --size 1024x1536
```

关键参数：

- `--prompt`
- `--out`
- `--size`
- `--image`
- `--image-url`
- `--mask`
- `--action`
- `--model`
- `--timeout`
- `--max-retries`

### 关键优势

- 能独立验证和使用 gateway 配置。
- 支持 image generation 和 image editing。
- 保存结果路径明确，适合后续本地 pipeline。
- 在内置 `image_gen` 之外提供稳定 fallback。

## `generate2dmap`

### 详细介绍

`generate2dmap` 是 Codex 侧生产导向 2D 地图 skill。它默认使用内置 `image_gen` 生产视觉资产，同时负责地图 pipeline 选择、runtime object model、collision model、scene hooks、engine/export target 和 QA preview。

它不是单图 prompt helper。对任何可玩 map、level、stage、room、prototype 或 engine scene，默认不接受“只有一张 baked image”作为 runtime map。可玩地图必须暴露 gameplay geometry、object layers、props、collision、zones 或 engine-native scene nodes。

### 使用场景

优先用 `generate2dmap` 的情况：

- 用户要求 RPG 地图、monster-taming route、town、dungeon、shrine、arena。
- 用户要求 side-scroller、platformer、runner、Metroidvania、parallax stage。
- 用户要求 tactical grid、factory grid、board-like battler、terrain-cost map。
- 用户要求 roguelike room、room chunks、modular interior。
- 用户要求 battle background、title/menu scene、visual novel background。
- 用户需要 prop pack、collision zones、walkable areas、spawn/exits、camera bounds、scene hooks。

不要用它处理：

- character、enemy、NPC、boss、projectile、impact、animation sprite。
- 单独的 projectile、spell FX 或 hero action bundle。

### 使用指南

推荐流程：

1. 读取目标项目的相机、坐标、asset loading、collision、zone 和 map schema。
2. 选择 `map_mode`：`tile_mode`、`scene_mode`、`side_scroll_mode`、`grid_mode`、`room_chunk_mode`、`baked_scene_mode`。
3. 选择 `visual_model`、`runtime_object_model`、`collision_model`、`engine_target`。
4. 用内置 `image_gen` 生成可见资产，prompt 必须由 agent 手写。
5. 可玩 layered map 先生成 foundation-only base，不把 props、actors、doors、hazards、pickups、foreground occluders 烘焙进 base。
6. 需要 reference mockup 时，先让 base 图片在会话上下文中可见，再调用 `image_gen` 生成 dressed reference 或 stage reference。
7. reference mockup 不作为最终 runtime map；后续必须产出 separate objects、placement metadata、collision、scene hooks 和 preview。
8. prop/object 生成前先分类，只有 compact props 适合 square prop pack。
9. side-scroll mode 必须先确定 `stage_canvas`，primary parallax layers、stage reference 和 stage preview 尺寸/比例/构图一致。
10. 最后验证图片尺寸、prompt metadata、JSON、collision、object references 和 QA preview。

常用脚本：

```bash
python scripts/extract_prop_pack.py --input "assets/props/raw/forest-props-sheet.png" --rows 3 --cols 3 --output-dir "assets/props" --manifest "assets/props/forest-prop-pack.json" --labels "rock,shrub,log,lamp,sign,flower,stump,crate,grass" --reject-edge-touch
```

```bash
python scripts/compose_layered_preview.py --base "assets/map/shrine-base.png" --placements "data/shrine-props.json" --output "assets/map/shrine-layered-preview.png" --report "assets/map/shrine-layered-preview.report.json" --project-root "."
```

### 关键优势

- 默认贴合 Codex 的内置 `image_gen` 能力。
- 地图 pipeline 覆盖从 flat background 到 playable parallax stage 的多种复杂度。
- 明确禁止把可玩地图简化为单张运行时图片。
- 对 prop classification、stage reference、parallax layer consistency 和 collision metadata 有严格规则。

## `generate2dsprite`

### 详细介绍

`generate2dsprite` 是 Codex 侧通用 2D sprite 和 sprite sheet 生产 skill。它从自然语言推断 asset plan，使用内置 `image_gen` 生成 raw sheet，再使用本地 Python processor 做 chroma-key cleanup、frame extraction、alignment、QC、transparent export 和 GIF export。

它适合处理：

- pixel-art sprites
- clean HD map props
- creatures
- characters
- NPCs
- spells
- projectiles
- impacts
- summons
- FX
- hero action bundles
- engine atlas

### 使用场景

优先用 `generate2dsprite` 的情况：

- 用户要求单个 sprite 或 animation sheet。
- 用户要求 hero idle/run/shoot/jump/attack/cast bundle。
- 用户要求 projectile、impact、explode、spell FX。
- 用户要求与地图风格匹配的透明 prop。
- 用户要求 `Phaser`、`Unity`、`Godot` 或项目自定义 atlas，但需要先生成和 QC 单独 action sheet。

不要用它处理：

- 地图结构、stage canvas、parallax layers、collision、zones、scene hooks。
- 严格 `32x32`、`64x64`、`128x128` native fixed-cell 角色包，优先用 `game-character-sprites`。

### 使用指南

推荐流程：

1. 推断 `asset_type`、`action`、`view`、`sheet`、`frames`、`bundle`、`art_style`、`reference`、`layout_guide`。
2. 对 controllable hero/main character，多动作时使用 `hero_action_bundle`，不要让内置 `image_gen` 一次生成混合动作 raw atlas。
3. 对 attack/shoot/cast body sheet 默认 body-only；slash、muzzle flash、projectile、dust、impact 分离。
4. 不要默认用 raw `1x4`、`1x6`、`1x8` 给角色身体动画；先生成 multi-row grid，再按需要确定性组装 engine strip。
5. 对 map props 先分类；square prop pack 只用于 compact props。
6. 对 fragile layout 先用 `make_layout_guide.py` 创建 layout guide，再让 `image_gen` 参考。
7. `image_gen` 生成 raw PNG 后，复制或引用到工作输出目录。
8. 使用 `generate2dsprite.py process` 后处理并生成 transparent output 和 metadata。
9. 检查 edge touch、scale drift、FX 分离、body height、GIF 预览。

layout guide 示例：

```bash
python scripts/make_layout_guide.py --rows 4 --cols 4 --cell-width 384 --cell-height 384 --output assets/sprites/hero/references/4x4-layout-guide.png
```

postprocess 示例：

```bash
python scripts/generate2dsprite.py process --input "assets/sprites/hero/raw-idle.png" --target player --mode idle --output-dir "assets/sprites/hero/idle" --rows 2 --cols 2 --shared-scale --align feet --reject-edge-touch
```

### 关键优势

- Codex 内置 `image_gen` 直连，适合快速进入本地后处理。
- 资产类型宽，覆盖 sprite、prop、FX、projectile、impact、bundle、atlas。
- 对 hero body-only、single-row body 禁用、map prop pack 分类有清晰 guardrails。
- 能把视觉生成和确定性 engine packaging 分开，减少大 atlas 一次失败的概率。

## `game-character-sprites`

### 详细介绍

`game-character-sprites` 是 Codex 侧固定 cell 像素角色动画生产线。它比 `generate2dsprite` 更专门，强调 native cell size、方向、动作、reference provenance、manual visual review 和多尺寸 hierarchy。

它适合从文本概念、参考图或已有角色图生成游戏可用的角色 spritesheets。

### 使用场景

优先用 `game-character-sprites` 的情况：

- 用户明确要 fixed-cell pixel-art character。
- 用户指定 `32x32`、`64x64`、`128x128` 中一个或多个 native sizes。
- 用户要求 4-way 或 8-way movement。
- 用户要求 idle、walk/run、jump、attack、archer、caster 等角色动作。
- 用户要求 GIF/WebP preview。
- 用户要求参考图一致性、provenance 和 visual QA。
- 用户只想重做部分方向或弱动画行。

不要用它处理：

- clean HD map props、spell FX、projectile、impact，优先 `generate2dsprite`。
- map layout、collision、zones、scene hooks，优先 `generate2dmap`。
- 纯 gateway 图片生成，优先 `codex-gateway-imagegen`。

### 使用指南

推荐流程：

1. 明确 cell size、actions、directions、frame count、reference details。
2. 如果用户指定多个 native sizes，每个 size 都需要独立图像生成输出。
3. 不要用一个 multi-size contact sheet 直接冒充 native 输出。
4. 先接受 `32x32` primary silhouette 和 pose timing，再生成 `64x64`、`128x128`。
5. 每个 action-direction-size 单独生成。
6. 创建并维护 `run/run-manifest.json`。
7. 用 bundled scripts assemble、pixel snap、validate、audit motion、export previews。
8. 写 `qa/visual-review.json`，只有人工确认 reference、direction、animation readability 后才接受。
9. 对弱方向 targeted regeneration，不要重做强行。

典型输出结构：

```text
run/
  run-manifest.json
  source/
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

### 关键优势

- fixed-cell pixel-art character 的流程最完整。
- 对 `32/64/128` native hierarchy 的定义清楚。
- 对 reference-grounded generation 和 manifest 验收严格。
- 支持 GIF/WebP preview 和 targeted regeneration。

## 相似 skill 对比

### `generate2dsprite` 与 `game-character-sprites`

| 维度 | `generate2dsprite` | `game-character-sprites` |
|---|---|---|
| 定位 | 通用 2D sprite/prop/FX/bundle/atlas | 固定 cell pixel-art character pipeline |
| 风格 | `pixel_art`、`clean_hd`、`pixel_inspired`、`map_style`、`project-native` | 主要服务 fixed-cell pixel art |
| 尺寸规则 | 根据 sheet 和 bundle 推断 | `32`、`64`、`128` native sizes 是硬约束 |
| 多动作 | `hero_action_bundle`，每个动作单独 QC 后组 atlas | action-direction-size strip 为核心 |
| 适合 | props、projectile、impact、FX、clean HD asset、general hero bundle | 8-way walk、native multi-size character、reference-grounded角色包 |

互补方式：

- 主角/NPC 的严格 fixed-cell movement pack 用 `game-character-sprites`。
- 同一角色的 projectile、impact、weapon FX、map pickup、engine atlas packaging 用 `generate2dsprite`。

### `generate2dmap` 与 `generate2dsprite`

| 维度 | `generate2dmap` | `generate2dsprite` |
|---|---|---|
| 负责对象 | 地图、关卡、场景、runtime object plan | 可复用透明图片、动画帧、FX、atlas |
| 关键数据 | collision、zones、scene hooks、placement、stage canvas | frames、transparent sheet、GIF、pipeline metadata |
| props 重叠 | 负责分类、放置、碰撞、preview | 负责生成透明 prop 图片和 sheet cleanup |
| 典型组合 | 先做 map base 和 object list | 再生成 props/objects，回填到 map preview |

互补方式：

- `generate2dmap` 先定义哪里需要树、石头、门、平台、hazard。
- `generate2dsprite` 生成这些对象的透明 asset。
- `generate2dmap` 再写 placement/collision 并合成 QA preview。

### `codex-gateway-imagegen` 与内置 `image_gen`

| 维度 | `codex-gateway-imagegen` | 内置 `image_gen` |
|---|---|---|
| 使用位置 | 显式 gateway fallback 或直接 gateway 调用 | Codex skill 默认视觉生成路径 |
| 输出方式 | helper 保存到用户指定路径 | Codex 环境生成后再做 file handoff |
| 配置依赖 | `~/.codex/config.toml`、`~/.codex/auth.json` | 平台内置能力 |
| 适合 | 验证 gateway、需要直接 Responses-compatible path、内置路径不可用 | 日常地图/sprite视觉生成 |

## 快速选择指南

| 用户需求 | 推荐 skill |
|---|---|
| “用 Codex 生成一张图并保存到当前目录” | `$codex-gateway-imagegen` 或内置 `image_gen`，取决于是否必须走 gateway |
| “做一个可玩的 side-scroller stage” | `$generate2dmap` |
| “做 tower defense 地图和 build slots” | `$generate2dmap` |
| “做 hero idle/run/shoot/jump bundle” | `$generate2dsprite` |
| “做 fireball projectile 和 explosion impact” | `$generate2dsprite` |
| “做 64x64 八方向像素角色 walk pack” | `$game-character-sprites` |
| “做 32/64/128 native 多尺寸角色动画” | `$game-character-sprites` |
| “给地图生成一组 matching props 并放回地图” | `$generate2dmap` 统筹，必要时 `$generate2dsprite` 生成资产 |

## 维护规则

- Codex 文档和提示应优先引用 `.codex/skills/...`。
- `agents/openai.yaml` 是 Codex 侧重要入口，修改前要确认 default prompt 与 `SKILL.md` 保持一致。
- 不要把 Claude 侧 `${CLAUDE_SKILL_DIR}` 写成 Codex 侧主流程。
- `generate2dmap` 不应该生成角色和动画 sprite。
- `generate2dsprite` 不应该承担地图 collision、zones、scene hooks。
- `game-character-sprites` 不应该弱化 native size、provenance 和 visual review 规则。
