# Python 脚本生成规范

## LLM API 调用

- 统一用 `openai` SDK，通过 `base_url` 切换厂商
- **禁止 `max_tokens`、`max_completion_tokens`、`stop`**，除非用户明确要求
- API key 从 `.env` 读取，禁止硬编码

## 结果持久化

- **每调用一次 API 立即保存一次**，不要攒到最后
- 保存到 `outputs/<任务名>/<序号>_<时间戳>.json`，含完整请求+响应

## 超时与重试

- timeout 30 秒（长文本不超过 60 秒），最多重试 3 次，间隔 1s→2s→3s
- 可重试：超时、429、5xx；不可重试：401、400

## 多线程并发

- **默认多线程**，线程数 **3**，`--workers N` 可调
- 用 `concurrent.futures.ThreadPoolExecutor`

## 断点续跑

- **默认续跑**：重新运行自动跳过已完成条目
- `--restart` 从头开始 | `--start N` / `--end N` 范围 | `--dry-run` 预览 | `--task-name` 区分批次

## 注释与文档

- **所有注释和 docstring 用中文**
- 每个函数必须写 docstring
- **脚本顶部写使用说明**，包含完整命令示例

## 进度显示

- **必须有进度显示**，用 `print()` + `flush=True`，不要用 tqdm/rich（终端运行时看不到）
- 格式：`[当前/总数] 状态`，开始打印总条数，结束打印汇总

## 通用规范

- Python 3.10+，类型提示 `X | Y`，f-string，pathlib
- 异常要具体，禁止 `except Exception`
- 编码 `encoding="utf-8"`，`.env` 加入 `.gitignore`
