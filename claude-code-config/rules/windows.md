# Windows 命令与路径规范

## Shell 分工
- PowerShell：文件操作、系统命令、npm/node
- Bash 工具：Git 操作、shell 脚本
- 跨平台安全命令优先：`npm`、`npx`、`node`、`python`、`git`

## 命令对照表

| 操作 | PowerShell | 禁止（Unix） |
|------|-----------|-------------|
| 列文件 | `Get-ChildItem` / `ls` | `dir`(cmd), `ll` |
| 递归搜索 | `Get-ChildItem -Recurse -Filter *.ts` | `find . -name "*.ts"` |
| 读文件 | `Get-Content` | `cat`, `head`, `tail` |
| 删目录 | `Remove-Item -Recurse -Force` | `rm -rf` |
| 创建目录 | `New-Item -ItemType Directory` | `mkdir -p` |
| 环境变量 | `$env:VAR` | `export VAR=`, `$VAR` |
| 搜索文本 | `Select-String` | `grep` |
| 下载 | `Invoke-WebRequest` | `curl` |
| 替换 | `-replace` 操作符 | `sed` |
| 查命令路径 | `(Get-Command name).Source` | `which` |

## 路径规则
- **一律用绝对路径**，不要用 `~` 或相对路径
- **用正斜杠 `/`**，不要用反斜杠（转义问题）
- **中文/空格路径必须加引号**：`"C:\Users\17343\Desktop\学习\file.md"`
- 代码中用 `path.join` / `Path.Combine`，禁止硬编码 `\\`

## 禁止假设
- Windows 没有 `which`、`grep`、`sed`、`awk`、`curl`
- PowerShell 中 `>` 重定向行为与 bash 不同，用 `Out-File`
- 含空格路径执行程序用 `& "C:\Program Files\..."` 调用
- 输出超 30000 字符会截断，用 `Select-Object -First N` 限制
