# Findings & Decisions

## Requirements
- 更新 `.claude/skills/generate2dmap` 和 `.claude/skills/generate2dsprite`。
- 不仅比较文件，还要理解 Claude Code skill 与 Codex skill 官方差异。
- 使用 agent team 协助。
- 最终要修改 Claude Code skill 文件。

## Research Findings
- Claude Code skill：项目目录为 `.claude/skills/<skill-name>/SKILL.md`；`SKILL.md` 使用 YAML frontmatter + markdown；可用 `/skill-name` 调用，也可由 Claude 根据 `description` 自动调用。
- Claude Code 支持 `${CLAUDE_SKILL_DIR}` 定位 skill 自带脚本/资源。
- Codex skill：通常在 `.agents/skills` 或 Codex skill 路径，显式调用使用 `$skill` 或 `/skills`；可有 `agents/openai.yaml` 配置 UI/policy/dependencies。
- `agents/openai.yaml`、`$CODEX_HOME`、`built-in image_gen`、`view_image`、`$generate2dsprite` 是 Codex 语境，不能原样复制到 Claude Code skill。
- `agent-sprite-forge-origin` 最新版新增/强化：map_mode、genre routing、可玩地图不能单图交付、visual reference handoff、post-reference object gate、side_scroll_mode/parallax 合同、clean HD 默认风格、prop/object 分类、hero_action_bundle、body-only action、single-row body 禁止、layout guide。

## Implementation Findings
- `generate2dmap` 需要以 `map_mode` 作为第一决策层，再选择 visual/runtime/collision/engine 轴。
- playable map、level、stage、room、prototype、engine scene 不能默认只交付 single baked image。
- dressed reference 是规划 artifact；如果对象涉及碰撞、y-sort、遮挡、交互或复用，必须拆成独立 runtime prop/object。
- map props 需要 object classification gate，避免把 NPC、敌人、 projectile、impact、UI 等误塞进 prop pack。
- `generate2dsprite` 需要 body-only hero action 规则：hero attack/shoot/cast body sheet 不能烘焙 slash、muzzle、projectile、impact、dust。
- raw single-row body sheet 默认禁止；`strip_1x3`/`strip_1x4` 主要用于 projectile、FX、impact 或明确的 engine strip。
- `generate2dsprite.py process --mode` 不限制新 mode 枚举，但 `shoot`/`jump` 等新动作没有内建默认网格，文档命令应显式传 `--rows`/`--cols`。
- `make_layout_guide.py` 是确定性 layout-only helper，适合迁移为 Claude Code skill bundled script。

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 只更新 `.claude/skills/*` | 用户要求更新 Claude Code skill。 |
| 不复制 `agents/openai.yaml` | Codex 专用；将其有用规则转写进 Claude Code 正文。 |
| 添加 `make_layout_guide.py` | 这是确定性辅助脚本，适合迁移到 Claude Code。 |
| 保留 `codex-gateway-imagegen` | Claude Code adapter 的 raw image generation 必须走已安装 gateway skill。 |
| 默认 clean HD / project-native，pixel art 仅显式请求 | 对齐 origin 最新 map/sprite 风格规则，避免旧版一律 pixel-art。 |

## Resources
- Claude Code skills docs: https://code.claude.com/docs/en/skills
- OpenAI Codex skills docs: https://developers.openai.com/codex/skills
- OpenAI Codex AGENTS.md docs: https://developers.openai.com/codex/guides/agents-md
