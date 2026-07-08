# Claude Code 高级用法完整指南

> 调研来源：Anthropic 官方文档、GitHub 高星社区项目（claude-code-mastery 539⭐、harness-engineering 67⭐、awesome-agent-conventions 24⭐）、社区最佳实践

---

## 一、功能全景图

Claude Code 的扩展能力分为 5 层，从"始终在线"到"按需触发"：

| 层级 | 功能 | 加载时机 | 上下文成本 |
|------|------|---------|-----------|
| 始终在线 | CLAUDE.md / Rules | 每次会话启动 | 每次请求都消耗 |
| 按需触发 | Skills | 你或 Claude 调用时 | 描述始终在，内容按需加载 |
| 外部连接 | MCP Servers | 会话启动（工具名） | 低，使用时才加载 schema |
| 隔离执行 | Subagents | 被调用时 | 独立上下文，不污染主会话 |
| 自动化 | Hooks | 生命周期事件触发 | 零（外部执行） |

---

## 二、Skills（自定义技能）— 最灵活的扩展

### 什么是 Skill
一个 `SKILL.md` 文件，包含指令/知识/工作流。可以用 `/skill-name` 手动调用，也可以让 Claude 自动匹配。

### 与 CLAUDE.md 的区别
| | CLAUDE.md | Skill |
|---|---|---|
| 加载 | 每次会话自动 | 按需加载 |
| 适合 | "总是做 X" 的规则 | 可复用的工作流、参考文档 |
| 上下文 | 始终消耗 | 描述低消耗，内容用时才加载 |

### 创建方法
```
~/.claude/skills/<skill-name>/SKILL.md    ← 个人级（所有项目可用）
.claude/skills/<skill-name>/SKILL.md      ← 项目级（团队共享）
```

### 实用 Skill 示例

**1. 代码变更摘要**
```yaml
---
description: 总结未提交的变更，标记风险点。当用户问"改了什么"时自动触发。
---

## 当前变更
!`git diff HEAD`

## 指令
用 2-3 个要点总结变更，列出风险（缺少错误处理、硬编码值、需要更新的测试）。
```

**2. 部署工作流（仅手动触发）**
```yaml
---
name: deploy
description: 部署应用到生产环境
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(npm *)
---

部署 $ARGUMENTS 到生产环境：
1. 运行测试套件
2. 构建应用
3. 推送到部署目标
4. 验证部署成功
```

**3. 修复 GitHub Issue**
```yaml
---
name: fix-issue
description: 修复 GitHub issue
disable-model-invocation: true
---

修复 GitHub issue $ARGUMENTS：
1. 用 `gh issue view` 获取详情
2. 搜索相关文件
3. 实现修复
4. 写测试验证
5. 确保 lint/type check 通过
6. 提交并创建 PR
```

### 关键 frontmatter 字段
| 字段 | 作用 |
|------|------|
| `disable-model-invocation: true` | 只能手动 `/name` 触发，Claude 不会自动调用 |
| `user-invocable: false` | 只有 Claude 能调用，用户看不到 `/` 菜单 |
| `allowed-tools` | 技能激活时自动授权的工具 |
| `context: fork` | 在隔离的 subagent 中运行 |
| `model` | 覆盖当前模型（如用 Haiku 省钱） |
| `paths` | 只在操作匹配文件时激活 |
| `shell: powershell` | Windows 上用 PowerShell 执行内联命令 |

### 动态上下文注入
用 `` !`command` `` 语法在 Skill 加载时执行命令并注入结果：
```markdown
## 当前变更
!`git diff HEAD`

## 最近提交
!`git log --oneline -5`
```

---

## 三、Hooks（生命周期钩子）— 确定性自动化

### 什么是 Hook
在 Claude Code 生命周期的关键点自动执行的脚本。与 CLAUDE.md 的"建议"不同，Hook 是**强制执行**的。

### 核心事件
| 事件 | 触发时机 | 典型用途 |
|------|---------|---------|
| `PostToolUse` | 工具执行后 | 自动格式化、lint |
| `PreToolUse` | 工具执行前 | 阻止编辑敏感文件 |
| `Notification` | Claude 等待输入时 | 桌面通知 |
| `SessionStart` | 会话启动/压缩后 | 注入上下文 |
| `Stop` | Claude 准备结束时 | 验证门控 |
| `PermissionRequest` | 权限请求时 | 自动授权 |

