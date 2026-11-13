# GenericAgent Reproduction — FTEC5660 Reproducibility Work

This repository is a **reproducibility study** of the open-source agent framework
**GenericAgent** (*A Token-Efficient Self-Evolving LLM Agent via Contextual Information
Density Maximization*). We run a subset of its `tool_efficiency_benchmark` on a local
Windows machine with the **DeepSeek API**, and apply **one isolated, measurable
modification**: changing the sampling temperature from `1.0` to `0.0`.

- Upstream framework: <https://github.com/lsdefine/GenericAgent> — this repo is a **fork**,
  pinned at upstream `main` HEAD `68d996a4` (2026-11-06).
- Benchmark / technical report source: <https://github.com/JinyiHan99/GA-Technical-Report>,
  version `feb354a5` (2026-06-15).
- Submission package for the course consists of three items: a ≤10-page brief report,
  this GitHub link, and a ≤15-minute recorded Zoom presentation.

> **Controlled-variable declaration (important).** The original report uses
> Claude Sonnet 4.6, while this study switches to the publicly accessible
> `deepseek-v4-pro` (DeepSeek V4 Pro, OpenAI-compatible interface). Model and
> decoding parameters are controlled variables, so the success rates obtained
> here **cannot be directly compared with the numbers reported in the paper**.
> They are used to reproduce, under one fixed setup, the behaviour "can the task
> be completed correctly", and to support an internal baseline-vs-modification
> comparison.

---

## 1. What is upstream and what is mine

This repository is a fork, so the **upstream framework lives directly at the
repository root** (`agentmain.py`, `llmcore.py`, `ga.py`, `memory/`, `plugins/`,
`docs/`, `frontends/`, …). There is **no `GenericAgent/` subdirectory** — do not
upload one.

| Part | Origin | Status |
|---|---|---|
| Root-level framework files (`agentmain.py`, `llmcore.py`, `ga.py`, …) | `lsdefine/GenericAgent` @ `68d996a4` | Logic unchanged. DeepSeek support in `llmcore.py` is an upstream-native capability. |
| `benchmark/tool_efficiency_benchmark/` | `JinyiHan99/GA-Technical-Report` @ `feb354a5` | Copied verbatim; the 16 official graders are never modified. |
| `scripts/` | Mine | Reproduction driver, grader invocation, summarisation, diagnostics, report generation. |
| `experiments/run_experiment.ps1` | Mine | One-command runner; the studied modification is a single default value here. |
| `results/` | Mine | Measured outputs: baseline and temp0, 5 tasks × 5 trials each. |
| Root `README.md`, `.gitignore` | Mine | Replaced README; .gitignore extended with an appended block (upstream rules preserved). |

Only two upstream-derived assumptions were adapted for the fork layout, in
`scripts/run_single.py` and `scripts/check_model.py`: the framework path constant
changed from a `GenericAgent/` subdirectory to the repository root. **No
experimental logic was changed.** The modification studied in this report is a
runtime parameter change (sampling temperature), not a code edit to the framework.

---

## 2. Repository layout

```
<repo-root>/                       # fork of lsdefine/GenericAgent; root = upstream framework
├─ agentmain.py, llmcore.py, ga.py, agent_loop.py, pyproject.toml, ...
├─ memory/, plugins/, reflect/, frontends/, docs/, assets/   # upstream framework dirs
├─ mykey_template.py              # upstream template; copy to mykey.py locally
├─ benchmark/
│  └─ tool_efficiency_benchmark/
│     ├─ tool_efficiency_tasks.jsonl   # 16 task definitions
│     ├─ graders/                      # 16 official auto-graders
│     └─ assets/                       # input files per task_id
├─ scripts/
│  ├─ run_benchmark.py        # batch runner + official grader + summary
│  ├─ run_single.py           # single-task driver (isolated workspace + monkeypatch)
│  ├─ grade_windows.py        # grader invocation helper
│  ├─ analyze_stability.py    # mean / variance across trials
│  ├─ inspect_assets.py       # inspect reference answers of input assets
│  ├─ check_model.py          # check model config / import
│  ├─ diagnose_platform.py    # platform diagnostics
│  └─ build_report.py         # generate the brief report (.docx)
├─ experiments/
│  └─ run_experiment.ps1      # one-command runner; the modification lives here
├─ results/
│  ├─ baseline/               # temperature 1.0, 5 tasks × 5 trials
│  ├─ temp0/                  # temperature 0.0, 5 tasks × 5 trials
│  └─ stability_analysis.json # per-task mean / variance comparison
├─ workspaces/                # isolated per-task execution dir (gitignored)
├─ .venv/                     # virtual environment (gitignored)
├─ deepseek_key.txt           # local key file (gitignored, never committed)
└─ .gitignore                 # upstream rules + appended reproduction rules
```

