# Python 脚本生成规范

当生成 Python 脚本时，必须遵循以下规则。

## LLM API 调用（优先级最高）

当脚本涉及调用大模型/生成式 AI 接口时：

### SDK 选择
- 统一使用 `openai` SDK 的调用方式（兼容 OpenAI/智谱/百度/小米/Deepseek 等所有兼容 OpenAI 格式的接口）
- 不要用 `requests` 手动拼 HTTP 请求
- 通过 `base_url` 参数切换不同厂商的接口地址

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),  # 切换厂商只需改这个
)
```

### 禁止截断输出
- **禁止添加 `max_tokens` 参数**，除非用户明确要求
- 不要设置 `max_completion_tokens`、`stop` 等可能截断输出的参数
- 让模型自然返回完整结果

### 调用结果持久化
- 每次 API 调用的输入和输出**必须保存到本地文件**
- 保存路径：`outputs/<任务名>/<时间戳>.json`
- 保存内容：完整请求参数 + 完整响应 + 时间戳 + 状态
- 目的：失败后可复跑，不用重新调用浪费 token

```python
import json
from datetime import datetime
from pathlib import Path

def save_result(task_name: str, request_data: dict, response_data: dict):
    """保存每次调用结果，用于失败复跑"""
    output_dir = Path("outputs") / task_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    record = {
        "timestamp": timestamp,
        "request": request_data,
        "response": response_data,
        "status": "success",
    }
    
    filepath = output_dir / f"{timestamp}.json"
    filepath.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return filepath
```

### 超时与重试
- 必须设置 `timeout`（默认 120 秒，长文本生成可适当增大）
- 失败后自动重试，最多 3 次
- 重试间隔用指数退避（2s → 4s → 8s）
- 区分可重试错误（超时、限流 429、服务器 5xx）和不可重试错误（认证失败 401、参数错误 400）

```python
import time
from openai import APITimeoutError, RateLimitError, APIStatusError

def call_with_retry(client, max_retries=3, **kwargs):
    """带重试的 API 调用"""
    kwargs.setdefault("timeout", 120.0)
    
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except APITimeoutError:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"超时，{wait}s 后重试 ({attempt+1}/{max_retries})...")
            time.sleep(wait)
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"限流，{wait}s 后重试 ({attempt+1}/{max_retries})...")
            time.sleep(wait)
        except APIStatusError as e:
            if e.status_code >= 500 and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"服务器错误 {e.status_code}，{wait}s 后重试...")
                time.sleep(wait)
            else:
                raise
```

### 复跑机制
- 脚本支持从已保存的结果文件恢复
- 检查 outputs 目录下是否已有结果，有则跳过该条目
- 命令行参数：`--resume` 启用复跑模式

## 通用 Python 规范

### 类型与格式
- Python 3.10+ 语法，类型提示用 `X | Y` 而不是 `Optional[X]`
- 字符串一律用 f-string
- 路径用 `pathlib.Path`，不用 `os.path`
- 编码一律 `encoding="utf-8"`

### 错误处理
- 异常要具体，禁止 `except Exception` 或裸 `except`
- 捕获后要记录错误信息，不要空 catch
- 关键操作要有 try-except 包裹

### 依赖管理
- 用 `requirements.txt` 或脚本顶部注释列出依赖
- 常用依赖版本：`openai>=1.0.0`, `httpx`, `python-dotenv`

### 输出与日志
- 进度信息打印到控制台
- 结果数据保存到文件
- 长时间运行的任务显示进度

### 安全
- API key 等敏感信息从 `.env` 读取，用 `python-dotenv`
- 禁止硬编码密钥/token/密码
- `.env` 文件加入 `.gitignore`