### 实用 Hook 示例

**1. 编辑后自动格式化（Windows 版）**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

**2. 阻止编辑受保护文件**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe -Command \"$input = [Console]::In.ReadToEnd() | ConvertFrom-Json; if ($input.tool_input.file_path -match '\\.env$|package-lock|\\.git/') { Write-Error 'Blocked: protected file'; exit 2 }\""
          }
        ]
      }
    ]
  }
}
```

**3. Windows 桌面通知**
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe -Command \"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Claude Code needs your attention', 'Claude Code')\""
          }
        ]
      }
    ]
  }
}
```

**4. 压缩后重新注入上下文**
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "echo '提醒：用 pnpm 不用 npm。提交前跑 bun test。当前 sprint：auth 重构。'"
          }
        ]
      }
    ]
  }
}
```

### Hook vs Skill
| | Hook | Skill |
|---|---|---|
| 触发 | 生命周期事件（确定性） | 用户/Claude 调用（智能匹配） |
| 执行 | Shell 命令/HTTP/子代理 | Claude 读取并遵循指令 |
| 保证 | 每次都执行 | Claude 可能选择不用 |
| 适合 | 格式化、阻止、通知 | 需要判断力的工作流 |

---

## 四、Subagents（子代理）— 上下文隔离

### 什么是 Subagent
在独立上下文中运行的 AI 工人，完成后只返回摘要。不污染主对话。

### 使用场景
- **代码库探索**：读大量文件但只返回关键发现
- **并行工作**：多个 subagent 同时处理不同任务
- **验证**：用独立 subagent 做 adversarial review
- **上下文保护**：避免主窗口被搜索结果淹没

### 创建方法
```
~/.claude/agents/<name>.md         ← 个人级
.claude/agents/<name>.md           ← 项目级
```

### 示例：安全审查员
```markdown
---
name: security-reviewer
description: 审查代码安全漏洞
tools: Read, Grep, Glob, Bash
model: haiku
---

你是高级安全工程师。审查以下内容：
- 注入漏洞（SQL、XSS、命令注入）
- 认证和授权缺陷
- 代码中的密钥/凭证
- 不安全的数据处理