---

## 3. Environment

- Windows + Python `>=3.10,<3.14` (this project used Python 3.13)
- A DeepSeek API key (OpenAI-compatible endpoint)
- No Docker / conda / separate upstream checkout required — `git clone` this repo is enough

Main dependencies: `requests`, `beautifulsoup4`, `bottle`, `simple-websocket-server`,
`aiohttp`, `pandas`, `openpyxl`, `nbformat`, `numpy`.

---

## 4. Installation & configuration

Run all commands from the **repository root**.

```powershell
# 1) Create and activate the virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install requests beautifulsoup4 bottle simple-websocket-server aiohttp pandas openpyxl nbformat numpy

# 3) Create the local model config from the upstream template
#    mykey.py is gitignored but required at runtime:
Copy-Item mykey_template.py mykey.py

# 4) Configure the DeepSeek key
#    Create deepseek_key.txt locally with one line:
#    DEEPSEEK_API_KEY=sk-your-real-key
#    (The environment variable DEEPSEEK_API_KEY takes higher priority.)
```

`deepseek_key.txt`, `mykey.py`, `.env`, `.venv/`, `workspaces/` and `temp/`
are all ignored by `.gitignore` and are not part of this repository.

---

## 5. Running the experiments

### 5.1 Baseline (temperature = 1.0)

```powershell
powershell -ExecutionPolicy Bypass -File .\experiments\run_experiment.ps1 `
  -Label baseline -Temperature 1.0 -Repeats 5
```

### 5.2 Modification (temperature = 0.0)

```powershell
powershell -ExecutionPolicy Bypass -File .\experiments\run_experiment.ps1 `
  -Label temp0 -Repeats 5
```

No `-Temperature` argument is needed for temp0: after the modification commit the
script's default is `0.0`. Every other condition — tasks, repeats, grader, model,
prompts, decoding settings — is held fixed.

Equivalent low-level commands:

```powershell
.venv\Scripts\python.exe scripts\run_benchmark.py --label baseline `
  --tasks teb_01,teb_02,teb_06,teb_07,teb_08 --repeats 5 --temperature 1.0

.venv\Scripts\python.exe scripts\run_benchmark.py --label temp0 `
  --tasks teb_01,teb_02,teb_06,teb_07,teb_08 --repeats 5 --temperature 0.0
```

Other helpers:

```powershell
.venv\Scripts\python.exe scripts\inspect_assets.py      # view reference answers
.venv\Scripts\python.exe scripts\analyze_stability.py   # rebuild stability_analysis.json
```

The committed `results/` already contains **5 tasks × 5 trials × 2 conditions = 50
runs**, so mean and variance can be reported without re-running anything.

---

## 6. The modification (isolated, measurable)

| | baseline | modification |
|---|---|---|
| sampling temperature | `1.0` | **`0.0`** |
| tasks | `teb_01, teb_02, teb_06, teb_07, teb_08` | identical |
| repeats | 5 | identical |
| grader | official, unmodified | identical |
| model / prompts | `deepseek-v4-pro`, unchanged | identical |

