# Claude Code Windows 配置方案 & 高级用法

针对 Windows 环境下 Claude Code 常见问题（命令报错重试、路径拼错重试）的 CLAUDE.md 配置，以及高级用法完整指南。

## 文件列表

| 文件 | 内容 |
|------|------|
| `CLAUDE.md` | 主配置文件，import 各规则 |
| `rules/windows.md` | Windows 命令/路径/Shell 对照表 |
| `rules/workflow.md` | 规划→执行→验证→自我改进流程 |
| `rules/code-quality.md` | 写码前中后规范、安全约束 |
| `advanced-guide.md` | **高级用法完整指南**（Skills/Hooks/Subagents/MCP/Agent Teams） |
| `research-plan.md` | 调研计划文档 |

## 快速开始

### 1. 应用 CLAUDE.md 配置

```powershell
# 创建目录
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\rules"

# 复制文件
Copy-Item "CLAUDE.md" "$env:USERPROFILE\.claude\CLAUDE.md"
Copy-Item "rules\*.md" "$env:USERPROFILE\.claude\rules\"
```

### 2. 阅读高级指南

直接打开 `advanced-guide.md`，涵盖：
- Skills（自定义技能）— 最灵活的扩展
- Hooks（生命周期钩子）— 确定性自动化
- Subagents（子代理）— 上下文隔离
- MCP（模型上下文协议）— 外部连接
- Agent Teams（代理团队）— 多代理协作
- 上下文管理技巧
- Windows 专属技巧

## 文件结构

```
~/.claude/
├── CLAUDE.md              ← 主文件，import 各规则文件
└── rules/
    ├── windows.md         ← Windows 命令/路径/Shell 对照表
    ├── workflow.md        ← 规划→执行→验证→自我改进流程
    └── code-quality.md    ← 写码前中后规范、安全约束
```

## 来源

- `windows.md` — 基于实际踩坑经验整理
- `workflow.md` / `code-quality.md` — 参考社区模板 [harness-engineering](https://github.com/jrenaldi79/harness-engineering) 的最佳实践
- `advanced-guide.md` — 综合官方文档 + 社区高星项目（[claude-code-mastery](https://github.com/TheDecipherist/claude-code-mastery) 539⭐、[harness-engineering](https://github.com/jrenaldi79/harness-engineering) 67⭐、[awesome-agent-conventions](https://github.com/ItamarZand88/awesome-agent-conventions) 24⭐）
