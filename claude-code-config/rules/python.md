# Python 脚本生成规范

## LLM API 调用（优先级最高）

- 统一用 `openai` SDK，通过 `base_url` 切换厂商，不要用 requests 手动拼
- **禁止添加 `max_tokens`、`max_completion_tokens`、`stop` 等截断参数**，除非用户明确要求
- API key 从 `.env` 读取，禁止硬编码

## 结果持久化

- **每调用一次 API，立即保存一次**，不要攒到最后批量保存
- 保存到 `outputs/<任务名>/<序号>_<时间戳>.json`
- 内容：完整请求参数 + 完整响应 + 序号 + 时间戳 + 状态
- 中途崩溃不丢数据

## 超时与重试

- timeout 默认 30 秒（长文本不超过 60 秒）
- 最多重试 3 次，间隔 1s → 2s → 3s
- 可重试：超时、429、5xx
- 不可重试：401、400（直接报错）

## 多线程并发

- **默认多线程并发执行**，不许单线程串行跑
- 默认线程数 **3**，通过 `--workers N` 参数调整
- 用 `concurrent.futures.ThreadPoolExecutor`
- 多线程时注意结果保存的线程安全（每条存盘无锁问题）

## 断点续跑（默认行为）

- **默认续跑**：重新运行自动检测 outputs 目录，跳过已完成条目
- **`--restart`**：清空历史结果，从头开始（必须显式指定才从头跑）
- **`--start N`**：从第 N 条开始
- **`--end N`**：跑到第 N 条结束
- **`--dry-run`**：只打印计划，不实际调用
- **`--workers N`**：并发线程数（默认 3）
- **`--task-name xxx`**：区分不同批次

## 通用规范

- Python 3.10+，类型提示用 `X | Y`
- 字符串用 f-string，路径用 pathlib
- 异常要具体，禁止 `except Exception`
- 编码一律 `encoding="utf-8"`
- `.env` 加入 `.gitignore`