The change appears in commit
`feat(modification): sampling temperature 1.0 -> 0.0 (isolated change)` as a
**one-line diff** in `experiments/run_experiment.ps1`. It is a parameter change
permitted by the assignment; the upstream framework code is not modified.

Because the underlying LLM differs from the paper, this is an internal
before/after comparison only — see the controlled-variable declaration above.

---

## 7. Scoring method

After each run, `scripts/run_benchmark.py` invokes the corresponding **official
grader**:

```
python <grader>.py --workspace <workspace> --response-file <response>
```

The grader emits one line of JSON containing `task_success` (boolean). Some tasks
(`teb_01/02/06`) use `rglob` to inspect **real files** in the workspace, so input
assets are fully copied into each isolated workspace first. Aggregated results
are written to `results/<label>/summary.json` and `summary.csv`, including success
rate, elapsed time, and token usage. `results/<label>/grade_windows.json` holds
the grader invocation records. The graders themselves are never edited.

---

## 8. Reproduced tasks (5 offline deterministic tasks)

| Task | Capability tested | Type |
|---|---|---|
| teb_01_glob_markdown_list | List all `.md` files (Glob) | Read-only |
| teb_02_grep_todo_hits | Find all `TODO` hits (Grep) | Read-only |
| teb_06_notebook_inspect | Insert a code cell into a Jupyter notebook | File modification |
| teb_07_csv_stats | CSV row count / header / numeric statistics | Read-only |
| teb_08_xlsx_budget_extract | Excel worksheet and amount reading | Read-only |

`teb_03/05`, which depend on live webpages, and the long-horizon complex tasks
`teb_12–16` are deliberately excluded to keep the results deterministic and
reproducible within a limited time and compute budget.

---

## 9. Results layout

```
results/
├─ baseline/<task_id>/r1..r5/{prompt.txt, response.txt, stats.json}
├─ temp0/<task_id>/r1..r5/{prompt.txt, response.txt, stats.json}
├─ baseline/{summary.json, summary.csv, grade_windows.json}
├─ temp0/{summary.json, summary.csv, grade_windows.json}
└─ stability_analysis.json     # mean / variance per task and per condition
```

Start with `results/stability_analysis.json` for the aggregate comparison, then
the two `summary.csv` files for per-task numbers.

---

## 10. Security notes

- The key exists only in the local `deepseek_key.txt` (or the
  `DEEPSEEK_API_KEY` environment variable). That file and `mykey.py` are ignored
  and never committed.
- Each task runs in an independent subprocess with an isolated workspace; the
  agent does not modify upstream code and does not access files outside the
  project directory.
- Runtime artifacts (`workspaces/`, `temp/`, `.venv/`) are excluded from git.

---

## 11. Commit map (for reviewers)

This fork is a small number of reviewable commits on top of upstream `main`;
there is no bulk vendor dump:

| # | Commit | Content |
|---|---|---|
| 1 | `docs: replace upstream README with FTEC5660 reproduction guide` | this file |
| 2 | `chore: ignore local secrets, venv and run artifacts` | appended `.gitignore` block |
| 3 | `data: import official tool_efficiency_benchmark @ feb354a5` | `benchmark/` |
| 4 | `feat: add reproduction driver and grading scripts` | `scripts/` |
| 5 | `docs: describe results layout` | `results/README.md` |
| 6 | `results: baseline measurements (5 tasks x 5 trials)` | `results/baseline/` |
| 7 | `results: temp0 measurements (5 tasks x 5 trials)` | `results/temp0/` |
| 8 | `feat: add one-command baseline runner (temperature=1.0)` | `experiments/` |
| 9 | `feat(modification): sampling temperature 1.0 -> 0.0` | **one line** |

---

# GenericAgent 复现项目（FTEC5660 Reproducibility Work）

