# Headroom — AI Agent 上下文压缩工具深度调研

> 项目地址：https://github.com/chopratejas/headroom
> 调研日期：2026-06-25
> 许可证：Apache 2.0
> 语言：Python（核心）+ TypeScript SDK + Rust（部分核心组件）

---

## 一、项目简介

Headroom 是一个 **AI Agent 上下文压缩层**，部署在你的应用和 LLM Provider 之间，压缩 Agent 读取的所有内容——工具输出、日志、RAG 结果、文件、对话历史——然后再发送给 LLM。号称 **减少 60-95% 的 token 数量，同时保持相同的回答质量**。

核心卖点：
- **本地运行**：数据不离开你的机器
- **可逆压缩（CCR）**：原始内容被缓存，LLM 需要时可以检索回来
- **多种集成方式**：Library / Proxy / Agent Wrap / MCP Server
- **跨 Agent 记忆**：Claude、Codex、Gemini 之间共享上下文
- **自动内容路由**：根据内容类型（JSON、代码、日志、文本）选择最优压缩器

---

## 二、如何使用

### 2.1 安装

```bash
# Python（推荐，功能最全）
pip install "headroom-ai[all]"

# TypeScript / Node
npm install headroom-ai

# Docker
docker pull ghcr.io/chopratejas/headroom:latest
```

Python 需要 **3.10+**。可选 extras：`[proxy]`、`[mcp]`、`[ml]`（Kompress-base 模型）、`[code]`、`[memory]`、`[image]` 等。

### 2.2 三种使用模式

#### 模式一：Agent Wrap（最简单，一行命令）

直接包装你现有的编程 Agent CLI：

```bash
headroom wrap claude      # 包装 Claude Code
headroom wrap codex       # 包装 Codex
headroom wrap cursor      # 包装 Cursor
headroom wrap aider       # 包装 Aider
headroom wrap copilot     # 包装 GitHub Copilot
headroom wrap opencode    # 包装 OpenCode
```

`wrap` 会自动启动本地代理（默认端口 8787），然后启动对应的 Agent CLI，所有请求都经过压缩。

#### 模式二：Proxy 代理（零代码改动）

```bash
headroom proxy --port 8787
```

启动后，把你的应用/API endpoint 指向 `http://127.0.0.1:8787` 即可。适用于任何语言、任何框架。

#### 模式三：Library 库调用（最灵活）

**Python：**
```python
from headroom import compress

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Analyze this codebase"},
    {"role": "tool", "content": '{"results": [...]}', "tool_call_id": "call_1"},
]

result = compress(messages)
print(f"压缩前: {result.tokens_before} tokens")
print(f"压缩后: {result.tokens_after} tokens")
print(f"节省: {result.savings_percentage:.0%}")
```

**TypeScript：**
```ts
import { compress } from "headroom-ai";

const result = await compress(messages, { model: "claude-sonnet-4-20250514" });
console.log(`Saved: ${result.tokensSaved} tokens`);
```

#### 模式四：MCP Server

```bash
headroom mcp install       # 安装到 MCP 客户端
```

提供三个 MCP 工具：`headroom_compress`、`headroom_retrieve`、`headroom_stats`。

### 2.3 SDK 集成

| 你的技术栈 | 集成方式 |
|-----------|---------|
| Anthropic SDK | `withHeadroom(new Anthropic())` |
| OpenAI SDK | `withHeadroom(new OpenAI())` |
| Vercel AI SDK | `wrapLanguageModel({ model, middleware: headroomMiddleware() })` |
| LiteLLM | `litellm.callbacks = [HeadroomCallback()]` |
| LangChain | `HeadroomChatModel(your_llm)` |
| 任意 Python Web | `app.add_middleware(CompressionMiddleware)` |

### 2.4 常用命令

```bash
headroom perf              # 查看压缩效果统计
headroom dashboard         # 实时节省仪表盘（需 proxy 运行中）
headroom learn             # 从失败会话中学习，写入 CLAUDE.md
headroom learn --verbosity # 自动学习你偏好的简洁程度
headroom output-savings    # 查看输出 token 节省估算
headroom update            # 更新 Headroom
```

---

## 三、压缩原理详解

### 3.1 三阶段流水线

每个请求经过三个阶段：

```
输入消息
   │
   ▼
┌──────────────┐     ┌────────────────┐     ┌─────────────────┐
│ CacheAligner │────>│ ContentRouter  │────>│ 具体压缩器       │
│ 前缀稳定化   │     │ 内容类型检测    │     │ SmartCrusher     │
│              │     │ 路由到最优压缩器│     │ CodeCompressor   │
│              │     │                │     │ LogCompressor    │
│              │     │                │     │ Kompress-base    │
└──────────────┘     └────────────────┘     └─────────────────┘
                                                  │
                                                  ▼
                                          CCR 存储（可逆）
                                                  │
                                                  ▼
                                          压缩后的消息 → LLM
```

