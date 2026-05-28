# Claude Skills 使用说明

本文档说明 `.claude/skills` 目录下的 Claude Code skill。它面向使用者和维护者，重点解释每个 skill 的定位、适用场景、使用方式、交付物、验证重点，以及功能相近 skill 之间的重叠与边界。

## 总览

`.claude/skills` 是 Claude Code 运行时版本。这里的核心特征是：所有需要真实视觉生成的流程都通过 `codex-gateway-imagegen` 这个本地 gateway skill 生成可落盘图片，然后再由地图或 sprite skill 的 Python 脚本做确定性后处理、校验和打包。

| Skill | 路径 | 核心定位 | 主要输出 |
|---|---|---|---|
| `codex-gateway-imagegen` | `.claude/skills/codex-gateway-imagegen` | 通过 Codex Responses-compatible gateway 生成或编辑图片，并保存到当前工作区 | PNG 图片、本地文件路径 |
| `generate2dmap` | `.claude/skills/generate2dmap` | 生成和集成可用于游戏运行时的 2D 地图、关卡、场景、props、碰撞和 metadata | 地图图片、分层 props、collision/zones JSON、scene hooks、preview |
| `generate2dsprite` | `.claude/skills/generate2dsprite` | 生成通用 2D sprite、透明 props、FX、projectile、impact、hero action bundle 和 engine atlas | raw sheet、transparent sheet、frames、GIF、metadata |
| `game-character-sprites` | `.claude/skills/game-character-sprites` | 生产固定 cell 的像素风角色动画包，强调 `32x32`/`64x64`/`128x128` native 输出和多方向一致性 | action atlas、frames、manifest、QA JSON、GIF/WebP previews |

## Claude 运行时约定

Claude 版本和 Codex 版本的能力很接近，但运行时约定不同：

- Claude 版本调用 bundled script 时应使用 `${CLAUDE_SKILL_DIR}`。
- Claude 版本不直接调用内置图片生成工具；视觉资产生成统一通过 `codex-gateway-imagegen`。
- `codex-gateway-imagegen` 会读取 `~/.codex/config.toml` 和 `~/.codex/auth.json`，调用 gateway 的 `/responses` 接口。
- 地图、sprite、角色动画 skill 的脚本只负责后处理、切图、清理、校验、预览和 metadata，不应该用脚本绘制最终视觉资产。
- 如果图片生成失败，要先区分网络/TLS/sandbox 路径问题、gateway 业务错误、图片生成限流，不要盲目改 prompt。

## `codex-gateway-imagegen`

### 详细介绍

`codex-gateway-imagegen` 是 Claude 目录中所有视觉资产生成的基础能力。它把手写 prompt、可选参考图、可选 mask 发送到已配置的 Responses-compatible gateway，并把返回的 base64 图片保存成本地 PNG。

它支持两类任务：

- 文生图：根据生产级 prompt 生成新图片。
- 图像编辑：基于一个或多个本地图片或远程图片做风格保持、局部修改、参考图延展。

### 使用场景

适合使用它的情况：

- 用户直接要求生成一张图片、海报、游戏素材、截图风格图。
- 其他 Claude skill 需要先得到本地 PNG 才能继续切图、清理、提取或验证。
- 内置图片生成路径不可用，但 Codex gateway 已配置。
- 需要对已有图片做参考图编辑，例如保留角色、场景构图或产品外观。
- 需要把生成结果固定保存到工作区，而不是只在会话里展示。

不适合使用它的情况：

- 只需要结构化 JSON、碰撞数据、地图 metadata，不需要生成视觉图片。
- 只是要 postprocess 已有图片，此时应由 `generate2dmap`、`generate2dsprite` 或 `game-character-sprites` 的脚本处理。
- 用户只要求解释 prompt 或写规划，不要求生成图片。

### 使用指南

典型流程：

1. 明确是 `generate` 还是 `edit`。
2. 明确输出路径，尽量保存在当前项目工作区。
3. 根据目标选择尺寸：方图常用 `1024x1024`，竖图常用 `1024x1536`，横图常用 `1536x1024`。
4. 写完整生产规格 prompt：主体、场景、风格、构图、光照、画幅、禁止项、需要保留的参考图特征。
5. 调用 helper script。
6. 如果返回 rate limit，保持同一个 prompt、图片、尺寸和 action，等待后重试。
7. 报告本地输出路径。

常用命令形态：

```bash
python "${CLAUDE_SKILL_DIR}/scripts/generate_gateway_image.py" --prompt "<prompt>" --out "<output-path>" --size 1024x1024
```

编辑本地参考图：

