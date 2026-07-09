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
- **每调用一次 API，立即保存一次**，不要攒到最后批量保存
- 保存路径：`outputs/<任务名>/<序号>_<时间戳>.json`
- 保存内容：完整请求参数 + 完整响应 + 时间戳 + 状态
- 目的：中途崩溃也不丢数据，失败后可从断点复跑

```python
import json
from datetime import datetime
from pathlib import Path

def save_result(task_name: str, index: int, request_data: dict, response_data: dict):
    """每次 API 调用后立即保存，不是任务结束后批量保存"""
    output_dir = Path("outputs") / task_name
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    record = {
        "timestamp": timestamp,
        "index": index,
        "request": request_data,
        "response": response_data,
        "status": "success",
    }

    filepath = output_dir / f"{index:04d}_{timestamp}.json"
    filepath.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return filepath

# 调用示例：每条数据调完立刻存盘
for i, item in enumerate(data_list):
    response = call_with_retry(client, messages=[...])
    save_result("my_task", i, request_data=item, response_data=response.model_dump())
```

### 超时与重试
- 必须设置 `timeout`（默认 30 秒，长文本生成可适当增大但不超过 60 秒）
- 失败后自动重试，最多 3 次
- 重试间隔短平快：1s → 2s → 3s，不要等太久
- 区分可重试错误（超时、限流 429、服务器 5xx）和不可重试错误（认证失败 401、参数错误 400）

```python
import time
from openai import APITimeoutError, RateLimitError, APIStatusError

def call_with_retry(client, max_retries=3, **kwargs):
    """带重试的 API 调用"""
    kwargs.setdefault("timeout", 30.0)

    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except APITimeoutError:
            if attempt == max_retries - 1:
                raise
            wait = attempt + 1  # 1s, 2s, 3s
            print(f"超时，{wait}s 后重试 ({attempt+1}/{max_retries})...")
            time.sleep(wait)
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait = attempt + 1
            print(f"限流，{wait}s 后重试 ({attempt+1}/{max_retries})...")
            time.sleep(wait)
        except APIStatusError as e:
            if e.status_code >= 500 and attempt < max_retries - 1:
                wait = attempt + 1
                print(f"服务器错误 {e.status_code}，{wait}s 后重试...")
                time.sleep(wait)
            else:
                raise
```

### 复跑机制
- 因为每条数据调完就存盘，复跑时只需检查 outputs 目录下已有多少个结果文件
- 已有结果的条目自动跳过，从断点继续
- 命令行参数：`--resume` 启用复跑模式

```python
import glob

def get_completed_indices(task_name: str) -> set[int]:
    """获取已完成的条目序号，复跑时跳过"""
    output_dir = Path("outputs") / task_name
    if not output_dir.exists():
        return set()
    indices = set()
    for f in output_dir.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        indices.add(data["index"])
    return indices

# 复跑示例
completed = get_completed_indices("my_task") if resume else set()
for i, item in enumerate(data_list):
    if i in completed:
        print(f"跳过第 {i} 条（已有结果）")
        continue
    response = call_with_retry(client, messages=[...])
    save_result("my_task", i, request_data=item, response_data=response.model_dump())
```

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
