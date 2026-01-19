"""
Validation Rules Prompt

This prompt summarizes critical validation rules for tool usage.
It is designed to be appended to system prompts to remind agents of:
1. Tool validation constraints (Shell/File/Git)
2. Safe command practices
3. Forbidden patterns
"""

VALIDATION_RULES_PROMPT = """
## Tool Usage & Validation Rules

You operate within a protected environment with strict validation rules. 
Any tool call that violates these rules will be rejected by the middleware.

### 1. General Safety
- **No Command Chaining**: Operators like `&&`, `;`, `|` are FORBIDDEN in shell commands. Run commands sequentially as separate tool calls.
- **No Dangerous Patterns**: `rm -rf`, `sudo`, `mkfs`, writing to `/dev`, or pipe-to-bash (`curl ... | bash`) are strictly blocked.
- **Path Restrictions**: All file and shell operations are restricted to the `./workspace` directory.

### 2. Shell & Git Operations
- **Unified Shell Tool**: Use `shell_run` for all system commands (including `ls`, `cd`, `git`, `npm`, `pip`, etc.).
- **Git Safety**: 
  - `git push --force` to protected branches (main/master) is BLOCKED.
  - Hard resets (`git reset --hard`) are monitored.
  - Standard git commands (`status`, `add`, `commit`, `checkout`) work normally.

### 3. File Operations
- **Paths**: Must be relative to `./workspace` or absolute paths within it.
- **No Traversal**: `../` traversal outside workspace is blocked.

### 4. Error Handling
- If a tool fails with "Permission denied" or "Validation failed", DO NOT retry the exact same command.
- Rephrase the command to be safer or break it down into atomic steps.
"""
