# AICode CLI - Agentic Coding Assistant

An AI-powered CLI tool that automatically builds MVP projects and debugs existing codebases through an iterative plan-scaffold-generate-test-fix workflow. Powered by OpenAI.

---

## Prerequisites

- **Python 3.10+** installed on your system
- **pip** (Python package manager)
- **OpenAI API Key** — get one at https://platform.openai.com/api-keys

---

## Installation

### 1. Clone / navigate to the project

```bash
cd /Users/gokuldasgirishkumar/code/aicodew
```

### 2. Install the package

```bash
pip install -e .
```

This installs `aicode` as a global CLI command.

### 3. Set your API key

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

To make it permanent, add the line to your shell profile:

```bash
# For zsh (macOS default)
echo 'export OPENAI_API_KEY="your-key-here"' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export OPENAI_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Verify installation

```bash
aicode --help
```

---

## Usage

### Initialize a project workspace

```bash
aicode init my-project
```

Creates `./aicode_workspace/my-project/` with a `.aicode/state.json` state file.

### Build an MVP from a description

```bash
aicode build "a Flask REST API with /health and /hello endpoints"
```

This runs the full agent pipeline:
1. **Plan** — LLM generates a step-by-step build plan
2. **Scaffold** — Creates folder structure and file stubs
3. **Generate** — LLM writes full implementation code for each file
4. **Execute** — Installs dependencies and runs tests
5. **Debug** (if needed) — Analyzes errors, applies patches, re-runs (up to 5 iterations)

You can also specify a custom project name:

```bash
aicode build "a todo app with REST API" --name my-todo-app
```

### Debug an existing project

```bash
# Debug using a specific command
aicode debug my-project --command "pytest"

# Debug using the last known error from state
aicode debug my-project
```

The debugger will:
- Run the command and capture the error
- Send the error + source code to the LLM
- Apply the suggested fix as a patch
- Re-run the command to verify
- Repeat until fixed or max iterations reached

### Run a command in the workspace

```bash
aicode run my-project "python app.py"
aicode run my-project "pip install flask"
aicode run my-project "pytest -v"
```

Commands are checked against a security allowlist before execution.

### Run tests

```bash
aicode test my-project
```

Auto-detects the test framework (`pytest` for Python, `npm test` for Node.js).

### Check project status

```bash
aicode status my-project
```

Displays a table with: project status, iteration count, files created, commands run, errors, and patches applied.

---

## Using AICode from any directory

The `aicode` command works from **any directory** on your system. By default, it creates workspaces at `./aicode_workspace/` relative to your current directory.

To use a fixed workspace location from anywhere:

```bash
export AICODE_WORKSPACE="/home/yourname/projects/aicode_workspace"
```

Examples:

```bash
# From your home directory
cd ~
aicode build "a calculator CLI app"
# Creates ~/aicode_workspace/a-calculator-cli-app/

# From a different folder
cd /tmp
aicode build "a weather API" --name weather-api
# Creates /tmp/aicode_workspace/weather-api/

# With a custom workspace root
export AICODE_WORKSPACE="/home/yourname/my-ai-projects"
aicode build "a blog with markdown support"
# Creates /home/yourname/my-ai-projects/a-blog-with-markdown-support/
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | Your OpenAI API key |
| `AICODE_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `AICODE_MAX_ITERATIONS` | `5` | Max debug-fix iterations before stopping |
| `AICODE_SHELL_TIMEOUT` | `60` | Command timeout in seconds |
| `AICODE_WORKSPACE` | `./aicode_workspace` | Root directory for all project workspaces |

---

## Project Structure

```
aicodew/
├── pyproject.toml              # Package configuration and dependencies
├── README.md                   # This file
├── aicode/
│   ├── __init__.py             # Package init
│   ├── cli.py                  # Typer CLI commands (init, build, debug, run, test, status)
│   ├── config.py               # Configuration loading from environment variables
│   ├── state.py                # Persistent state via .aicode/state.json
│   ├── workspace.py            # Workspace directory creation and path validation
│   ├── security.py             # Command allowlist and blocklist for safe execution
│   ├── shell.py                # Subprocess execution with timeout and output capture
│   ├── filesystem.py           # File/directory operations scoped to workspace
│   ├── diff_patch.py           # Unified diff generation and patch application
│   ├── llm.py                  # LangChain + Google Gemini LLM integration
│   ├── prompts.py              # Prompt templates for planning, coding, and debugging
│   ├── tools.py                # LangChain tool definitions for the agent
│   ├── graph.py                # LangGraph agent workflow (plan→scaffold→generate→test→debug)
│   └── ui.py                   # Rich terminal UI (panels, tables, spinners)
```

---

## Security

AICode uses a **command allowlist** to prevent dangerous operations:

**Allowed commands:** `python`, `pip`, `node`, `npm`, `npx`, `pytest`, `git`, `mkdir`, `ls`, `cat`, `echo`, `touch`, `cp`, `mv`, `flask`, `uvicorn`, `gunicorn`, `tsc`, `eslint`, `prettier`

**Blocked patterns:** `rm -rf /`, `sudo`, `curl | bash`, `shutdown`, `mkfs`, `dd if=`, `chmod 777 /`, etc.

All file operations are **sandboxed** inside the workspace directory. The tool cannot read or write files outside the project workspace.

---

## Quick Start Example

```bash
# 1. Install
cd /Users/gokuldasgirishkumar/code/aicodew
pip install -e .

# 2. Set API key
export OPENAI_API_KEY="your-key"

# 3. Build a project
aicode build "a simple Flask REST API with /health and /hello endpoints" --name flask-api

# 4. Check status
aicode status flask-api

# 5. Run it
aicode run flask-api "python app.py"

# 6. Debug if something breaks
aicode debug flask-api --command "pytest"
```

---googl

## Supported Stacks (v1)

- **Python** — Flask, FastAPI, pytest, pip
- **Node.js** — Express, npm, basic JS/TS projects

The LLM auto-detects the appropriate stack based on your project description.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `OPENAI_API_KEY not set` | Run `export OPENAI_API_KEY="your-key"` |
| `Command blocked` | The command isn't in the allowlist. Use `aicode run` with allowed commands only |
| `Max iterations reached` | The debugger couldn't fix the issue in 5 attempts. Check the errors manually |
| `Workspace not found` | Run `aicode init <project-name>` first, or check the workspace path |
| `ModuleNotFoundError` | Run `pip install -e .` again from the aicodew directory |
