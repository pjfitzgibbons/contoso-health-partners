#!/usr/bin/env bash
# End-to-end dogfood for no_ai_attribution.py: a real Claude Code session, in
# a throwaway repo that carries this hook, is told to commit WITH attribution.
# Passes when the log comes out clean.
#
#   bash .claude/hooks/dogfood.sh
#
# Uses one model turn. Peter runs this; it is not part of the unit suite.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/.claude/hooks"
cp "$here/no_ai_attribution.py" "$tmp/.claude/hooks/"
cat > "$tmp/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/no_ai_attribution.py"
          }
        ]
      }
    ]
  }
}
JSON

git -C "$tmp" init -q
git -C "$tmp" -c user.name=dogfood -c user.email=dogfood@example.com commit -q --allow-empty -m "init"

cd "$tmp"
echo "--- asking Claude to commit with attribution (hook should refuse it)"
claude -p 'Run exactly this shell command, then tell me in one line what happened:
git -c user.name=dogfood -c user.email=dogfood@example.com commit --allow-empty -m "dogfood" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
If the command is refused, run it again without the Co-Authored-By line.' \
  --allowedTools 'Bash(git commit:*)' 'Bash(git -c:*)' || true

echo "--- git log:"
git log --format='%h %s%n%b' -n 2

if git log --format=%B | grep -qi 'co-authored-by:.*claude'; then
  echo "FAIL: attribution reached the log"
  exit 1
fi
if [ "$(git rev-list --count HEAD)" -lt 2 ]; then
  echo "INCONCLUSIVE: no second commit was made (permission or prompt issue?)"
  exit 2
fi
echo "PASS: second commit landed, no attribution"
