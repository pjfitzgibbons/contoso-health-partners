# PLAN — From Three Legacy Apps to a Compliant Identity Platform on Azure

**Status:** Act 0.3 — Claude Code configuration · Last updated 2026-09-10

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
its own user table. Each holds PII; two hold data that is arguably PHI. None has an audit trail.
This is not a strawman — it is the median state of a company that has been shipping for a decade.

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

---

## Repo layout

Four repos, matching the "different teams, different eras" story. `~/programming/ms-security/` is
a **workspace, not a repo** — it holds the four clones plus the shared `CLAUDE.md` symlink.

| Repo | Story | Stack | Era |
|---|---|---|---|
| `ms-security-docs` | Our repo. Plan, blog drafts, ADRs, compliance matrix, threat models, runbooks. | Markdown | now |
| `caretasks` | Care-coordinator task tracker. Contractor-built, newest, nobody left who wrote it. | TypeScript / Next.js / Prisma | ~2024 |
| `patient-directory` | The Rolodex. Oldest, owned by the "enterprise" team, grudgingly ported forward. | C# / ASP.NET Core / EF Core | ~2016 |
| `referral-intake` | Escaped from the data team as a POC and became load-bearing. | Python / FastAPI / SQLModel | ~2021 |

**Config resolution drove this layout.** `CLAUDE.md` loads from the working directory *and every
directory above it*, so a workspace-level file is inherited by all four repos for free.
`settings.json` does **not** inherit — it anchors to the git repo root — so each repo carries its
own. That asymmetry is why the shared memory lives at workspace level and per-repo settings live
per repo.

**Infra starts deliberately duplicated.** In Acts 1–2 each app repo carries its own `infra/`
Bicep, diverging in style, because that is what actually happens. Extracting a shared platform
layer in Act 7 is itself a lesson, and a post.

**Candidate open-source bases** — all permissively licensed, all Postgres-capable, all shipping
their own bespoke auth, which is exactly the naive starting state we want. Verified at the start
of each Act rather than trusted from this list:

- `caretasks` — a Next.js + Prisma todo starter; we bolt on a credentials login and a `users` table.
- `patient-directory` — [`jasontaylordev/CleanArchitecture`](https://github.com/jasontaylordev/CleanArchitecture),
  scaffolded via `dotnet new ca-sln --database postgresql`. Ships ASP.NET Core Identity: local
  passwords, PBKDF2 hashes, no MFA. A perfect period piece.
- `referral-intake` — [`fastapi/full-stack-fastapi-template`](https://github.com/fastapi/full-stack-fastapi-template).
  Ships SQLModel + Postgres + homegrown JWT + bcrypt + a `FIRST_SUPERUSER` env var.

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

### An early constraint

Auth0 signs a **BAA only on enterprise/contracted tiers**, not self-service ones. That is a hard
input to the Act 4 buy-vs-build decision. It also points at the right design regardless: **keep
PHI out of the identity provider entirely.** Auth0 holds identifiers and authorization facts; PHI
stays in our Postgres.

---

## The arc

Eight Acts. Each ends with a blog post and a ⏸ checkpoint.

### Act 0 — The workbench *(no Azure yet)*

- **0.1** ✅ Remove the speculative scaffold. Start genuinely empty.
- **0.2** ✅ `ms-security-docs` repo: `PLAN.md`, `CLAUDE.workspace.md`, `.gitignore`.
  Workspace memory symlinked to `~/programming/ms-security/CLAUDE.md`.
  **Decided:** memory inherits down the directory tree, settings anchor to the git repo root and
  do not — hence workspace-level `CLAUDE.md`, per-repo `settings.json`.
  **Decided:** no AI attribution in any commit or document. Peter is sole author of record; a
  change record's authorship is a control (ALCOA+ *Attributable*), not a courtesy.
- **0.3** ⏳ **Resume here.** Claude Code configuration, one piece at a time with reasoning for each:
  - `.claude/settings.json` — permissions and env; shared vs `settings.local.json`.
  - `.mcp.json` — **Microsoft Learn MCP** (`https://learn.microsoft.com/api/mcp`, HTTP, no auth)
    so Azure answers come from current docs rather than recalled knowledge. **Auth0 MCP**
    (`@auth0/auth0-mcp-server`) arrives in Act 4; **Azure MCP** (`@azure/mcp`) in Act 1.
  - `.claude/skills/` — repeatable procedures (deploy runbook, control-matrix update, blog drafting).
  - `.claude/agents/` — subagents (azure-architect, compliance-auditor, security-reviewer).
  - `.claude/rules/` — path-scoped conventions, so each app's team culture loads only for its files.
  - **Hooks** — a `PreToolUse` hook rejecting any `git commit` message containing AI attribution.
    🏛 The first appearance of the project's central distinction: `CLAUDE.md` is *context* and can
    be ignored; a hook is *enforcement* and cannot. Same distinction as Azure Policy vs a written
    standard in Act 7, and as a validated control vs an SOP in Act 8.
  - 🏛 How config resolves, and the decision rule for MCP vs skill vs subagent vs rule vs command.
- **0.4** Local toolchain. Present: `node` 21, `python3`, `docker`, `git` 2.39. Missing and needed:
  `az` (+ `bicep`), `gh`, `dotnet`, `psql`, `uv` — installed as each Act needs them, not upfront.

**📝 Post 0:** *Setting up an AI-assisted engineering workbench for regulated cloud work*
**⏸ Checkpoint:** config reviewed, tooling installed, nothing in the cloud.

---

### Act 1 — Get one thing on the internet

One app, one database, deployed. Naive on purpose: public endpoints, a connection string in app
settings, a local users table.

- **1.1** Azure from zero: signup, what the free tier actually gives you, where the meter starts.
  Cost guardrails — budget and alert — **before** creating anything.
- **1.2** 🏛 **The Azure mental model**, the core teaching moment of the Act. Entra tenant →
  subscription → resource group → resource. Everything is a resource with a resource ID; the
  portal, the CLI and Bicep are all just clients of **Azure Resource Manager**. ARM is declarative
  and idempotent: you describe desired state, ARM reconciles. RBAC hangs off the resource tree and
  inherits downward. Regions, availability, data residency. Contrast with AWS's flatter account
  model, which is the mental model most people arrive carrying.
- **1.3** `az login`, tenant and subscription orientation, first resource group. Naming and tagging
  conventions — which become compliance evidence in Act 3, so tag now.
- **1.4** Scaffold `caretasks` from a Next.js + Prisma todo starter. Single-user, running locally
  first.
- **1.5** Azure Database for PostgreSQL Flexible Server. Firewall, SSL enforcement, connection
  string, first migration.
- **1.6** **Deploy the same app three ways, in this order** — the repetition *is* the lesson:
  1. **Portal**, clicking through, to see resource shapes and read field labels.
  2. **`az` CLI**, the same thing as imperative commands.
  3. **Bicep**, as declarative desired state — then `what-if` to prove idempotency.

  🏛 Why Microsoft pushes you up that ladder, and why Bicep exists on top of ARM JSON. Compute
  choice — App Service vs Container Apps — decided with the trade-off on the table.
- **1.7** Custom domain and managed TLS *(optional, only if it earns its place)*.

**📝 Post 1:** *Deploying an app to Azure three ways: portal, CLI, and Bicep*
**⏸ Checkpoint:** app live, cost alerts armed, Bicep reproduces it from scratch.

---

### Act 2 — Three apps, three logins *(building the mess faithfully)*

- **2.1** `patient-directory`: .NET Clean Architecture on Postgres, ASP.NET Core Identity. Local
  passwords, PBKDF2, no MFA, untuned lockout.
- **2.2** `referral-intake`: FastAPI template on Postgres. Homegrown JWT, bcrypt, superuser from an
  env var, a generous token expiry nobody revisited.
- **2.3** Each app gets its **own** resource group, Postgres server, deploy pipeline, users table.
  Nothing shared.
- **2.4** **Deliberate divergence** — different password policies, session lengths, secret handling,
  log formats. Documented as "as-found," not as bugs.
- **2.5** Seed realistic **synthetic** PII/PHI. 🏛 Why synthetic data generation is itself a
  regulated-industry skill, and why real data never touches non-prod.
- **2.6** As-found architecture diagram and data-flow map.

**📝 Post 2:** *Three teams, three identity systems: how organizations actually get here*
**⏸ Checkpoint:** three apps live, three logins, mess documented rather than fixed.

---

### Act 3 — The reckoning *(assessment; deliberately zero code changes)*

The most valuable Act, and the one most projects skip.

- **3.1** **Data inventory and classification**, column by column: PII, PHI, or neither. Free-text
  notes get special attention — they *always* contain PHI in practice, regardless of intent.
- **3.2** **Threat model** (STRIDE) per app, plus the cross-app threats that exist only because
  there are three: credential reuse, orphaned accounts, no central revocation.
- **3.3** **Applicability analysis** — which regimes actually bind Contoso, which we adopt
  voluntarily, and why.
- **3.4** **Control matrix.** One row per control, mapped to HIPAA §164.312, Part 11 §11.10 /
  §11.50 / §11.70 / §11.200 / §11.300, Annex 11 draft chapters, ALCOA+ letters, NIST 800-63B AAL.
  Status: met / partial / gap. **Stays live for the rest of the project** as the spine of every
  later decision.
- **3.5** **Risk register** and prioritization.

**📝 Post 3:** *What an auditor would actually find in our three apps*
**⏸ Checkpoint:** `compliance/control-matrix.md` agreed as the project's source of truth.

---

### Act 4 — Buy vs build the identity layer

- **4.1** Requirements derived from Act 3 gaps: SSO, MFA, RBAC, org/tenancy model, audit export and
  retention, BAA availability, data residency, session policy, step-up auth, e-signature support,
  and a migration path off three password stores.
- **4.2** Honest evaluation, including the open-source options: **Auth0/Okta**, **Microsoft Entra
  External ID** (the obvious Microsoft-way answer, which we must argue against on the record),
  **Keycloak**, **Zitadel**, **Ory**, **Authentik**, **Logto**. Scored against 4.1 — including the
  operational cost of self-hosting an IdP in a regulated environment, which is where "free" open
  source stops being free.
- **4.3** Decision plus **ADR-0001**. Auth0 is pre-selected; the exercise is writing the argument
  well enough to satisfy a skeptic, or an auditor.

**📝 Post 4:** *Buy vs build identity in a regulated shop — and why we didn't pick the Microsoft option*
**⏸ Checkpoint:** ADR-0001 merged, Auth0 tenant provisioned.

---

### Act 5 — Strangle the auth, one app at a time

The longest Act; likely a four-post series.

- **5.1** Auth0 tenant design: dev/stage/prod tenants, applications, APIs, connections,
  Organizations for tenancy, RBAC model, Actions pipeline.
- **5.2** **Tenant-as-code** via Auth0 Deploy CLI or the Terraform provider. 🏛 Config drift in an
  IdP is an audit finding; clicking in a dashboard is not a control.
- **5.3** `caretasks` first (newest, least coupled): OIDC Authorization Code + PKCE, sessions,
  logout, token storage.
- **5.4** **User migration** — the genuinely hard part. Bulk import vs lazy/trickle migration via a
  custom database connection. ASP.NET Identity's PBKDF2 and FastAPI's bcrypt have different import
  stories; one may force trickle migration. **Account linking**: the same human has three accounts
  across three apps, and reconciling them is a data problem, not an auth problem.
- **5.5** `patient-directory`: replace ASP.NET Core Identity with OIDC middleware.
- **5.6** `referral-intake`: API-first JWT validation plus machine-to-machine tokens.
- **5.7** MFA enforcement, **step-up authentication** before PHI access, idle and absolute session
  timeouts — HIPAA §164.312(a)(2)(iii) automatic logoff, Part 11 §11.300.
- **5.8** Authorization beyond roles: RBAC vs relationship-based (Auth0 FGA) for "which clinician
  may see which patient." 🏛 Why "minimum necessary" is an authorization-model problem, not a UI
  problem.

**📝 Posts 5a–5d:** tenant as code · the migration nobody warns you about · step-up auth for PHI · RBAC vs ReBAC
**⏸ Checkpoints** after each app cuts over.

---

### Act 6 — Audit, evidence, and data integrity

- **6.1** **Application audit trail**: append-only, hash-chained, capturing who / what / when /
  old value → new value. Part 11 §11.10(e) — changes must never obscure prior values. The Annex 11
  draft devotes ~10 subsections to this. Maps directly onto ALCOA+.
- **6.2** **Auth0 Log Streams** → Azure Event Hub → Log Analytics. Auth0 retains logs only ~30 days
  depending on plan, so export is mandatory rather than optional.
- **6.3** **Immutable retention**: Azure Blob immutability policies (WORM), Log Analytics data
  export, retention aligned to the record-retention requirement — and Part 11's rule that audit
  trails are kept at least as long as the records they describe.
- **6.4** Azure Monitor, KQL, workbooks, alerting. Microsoft Sentinel as the SIEM question.
- **6.5** Electronic signatures (Part 11 Subpart C), if Act 3.3 puts them in scope.
- **6.6** **Audit trail *review*.** Annex 11 requires periodic review, not merely capture — an
  unread audit log is a finding. Build the review process and its evidence.

**📝 Post 6:** *An audit trail that would survive an inspection*
**⏸ Checkpoint:** end-to-end evidence chain demonstrable for a single user action.

---

### Act 7 — Platform hardening

Where the duplicated per-app infrastructure becomes a real platform layer.

- **7.1** **Secrets**: Key Vault plus managed identity; eliminate every connection string from app
  settings. 🏛 Managed identity is the biggest philosophical difference in how Azure wants you to
  authenticate workloads — there is no secret to leak.
- **7.2** **Encryption at rest**: Postgres encryption, customer-managed keys, TLS enforcement,
  column-level encryption for the most sensitive PHI. What CMK actually buys, and what it costs
  operationally.
- **7.3** **Network**: VNet integration, private endpoints, Postgres off the public internet
  entirely, Front Door and WAF.
- **7.4** **Workload identity**: GitHub Actions → Azure via OIDC federation. No stored cloud
  credentials anywhere.
- **7.5** **Governance**: Azure Policy as preventive control, Defender for Cloud, management
  groups, Cloud Adoption Framework landing zones. 🏛 Policy-as-preventive-control is how Azure
  expects compliance to be *enforced* rather than *audited after the fact* — the deepest
  Microsoft-philosophy point in the project.
- **7.6** Backup, DR, RPO/RTO, and an actually-tested restore.

**📝 Post 7:** *From three snowflakes to a platform*
**⏸ Checkpoint:** control matrix re-run; gaps closed or consciously accepted.

---

### Act 8 — Validation and the evidence pack *(depth optional)*

- **8.1** CI/CD with change control: PR gates, environment promotion, signed commits, SBOM.
- **8.2** CSV / CSA: URS, FS, DS, IQ/OQ/PQ, requirements traceability matrix, GAMP 5
  categorization. 🏛 Why FDA's Computer Software Assurance shift matters — risk-based testing
  instead of documentation theater.
- **8.3** Access recertification, periodic review cadence, penetration test.
- **8.4** Assemble the inspection-ready evidence pack.

**📝 Post 8:** *What "validated" actually means, and what it costs*

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
| Identity provider | Auth0 · Entra External ID · Keycloak · Zitadel · Ory |
| Audit log | Postgres hash-chain (build) · OpenTelemetry + Log Analytics · purpose-built ledger |
| Secrets | Azure Key Vault · HashiCorp Vault |
| Authorization | Auth0 FGA · OpenFGA self-hosted · SpiceDB · app-level RBAC |
| Search | Azure AI Search · Postgres FTS · self-hosted OpenSearch |
| SIEM | Microsoft Sentinel · Log Analytics alone · third party |

---

## Verification

How we know each Act actually worked:

- **Act 0** — `claude` starts clean in each repo; `/context` lists the expected memory files;
  `/doctor` reports no config errors; the Microsoft Learn MCP server answers a live Azure question.
- **Act 1** — App reachable over HTTPS. `az deployment group what-if` reports **no changes**
  against deployed state, proving the Bicep is the source of truth. The resource group can be
  deleted and rebuilt from Bicep alone. A budget alert fires on a test threshold.
- **Act 2** — Three URLs, three distinct logins, three databases. An account in one app
  demonstrably cannot authenticate to another.
- **Act 3** — Control matrix reviewed line by line; every "gap" row traceable to a specific
  citation and a risk-register entry.
- **Act 4** — ADR-0001 states the decision, the alternatives, and reasoning a skeptic would need.
- **Act 5** — Per app: login via Auth0 succeeds; the legacy login path is *removed*, not hidden; a
  migrated user authenticates with their original password; MFA is enforced; session timeout
  observed empirically.
- **Act 6** — Take one user action and produce the complete evidence chain: app audit row → Auth0
  log → Log Analytics → immutable archive. Demonstrate that a prior value cannot be obscured and
  an audit row cannot be deleted.
- **Act 7** — Postgres unreachable from the public internet (proven). No secret in any app setting.
  Azure Policy blocks a deliberately non-compliant deployment. Restore from backup succeeds.
- **Act 8** — Traceability matrix links each requirement to a test and to evidence.

---

## Sources

- [HIPAA Security Rule update delayed until 2027 — Clark Hill](https://www.clarkhill.com/news-events/news/hipaa-security-rule-update-delayed-until-2027/)
- [Proposed HIPAA Security Rule update — Compliancy Group](https://compliancy-group.com/proposed-hipaa-security-rule-update-2026/)
- [Audit trails for 21 CFR Part 11 & Annex 11 — IntuitionLabs](https://intuitionlabs.ai/articles/audit-trails-21-cfr-part-11-annex-11-compliance)
- [ALCOA & ALCOA+ principles — TotalLab](https://totallab.com/resources/alcoa-principles/)
- [EU GMP Annex 11 (Draft 2025) — ECA Academy](https://www.gmp-compliance.org/guidelines/gmp-guideline/eu-gmp-annex-11-draft-2025-computerised-systems)
- [Annex 11 revision: computerised systems, data integrity and AI — MFLRC](https://mflrc.com/article/eu-gmp-annex-11-revision-2026)
- [Auth0 HIPAA compliance: BAA, PHI, configuration — Accountable](https://www.accountablehq.com/post/auth0-hipaa-compliance-baa-phi-and-configuration-guide)
- [Claude Code — memory and CLAUDE.md resolution](https://code.claude.com/docs/en/memory)
- [Claude Code — settings files and precedence](https://code.claude.com/docs/en/settings)
- [Microsoft Learn MCP Server developer reference](https://learn.microsoft.com/en-us/training/support/mcp-developer-reference)
- [Auth0 MCP Server](https://github.com/auth0/auth0-mcp-server)
- [Azure MCP Server — get started](https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/get-started)
- [jasontaylordev/CleanArchitecture](https://github.com/jasontaylordev/CleanArchitecture)
- [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)
