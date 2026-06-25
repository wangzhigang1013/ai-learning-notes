# Open Design — Windows 环境安装与使用调研

> 项目地址：https://github.com/nexu-io/open-design
> 调研日期：2026-06-25
> 当前版本：0.10.0

---

## 一、项目简介

Open Design 是一个 **开源的 Claude Design 替代品**，定位为 **本地优先、Agent 原生的设计工作空间**。它不是一个独立的设计工具（不像 Figma），而是一个让编程 Agent（Claude Code、Codex、Cursor、Copilot 等）直接生成设计产物（HTML 原型、PPT、图片、视频等）的平台。

核心特点：
- **开源 (Apache-2.0)**，可自托管
- **Agent 原生**：支持 22+ 编程 Agent CLI，不绑定某个模型
- **本地优先**：数据不离开你的电脑，BYOK（自带 API Key）
- **品牌级设计系统**：内置 150 个 DESIGN.md 设计系统（Linear、Stripe、Apple、Tesla 等）
- **100+ Skills**、**261 个插件**
- **产物类型丰富**：网页原型、移动原型、Dashboard、PPT/Deck、图片、视频（HyperFrames）

---

## 二、Windows 安装方式

### 方式一：桌面应用（推荐，零配置）

最简单的方式，不需要安装 Node.js 或 pnpm。

