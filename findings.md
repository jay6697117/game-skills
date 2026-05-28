# Findings & Decisions

## Requirements
- 目标目录：`.claude/skills` 与 `.codex/skills`。
- 输出文件：`CLAUDE_README.md`、`CODEX__README.md`、`README.md`。
- 文档内容必须覆盖：skill 详细介绍、使用场景、使用指南、相似功能对比、互补关系、重叠点、差异、各自优势。
- 代码、命令和标识符保持英文；正文使用简体中文。

## Research Findings
- 两个目录都包含同一组核心 skill：`codex-gateway-imagegen`、`game-character-sprites`、`generate2dmap`、`generate2dsprite`。
- `.codex/skills` 额外包含每个 skill 的 `agents/openai.yaml`，用于 Codex UI 展示、默认提示和隐式调用策略。
- `codex-gateway-imagegen` 是 Responses-compatible gateway 的图片生成/编辑 helper，读取 `~/.codex/config.toml` 和 `~/.codex/auth.json`，输出本地 PNG。
- Claude 版 `codex-gateway-imagegen` 示例使用 `${CLAUDE_SKILL_DIR}/scripts/generate_gateway_image.py`；Codex 版示例使用 skill 目录内 `scripts/generate_gateway_image.py`。
- Claude 版 `generate2dmap`、`generate2dsprite`、`game-character-sprites` 的原始视觉资产生成必须通过 `codex-gateway-imagegen`；Codex 版默认使用内置 `image_gen`。
- `generate2dmap` 面向地图、关卡、场景、tilemap、layered raster、parallax stage、prop pack、collision、zone 和 scene-hook metadata；它不负责角色、敌人、NPC、投射物或动画 sprite。
- `generate2dsprite` 面向通用 2D sprite、透明 props、角色/生物/FX/projectile/impact、hero action bundle 和 engine atlas；它强调 raw art 来自图像生成，脚本只做确定性后处理和 QC。
- `game-character-sprites` 是更专门的固定格像素角色动画 skill，硬性支持 `32x32`、`64x64`、`128x128` native cell、多方向、多动作、provenance、visual review、GIF/WebP previews。
- `generate2dsprite` 与 `game-character-sprites` 重叠在角色动画和 sheet 后处理，但前者更通用，支持 clean HD/map props/FX/bundles；后者更严格，适合固定 cell pixel-art 角色生产线和多尺寸一致性验证。
- `generate2dmap` 与 `generate2dsprite` 互补：地图 skill 负责地形、地图结构、碰撞和对象摆放；sprite skill 负责可复用透明对象、角色、FX 和动画资产。
- `codex-gateway-imagegen` 与其他三个 skill 互补：它是 Claude 侧视觉生成后端，也是 Codex 侧在内置图片路径不可用时的 fallback。

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 独立文档使用中文正文 | 符合仓库交互与文档阅读要求。 |
| 保留真实路径和 skill 名称 | 降低用户按文档定位文件时的歧义。 |
| 文档将 Claude 和 Codex 分开描述 | 两者能力相似但调用入口、图像生成后端和路径约定不同。 |
| 对比部分按能力边界组织 | 用户特别要求比较相似 skill 的互补、重叠、差异和优势。 |

## Resources
- `.claude/skills`
- `.codex/skills`
