# Task Plan: Update Claude Code skills from Codex origin

## Goal
更新 `.claude/skills/generate2dmap` 和 `.claude/skills/generate2dsprite`，吸收 `agent-sprite-forge-origin` 最新能力，同时保留 Claude Code skill 格式、`codex-gateway-imagegen` 图像生成流程和 `${CLAUDE_SKILL_DIR}` 脚本路径。

## Current Phase
Phase 5

## Phases

### Phase 1: Requirements & Discovery
- [x] 捕获用户要求：不仅比较文件，还要理解 Claude Code skill 与 Codex skill 官方差异。
- [x] 使用团队审计 origin、map skill、sprite skill 和官方文档。
- **Status:** complete

### Phase 2: Comparative Audit
- [x] 确认 `agents/openai.yaml` 是 Codex 专用，不复制到 Claude Code skill。
- [x] 确认 map references、sprite references 和 sprite layout guide 能力需要更新。
- **Status:** complete

### Phase 3: Implementation
- [x] 更新 `generate2dmap` 的 `SKILL.md` 和 references。
- [x] 更新 `generate2dsprite` 的 `SKILL.md` 和 references。
- [x] 新增 `generate2dsprite/scripts/make_layout_guide.py`。
- **Status:** complete

### Phase 4: Verification
- [x] 检查 stale Codex-only terms。
- [x] 运行 Python 语法检查。
- [x] 查看 git diff/status 摘要。
- **Status:** complete

### Phase 5: Delivery
- [x] 汇总修改内容、保留差异和验证结果。
- **Status:** ready

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 不复制 `agents/openai.yaml` | 这是 Codex/OpenAI 平台元数据，不是 Claude Code skill 格式。 |
| 保留 `codex-gateway-imagegen` | Claude Code adapter 的原始图片生成硬规则。 |
| 使用 `${CLAUDE_SKILL_DIR}` | Claude Code 官方推荐的 skill 自带脚本定位方式。 |
| 新增 `make_layout_guide.py` | 迁移 origin 的确定性 layout-only 辅助脚本，适合 Claude Code skill bundled scripts。 |
| `shoot`/`jump` 文档要求显式 `--rows/--cols` | 现有 processor 的 `process --mode` 可接收任意 mode，但新动作没有内建默认网格。 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| 计划文件读取失败 | 1 | 重新创建简短计划文件继续执行。 |
| `grep` 模式以 `--` 开头被当成选项 | 1 | 改用 `grep -e`。 |
| stale term grep 在当前环境只返回退出码不返回内容 | 2 | 改用 Python 文本扫描完成验证。 |
