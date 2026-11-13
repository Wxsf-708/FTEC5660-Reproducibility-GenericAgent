"""稳定性研究综合统计：对比 baseline(temp=1.0) 与 temp0(temp=0.0)。

对每个 label 计算：
  1. 官方 / 语义成功率（总体与每任务）；
  2. inp/out token 的均值与标准差、总 token；
  3. 运行轮数的均值与标准差（从 response 解析）；
  4. 输出一致性：同一任务 5 次重复的最终答案规范化后是否一致（unique 答案数）。
结果写入 results/stability_analysis.json，并打印对比表。
"""
import json
import os
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
LABELS = ["baseline", "temp0"]


def extract_final_answer(text):
    # 优先最后一个 ```json 块（agent 最终答案通常在末尾），规范化后比较；
    # 找不到则用纯文本（如 teb_06 的 OK）。
    blocks = re.findall(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    if blocks:
        try:
            return "json:" + json.dumps(json.loads(blocks[-1]),
                                        sort_keys=True, ensure_ascii=False)
        except Exception:
            return "json:" + blocks[-1].strip()
    # 纯文本任务（如 teb_06 输出 OK）：只取最后一个非空行作为最终答案，忽略运行过程。
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return "text:" + (lines[-1] if lines else "")


def count_turns(text):
    turns = [int(m) for m in re.findall(r"LLM Running \(Turn (\d+)", text)]
    return max(turns) if turns else 0


def analyze_label(label):
    summary = json.loads((RESULTS / label / "summary.json").read_text(encoding="utf-8"))
    gw = json.loads((RESULTS / label / "grade_windows.json").read_text(encoding="utf-8"))
    # grade_windows 的 row 无 run_idx：按 task_id 分组后按顺序对应每任务内序号 1..n。
    gw_by_task = {}
    for r in gw["rows"]:
        gw_by_task.setdefault(r["task_id"], []).append(r)
    sem_map = {}
    for tid, grs in gw_by_task.items():
        for j, r in enumerate(grs, start=1):
            sem_map[(tid, j)] = r["semantic_success"]

    rows = summary["rows"]
    per_task = {}
    inp, out, turns = [], [], []
    n_off, n_sem = 0, 0
    for r in rows:
        tid, idx = r["task_id"], r["run_idx"]
        inp.append(r["inp_tokens"]); out.append(r["out_tokens"])
        answer = extract_final_answer(Path(r["response_file"]).read_text(
            encoding="utf-8", errors="replace"))
        t = count_turns(Path(r["response_file"]).read_text(
            encoding="utf-8", errors="replace"))
        turns.append(t)
        sem = sem_map.get((tid, idx), r["task_success"])
        n_off += 1 if r["task_success"] else 0
        n_sem += 1 if sem else 0
        per_task.setdefault(tid, {"official": 0, "semantic": 0, "n": 0,
                                  "answers": []})
        per_task[tid]["official"] += 1 if r["task_success"] else 0
        per_task[tid]["semantic"] += 1 if sem else 0
        per_task[tid]["n"] += 1
        per_task[tid]["answers"].append(answer)

    task_report = {}
    for tid, d in per_task.items():
        unique = sorted(set(d["answers"]))
        task_report[tid] = {
            "official_rate": "%d/%d" % (d["official"], d["n"]),
            "semantic_rate": "%d/%d" % (d["semantic"], d["n"]),
            "unique_answer_count": len(unique),
            "fully_consistent": len(unique) == 1,
        }

    def ms(vals):
        return {"mean": round(statistics.mean(vals), 2),
                "median": round(statistics.median(vals), 2),
                "std": round(statistics.pstdev(vals), 2),
                "total": sum(vals),
                "max": max(vals)}

    return {
        "label": label,
        "temperature": summary["temperature"],
        "n_runs": len(rows),
        "official_success_rate": round(n_off / len(rows), 4),
        "semantic_success_rate": round(n_sem / len(rows), 4),
        "inp_tokens": ms(inp),
        "out_tokens": ms(out),
        "turns": ms(turns),
        "per_task": task_report,
    }


def main():
    report = {label: analyze_label(label) for label in LABELS}
    out_path = RESULTS / "stability_analysis.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    b, t = report["baseline"], report["temp0"]
    print("%-28s %-18s %-18s" % ("指标", "baseline (T=1.0)", "temp0 (T=0.0)"))
    print("-" * 66)
    print("%-28s %-18s %-18s" % ("官方成功率", b["official_success_rate"],
                                 t["official_success_rate"]))
    print("%-28s %-18s %-18s" % ("语义成功率", b["semantic_success_rate"],
                                 t["semantic_success_rate"]))
    for key, name in [("inp_tokens", "输入token 均值[中位数]"),
                      ("out_tokens", "输出token 均值[中位数]"),
                      ("turns", "轮数 均值[中位数]")]:
        print("%-28s %-18s %-18s" % (name,
              "%s [%s]" % (b[key]["mean"], b[key]["median"]),
              "%s [%s]" % (t[key]["mean"], t[key]["median"])))
    print("\n每任务输出一致性（unique 答案数，1=完全一致）：")
    print("%-32s %-16s %-16s" % ("task", "baseline", "temp0"))
    for tid in b["per_task"]:
        print("%-32s %-16s %-16s" % (tid,
              b["per_task"][tid]["unique_answer_count"],
              t["per_task"][tid]["unique_answer_count"]))
    print("\n已保存:", out_path)


if __name__ == "__main__":
    main()
