"""
通用 Prompt Runner — 从 CSV 读取数据，批量调用 LLM API

使用方法：
    # 默认运行（多线程 3，自动续跑）
    python run.py --csv data/input.csv

    # 指定线程数
    python run.py --csv data/input.csv --workers 5

    # 从头开始跑
    python run.py --csv data/input.csv --restart

    # 只跑第 10-20 条
    python run.py --csv data/input.csv --start 10 --end 20

    # 预览会执行哪些（不实际调用 API）
    python run.py --csv data/input.csv --dry-run

    # 指定任务名（影响输出目录）
    python run.py --csv data/input.csv --task-name my_task

依赖：pip install openai python-dotenv
"""

import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ============================================================
# 配置区 — 用户根据需要修改
# ============================================================

# Prompt 模板：{input} 会被替换为 CSV 每行的输入文本
PROMPT_TEMPLATE = """请处理以下内容：

{input}
"""

# CSV 中用作输入的列名（留空则取第一列）
INPUT_COLUMN = ""

# 默认使用的模型
MODEL = "gpt-4o-mini"

# 超时时间（秒）
TIMEOUT = 30

# 最大重试次数
MAX_RETRIES = 3

# ============================================================


def load_client() -> OpenAI:
    """初始化 OpenAI 客户端，从 .env 读取配置"""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")

    if not api_key:
        print("错误：未设置 OPENAI_API_KEY，请在 .env 文件中配置")
        sys.exit(1)

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    return OpenAI(**kwargs)


