# Game Skills for Claude Code and Codex

这个仓库维护一组游戏资产生产 skill，并同时提供 Claude Code 和 Codex 两套运行时适配版本。它们主要服务 2D 游戏资产生成，包括地图、场景、props、sprite、固定 cell 角色动画、FX、projectile、impact、preview 和 QA metadata。

## 文档入口

| 文档 | 内容 |
|---|---|
| [CLAUDE_README.md](CLAUDE_README.md) | `.claude/skills` 的详细说明、使用场景、使用指南和 skill 对比 |
| [CODEX__README.md](CODEX__README.md) | `.codex/skills` 的详细说明、Codex 运行时差异、`agents/openai.yaml` 和 skill 对比 |

## 目录结构

```text
.
|-- .claude/skills/
|   |-- codex-gateway-imagegen/
|   |-- game-character-sprites/
|   |-- generate2dmap/
|   `-- generate2dsprite/
|-- .codex/skills/
|   |-- codex-gateway-imagegen/
|   |-- game-character-sprites/
|   |-- generate2dmap/
|   `-- generate2dsprite/
|-- CLAUDE_README.md
|-- CODEX__README.md
`-- README.md
```

## Skill 总览

| Skill | 主要职责 | 适合任务 |
|---|---|---|
| `codex-gateway-imagegen` | 通过 configured Responses gateway 生成或编辑图片并保存为本地 PNG | 单图生成、参考图编辑、gateway fallback、其他 skill 的视觉生成后端 |
| `generate2dmap` | 生成 production-oriented 2D 地图、关卡、场景、props、collision、zones、scene hooks 和 preview | RPG 地图、塔防地图、side-scroller stage、tilemap、grid map、room chunk、battle background |
| `generate2dsprite` | 生成通用 2D sprite、透明 props、FX、projectile、impact、hero action bundle、engine atlas | hero actions、spell bundle、projectile/impact、map props、clean HD 或 pixel art sprite |
| `game-character-sprites` | 生成固定 cell pixel-art 角色动画包，强调 native sizes、directions、manifest 和 visual QA | `32x32`/`64x64`/`128x128` 角色、4-way/8-way movement、GIF/WebP previews、targeted regeneration |

## Claude 与 Codex 版本差异

| 维度 | `.claude/skills` | `.codex/skills` |
|---|---|---|
| 运行时 | Claude Code | Codex |
| 视觉生成默认路径 | `codex-gateway-imagegen` | 内置 `image_gen` |
| 脚本路径示例 | `${CLAUDE_SKILL_DIR}/scripts/...` | 当前 skill 目录下 `scripts/...` |
| 额外 metadata | 无 `agents/openai.yaml` | 每个 skill 有 `agents/openai.yaml` |
| 文档入口 | [CLAUDE_README.md](CLAUDE_README.md) | [CODEX__README.md](CODEX__README.md) |

## 快速选择

| 需求 | 推荐 skill |
|---|---|
| 只生成或编辑一张图片 | `codex-gateway-imagegen` |
| 做可玩地图、关卡、stage、collision 或 scene metadata | `generate2dmap` |
| 做透明 sprite、props、FX、projectile、impact 或 hero action bundle | `generate2dsprite` |
| 做固定 cell 像素角色动画包，尤其是多方向和多 native size | `game-character-sprites` |

## 能力边界

`generate2dmap` 和 `generate2dsprite` 是互补关系。地图 skill 负责地图结构、运行时对象、坐标、碰撞、zones、scene hooks 和 preview；sprite skill 负责生成可复用透明图片、动画帧、FX 和 atlas。可玩地图中需要的树、门、平台、hazard、pickup 等对象，通常由地图 skill 先分类和放置，再由 sprite skill 生成或清理透明资产。

`generate2dsprite` 和 `game-character-sprites` 有角色动画能力重叠，但默认选择不同。普通 sprite、props、FX、projectile、impact、clean HD asset 和 hero action bundle 用 `generate2dsprite`；严格 fixed-cell pixel-art character pack，尤其是 `32x32`、`64x64`、`128x128` native hierarchy、4-way/8-way directions 和 provenance QA，用 `game-character-sprites`。

`codex-gateway-imagegen` 是视觉生成后端或 fallback，不替代地图和 sprite skill 的生产流程。它负责把图片生成出来并落盘；地图和 sprite skill 负责把图片变成可用游戏资产并验证质量。

## 维护约定

- 更新 Claude 侧文档时，示例命令优先使用 `${CLAUDE_SKILL_DIR}`。
- 更新 Codex 侧文档时，路径优先引用 `.codex/skills/...`。
- 修改 `.codex/skills/*/agents/openai.yaml` 时，要同步检查对应 `SKILL.md` 的触发语义。
- 不要用脚本绘制最终视觉资产；脚本只做 layout guide、切图、清理、合成、校验和 preview。
- 不要把可玩地图简化成单张 baked image，除非用户明确只要 flat background。
- 不要把 scaled sprite 伪装成 native `32x32`、`64x64` 或 `128x128` 输出。
- 文档、prompt 示例和命令应保持路径真实、术语一致，避免 Claude/Codex 运行时路径混用。

## 建议验证

文档更新后至少检查：

```bash
rg -n ".claude/skills|.codex/skills|CLAUDE_README.md|CODEX__README.md|generate2dmap|generate2dsprite|game-character-sprites|codex-gateway-imagegen" README.md CLAUDE_README.md CODEX__README.md
```

如果修改了 Python 脚本，再额外做语法检查：

```bash
python3 -m py_compile .claude/skills/*/scripts/*.py .codex/skills/*/scripts/*.py
```
