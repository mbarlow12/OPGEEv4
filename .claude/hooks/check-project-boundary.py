#!/usr/bin/env python3
"""
PreToolUse hook: Block file operations outside project directory.
Allowed: Project directory, /tmp, ~/.claude, ~/.config/claude
"""
import json
import sys
from pathlib import Path

# Configuration
PROJECT_ROOT = Path.cwd().resolve()
ALLOWED_PREFIXES = [
    PROJECT_ROOT,
    Path("/tmp"),
    Path.home() / ".claude",
    Path.home() / ".config" / "claude",
]

def is_path_allowed(path_str: str) -> tuple[bool, str]:
    """Check if a path is within allowed boundaries."""
    try:
        path = Path(path_str).resolve()
        for allowed in ALLOWED_PREFIXES:
            try:
                path.relative_to(allowed)
                return True, ""
            except ValueError:
                continue
        return False, f"Path '{path}' is outside project directory"
    except Exception as e:
        return False, f"Could not resolve path: {e}"

def check_tool_input(data: dict) -> tuple[bool, str]:
    """Check tool input for path violations."""
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool in ("Read", "Edit", "Write", "NotebookEdit"):
        file_path = tool_input.get("file_path", "")
        if file_path:
            return is_path_allowed(file_path)

    if tool in ("Glob", "Grep"):
        path = tool_input.get("path", ".")
        return is_path_allowed(path)

    return True, ""

def main():
    data = json.load(sys.stdin)
    allowed, reason = check_tool_input(data)

    if allowed:
        sys.exit(0)
    else:
        result = {"decision": "block", "reason": reason}
        print(json.dumps(result))
        sys.exit(0)

if __name__ == "__main__":
    main()