1. 前往 [GitHub Releases](https://github.com/nexu-io/open-design/releases) 下载 Windows x64 安装包（如 `open-design-0.10.0-win-x64-setup.exe`）
2. 运行安装程序
3. 安装完成后启动，应用会自动检测 PATH 上的编程 Agent CLI

**注意：Windows SmartScreen 警告**

首次运行安装程序时，Windows Defender SmartScreen 会弹出蓝色警告框（"Windows protected your PC"），显示 "Publisher: Unknown publisher"。这是因为安装包没有代码签名证书，**不代表程序不安全**。

解决步骤：
1. 点击 **"更多信息"（More info）**
2. 点击 **"仍要运行"（Run anyway）**
3. 正常继续安装

> ⚠️ 只从 [open-design.ai](https://open-design.ai/) 或 [GitHub Releases](https://github.com/nexu-io/open-design/releases) 下载，不要从第三方镜像下载。

验证下载完整性（可选）：
```powershell
Get-FileHash .\open-design-x.y.z-win-x64-setup.exe -Algorithm SHA256
```
将输出的哈希值与 Release 页面上的 SHA-256 校验和对比。

---

### 方式二：从源码构建（开发者模式）

适合想要参与开发或需要最新功能的用户。

#### 前置依赖

| 工具 | 版本 | 验证命令 |
|------|------|---------|
| Node.js | `~24` (24.x) | `node -v` |
| pnpm | `10.33.x` | `pnpm -v` |
| Git | 任意近期版本 | `git --version` |

#### 安装步骤

```powershell
# 1. 克隆仓库
git clone https://github.com/nexu-io/open-design.git
cd open-design

# 2. 启用 Corepack（自动选择正确的 pnpm 版本）
corepack enable

# 3. 安装依赖
pnpm install

# 4. 启动开发服务器
pnpm tools-dev run web
```

启动后终端会输出类似：
```
Open Design dev server ready
  - Local:   http://localhost:17573
```

在浏览器中打开该地址即可使用。

#### 快速启动脚本（可选）

在仓库根目录创建 `launch.bat`：
```bat
@echo off
cd /d %~dp0
corepack pnpm tools-dev run web
```
以后双击即可启动。

---

### 方式三：Docker

适合不想在本机安装 Node.js 的用户。

```powershell
# 1. 克隆仓库
git clone https://github.com/nexu-io/open-design.git
cd open-design\deploy

# 2. 创建环境配置
copy .env.example .env

# 3. 生成安全令牌
openssl rand -hex 32

# 4. 将生成的令牌填入 .env 文件的 OD_API_TOKEN=

# 5. 启动容器
docker compose up -d

# 6. 打开浏览器
# http://localhost:7456
```

常用 Docker 命令：
```powershell
docker compose logs -f          # 查看日志
docker compose restart          # 重启容器
docker compose down             # 停止容器
docker compose pull             # 拉取最新镜像
docker compose down -v          # 删除所有本地数据
```

---

## 三、Windows 常见问题排查

### 1. `pnpm` 命令找不到

**症状**：`pnpm : The term 'pnpm' is not recognized...`

**解决方案**：
```powershell
# 推荐：使用 Corepack
corepack enable
corepack pnpm --version   # 应输出 10.33.2
```

如果 `corepack enable` 报权限错误（`EPERM`/`EACCES`），用 npm 全局安装替代：
```powershell
npm install -g pnpm@10.33.2
```

### 2. Node 版本不对

**症状**：`node -v` 显示的不是 v24.x.x

**解决方案（推荐 nvm-windows）**：
1. 安装 [nvm-windows](https://github.com/coreybutler/nvm-windows/releases)
2. 在新的 PowerShell 窗口中：
```powershell
nvm install 24
nvm use 24
node -v   # 应输出 v24.x.x
```

**nvm-windows 常见坑**：如果运行 `nvm version` 或 `node -v` 弹出 "How do you want to open this file?" 对话框，说明 `C:\Windows\System32` 下有一个假的 `nvm` 文件（无扩展名），删除它然后重启 PowerShell。

### 3. 构建脚本被阻止

**症状**：`pnpm install` 时出现 `Ignored build scripts: better-sqlite3, ...`

**解决方案**：pnpm 10 默认阻止生命周期脚本，需要手动批准：
```powershell
pnpm approve-builds
# 批准 better-sqlite3、electron、esbuild 等
pnpm install
```

### 4. Visual Studio / gyp 构建错误

**症状**：`gyp ERR! find VS could not find Visual Studio` 或 `error MSB8036: The Windows SDK version was not found`

**解决方案**：安装 **Build Tools for Visual Studio 2022**，勾选以下工作负载：
- **Desktop development with C++**
- **MSVC v143 - VS 2022 C++ x64/x86 build tools**
- **Windows 11 SDK**（或 Windows 10 SDK）

下载地址：https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

如果报 `gyp ERR! find Python`，确认 Python 已安装：
```powershell
python --version
```

### 5. PowerShell 脚本执行策略

**症状**：`cannot be loaded because running scripts is disabled on this system.`

**解决方案**：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
修改后重启 PowerShell。

### 6. "no agents found on PATH"

**症状**：启动后提示找不到 Agent

**解决方案**：安装至少一个支持的 Agent CLI（如 `claude`、`codex`、`cursor-agent`、`copilot` 等），或者在 Settings 中切换到 API 模式，粘贴 API Key。

### 7. `better-sqlite3` 加载失败 / ABI 不匹配

**症状**：切换 Node 版本后启动失败

**解决方案**：
```powershell
pnpm install   # 会自动重新编译 native addon
# 或手动重建：
pnpm --filter @open-design/daemon rebuild better-sqlite3
```

### 8. 诊断命令清单

遇到问题时，在 PowerShell 中运行以下命令，将输出附在 Issue 中：
```powershell
node -v
pnpm -v
where.exe pnpm
where.exe node
corepack --version
python --version
Get-ExecutionPolicy -List
```

---

## 四、使用技巧

### 4.1 快速上手流程

1. 启动 Open Design（桌面应用或 `pnpm tools-dev run web`）
2. 在 **Home** 页面选择一个 **Skill**（如 `web-prototype`）
3. 选择一个 **Design System**（如 `linear-app`）
4. 输入你的设计需求描述（brief）
5. 点击 **Send**，Agent 会生成 HTML 原型并实时预览

### 4.2 核心概念

| 概念 | 说明 |
|------|------|
| **Skill** | 告诉 Agent 生成什么类型的产物（原型、PPT、Dashboard 等） |
| **Design System** | 告诉 Agent 用什么视觉风格（品牌色彩、字体、间距等） |
| **Plugin** | 可复用的工作流，可以串联多个步骤 |
| **Brief** | 你对设计需求的自然语言描述 |

### 4.3 Skill 速查

| Skill | 用途 |
|-------|------|
| `web-prototype` | 通用网页原型（默认） |
| `saas-landing` | SaaS 落地页（Hero / 特性 / 定价 / CTA） |
| `dashboard` | 管理后台 / 数据看板 |
| `mobile-app` | 手机 App 原型（带 iPhone 框架） |
| `mobile-onboarding` | 手机引导页流程 |
| `social-carousel` | 社交媒体轮播图（1080×1080） |
| `email-marketing` | 品牌营销邮件 |
| `guizang-ppt` | 杂志风 Web PPT（Deck 默认） |
| `hyperframes` | HTML → MP4 动态图形 |
| `pm-spec` | PM 产品需求文档 |
| `team-okrs` | OKR 记分卡 |
| `finance-report` | 财务报告 |

### 4.4 使用 MCP 集成到编程 Agent

如果你想在 Claude Code、Codex、Cursor 等 Agent 中直接调用 Open Design：

```powershell
# 一键安装 MCP 集成
od mcp install claude     # Claude Code
od mcp install codex      # Codex
od mcp install cursor     # Cursor
od mcp install copilot    # GitHub Copilot

# 预览安装内容（不实际安装）
od mcp install claude --print

# 卸载
od mcp install claude --uninstall
```

安装后，在 Agent 中可以直接说：
```
> Use open-design to generate a landing page with the Linear design system
```

### 4.5 导出格式

- **HTML** — 单文件，内联所有资源
- **PDF** — 浏览器打印模式
- **PPTX** — Agent 驱动的导出
- **MP4** — HyperFrames 动态图形
- **ZIP** — 归档包
- **Markdown** — 文本格式

### 4.6 CLI 常用命令

```powershell
# 插件管理
od plugin list                        # 列出已安装插件
od plugin search "landing page"       # 按关键词搜索
od plugin install od-figma-migration  # 安装插件
od plugin apply od-default --input brief="..."  # 应用插件

# 文件操作
od search-files "primary button"      # 跨项目搜索文件
od get-file design-systems/linear-app/DESIGN.md  # 获取设计系统文件
od get-artifact <slug>                # 获取最新渲染产物

# 技能列表
od skill list --scenario marketing
```

### 4.7 BYOK 模式（自带 API Key）

如果没有安装任何 Agent CLI，可以在 Settings 中切换到 API 模式，支持：
- Anthropic Claude
- OpenAI / Azure OpenAI
- Google Gemini
- Ollama / LM Studio / vLLM
- 任何 OpenAI 兼容端点

---

## 五、WSL2 用户注意事项

如果你的编程 Agent CLI 在 WSL2 内运行，**建议也在 WSL2 内安装和运行 Open Design**，而不是使用 Windows 桌面应用的 Daemon。原因：

- WSL2 网络和 Windows 凭据存储可能导致连接问题
- WSL 内启动的 Daemon 保持 MCP 客户端和 Open Design 在同一环境中

关键步骤：
1. 在 WSL2 内克隆和安装 Open Design
2. **解决 `od` 命令冲突**：Linux 自带 `/usr/bin/od`（octal dump），需要创建 wrapper 让 Open Design 的 `od` 优先

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/od <<'EOF'
#!/usr/bin/env bash
repo="$HOME/tools/open-design"
cd "$repo" || exit 127
exec corepack pnpm exec od "$@"
EOF
chmod +x ~/.local/bin/od
export PATH="$HOME/.local/bin:$PATH"
```

---

## 六、参考链接

| 资源 | 链接 |
|------|------|
| 官网 | https://open-design.ai/ |
| GitHub | https://github.com/nexu-io/open-design |
| Releases | https://github.com/nexu-io/open-design/releases |
| Discord | https://discord.gg/9ptkbbqRu |
| Windows 排查指南 | https://github.com/nexu-io/open-design/blob/main/docs/windows-troubleshooting.md |
| WSL2 配置指南 | https://github.com/nexu-io/open-design/blob/main/docs/wsl-setup.md |
| Quickstart | https://github.com/nexu-io/open-design/blob/main/QUICKSTART.md |
| AMR 模型路由 | https://open-design.ai/amr/ |
