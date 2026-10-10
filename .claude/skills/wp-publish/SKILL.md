---
name: wp-publish
description: Read and write the WordPress site peter.fitzgibbons.info through its REST API. Use this skill for ANY question or request about that blog, including: post, publish, push, update, or unpublish a draft from blog/*.md; preview how a post will render; check the site credentials; and read back how a published post is doing — its comments (including held, spam, and trashed ones), its traffic or page views or analytics, its live URL, or whether anyone has responded to it. Also use it when asked whether a post got any traffic, readers, hits, or engagement, since the answer requires probing what the site actually measures rather than guessing.
---

# Publish a blog post to WordPress

Source of truth is the Markdown file in `blog/`. WordPress is a rendering target; nothing is
edited there. Re-running on the same file updates the same post.

## The gate is the frontmatter

| `status:` line | Effect |
|---|---|
| absent | Nothing is sent. The script exits 0 and says so. |
| `draft` | Created (or updated) on the site as an unpublished draft. |
| `publish` | Live. |

**Peter sets `status:`.** Do not add or change that line unless he asks for it in the same
turn. Posting is outward-facing; the keystroke that flips it is his.

## Procedure

1. Confirm the file has a frontmatter block. Minimum viable:
   ```yaml
   ---
   status: draft
   categories: [Workbench]
   tags: [claude-code, hooks]
   excerpt: One sentence for the listing page.
   ---
   ```
   `title:` defaults to the first `# ` heading (which is then removed from the body so the site
   doesn't show it twice). `slug:` defaults to the filename stem. Categories must already exist
   on the site — taxonomy structure is Peter's decision, so the script refuses rather than
   creates. Tags are created on demand.
2. **Dry-run yourself** — read-only against the site, safe to execute:
   ```bash
   uv run --script .claude/skills/wp-publish/wp_publish.py blog/POST.md --dry-run
   ```
   It resolves categories/tags, checks the remote status if `wp_id` is set, and reports what it
   *would* send. Show Peter the output. To eyeball the conversion with no network at all,
   use `--html` instead.
3. **Gutenberg blocks are the default.** `--classic` is the escape hatch, for a
   post the serializer mangles. Undelimited HTML still renders, but the editor
   stores the whole post as one Classic block and block-aware plugins never
   fire. `blocks.py` holds the serializer, `test_blocks.py` its suite:
   ```bash
   python3 .claude/skills/wp-publish/test_blocks.py
   ```
   What it emits, and why — every line below was checked against the live site,
   not against the handbook:
   - **Code → `syntaxhighlighter/code`, not `core/code`.** The site runs
     SyntaxHighlighter Evolved; it is the only non-core block registered
     (`GET /wp-json/wp/v2/block-types`, 117 blocks). `core/code` has exactly one
     attribute, `content` — no `language` — and the plugin converts a `core/code`
     block only through a manual editor transform, never on render. Code in a
     `core/code` block reaches the page unhighlighted.
   - **The `<pre>` carries `class="wp-block-syntaxhighlighter-code"`, and no
     trailing newline.** The block's `supports` does not set
     `className: false`, so WordPress appends that generated class to whatever
     `save()` returns. A bare `<pre>` parses fine and then shows "Block
     contains unexpected or invalid content" on every open.
   - **Code text escapes `&` and `<` and nothing else.** The block's `save()` is
     `escapeEditableHTML(unescape(content))`, and `escapeEditableHTML` is
     `n(e.replace(/&/g,"&amp;"))` — read from the site's own
     `wp-includes/js/dist/escape-html.min.js`. Escape `>` or `"` too and the
     stored markup no longer matches what `save()` regenerates, so the editor
     offers to "recover" the block on every open. `test_blocks.py` pins the
     round trip.
   - Language names are SyntaxHighlighter *brush aliases*, not markdown fence
     names. They mostly coincide (`python`, `bash`, `sh`, `js`, `json`); an
     unknown one falls back to the site's default brush rather than erroring.
   - Lists get `wp:list-item` wrappers (WordPress 6.0+), nested lists
     recursively. The footnotes div has no core equivalent and goes in
     `wp:html`, which the editor leaves alone.

   To check markup against WordPress's own parser, use the `wp-blockmarkup`
   MCP server in `.mcp.json` (`validate_markup`, `get_block_markup`). It needs a
   one-time index (`wp-blocks` is a binary inside `wp-blockmarkup-mcp`, and
   Gutenberg's default branch is `trunk`, not `main`):
   ```bash
   npm install -g wp-blockmarkup-mcp
   wp-blocks source:add --name gutenberg --type github-public \
     --repo https://github.com/WordPress/gutenberg --branch trunk
   ```
   It indexes Gutenberg core only, so it reports `syntaxhighlighter/code` as
   "not found in any indexed source". That is the expected answer for a
   third-party block, not a defect.

   **`validate_markup` checks structure, not equivalence.** It parsed the bare
   `<pre>` as valid, and the editor still refused it. Structural validity is
   necessary and not sufficient: a static block is only valid if the stored
   markup equals what its `save()` regenerates, which no external parser can
   tell you. So the ground truth for any new block type is a block WordPress
   itself wrote:
   ```bash
   # make one block of the kind you need in the editor, save the draft, then:
   GET /wp-json/wp/v2/posts/<id>?context=edit   # content.raw is the exact markup
   ```
   `test_blocks.py` pins two such samples (posts 8282469899 and 8282469903).
   Add one whenever this script learns a new block type. Reading the plugin
   source instead is what produced the bare `<pre>`.
4. **Hand Peter the real command.** Never run it yourself:
   ```bash
   uv run --script .claude/skills/wp-publish/wp_publish.py blog/POST.md
   ```
   On first create the script writes `wp_id: N` into the file's frontmatter — that line is what
   makes later runs an update instead of a duplicate. Remind him to commit it.
5. Moving `publish` → `draft` (unpublishing) is refused unless `--force` is passed. Say so
   rather than adding the flag.

## Reading back: comments and traffic

`wp_report.py` is the read side. Stdlib only, every request a GET, nothing modified — so
**run it yourself** rather than handing it over. That is the one place this skill departs from
"Peter runs the commands": there is nothing here to approve.

```bash
python3 .claude/skills/wp-publish/wp_report.py blog/POST.md     # wp_id read from frontmatter
python3 .claude/skills/wp-publish/wp_report.py --id 8282469942
python3 .claude/skills/wp-publish/wp_report.py --id N --comments   # skip the traffic probe
python3 .claude/skills/wp-publish/wp_report.py --id N --json
```

**Comments are real counts.** Queried one status at a time, so the `X-WP-Total` header gives an
authoritative number per status without paging, and the report includes what a visitor never
sees: `hold`, `spam`, `trash`. A status that fails to query prints `?`, never `0`.

**Traffic has no source on this site, and the probe exists to prove that rather than assume it.**
WordPress core stores no view counter — a page view leaves no row in the database. Every "views"
number anywhere comes from a plugin or a third-party beacon, so the probe checks the three places
one can be installed: registered REST namespaces, the active plugin list, and the rendered post
HTML. Observed 2026-10-10: seven namespaces, seven active plugins, 98 KB of page HTML, and
**zero** analytics markers in any of the three. Active plugins are Add MIME Types, Antispam Bee,
Aspose Importer & Exporter, Public Post Preview, SyntaxHighlighter Evolved, UpdraftPlus and
Wordfence. No Jetpack, no stats plugin, no tag manager, no beacon.

So the honest report for any post is **page views unknown** — not zero, and not inferred from
something else.

- **Never substitute a proxy for a view count.** A comment count, a share count, a backlink, or
  a recollection of the post doing well is not traffic. If the probe finds nothing, say the
  number does not exist.
- The only surviving record is the host's web-server access log, which no API reaches. Getting
  one requires Peter in the hosting panel.
- To make traffic measurable in future, the decision is Peter's and it is a privacy decision as
  much as a measurement one: a server-side counter that keeps no personal data (Koko Analytics,
  Statify) behaves very differently from a third-party beacon. Neither is installed; do not
  install one.

When the probe *does* find a source, the script names it and stops. It deliberately does not
read any analytics API — each one has its own auth, and inventing a client for one on the fly is
how a made-up number gets published.

## Credentials

A netrc-format file at `~/.config/wp-publish/netrc`, mode `0600`, holding a WordPress
**Application Password** (core WP, revocable per client, HTTPS-only). Outside every repo by
design — the `.gitignore` is defense in depth; the control is that the secret never sits inside
a repo at all. The script refuses to read the file if group/other can.

**Never `cat`, `Read`, or echo that file.** If auth fails, run `--whoami` and report the error
text; the fix (rotate the password in WP Admin → Users → Profile → Application Passwords) is
Peter's.

Overrides for a different site: `WP_SITE=https://…` and `WP_NETRC=/path`.

## Voice

When drafting or editing a post, `.claude/rules/blog-voice.md` loads automatically for
`blog/**` and describes the inferred house voice. Match it.

## Scripts

`wp_report.py` — the read side. Stdlib only, no `uv`, no dependencies: a reporting tool that
needs nothing resolved always runs. `python3 wp_report.py --help` documents it.

`wp_publish.py` — Python, run under `uv run --script` so its two dependencies
(`markdown`, `python-frontmatter`) are declared inline and nothing is installed globally.
Stdlib `netrc` and `urllib` for everything else. `python3 wp_publish.py --help` documents the
full frontmatter contract.
