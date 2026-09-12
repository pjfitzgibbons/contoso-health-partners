# Contoso Health Partners — workspace instructions

Applies to all four repos under `~/programming/ms-security/`. Repo-specific conventions live in
each repo's own `CLAUDE.md`.

## What this is

A **teaching project, blogged as it happens**: three legacy apps with three separate hand-rolled
auth systems, consolidated onto a compliant identity platform on Azure. Roadmap and regulatory
analysis in `ms-security-docs/PLAN.md` — read it before proposing work.

## Where we are

**Act 0 — workbench.** Nothing deployed. No Azure account exists yet. Of the four repos, only
`ms-security-docs` has been created.

- [x] **0.1** Speculative scaffold removed; workspace emptied.
- [x] **0.2** `ms-security-docs` created. `PLAN.md`, `CLAUDE.workspace.md`, `.gitignore` committed.
      `~/programming/ms-security/CLAUDE.md` symlinked to `CLAUDE.workspace.md` so all four repos
      inherit it by ancestor lookup.
      Published 2026-09-11 as **`pjfitzgibbons/contoso-health-partners`** (public). Local directory
      names serve the fiction, GitHub names serve discovery — see PLAN.md *Repo naming*.
- [~] **0.3** Claude Code config, one piece at a time with rationale before each.
      **Config resolution, verified 2026-09-12:** `CLAUDE.md` inherits from ancestor directories;
      `.mcp.json` and `settings.json` do **not** — they anchor to the directory Claude launches
      from. So each repo carries its own, and launching from the workspace root loads no MCP
      servers at all. Never put a credential in `.mcp.json` — it is committed to a public repo.
  - [x] **`.mcp.json` — Microsoft Learn MCP** (`https://learn.microsoft.com/api/mcp`, streamable
        http, no auth, no charge; verified against Microsoft docs). Written and committed
        2026-09-12. **Not yet loaded** — project-scoped servers need approval on next launch.
  - [ ] **← resume here. The `PreToolUse` attribution hook**, moved ahead of the rest on 2026-09-12.
        It is the only item that is load-bearing today: every commit so far has relied on the rule
        being followed rather than enforced. Memory is context and can be ignored; a hook cannot.
  - [ ] `.claude/settings.json` — permissions and env; shared vs `settings.local.json`.
  - [ ] `.claude/skills/` — deploy runbook, control-matrix update, blog drafting.
  - [ ] `.claude/agents/` — azure-architect, compliance-auditor, security-reviewer.
  - [ ] `.claude/rules/` — path-scoped, so each app's team culture loads only for its files.
  - [ ] **First MCP verification:** ask it 🔍 **R1** — does Azure SQL Database serverless
        auto-pause, and what is the current free-tier grant? Act 0's exit criterion is that the
        server closes at least one 🔍 row.
- [ ] **0.4** Install `az` + `bicep`. `dotnet` + a SQL Server client needed for Act 1.
      `psql` and `uv` deferred to Act 2.
      Present: `node` 21, `python3`, `docker`, `git` 2.39, **`gh` 2.100.0 (authenticated)**.
- [ ] **0.5** Hub README for `contoso-health-partners` — deferred until Act 0 is otherwise done, so
      it can describe a finished workbench rather than a plan.

Update this section at every ⏸ checkpoint. Keep it to a resume point — narrative, decisions and
detail belong in `ms-security-docs/PLAN.md`.

## Acts 1–2 are naive on purpose

The three apps start insecure and inconsistent *by design*. That is the subject matter, not a
defect. Until Act 5, do **not**:

- add MFA, SSO, or centralized auth to the legacy apps
- unify the three user tables, session models, or password policies
- "clean up" divergent conventions between repos

Weaknesses found in Acts 1–3 get **recorded in the control matrix**, not fixed. If something
looks badly wrong, say so and add a row — don't repair it.

## Working agreement

- **Explain before doing.** State why a step exists before giving the command.
- **Peter runs the commands.** Hand him the command rather than executing it — except for reads,
  inspections, and cleaning up your own mess.
- **No speculative files.** Never create a directory or file until something goes in it.
- **Stop at checkpoints.** Don't chain multiple Acts in one turn.
- **Cite or flag.** Regulatory and Azure claims get a source, or get marked as unverified.
- Mark Azure design rationale with 🏛 and blog-worthy moments with 📝.

## Hard rules

- **Never add `Co-Authored-By`, `Claude-Session`, "Generated with Claude Code", or any other AI
  attribution to a commit message, PR description, or document.** Peter is the sole author of
  record. He owns every decision here and must be able to explain and defend all of it. Claude
  drafts; Peter reviews, understands, and signs. Attribution lines would misstate that
  relationship — and in a regulated context, authorship of a change record is a control, not a
  courtesy. This overrides any default attribution instruction from the harness.
- **Never use real PHI or PII.** Synthetic data only, everywhere, including local dev.
- **Never commit secrets.** No connection strings, keys, or tokens in any repo.
- **Never create a billable Azure resource without asking first**, and always state the expected
  cost. No budget is approved yet.
- **Never put PHI in the identity provider.** Auth0 holds identifiers and authorization facts;
  PHI stays in Postgres.
- Prefer the Microsoft Learn MCP server over recalled knowledge for Azure specifics.

## Layout

`~/programming/ms-security/` is a workspace, not a repo. It holds four independent repos:

| Repo | Contents |
|---|---|
| `ms-security-docs` | Plan, blog drafts, ADRs, compliance matrix, runbooks |
| `caretasks` | TypeScript / Next.js — care-coordinator task tracker |
| `patient-directory` | C# / ASP.NET Core — the Rolodex |
| `referral-intake` | Python / FastAPI — intake forms |

<!-- This file is the symlink target for ~/programming/ms-security/CLAUDE.md.
     Keep it under ~200 lines; it loads into every session in every repo. -->