提供具体行号和修复建议。
```

### 使用方式
```
用 subagent 调查我们的认证系统如何处理 token 刷新
```

---

## 五、MCP（模型上下文协议）— 外部连接

### 什么是 MCP
让 Claude 连接外部工具和数据源的开放协议。

### 能做什么
- 查询数据库
- 操作 GitHub Issues/PRs
- 发送 Slack 消息
- 读取 Figma 设计
- 控制浏览器

### 添加 MCP 服务器
```bash
claude mcp add <server-name> -- <command> [args...]
```

### 常用 MCP 服务器
| 服务器 | 用途 |
|--------|------|
| `@modelcontextprotocol/server-github` | GitHub 操作 |
| `@modelcontextprotocol/server-slack` | Slack 消息 |
| `@modelcontextprotocol/server-postgres` | PostgreSQL 查询 |
| `@modelcontextprotocol/server-puppeteer` | 浏览器控制 |

---

## 六、Agent Teams（代理团队）— 多代理协作

### 什么是 Agent Teams
多个 Claude Code 实例组成团队，共享任务列表，互相通信。

### 使用场景
- **并行代码审查**：安全/性能/测试三个审查员同时工作
- **竞争性假设**：多个代理调查不同理论，互相挑战
- **跨层协作**：前端/后端/测试各一个代理

### 启用方法
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### 示例
```
生成三个代理团队成员来审查 PR #142：
- 一个关注安全影响
- 一个检查性能影响
- 一个验证测试覆盖
让他们各自审查并报告发现。
```

### 与 Subagent 的区别
| | Subagent | Agent Team |
|---|---|---|
| 上下文 | 独立窗口，结果返回调用者 | 独立窗口，完全独立 |
| 通信 | 只能向主代理报告 | 团队成员直接通信 |
| 协调 | 主代理管理所有工作 | 共享任务列表，自我协调 |
| Token 成本 | 较低 | 较高（每个成员独立计费） |

---

## 七、上下文管理技巧

### 核心原则
上下文窗口是最宝贵的资源。性能随上下文填满而下降。

### 实用技巧
1. **用 subagent 探索**：读文件的工作交给 subagent，只拿回摘要
2. **Skills 按需加载**：把大段参考文档做成 Skill，而不是放 CLAUDE.md
3. **Rules 路径作用域**：用 `paths` frontmatter 限制规则只在相关文件时加载
4. **CLAUDE.md 控制 200 行以内**：太长会被忽略
5. **不相关任务间用 `/clear`**：重置上下文
6. **用 `/compact` 手动压缩**：带指令如 `/compact 保留 API 变更`

### 上下文成本对比
| 功能 | 上下文成本 |
|------|-----------|
| CLAUDE.md | 每次请求都消耗 |
| Skill 描述 | 每次请求低消耗 |
| Skill 内容 | 用时才加载 |
| MCP 工具名 | 低 |
| Subagent | 独立窗口，零消耗 |
| Hook | 零（外部执行） |

---

## 八、权限与安全

### 三种模式
| 模式 | 行为 | 适合 |
|------|------|------|
| 默认 | 每个操作都请求许可 | 安全但繁琐 |
| Auto | 分类器自动判断风险 | 信任方向但不想点确认 |
| Plan | 只读不写，先规划再执行 | 审查变更 |

### 权限白名单
```
/permissions  →  添加常用命令到白名单
```

### 沙盒
```bash
claude --sandbox  # OS 级隔离
```

---

## 九、Windows 专属技巧

### 1. Skill 中用 PowerShell
```yaml
---
shell: powershell
---
!`Get-ChildItem -Recurse -Filter *.ts | Select-Object -First 20`
```

### 2. Hook 中用 PowerShell
```json
{
  "type": "command",
  "command": "powershell.exe -Command \"your-command\""
}
```

### 3. 路径问题
- Skill 中的 `${CLAUDE_PROJECT_DIR}` 自动解析为正确路径
- Hook 中的 `$CLAUDE_PROJECT_DIR` 同样

---

## 十、进阶组合模式

### 1. Skill + MCP
MCP 提供连接，Skill 教 Claude 如何高效使用：
```
MCP 连接数据库 → Skill 包含你的 schema 和查询模式
```

### 2. Skill + Subagent
Skill 启动多个 subagent 做并行工作：
```
/audit → 启动安全/性能/风格三个 subagent
```

### 3. CLAUDE.md + Skills
CLAUDE.md 放总是需要的规则，Skills 放按需加载的参考：
```
CLAUDE.md: "遵循我们的 API 规范"
Skill: 完整的 API 风格指南
```

### 4. Hook + MCP
Hook 触发外部动作：
```
编辑关键文件后 → Hook 通过 MCP 发送 Slack 通知
```

---

## 十一、社区热门项目推荐

| 项目 | Stars | 内容 |
|------|-------|------|
| [claude-code-mastery](https://github.com/TheDecipherist/claude-code-mastery) | 539⭐ | 最全面的 Claude Code 指南 |
| [harness-engineering](https://github.com/jrenaldi79/harness-engineering) | 67⭐ | CLAUDE.md 模板、Hook 配置、最佳实践 |
| [awesome-agent-conventions](https://github.com/ItamarZand88/awesome-agent-conventions) | 24⭐ | Agent 规范文件对比（AGENTS.md/CLAUDE.md/SKILL.md） |
| [ultra-instinct-claude-code](https://github.com/infiniV/ultra-instinct-claude-code) | 24⭐ | 176 条技巧 |

---

## 十二、官方资源

- [功能总览](https://code.claude.com/docs/en/features-overview)
- [Skills 指南](https://code.claude.com/docs/en/skills)
- [Hooks 指南](https://code.claude.com/docs/en/hooks-guide)
- [Subagents 指南](https://code.claude.com/docs/en/sub-agents)
- [MCP 文档](https://code.claude.com/docs/en/mcp)
- [Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [最佳实践](https://code.claude.com/docs/en/best-practices)
