"""Prompt templates for the agentic workflow."""

PLAN_PROMPT = """You are an expert software architect. Given a project description, produce a detailed build plan.

Project Description: {description}

Respond with a JSON object containing:
{{
  "project_name": "short-name",
  "stack": "python" or "node",
  "steps": [
    {{
      "step": 1,
      "description": "what to do",
      "files": ["path/to/file.py"]
    }}
  ],
  "folder_structure": ["dir1/", "dir1/file.py", "dir2/"],
  "test_command": "pytest" or "npm test",
  "run_command": "python app.py" or "node index.js"
}}

Keep the plan minimal and focused on an MVP. Only include essential files.
Respond ONLY with the JSON object, no markdown fences or extra text."""

SCAFFOLD_PROMPT = """You are a code scaffolding tool. Given a project plan, create the initial file stubs.

Plan:
{plan}

For each file in the plan, produce the content. Respond with a JSON object:
{{
  "files": {{
    "path/to/file.py": "file content here...",
    "path/to/another.js": "file content..."
  }}
}}

Create proper file content with imports, basic structure, and placeholder comments.
Respond ONLY with the JSON object, no markdown fences or extra text."""

GENERATE_PROMPT = """You are an expert programmer. Generate the complete implementation for a file.

Project context:
{context}

File to generate: {file_path}
Purpose: {purpose}

Other project files for reference:
{other_files}

Write the complete, working code for this file. Respond ONLY with the raw code, no markdown fences.
The code must be production-ready and functional."""

DEBUG_PROMPT = """You are an expert debugger. Analyze the error and provide a fix.

Project files:
{files}

Command that failed: {command}
Exit code: {exit_code}

Error output:
{error_output}

Previous fix attempts (if any):
{previous_attempts}

Analyze the root cause and provide a fix. Respond with a JSON object:
{{
  "root_cause": "explanation of the error",
  "fixes": [
    {{
      "file": "path/to/file.py",
      "content": "entire corrected file content"
    }}
  ],
  "additional_commands": ["pip install missing-package"]
}}

Respond ONLY with the JSON object, no markdown fences or extra text."""

FINAL_PROMPT= """ you are an security expert. go through the full code and find any possible security vulnerabilities
Project Files:
{files}

Analyze the complete code base and suggest possible security vulenerabilites respond with a JSON object:
{{
  "vulnerability" : "security issue found",
  "level" : "the level of threat",
  "fixes": [
    {{
      "file": "path/to/file.py",
      "content": "entire corrected file content"
    }}
  ],
  "additional_commands": ["pip install missing-package"]
}}
"""