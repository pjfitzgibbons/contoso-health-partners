# Contoso Health Partners — workspace instructions

Applies to all four repos under `~/programming/ms-security/`. Repo-specific conventions live in
each repo's own `CLAUDE.md`.

## What this is

A **teaching project, blogged as it happens**: three legacy apps with three separate hand-rolled
auth systems, consolidated onto a compliant identity platform on Azure. Roadmap and regulatory
analysis in `ms-security-docs/PLAN.md` — read it before proposing work.

**Current position: Act 0 — workbench.** Nothing deployed. No Azure account yet.

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
