# Claude Code 实用技巧：开发者日常真正用的东西

> 不讲理论，只讲实际开发中能提高效率的用法。

---

## 一、每天必用的命令

| 命令 | 用途 | 什么时候用 |
|------|------|-----------|
| `/compact` | 压缩上下文 | 对话太长、响应变慢时 |
| `/clear` | 清空重来 | 切换不相关任务时 |
| `/model` | 切换模型 | 需要更强/更快的模型时 |
| `/effort` | 调推理深度 | 简单任务用 low 省钱，难的用 high |
| `/plan` | 进入规划模式 | 大改动前先看方案 |
| `/diff` | 看改了什么 | 提交前检查变更 |
| `/rewind` | 回滚 | 改错了，回到之前 |
| `/resume` | 恢复上次会话 | 第二天继续昨天的工作 |
| `/rename` | 给会话命名 | 多个并行任务时方便切换 |
| `/context` | 看上下文用了多少 | 感觉变慢时检查 |
| `/usage` | 看花了多少钱 | 控制成本 |

---

## 二、真正好用的内置 Skill

### `/code-review` — 代码审查
```
/code-review                    # 审查当前 diff
/code-review --fix              # 审查并自动修复
/code-review high               # 深度审查
/code-review ultra              # 云端深度审查（多代理）
```

### `/simplify` — 代码简化
```
/simplify                       # 找出可以简化的地方并修复
```

### `/debug` — 调试
```
/debug                          # 开启调试日志
/debug npm test fails           # 带问题描述调试
```

### `/deep-research` — 深度调研
```
/deep-research 如何优化 PostgreSQL 查询性能
```
自动扇出多个搜索，交叉验证，生成带引用的报告。

### `/run` + `/verify` — 运行验证
```
/run                            # 启动应用看效果
/verify                         # 验证改动是否生效（不只是跑测试）
```
首次使用前跑 `/run-skill-generator` 教它怎么启动你的项目。

### `/goal` — 设定目标让 Claude 持续工作
```
/goal 所有测试通过且 lint 无报错
```
Claude 会一直改到满足条件为止。

### `/fewer-permission-prompts` — 减少确认弹窗
扫描你的常用操作，自动加入白名单。

### `/insights` — 分析你的使用习惯
生成报告，告诉你哪些地方效率可以提升。

---

## 三、高效工作流

### 1. 调研 → 规划 → 执行（三步法）
```
# 第一步：调研（用 subagent，不污染上下文）
用 subagent 调研 XX API 的调用方式和最佳实践

# 第二步：规划
/plan 基于调研结果，生成一个调用脚本的方案

# 第三步：执行
实现这个方案，跑测试验证
```

### 2. 并行工作（Worktree）
```bash
# 终端1：做功能
claude --worktree feature-auth

# 终端2：同时修 bug
claude --worktree bugfix-login
```

### 3. 批量处理
```bash
# 批量迁移文件
for file in $(cat files.txt); do
  claude -p "把 $file 从 React 迁移到 Vue" --allowedTools "Edit,Bash(git commit *)"
done
```

### 4. 定时任务
```
/loop 5m 检查 CI 是否跑完
/loop 30m 检查有没有新的 PR 需要 review
```

### 5. 会话接力
```bash
# 继续上次的对话
claude --continue

# 选择特定会话
claude --resume
```

---

## 四、实用 Hook 配置

### 1. 编辑后自动格式化（省去手动 lint）
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command", "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write" }]
    }]
  }
}
```

### 2. Claude 等待时通知你（不用一直盯着）
```json
{
  "hooks": {
    "Notification": [{
      "matcher": "",
      "hooks": [{ "type": "command", "command": "powershell.exe -Command \"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Claude 等你了', 'Claude Code')\"" }]
    }]
  }
}
```

### 3. 阻止改敏感文件
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command", "command": "powershell.exe -Command \"$input = [Console]::In.ReadToEnd() | ConvertFrom-Json; if ($input.tool_input.file_path -match '\\.env$|package-lock') { exit 2 }\"" }]
    }]
  }
}
```

---

## 五、实用 Skill 模板