```bash
python "${CLAUDE_SKILL_DIR}/scripts/generate_gateway_image.py" --prompt "<prompt>" --image "<reference-image>" --action edit --out "<output-path>" --size 1024x1536
```

### 关键优势

- 能把生成结果稳定保存为本地文件，方便后续脚本消费。
- 支持多个参考图和 mask。
- 内置对图片生成限流的重试策略。
- 对 Claude 侧其他 skill 来说，它提供了统一的视觉生成后端。

### 维护提示

- 不要把 prompt 简化当成限流修复手段。
- 看到 HTTP 错误时先打印错误 body，再决定是请求参数问题还是环境问题。
- 如果 gateway 最低像素预算变化，优先调大 size，而不是反复提交同一非法尺寸。

## `generate2dmap`

### 详细介绍

`generate2dmap` 用于生产导向的 2D 游戏地图、关卡、场景和地图资产包。它不是“生成一张漂亮地图图”的简单工具，而是一个把视觉资产、可玩结构、runtime objects、collision、zones、scene hooks 和引擎格式串起来的地图工作流。

它的第一决策是 `map_mode`：

| `map_mode` | 适用方向 | 典型交付 |
|---|---|---|
| `tile_mode` | RPG、monster-taming、Tiled、LDtk、Godot TileMap、Unity Tilemap、grid-perfect 编辑器流程 | tileset、tile layers、object layers、tile collision、preview |
| `scene_mode` | 塔防、幸存者、固定视角探索、top-down showcase、base map plus props | foundation base、props、placement JSON、collision/zones、preview |
| `side_scroll_mode` | platformer、runner、Metroidvania、横版射击、beat-em-up、parallax stage | parallax layers、platform objects、hazards、collision、scene hooks、stage preview |
| `grid_mode` | tactical RPG、棋盘战斗、建造格、工厂自动化、terrain-cost map | grid art、cell metadata、blocked/buildable cells、object layers |
| `room_chunk_mode` | roguelike room、模块化地牢、procedural chunk、prefab room | chunk art、socket metadata、collision、spawn/exit hooks |
| `baked_scene_mode` | 战斗背景、标题图、视觉小说背景、概念图、明确不可编辑的平面背景 | 单张 PNG、可选 rough zones |

### 使用场景

优先用 `generate2dmap` 的情况：

- 用户要求地图、关卡、房间、路线、城镇、arena、stage、battle background。
- 地图需要可玩，不只是展示图。
- 需要明确 walkable area、blockers、spawn、exit、camera bounds、trigger zones。
- 需要分层地图：地面 base、可复用 props、前景遮挡、y-sort、碰撞。
- 需要 side-scroller/parallax 背景和平台对象。
- 需要 prop pack、地图预览、Tiled/LDtk/Godot/Unity/project-native metadata。

不要用它处理：

- 玩家角色、NPC、敌人、boss、投射物、技能 FX、动画 sheet。这些属于 `generate2dsprite` 或 `game-character-sprites`。
- 只需要单个透明 prop，且不涉及地图结构时，优先用 `generate2dsprite`。
- 用户明确只要角色固定 cell pixel-art animation pack 时，优先用 `game-character-sprites`。

### 使用指南

推荐工作流：

1. 先检查目标游戏：相机尺寸、坐标系、资源加载方式、碰撞格式、现有地图 schema。
2. 选择 `map_mode`，再选择 `visual_model`、`runtime_object_model`、`collision_model`、`engine_target`。
3. 如果是可玩地图，不要把单张 baked image 当 runtime map，除非用户明确只要 flat background。
4. 通过 `codex-gateway-imagegen` 生成 foundation-only base。base 只能包含地面、道路、水、悬崖、低矮地形，不应烘焙 runtime props。
5. 如需 props，基于 base 生成 dressed reference，但 dressed reference 只是规划 artifact。
6. 从 reference 中列出最终 runtime objects，并分类：compact prop、wide/long object、tall/large object、collision-bearing object、tileset/strip piece。
7. 用合适策略生成 props：one-by-one、prop pack、platform strip、custom wide pack 或 tile/object layer。
8. 写 placement、collision、zones、scene hooks。
9. 用 bundled script 合成 QA preview。
10. 验证图片尺寸、JSON 可解析性、collision/zone 可达性、base 是否仍然干净。

常用脚本：

```bash
python "${CLAUDE_SKILL_DIR}/scripts/extract_prop_pack.py" --input "assets/props/raw/forest-props-sheet.png" --rows 3 --cols 3 --output-dir "assets/props" --manifest "assets/props/forest-prop-pack.json" --labels "rock,shrub,log,lamp,sign,flower,stump,crate,grass" --reject-edge-touch
```

