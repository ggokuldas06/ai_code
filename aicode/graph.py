"""LangGraph agent workflow: plan → scaffold → generate → execute → debug loop."""

import json
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from aicode.config import AICodeConfig
from aicode.llm import create_llm
from aicode.prompts import PLAN_PROMPT, SCAFFOLD_PROMPT, GENERATE_PROMPT, DEBUG_PROMPT
from aicode.shell import run_command
from aicode.filesystem import write_file, read_file, list_files, create_directory
from aicode.diff_patch import apply_patch_to_file, show_diff_summary
from aicode.state import add_command_history, add_error, add_patch
from aicode.ui import console, print_step, print_error, print_success, print_diff


class AgentState(TypedDict, total=False):
    config: dict
    workspace: str
    description: str
    plan: dict
    files: dict[str, str]
    current_step: str
    command_output: str
    errors: list[str]
    iteration: int
    max_iterations: int
    state_data: dict
    status: str


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def planner_node(state: AgentState) -> dict:
    """LLM generates a project build plan."""
    print_step("Planning", "Generating project plan...")
    config = AICodeConfig(**state["config"])
    llm = create_llm(config)

    prompt = PLAN_PROMPT.format(description=state["description"])
    response = llm.invoke(prompt)
    plan = _parse_json_response(response.content)

    print_success(f"Plan created: {len(plan.get('steps', []))} steps, {len(plan.get('folder_structure', []))} files/dirs")
    return {"plan": plan, "current_step": "scaffold", "iteration": 0}


def scaffolder_node(state: AgentState) -> dict:
    """Create folder structure from the plan."""
    print_step("Scaffolding", "Creating project structure...")
    from pathlib import Path

    workspace = Path(state["workspace"])
    plan = state["plan"]
    files = state.get("files", {})

    # Create directories
    for item in plan.get("folder_structure", []):
        if item.endswith("/"):
            create_directory(workspace, item)
        else:
            # It's a file path - ensure parent dir exists
            parent = str(Path(item).parent)
            if parent and parent != ".":
                create_directory(workspace, parent)

    # Use LLM to generate initial file stubs
    config = AICodeConfig(**state["config"])
    llm = create_llm(config)

    prompt = SCAFFOLD_PROMPT.format(plan=json.dumps(plan, indent=2))
    response = llm.invoke(prompt)
    scaffold_data = _parse_json_response(response.content)

    for file_path, content in scaffold_data.get("files", {}).items():
        write_file(workspace, file_path, content)
        files[file_path] = content

    print_success(f"Scaffolded {len(files)} files")
    return {"files": files, "current_step": "generate"}


def generator_node(state: AgentState) -> dict:
    """LLM generates full implementation for each file."""
    print_step("Generating", "Writing implementation code...")
    from pathlib import Path

    workspace = Path(state["workspace"])
    config = AICodeConfig(**state["config"])
    llm = create_llm(config)
    plan = state["plan"]
    files = state.get("files", {})

    other_files_summary = "\n".join(
        f"--- {fp} ---\n{content[:500]}" for fp, content in files.items()
    )

    for step in plan.get("steps", []):
        for file_path in step.get("files", []):
            print_step("Generating", f"  -> {file_path}")
            prompt = GENERATE_PROMPT.format(
                context=json.dumps(plan, indent=2),
                file_path=file_path,
                purpose=step.get("description", ""),
                other_files=other_files_summary,
            )
            response = llm.invoke(prompt)
            content = response.content.strip()
            # Remove markdown fences if present
            if content.startswith("```"):
                lines = content.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)

            diff = apply_patch_to_file(workspace, file_path, content)
            files[file_path] = content
            if diff:
                print_diff(file_path, show_diff_summary(diff))

    print_success(f"Generated {len(files)} files")
    return {"files": files, "current_step": "execute"}


def executor_node(state: AgentState) -> dict:
    """Run build/test commands to verify the project."""
    print_step("Executing", "Running verification commands...")
    from pathlib import Path

    workspace = Path(state["workspace"])
    plan = state["plan"]
    state_data = state.get("state_data", {})
    errors = []

    # Install dependencies first
    stack = plan.get("stack", "python")
    if stack == "python":
        # Check for requirements.txt
        req_file = workspace / "requirements.txt"
        if req_file.exists():
            print_step("Executing", "Installing Python dependencies...")
            result = run_command("pip install -r requirements.txt", cwd=workspace)
            add_command_history(state_data, result.command, result.exit_code, result.output)
            if not result.success:
                errors.append(result.output)
    elif stack == "node":
        pkg_file = workspace / "package.json"
        if pkg_file.exists():
            print_step("Executing", "Installing Node.js dependencies...")
            result = run_command("npm install", cwd=workspace)
            add_command_history(state_data, result.command, result.exit_code, result.output)
            if not result.success:
                errors.append(result.output)

    # Run test command
    test_cmd = plan.get("test_command", "")
    if test_cmd:
        print_step("Executing", f"Running: {test_cmd}")
        result = run_command(test_cmd, cwd=workspace)
        add_command_history(state_data, result.command, result.exit_code, result.output)
        if not result.success:
            errors.append(result.output)

    # Run the main command (quick check)
    run_cmd = plan.get("run_command", "")
    if run_cmd and not errors:
        print_step("Executing", f"Testing: {run_cmd}")
        # Use short timeout for run commands (they may start a server)
        result = run_command(run_cmd, cwd=workspace, timeout=10)
        add_command_history(state_data, result.command, result.exit_code, result.output)
        if not result.success and not result.timed_out:
            errors.append(result.output)

    if errors:
        print_error(f"Found {len(errors)} error(s)")
        return {
            "command_output": "\n---\n".join(errors),
            "errors": errors,
            "current_step": "debug",
            "state_data": state_data,
        }

    print_success("All commands passed!")
    return {
        "command_output": "All commands executed successfully",
        "errors": [],
        "current_step": "done",
        "state_data": state_data,
        "status": "completed",
    }