本项目对开源智能体框架 **GenericAgent**（*A Token-Efficient Self-Evolving LLM
Agent via Contextual Information Density Maximization*）进行可复现性实验：在
本地 Windows 上使用 **DeepSeek API** 复现其 `tool_efficiency_benchmark` 中若干
**离线确定性任务**的成功率，并完成一个**隔离、可量化的小改动**（采样温度
temperature 由 `1.0` 改为 `0.0`）。

- 上游框架：<https://github.com/lsdefine/GenericAgent> —— 本仓库为 **fork**，
  固定在上游 `main` HEAD `68d996a4`（2026-11-06）。
- Benchmark / 技术报告来源：<https://github.com/JinyiHan99/GA-Technical-Report>，
  版本 `feb354a5`（2026-06-15）。
- 作业提交共三项：≤10 页 brief report、本 GitHub 链接、≤15 分钟 Zoom 录屏。

> **受控变量声明（重要）**：原论文使用 Claude Sonnet 4.6，本项目改用公开可访问的
> `deepseek-v4-pro`（DeepSeek V4 Pro，OpenAI 兼容接口）。模型与解码参数均为受控变量，
> 因此本项目得到的成功率**不能与论文数值直接比较**，仅用于在同一设置下复现
> 「任务能否被正确完成」这一行为，并做 baseline 与 modification 的内部对照。

---

## 1. 哪些来自上游 / 哪些是本项目的

本仓库是 fork，因此**上游框架代码直接位于仓库根目录**（`agentmain.py`、
`llmcore.py`、`ga.py`、`memory/`、`plugins/` 等），**没有 `GenericAgent/` 子目录**，
也不需要另外下载一份。

| 部分 | 来源 | 状态 |
|---|---|---|
| 根目录框架文件 | `lsdefine/GenericAgent` @ `68d996a4` | 逻辑未改动；`llmcore.py` 的 DeepSeek 支持为上游原生能力 |
| `benchmark/tool_efficiency_benchmark/` | `JinyiHan99/GA-Technical-Report` @ `feb354a5` | 原样复制，16 个官方 grader 从不修改 |
| `scripts/` | 本项目新增 | 复现驱动、grader 调用、汇总、诊断、报告生成 |
| `experiments/run_experiment.ps1` | 本项目新增 | 一键运行脚本；研究的改动就是此处的一个默认值 |
| `results/` | 本项目新增 | 实测输出：baseline 与 temp0，各 5 任务 × 5 次重复 |
| 根目录 `README.md`、`.gitignore` | 本项目 | 替换 README；`.gitignore` 以追加方式扩展（保留上游原有规则） |

仅 `scripts/run_single.py` 与 `scripts/check_model.py` 中的框架路径常量由
`GenericAgent/` 子目录改为仓库根目录，以适配 fork 的目录结构，**实验逻辑未改**。
本报告研究的「修改」是运行时参数改动（采样温度），并非对上游框架的代码修改。

---

## 2. 目录结构

```
<仓库根目录>/                  # fork 自 lsdefine/GenericAgent，根目录即上游框架
├─ agentmain.py, llmcore.py, ga.py, agent_loop.py, pyproject.toml, ...
├─ memory/, plugins/, reflect/, frontends/, docs/, assets/   # 上游框架目录
├─ mykey_template.py          # 上游模板；本地复制为 mykey.py
├─ benchmark/
│  └─ tool_efficiency_benchmark/
│     ├─ tool_efficiency_tasks.jsonl   # 16 个任务定义
│     ├─ graders/                      # 16 个官方自动评分器
│     └─ assets/                       # 各任务输入文件（按 task_id 分目录）
├─ scripts/
│  ├─ run_benchmark.py        # 批量运行 + 调用官方 grader + 汇总
│  ├─ run_single.py           # 单任务驱动（隔离 workspace + monkeypatch）
│  ├─ grade_windows.py        # grader 调用辅助
│  ├─ analyze_stability.py    # 多次重复的均值 / 方差
│  ├─ inspect_assets.py       # 查看输入数据的正确答案参考
│  ├─ check_model.py          # 检查模型配置 / import
│  ├─ diagnose_platform.py    # 平台诊断
│  └─ build_report.py         # 生成 brief report（.docx）
├─ experiments/
│  └─ run_experiment.ps1      # 一键运行；改动就在这里
├─ results/
│  ├─ baseline/               # temperature 1.0，5 任务 × 5 次
│  ├─ temp0/                  # temperature 0.0，5 任务 × 5 次
│  └─ stability_analysis.json # 各任务均值 / 方差对比
├─ workspaces/                # 每任务隔离执行目录（gitignore）
├─ .venv/                     # 虚拟环境（gitignore）
├─ deepseek_key.txt           # 本地密钥（gitignore，不提交）
└─ .gitignore                 # 上游规则 + 追加的复现规则
```