### 3.2 第一阶段：CacheAligner（前缀稳定化）

**目的**：让 Provider 的 KV 缓存能够命中。

**原理**：系统提示词中经常包含动态内容（日期、时间戳、UUID、session ID），哪怕只有一个字符不同，整个 Provider 缓存就会失效。CacheAligner 检测这些不稳定内容并发出警告。

**重要说明**：当前版本的 CacheAligner 是 **纯检测器**（detector-only），不会修改消息内容。它会：
- 检测系统提示词中的 UUID、ISO 8601 时间戳、JWT、十六进制哈希
- 发出警告日志，提示调用者缓存前缀不稳定
- 计算前缀哈希用于可观测性

**Anthropic 缓存优化器**则会主动插入 `cache_control` 断点：
- 自动在系统提示词、工具定义、few-shot 示例后插入缓存断点
- 最多 4 个断点（Anthropic 限制）
- 最小 1024 token 才值得缓存
- 稳定前缀（移除日期等动态内容）

### 3.3 第二阶段：ContentRouter（内容路由）

自动检测内容类型，路由到最优压缩器：

| 内容类型 | 检测信号 | 压缩器 | 典型压缩率 |
|---------|---------|--------|-----------|
| JSON 数组 | 有效 JSON + 数组结构 | SmartCrusher | **70-90%** |
| 源代码 | 语法模式、缩进、关键字 | CodeCompressor (AST) | **40-70%** |
| 搜索结果 | `file:line:content` 格式 | SearchCompressor | **80-95%** |
| 构建/测试日志 | 时间戳、日志级别、pytest/npm 标记 | LogCompressor | **85-95%** |
| Diff | unified diff 格式 | DiffCompressor | **60-80%** |
| HTML | 标签结构 | HTMLCompressor | **50-70%** |
| 纯文本 | 回退 | TextCompressor / Kompress-base | **60-80%** |

### 3.4 第三阶段：具体压缩器

#### SmartCrusher（JSON 压缩）
- 统计式压缩，保留 JSON schema
- 保留所有 key、括号、布尔值、null、短值、UUID
- 压缩长字符串值和空白

#### CodeCompressor（代码压缩）
- 基于 AST（tree-sitter），支持 Python、JS、Go、Rust、Java、C++
- 保留：imports、函数签名、类定义、类型
- 压缩：函数体、注释

#### Kompress-base（文本压缩）
- 自研的 HuggingFace 模型，基于 Agent traces 训练
- 用于通用文本和日志压缩
- 需要 `[ml]` extra

### 3.5 CCR（Compress-Cache-Retrieve）可逆压缩

CCR 让压缩变得 **可逆**：
1. 原始内容被存储在本地 SQLite 中
2. LLM 调用 `headroom_retrieve` 工具来获取原始内容
3. 默认 TTL 300 秒，最多 1000 条目

这意味着：**压缩不是有损的**——LLM 觉得需要原始数据时可以随时取回。

### 3.6 输出 Token 缩减

除了压缩输入，Headroom 还能减少模型 **写回** 的 token：
- **Verbosity Steering**：在系统提示词末尾添加"简洁、不要重复上下文"的指令
- **Effort Routing**：简单任务（如读文件后继续）降低模型的 thinking effort

```bash
export HEADROOM_OUTPUT_SHAPER=1   # 默认关闭
```

---

## 四、压缩对缓存命中率的影响（核心问题）

这是你最关心的问题。答案是：**压缩不会降低缓存命中率，反而会提高。**

### 4.1 两种"缓存"的区别

需要区分两种完全不同的缓存：

| 缓存类型 | 是什么 | 谁的缓存 |
|---------|--------|---------|
| **Provider KV 缓存** | LLM Provider（Anthropic/OpenAI/Google）对相同前缀的 prompt 缓存 KV 注意力状态 | Provider 端 |
| **Headroom 压缩缓存** | Headroom 本地缓存已压缩内容的映射（避免重复压缩） | 本地 |

Headroom 影响的是 **Provider KV 缓存**的命中率，而不是自己的压缩缓存。

### 4.2 为什么压缩反而提高 Provider 缓存命中率

**核心机制**：Headroom 的 CacheAligner 和 Anthropic 缓存优化器会 **稳定前缀**。

