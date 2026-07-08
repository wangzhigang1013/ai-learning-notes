# Claude Code Windows 配置方案

针对 Windows 环境下 Claude Code 常见问题（命令报错重试、路径拼错重试）的 CLAUDE.md 配置。

## 使用方法

将文件复制到用户目录：

```powershell
# 创建目录
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\rules"

# 复制文件
Copy-Item "CLAUDE.md" "$env:USERPROFILE\.claude\CLAUDE.md"
Copy-Item "rules\*.md" "$env:USERPROFILE\.claude\rules\"
```

## 文件结构

```
~/.claude/
├── CLAUDE.md              ← 主文件，import 各规则文件
└── rules/
    ├── windows.md         ← Windows 命令/路径/Shell 对照表
    ├── workflow.md        ← 规划→执行→验证→自我改进流程
    └── code-quality.md    ← 写码前中后规范、安全约束
```

## 各文件说明

| 文件 | 解决的问题 |
|------|-----------|
| `windows.md` | 模型在 Windows 上用错 Unix 命令、路径拼接错误 |
| `workflow.md` | 没有规划就动手、改完不验证、重复犯同样的错 |
| `code-quality.md` | 代码风格不一致、过度工程化、安全疏漏 |

## 来源

- `windows.md` — 基于实际踩坑经验整理
- `workflow.md` / `code-quality.md` — 参考社区模板 [harness-engineering](https://github.com/jrenaldi79/harness-engineering) 的最佳实践