```bash
python "${CLAUDE_SKILL_DIR}/scripts/compose_layered_preview.py" --base "assets/map/shrine-base.png" --placements "data/shrine-props.json" --output "assets/map/shrine-layered-preview.png" --report "assets/map/shrine-layered-preview.report.json" --project-root "."
```

### 交付物建议

对可玩 layered raster map，合理交付包括：

- foundation-only base image
- base prompt
- dressed reference
- transparent prop assets
- prop placement JSON
- collision JSON
- zones JSON
- scene hooks
- flattened QA preview
- 加载这些资产和 metadata 的项目代码变更

对 side-scroller stage，合理交付包括：

- `sky`、`far_bg`、`mid_bg`、`near_bg`、可选 `foreground_overlay`
- 统一的 `stage_canvas`
- stage reference
- separate platform/hazard/pickup/door/checkpoint assets
- objects JSON
- scene hooks JSON
- collision JSON
- stage preview

### 关键优势

- 把“图像生成”提升到“可玩地图 bundle”层级。
- 明确区分 base、reference、props、collision、zones、preview，避免把所有东西烘焙进一张图。
- 对 side-scroll/parallax stage 有严格尺寸、层级和 collision 约束。
- 有 prop pack extraction 和 layered preview composer，便于从视觉图走向 runtime 资产。

## `generate2dsprite`

### 详细介绍

`generate2dsprite` 是通用 2D sprite 资产生产 skill。它覆盖角色、生物、NPC、透明 props、projectile、impact、spell FX、hero action bundle、line bundle 和 engine atlas。

它和 `game-character-sprites` 的区别是：`generate2dsprite` 更通用，不只做固定 cell 像素角色；它也可以做 clean HD map props、FX、投射物、非像素风 game-ready 资产，以及按引擎需要组装 atlas。

### 使用场景

优先用 `generate2dsprite` 的情况：

- 用户要求普通 sprite、透明 prop、projectile、impact、spell、FX、boss idle、monster line。
- 地图流程中需要生成单个可复用 prop，或少量 matching map style 的 props。
- 需要 hero action bundle，例如 idle、run、jump、shoot、attack、cast。
- 需要把 raw generated sheet 清理成 transparent sheet、frame PNG 和 GIF。
- 需要生成 engine atlas，但希望先逐 action 做 QC，再确定性组装。

不要用它处理：

- 地图结构、关卡布局、collision zones、scene hooks，这些属于 `generate2dmap`。
- 严格 `32x32`、`64x64`、`128x128` native pixel character pack，尤其是多方向、多尺寸一致性验证，优先 `game-character-sprites`。
- 纯图片生成，不需要 sheet postprocess 时，可直接用 `codex-gateway-imagegen`。

### 使用指南

推荐工作流：

1. 从用户自然语言推断 `asset_type`、`action`、`view`、`sheet`、`frames`、`bundle`、`art_style`、`reference`。
2. 对 hero/main character 的 `attack`、`shoot`、`cast` body sheet，默认 body-only，slash、muzzle、projectile、impact、dust 独立生成。
3. 不要默认用 raw single-row body sheet。角色身体动画优先用 `2x2`、`2x3`、`2x4`、`3x4`、`4x4` 或 custom grid。
4. 对 fragile grid、hero action bundle、5x5、custom grid、拥挤 prop pack，先生成 layout guide。
5. 手写 prompt，并要求 solid `#FF00FF` background、exact grid、same identity、same scale、no text、no grid lines、no edge crossing。
6. 通过 `codex-gateway-imagegen` 生成 raw PNG。
7. 用 `generate2dsprite.py process` 做 chroma-key cleanup、frame splitting、alignment、QC metadata、transparent export、GIF export。
8. 视觉检查结果，必要时只重生成失败动作或失败 sheet。

layout guide 示例：

```bash
python "${CLAUDE_SKILL_DIR}/scripts/make_layout_guide.py" --rows 5 --cols 5 --cell-width 384 --cell-height 384 --safe-margin-x 52 --safe-margin-y 52 --output "assets/sprites/hero/layout-guide.png"
```

postprocess 示例：

```bash
python "${CLAUDE_SKILL_DIR}/scripts/generate2dsprite.py" process --input "assets/sprites/hero/raw-shoot-body.png" --target player --mode shoot --output-dir "assets/sprites/hero/shoot-body" --rows 2 --cols 2 --shared-scale --align feet --reject-edge-touch
```

### 关键优势

- 资产类型覆盖面广，不限于角色。
- 能处理 clean HD、map style、pixel art、project-native 等风格。
- 对 hero action body-only、FX 分离、single-row body 禁用有明确规则，避免固定 cell 角色被宽特效压缩。
- 能先分 action 做 QC，再组装 engine atlas，降低一次性大图失败风险。