原始场景（没有 Headroom）：
```
请求1: "你是助手。当前日期: 2026-06-25。请分析代码..."
请求2: "你是助手。当前日期: 2026-06-25。请分析代码..."
请求3: "你是助手。当前日期: 2026-06-26。请分析代码..."  ← 日期变了，缓存失效！
```

使用 Headroom 后：
```
请求1: "你是助手。" + [动态内容移到末尾]  ← 稳定前缀，缓存命中
请求2: "你是助手。" + [动态内容移到末尾]  ← 稳定前缀，缓存命中
请求3: "你是助手。" + [动态内容移到末尾]  ← 稳定前缀，缓存命中
```

**关键洞察**：
- Provider 的 KV 缓存是 **前缀匹配** 的——只要前 N 个 token 完全相同，缓存就能命中
- 压缩让内容更 **确定性**（去掉了动态部分），前缀更稳定
- 压缩后 token 数量更少，但前缀的一致性更高

### 4.3 各 Provider 的缓存机制与折扣

| Provider | 缓存机制 | 读取折扣 | 写入成本 | TTL | 最小 token |
|---------|---------|---------|---------|-----|-----------|
| **Anthropic** | 显式 `cache_control` 断点 | **90% 折扣** | +25% 首次写入 | 5 分钟（命中时延长） | 1024 |
| **OpenAI** | 自动前缀缓存 | **50% 折扣** | 无额外成本 | 自动管理 | 1024 |
| **Google** | CachedContent API | **75% 折扣** | 按小时存储费 | 用户自定义（默认 1 小时） | 32,768 |

### 4.4 复合节省示例

以 Anthropic 为例，100K 输入 token 的场景：

```
原始: 100,000 tokens × $15/M = $1.50

使用 Headroom:
  1. 压缩: 100K → 20K tokens (80% 压缩)
  2. 缓存命中: 18K 命中缓存，2K 未命中
  3. 成本计算:
     - 缓存写入: 20K × $15/M × 1.25 = $0.375（首次）
     - 缓存读取: 18K × $15/M × 0.10 = $0.027
     - 未缓存: 2K × $15/M = $0.030
     - 总计: $0.087（首次）/ $0.057（后续）
  4. 总节省: 96.2%
```

**压缩 + 缓存是乘法关系**，不是加法。

---

## 五、不同计费方式下的成本分析

### 5.1 按量付费（PAYG）— 最适合使用 Headroom

**场景**：使用 `sk-ant-api*` 或 `sk-*` API Key，按 token 计费。

**分析**：
- 每个 token 都有直接成本
- 压缩直接减少 token 数量 → 直接省钱
- 缓存命中率越高 → 省钱越多（Anthropic 缓存读取 90% 折扣）
- **Headroom 的压缩 + 缓存优化 = 双重节省，效果最显著**

**结论**：✅ **强烈推荐**。压缩率 60-95% + 缓存折扣 50-90% = 总节省 80-99%。

**Headroom 对 PAYG 的策略**：激进压缩。开启所有压缩器、CCR、缓存优化。

### 5.2 订阅制（Subscription）— 价值不同，但仍有益

**场景**：Claude Pro/Max、Claude Code CLI、Cursor 等订阅服务。

**分析**：
- 每个 token 的成本是 **不透明的**（订阅费已包含）
- 压缩不能直接省钱（账单是固定的）
- 但压缩的价值在于：**在 rate-limit/配额窗口内塞入更多上下文**
- 更少的 token = 更多的请求可以在配额内完成

**Headroom 对 Subscription 的策略**：保守（passthrough-prefer）。
- 不自动注入 `cache_control`（因为 OAuth scope 绑定了 account/model/session，自动注入可能破坏缓存）
- 只使用无损压缩器
- 不修改 User-Agent（避免被 Provider 检测为程序化访问）

**结论**：✅ **有用，但价值体现在"扩展有效上下文"而非"省钱"**。

### 5.3 按量付费 + 高缓存命中率 — 需要仔细计算

**关键问题**：如果我的 prompt 前缀本来就很稳定（缓存命中率已经很高），压缩还有意义吗？

**分析**：

假设一个场景：前缀已经 100% 稳定，缓存命中率 100%。

```
没有 Headroom:
  100K tokens，全部缓存命中
  成本: 100K × $15/M × 0.10 = $0.15

使用 Headroom（压缩 80%）:
  20K tokens，全部缓存命中
  成本: 20K × $15/M × 0.10 = $0.03
  节省: 80%
```

**即使缓存已经 100% 命中，压缩仍然有意义**，因为缓存折扣只打折，不免费。压缩后的 token 数量更少，即使享受同样的折扣比例，绝对成本也更低。

### 5.4 成本对比总结