def read_csv(csv_path: str, input_column: str = "") -> list[dict]:
    """
    读取 CSV 文件，返回 [{index, input}, ...]

    Args:
        csv_path: CSV 文件路径
        input_column: 指定用作输入的列名，留空取第一列

    Returns:
        包含序号和输入文本的字典列表
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"错误：CSV 文件不存在 → {csv_path}")
        sys.exit(1)

    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if input_column and input_column in row:
                text = row[input_column].strip()
            else:
                # 取第一列
                text = list(row.values())[0].strip()
            if text:
                rows.append({"index": i, "input": text})

    print(f"从 CSV 读取到 {len(rows)} 条数据")
    return rows


def call_llm(client: OpenAI, user_input: str, model: str) -> dict:
    """
    调用 LLM API，带重试机制

    Args:
        client: OpenAI 客户端
        user_input: 用户输入文本
        model: 模型名称

    Returns:
        {success, content, error, usage} 字典
    """
    prompt = PROMPT_TEMPLATE.format(input=user_input)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=TIMEOUT,
            )
            content = response.choices[0].message.content or ""
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            return {"success": True, "content": content, "error": None, "usage": usage}

        except Exception as e:
            error_msg = str(e)
            # 不可重试的错误
            if any(code in error_msg for code in ["401", "400"]):
                return {"success": False, "content": "", "error": error_msg, "usage": {}}

            # 可重试：等待后重试
            if attempt < MAX_RETRIES - 1:
                wait = attempt + 1
                print(f"  调用失败，{wait}s 后重试: {error_msg[:80]}")
                time.sleep(wait)

    return {"success": False, "content": "", "error": "超过最大重试次数", "usage": {}}


def save_result(output_dir: Path, item: dict, result: dict, task_name: str):
    """
    保存单条结果到 JSON 文件（每条即时存盘）

    Args:
        output_dir: 输出目录
        item: 输入数据 {index, input}
        result: API 返回结果 {success, content, error, usage}
        task_name: 任务名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"{item['index']:04d}_{timestamp}.json"
    filepath = output_dir / filename

    data = {
        "task_name": task_name,
        "index": item["index"],
        "input": item["input"],
        "prompt": PROMPT_TEMPLATE.format(input=item["input"]),
        "result": result,
        "timestamp": datetime.now().isoformat(),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_completed_indices(output_dir: Path) -> set[int]:
    """
    扫描输出目录，获取已完成的序号集合（用于断点续跑）

    Args:
        output_dir: 输出目录

    Returns:
        已完成的序号集合
    """
    completed = set()
    if not output_dir.exists():
        return completed

    for f in output_dir.glob("*.json"):
        try:
            # 文件名格式：0001_20260709_xxx.json
            idx = int(f.name.split("_")[0])
            completed.add(idx)
        except (ValueError, IndexError):
            continue

    return completed


def process_item(client: OpenAI, item: dict, model: str) -> dict:
    """处理单条数据（调用 API）"""
    result = call_llm(client, item["input"], model)
    return {"item": item, "result": result}


def main():
    """主函数：解析参数、读取数据、并发调用、保存结果"""
    parser = argparse.ArgumentParser(description="通用 Prompt Runner — 批量调用 LLM API")
    parser.add_argument("--csv", required=True, help="CSV 文件路径")
    parser.add_argument("--workers", type=int, default=3, help="并发线程数（默认 3）")
    parser.add_argument("--restart", action="store_true", help="清空历史结果，从头开始")
    parser.add_argument("--start", type=int, default=0, help="从第 N 条开始（0-based）")
    parser.add_argument("--end", type=int, default=-1, help="跑到第 N 条结束（不含，-1 表示全部）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不实际调用")
    parser.add_argument("--task-name", default="prompt_run", help="任务名（影响输出目录）")
    parser.add_argument("--column", default="", help="CSV 中用作输入的列名（默认取第一列）")
    parser.add_argument("--model", default=MODEL, help=f"使用的模型（默认 {MODEL}）")
    args = parser.parse_args()

    # 输出目录
    output_dir = Path("outputs") / args.task_name

    # 重启模式：清空输出目录
    if args.restart and output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
        print(f"已清空输出目录：{output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 读取 CSV
    rows = read_csv(args.csv, args.column or INPUT_COLUMN)
    if not rows:
        print("CSV 中没有有效数据，退出")
        sys.exit(0)

    # 切片
    end = args.end if args.end >= 0 else len(rows)
    rows = rows[args.start:end]
    print(f"本次处理范围：第 {args.start} ~ {end - 1} 条，共 {len(rows)} 条")

    # 断点续跑：跳过已完成
    completed = get_completed_indices(output_dir)
    if completed and not args.restart:
        before = len(rows)
        rows = [r for r in rows if r["index"] not in completed]
        print(f"断点续跑：跳过 {before - len(rows)} 条已完成，剩余 {len(rows)} 条")

    if not rows:
        print("所有数据已完成，无需处理")
        return

    # Dry run
    if args.dry_run:
        print("\n=== DRY RUN ===")
        for item in rows[:5]:
            print(f"  [{item['index']}] {item['input'][:60]}...")
        if len(rows) > 5:
            print(f"  ... 共 {len(rows)} 条")
        print("===============")
        return

    # 初始化客户端
    client = load_client()
    print(f"\n开始调用 API（模型: {args.model}，线程: {args.workers}）\n")

    # 多线程并发执行
    success_count = 0
    fail_count = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_item, client, item, args.model): item
            for item in rows
        }

        for future in as_completed(futures):
            item = futures[future]
            try:
                ret = future.result()
                result = ret["result"]

                # 即时保存
                save_result(output_dir, ret["item"], result, args.task_name)

                if result["success"]:
                    success_count += 1
                    tokens = result["usage"].get("total_tokens", "?")
                    print(f"  ✓ [{ret['item']['index']}] 成功 ({tokens} tokens)")
                else:
                    fail_count += 1
                    print(f"  ✗ [{ret['item']['index']}] 失败: {result['error'][:60]}")

            except Exception as e:
                fail_count += 1
                print(f"  ✗ [{item['index']}] 异常: {e}")

    # 汇总
    elapsed = time.time() - start_time
    print(f"\n完成！成功 {success_count}，失败 {fail_count}，耗时 {elapsed:.1f}s")
    print(f"结果保存在: {output_dir}")


if __name__ == "__main__":
    main()
