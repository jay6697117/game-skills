# Task Plan: Skill directory documentation

## Goal
为 `/Users/zhangjinhui/Desktop/game-skills` 下的 `.claude/skills` 和 `.codex/skills` 编写成体系的中文说明文档：

- 新建 `CLAUDE_README.md`，说明 `.claude/skills` 下各 skill 的详细介绍、使用场景、使用指南、能力对比。
- 新建 `CODEX__README.md`，说明 `.codex/skills` 下各 skill 的详细介绍、使用场景、使用指南、能力对比。
- 补齐根目录 `README.md`，说明项目定位、目录结构、两个文档入口、Claude/Codex 使用差异和维护规则。

## Current Phase
Complete

## Phases

### Phase 1: Discovery
- [x] 读取 `.claude/skills` 与 `.codex/skills` 的目录结构。
- [x] 读取各 `SKILL.md`、关键 reference、README、agent metadata。
- **Status:** complete

### Phase 2: Synthesis
- [x] 归纳每个 skill 的定位、输入输出、使用场景、典型流程和验证方式。
- [x] 对功能相似 skill 做横向对比，标出互补、重叠、差异和优势。
- **Status:** complete

### Phase 3: Documentation
- [x] 创建 `CLAUDE_README.md`。
- [x] 创建 `CODEX__README.md`。
- [x] 更新根目录 `README.md`。
- **Status:** complete

### Phase 4: Verification
- [x] 检查文档路径和 skill 名称是否与实际文件一致。
- [x] 检查 Codex 文档是否优先引用 `.codex/skills/...`。
- [x] 查看 git status 和文档摘要。
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 不修改 skill 运行代码 | 用户要求是补齐说明文档，不涉及行为变更。 |
| Claude 与 Codex 分开成文 | 两个目录有相似能力但运行入口、metadata 和路径约定不同。 |
| 根 README 作为索引与维护说明 | 根 README 应承担项目入口职责，不重复两个长文档的全部细节。 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