### 1. 调研报告生成器
```yaml
# ~/.claude/skills/research/SKILL.md
---
description: 对指定主题进行深度调研，生成结构化报告
disable-model-invocation: true
---

调研 $ARGUMENTS，输出结构化报告：
1. 核心概念（用大白话解释）
2. 技术细节（关键参数、限制、坑）
3. 实际用法（代码示例、命令）
4. 对比分析（和替代方案对比）
5. 推荐用法（什么时候用、怎么用）
```

### 2. 错误修复助手
```yaml
# ~/.claude/skills/fix-error/SKILL.md
---
description: 修复错误信息，自动定位和修复
disable-model-invocation: true
---

修复以下错误：$ARGUMENTS

1. 定位错误源头
2. 分析原因
3. 实现修复
4. 验证修复成功
```

### 3. 代码迁移助手
```yaml
# ~/.claude/skills/migrate/SKILL.md
---
description: 代码迁移工具
disable-model-invocation: true
---

迁移 $ARGUMENTS：

1. 分析现有代码
2. 制定迁移计划
3. 逐文件迁移
4. 跑测试验证
5. 生成迁移报告
```

---

## 六、上下文管理技巧

### 什么时候用什么

| 场景 | 用什么 |
|------|--------|
| 上下文快满了 | `/compact` 压缩 |
| 切换不相关任务 | `/clear` 清空 |
| 探索代码库 | 用 subagent，不污染主上下文 |
| 简单问题 | `/btw` 侧问，不进历史 |
| 改错了 | `/rewind` 回滚 |

### 省 token 的技巧

1. **用 `@` 引用文件**，而不是描述文件路径
2. **大段参考文档做成 Skill**，按需加载
3. **CLAUDE.md 控制 200 行以内**
4. **用 subagent 探索**，只拿回摘要
5. **`/btw` 问不影响任务的问题**，答案不进上下文

---

## 七、Windows 专属技巧

### 用 PowerShell 跑 Claude
```bash
claude --shell powershell
```

### 路径问题
```powershell
# 正确：用正斜杠
C:/Users/17343/Desktop/学习

# 错误：反斜杠可能出问题
C:\Users\17343\Desktop\学习
```

### Skill 中用 PowerShell
```yaml
---
shell: powershell
---
!`Get-ChildItem -Recurse -Filter *.py | Measure-Object`
```

---

## 八、真实开发场景示例

### 场景1：接手新项目
```
给我说一下这个项目的整体架构
主要的数据流是什么样的？
有哪些关键的配置文件？
用 subagent 调研一下测试怎么跑
```

### 场景2：修 Bug
```
/users/login 接口报 500，帮我查一下原因
先看日志，定位错误，然后修复
/code-review 确认修复没有引入新问题
```

### 场景3：写新功能
```
/plan 实现用户注册功能，包括邮箱验证
（审查方案后）
实现这个方案
跑测试验证
create a pr
```

### 场景4：批量处理
```
帮我把所有 .js 文件迁移到 .ts
先列出来有多少个文件
然后逐个迁移，每迁移一个跑一次测试
```

### 场景5：调研 + 执行
```
/deep-research 如何用 Python 调用 OpenAI API 的最佳实践
（看完报告后）
基于调研结果，帮我写一个调用脚本
```

---

## 九、常见问题

### Q: Claude 不遵守 CLAUDE.md 怎么办？
1. 跑 `/memory` 确认文件被加载了
2. 规则写具体点（"用 2 空格缩进" 比 "格式化好" 强）
3. 检查有没有冲突的规则
4. 太长的 CLAUDE.md 会被忽略，精简到 200 行以内

### Q: 上下文满了怎么办？
1. `/compact` 压缩
2. `/clear` 清空重来
3. 用 subagent 做探索性工作
4. 大段参考文档做成 Skill

### Q: 怎么省钱？
1. 简单任务用 `/effort low`
2. 用 Haiku 模型跑简单任务
3. 用 subagent 隔离消耗大的工作
4. `/usage` 监控花费

### Q: 怎么提高响应速度？
1. `/fast` 开启快速模式
2. 保持上下文干净（`/clear`）
3. 用 subagent 分担工作
4. CLAUDE.md 不要太长