| 计费方式 | 压缩节省 | 缓存节省 | 综合节省 | 推荐度 |
|---------|---------|---------|---------|--------|
| **PAYG（无缓存）** | 60-95% | 0% | **60-95%** | ⭐⭐⭐⭐⭐ |
| **PAYG（有缓存）** | 60-95% | 50-90% | **80-99%** | ⭐⭐⭐⭐⭐ |
| **订阅制** | 无直接省钱 | 无直接省钱 | 扩展上下文 | ⭐⭐⭐ |
| **Google（大上下文）** | 60-95% | 75% | **90-99%** | ⭐⭐⭐⭐⭐ |

### 5.5 什么时候 Headroom 反而"不划算"？

1. **你的 prompt 前缀已经极其稳定，且 token 数很少**（< 1024）——压缩节省的绝对量太小，不值得引入额外的复杂度和延迟
2. **你在使用订阅制且 rate-limit 不是瓶颈**——如果从不撞限制，扩展上下文的价值为零
3. **你在沙盒环境中无法运行本地进程**——Headroom 需要本地运行

---

## 六、性能与延迟

| 组件 | 延迟 |
|------|------|
| CacheAligner | ~0ms（纯检测） |
| SmartCrusher (JSON) | ~1ms |
| SearchCompressor | ~2ms |
| LogCompressor | ~3ms |
| TextCompressor | ~5ms |
| CodeCompressor (AST) | ~10ms |
| Proxy 总开销 | ~5-10ms |

压缩本身的延迟可以忽略不计（< 10ms），远小于 LLM 的响应时间。

---

## 七、与同类工具对比

| 工具 | 范围 | 部署方式 | 本地 | 可逆 |
|------|------|---------|------|------|
| **Headroom** | 所有上下文 | Proxy / Library / MCP | ✅ | ✅ |
| RTK | CLI 命令输出 | CLI wrapper | ✅ | ❌ |
| lean-ctx | CLI 命令、MCP 工具 | CLI wrapper / MCP | ✅ | ❌ |
| Compresr / Token Co. | 发送到其 API 的文本 | 托管 API | ❌ | ❌ |
| OpenAI Compaction | 对话历史 | Provider 原生 | ❌ | ❌ |

Headroom 的独特优势：
- **覆盖面最广**：JSON、代码、日志、搜索结果、diff、HTML、纯文本
- **可逆压缩**：原始内容可通过 CCR 检索
- **跨 Agent 记忆**：Claude/Codex/Gemini 共享上下文
- **`headroom learn`**：从失败会话中学习，自动改进

---

## 八、局限性

根据官方文档：
- 对于非常短的上下文（< 1024 tokens），节省不明显
- Kompress-base ML 模型需要额外下载（~几百 MB）
- 代码压缩默认关闭（需 opt-in）
- 订阅模式下不会自动注入缓存断点（出于安全考虑）
- 本地进程运行，沙盒环境无法使用

---

## 九、参考链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/chopratejas/headroom |
| 文档 | https://headroom-docs.vercel.app/docs |
| PyPI | https://pypi.org/project/headroom-ai/ |
| npm | https://www.npmjs.com/package/headroom-ai |
| HuggingFace 模型 | https://huggingface.co/chopratejas/kompress-v2-base |
| Discord | https://discord.gg/yRmaUNpsPJ |
| 架构文档 | https://headroom-docs.vercel.app/docs/architecture |
| 缓存优化 | https://headroom-docs.vercel.app/docs/cache-optimization |
| 压缩原理 | https://headroom-docs.vercel.app/docs/how-compression-works |
| CCR 可逆压缩 | https://headroom-docs.vercel.app/docs/ccr |

---

## 十、⚠️ 国内用户警告：缓存价格差风险

**如果你的 Provider 缓存命中与未命中的价格差 > 50 倍（国内大部分 Provider），使用 Headroom proxy 模式压缩全部内容可能导致成本反而增加。**

原因：Headroom 没有确定性压缩保证（不像 lean-ctx 有 byte-stable contract），压缩后的对话历史每轮都不同，导致 Provider KV 缓存前缀失效，大量 token 从缓存价格变成未命中价格。

**建议**：
- 只使用 Headroom 的工具模式（wrap/MCP），不压缩对话历史
- 或改用 lean-ctx（确定性压缩，缓存安全有保证）
- 详见 [[llm-caching]] 中的竞品对比和成本计算

## 十一、关联调研

- [[llm-caching]] — LLM 缓存机制原理、压缩对缓存命中率的深度分析、竞品对比（RTK/lean-ctx/Headroom/LLMLingua）、国内 100 倍差价场景计算
- [[api-pricing]] — 各家 Provider 计费模型详解，是否区分缓存 token，订阅 vs 按量对比
