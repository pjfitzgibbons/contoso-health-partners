# TODO — open items

Collected 2026-10-06 from `Untitled-1.md` and the config-research session. Ordered by whether
something is wrong, then by whether something is blocked on it.

## Wrong, and live

- [ ] **Attribution hook has five bypasses.** `no_ai_attribution.py` enumerates commit verbs
      (`git commit`, `gh pr create|edit`). Verified ALLOWED with attribution: `gt create`,
      `gt modify`, `gt submit`, `jj commit`, `hg commit`. `jj` is installed on this machine, so
      this is live, not theoretical. `git -C <dir> commit` is correctly blocked. Add the verbs,
      add a test case per verb. The published W1 post calls this a working control.
- [ ] **`deny` does not protect the enforcement layer.** Claude can edit `.claude/settings.json`
      and unwire the hook. See `config-guard` in `karanb192/claude-code-hooks`.
- [ ] **`deny` does not cover history rewriting.** `git push` is denied; `git rebase` and
      `git reset` are not. Anthropic's `code-migration-kit` template denies both —
      `.tmp/readings/6b-code-migration-kit-settings.json`.
- [ ] **`CLAUDE.workspace.md:55` names the wrong credential path.** Says `~/.netrc`; the file is
      `~/.config/wp-publish/netrc` (0600). `SKILL.md:115` is correct. The wrong path is also in
      the public commit message of `8c2dcf6`.
- [ ] **`CLAUDE.workspace.md:52` references `blog/w1-outline.md`**, which has never been
      committed and is not on disk. Same reference inside the `w1-deferred-settings-layers-thesis`
      memory.

## PLAN.md is behind reality

- [ ] `PLAN.md:138` and `:315` — `settings.json` anchors to the **launch directory**, not the git
      repo root. Refuted by test on 2.1.289. The git-root rule belongs to auto-memory.
- [ ] `PLAN.md:331` — the `.mcp.json` half must be retracted. It **inherits additively from all
      ancestors**, unbounded by the git root, in 2.1.270 / 2.1.278 / 2.1.289 alike. The corollary
      "launching from the workspace root loads zero MCP servers" is the inverse of the truth.
- [ ] `PLAN.md:336` — "zero MCP servers" ignores user-scope servers in `~/.claude.json`, which
      load regardless of launch directory.
- [ ] Downgrade three claims marked "verified" that were documentation fetches, not observations:
      `.mcp.json` non-inheritance, `Read(./.env)` deny blocking a Bash write (the session that
      produced it flagged it may have been a manual decline), and the `attribution` setting
      flipping the harness instruction mid-session (model self-report; the project later searched
      the log and found nothing).
- [ ] Replace the two-way resolution model with the five-row table. Every row has a positive
      control behind it.
- [ ] `PLAN.md:348` / `:372` — hook is `no_ai_attribution.py`, 18 cases in 6 methods, plus
      `dogfood.sh`. Not the `.sh` with 15 cases.
- [ ] `PLAN.md:400` — the `enableAllProjectMcpServers` recommendation was already taken; the flag
      is gone from `settings.local.json`.
- [ ] `PLAN.md:412` — `uv` is a live dependency of the committed `wp-publish` skill, not deferred
      to Act 2. `uv 0.11.7` is installed.
- [ ] `PLAN.md:3` — "Last updated 2026-09-12" while the file was edited 2026-10-04.
- [ ] Terminology: `PLAN.md:138`/`:315` use "memory" to mean `CLAUDE.md`. Auto-memory is a
      different mechanism that behaves oppositely. Two layers, one word.
- [ ] `SKILL.md:133` says two dependencies; `wp_publish.py:3` declares three (Pygments missing).
- [ ] `palette.py` (313 lines, committed) is referenced by no document and its docstring describes
      generating a site palette, not publishing. Against the no-speculative-files rule.

## Act 0.3 remaining

- [ ] `.claude/agents/` — azure-architect, compliance-auditor, security-reviewer. **No good
      compliance-auditor prior art exists**; the 25k-star collection's version is
      template-generated keyword padding that would fight the cite-or-flag rule. Best raw
      material: `trailofbits/skills` `spec-to-code-compliance`, ring's `scoring.md`,
      harness-engineering's `readiness` rubric, VoltAgent's `hipaa-compliance.md` checklist.
      First-party template: `/docs/en/best-practices` ships a complete `security-reviewer.md`.
