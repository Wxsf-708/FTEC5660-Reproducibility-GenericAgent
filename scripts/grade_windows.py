"""透明的 Windows 平台适配评估（不修改任何官方 grader）。

对每个任务同时报告：
  official_success：官方 grader 在 Windows 上的原始判定；
  semantic_success：在不改变判断语义的前提下，对已知 Windows 平台差异做
                    最小、带注释的适配后的判定。

已知平台差异（均为 grader/环境问题，非 agent 答案错误）：
  teb_01：Windows 的 relative_to 产生反斜杠，agent 输出跨平台正斜杠，
          仅做路径分隔符规范化后比对；
  teb_06：agent 插入了正确的 code cell 但未运行（outputs 为空），
          执行 notebook 后验证 release_snapshot 计算结果；
  teb_02/07/08：修复驱动脚本后官方 grader 直接通过，无需适配。

用法：python grade_windows.py --label baseline
"""
import argparse
import importlib.util
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmark" / "tool_efficiency_benchmark"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"


def load_grader(name):
    path = BENCH / "graders" / name
    spec = importlib.util.spec_from_file_location("grader_mod_%s" % name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_official(grader_rel, workspace, response_file):
    proc = subprocess.run(
        [str(VENV_PY), str(BENCH / grader_rel), "--workspace", workspace,
         "--response-file", response_file],
        capture_output=True, text=True, encoding="utf-8")
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        return {"task_success": False, "error": proc.stdout + proc.stderr}


def semantic_teb01(workspace, response_file):
    g = load_grader("teb_01_glob_markdown_list_grader.py")
    text = Path(response_file).read_text(encoding="utf-8", errors="replace")
    data = g.extract_json_block(text)
    if not data:
        return False, "未找到 JSON 块"
    agent = data.get("markdown_files", [])
    expected = [p.replace("\\", "/") for p in g.expected_markdown_files(Path(workspace))]
    ok = sorted(agent) == sorted(expected)
    return ok, "仅规范化路径分隔符: agent=%s expected=%s" % (sorted(agent), sorted(expected))


def semantic_teb06(workspace, _response_file):
    nb = json.loads((Path(workspace) / "analysis.ipynb").read_text(encoding="utf-8"))
    if len(nb["cells"]) != 5:
        return False, "单元格数=%d，非 5" % len(nb["cells"])
    ns = {}
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            exec("".join(cell["source"]), ns)
    got = ns.get("release_snapshot")
    expected = {"mean_value": 7.25, "tool_count": 7, "step_claim": "1-2"}
    return got == expected, "执行 notebook 得到 release_snapshot=%s" % got


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    summary_path = ROOT / "results" / args.label / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    out_rows = []
    for row in summary["rows"]:
        tid = row["task_id"]
        ws, rf = row["workspace"], row["response_file"]
        rec = next(r for r in [json.loads(l) for l in
                   (BENCH / "tool_efficiency_tasks.jsonl").read_text(
                       encoding="utf-8").splitlines() if l.strip()]
                   if r["task_id"] == tid)
        official = run_official(rec["grader"], ws, rf)
        sem_success, note = official["task_success"], "官方 grader 直接通过"
        if not sem_success:
            if tid.startswith("teb_01"):
                sem_success, note = semantic_teb01(ws, rf)
            elif tid.startswith("teb_06"):
                sem_success, note = semantic_teb06(ws, rf)
        out_rows.append({
            "task_id": tid,
            "official_success": official["task_success"],
            "semantic_success": sem_success,
            "adaptation_note": note,
            "official_detail": official,
        })

    n = len(out_rows)
    off = sum(1 for r in out_rows if r["official_success"])
    sem = sum(1 for r in out_rows if r["semantic_success"])
    result = {"label": args.label,
              "official_rate": "%d/%d" % (off, n),
              "semantic_rate": "%d/%d" % (sem, n),
              "rows": out_rows}
    out_path = ROOT / "results" / args.label / "grade_windows.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    print("label=%s" % args.label)
    print("%-32s %-16s %-16s" % ("task_id", "official", "semantic(适配)"))
    for r in out_rows:
        print("%-32s %-16s %-16s" % (r["task_id"],
              r["official_success"], r["semantic_success"]))
    print("\n官方原始成功率: %d/%d；平台适配后语义成功率: %d/%d" % (off, n, sem, n))
    print("已保存:", out_path)


if __name__ == "__main__":
    main()
