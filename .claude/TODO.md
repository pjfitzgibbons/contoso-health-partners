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

## Control-matrix rows waiting for a control matrix

No matrix file exists yet, and the no-speculative-files rule says not to create one for a single
row. Park them here; move them when the matrix is born.

- [ ] **A WordPress application password cannot be scoped.** It inherits every capability of its
      user, with no publish-only or read-only variant. The password created on 2026-09-12 to post
      a blog draft also carried `install_plugins`, `delete_plugins`, `activate_plugins` and
      `manage_options` — and on 2026-10-10 it is what deleted five plugins and installed Koko
      Analytics. Mitigated 2026-10-10 by a separate `wp_publisher` role and account; the admin
      credential moved to `netrc-admin` and is now passed explicitly. The underlying platform
      weakness is not fixable and belongs in the matrix as an accepted risk with a compensating
      control.
- [ ] 📝 **A refused read can arrive as a successful empty answer.** A WordPress credential without
      `moderate_comments` querying `/wp/v2/comments?status=hold` gets `200`, `[]` and
      `X-WP-Total: 0` — not a 403. The filter is silent, so an empty result is indistinguishable
      from a real zero, and any tool that trusts the response reports "no spam" when it means "no
      visibility". Measured 2026-10-10 against both credentials. `wp_report.py` now keys those
      counts on the capability rather than the response. The general rule — *check the permission,
      not the payload* — is the same shape as the L1 finding that config failures are silent, and
      belongs in the same family of posts.
- [ ] 📝 **WordPress uses `post_author` as both the access-control subject and the public byline.**
      So a least-privilege publishing identity and a human byline are in direct conflict: either
      the service account owns the posts and appears as their author, or it does not own them and
      needs `edit_others_posts` to touch them. Measured 2026-10-10 with a role holding
      `edit_posts` + `edit_published_posts` but not `edit_others_posts`: a no-op update of W1
      returned 403, an edit-context post listing returned 0 rows, and the real `wp_publish.py`
      failed on its pre-update read. Resolved by granting `edit_others_posts` and keeping the
      byline correct, since authorship of record is the control this project is about. Generalises
      past WordPress — any system that conflates ownership with attribution forces this trade.
      Strong L-track material.
- [ ] **Koko Analytics cookieless mode reads the client IP.** `xxh64(daily_seed + user_agent + ip)`
      with a 16-byte seed rotated daily and session files wiped daily; the IP is never stored.
      Chosen 2026-10-10 over the cookie method, which never touches the IP but would require a
      consent banner. Worth a row because it is a real processing-of-personal-data decision taken
      deliberately, and because Koko's own UI calls the *cookie* method the more privacy-friendly
      of the two.
- [ ] **The fingerprint session directory is protected by `.htaccess` only.** Apache-specific; on
      nginx the deny block does nothing. Filenames are unguessable hashes and the directory ships
      an empty `index.html`, so exposure is low. Confirm which server is in front of the site.

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
- [x] **Check whether W1 has had any traffic — answered 2026-10-10: unmeasured.** Zero comments
      (approve/hold/spam/trash all 0). Page views do not exist as data: the site runs no analytics
      plugin and serves no beacon, so WordPress has never counted a view. `wp_report.py` in the
      `wp-publish` skill now proves this rather than assuming it. Open question for Peter, and it
      is a privacy decision as much as a measurement one: install a server-side counter that keeps
      no personal data (Koko Analytics, Statify), pull the host's access log by hand, or keep the
      blog deliberately unmeasured. **Resolved 2026-10-10:** Koko Analytics 2.5.3 installed,
      cookieless (`"method":"fingerprint","use_cookie":false`), optimized endpoint live. W1's
      number therefore starts from zero on 2026-10-10 and the first nine months are permanently
      unmeasured — say so when citing it.
- [x] **Teach `wp_report.py` to read Koko — done 2026-10-10.** Reads `/totals`, `/posts`,
      `/referrers` and `/stats`, all gated on `view_koko_analytics`, which the `wp_publisher` role
      holds. Reports per-post and site-wide pageviews and visitors, top referrers, and the first
      recorded day, with `KOKO_EPOCH` marking the floor so a zero is never read as "unread".
- [ ] **UpdraftPlus and Wordfence are behind.** 1.26.7 vs 1.26.8, and 9.0.0 vs 9.0.2 as of
      2026-10-10, after a round of updates that did not pick them up. Wordfence being the stale one
      is the wrong plugin to be stale.
- [ ] Notebook idea: how to verify harness resolution rules by script. The method is already
      proven — throwaway trees under `/private/tmp`, a marker instruction, a positive control, and
      `claude -p '/context' < /dev/null` to read back which files loaded.
