---
title: "Instructions Inherit, Enforcement Doesn't: Claude Code Across Many Repos"
slug: l1-multi-repo-config
excerpt: In Claude Code, instructions inherit down a directory tree and enforcement does not, so shared conventions belong at the top of the tree and every repo carries its own copy of the rules that bite.
categories: [Workbench]
tags: [claude-code, configuration, multi-repo, hooks, permissions, workbench]
---
# Instructions Inherit, Enforcement Doesn't: Claude Code Across Many Repos

*Learnings track, L1 · Draft, 2026-10-08 · Claude Code v2.1.289*

---

In Claude Code, instructions inherit down a directory tree and enforcement does not, so shared conventions belong at the top of the tree and every repo carries its own copy of the rules that bite.

The intention most people start with is one sentence: launch the agent anywhere in the tree, at any depth, and both the shared conventions and the enforcement apply. Half of that is free. The other half you build, and the build is a copy plus a check.

## The Fix

The shape below works for a plain parent directory holding several independent repos. The parent is deliberately not a repo; it is a place where repos sit next to each other, which is how most people's `~/work` or `~/src` actually looks.

```text
workspace/                        # a plain directory, not a git repo
  CLAUDE.md                       # reaches every launch below it; a symlink is fine
  .claude/rules/*.md              # reaches every launch below it; real files only
  .mcp.json                       # reaches every launch below it, additively
  repo-a/
    .claude/settings.json         # hooks, permissions, plugins: launch directory only
    .claude/hooks/
    .claude/settings.local.json   # trust and convenience; anchors to this repo's git root
  repo-b/
    .claude/settings.json         # byte-for-byte identical to repo-a's
    .claude/hooks/
```

Conventions go up top, once. Enforcement goes in each repo, duplicated, and the duplication is the price of the next part:

```jsonc
// repo-a/.claude/settings.json (identical in every repo in the workspace)
{
  "permissions": {
    "deny": [
      "Bash(git push:*)",
      "Bash(git rebase:*)",
      "Bash(git reset:*)",
      "Read(./**/*.pem)",
      "Read(./secrets/**)"
    ]
  },
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
  // "enabledPlugins" and "extraKnownMarketplaces" also live in this file,
  // which is why "plugins on everywhere" needs a copy per repo too.
}
```

A copy that nobody checks drifts within a month. Each repo's build asserts its own copy is the canonical one, so changing the enforcement layer means changing a digest in a pull request where someone sees it:

```bash
# scripts/check-enforcement.sh (runs in every repo's build)
EXPECTED=0ae1b2c3...            # bumped by the pull request that changes settings.json
ACTUAL=$(shasum -a 256 .claude/settings.json | cut -d' ' -f1)
test "$ACTUAL" = "$EXPECTED" || { echo "enforcement layer drifted"; exit 1; }
```

And one command answers every "is it loaded?" question in this post, printing each instruction, rule, and memory file by absolute path with its token cost:

```bash
claude -p '/context' < /dev/null
```

## 1. Reach Is a Property of Each Mechanism, Not of `.claude/`

The `.claude/` directory looks like a unit and behaves like seven unrelated features. Every file in it has its own answer to "how far up does this look?", and the answers do not agree with each other. These are results observed on Claude Code v2.1.289, each with a positive control beside it.

| Mechanism | Anchors to | Positive control |
|---|---|---|
| `CLAUDE.md` | every ancestor directory | loaded from a sibling repo; 67 tokens of real content, named in `/context` by absolute path |
| `.claude/rules/*.md` | every ancestor directory, lazily on file access | an ancestor's `paths:`-scoped rule fired when a matching file was opened |
| `.mcp.json` | every ancestor directory, additively, unbounded by the git root | an ancestor's server appeared in the session, marked pending approval |
| `.claude/settings.json` | the launch directory only | a hook at the repo root did not fire from `repo/sub/deep` |
| `.claude/settings.local.json` | the git repo root, since v2.1.211 | loaded from every subdirectory of the repo |
| auto-memory | the git repo root, else the launch directory | two stores on one machine: one for the non-repo parent, one for the repo inside it |
| project skills | the launch directory and its ancestors | a skill in a subdirectory repo was never offered |

Two of those rows contradict the published documentation, which says project settings and `.mcp.json` both anchor to the launch directory and are not inherited.[^reach] I had the same sentence written into my own project plan, marked verified, for three weeks. It was a documentation fetch wearing a test's clothes. The actual test is four throwaway directories under `/private/tmp`, a marker instruction in the ancestor file, a positive control, and `/context` read back from a non-interactive session. The `.mcp.json` three levels up loaded. The hook one level up did not fire.

Nothing about that is a bug report; `settings.json` not inheriting is a reasonable design, because a parent directory you happened to launch from should not be able to install a hook into your session. The cost is that "put the shared config at the top" is not a strategy. It is a strategy for three mechanisms and a no-op for the rest. From now on, every claim about where a config file reaches gets a throwaway tree and a `/context` read before it gets written down, including the claims in this post.

## 2. The Failure Mode Is Silence, Not an Error

The obvious way to share one file across several repos is to link it. That works for exactly one of the mechanisms above.

My workspace `CLAUDE.md` is a symlink whose target lives inside one of the repos, so the shared conventions are versioned somewhere a pull request can reach them. Launched from a sibling repo, it loads: 67 tokens of real content, not a stub, with the resolved path in `/context`. The same arrangement for a rule file under `.claude/rules/` is dropped. No warning, no entry in `/context`, no non-zero exit. Silence.

