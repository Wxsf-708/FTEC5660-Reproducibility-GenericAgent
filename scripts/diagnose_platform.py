"""诊断平台相关的两个"假阴性"：
  teb_01：Windows 下 relative_to 产生反斜杠，与 agent 输出的正斜杠不同；
  teb_06：新插入的 cell 未执行（outputs 为空），手动执行后确认结果正确。
"""
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmark" / "tool_efficiency_benchmark"


def load_grader(name):
    path = BENCH / "graders" / name
    spec = importlib.util.spec_from_file_location("grader_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---- teb_01 ----
print("=" * 15, "teb_01 路径分隔符诊断", "=" * 15)
g1 = load_grader("teb_01_glob_markdown_list_grader.py")
ws1 = ROOT / "workspaces" / "baseline" / "teb_01_glob_markdown_list" / "r1"
rf1 = ROOT / "results" / "baseline" / "teb_01_glob_markdown_list" / "r1" / "response.txt"
expected = g1.expected_markdown_files(ws1)
agent = g1.extract_json_block(rf1.read_text(encoding="utf-8"))["markdown_files"]
print("grader 期望(Windows 原生):", expected)
print("agent 输出(正斜杠)       :", agent)
normalized = sorted(p.replace("\\", "/") for p in expected)
print("规范化为正斜杠后是否相等:", normalized == sorted(agent))

# ---- teb_06 ----
print("\n" + "=" * 15, "teb_06 notebook 执行诊断", "=" * 15)
nb_path = ROOT / "workspaces" / "baseline" / "teb_06_notebook_inspect" / "r1" / "analysis.ipynb"
nb = json.loads(nb_path.read_text(encoding="utf-8"))
print("单元格总数:", len(nb["cells"]), "(grader 期望 5)")
new_cell = nb["cells"][4]
print("新 cell 类型:", new_cell["cell_type"], " outputs 长度:", len(new_cell.get("outputs", [])))
print("新 cell 源码:\n" + "".join(new_cell["source"]))

# 按顺序执行所有 code cell，验证新 cell 的真实计算结果。
ns = {}
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        exec("".join(cell["source"]), ns)
print("执行全部 code cell 后 release_snapshot =", ns.get("release_snapshot"))
expected_snapshot = {"mean_value": 7.25, "tool_count": 7, "step_claim": "1-2"}
print("与 grader 期望是否一致:", ns.get("release_snapshot") == expected_snapshot)