---

## 3. 环境要求

- Windows + Python `>=3.10,<3.14`（本项目使用 Python 3.13）
- DeepSeek API key（OpenAI 兼容接口）
- 无需 Docker / conda，也无需另外下载上游框架：`git clone` 本仓库即可

主要依赖：`requests`、`beautifulsoup4`、`bottle`、`simple-websocket-server`、
`aiohttp`、`pandas`、`openpyxl`、`nbformat`、`numpy`。

---

## 4. 安装与配置

以下命令均在**仓库根目录**执行。

```powershell
# 1) 创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2) 安装依赖
pip install requests beautifulsoup4 bottle simple-websocket-server aiohttp pandas openpyxl nbformat numpy

# 3) 从上游模板生成本地模型配置（mykey.py 被 gitignore，但运行时必需）
Copy-Item mykey_template.py mykey.py

# 4) 配置 DeepSeek 密钥
#    在本地新建 deepseek_key.txt，内容为一行：
#    DEEPSEEK_API_KEY=sk-你的真实key
#    （也可使用环境变量 DEEPSEEK_API_KEY，优先级更高）
```

`deepseek_key.txt`、`mykey.py`、`.env`、`.venv/`、`workspaces/`、`temp/`
均已被 `.gitignore` 忽略，不在版本库中。

---

## 5. 运行实验

### 5.1 基线（temperature = 1.0）

```powershell
powershell -ExecutionPolicy Bypass -File .\experiments\run_experiment.ps1 `
  -Label baseline -Temperature 1.0 -Repeats 5
```

### 5.2 小改动（temperature = 0.0）

```powershell
powershell -ExecutionPolicy Bypass -File .\experiments\run_experiment.ps1 `
  -Label temp0 -Repeats 5
```

temp0 不需要传 `-Temperature`：改动 commit 之后脚本默认值即为 `0.0`。
其余条件（任务、重复次数、grader、模型、prompt、解码参数）完全一致。

等价的底层命令：

```powershell
.venv\Scripts\python.exe scripts\run_benchmark.py --label baseline `
  --tasks teb_01,teb_02,teb_06,teb_07,teb_08 --repeats 5 --temperature 1.0

.venv\Scripts\python.exe scripts\run_benchmark.py --label temp0 `
  --tasks teb_01,teb_02,teb_06,teb_07,teb_08 --repeats 5 --temperature 0.0
```

其他辅助脚本：

```powershell
.venv\Scripts\python.exe scripts\inspect_assets.py      # 查看输入数据的正确答案参考
.venv\Scripts\python.exe scripts\analyze_stability.py   # 重新生成 stability_analysis.json
```

已提交的 `results/` 内含 **5 任务 × 5 次 × 2 组 = 50 次运行**，
无需重跑即可报告均值与方差。

---

## 6. 本作业研究的唯一改动（隔离、可量化）

| | baseline | modification |
|---|---|---|
| 采样温度 temperature | `1.0` | **`0.0`** |
| 任务 | `teb_01, teb_02, teb_06, teb_07, teb_08` | 完全相同 |
| 重复次数 | 5 | 完全相同 |
| grader | 官方，未修改 | 完全相同 |
| 模型 / prompt | `deepseek-v4-pro`，未改动 | 完全相同 |

