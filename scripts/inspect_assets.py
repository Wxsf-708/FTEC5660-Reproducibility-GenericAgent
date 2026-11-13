"""检查 5 个离线任务的输入数据，输出"正确答案"参考，便于核对 agent 结果。

用法：python inspect_assets.py
"""
import json
import os
import sys

BENCH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "benchmark",
                 "tool_efficiency_benchmark", "assets")
)


def sep(title):
    print("\n" + "=" * 20 + " " + title + " " + "=" * 20)


# ---- teb_01: 所有 .md 文件（相对 workspace 根）----
sep("teb_01 正确答案：所有 .md 相对路径")
base = os.path.join(BENCH, "teb_01_glob_markdown_list")
md_files = []
for root, _dirs, files in os.walk(base):
    for fn in files:
        if fn.endswith(".md"):
            md_files.append(os.path.relpath(os.path.join(root, fn), base)
                            .replace("\\", "/"))
print(json.dumps({"markdown_files": sorted(md_files)}, ensure_ascii=False, indent=2))

# ---- teb_02: 所有 TODO 命中（path, line）----
sep("teb_02 正确答案：TODO 命中项")
base = os.path.join(BENCH, "teb_02_grep_todo_hits")
hits = []
for root, _dirs, files in os.walk(base):
    for fn in files:
        path = os.path.join(root, fn)
        rel = os.path.relpath(path, base).replace("\\", "/")
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, start=1):
                if "TODO" in line:
                    hits.append({"path": rel, "line": i})
hits.sort(key=lambda x: (x["path"], x["line"]))
print(json.dumps({"hits": hits}, ensure_ascii=False, indent=2))

# ---- teb_06: notebook 结构 ----
sep("teb_06 正确答案：notebook 现状与期望快照")
import nbformat
nb = nbformat.read(os.path.join(BENCH, "teb_06_notebook_inspect",
                                "analysis.ipynb"), as_version=4)
print("现有单元格数:", len(nb.cells))
for i, cell in enumerate(nb.cells):
    src = cell.source if isinstance(cell.source, str) else "".join(cell.source)
    print(f"  cell[{i}] type={cell.cell_type} source={src[:80]!r}")
print("grader 期望: 新 cell[4] 为 code，release_snapshot mean=7.25, "
      "tool_count=7, step_claim='1-2'，最终单元格数=5")

# ---- teb_07: CSV 统计 ----
sep("teb_07 正确答案：CSV 统计")
import pandas as pd
df = pd.read_csv(os.path.join(BENCH, "teb_07_csv_stats", "quarterly_sales.csv"))
print("columns:", list(df.columns))
print("row_count(不含表头):", len(df))
num = df.select_dtypes(include="number")
col = num.columns[0]
print("主要数值列:", col)
print("min/max/mean:", num[col].min(), num[col].max(), num[col].mean())

# ---- teb_08: xlsx ----
sep("teb_08 正确答案：Excel 工作表与金额")
import openpyxl
wb = openpyxl.load_workbook(os.path.join(BENCH, "teb_08_xlsx_budget_extract",
                                         "company_expenses.xlsx"), data_only=True)
print("sheet_names:", wb.sheetnames)
for ws in wb.worksheets:
    print(f"--- sheet: {ws.title} (dims {ws.dimensions}) ---")
    for row in ws.iter_rows(values_only=True):
        if any(v is not None for v in row):
            print("  ", row)