`@path` imports behave the same way. They resolve relative to the importing file and follow up to four hops, and an import that resolves outside the working directory fails silently in a non-interactive session—no prompt, no warning, exit code zero.[^imports] A `claude -p` run in a build pipeline will tell you it succeeded while running without the instructions the file said to load. Project skills complete the set: a skill in a repo below the launch directory is not discovered, and a session that never had it also never says so.

Three mechanisms, three different ways of not being there, and none of them announce it. That is the argument for the duplicated real file over the clever link, and the argument for reading `/context` rather than reasoning about the tree. The steady state is cheap: after any change to a shared instruction file, one `claude -p '/context' < /dev/null` prints the absolute path of everything that loaded, and a file missing from that list is a file that is not in the session.

## 3. Enforcement Has to Be Copied, and a Copy Needs a Witness

Who gets to turn off the control that blocks a `git push`? Where would they do it? Would anyone see the diff?

Permissions, hooks, and `enabledPlugins` all live in `settings.json`, the one file that reaches only the launch directory. Plugins can carry skills, hooks, subagents, and output styles, which makes them the natural answer for sharing a setup across repos—except that permission rules cannot travel in a plugin at all, and the switch that turns a plugin on is itself a `settings.json` key.[^plugins] So "plugins enabled anywhere in the tree" cannot be achieved by placing one file at the top of the tree. Three things can achieve it, and they cost different things.

User-scope settings in `~/.claude/settings.json` apply to every project on the machine and cannot be path-restricted. A rule written for three repos becomes a rule for every repo you will ever open, a client's included. Machine-wide managed settings at `/Library/Application Support/ClaudeCode/managed-settings.json` carry both hooks and permissions, cannot be overridden by user or project settings, and need only write access to a system directory.[^managed] They are also outside every repo. No clone contains them, no pull request shows them, and the person who changed one leaves no diff behind. A per-repo `settings.json` is the duplicated option: more bytes, drift to manage, and the only one of the three that a reviewer can read in the change that introduces it.

I take the per-repo copy with the digest check, because a control nobody can show you in a diff is a control nobody can defend. Three years on, a new engineer runs `git log` on the file and sees when the deny list changed and who signed it. Managed settings are the escalation when force matters more than provenance, and the pairing is worth testing: managed settings for the guarantee, a committed copy for the record, and a build step asserting the two match. From here on, a repo whose `.claude/settings.json` does not hash to the published digest fails its build, and the pull request that changes the digest is where the conversation about enforcement happens.

## Where This Doesn't Hold

Every row in the reach table is one machine, one platform, one version of Claude Code—v2.1.289—and the two rows that contradict the documentation are the two most likely to change under me, in either direction. I have not tested managed settings at all; the claim that they carry hooks and permissions and resist local override comes from the documentation, and the hybrid I recommend in reason 3 is a proposal, not a result. The digest check catches drift and does nothing about the cause, and it cannot see the three other ways a session can lose a shared instruction: `claudeMdExcludes` skips `CLAUDE.md` and rules files by glob against absolute paths, and because its arrays merge across scopes, a local file can quietly drop conventions the project set;[^excludes] `additionalDirectories` grants file access while loading no instructions at all; and `--add-dir` loads skills but loads `CLAUDE.md` and rules only when `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` is set in the environment.[^adddir] None of those three is a hole in the scheme above. They are three more places where a file you believe is loaded is not, which is the same lesson as reason 2 with the volume up.

Test the reach before you trust the file.

[^reach]: Claude Code documentation: [Debug your configuration](https://code.claude.com/docs/en/debug-your-config), [Settings](https://code.claude.com/docs/en/settings) (precedence and where Claude Code looks for each file), and [Set up Claude Code in a monorepo or large codebase](https://code.claude.com/docs/en/large-codebases), which states that "project settings in `.claude/settings.json` aren't inherited from parent directories the way CLAUDE.md files are"—correct—and the [MCP](https://code.claude.com/docs/en/mcp) page's companion troubleshooting row, which describes `.mcp.json` as belonging at the repository root. Neither page describes additive inheritance from ancestors; that row of the table is observation against documentation, and the observation is what I act on.
[^imports]: Observed on 2.1.289 in a non-interactive `claude -p` session. The four-hop limit and the relative resolution are documented under [Memory and project instructions](https://code.claude.com/docs/en/memory); the silent failure outside the working directory is not, and I treat it as version-specific until someone reproduces it elsewhere.
[^plugins]: ["Steering Claude Code: when to use CLAUDE.md, skills, hooks, and subagents"](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more), June 18, 2026, for the layer taxonomy and the point that a real guardrail has to be deterministic. Plugin components and the `enabledPlugins` key: [Plugins](https://code.claude.com/docs/en/plugins/overview) and the [settings reference](https://code.claude.com/docs/en/settings-reference).
[^managed]: Claude Code documentation: [Managed settings](https://code.claude.com/docs/en/settings#managed-settings). Unverified here—I have not deployed the file.
[^excludes]: `claudeMdExcludes` under [Set up Claude Code in a monorepo or large codebase](https://code.claude.com/docs/en/large-codebases): glob patterns matched against absolute file paths, skipping both `CLAUDE.md` and rules files, settable at user, project, local, or managed scope, with arrays merging across scopes. Managed-policy `CLAUDE.md` files cannot be excluded.
[^adddir]: Same page, [Grant access across packages or repositories](https://code.claude.com/docs/en/large-codebases): the `additionalDirectories` setting never loads `CLAUDE.md`, rules, or skills, while `--add-dir` loads skills always and instruction files only with the environment variable set.
