#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash). Refuses git commits and PR descriptions
that carry AI attribution.

The author of record is the human who reviewed and signed the change. A
CLAUDE.md rule says so; this hook enforces it. Context might be ignored;
enforcement cannot.

Claude Code sends the pending tool call as JSON on stdin:
    {"tool_name": "Bash", "cwd": "...", "tool_input": {"command": "..."}}

Exit 0 allows the call. Exit 2 blocks it and returns stderr to the model,
which then rewrites the message.
"""

import json
import re
import sys
from pathlib import Path

# A commit or PR verb counts only in command position: the start of a line, or
# right after ; && || | ( $(. Prose that merely *mentions* "git commit" (in a
# heredoc that edits a document, say) is not a commit and must pass.
COMMAND_POSITION = r"(?:^|[;&|(]\s*|\$\(\s*)"
GIT_GLOBAL_OPTIONS = r"(?:\s+-\S+(?:\s+[^-\s]\S*)?)*"  # -C <path>, -c k=v, --no-pager
CHANGE_RECORD = re.compile(
    COMMAND_POSITION
    + r"(?:git" + GIT_GLOBAL_OPTIONS + r"\s+commit"
    + r"|gh\s+pr\s+(?:create|edit))"
    + r"(?:\s|$)",
    re.MULTILINE,
)

# Markers of AI authorship. A Co-Authored-By naming a human is a legitimate
# record and does not match.
AI_ATTRIBUTION = re.compile(
    r"co-authored-by:.*(?:claude|anthropic)"
    r"|claude-session:"
    r"|generated with.*claude"
    r"|claude\.ai/code",
    re.IGNORECASE,
)

# git commit -F <file> and gh pr --body-file <file> keep the message where the
# command string can't show it. Those files are read too.
MESSAGE_FILE = re.compile(r"(?:-F|--file|--body-file)[= ]+['\"]?([^\s'\"]+)")

BLOCKED = """\
BLOCKED: commit message or PR description contains AI attribution.
The author of record is the human who reviewed and signed the change.
Remove the attribution lines and retry.
"""


def is_change_record(command: str) -> bool:
    """True if the command commits or writes a PR description."""
    return CHANGE_RECORD.search(command) is not None


def message_text(command: str, cwd: str = ".") -> str:
    """The command plus the contents of any message file it names."""
    text = command
    for match in MESSAGE_FILE.finditer(command):
        path = Path(match.group(1))
        if not path.is_absolute():
            path = Path(cwd) / path
        if path.is_file():
            text += "\n" + path.read_text(errors="replace")
    return text


def should_block(command: str, cwd: str = ".") -> bool:
    """The whole rule: a change record that carries AI attribution."""
    return is_change_record(command) and AI_ATTRIBUTION.search(message_text(command, cwd)) is not None


def main() -> int:
    if len(sys.argv) > 2 and sys.argv[1] == "--check":
        # Hand-check from a shell, no JSON needed:
        #   python3 no_ai_attribution.py --check 'git commit -m "..."'
        command, cwd = " ".join(sys.argv[2:]), "."
    else:
        payload = json.load(sys.stdin)
        command = (payload.get("tool_input") or {}).get("command") or ""
        cwd = payload.get("cwd") or "."
    if should_block(command, cwd):
        sys.stderr.write(BLOCKED)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