## `game-character-sprites`

### 详细介绍

`game-character-sprites` 是更严格、更专门的固定 cell 像素角色动画生产线。它的核心目标是生成能进游戏的 character spritesheets，而不是泛化的 sprite 或 props。

它支持：

- `32x32`、`64x64`、`128x128` native cell。
- 单方向、4-way、8-way directions。
- idle、walk/run、jump、attack、archer、caster 等动作。
- per-direction targeted regeneration。
- transparent atlas PNG。
- GIF/WebP previews。
- run manifest、provenance、visual review、resolution hierarchy QA。

### 使用场景

优先用 `game-character-sprites` 的情况：

- 用户明确要固定 cell 像素角色，例如 `64x64 walk south 6 frames`。
- 用户要求同一角色的 `32x32`、`64x64`、`128x128` native 输出。
- 用户要求 4-way 或 8-way movement pack。
- 用户提供角色参考图，并要求保留身份特征。
- 用户要求 GIF/WebP 预览和可审计 provenance。
- 之前生成结果部分方向弱，需要只重做 weak rows。

不适合用它的情况：

- 非角色地图 props、FX、projectile、impact，优先 `generate2dsprite`。
- 地图、关卡、场景，优先 `generate2dmap`。
- clean HD 非像素角色资产，优先 `generate2dsprite`。

### 使用指南

推荐工作流：

1. 确定 cell sizes、actions、directions、frame count、reference details。
2. 对用户指定的每个 native cell size 都单独生成，不用一个 multi-size contact sheet 充当 native 输出。
3. 先锁定最小尺寸，通常是 `32x32` 的 silhouette、比例、pose timing 和主色块。
4. 再用已接受的低分辨率结构约束 `64x64` 和 `128x128`，只增加细节，不改变主轮廓和动作结构。
5. 每个 action-direction-size 单独通过 `codex-gateway-imagegen` 生成 source PNG。
6. 更新 `run/run-manifest.json`，记录 reference、scope、generation method、imagegen output path、prompt path。
7. 用 assembler 合成 action atlas。
8. 用 `pixel_snap.py` 清理 chroma key 和像素边缘。
9. 用 `validate_sheet.py`、`audit_sprite_motion.py`、`validate_resolution_hierarchy.py`、`validate_run_manifest.py` 做几何、运动、多尺寸和 provenance 验证。
10. 导出 transparent WebP/GIF 和 checkerboard GIF。
11. 人工检查 contact sheet 和 preview，写入 `qa/visual-review.json`。

常用验证命令：

```bash
python "${CLAUDE_SKILL_DIR}/scripts/validate_run_manifest.py" --manifest path/to/run/run-manifest.json --required-sizes 32,64,128 --required-actions walk --required-directions south --require-visual-review
```

```bash
python "${CLAUDE_SKILL_DIR}/scripts/export_animation_previews.py" --atlas path/to/final/walk-sheet-clean.png --rows 1 --columns 6 --cell 64 --row-names south --prefix walk --out-dir path/to/qa/previews --scale 4
```

### 关键优势

- 对 fixed-cell pixel-art character 的生产约束最强。
- 多尺寸 native 输出有明确 hierarchy，不会把 resize 伪装成 native。
- provenance 和 visual review gate 能防止把 procedural/test fixture 当成真实角色资产。
- targeted regeneration 避免重做已经合格的方向和动作。

## 相似 skill 对比

### `generate2dsprite` 与 `game-character-sprites`

| 维度 | `generate2dsprite` | `game-character-sprites` |
|---|---|---|
| 核心定位 | 通用 2D sprite/prop/FX/bundle 生产 | 固定 cell pixel-art 角色动画生产 |
| 风格范围 | `clean_hd`、`pixel_art`、`map_style`、`project-native` | 主要是 fixed-cell pixel-art character |
| 资产范围 | 角色、生物、NPC、props、projectile、impact、FX、atlas | 角色动画、方向行、动作行、native cell sizes |
| 多尺寸规则 | 可按需求处理，但不是核心强约束 | `32/64/128` native hierarchy 是核心能力 |
| 验证重点 | edge touch、scale drift、body-only、FX split、transparent output | manifest、provenance、direction、motion、hierarchy、visual review |
| 最适合 | “给这个地图做几个透明 props”、“做一个 hero shoot bundle”、“做 projectile/impact” | “按参考图做 64x64 八方向 walk/attack 角色包” |

互补关系：