改动位于 commit
`feat(modification): sampling temperature 1.0 -> 0.0 (isolated change)`，
diff 仅为 `experiments/run_experiment.ps1` 的**一行默认值**。这是作业允许的
参数改动，未修改上游框架代码。由于底层 LLM 与论文不同，此对照仅在同一设置下成立，
见前文受控变量声明。

---

## 7. 评分方式

每次运行后，`scripts/run_benchmark.py` 自动调用对应的**官方 grader**：

```
python <grader>.py --workspace <workspace> --response-file <response>
```

grader 输出一行 JSON，其中 `task_success` 为布尔值。部分任务（`teb_01/02/06`）会用
`rglob` 核对 workspace 中的**真实文件**，因此输入资产会先完整复制进每个隔离
workspace。汇总结果写入 `results/<label>/summary.json` 与 `summary.csv`，
包含成功率、耗时与 token 用量；`results/<label>/grade_windows.json` 记录 grader
调用过程。grader 本身从不修改。

---

## 8. 复现的任务（5 个离线确定性任务）

| 任务 | 考察能力 | 类型 |
|---|---|---|
| teb_01_glob_markdown_list | 列举全部 `.md` 文件（Glob） | 只读 |
| teb_02_grep_todo_hits | 检索全部 `TODO` 命中（Grep） | 只读 |
| teb_06_notebook_inspect | 在 Jupyter notebook 插入 code 单元 | 文件修改 |
| teb_07_csv_stats | CSV 行数 / 表头 / 数值统计 | 只读 |
| teb_08_xlsx_budget_extract | Excel 工作表与金额读取 | 只读 |

刻意排除依赖实时网页的 `teb_03/05` 与长程复杂任务 `teb_12–16`，以保证结果确定、
可在有限时间与预算内复现。

---

## 9. 结果文件

```
results/
├─ baseline/<task_id>/r1..r5/{prompt.txt, response.txt, stats.json}
├─ temp0/<task_id>/r1..r5/{prompt.txt, response.txt, stats.json}
├─ baseline/{summary.json, summary.csv, grade_windows.json}
├─ temp0/{summary.json, summary.csv, grade_windows.json}
└─ stability_analysis.json     # 各任务、各条件的均值 / 方差
```

建议先看 `results/stability_analysis.json` 的汇总对比，再看两个 `summary.csv`
的逐任务数字。

---

## 10. 安全说明

- 密钥仅存在于本地 `deepseek_key.txt`（或环境变量 `DEEPSEEK_API_KEY`），
  该文件与 `mykey.py` 均被忽略，不会提交。
- 智能体在每个任务的独立子进程、独立 workspace 中运行，不改动上游代码，
  也不访问项目目录之外的文件。
- 运行产物（`workspaces/`、`temp/`、`.venv/`）不进入版本库。

---

## 11. Commit 结构（供评分人查阅）

本 fork 在上游 `main` 之上只有少量可审阅的小 commit，没有整包 vendor dump：

| # | Commit | 内容 |
|---|---|---|
| 1 | `docs: replace upstream README with FTEC5660 reproduction guide` | 本文件 |
| 2 | `chore: ignore local secrets, venv and run artifacts` | 追加的 `.gitignore` 规则 |
| 3 | `data: import official tool_efficiency_benchmark @ feb354a5` | `benchmark/` |
| 4 | `feat: add reproduction driver and grading scripts` | `scripts/` |
| 5 | `docs: describe results layout` | `results/README.md` |
| 6 | `results: baseline measurements (5 tasks x 5 trials)` | `results/baseline/` |
| 7 | `results: temp0 measurements (5 tasks x 5 trials)` | `results/temp0/` |
| 8 | `feat: add one-command baseline runner (temperature=1.0)` | `experiments/` |
| 9 | `feat(modification): sampling temperature 1.0 -> 0.0` | **仅一行** |