def debugger_node(state: AgentState) -> dict:
    """LLM analyzes errors and produces fixes."""
    from pathlib import Path

    iteration = state.get("iteration", 0) + 1
    max_iter = state.get("max_iterations", 5)

    print_step("Debugging", f"Analyzing errors (attempt {iteration}/{max_iter})...")

    if iteration > max_iter:
        print_error(f"Max iterations ({max_iter}) reached. Stopping.")
        return {"current_step": "done", "iteration": iteration, "status": "max_iterations_reached"}

    workspace = Path(state["workspace"])
    config = AICodeConfig(**state["config"])
    llm = create_llm(config)
    files = state.get("files", {})
    state_data = state.get("state_data", {})

    files_content = "\n".join(
        f"--- {fp} ---\n{content}" for fp, content in files.items()
    )

    previous = "\n".join(
        f"Attempt {i+1}: {e}" for i, e in enumerate(state_data.get("errors", []))
    )

    prompt = DEBUG_PROMPT.format(
        files=files_content,
        command=state_data.get("command_history", [{}])[-1].get("command", "unknown") if state_data.get("command_history") else "unknown",
        exit_code="non-zero",
        error_output=state.get("command_output", ""),
        previous_attempts=previous or "None",
    )

    response = llm.invoke(prompt)
    fix_data = _parse_json_response(response.content)

    print_step("Debugging", f"Root cause: {fix_data.get('root_cause', 'unknown')}")

    # Apply fixes
    for fix in fix_data.get("fixes", []):
        fp = fix["file"]
        new_content = fix["content"]
        diff = apply_patch_to_file(workspace, fp, new_content)
        files[fp] = new_content
        add_patch(state_data, fp, diff)
        print_diff(fp, show_diff_summary(diff))

    # Run additional commands (like pip install)
    for cmd in fix_data.get("additional_commands", []):
        print_step("Debugging", f"Running: {cmd}")
        result = run_command(cmd, cwd=workspace)
        add_command_history(state_data, result.command, result.exit_code, result.output)

    add_error(state_data, fix_data.get("root_cause", "unknown"))

    return {
        "files": files,
        "current_step": "execute",
        "iteration": iteration,
        "state_data": state_data,
    }


def route_next(state: AgentState) -> str:
    """Route to the next node based on current_step."""
    step = state.get("current_step", "done")
    if step == "scaffold":
        return "scaffolder"
    elif step == "generate":
        return "generator"
    elif step == "execute":
        return "executor"
    elif step == "debug":
        return "debugger"
    else:
        return END


def build_graph() -> StateGraph:
    """Build the LangGraph agent workflow."""
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("scaffolder", scaffolder_node)
    graph.add_node("generator", generator_node)
    graph.add_node("executor", executor_node)
    graph.add_node("debugger", debugger_node)

    graph.set_entry_point("planner")

    graph.add_conditional_edges("planner", route_next)
    graph.add_conditional_edges("scaffolder", route_next)
    graph.add_conditional_edges("generator", route_next)
    graph.add_conditional_edges("executor", route_next)
    graph.add_conditional_edges("debugger", route_next)

    return graph.compile()


def run_build_agent(
    workspace_path: str,
    description: str,
    config: AICodeConfig,
    state_data: dict | None = None,
) -> dict:
    """Run the full build agent pipeline."""
    graph = build_graph()

    initial_state: AgentState = {
        "config": {
            "openai_api_key": config.openai_api_key,
            "model_name": config.model_name,
            "max_iterations": config.max_iterations,
            "shell_timeout": config.shell_timeout,
            "workspace_root": config.workspace_root,
        },
        "workspace": workspace_path,
        "description": description,
        "plan": {},
        "files": {},
        "current_step": "plan",
        "command_output": "",
        "errors": [],
        "iteration": 0,
        "max_iterations": config.max_iterations,
        "state_data": state_data or {},
        "status": "running",
    }

    result = graph.invoke(initial_state)
    return result


def run_debug_agent(
    workspace_path: str,
    error_output: str,
    config: AICodeConfig,
    state_data: dict | None = None,
    files: dict[str, str] | None = None,
) -> dict:
    """Run just the debug cycle on an existing project."""
    graph = build_graph()

    # Build a state that starts at the debug step
    initial_state: AgentState = {
        "config": {
            "openai_api_key": config.openai_api_key,
            "model_name": config.model_name,
            "max_iterations": config.max_iterations,
            "shell_timeout": config.shell_timeout,
            "workspace_root": config.workspace_root,
        },
        "workspace": workspace_path,
        "description": "",
        "plan": state_data.get("plan", {}) if state_data else {},
        "files": files or {},
        "current_step": "debug",
        "command_output": error_output,
        "errors": [error_output],
        "iteration": 0,
        "max_iterations": config.max_iterations,
        "state_data": state_data or {},
        "status": "debugging",
    }

    result = graph.invoke(initial_state)
    return result