- `game-character-sprites` 适合严格角色动画主线。
- `generate2dsprite` 适合角色以外的 sprite 资产、特效、投射物、地图 props，以及不需要 `32/64/128` hierarchy 的角色动作。
- 同一游戏里可以用 `game-character-sprites` 做主角/NPC fixed-cell 动画，用 `generate2dsprite` 做武器、projectile、impact、pickup 和地图小物件。

重叠点：

- 两者都能处理角色动画 sheet。
- 两者都要求真实图片生成先发生，再由脚本做 cleanup、frame extraction、GIF export。
- 两者都关注 frame containment、scale consistency、edge touch 和 visual QA。

关键区别：

- `game-character-sprites` 的验收更严格，尤其是 reference provenance、native multi-size 和 direction rows。
- `generate2dsprite` 的 asset taxonomy 更宽，能覆盖 map props、FX、projectile、spell bundle 和 engine atlas。

### `generate2dmap` 与 `generate2dsprite`

| 维度 | `generate2dmap` | `generate2dsprite` |
|---|---|---|
| 核心对象 | 地图、场景、关卡、房间、stage | 角色、props、FX、projectile、impact、sprite sheet |
| Runtime 关注点 | collision、zones、scene hooks、object placement、camera bounds | transparent assets、frame sheets、animation previews、atlas |
| 图片层级 | base、dressed reference、props、preview、parallax layers | raw sheet、clean sheet、transparent frames、GIF |
| 不该做的事 | 不生成角色/敌人/NPC/动画 sprite | 不负责地图碰撞、路径、spawn、exit、scene hooks |
| 最佳协作 | 地图 skill 列出 object plan，然后调用 sprite skill 生产 props/objects | sprite skill 生成透明对象，再回到地图 skill 放置和预览 |

互补关系：

- `generate2dmap` 定义地图结构和对象需求。
- `generate2dsprite` 生产地图中需要独立渲染的透明 props、platform pieces、pickup、hazard、checkpoint、door 等。
- 地图预览由 `generate2dmap` 合成，sprite 资产由 `generate2dsprite` 提供。

重叠点：

- 两者都可能涉及 props。
- `generate2dmap` 有 prop pack extraction；`generate2dsprite` 也可以生成 prop packs 或 one-by-one props。

边界建议：

- 需要放进地图坐标、碰撞、y-sort 或 scene hooks 的对象，由 `generate2dmap` 统筹。
- 需要生成透明图片、动画帧或 GIF 的对象，由 `generate2dsprite` 执行。

### `codex-gateway-imagegen` 与其他 skill

| 维度 | `codex-gateway-imagegen` | 其他三个 skill |
|---|---|---|
| 核心职责 | 生成或编辑图片并落盘 | 把图片变成游戏资产、metadata、preview、验证结果 |
| 输入 | Prompt、reference images、mask、size、action | 用户目标、项目结构、已生成图片、脚本参数 |
| 输出 | PNG | 地图 bundle、sprite bundle、QA artifacts |
| 是否懂游戏结构 | 不负责 | 负责 |

互补关系：

- `codex-gateway-imagegen` 是视觉生成源。
- `generate2dmap`、`generate2dsprite`、`game-character-sprites` 是生产流程和质量控制层。

## 快速选择指南

| 用户需求 | 推荐 skill |
|---|---|
| “生成一张横版游戏背景图” | `codex-gateway-imagegen`，如果只是单图；`generate2dmap`，如果要 stage/runtime metadata |
| “做一个可玩的 top-down 村庄地图” | `generate2dmap` |
| “给这个地图做 9 个小 props” | `generate2dmap` 统筹 prop plan，必要时调用 `generate2dsprite` |
| “做一个火球 projectile 和爆炸 impact” | `generate2dsprite` |
| “做主角 idle/run/jump/shoot bundle” | `generate2dsprite` |
| “按参考图做 64x64 八方向 walk 角色动画” | `game-character-sprites` |
| “同时要 32x32、64x64、128x128 native 角色动画” | `game-character-sprites` |
| “已有图片要用 gateway 重新风格化并保存到 workspace” | `codex-gateway-imagegen` |

## 维护规则

- 修改 Claude skill 文档或示例命令时，优先使用 `${CLAUDE_SKILL_DIR}`。
- 不要把 Codex-only `$imagegen`、`view_image` 或 `$generate2dsprite` 写成 Claude 侧唯一流程。
- 不要把脚本绘制当成真实视觉资产生成。
- `generate2dmap` 和 `generate2dsprite` 的边界要保持清楚：地图结构归地图，透明资产和动画归 sprite。
- `game-character-sprites` 的 native multi-size、manifest 和 visual review gate 不要弱化。
