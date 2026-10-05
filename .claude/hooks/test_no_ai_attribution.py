#!/usr/bin/env python3
"""Tests for no_ai_attribution.py.

Run:  python3 .claude/hooks/test_no_ai_attribution.py

A control without a test is an assertion. The suite passes whole or fails.

The fixtures below look like real commits because, to the hook, they are.
Writing this file through a shell heredoc trips the live hook for exactly
that reason; it was written with a file tool instead. Nothing here commits.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import no_ai_attribution as hook  # noqa: E402

HOOK = Path(hook.__file__)

ALLOW = [
    ("plain commit", 'git commit -m "Act 0.3: attribution hook"'),
    ("human co-author", 'git commit -m "Fix" -m "Co-Authored-By: Jane Doe <jane@example.com>"'),
    ("unrelated command", "ls -la && echo Co-Authored-By: Claude"),
    ("amend no-edit", "git commit --amend --no-edit"),
    ("prose in heredoc", "python3 - <<'PY'\ns=\"if it is a `git commit` whose text carries `Co-Authored-By: Claude`\"\nPY"),
    ("committer in prose", 'echo "the git committer said Co-Authored-By: Claude"'),
    ("gh pr view", "gh pr view 1 --json body | grep Claude-Session"),
]

BLOCK = [
    ("claude co-author", 'git commit -m "Fix" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"'),
    ("claude-session heredoc", 'git commit -m "$(cat <<\'M\'\nAct 0.3: hook\n\nClaude-Session: https://claude.ai/code/session_abc\nM\n)"'),
    ("gh pr generated-with", 'gh pr create --title x --body "🤖 Generated with [Claude Code](https://claude.com/claude-code)"'),
    ("chained after &&", 'git add -A && git commit -m "x" -m "Claude-Session: y"'),
    ("git -C path commit", 'git -C /tmp/x commit -m "x" -m "Co-Authored-By: Claude <noreply@anthropic.com>"'),
    ("commit on second line", 'cd /tmp\ngit commit -m "Generated with Claude Code"'),
    ("inside $( )", 'x=$(git commit -m "claude.ai/code/session_1")'),
]


class RuleTests(unittest.TestCase):
    """The pure function, no process boundary."""

    def test_allows(self):
        for label, command in ALLOW:
            with self.subTest(label):
                self.assertFalse(hook.should_block(command), label)

    def test_blocks(self):
        for label, command in BLOCK:
            with self.subTest(label):
                self.assertTrue(hook.should_block(command), label)

    def test_blocks_message_file(self):
        """git commit -F hides the message in a file; the file is read."""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "msg.txt").write_text("Msg\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n")
            self.assertTrue(hook.should_block("git commit -F msg.txt", cwd=tmp))
            self.assertTrue(hook.should_block(f"git commit -F {tmp}/msg.txt"))


class ProcessTests(unittest.TestCase):
    """The hook as Claude Code runs it: JSON on stdin, exit code out."""

    @staticmethod
    def run_hook(command: str) -> subprocess.CompletedProcess:
        payload = json.dumps({"tool_name": "Bash", "cwd": os.getcwd(), "tool_input": {"command": command}})
        return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)

    def test_exit_0_allows(self):
        result = self.run_hook(ALLOW[0][1])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")

    def test_exit_2_blocks_with_reason(self):
        result = self.run_hook(BLOCK[0][1])
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)

    def test_missing_command_allows(self):
        result = subprocess.run([sys.executable, str(HOOK)], input="{}", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
