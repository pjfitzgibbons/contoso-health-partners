# PLAN — From Three Legacy Apps to a Compliant Identity Platform on Azure

**Status:** Act 0.3 — Claude Code configuration · Last updated 2026-09-11

> **Scheduled split:** this document is at the practical ceiling for something read end-to-end
> before every session. **At the Act 1 checkpoint, split it** — blog drafts and the control matrix
> move to their own files (`compliance/control-matrix.md` already has a home planned at 3.4), and
> PLAN.md keeps the arc, the decisions, and the research queue.

> A living document. Every Act updates it, and the diffs are blog material. When a decision here
> turns out wrong, we amend it in place and note why — the amendment is often the better post.

---

## Context

This is a **teaching project, blogged as it happens**. The subject is not the apps — it's the
journey from the identity mess real organizations actually have to a standards-compliant,
auditable identity platform on Azure.

The premise: **Contoso Health Partners**, a mid-size specialty care org, has accumulated three
customer-service apps over roughly ten years under different teams and changing leadership. Each
was built by a different group, in a different stack, with its own hand-rolled authentication and
its own user table. **All three hold PHI** — see *Why all of it is PHI* below; this is not the
hedge it first appears to be. None has an audit trail worth the name. This is not a strawman — it is the median state of a company that has been
shipping for a decade.

