"""单任务驱动：在指定的隔离 workspace 中运行一次 GenericAgent。

不修改原作者的任何文件，仅在运行时 monkeypatch：
  1. GenericAgentHandler 的工作目录强制为传入的 workspace；
  2. 系统提示中的 cwd 行同步改为 workspace；
  3. 可选覆盖 temperature、禁用指定工具（用于后续改动/消融实验）。

用法：
  python run_single.py --workspace <绝对路径> --prompt-file <文件> \
      --output <响应文件> --stats <统计json> [--temperature 0.0] \
      [--disable-tools ask_user,start_long_term_update] [--max-turns 40]
"""
import argparse
import json
import os
import queue
import sys
import threading


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stats", required=True)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--disable-tools", default="")
    parser.add_argument("--max-turns", type=int, default=40)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    workspace = os.path.abspath(args.workspace)
    os.makedirs(workspace, exist_ok=True)
    with open(args.prompt_file, encoding="utf-8") as f:
        prompt = f.read()

    # 让进程以 GenericAgent 代码目录为工作目录，保证 mykey/memory/相对路径正常。
    # Fork layout: the upstream framework files live at the repository root,
    # NOT in a GenericAgent/ subdirectory. Only this path constant is changed.
    ga_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(ga_dir)
    sys.path.insert(0, ga_dir)

    import agentmain
    import llmcore
    from ga import GenericAgentHandler

    # --- monkeypatch 1：handler 工作目录 ---
    class _WorkspaceHandler(GenericAgentHandler):
        def __init__(self, parent, history, _ignored_cwd=None):
            super().__init__(parent, history, cwd=workspace)

    agentmain.GenericAgentHandler = _WorkspaceHandler

    # --- monkeypatch 2：系统提示中的 cwd 行 ---
    original_get_system_prompt = agentmain.get_system_prompt
    temp_cwd_line = "cwd = %s (./)" % os.path.join(agentmain.script_dir, "temp")
    ws_cwd_line = "cwd = %s (./)" % workspace

    def _patched_get_system_prompt():
        return original_get_system_prompt().replace(temp_cwd_line, ws_cwd_line)

    agentmain.get_system_prompt = _patched_get_system_prompt

    # --- 可选：禁用工具（在 agent 读取 schema 后过滤）---
    disabled = {x.strip() for x in args.disable_tools.split(",") if x.strip()}

    original_load_tool_schema = agentmain.load_tool_schema

    def _filtered_tool_schema(suffix=""):
        original_load_tool_schema(suffix)
        if disabled:
            agentmain.TOOLS_SCHEMA = [
                t
                for t in agentmain.TOOLS_SCHEMA
                if t.get("function", {}).get("name") not in disabled
            ]

    agentmain.load_tool_schema = _filtered_tool_schema

    # --- 让 --max-turns 生效：包装 agent_runner_loop 注入 max_turns ---
    from agent_loop import agent_runner_loop as _original_runner_loop

    def _runner_with_max_turns(*a, **k):
        k.setdefault("max_turns", args.max_turns)
        return _original_runner_loop(*a, **k)

    agentmain.agent_runner_loop = _runner_with_max_turns

    # --- 初始化 agent ---
    agent = agentmain.GenericAgent()
    if args.temperature is not None:
        agent.llmclient.backend.temperature = args.temperature

    threading.Thread(target=agent.run, daemon=True).start()

    display_queue = agent.put_task(prompt)
    full_response = ""
    try:
        while True:
            item = display_queue.get(timeout=args.timeout)
            if "done" in item:
                full_response = item["done"]
                break
    except queue.Empty:
        full_response = full_response or "[ERROR] 任务超时（%s 秒）" % args.timeout
        agent.abort()

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(full_response)

    # 注意：不向 workspace 写 final_response.txt。grader 始终通过 --response-file
    # 读取响应；若在 workspace 放副本，会被用 rglob 扫描全部文件的 grader（如 teb_02）
    # 当成输入文件，引入额外命中，造成"假阴性"。

    stats = dict(llmcore.STATS)
    stats["workspace"] = workspace
    stats["model"] = agent.get_llm_name(model=True)
    with open(args.stats, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("DONE:", args.output)


if __name__ == "__main__":
    main()