- [ ] Remaining skills — deploy runbook, control-matrix update, blog drafting. Skeleton for the
      runbook: ring's `generating-release-guides` with its `STRICT_NO_TOUCH` read-only mode.
- [ ] **Rewrite `wp-publish`'s description to be "pushy."** First-party `skill-creator` states
      Claude *undertriggers* skills, and that all trigger conditions belong in the description,
      never the body. Current description is factual and restrained.
- [ ] 🔍 **R1** still open — Azure SQL serverless auto-pause and the current free-tier grant.
      Act 0's exit criterion is that the Learn MCP closes at least one 🔍 row, and across twelve
      transcripts the server has **never been called once**.
- [ ] Decide the shape of workspace-level shared rules. They must be **real files** at the
      workspace level — a symlinked rule file whose target is outside cwd is silently dropped —
      and the workspace root is not a repo, so they would be unversioned. Options: an umbrella
      git repo that ignores the four subrepos, or real copies per repo.

## Decisions taken, not yet done

- [ ] **Un-memory the Taxes-Research infrastructure detail.** Its memory store holds a production
      VPS IP, SSH user, firewall posture, and deploy-key path. No secret values. The repo at
      `~/programming/Taxes-Research` **is already a git repo**, so "create local git" is done —
      what remains is moving the infra notes into a versioned file there and removing them from
      the memory store.

## Harness practice

- [ ] **Subagent cost.** 94% of last-24h usage came from subagent-heavy sessions; 66% from
      `general-purpose`. Define named agents in `.claude/agents/` with cheaper models for
      mechanical work, and tighten prompts. The fix and the Act 0.3 deliverable are the same item.
- [ ] Adopt `agent-sh/agnix` — 458 config-lint rules, each carrying `source_urls`, `verified_on`,
      and an RFC-2119 level. Run it over `.claude/` and triage.
- [ ] Consider `managed-settings.json` at `/Library/Application Support/ClaudeCode/`. It carries
      `hooks` **and** `permissions`, machine-wide, needing only write access to a system
      directory. It is also outside every repo and unreviewable in a PR — enforceability up,
      provenance down. Hybrid worth testing: managed for force, committed copy for evidence, CI
      asserting they match.
- [ ] Port the `SessionStart` TODO hook from `~/programming/Taxes-Research/.claude/settings.json`
      so this file loads every session instead of relying on a human reading it. Use
      `$CLAUDE_PROJECT_DIR`, not the hardcoded absolute path that version uses.
- [ ] `.mcp.json` supports `${VAR}` and `${VAR:-default}` expansion. The no-credential rule can be
      *satisfied* rather than avoided. Note the open bug where `claude mcp add` writes resolved
      values back into the file.

## Writing

- [x] **L1 `blog/l1-multi-repo-config.md`** drafted 2026-10-08 — instructions inherit, enforcement
      does not. No `status:` line; Peter sets that. Two open items in it: the `EXPECTED=0ae1b2c3...`
      digest is a placeholder a reader could copy, and the numbered-reason-heading question in
      `blog-voice.md` *Open* is now exercised by two posts and could be closed either way.
- [ ] **Correct W1 — decide append vs. L2.** `blog-voice.md` freezes a published body above the
      charge and allows only dated `**Update:**` appends, so a deviation this large probably wants
      its own position as **L2** with a link back, rather than an append that rewrites the
      argument. Specifically: the hook failed open once with an unbalanced regex
      (enforcement fails *silently*, which inverts the post's conclusion); the verb enumeration
      is closed-world; and the Linux kernel reached the same rule independently
      (`Documentation/process/coding-assistants.rst`, merged 2025-12-23) while drawing a sharper
      line — AI banned from the certifying field, *required* in a disclosure field.
- [ ] Check whether W1 has had any traffic.
- [ ] Notebook idea: how to verify harness resolution rules by script. The method is already
      proven — throwaway trees under `/private/tmp`, a marker instruction, a positive control, and
      `claude -p '/context' < /dev/null` to read back which files loaded.