*(Contoso is deliberate. Contoso, Fabrikam, Northwind and Adventure Works are Microsoft's
canonical fictional companies; every Azure doc example uses them, so our naming lines up with the
documentation we'll be reading.)*

We start **naive on purpose**. Acts 1 and 2 build the mess faithfully and solve nothing. Then we
assess it, decide buy-vs-build, and strangle the old auth out app by app — learning the Azure
platform model and the regulatory landscape as we go.

**Two outputs matter equally:** a working compliant system, and a blog series that teaches
someone else to do it.

---

## Working agreement

1. **Peter runs the commands.** Claude explains *why* first, hands over the command, and they read
   the output together. `! <command>` in the prompt runs it inline so output lands in the session.
2. **Nothing is created speculatively.** No directory, file, or Azure resource exists until there
   is a stated reason for it. *(Claude's opening move was a `mkdir` scaffold — exactly the wrong
   instinct, and the origin of this rule.)*
3. **⏸ Checkpoints** are explicit stop-and-discuss points.
4. **🏛 Sidebars** mark "the Microsoft way" — the philosophy behind a design, not the steps. Why
   ARM is declarative. Why everything is a resource ID. Why RBAC hangs off the resource tree.
   These are what make Azure make sense rather than feel arbitrary.
5. **📝 Blog notes** get captured *while confused*, not after. The moment of not-understanding is
   the post.
6. **Corrections are expected.** Verified claims get a citation; reasoning from memory is labeled.
7. **🔍 Research tags.** Any claim reasoned from memory carries an inline **🔍 R*n*** tag at the
   point of use, and a matching row in the **Open verification queue** at the foot of this
   document. A tagged claim may shape the plan but may **not** enter a post, a control-matrix row,
   or an ADR until it is checked and the tag is retired with a source. Most of the queue is
   blocked on the Microsoft Learn MCP server (Act 0.3), which is why that is the resume point.

---

## Editorial rules

Decided 2026-09-11. These govern what gets published, and they are not negotiable per-post.

1. **Agentic tooling is quarantined.** The security-architecture series (Posts 1–8) contains no
   content about AI assistance, agents, or Claude Code. How this project was built is an
   implementation detail the main series does not discuss. The workbench track is a separate,
   independent study with its own numbering.
   - *One non-exception:* **Annex 22 (AI)** is subject matter — AI as a regulated system under
     GMP has nothing to do with our tooling. It stays in the compliance thread. Post 3 should say
     so in a sentence so readers don't hear an echo.
2. **No public URLs.** Deployed hostnames are never published. A technical walkthrough plus the
   public GitHub repos is sufficient context for any post. If a post genuinely cannot work without
   a live URL, that is a signal the post is wrong, not that the rule is.
3. **Redaction discipline.** Screenshots have hostnames blurred. No tenant IDs, no subscription
   IDs, no resource names that encode anything real. Synthetic data everywhere means screenshot
   *contents* are already safe; hostnames are the exposure.
4. **Named vendors get verified before publication.** Characterizing a real business in public is
   a higher bar than a plan entry. Drafts use categories; names go in only after checking.
5. **Intentionally insecure code is labeled as such, prominently.** The three app repos are public
   and contain deliberately broken authentication in a health-adjacent context. Each gets a README
   banner above the fold — *intentionally insecure, teaching artifact, do not deploy* — naming the
   specific weaknesses and the Act that removes them. Non-negotiable before any app repo is pushed.

---

## Repo layout

Four repos, matching the "different teams, different eras" story. `~/programming/ms-security/` is
a **workspace, not a repo** — it holds the four clones plus the shared `CLAUDE.md` symlink.

| Repo | Story | Stack | Era | Built in |
|---|---|---|---|---|
| `ms-security-docs` | Our repo. Plan, blog drafts, ADRs, compliance matrix, threat models, runbooks. | Markdown | now | Act 0 |
| `patient-directory` | The Rolodex. Oldest, owned by the "enterprise" team, grudgingly ported forward. | C# / ASP.NET Core / EF Core / **SQL Server** | ~2016 | **Act 1** |
| `referral-intake` | Escaped from the data team as a POC and became load-bearing. | Python / FastAPI / SQLModel / Postgres | ~2021 | **Act 2** |
| `caretasks` | Care-coordinator task tracker. Contractor-built, newest, nobody left who wrote it. | TypeScript / Next.js / Prisma / Postgres | ~2024 | **Act 2** |

**Repo naming.** Decided 2026-09-11. Local directory names serve the fiction; GitHub repo names
serve discovery. They deliberately differ, which costs nothing and keeps `CLAUDE.md`, paths and the
story clean.

| Local directory | GitHub repo (`pjfitzgibbons`) | Created |
|---|---|---|
| `ms-security-docs` | **`contoso-health-partners`** — the hub | ✅ 2026-09-11, public |
| `patient-directory` | `contoso-patient-directory` | Act 1 |
| `referral-intake` | `contoso-referral-intake` | Act 2 |
| `caretasks` | `contoso-caretasks` | Act 2 |

Three rules: a shared **`contoso-`** prefix does the visual grouping, since GitHub has no folders;
a shared **topic** (`contoso-health-partners`) does the actual discovery; and **the docs repo is the
hub** — its README is the front door every post links to, pointing onward to the three apps.
`contoso-` reads instantly as "fictional company, teaching artifact" to an audience that reads Azure
documentation, which is the whole reason the premise picked the name. ⚠️ Microsoft publishes its own
Contoso samples, so each app README carries a line disowning any official affiliation (Editorial
rule 5).

**Implementation follows era.** Decided 2026-09-11. We build oldest-first, because that is the
order the org accumulated them and because each app inherits constraints from the one before it.
It also puts the most Microsoft-shaped app (.NET on SQL Server) in Act 1, where the Azure mental
model is being taught — which is the right pairing.

**`patient-directory` is SQL Server, not Postgres.** In 2016 no Microsoft shop was reaching for
Postgres; they were still recovering from the Access-to-SQL-Server migration. Getting this right
matters beyond flavor:
- 🏛 It makes **Entra authentication for Azure SQL** reachable in Act 1 — the best "Microsoft way"
  lesson available that early, and unreachable with Postgres.
- It splits Act 7.2 into two genuinely different encryption stories: Azure SQL has TDE on by
  default with CMK optional; Postgres does not work that way.
- 🔍 **R1** It may *help* cost — Azure SQL serverless auto-pauses, which Postgres Flexible Server
  cannot. Unverified; check before Act 1.1.
- It breaks the "three identical Postgres servers" symmetry, which is more realistic, not less.

**Config resolution drove the repo layout.** `CLAUDE.md` loads from the working directory *and
every directory above it*, so a workspace-level file is inherited by all four repos for free.
`settings.json` does **not** inherit — it anchors to the git repo root — so each repo carries its
own. That asymmetry is why the shared memory lives at workspace level and per-repo settings live
per repo.

**Infra starts deliberately duplicated.** In Acts 1–2 each app repo carries its own `infra/`
Bicep, diverging in style, because that is what actually happens. Extracting a shared platform
layer in Act 7 is itself a lesson, and a post.

**Environments: `test` and `prod` per app. That is all.** Decided 2026-09-11. No dev tier, no
staging, no ephemeral PR environments — a mid-size org with three inherited apps does not have a
mature environment strategy, and pretending otherwise would teach the wrong thing. Six
environments total. `prod` stands; `test` is Bicep-defined and torn down when not in active use
(see Act 1.1 on teardown as the primary cost control).

**Candidate open-source bases** — all permissively licensed, all shipping their own bespoke auth,
which is exactly the naive starting state we want. Verified at the start of each Act rather than
trusted from this list:

- `patient-directory` — [`jasontaylordev/CleanArchitecture`](https://github.com/jasontaylordev/CleanArchitecture),
  scaffolded via `dotnet new ca-sln` (SQL Server is the template default). Ships ASP.NET Core
  Identity: local passwords, PBKDF2 hashes, no MFA, and an `AuditableEntity` base class carrying
  `Created` / `CreatedBy` / `LastModified` / `LastModifiedBy`. A perfect period piece.
- `referral-intake` — [`fastapi/full-stack-fastapi-template`](https://github.com/fastapi/full-stack-fastapi-template).
  Ships SQLModel + Postgres + homegrown JWT + bcrypt + a `FIRST_SUPERUSER` env var.
- `caretasks` — a Next.js + Prisma todo starter; we bolt on a credentials login and a `users` table.

---

## Regulatory landscape (verified 2026-09-10)

Established early because it drives every downstream design decision — and because two items in
the original brief needed correcting.

### Corrections to the brief

- **"FDA CFR pt 12"** is **21 CFR Part 11** — *Electronic Records; Electronic Signatures*. There
  is no Part 12 in this space.
- **Part 11 and Annex 11 may not actually bind us.** Part 11 applies to records an FDA-regulated
  entity must keep under a *predicate rule* (drugs, devices, biologics, clinical trials). EU
  Annex 11 is EU **GMP** — manufacturing. A care-delivery org is squarely under HIPAA and
  probably neither of the others. **Act 3.3 does an honest applicability analysis.** We will still
  engineer to Part 11 and Annex 11 because they are the strictest audit-trail and data-integrity
  bar available, and clearing them makes HIPAA straightforward — but we will state plainly which
  controls are *required* versus *voluntarily adopted*. Claiming compliance you don't have is its
  own liability.

### What actually applies

| Regime | Status | What it forces on us |
|---|---|---|
| **HIPAA Security Rule** (45 CFR 164 Subpart C) | In force | Access control, unique user ID, automatic logoff, encryption (currently *addressable*), audit controls, integrity, transmission security |
| **HIPAA Privacy / Breach Notification** | In force | Minimum necessary, accounting of disclosures, 60-day breach notice |
| **HIPAA Security Rule NPRM** | **Proposed, not final.** Published 2025-01-06; comments closed 2025-03-07; OMB targets ~July 2027. Current rule remains in effect. | Would make **MFA mandatory** and **encryption at rest and in transit mandatory** (removing "addressable"), plus asset inventory and network mapping. **We build to this now** — it is where the puck is going, and good practice regardless. |
| **HITECH** | In force | Business-associate liability, breach economics |
| **21 CFR Part 11** | Applicability TBD (Act 3.3) | §11.10(e) secure, computer-generated, time-stamped audit trails that never obscure prior values; §11.10(d) access limited to authorized individuals; §11.300 password/ID controls; Subpart C electronic signatures |
| **EU GMP Annex 11** | Applicability TBD. **Draft revision published 2025-07-07**, consultation closed 2025-10-07, final expected mid-2026. | Grows 5 → 19 pages, 17 chapters. First time **cybersecurity is a core GMP requirement** (~20 subsections). New identity-and-access-management chapter, ~10 subsections on audit trails, cloud services explicitly in scope, supplier and contract obligations. Companion **new Annex 22 (AI)** limits GMP-critical AI to static deterministic models. Directly relevant to us. |
| **ALCOA+** | Guidance, universally expected | **A**ttributable, **L**egible, **C**ontemporaneous, **O**riginal, **A**ccurate, plus **C**omplete, **C**onsistent, **E**nduring, **A**vailable |
| **GDPR** | If any EU data subjects | Lawful basis, DSARs, erasure, residency, processor DPA |
| **NIST SP 800-63B** | Not law; the reference standard | Authenticator assurance levels — what "MFA" concretely means |
| **42 CFR Part 2**, state law (CCPA/CPRA, TX HB 300) | Situational | Substance-use records, state privacy overlays |

### Why all of it is PHI

*(Established 2026-09-11. This governs Act 3.1 and every scoping argument after it.)*

**The identity model, stated precisely** *(corrected 2026-09-11 — an earlier draft of this section
had patients holding accounts. They do not.)*:

| Table | Who | Classification |
|---|---|---|
| **Users** | App users: Contoso internal staff **and external healthcare-partner staff** | **Confidential, not PHI.** No protected-individual data lives here |
| **Customers** | The protected individuals themselves — patients | **Strictly PHI** |

Patients are the *subjects* of the data, not *users* of the systems. With that settled, the
scoping move every team reaches for is still foreclosed, on two independent legs, either
sufficient:

1. **The association is the health information.** PHI is individually identifiable information
   relating to health status, the **provision of health care**, or payment for it, held by a
   covered entity. For a care-delivery org, the fact that a named person is a patient *of a
   specialty care organization* is itself information about the provision of care. There is no
   neutral demographics table inside a covered entity's patient system — the record's existence
   is the disclosure.

2. **The cross-app reference IDs are linking identifiers.** Safe Harbor de-identification
   (§164.514(b)(2)) requires removing 18 identifiers, among them *any other unique identifying
   number, characteristic, or code*, and separately bars re-identification codes derived from the
   data. 🔍 **R15** A `patient_id` in `caretasks` that joins to `patient-directory` **is** such an
   identifier. `caretasks` cannot be scoped out for holding no clinical fields; it holds a pointer
   into a PHI system, and the pointer is the identifier. The same applies to `referral-intake`.

**Two user populations, and the harder split is not the obvious one.** The Users table mixes
**internal staff** with **external healthcare-partner staff** — people employed by organizations
Contoso does not control. That is materially harder than a staff/consumer split:

- **No HR feed for partner employees — and this is a different *kind* of failure.** 🏛 Internal
  deprovisioning is a **process failure**: you had the information and fumbled it. That is the
  2008 story in Act 3.2, and in principle a good runbook, a central directory, and a checklist
  fix it. Partner deprovisioning is an **information failure**: the event happens inside an
  organization that has no obligation to tell you, and you may not learn of it for years. **No
  amount of discipline reaches it.** Only architecture does:
  - **Federation** is the real answer — the partner authenticates against their own IdP, so their
    offboarding propagates to you for free, because you never held the credential. (Act 5.1)
  - **Time-bounded access** that expires by default rather than persisting until revoked, for the
    smaller partners who have no IdP to federate with. (Act 5.7)
  - **Access recertification** — periodic re-attestation *by the partner*, which converts an
    unanswerable question into a scheduled one. (Act 8.3)

  📝 That progression — a control you cannot fix with care, only with design — is the strongest
  argument for the Act 5 work anywhere in the project.
- **Delegated administration** becomes a genuine requirement — who creates and removes partner
  accounts, under whose authority, with what evidence.
- **Minimum necessary across an organizational boundary** — a partner's staff should see only the
  patients attached to their own referrals. A cleaner and more forceful case for Act 5.8 than a
  purely internal one.
- **One policy for two risk profiles.** Naive state: partner staff and internal coordinators share
  the same flow, the same MFA posture (none), the same session length, the same recovery path.
- **`referral-intake`'s `FIRST_SUPERUSER`** sits in this table alongside everyone else.

**Consequences, which run through the whole plan:**
- **Act 3.1 collapses in an instructive way.** 📝 The expected finding is *"good, we can scope down
  — only the Rolodex is really in scope."* The analysis destroys that hope and the three buckets
  turn out to be one. That is the moment that feeds 3.4.
- **Act 2.5 is worse than labeled.** Nightly prod restores put **PHI**, not PII, onto unmanaged
  developer endpoints.
- **The Coordinator Console (2.7) joins three PHI systems**, not one plus two auxiliaries.
- **For Contoso, Azure is a business associate across the entire estate** — so every service
  touching any of the three must be BAA-covered, which widens 🔍 **R3** considerably for Acts 6–7.
  *(This does not change our own position: our data is synthetic, so no BAA is required for
  anything we deploy.)*

### The instructional gap

**Every regime above is deliberately technology-neutral, and they are neutral in overlapping ways
that leave a hole exactly where the engineering cost is.** Stacked together they form a rigorous,
mutually-reinforcing description of *what a compliant system is* — and contain almost nothing
about *how to build one*. This is the thesis of the Interlude post; see below.

### Business associate agreements

The *why* belongs in **Act 3.3** — a BAA is the legal mechanism by which HIPAA obligations flow
downhill to vendors and their subcontractors, which is the natural companion to "which regimes
bind us." The *how* belongs in **Act 4.1**, as a scored requirement.

Two hard inputs already known:
- **Auth0 signs a BAA only on enterprise/contracted tiers**, not self-service ones. That is a
  direct input to the Act 4 decision.
- 🔍 **R3** Microsoft offers a BAA covering HIPAA for *in-scope* Azure services under its data
  protection addendum, and the in-scope list is specific — not every Azure service is covered.

📝 **The trigger is the data, not the industry and not the platform.** Readers routinely assume
"healthcare app on cloud ⇒ we need a BAA." No PHI, no business-associate relationship, no BAA.
**This project never needs one**, because the synthetic-data rule keeps us permanently out of
scope — which is worth saying out loud, since it is the clearest demonstration of why that rule is
load-bearing beyond ethics. R3 is therefore subject-matter research for Acts 3.3 and 4.2, **not an
operational gate on deploying anything.** *(Amended 2026-09-11: previously flagged as blocking Act
1. It doesn't.)*

The residual concern is narrower and lands later: designing on services a real covered entity
could not use would teach an architecture that has to be unwound in production. That risk is in
Acts 6–7 (Event Hub, Log Analytics, Blob immutability), not Act 1, where App Service and Azure SQL
are core services.

Either way it points at the same design: **keep PHI out of the identity provider entirely.**
Auth0 holds identifiers and authorization facts; PHI stays in our own databases.

---

## The arc

Eight Acts plus an Interlude. Each ends with a blog post and a ⏸ checkpoint.

### Act 0 — The workbench *(no Azure yet)*

- **0.1** ✅ Remove the speculative scaffold. Start genuinely empty.
- **0.2** ✅ `ms-security-docs` repo: `PLAN.md`, `CLAUDE.workspace.md`, `.gitignore`.
  Workspace memory symlinked to `~/programming/ms-security/CLAUDE.md`.
  **Decided:** memory inherits down the directory tree, settings anchor to the git repo root and
  do not — hence workspace-level `CLAUDE.md`, per-repo `settings.json`.
  **Decided:** no AI attribution in any commit or document. Peter is sole author of record; a
  change record's authorship is a control (ALCOA+ *Attributable*), not a courtesy.
- **0.3** ⏳ **Resume here.** Claude Code configuration, one piece at a time with reasoning for each:
  - ✅ **`.mcp.json` — Microsoft Learn MCP**, added 2026-09-12. Endpoint
    `https://learn.microsoft.com/api/mcp`, **streamable HTTP, no authentication, no charge**
    (verified against Microsoft's own docs, not recalled). Three tools: search documentation,
    fetch a full article, search code samples. Returns `405` in a browser — it is MCP-client-only,
    so do not test it by visiting the URL.

    **Chosen first deliberately.** 16 🔍 rows are blocked on it, and it is the lowest-risk server
    that exists: read-only, unauthenticated, public content. If MCP configuration is going to
    break, break it on something that cannot leak.

    🏛 **Config resolution, verified 2026-09-12 — this extends the 0.2 rule.** `CLAUDE.md`
    inherits from every ancestor directory. **`settings.json` and `.mcp.json` do not** — they
    anchor to the directory Claude launches from. Therefore:
    - **Each repo carries its own `.mcp.json`**, with the servers that repo actually needs. Not
      duplication by laziness: Learn everywhere, **Azure MCP** (`@azure/mcp`) in the app repos
      from Act 1, **Auth0 MCP** (`@auth0/auth0-mcp-server`) only from Act 4.
    - **Launching `claude` from the workspace root loads the memory and zero MCP servers.** A real
      gotcha; know it before it costs an evening.
    - **Project scope over user scope**, deliberately — user scope would inject a Microsoft docs
      server into unrelated projects, and it lives in `~/.claude.json`, which is not version
      controlled and so can be neither a blog artifact nor something a cloner inherits.

    🏛 **Standing rule, set now while it is free: never put a credential in `.mcp.json`.** It is
    checked into a public repo. Nothing in the Learn config is secret, but Act 4's Auth0 server
    will need one, and it goes in an environment variable or `headersHelper` — never inline.
    Same principle as Act 7.1's managed identity: the safest secret is the one that is not there.
    (Workspace hard rule: *never commit secrets*.)
  - `.claude/settings.json` — permissions and env; shared vs `settings.local.json`.
  - `.claude/skills/` — repeatable procedures (deploy runbook, control-matrix update, blog drafting).
  - `.claude/agents/` — subagents (azure-architect, compliance-auditor, security-reviewer).
  - `.claude/rules/` — path-scoped conventions, so each app's team culture loads only for its files.
  - **Hooks** — a `PreToolUse` hook rejecting any `git commit` message containing AI attribution.
    🏛 The project's central distinction, in miniature: **`CLAUDE.md` is context and can be
    ignored; a hook is enforcement and cannot.** Same distinction as Azure Policy vs a written
    standard in Act 7, and as a validated control vs an SOP in Act 8. The lesson is
    *authorship of a change record is a control* — the hook is merely how it's implemented.
  - 🏛 How config resolves, and the decision rule for MCP vs skill vs subagent vs rule vs command.
- **0.4** Local toolchain. Present: `node` 21, `python3`, `docker`, `git` 2.39.
  **Needed for Act 1:** `az` (+ `bicep`), `dotnet`, and a SQL Server client (🔍 **R5** — Azure Data
  Studio is retired; confirm the current recommendation is the VS Code MSSQL extension).
  ✅ **`gh` 2.100.0 installed and authenticated 2026-09-11** — pulled forward from Act 8 to create
  the hub repo. **Deferred:** `psql` and `uv` to Act 2.

**📝 Workbench track, Post W1:** *Setting up an AI-assisted engineering workbench for regulated
cloud work.* Separate series, independent of the security-architecture thread — see Editorial
rule 1.
**⏸ Checkpoint:** config reviewed, tooling installed, nothing in the cloud.

---

### Interlude — The framework with no instructions *(no code, no cloud)*

Publishes second, immediately after Post W1 and before Act 1. Costs nothing to write — the
research is already in the Regulatory Landscape section above — and it motivates everything that
follows.

**The argument.** HIPAA §164.312(b) requires "audit controls" and never says what to log, at what
granularity, or for how long. Part 11 §11.10(e) says the trail must be computer-generated,
time-stamped, and must not obscure previously recorded information — three adjectives, no schema.
The Annex 11 draft adds ten subsections of the same shape. ALCOA+ is nine adjectives. NIST
800-63B is the closest thing to a *how*, and it isn't law and covers only authenticators. Stack
them and you get a complete specification of *what* and a near-total silence on *how*.

The silence is not an oversight. Regulators cannot specify implementations that would be obsolete
in three years, and prescriptive rules get gamed. But the consequence lands entirely on engineers,
who are handed a framework with no worked example.

**Who filled the vacuum, and why it's documentation.** Five categories: compliance-automation SaaS,
enterprise GRC platforms, life-sciences CSV consultancies selling GAMP 5 deliverable packages and
IQ/OQ/PQ protocol sets, SOP-template vendors, and the auditors themselves. The *why* requires no
bad faith:

1. **The regulation is the product spec, and the spec only describes documents.** You can build a
   product that satisfies "maintain a policy." You cannot build one that satisfies "your audit
   trail must not obscure previously recorded information" — that lives in *your* schema,
   describing *your* domain. Documentation generalizes; implementation is irreducibly bespoke.
   Vendors sell what generalizes.
2. **Liability shape.** A policy template carries almost no liability. A tool that writes to a
   regulated system *becomes a system in scope*, and needs its own validation.
3. **Buyer incentive** — the uncomfortable one. The buyer is often not engineering; it is quality,
   legal, or a compliance officer whose personal downside is an audit finding, not a breach.
   Documentation demonstrably reduces *their* risk.
4. **Auditors read paper.** The artifact that survives an inspection is a document, so the market
   optimizes for documents.
5. **The deadline is real** and re-architecting authorization does not fit inside it.

**The turn, which keeps this from being a cheap shot:** this is not a scam. The paperwork layer is
genuinely mandatory and genuinely miserable, and automating it is real value. The sharper claim is
that **the market is complete on the "what" side and nearly empty on the "how" side, and buyers
routinely mistake having bought the first for having done the second.** The rest of this series is
the "how," done once, in public.

🔍 **R7** Company names verified before publication per Editorial rule 4. Categories only until
then.

**📝 Post 1:** *The regulations tell you what. Nobody tells you how.*

---

### Act 1 — Get one thing on the internet

`patient-directory` — oldest app, most Microsoft-shaped, right vehicle for the Azure mental model.
Naive on purpose: a connection string in app settings, a local users table, no MFA.

- **1.1** Azure from zero: signup, what the free tier actually gives you, where the meter starts.
  **Cost guardrails before creating anything** — and 🏛 the guardrail hierarchy, because the
  obvious answer is the weakest one:
  1. **Azure budgets do not stop spend.** They are a notification, not a control. Set them
     anyway; understand what they are. 🔍 **R10** — the entire cost strategy rests on this being
     true, so it gets checked rather than assumed.
  2. **Teardown is the primary control.** Act 1's own verification already requires that the
     resource group can be destroyed and rebuilt from Bicep alone. Once that is true, the cheapest
     environment is a deleted one — and teardown validates the Bicep every time it's used. `test`
     environments live only while in use.
  3. **A minimal Azure Policy, pulled forward from Act 7.5** — deny expensive SKUs and non-approved
     regions. Preventive, not reactive. Front-loads the deepest Microsoft-philosophy point in the
     project rather than stranding it in Act 7.
  4. **SKU choice with hard ceilings.** 🔍 **R1**, 🔍 **R2**.
- **1.2** 🏛 **The Azure mental model**, the core teaching moment of the Act. Entra tenant →
  subscription → resource group → resource. Everything is a resource with a resource ID; the
  portal, the CLI and Bicep are all just clients of **Azure Resource Manager**. ARM is declarative
  and idempotent: you describe desired state, ARM reconciles. RBAC hangs off the resource tree and
  inherits downward. Regions, availability, data residency. Contrast with AWS's flatter account
  model, which is the mental model most people arrive carrying.
  - 🏛 **Critical distinction, stated here and referenced for the rest of the series:** Azure RBAC
    governs the **management plane** — who may restart the App Service, read the Key Vault secret,
    alter the SQL server's config. It says *nothing* about which clinician may see which patient
    row. Those are two authorization systems sharing a vocabulary. The resource-tree model is
    seductive enough that people try to stretch it over application data, and it tears. Act 5.8
    is where we watch it tear.
- **1.3** `az login`, tenant and subscription orientation, first resource group. Naming and tagging
  conventions — which become compliance evidence in Act 3, so tag now.
- **1.4** Scaffold `patient-directory` from `dotnet new ca-sln`. Running locally against SQL Server
  in Docker first.
  - **The bolted-on REST API.** Around 2019 the referral team "needed to look up patients," so
    someone added `/api/v1/` to the Rolodex over a long weekend. Two endpoints, and that is all it
    has ever had:
    - `GET /api/v1/patients?q=` — search
    - `GET /api/v1/patients/{id}` — detail

    **Auth is HTTP Basic, validated against the same `AspNetUsers` table** — a real user's
    username and password, base64-encoded, on every single request. Era-plausible, trivially
    demonstrable, and quietly catastrophic:
    - Credentials ride in a header on every call, so they land in **IIS and App Service request
      logs**. A password store you did not know you had, with no hashing and no retention policy.
    - No token, no expiry, **no revocation**. Changing the password breaks the integration, so
      nobody changes the password. It has been the same since 2019.
    - PBKDF2 verification on *every* request is expensive, which means someone "optimized" it.
      Whatever they did is a finding.
    - It is a **second authentication path**. Act 5.5 must find and remove it, or the strangler
      leaks — the legacy login is gone from the UI while the API still accepts 2019 passwords.

    📝 Every org has one of these. It is never in the architecture diagram, and it is always
    discovered by an auditor rather than by the team.
- **1.5** **Azure SQL Database.** Firewall, TLS enforcement, connection string, first EF Core
  migration. 🏛 **Entra authentication for Azure SQL** — the first appearance of "there is no
  secret to leak," which becomes managed identity in Act 7.1.
- **1.6** **Deploy the same app three ways, in this order** — the repetition *is* the lesson:
  1. **Portal**, clicking through, to see resource shapes and read field labels.
  2. **`az` CLI**, the same thing as imperative commands.
  3. **Bicep**, as declarative desired state — then `what-if` to prove idempotency.

  ARM JSON appears exactly once, as `bicep build` output, to show what is underneath. Nobody
  hand-writes ARM JSON in 2026 and making a reader do it would teach the wrong thing.

  🏛 Why Microsoft pushes you up that ladder, and why Bicep exists on top of ARM JSON. Compute
  choice — App Service vs Container Apps — decided with the trade-off on the table, including
  scale-to-zero, which Container Apps has and App Service does not.
- **1.7** **IP allowlist at the edge, from the very first deployment.** Decided 2026-09-11.
  The apps stay exactly as naive as designed; the allowlist sits in front of them. Act 3 still
  finds every application-level gap, because the allowlist is documented as **scaffolding, not a
  control**, and carries its own control-matrix row saying so. 📝 The distinction between a
  compensating control and a thing you are hiding behind is worth the paragraph it costs — but
  hand-wave it in the post unless it earns more.
  - This also settles DDoS for now. 🔍 **R4** — Azure's platform-level infrastructure DDoS
    protection is believed always-on and free for all Azure services, while Azure DDoS Protection
    (Network tier) runs roughly $3,000/month and is categorically out of scope. 📝 That
    price tag is itself a teaching moment about who those controls are sold to. The honest answer
    at our scale is that **the cheapest DDoS protection is not being a target** — which is the
    same reason we don't publish URLs.
- **~~1.8 Custom domain and managed TLS~~** — **dropped.** A custom domain exists to be findable.

**📝 Post 2a:** *Portal, CLI, Bicep: why Azure makes you climb the same ladder three times* — the
conceptual walkthrough, ~12 min read.
**📝 Post 2b:** *Deploying a 2016 .NET app to Azure, for real* — the hands-on companion.
*(Split because one post covering both would run long. Confirm the split is needed once 2a is
drafted — if it lands under 15 minutes, merge them.)*
**⏸ Checkpoint:** app live behind the allowlist, cost guardrails armed, Bicep reproduces it from
scratch, policy denies a deliberately oversized SKU.

---

### Act 2 — Three apps, three logins *(building the mess faithfully)*

Era order: `referral-intake` (2021), then `caretasks` (2024).

- **2.1** `referral-intake`: FastAPI template on Azure Database for PostgreSQL. Homegrown JWT,
  bcrypt, superuser from an env var, a generous token expiry nobody revisited.
- **2.2** `caretasks`: Next.js + Prisma on its own Postgres. Credentials login bolted on.
- **2.3** Each app gets its **own** resource group, database server, deploy pipeline, users table,
  and its own `test` + `prod` pair. Nothing shared.

- **2.4** **Deliberate divergence.** Documented as "as-found," not as bugs.

  **Change history — two apps have it, in incompatible and differently-broken ways.** Decided
  2026-09-11. Both are **application-level**, so any direct SQL write bypasses them entirely —
  that is a finding for Act 3, not a defect to design around.

  | App | Pattern | How it fails |
  |---|---|---|
  | `patient-directory` | **Proposed:** SQL Server **temporal tables** (system-versioned) on `Patient` and `Insurance` only — added by one keen developer who has since left — plus `created_by`/`modified_by` stamps everywhere else | Era-exact: temporal tables shipped in SQL Server 2016. The history is genuinely un-tamperable by the app and captures **what changed and when, perfectly** — and records **no actor at all**. The `who` exists only where the app happened to stamp `modified_by` into the row. Sophisticated-looking, covers 2 tables of 9, fails ALCOA+ *Attributable* |
  | `referral-intake` | Side table `referral_status_history`, append-only-ish, JSON payload | Captures only the fields someone thought of, **and the actor is almost always `FIRST_SUPERUSER`**. Fails ALCOA+ *Attributable* and *Complete* |
  | `caretasks` | `updatedAt` and nothing else | No history. The honest baseline |

  📝 The newest app has the worst audit story while the 2016 app has the most sophisticated one.
  That inversion is true to life and is a post by itself. Two apps, two different routes to the
  same non-attributable dead end.

  **Login experience — three genuinely different flows, three routes to the same bug class.**

  | | `patient-directory` (2016) | `referral-intake` (2021) | `caretasks` (2024) |
  |---|---|---|---|
  | Flow | Full-page server-rendered POST. Username is `jsmith`, not email — AD habit. A vestigial **"Domain" dropdown** that no longer does anything | JSON API, email + password, token in `localStorage`, no page transition | **Identifier-first**: email → Continue → password on a second screen. Looks modern, looks like Auth0 |
  | Enumeration via | Distinct copy: *"User not found"* vs *"Incorrect password."* Plus a timing side channel — PBKDF2 runs only on a found user | UI shows a generic 400, but the **FastAPI error detail leaks in the response body**. `/docs` publicly exposed | On-screen copy is careful and generic — **the Continue step itself is the oracle**: known email advances, unknown errors |
  | Lockout | Untuned ASP.NET Identity default | None | None |

  📝 The newest, most thoughtfully-designed app has the same bug as the nine-year-old one, reached
  from the opposite direction, and **invisible to anyone auditing error strings** — which is how
  most people audit for this.

  Plus divergent password policies, session lengths, secret handling, and log formats.

- **2.5** **Data handling as-found: the team slings prod data.** Replaces the original
  synthetic-seeding plan. Prod is backed up nightly on cron — the team has *some* discipline —
  and those backups are **restored into `test` and onto developer workbenches**. Given *Why all of
  it is PHI*, this is a top-three finding in all three apps, not just the Rolodex: PHI crossing an
  environment boundary on a schedule, PHI at rest on unmanaged endpoints, and a backup path nobody
  ever classified as a data flow.

  **📝 Deferred post — *Obfuscation won't cut it*.** Scoped in a later discussion; registering the
  thesis so it doesn't get lost. Masking prod data for non-prod is the standard enterprise answer
  and it fails structurally, not occasionally: re-identification through linkage survives masked
  demographics (🔍 **R16**); Safe Harbor's 18 identifiers are hard to fully strip and free text
  defeats the attempt; the masking pipeline itself must read and hold prod data in the clear, so
  it is in scope; masking **fails silently**, producing data that looks masked and isn't; and
  preserving referential integrity so the app still works preserves exactly the linking structure
  that enables re-identification. Expert Determination (§164.514(b)(1)) is the only rigorous
  alternative and carries a recurring qualified-statistician cost per dataset (🔍 **R15**).
  🏛 **Masking is a process that must not fail. Synthetic generation is a structure that cannot.**
  That distinction — preventive control vs. careful procedure — is the same one that runs through
  hooks vs. memory in Act 0 and Azure Policy vs. written standards in Act 7.

  🛑 **Non-negotiable:** the *fiction* is prod data. **Every byte we generate is synthetic.** The
  practice is what's being modeled, not the payload. 📝 That even a teaching project doesn't get
  to touch the real thing is the paragraph that makes the point land.

- **2.6** **As-found architecture: three confidently-wrong documents.** Each team's legacy includes
  someone's attempt to explain the system, and the *genre* encodes the culture:
  - `patient-directory` — a Visio diagram exported to PNG, dated 2019, one box labeled
    `TODO: document this`. Describes a component removed in 2021.
  - `referral-intake` — a Jupyter notebook with a dataflow markdown cell and exploratory SQL.
    Accurate the day it was written; missing three tables now.
  - `caretasks` — an excellent README describing the *intended* architecture, roughly 70% of which
    was built, with nothing marking which 70%.

  📝 This makes 2.6 an **evidence** exercise rather than a drawing exercise: the deliverable is the
  *diff* between what three documents claim and what the code does. That is what "as-found"
  actually means, and it is the first time in the series a control gets built out of a
  discrepancy.

- **2.7** **The Coordinator Console** — `caretasks` builds it, last and deliberately. The newest
  team is enterprise-minded and keen to build something impressive on their platform, and by 2024
  the other two apps already exist to read from. A care coordinator's "my day" view joining:
  - open tasks (`caretasks` own Postgres)
  - patient demographics (`patient-directory`'s SQL Server)
  - pending referrals (`referral-intake`'s Postgres)

  The naive implementation is the one that actually happens — and it is **inconsistent**, because
  the two upstreams offer different affordances:
  - **`patient-directory` → via the Basic-auth REST API** (1.4), because the API exists and using
    it felt like the responsible choice. `caretasks` holds one shared service account's username
    and password in app settings.
  - **`referral-intake` → direct database read** with a shared connection string, because it
    exposes no API anyone asked for.

  Two mechanisms, two *different* attribution failures: every API read is attributed to one
  service user who is not a person, and every direct read is attributed to nobody at all. 📝 The
  team that did the "responsible" thing and the team that did the lazy thing end up in the same
  place, which is the argument for why this is an architecture problem rather than a discipline
  problem. Together they generate, at minimum:
  - cross-app data access with no minimum-necessary enforcement
  - every cross-app read attributed to a service account — so the change history from 2.4 records
    the **wrong actor**, and the two findings compound
  - the stress case for **Act 5.8**: a row-per-patient view where the authorization answer differs
    per row is exactly where role-based collapses
  - a concrete Act 7 test of what changes under managed identity and private endpoints

  Keep it thin: one page, three queries, no pagination, no caching.

  📝 *The dashboard is where your authorization model goes to die.*

**📝 Post 3:** *Three teams, three identity systems: how organizations actually get here*
**⏸ Checkpoint:** three apps live behind the allowlist, three logins, mess documented rather than
fixed.

---

### Act 3 — The reckoning *(assessment; deliberately zero code changes)*

The most valuable Act, and the one most projects skip. 📝 **Frame the post around the persona:**
the enterprise engineer handed this project, assembling the control matrix, discovering the cloud
of regulations they're standing under and exactly how far from compliant they are. Act 3 is the
"oh crap" moment, and it pairs with the Interlude — the Interlude describes the framework, Act 3
is where a real person walks into it.

- **3.1** **Data inventory and classification — two axes, and they answer different questions.**
  Conflating them is the mistake; doing only one of them is worse.

  **Axis 1 — scope, at system and record level.** *Is this in scope?* Binary, and the answer is
  yes, uniformly, for the two reasons in *Why all of it is PHI*. Run it expecting three buckets —
  PII, PHI, neither — and watch them collapse into one. 📝 The post should let the reader make the
  scoping argument first and then take it away; that sequence is the lesson, and skipping to the
  answer wastes it.

  **Axis 2 — exposure, column by column. Still required, and the collapse does not touch it.**
  *Which fields, for which role, in which context?* Not all PHI is equally sensitive: preferred
  name, SSN, diagnosis, and substance-use treatment history are all PHI and are not remotely the
  same thing — the last is not even under the same regime (**42 CFR Part 2** is stricter than
  HIPAA). Six things already in this plan depend on the column-level answer and cannot be decided
  without it:
  - **Minimum necessary** per role — the input to Act 5.8's authorization model
  - **Column-level encryption** choices (7.2)
  - **Which field changes must capture old → new values** (6.1) — not all of them
  - **Log and error-message scrubbing** — which fields must never appear
  - **Accounting of disclosures** — disclosed *what*, which is field-granular
  - **Export and reporting limits** — what may leave the system

  **Employee disclosure, and the ugly case.** In a care organization **staff are frequently also
  patients — of their own employer.** A coordinator viewing a colleague's record, or their own,
  through the normal application UI leaves a trail indistinguishable from legitimate work unless
  field-level classification exists to say otherwise. This is the canonical snooping scenario and
  it is likely what 🔍 **R13** surfaces when it goes hunting for access-control enforcement
  actions — the two threads reinforce each other.

  **Scope honesty:** masking, redaction, and differentiated employee disclosure are **discussed in
  detail, not necessarily demonstrated.** We decide what to build when we reach Act 5.8 and 7.2;
  the analysis is the deliverable here either way.

  Free-text notes get special attention on both axes; they *always* contain identifiers in
  practice, regardless of intent. The 2.5 backup path is a classified data flow here, not an ops
  detail.
- **3.2** **Threat model** (STRIDE) per app, plus the cross-app threats that exist only because
  there are three: credential reuse, orphaned accounts, no central revocation, and the Coordinator
  Console's service credential.
  - 📝 **Sidebar, first person:** the 2008 housing-crash layoff at a residential homebuilder. Ten
    minutes sitting in a vice president's office waiting for the IT lead to arrive — who was, it
    turned out, frantically revoking access across a cloud of non-centralized apps and servers,
    without a list. No central revocation is universally taught as a checkbox; this makes it a
    room with a clock in it. Maps to HIPAA §164.308(a)(3)(ii)(C), termination procedures.

    **The prose has to answer two questions the anecdote raises, or it's just a war story:**

    **How would an auditor ever find out?** Not by hearing the story. By **sampling**. The
    procedure is dull and completely effective: the auditor pulls the **termination list from HR**
    for the audit period, selects a sample, and for each departed person asks for evidence of
    access removal **per system** — a date, and something that proves it. A ticket. A log line. A
    screenshot of a disabled account. Three ways it falls apart, in ascending order of pain:
    1. You cannot produce per-system evidence, because there was never a list of systems.
    2. You produce it, and the revocation timestamps are *after* the termination date.
    3. The auditor runs a current user listing against each system and finds a live account
       belonging to someone who left fourteen months ago.

    The second route in is **access recertification**: if the org claims a quarterly access
    review, the auditor asks for the last four, signed. Missing or unsigned is a finding on its
    own. The third route is the one that actually ruins a year — an incident investigation finds
    the orphaned account in the forensics, at which point it stops being an audit finding and
    becomes a breach report. 🔍 **R9**

    In my case there was no ticket, no list, and no per-system timestamp. An auditor sampling that
    termination would ask when access was removed from each of the several dozen systems, and the
    honest answer was *we don't know, and we don't know what all the systems are.* The finding is
    not "you were slow." It is **"you cannot demonstrate that access was removed"** — which, under
    any evidence-based regime, is treated as equivalent to it not having happened.

    📝 **The first turn:** the cost of that afternoon in 2008 was never the ten minutes. It was
    that the company could not have proved, on any later day, that the access had actually been
    removed. The control is not revocation. The control is *demonstrable* revocation — and that
    distinction is the entire reason Act 6 exists.

    📝 **The second turn, and the reason this sidebar is a setup rather than a conclusion:** every
    instinct that story produces — *get a central directory, write a runbook, keep a list* — is
    aimed at a **process failure**, and it works, because in 2008 the company *had* the
    information and fumbled it. Then look at Contoso's external partner staff, where the departure
    happens inside an organization with no obligation to tell you. That is an **information
    failure**, and none of those instincts touch it. Discipline is not a weaker version of the
    answer; it is the wrong category of answer. The fix is federation, time-bounded access, and
    partner-side recertification — see *Why all of it is PHI*, and Acts 5.1, 5.7 and 8.3.

    **And then what?** The consequences deserve more room than a sidebar — they are
    **Interlude II**, below.
  - Also here: **inconsistent email normalization** across the three apps (plus-addressing handled
    three different ways) means one human can silently create duplicate accounts, or two humans
    can collide. A control-matrix row, and a direct input to 5.4.
- **3.3** **Applicability analysis** — which regimes actually bind Contoso, which we adopt
  voluntarily, and why. **Includes the BAA *why*:** the mechanism by which HIPAA obligations flow
  downhill to vendors and their subcontractors.
- **3.4** **Control matrix.** One row per control, mapped to HIPAA §164.312, Part 11 §11.10 /
  §11.50 / §11.70 / §11.200 / §11.300, Annex 11 draft chapters, ALCOA+ letters, NIST 800-63B AAL.
  Status: met / partial / gap. **Stays live for the rest of the project** as the spine of every
  later decision.
- **3.5** **Risk register** and prioritization.

**📝 Post 4:** *What an auditor would actually find in our three apps*
**⏸ Checkpoint:** `compliance/control-matrix.md` agreed as the project's source of truth.

---

### Interlude II — What a "citation" actually is *(no code, no cloud)*

Publishes as **Post 4.5**, immediately after the reckoning. *(Promoted 2026-09-11 from a sidebar in
Post 4 — it outgrew the slot.)* Interlude I asked *the rules say what, nobody says how*; this asks
*and what happens when you get it wrong*. The reader has just watched a control matrix fill with
gaps and is asking **so what?** — which is the only moment this post lands properly.

**What makes it worth writing:** unlike almost every other compliance topic, this one has
**public primary documents**. We can put real enforcement records on screen and read them, rather
than describing a process abstractly. 🔍 **R11**

**Structure:**

1. **The word is wrong.** Nobody at FDA issues a "citation." The reader arrives with one vague
   term and should leave with four or five precise ones. Opening on the imprecision is the hook.
2. **The ladder, per regulator**, each traced to its primary source: 🔍 **R8**
   - **FDA** — **Form 483** (inspectional observations, not a final determination) → **Warning
     Letter**, *published on FDA's website* → consent decree, injunction, seizure.
   - **HIPAA / OCR** — complaint or breach report → investigation → **civil money penalty** on a
     culpability-tiered structure (did not know / reasonable cause / willful neglect corrected /
     willful neglect uncorrected), or a **Resolution Agreement** with a multi-year **Corrective
     Action Plan** under monitored reporting.
   - **SOC 2 / ISO 27001** — a **qualified opinion** or logged nonconformity. Reaches you
     commercially, as a customer declining to renew.
   - **EU GMP** — **deficiencies** graded critical / major / other; critical can mean a statement
     of non-compliance.
3. **Read one real document, line by line.** A 483 and an OCR resolution agreement. 483 prose has
   a distinctive voice — *"Failure to exercise appropriate controls over computer systems…"* — and
   engineers have never seen what a finding actually looks like. This section is the post.
4. **Filter for our subject.** Find enforcement actions specifically about **access control,
   termination/deprovisioning, and audit trails**, not generic breaches, so the examples connect
   to Acts 5 and 6. Hardest research in the queue and the highest payoff. 🔍 **R13**
5. **What it costs, ultimately.** The headline penalty is rarely the big number. The big numbers
   are the **CAP** — years of mandated process, external monitoring, reporting obligations — plus
   breach-notification costs if it became a breach (individual notice, credit monitoring, media
   notice above 500 individuals, HHS reporting), legal fees, and deals that quietly stop closing.
   🔍 **R12** 🔍 **R14**

   And the tier that hurts is **willful neglect** — precisely where *"we had no way to know"*
   puts you. A documented process that failed sits in a materially better tier than no process at
   all. 📝 That single sentence is the commercial argument for everything in Acts 6 and 8.
6. **The asymmetry, stated honestly.** FDA and OCR publish; SOC 2 qualified opinions and ISO
   nonconformities are private contractual matters that never see daylight. You can study
   healthcare and pharma enforcement in detail and learn almost nothing from commercial audit
   failure — which quietly distorts what the whole industry thinks it knows.

⚠️ **Editorial note.** Editorial rule 4 governs characterizing vendors. Enforcement targets are a
different case — these are public records — but the post **quotes the published document and does
not editorialize beyond it**. Accuracy here matters more than anywhere else in the series.

**📝 Post 4.5:** *What a "citation" actually is, and what it costs*

---

### Act 4 — Buy vs build the identity layer

- **4.1** Requirements derived from Act 3 gaps: SSO, MFA, RBAC, org/tenancy model, audit export and
  retention, **BAA availability and on which tier**, data residency, session policy, step-up auth,
  e-signature support, and a migration path off three password stores. The BAA *how* — the terse
  steps — is a sidebar here: establish covered-entity vs business-associate posture → enumerate
  every vendor that creates, receives, maintains or transmits PHI, *including subcontractors* →
  confirm each offers a BAA and at what tier → execute → record in a vendor register with
  reference and scope → re-review at renewal and on any scope change.

- **4.2** **A brief vendor decision matrix — four entries, chosen for the axes they force:**

  | | Why it's on the list |
  |---|---|
  | **Auth0** | The incumbent by familiarity. The enterprise team knows it well — which is a legitimate operational-risk input, not a bias to apologize for, but is not the same thing as a decision |
  | **Microsoft Entra External ID** | The platform-native answer, which we must argue against **on the record** if we don't pick it |
  | **Keycloak** | Forces the **self-host axis**. Its BAA row reads *"N/A — you are your own business associate,"* converting a contract into an operational burden. The most instructive single cell in the table |
  | **Zitadel** | The SaaS-to-SaaS comparison against Auth0 on features and cost, and it self-hosts too — so it straddles the axis Keycloak anchors |

  **Rows:** **workforce vs. B2B partner identity in one tenant, and delegated administration** —
  internal staff and partner-org staff have different lifecycles and different administrators, and
  this is precisely where Auth0 Organizations, Entra External ID, Keycloak and Zitadel genuinely
  diverge · BAA availability + required tier ·
  PHI boundary · MFA / AAL per 800-63B · audit log
  retention and export path · tenancy and org model · fine-grained authorization story · migration
  path for PBKDF2 and bcrypt · tenant-as-code · Azure integration · cost at our scale ·
  operational burden · exit cost.

  **Plus one row that decides more real procurements than any technical criterion:
  🏛 corporate financial inertia.** We already spend on Azure. Incremental Azure spend flows
  through an existing contract, an existing PO, an existing cost center, and creates work for
  nobody. Opening a new vendor account means procurement, security review, a BAA negotiation,
  a new invoice path, and a new annual renewal to own. That is a real cost, it is rarely written
  down, and it is frequently decisive. 📝 Naming it explicitly — and pricing it — is more honest
  than the feature matrix it usually hides behind, and it is the strongest argument Entra External
  ID has.

- **4.3** Decision plus **ADR-0001**. **The outcome is genuinely open.** *(Amended 2026-09-11 —
  this previously read "Auth0 is pre-selected." It isn't. An ADR that reverse-engineers a
  justification is worse than useless, and Post 5 is only interesting if the decision is real.)*

**📝 Post 5:** *Buy vs build identity in a regulated shop*
**⏸ Checkpoint:** ADR-0001 merged, tenant provisioned with the chosen vendor.

---

### Act 5 — Strangle the auth, one app at a time

The longest Act; likely a four-post series.

- **5.1** Tenant design: **`test` and `prod` tenants** (matching our two-environment reality),
  applications, APIs, connections, Organizations for tenancy, RBAC model, Actions pipeline.
- **5.2** **Tenant-as-code** via the vendor's deploy CLI or Terraform provider. 🏛 Config drift in
  an IdP is an audit finding; clicking in a dashboard is not a control.
- **5.3** **`referral-intake` cuts over first.** *(Amended 2026-09-11 — this previously read
  `caretasks`.)* API-first JWT validation plus machine-to-machine tokens.

  🏛 **Choosing the pilot is a political decision wearing a technical costume**, and the post should
  say so. Engineering wants the **least-friction** app so the proof-of-concept succeeds.
  Leadership wants the **most alarming** app so the budget keeps flowing. Those usually point at
  different apps, and the argument between them is where migrations stall. Here they happen to
  agree, and `referral-intake` wins on both:

  | Least friction | Most alarming |
  |---|---|
  | Smallest codebase, fewest users | **`FIRST_SUPERUSER` from an env var** — a shared god account whose credential sits in config, and to which the audit trail attributes nearly everything |
  | API-first, so there is no session/cookie/SSR login UI to rewrite — you are replacing token *validation*, not a login *experience* | Publicly exposed `/docs`, no lockout at all, a token expiry nobody revisited |
  | Politically unowned: it "escaped from the data team as a POC." Nobody defends it | It is the intake path — the front door for new patient data |

  Two words to an executive — *shared admin account* — fund the rest of Act 5. 📝 We got lucky
  that both criteria agreed; the post should show how you'd argue it when they don't.

  **It also de-risks the longest dependency chain in the plan:** `referral-intake`'s audit-trail
  retrofit (6.1) is meaningless until attribution works, and attribution cannot work until its
  auth is cut over. Doing it first unblocks the most downstream work.
- **5.4** **User migration** — the genuinely hard part. The Users table carries no PHI, so it can
  move to the IdP wholesale; what it *does* carry is two populations with different lifecycles —
  internal staff and external partner staff — which have to land in different organization/tenancy
  structures rather than one flat pool. Then: bulk import vs lazy/trickle migration via a
  custom database connection. ASP.NET Identity's PBKDF2 and FastAPI's bcrypt have different import
  stories; one may force trickle migration. **Account linking**: the same human has three accounts
  across three apps, and reconciling them is a data problem, not an auth problem.

  **Test identities — two tiers, decided 2026-09-11:**

  | Tier | Count | Approach |
  |---|---|---|
  | Bulk synthetic, for the import exercise | dozens–hundreds | **`@example.com`** — RFC 2606 reserved, permanently undeliverable, and self-documenting as fake in any screenshot. Free |
  | Interactive — verification links, MFA enrollment, password reset, step-up | 6–10 | Real, **distinct**, deliverable addresses landing in one inbox. **iCloud+ Hide My Email** recommended (real `@icloud.com` addresses, nothing to normalize together, ~$1/mo). Free alternatives: SimpleLogin, addy.io |

  🛑 **Do not use plus-addressing for the account-linking exercise.** Plus-addresses are
  *normalizable*, the three apps and the IdP may disagree about how, and the exercise becomes a
  debugging session about subaddressing semantics instead of identity reconciliation. The
  disagreement is a **finding** (see 3.2), not a test fixture.

  🔍 **R6** Auth0 free/dev tenants are believed to send through a shared email provider with rate
  limits — fine for 6 accounts, not for bulk, which is another reason the bulk tier is
  undeliverable by design. Confirm at 4.3.

  ❌ HEY is not an option: HEY for You does not support aliases at all; only HEY for Domains does,
  via paid custom-domain "extensions." Plus-addressing on `hey.com` unconfirmed.

- **5.5** `patient-directory`: replace ASP.NET Core Identity with OIDC middleware. The oldest app
  and the hardest cutover — PBKDF2 hashes, the vestigial Domain dropdown, `jsmith`-style usernames
  that must map to email identities.
  - **And remove the Basic-auth API path from 1.4**, converting it to client-credentials. This is
    the single highest-risk step in Act 5: cutting over the *UI* while leaving the API accepting
    2019 passwords means the legacy auth is gone from view and fully alive underneath. 📝 A
    strangler that leaves a second door open hasn't strangled anything.
- **5.6** `caretasks` cuts over last — newest codebase and cleanest OIDC integration, but it owns
  the Coordinator Console and reads two other systems, so it is no longer "least coupled."
  - ⚠️ **Scope fence:** 5.6 cuts over **authentication only**. The Console's *authorization*
    problem is deferred to 5.8, which follows immediately — deliberately, so the ReBAC argument
    lands while the problem is still on screen.
- **5.7** MFA enforcement **differentiated by population** — internal staff and external partner
  staff do not get the same posture — plus **step-up authentication** before PHI access, idle and absolute session
  timeouts — HIPAA §164.312(a)(2)(iii) automatic logoff, Part 11 §11.300.
- **5.8** **Authorization beyond roles**, using the Coordinator Console as the forcing case. RBAC vs
  relationship-based (FGA/ReBAC) for "which clinician may see which patient." This is where the
  management-plane/data-plane distinction from 1.2 pays off: no amount of resource-tree RBAC
  answers a question that differs per row. 🏛 Why "minimum necessary" is an authorization-model
  problem, not a UI problem.

**📝 Posts 6a–6d:** tenant as code · the migration nobody warns you about · step-up auth for PHI ·
the dashboard is where your authorization model goes to die
**⏸ Checkpoints** after each app cuts over.

---

### Act 6 — Audit, evidence, and data integrity

- **6.1** **Application audit trail**: append-only, hash-chained, capturing who / what / when /
  old value → new value. Part 11 §11.10(e) — changes must never obscure prior values. The Annex 11
  draft devotes ~10 subsections to this. Maps directly onto ALCOA+.
  **Two retrofits, not one:**
  - `patient-directory` — temporal tables already give un-tamperable *what and when* on two tables.
    The work is adding the **actor** and extending coverage. A partial asset, not a blank slate.
  - `referral-intake` — the side table has an actor field that is almost always
    `FIRST_SUPERUSER`. The work is making attribution *mean* something, which can't happen until
    5.6 lands.
  - `caretasks` — greenfield, and the Console means its writes span three systems.
- **6.2** **IdP log streams** → Azure Event Hub → Log Analytics. 🔍 **R6** — Auth0 is believed to
  retain logs only ~30 days depending on plan, which would make export mandatory rather than
  optional. Verify per chosen vendor.
- **6.3** **Immutable retention**: Azure Blob immutability policies (WORM), Log Analytics data
  export, retention aligned to the record-retention requirement — and Part 11's rule that audit
  trails are kept at least as long as the records they describe.
- **6.4** Azure Monitor, KQL, workbooks, alerting. Microsoft Sentinel as the SIEM question.
- **6.5** Electronic signatures (Part 11 Subpart C), if Act 3.3 puts them in scope.
- **6.6** **Audit trail *review*.** Annex 11 requires periodic review, not merely capture — an
  unread audit log is a finding. Build the review process and its evidence.

**📝 Post 7:** *An audit trail that would survive an inspection*
**⏸ Checkpoint:** end-to-end evidence chain demonstrable for a single user action.

---

### Act 7 — Platform hardening

Where the duplicated per-app infrastructure becomes a real platform layer.

- **7.1** **Secrets**: Key Vault plus managed identity; eliminate every connection string from app
  settings. 🏛 Managed identity is the biggest philosophical difference in how Azure wants you to
  authenticate workloads — there is no secret to leak. Act 1.5's Entra auth for Azure SQL was the
  first taste; this is the full meal.
- **7.2** **Encryption at rest — two different stories, which is why the SQL Server choice earns
  its keep.** Azure SQL: TDE on by default, CMK optional, what CMK actually buys and what it costs
  operationally. Postgres: a different model with different defaults. Plus TLS enforcement and
  column-level encryption for the most sensitive PHI.
- **7.3** **Network**: VNet integration, private endpoints, databases off the public internet
  entirely, Front Door and WAF. **The Act 1.7 IP allowlist gets replaced by real edge controls
  here** — and the control-matrix row that called it scaffolding gets closed out honestly.
- **7.4** **Workload identity**: GitHub Actions → Azure via OIDC federation. No stored cloud
  credentials anywhere.
- **7.5** **Governance**: Azure Policy as preventive control (expanded from the minimal cost-control
  policy in Act 1.1), Defender for Cloud, management groups, Cloud Adoption Framework landing
  zones. 🏛 Policy-as-preventive-control is how Azure expects compliance to be *enforced* rather
  than *audited after the fact*.
- **7.6** Backup, DR, RPO/RTO, and an actually-tested restore — **including who may restore, and to
  where**, which is the control that Act 2.5's nightly cron so thoroughly lacked.

**📝 Post 8:** *From three snowflakes to a platform*
**⏸ Checkpoint:** control matrix re-run; gaps closed or consciously accepted.

---

### Act 8 — Validation and the evidence pack *(depth optional)*

- **8.1** CI/CD with change control: PR gates, environment promotion, signed commits, SBOM.
- **8.2** CSV / CSA: URS, FS, DS, IQ/OQ/PQ, requirements traceability matrix, GAMP 5
  categorization. 🏛 Why FDA's Computer Software Assurance shift matters — risk-based testing
  instead of documentation theater. Closes the loop with the Interlude post.
- **8.3** Access recertification, periodic review cadence, penetration test.
- **8.4** Assemble the inspection-ready evidence pack.

**📝 Post 9:** *What "validated" actually means, and what it costs*

---

## Discovered as we go

Deliberately unplanned; added when a real need appears, each with its own post:

- Caching — Azure Cache for Redis (session store? read-through? both?)
- Search — Azure AI Search, and the problem of indexing PHI
- PII/PHI detection — Azure AI Language / Text Analytics for health, for those free-text notes
- Rate limiting and abuse prevention
- Feature flags and safe rollout during the auth cutover

---

## Buy-vs-build register

One ADR each in `decisions/`, written when we reach it:

| Concern | Leading options |
|---|---|
| Identity provider | Auth0 · Entra External ID · Keycloak · Zitadel |
| Audit log | Hash-chain in-database (build) · OpenTelemetry + Log Analytics · purpose-built ledger |
| Secrets | Azure Key Vault · HashiCorp Vault |
| Authorization | Auth0 FGA · OpenFGA self-hosted · SpiceDB · app-level RBAC |
| Search | Azure AI Search · Postgres FTS · self-hosted OpenSearch |
| SIEM | Microsoft Sentinel · Log Analytics alone · third party |

---

## Verification

How we know each Act actually worked:

- **Act 0** — `claude` starts clean in each repo; `/context` lists the expected memory files;
  `/doctor` reports no config errors; the Microsoft Learn MCP server answers a live Azure question
  and closes at least one 🔍 row from this document.
- **Act 1** — App reachable over HTTPS **from an allowlisted address only**. `az deployment group
  what-if` reports **no changes** against deployed state, proving the Bicep is the source of truth.
  The resource group can be deleted and rebuilt from Bicep alone. A budget alert fires on a test
  threshold. Azure Policy blocks a deliberately oversized SKU.
- **Act 2** — Three apps, three distinct login flows, three databases (one SQL Server, two
  Postgres). An account in one app demonstrably cannot authenticate to another. Each app's
  enumeration path is reproducible. The Coordinator Console renders a joined view, and its
  database reads are attributable to nobody.
- **Act 3** — Control matrix reviewed line by line; every "gap" row traceable to a specific
  citation and a risk-register entry. The 2.6 documentation diff is written down.
- **Act 4** — ADR-0001 states the decision, the alternatives, and reasoning a skeptic would need —
  including the financial-inertia row, priced.
- **Act 5** — Per app: login via the IdP succeeds; the legacy login path is *removed*, not hidden;
  **`patient-directory`'s Basic-auth API rejects a valid 2019 username/password pair**;
  a migrated user authenticates with their original password; MFA is enforced; session timeout
  observed empirically. One human's three accounts are linked to one identity.
- **Act 6** — Take one user action and produce the complete evidence chain: app audit row → IdP
  log → Log Analytics → immutable archive. Demonstrate that a prior value cannot be obscured and
  an audit row cannot be deleted.
- **Act 7** — Databases unreachable from the public internet (proven). No secret in any app
  setting. The Act 1.7 allowlist is gone, replaced by real controls. Restore from backup succeeds,
  and an unauthorized restore is blocked.
- **Act 8** — Traceability matrix links each requirement to a test and to evidence.

---

## Open verification queue

Every 🔍 **R*n*** tag in this document resolves here. A tagged claim may shape the plan; it may not
enter a post, a control-matrix row, or an ADR until the row below is closed with a source. Most are
blocked on the Microsoft Learn MCP server (Act 0.3) — which is the concrete argument for doing that
first, and Act 0's verification criterion is that it closes at least one row.

| # | Question | Blocks | Source |
|---|---|---|---|
| **R1** | Azure SQL serverless auto-pause behavior, and the current free-tier grant | Act 1.1 cost model, Act 1.5 SKU choice | Learn MCP |
| **R2** | Azure Database for PostgreSQL Flexible Server stop/start window | Act 1.1, Act 2 cost model | Learn MCP |
| **R3** | Microsoft BAA coverage and the in-scope Azure service list | Act 3.3, Act 4.2, and service selection in Acts 6–7. **Not a gate on Act 1** — synthetic data means no BAA is ever required here | Learn MCP |
| **R4** | Azure platform-level DDoS protection (always-on, free?) vs DDoS Protection Network tier pricing | Act 1.7, Act 7.3 | Learn MCP |
| **R5** | Current recommended SQL Server client tooling now that Azure Data Studio is retired | Act 0.4 | Learn MCP |
| **R6** | Auth0 dev-tenant email sending limits; log retention by plan | Act 5.4 test identities, Act 6.2 export design | Vendor docs, at 4.3 |
| **R7** | Compliance-vendor characterizations — who sells what, accurately | Interlude post (Editorial rule 4) | Vendor sites, analyst coverage |
| **R8** | The escalation ladder per regulator: FDA 483 → Warning Letter → consent decree; OCR complaint → CMP or Resolution Agreement; EU GMP deficiency grading. What triggers each rung, expected response, timelines | Interlude II §2 | FDA, HHS/OCR, EMA |
| **R11** | Confirm the public primary-document sources exist and are currently accessible: FDA Warning Letter database, OCR enforcement / resolution agreements, the HHS breach portal (500+ individuals), EudraGMDP non-compliance register | Interlude II — the whole post depends on this | Direct |
| **R12** | **Current inflation-adjusted HIPAA civil money penalty tiers.** Adjusted annually — never quote from memory | Interlude II §5 | eCFR / HHS |
| **R13** | Real enforcement actions specifically about **access control, termination/deprovisioning, or audit trails** — not generic breaches. Hardest row in the queue, highest payoff | Interlude II §4, and it validates Acts 5–6 | FDA WL database, OCR actions |
| **R14** | Typical CAP duration and what monitored reporting actually entails in practice | Interlude II §5 | OCR resolution agreements |
| **R15** | The 18 Safe Harbor identifiers verbatim (§164.514(b)(2)), the bar on derived re-identification codes, and what Expert Determination (§164.514(b)(1)) actually requires and costs | *Why all of it is PHI*; Act 3.1; the obfuscation post | eCFR, HHS de-identification guidance |
| **R16** | Re-identification-by-linkage evidence. Sweeney's *Simple Demographics Often Identify People Uniquely* claims ~87% of the US population unique on {5-digit ZIP, gender, DOB}; Golle (2006) revised it to ~63% on 2000 census data. **Cite both and the dispute** — do not quote a single figure | The obfuscation post | Primary papers |
| **R9** | Standard audit procedure for termination sampling and access recertification — sample sizes, evidence accepted | Act 3.2, Act 8.3 | Audit guidance |
| **R10** | Confirm Azure budgets alert but do not enforce, and identify what *does* hard-stop spend (if anything) | Act 1.1 — the whole cost strategy | Learn MCP |

## Sources

- [HIPAA Security Rule update delayed until 2027 — Clark Hill](https://www.clarkhill.com/news-events/news/hipaa-security-rule-update-delayed-until-2027/)
- [Proposed HIPAA Security Rule update — Compliancy Group](https://compliancy-group.com/proposed-hipaa-security-rule-update-2026/)
- [Audit trails for 21 CFR Part 11 & Annex 11 — IntuitionLabs](https://intuitionlabs.ai/articles/audit-trails-21-cfr-part-11-annex-11-compliance)
- [ALCOA & ALCOA+ principles — TotalLab](https://totallab.com/resources/alcoa-principles/)
- [EU GMP Annex 11 (Draft 2025) — ECA Academy](https://www.gmp-compliance.org/guidelines/gmp-guideline/eu-gmp-annex-11-draft-2025-computerised-systems)
- [Annex 11 revision: computerised systems, data integrity and AI — MFLRC](https://mflrc.com/article/eu-gmp-annex-11-revision-2026)
- [Auth0 HIPAA compliance: BAA, PHI, configuration — Accountable](https://www.accountablehq.com/post/auth0-hipaa-compliance-baa-phi-and-configuration-guide)
- [Can I create email aliases? — HEY Help](https://help.hey.com/article/928-can-i-create-email-aliases)
- [Claude Code — memory and CLAUDE.md resolution](https://code.claude.com/docs/en/memory)
- [Claude Code — settings files and precedence](https://code.claude.com/docs/en/settings)
- [Microsoft Learn MCP Server developer reference](https://learn.microsoft.com/en-us/training/support/mcp-developer-reference)
- [Auth0 MCP Server](https://github.com/auth0/auth0-mcp-server)
- [Azure MCP Server — get started](https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/get-started)
- [jasontaylordev/CleanArchitecture](https://github.com/jasontaylordev/CleanArchitecture)
- [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)
