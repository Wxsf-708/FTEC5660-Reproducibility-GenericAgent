"""批量运行 tool_efficiency benchmark 并调用官方 grader 汇总。

为每个任务的每次重复：
  1. 创建独立 workspace，把该任务 assets/<task_id>/ 的内容复制进去；
  2. 用独立子进程运行 run_single.py（进程级隔离）；
  3. 调用官方 grader 评分，解析 task_success；
  4. 汇总成功率与 token 用量到 results/<label>/。

示例：
  python run_benchmark.py --label baseline --tasks teb_01,teb_02,teb_07,teb_08,teb_06
  python run_benchmark.py --label temp0 --temperature 0.0
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BENCH_DIR = os.path.join(PROJECT_ROOT, "benchmark", "tool_efficiency_benchmark")
TASKS_JSONL = os.path.join(BENCH_DIR, "tool_efficiency_tasks.jsonl")
VENV_PY = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
RUN_SINGLE = os.path.join(PROJECT_ROOT, "scripts", "run_single.py")
WORKSPACES_ROOT = os.path.join(PROJECT_ROOT, "workspaces")
RESULTS_ROOT = os.path.join(PROJECT_ROOT, "results")


def load_tasks():
    records = {}
    with open(TASKS_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                records[rec["task_id"]] = rec
    return records


def resolve_task_ids(records, selected):
    if not selected:
        return list(records.keys())
    chosen = []
    for token in selected:
        token = token.strip()
        matches = [tid for tid in records if tid == token or tid.startswith(token)]
        if not matches:
            print("[WARN] 未找到匹配任务: %s" % token)
        for tid in matches:
            if tid not in chosen:
                chosen.append(tid)
    return chosen


def run_one(task_id, rec, label, run_idx, args):
    workspace = os.path.join(WORKSPACES_ROOT, label, task_id, "r%d" % run_idx)
    out_dir = os.path.join(RESULTS_ROOT, label, task_id, "r%d" % run_idx)
    if os.path.exists(workspace):
        shutil.rmtree(workspace)
    os.makedirs(workspace, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    # 复制 assets/<task_id>/ 的内容到 workspace 根（保留内部结构）。
    asset_src = os.path.join(BENCH_DIR, "assets", task_id)
    if os.path.isdir(asset_src):
        shutil.copytree(asset_src, workspace, dirs_exist_ok=True)

    prompt_file = os.path.join(out_dir, "prompt.txt")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(rec["prompt"])

    response_file = os.path.join(out_dir, "response.txt")
    stats_file = os.path.join(out_dir, "stats.json")

    cmd = [
        VENV_PY, RUN_SINGLE,
        "--workspace", workspace,
        "--prompt-file", prompt_file,
        "--output", response_file,
        "--stats", stats_file,
        "--max-turns", str(args.max_turns),
        "--timeout", str(args.timeout),
    ]
    if args.temperature is not None:
        cmd += ["--temperature", str(args.temperature)]
    if args.disable_tools:
        cmd += ["--disable-tools", args.disable_tools]

    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=args.timeout + 120, encoding="utf-8")
    elapsed = time.time() - t0
    if proc.returncode != 0:
        print("  [run_single 返回码 %s] %s" % (proc.returncode, proc.stderr[-500:]))

    # 调用官方 grader。
    grader_path = os.path.join(BENCH_DIR, rec["grader"])
    gcmd = [VENV_PY, grader_path, "--workspace", workspace,
            "--response-file", response_file]
    gproc = subprocess.run(gcmd, capture_output=True, text=True, encoding="utf-8")
    grade = {}
    try:
        grade = json.loads(gproc.stdout.strip().splitlines()[-1])
    except Exception:
        grade = {"task_success": False, "grader_error": gproc.stdout + gproc.stderr}

    stats = {}
    if os.path.exists(stats_file):
        try:
            with open(stats_file, encoding="utf-8") as f:
                stats = json.load(f)
        except Exception:
            pass

    return {
        "task_id": task_id,
        "run_idx": run_idx,
        "task_success": bool(grade.get("task_success")),
        "grade": grade,
        "elapsed_sec": round(elapsed, 1),
        "inp_tokens": stats.get("inp", 0),
        "out_tokens": stats.get("out", 0),
        "cached_tokens": stats.get("cached", 0),
        "model": stats.get("model", ""),
        "workspace": workspace,
        "response_file": response_file,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--tasks", default="teb_01,teb_02,teb_07,teb_08,teb_06")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--disable-tools", default="")
    parser.add_argument("--max-turns", type=int, default=40)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    records = load_tasks()
    task_ids = resolve_task_ids(records, args.tasks.split(","))
    print("本次运行 label=%s，任务 %d 个，每个重复 %d 次，共 %d 次调用。"
          % (args.label, len(task_ids), args.repeats, len(task_ids) * args.repeats))

    rows = []
    for tid in task_ids:
        for r in range(1, args.repeats + 1):
            print("-> %s [run %d] ..." % (tid, r), flush=True)
            try:
                row = run_one(tid, records[tid], args.label, r, args)
            except subprocess.TimeoutExpired:
                row = {"task_id": tid, "run_idx": r, "task_success": False,
                       "grade": {"timeout": True}, "elapsed_sec": args.timeout,
                       "inp_tokens": 0, "out_tokens": 0, "cached_tokens": 0,
                       "model": "", "workspace": "", "response_file": ""}
            rows.append(row)
            print("   success=%s  用时=%ss  inp=%s out=%s"
                  % (row["task_success"], row["elapsed_sec"],
                     row["inp_tokens"], row["out_tokens"]))

    label_dir = os.path.join(RESULTS_ROOT, args.label)
    os.makedirs(label_dir, exist_ok=True)
    with open(os.path.join(label_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"label": args.label, "temperature": args.temperature,
                   "disable_tools": args.disable_tools, "rows": rows},
                  f, ensure_ascii=False, indent=2)

    csv_path = os.path.join(label_dir, "summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["task_id", "run_idx", "task_success", "elapsed_sec",
                         "inp_tokens", "out_tokens", "cached_tokens", "model"])
        for row in rows:
            writer.writerow([row["task_id"], row["run_idx"], row["task_success"],
                             row["elapsed_sec"], row["inp_tokens"],
                             row["out_tokens"], row["cached_tokens"], row["model"]])

    total = len(rows)
    successes = sum(1 for r in rows if r["task_success"])
    print("\n===== 汇总（label=%s）=====" % args.label)
    print("总体成功率: %d/%d = %.1f%%" % (successes, total, 100 * successes / max(total, 1)))
    by_task = {}
    for r in rows:
        by_task.setdefault(r["task_id"], []).append(r["task_success"])
    for tid, oks in by_task.items():
        print("  %s: %d/%d 成功" % (tid, sum(oks), len(oks)))
    print("总 inp tokens=%s，总 out tokens=%s"
          % (sum(r["inp_tokens"] for r in rows), sum(r["out_tokens"] for r in rows)))
    print("明细已保存: %s" % label_dir)


if __name__ == "__main__":
    main()
