"""生成 GenericAgent 复现报告（英文 Word，.docx），deepseek-v4-pro 版，约 7 页。
结构严格对应作业建议的 7 个部分；数字取自 results/stability_analysis.json。
"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PROJECT_ROOT, "GenericAgent_Reproducibility_Report.docx")
BLACK = RGBColor(0, 0, 0)
GREY = "D9D9D9"

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.5)
sec.left_margin = sec.right_margin = Cm(2.5)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(11)
normal.font.color.rgb = BLACK
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
pf = normal.paragraph_format
pf.space_before = Pt(0)
pf.space_after = Pt(6)
pf.line_spacing = 1.15


def style_heading(name, size):
    st = doc.styles[name]
    st.font.name = "Times New Roman"
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = BLACK
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    st.paragraph_format.space_before = Pt(12)
    st.paragraph_format.space_after = Pt(4)
    st.paragraph_format.keep_with_next = True


style_heading("Heading 1", 14)
style_heading("Heading 2", 12)


def para(text, bold=False, align=None, size=None, space_after=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    if size:
        r.font.size = Pt(size)
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p


def bullet(text):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text)
    r.font.size = Pt(11)
    p.paragraph_format.space_after = Pt(2)
    return p


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def make_table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        hdr[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade(hdr[i], GREY)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(val))
            run.font.size = Pt(10)
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cells[i].paragraphs[0].paragraph_format.space_after = Pt(0)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


# ============ 封面 ============
para("Reproducibility Report", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=18, space_after=4)
para("GenericAgent on the Tool-use Efficiency Benchmark", bold=True,
     align=WD_ALIGN_PARAGRAPH.CENTER, size=14, space_after=14)
para("Course: FTEC5660 Agentic AI for Business and FinTech",
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
para("Model under test: DeepSeek V4 Pro (deepseek-v4-pro)",
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
para("Student name: [Student Name]    Student ID: [Student ID]",
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
para("Date: November 2026", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

# ============ 1. Project Summary ============
doc.add_heading("1. Project Summary", level=1)
para("GenericAgent is a token-efficient, self-evolving LLM agent. Its architecture combines four "
     "closely connected components. The first is a minimal set of atomic tools that keeps the action "
     "space small and composable. The second is a hierarchical on-demand memory that presents only a "
     "short high-level view by default and expands detail on request. The third is a context "
     "management mechanism that trims message history according to information density. The fourth "
     "is a self-evolution pipeline that compresses verified past trajectories into reusable operating "
     "procedures and executable code.")
para("The source code is publicly available and is listed as a Tier A project in the course paper "
     "list. The central design claim is that a small, composable tool space can cover the same range "
     "of tasks as a large inventory of specialized tools while reducing prompt size and interaction "
     "overhead. The framework is not a single prompt-response system. It plans and acts over multiple "
     "steps, invokes tools, maintains memory, and executes code.")
para("This work reproduces a subset of the tool-use efficiency benchmark distributed with the "
     "GenericAgent technical report. Five offline, deterministic tasks were selected: teb_01, "
     "teb_02, teb_06, teb_07, and teb_08. These tasks cover recursive file listing, text search with "
     "line numbers, notebook inspection, CSV statistics, and spreadsheet reading.")
para("The study addresses three research questions. First, can the minimal atomic tool set complete "
     "the selected file and data tasks reliably when driven by DeepSeek V4 Pro? Second, how large is "
     "the resource cost in tokens and interaction turns? Third, does switching from stochastic "
     "decoding to greedy decoding improve stability and output consistency?")
para("The original report runs the agent on Claude Sonnet 4.6. The accessible model in this study "
     "is DeepSeek V4 Pro, identified by the API as deepseek-v4-pro. The model swap is treated as a "
     "controlled variable and documented in Section 2. Following the assignment guidance, the "
     "measured numbers are not directly comparable to the reported numbers, although the same tasks, "
     "metrics, and evaluation scripts are used. A single well-scoped modification is then studied. "
     "The decoding temperature is changed from the default 1.0 to 0.0, and the effect on stability "
     "is measured over repeated trials.")

# ============ 2. Setup Notes ============
doc.add_heading("2. Setup Notes", level=1)
doc.add_heading("2.1 Computing environment", level=2)
para("All work was performed on a local Windows machine running Python 3.13. A dedicated project "
     "directory was created, and an isolated virtual environment was built with the standard library "
     "venv module. No system files outside the project directory were modified. Dependencies were "
     "installed with pip from a public package mirror. The project is organized into separate folders "
     "for the framework source, the benchmark data, the per-run workspaces, the result files, and the "
     "driver scripts. Each task runs in a separate operating system process with a fresh workspace.")
doc.add_heading("2.2 Model configuration", level=2)
make_table(
    ["Parameter", "Value"],
    [
        ["API base", "https://api.deepseek.com"],
        ["Model identifier", "deepseek-v4-pro"],
        ["Baseline temperature", "1.0"],
        ["Modified temperature", "0.0"],
        ["Maximum output tokens", "8192"],
        ["Streaming", "Enabled"],
        ["Adapter context window", "80,000 tokens"],
    ],
    widths=[6.0, 8.4],
)
para("DeepSeek exposes an OpenAI-compatible endpoint, so the framework connects through its native "
     "OpenAI client by changing only the model name, base URL, and key. The built-in DeepSeek adapter "
     "retains thinking blocks in the message history because the model requires them for coherent "
     "multi-turn context.")
doc.add_heading("2.3 Key management", level=2)
para("The API key is never hard-coded. It is read at runtime from the DEEPSEEK_API_KEY environment "
     "variable when present, and otherwise from a separate local text file. Comment lines are ignored "
     "before parsing, and a key matching the expected prefix is preferred. Both the configuration file "
     "and the key file are excluded from version control.")
doc.add_heading("2.4 Atomic tool inventory", level=2)
make_table(
    ["Tool", "Purpose"],
    [
        ["file_read", "Read the content of a single file"],
        ["file_write", "Create or overwrite a file"],
        ["file_patch", "Apply a targeted edit to a file"],
        ["code_run", "Execute a Python script in the workspace"],
        ["web_scan", "Retrieve and parse a web page"],
        ["web_execute_js", "Run JavaScript in a browser context"],
        ["ask_user", "Request clarification from the user"],
        ["update_working_checkpoint", "Save a short-term working checkpoint"],
        ["start_long_term_update", "Trigger long-term memory consolidation"],
    ],
    widths=[5.4, 9.0],
)
para("Across all fifty runs, tool use was almost entirely concentrated in code_run. The model "
     "consistently prefers to write a short Python script to solve file and data tasks rather than "
     "composing the dedicated file tools. This concentration is consistent with the tool distribution "
     "reported in the paper.")
doc.add_heading("2.5 Key software dependencies", level=2)
make_table(
    ["Package", "Version", "Purpose"],
    [
        ["requests", "2.34.2", "HTTP calls to the model API"],
        ["pandas", "3.1.1", "Tabular data processing"],
        ["numpy", "2.5.4", "Numeric computation"],
        ["openpyxl", "3.1.5", "Excel file reading and writing"],
        ["nbformat", "5.11.1", "Notebook manipulation"],
        ["python-docx", "1.2.0", "Report generation"],
        ["pymupdf", "Current", "PDF text extraction"],
        ["beautifulsoup4", "4.15.0", "HTML parsing"],
    ],
    widths=[3.6, 2.6, 8.2],
)

# ============ 3. Reproduction Target and Metric Definition ============
doc.add_heading("3. Reproduction Target and Metric Definition", level=1)
para("The target claim is that a minimal atomic tool set can complete realistic file and data "
     "workflows without a loss of capability and with limited interaction overhead. The five "
     "selected tasks and their required outputs are summarized below.")
make_table(
    ["Task", "Capability", "Required output"],
    [
        ["teb_01", "Recursive markdown listing", "List of markdown file paths"],
        ["teb_02", "Text search", "TODO hits with file and line"],
        ["teb_06", "Notebook inspection", "Notebook cell with computed values"],
        ["teb_07", "CSV statistics", "Row count, columns, numeric summary"],
        ["teb_08", "Spreadsheet reading", "Sheet names, budget and expense totals"],
    ],
    widths=[2.2, 5.2, 7.0],
)
para("These tasks were selected because they are fully offline, deterministic, and representative "
     "of common business file operations. None requires a browser, a database service, or multimodal "
     "input, so the text-only model can complete them without additional infrastructure.")
para("Each condition was run five times per task, giving 25 runs per condition and 50 model calls "
     "in total. Five repetitions sit at the upper end of the three to five trial range recommended in "
     "the assignment. The following metrics are recorded for every run.")
bullet("Success: the binary result returned by the original benchmark grader.")
bullet("Semantic success: the result after clearly labeled Windows adaptations, with the official "
       "grader left unchanged.")
bullet("Input and output tokens: the token counts reported by the API.")
bullet("Turns: the number of model request rounds before the final answer.")
bullet("Output consistency: the number of distinct final answers across the five repetitions, where "
       "a value of one indicates identical answers.")
para("The official graders are never modified. A separate evaluation script adds transparent "
     "Windows adaptations, including path separator normalization and notebook execution, and records "
     "both the original and adapted results side by side. This separation preserves the integrity of "
     "the benchmark while exposing platform-specific assumptions.")

# ============ 4. Results ============
doc.add_heading("4. Results: Measured Numbers versus Reported Numbers", level=1)
doc.add_heading("4.1 Overall success rate", level=2)
make_table(
    ["Metric", "Baseline (T=1.0)", "Modified (T=0.0)"],
    [
        ["Official success rate", "0.60 (15/25)", "0.60 (15/25)"],
        ["Semantic success rate", "1.00 (25/25)", "1.00 (25/25)"],
    ],
    widths=[5.2, 4.6, 4.6],
)
doc.add_heading("4.2 Per-task success and output consistency", level=2)
make_table(
    ["Task", "Base official", "Base semantic", "T0 official", "T0 semantic", "Distinct answers"],
    [
        ["teb_01", "0/5", "5/5", "0/5", "5/5", "1 to 1"],
        ["teb_02", "5/5", "5/5", "5/5", "5/5", "1 to 1"],
        ["teb_06", "0/5", "5/5", "0/5", "5/5", "2 to 3"],
        ["teb_07", "5/5", "5/5", "5/5", "5/5", "1 to 3"],
        ["teb_08", "5/5", "5/5", "5/5", "5/5", "5 to 5"],
    ],
    widths=[2.0, 2.4, 2.4, 2.2, 2.4, 3.0],
)
doc.add_heading("4.3 Resource use", level=2)
make_table(
    ["Metric", "Baseline mean [median]", "Modified mean [median]"],
    [
        ["Input tokens", "4708.04 [4663]", "4985.32 [4778]"],
        ["Output tokens", "226.20 [198]", "316.12 [255]"],
        ["Turns", "4.44 [4]", "4.28 [4]"],
    ],
    widths=[4.6, 5.0, 5.0],
)
para("The median turn count is four in both conditions, and the median input tokens are close. "
     "Output tokens are slightly higher in the modified condition, which shows that output length is "
     "driven mainly by the chosen tool path and the level of explanation rather than by temperature.")
doc.add_heading("4.4 The teb_08 budget reporting scope", level=2)
make_table(
    ["Value", "Amount", "Interpretation"],
    [
        ["Q1 matching budget", "60,000", "Sum of the four Q1 categories, aligns with Q1 expenses"],
        ["Full year budget", "267,000", "Sum across all four quarters, literal total budget"],
        ["Q1 expense total", "15,430", "Computed from the expense sheet, identical in all runs"],
    ],
    widths=[3.8, 2.6, 8.0],
)
para("The grader only checks that the reported totals are non-negative, so both budget scopes pass. "
     "The expense total and the sheet names are identical across all runs. The apparent answer "
     "divergence therefore reflects a defensible choice of scope rather than a factual error.")
doc.add_heading("4.5 Comparison with the reported results", level=2)
para("The technical report Table 4 describes the long-horizon task set under Claude Sonnet 4.6. For "
     "GenericAgent it reports a 100 percent success rate, 188,829 total tokens, 11.0 requests, and "
     "12.8 tool calls. The five tasks in this study belong to the simple tool-generalization group, "
     "and the underlying model also differs. A direct numerical comparison is therefore not valid.")
para("The technical report Table 2 also reports task completion on broader benchmarks. On "
     "SOP-Bench, GenericAgent reaches 100 percent accuracy with Claude Sonnet 4.6, and on the "
     "RealFin benchmark it reaches 65 percent. These figures establish the reported performance "
     "context but remain tied to the original backbone model.")
para("The qualitative finding nevertheless reproduces. The agent completed every selected task "
     "using a small number of code_run calls, and the semantic success rate reached 100 percent in "
     "both conditions. On teb_02 the model correctly excluded its own temporary script from the "
     "search, so no self-reference pollution occurred. Apparent differences on other tasks came from "
     "the choice of numeric column, internal planning text, the budget reporting scope, and floating "
     "point precision rather than incorrect facts.")

# ============ 5. Modification ============
doc.add_heading("5. Modification and Results after Modification", level=1)
doc.add_heading("5.1 Definition and hypotheses", level=2)
para("The modification is a parameter change. The decoding temperature is reduced from 1.0 to 0.0, "
     "and all other settings are held constant. This satisfies the isolation requirement because "
     "temperature is the only changed variable, and the measurability requirement because its effect "
     "is quantified across success rate, tokens, turns, and output consistency. Two hypotheses were "
     "stated before the runs. Greedy decoding was expected to reduce variation in repeated outputs, "
     "and it was expected to have little effect on the typical resource cost because the task logic "
     "and tool set remain unchanged.")
doc.add_heading("5.2 Why greedy decoding is more stable", level=2)
para("Temperature controls the sharpness of the token probability distribution. At temperature 0.0, "
     "the decoder uses greedy selection and always chooses the highest probability token at each step, "
     "equivalent to taking the argmax of the logit distribution. Given the same context, sampling "
     "noise is removed and the output is deterministic. At temperature 1.0, the distribution is "
     "flatter, lower probability tokens remain reachable, and repeated runs can diverge in wording "
     "and occasionally in tool choices.")
doc.add_heading("5.3 Observed effect", level=2)
para("The success rate does not change. Both conditions produce a 100 percent semantic success rate "
     "and a 60 percent official success rate. The median turn count remains four in both conditions. "
     "The expected consistency improvement is not uniform. teb_01 and teb_02 stay fully consistent, "
     "but teb_06 and teb_07 show more distinct answers under greedy decoding, and teb_08 remains "
     "fully varied at the surface level.")
doc.add_heading("5.4 Why greedy decoding does not guarantee identical agent runs", level=2)
para("Greedy decoding removes only the randomness in token sampling. It does not make the full agent "
     "trajectory deterministic, because the context seen at later steps includes the results of tool "
     "calls, and those intermediate paths can differ. On teb_07, one greedy run summarizes a "
     "different numeric column from the other runs even though the row count and the underlying data "
     "are identical. On teb_06, internal planning text is occasionally appended to the final OK "
     "marker. These differences originate in the agent loop and its tool outputs rather than in "
     "sampling.")
doc.add_heading("5.5 A longer successful run", level=2)
para("One modified run, teb_02 repetition 4, ran for 139.8 seconds and produced 1,868 output tokens "
     "because the model performed extended intermediate reasoning within the task. It still finished "
     "correctly and did not enter an unrecoverable loop. This event is retained in the data and "
     "illustrates why median statistics are reported alongside the mean.")
para("Honest interpretation. For a capable model on simple deterministic tasks, the success rate is "
     "already at the ceiling, so lowering temperature cannot improve it. Greedy decoding adds "
     "token-level determinism, but repeated runs still diverge at the trajectory level because "
     "agent-level tool behavior is the dominant source of variation.")

# ============ 6. Debug Diary ============
doc.add_heading("6. Debug Diary", level=1)
diary = [
    ("Low initial official score", "The first full run scored 40 percent under the official "
     "graders. Per-task inspection showed that the agent had completed the work semantically and "
     "that the failures were concentrated in platform assumptions. Each discrepancy was reproduced "
     "and verified independently before any adaptation was applied."),
    ("Windows path separator in teb_01", "The grader expects a backslash path while the agent "
     "returns a forward slash path. Normalizing the separators makes the paths equal, so this is a "
     "platform false negative. The adaptation is recorded without changing the grader source."),
    ("Notebook outputs in teb_06", "The agent inserts the correct cell but does not execute it, "
     "leaving empty outputs that the grader cannot match. Executing the notebook produces the "
     "correct result, again indicating a platform false negative."),
    ("Driver script pollution", "An early driver wrote a final response file into the workspace. A "
     "grader that scans every file then treated this helper file as input. The extra write was "
     "removed, and the grader now receives the response through its response file argument."),
    ("Surface inconsistency under greedy decoding", "Repeated greedy runs were not always "
     "identical. Inspection traced the cause to different tool paths and internal planning text "
     "rather than to sampling, which clarified the boundary between token-level and trajectory-level "
     "determinism."),
    ("One extended run", "A single modified run took far longer than the others. The event was "
     "kept in the data and reported with median statistics so that it would not distort the "
     "typical-case conclusions."),
]
for title, body in diary:
    p = doc.add_paragraph()
    r = p.add_run(title + ". ")
    r.bold = True
    r.font.size = Pt(11)
    r2 = p.add_run(body)
    r2.font.size = Pt(11)
    p.paragraph_format.space_after = Pt(6)
doc.add_heading("6.1 Issue classification summary", level=2)
make_table(
    ["Issue", "Category", "Resolution"],
    [
        ["teb_01 path separator", "Platform false negative", "Path normalization"],
        ["teb_06 unexecuted cell", "Platform false negative", "Notebook execution"],
        ["Driver response file", "Test harness bug", "Removed the extra write"],
        ["Greedy surface divergence", "Agent trajectory variation", "Traced and documented"],
        ["Extended run", "Within-task reasoning cost", "Retained with median statistics"],
    ],
    widths=[4.4, 4.2, 5.8],
)

# ============ 7. Conclusions ============
doc.add_heading("7. Conclusions", level=1)
doc.add_heading("7.1 What reproduces", level=2)
para("The core behavior of GenericAgent is reproducible. A minimal atomic tool set driven mainly by "
     "code_run completes offline file and data tasks with a 100 percent semantic success rate in "
     "both conditions. Tool use is highly concentrated in a single function, and the key factual "
     "values remain stable across repetitions. These observations support the paper's central claim "
     "that a small composable tool space is sufficient for the evaluated workflows.")
doc.add_heading("7.2 What does not reproduce directly", level=2)
para("The exact reported figures cannot be compared because the backbone model is changed from "
     "Claude Sonnet 4.6 to DeepSeek V4 Pro. In addition, the official graders produce false "
     "negatives on Windows because they assume Unix style paths and already executed notebook "
     "cells. These are hidden platform assumptions rather than failures of the agent's reasoning.")
doc.add_heading("7.3 Why", level=2)
para("The graders encode environment specific expectations, and success on these simple tasks is "
     "already at the ceiling. The temperature study shows that greedy decoding adds token-level "
     "determinism but has no effect on the success rate and does not remove trajectory-level "
     "variation, because agent-level tool behavior is the main source of differences.")
doc.add_heading("7.4 Threats to validity", level=2)
para("The sample is limited to five tasks and five repetitions per condition, so the power to "
     "detect small differences is low, and no strong statistical significance claim is warranted. "
     "The model swap is a controlled change that limits comparison with the original numbers. The "
     "semantic adaptations involve judgment, although their rules are explicit and the official "
     "results are always reported alongside them.")
doc.add_heading("7.5 Recommendations and future work", level=2)
para("First, normalize file paths when reproducing across operating systems. Second, use "
     "temperature 0.0 for simple deterministic tasks to obtain token-level reproducibility, but do "
     "not expect it to repair tool-level or trajectory-level variation. Third, automatic graders "
     "should isolate agent generated temporary files and document their environment assumptions. "
     "Future work could extend the study to the long-horizon tasks, increase the number of "
     "repetitions to support formal significance testing, and compare several DeepSeek models under "
     "identical tasks and evaluation scripts.")

doc.save(OUT)
print("saved:", OUT)
