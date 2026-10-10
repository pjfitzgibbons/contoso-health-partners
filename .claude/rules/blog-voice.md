---
paths:
  - "blog/**"
---

# Blog voice — peter.fitzgibbons.info

Tagline: *Raise Kids, Raise Vegetables, Raise Code.*

## Inputs a draft needs

- **Audience.** Who the post is for and what they already know. The audience varies by post, so it is a required input to any drafting prompt. If it is not given, ask for it before writing a word. The audience decides what gets explained: anything that audience would not know gets one clause on first use; the thing the post is not about never gets explained.
- **The decision.** The one sentence the reader should be able to repeat. It becomes the `excerpt`.
- **The evidence.** The incidents, errors, numbers, and files the reasons will draw on.

## The target: a thought leader with an engineer's evidence

The unit of value is a **position** — a claim about how a class of problems should be decided — not a fix. The position is earned with the engineer's material: the exact error, the thing that didn't work, the hours it cost. The incident is *evidence*, never the point.

Test for a draft: can the reader state the claim in one sentence after the first paragraph? If not, it's a story, not a position. Can they point to the concrete moment that proves each reason? If not, it's an opinion, not a position.

## Structure: decision → fix → reasons → limits → charge

Pyramid Principle / BLUF. The standard shape:

1. **The decision.** One to three sentences. What I concluded and what I'd tell you to do. No context-setting before it — the context comes *after*, as part of why.
2. **The fix.** Only when the post has one. The final code or config, so the reader who only wants the fix stops here. The rabbit hole comes after.
3. **Why — three reasons**, each with its own subhead. One claim per reason, and under each, the concrete moment from the work that proves it. This is where problem → attempts → solution lives: each dead end becomes evidence for whichever reason it proves. Three, not five; if there are five, two are sub-points of others.
4. **Where it doesn't hold.** One paragraph: the cost, the case it doesn't cover, the thing that's still unverified. A position without limits is marketing.
5. **The charge.** One line to the reader, and the last line of prose in the post. "Embrace your Artisan." "Enjoy!" Not a summary.

**Updates append at document level.** After a post is published, nothing above the charge changes. New material goes at the end as `**Update, YYYY-MM-DD:**` paragraphs.

### Thought openers

A cluster of rhetorical questions gives the reader food for thought and builds context without requiring the whole domain. "Who will answer questions about that commit later — a colleague? a manager? an auditor?" Use one cluster per post, at the decision or at the top of a reason, three questions at most. Equivalent devices, interchangeable with the cluster: a concrete future scene ("three years on, a new engineer runs `git blame` and asks why"), or a named person asking ("a manager asks who wrote this").

### Inside a section

- **Headings are plain labels.** "The Fix", not "The fix, if that's all you came for". No winks, no asides, no clauses in headings. A heading may name the lesson: "Failing Tests Are Education".
- **Name the subject; don't refer to it before it's introduced.** "A PreToolUse hook does", not "The hook does". "Agent context might be ignored", not "Context can be ignored" — say whose context.
- **Don't restate the claim after the evidence.** Once the evidence lands, the section is over. No summary sentence, no "so".
- **A segue is the last sentence before its target.** "…the difference is the next reason." → heading. Nothing sits between a segue and the section it points to. If a paragraph wants to be there, it goes before the segue or it goes.
- **Say what the steady state is, not just the incident.** After the story, state what happens every time from now on, as the closing paragraph of the reason that proves it. The interesting fact about a control is not the day it was installed; it is that it now needs nobody in the room. *Where it doesn't hold* stays pure limits. Example: the reason that argues *enforcement cannot be ignored* ends: "The next time Claude reaches for a `Co-Authored-By`, with no instruction in context telling it not to, `PreToolUse` refuses the commit and Claude rewrites the message. Nobody remembers anything. Nobody intervenes." The limits section then says only what the hook does not cover.
- **Name the mechanism, not the vibe.** "The Claude Code harness hands the model a context-prompt preceding any user-written input" beats "Claude Code tells the model to." Harness, session-context, user-input, tool-use-command: the precise noun for each part, and the same noun every time. Define an acronym on first use: "TDD (Test-Driven Development)."
- **One key term per argument, reused.** A section arguing that model output is probabilistic says *probabilistic* every time, not a rotation through statistical, random, luck, chance. Repetition of the term is the argument accumulating; synonyms dissipate it.
- **Notation when it is shorter than the sentence.** "This raises probability, yet cannot set P=1." The symbol does the work of a clause.
- **A concrete counterexample for a psychological claim.** "We humans are easily tricked into believing in the consistency after we watch a model produce a fully correct 5,000-line website in one go." The reader has seen that; the abstract version ("people over-trust models") they would argue with.
- **Educational and evangelist by default.** When a failure taught something, say what it taught, as a call-out. A section can close by listing what the failures taught. Use the phrase "learning experience" rarely; use the pattern often.

## Sentence and paragraph discipline

The agent's default prose runs long and chains clauses. Counter it mechanically:

- **One idea per sentence.** If a sentence has a dash *and* a comma clause, or two "and"s joining clauses, split it.
- **Vary length on purpose.** Aim for a mix of 8–25 words, averaging around 15. A 30-word sentence is allowed only if the next one is under 10. Never two long sentences in a row.
- **Paragraphs of three to five sentences.** One-line paragraphs for the decision and the charge; nowhere else by default.
- **A semicolon only when the second clause explains the first.** "Claude can't own this code though; it can't answer questions years later." Never to glue two unrelated sentences.
- **Cut the connective tissue.** "That said," "It's worth noting that," "Importantly," "In other words," — delete and see if the sentence still stands. It will.
- **Triads.** "Intent, construction, or quality." "A hook, avoiding false positives, and testing." Three nouns is the rhythm for a list inside a sentence.
- **Present tense for the principle, past tense for the evidence.** "Making it permanent takes a hook, avoiding false positives, and testing" is a general truth; the sections under it are the story, and they happened.
- **Generalize the incident into the practice in summary lines.** "A false positive" → "avoiding false positives"; "a test" → "testing". In the evidence sections the incident stays specific.
- **Hedge the weak side, assert the strong side.** "Agent context *might* be ignored. Enforcement *cannot*." The possibility gets a soft verb; the guarantee gets a hard one.
- **Contractions, yes. Profanity, no.**

## Every sentence does work

Filler is the agent's most reliable failure, and it survives every other rule. The test is deletion: remove the sentence; if the reader loses nothing, it stays removed. The recurring shapes:

- **The moral after the evidence.** "A control everyone routes around is worse than none." The evidence already said it. Cut.
- **The aphoristic closer.** "Nobody remembers anything. Nobody intervenes." A pull-quote is not a paragraph ending. State what happens and stop: "Claude sees the error and retries without the attribution."
- **The lesson list that repeats the section.** "Three blocks, three lessons. Fix the control, not the input…" If each lesson was already the point of its paragraph, the list is a second reading of the same section.
- **The generalized principle where a mechanism will do.** Not "'Looks like a test' is not an exception any control should accept." Say what the code does: "'Looks like a test' isn't any part of the hook's filter."
- **The second telling of one fact.** A fact appears once, where it does the most work. The live-reload observation proves the hook loaded instantly; it does not also need to prove the setting works.
- **The flourish on a joke.** "…and if someone did, the pull request would be closed with a laugh." The joke was `Co-Authored-By: Python 3.22`. The explanation is the filler.

## Lists

**Prose lists stop at three.** Three items ride inside a sentence: "intent, construction, or quality." Four or more go to bullets, nested if they group. A reader cannot hold eight comma-separated cases in one sentence and should not be asked to.

## Emphasis budgets

Each device has its own ceiling, and the post has a total. Defaults; tune here.

| Device | Per post | Example |
|---|---|---|
| Wink (playful aside) | 0–1 | "Grasshopper." "The black art of WinAPI." |
| CAPS for emphasis | 0–1 | "5 times... on THIS project." |
| Italic *you* at the pivot | 0–1 | "Only a human, *you*, can do that." |
| Fragment | 0–2 | "Bingo." "Still no joy." |
| Rhetorical-question cluster | 0–1 (≤3 questions) | See *Thought openers*. |
| **Total devices** | **≤5** | |

None is required. A post with zero of them is fine; a post over budget is shouting.

## Stance

- **Admit the mess as fact, not confession.** "I'm a month late on this project." "This befuddles the newbie — namely, me." State the fact; don't frame it as a disclosure.
- **Opinions are flat and owned.** No "some might argue." One "I think" is owned; three is hedging.
- **Credit by name, with a link.** Anyone whose work was used. Attribution is a value.
- **Human framing.** Craft, storytelling, "sleep on it", the law of least astonishment. The technical decision is always in service of a person doing work.
- **Blunt about vendors, generous about people.**
- **Plain colloquial verbs are welcome.** "Claude gladly did the dance." "Prose that mentions `git commit` offhandedly passes." Working language, not slang; the register of an engineer explaining at a whiteboard.
- **A parenthetical aside is a wink.** "(Though, WHY?)" counts against the wink budget and the CAPS budget both.
- **Universal, never project-scoped.** A position is true for every reader or it is not a position. The project, the domain, and the regulations are never the reason; at most they are a footnote that someone wrote the principle down. If a reason section opens with "The project is…", it is wrong.
- **Argue from what the tool can't do, not from what I do.** "Claude can't own this code; it can't answer questions years later, or stand up to a manager or a subcommittee to the intent, construction, or quality of the submission." The capability gap is the argument. Narrating my own process is not.
- **Accountability is to named people, over years.** "A manager or a subcommittee", "years later", "the next engineer". Not "an auditor", not "a control record". Universal workplace, not compliance vocabulary.
- **Name the weak alternative by what it actually is.** "Telling Claude to memorize this removal is one thing." Not "a preference", not "one setting". Say what the weaker thing is in plain words a reader outside the tool understands.
- **Cross-project evidence proves the claim isn't local.** One other project turns "it happened here" into "it happens". "I have had this rule in place for weeks on another project and repeatedly have to amend commit messages."
- **Don't command the reader to look. Show it.** Not "Look at what the attribution line actually records." Instead: "Even the attribution itself — `Claude Opus 5 (1M context)` — is a model version."

## Pronouns: who is voicing this line?

Written text has no speaker. The reader supplies one, in their own inner voice. Every pronoun choice decides whose mouth the sentence ends up in.

- **"I" for evidence.** The incident, the error, the hours lost, the thing that didn't work. The reader hears testimony and weighs it. This is where credibility is earned, so keep "I" concrete: "five commits", "an hour", "the sixth commit in the repo". Never "I feel" or "I believe" as a substitute for a fact.
- **"You" for the decision and the charge.** "You own what the agent authors. So own it." The reader voices that line to themselves, which is why it can land as their own conclusion (Brunyé et al., 2009: second person produces the strongest perspective-taking). It is also why it can read as presumption. A second-person opener is a loan against the evidence under it. If reason 1 doesn't pay it off, cut the "you" and state the claim impersonally.
- **"You" for instructions.** "Put it in `~/.claude/settings.json`." Fine everywhere; that's a how-to talking.
- **"We" only when the reader is actually in it.** "We software engineers are also storytellers" works because the reader is one. "We" to a reader outside the situation is recruitment, and they notice. Never "we" as a soft "I".
- **"We" for the pair at the bench.** In narration of the work, "we" may mean the engineer and the agent together: "we're in the middle of building this hook." Decisions stay "I"; the agent's actions stay "Claude"; the shared situation can be "we".
- **Don't tell the reader what they feel or think.** "You've probably seen this and been annoyed" makes a claim about the reader's mind. "If you use Claude Code, you have seen this at the bottom of a commit" makes a claim about their screen. The second is checkable. Asking is allowed (see *Thought openers*); asserting is not.
- **"It", "them", "this", "that" get one obvious noun, or they get replaced by the noun.** A pedestrian reader takes whichever noun is closest or loudest, and should never have to choose. "None of *them* came from writing the hook" → "None of *the gaps* were apparent while writing the hook." Test: read the sentence alone. If the pronoun could be two things, write the thing. Repeating a noun is never the error; the reader's hesitation is.
- **The absent-speaker rule:** spoken "you" is softened by tone and face; written "you" has neither. Read every second-person sentence as if a stranger said it flatly. If it would be presumptuous from a stranger, it's presumptuous on the page.
- **The agent is a tool, and the post is in the human's voice.** "My" means Peter. Code, config, prose, and decisions the agent produced and Peter accepted are "my" without qualification, the same as work done with a compiler or an editor. The agent is never a co-author and never gets a credit line. The only place agent text appears as the agent's is verbatim session output, in a code block, quoted as evidence.
- **When the post is *about* the agent**, the agent is named as an *actor* ("Claude reported the change", "Claude was blocked"), never as an author. Actions stay attributed to whoever took them so the reader can tell what the tool did from what the human decided. A link to the vendor's documentation is a source citation, not attribution.

## Mechanics

**House style is *The Chicago Manual of Style*** (CMOS, University of Chicago Press) for everything this document does not decide: punctuation, capitalization, hyphenation, quotation, citation. Where this document and CMOS disagree, this document wins; the known deviations are marked ⚠.

- **Titles: headline-style capitalization, colons allowed** (CMOS 8.159). "Write Better Software: Embrace Your Humanity." Headings inside the post follow the same case.
- **Em dash, closed.** `word—word`, no spaces (CMOS 6.85). Never a spaced hyphen ` - ` or a double hyphen `--`; correct them on sight. The one-idea-per-sentence rule applies to em-dash clauses.
- **Serial comma, always** (CMOS 6.19). "Intent, construction, or quality."
- **Spelling ⚠ deviates from CMOS** (which follows Merriam-Webster). Canadian for agent-written prose (*colour*, *organize*, *centre*, *modelled*). Consistency within a post beats any dictionary. Never "correct" Peter's own words in either direction.
- **Numbers ⚠ deviates from CMOS** (which spells out one through one hundred). Zero through nine: word or digit, writer's choice, not enforced. Ten and up: digits. Anything that is not a small integer — decimals, fractions, percentages, versions, times, hex — digits or the notation of its own system.
- **Tests pass whole or fail. Never "N must pass".** Keep two vocabularies apart: a hook's verdict is *allow/block*; a suite's result is *pass/fail*, and it is all cases or nothing. Partial pass is not pass.
- **Product and version on first mention in a section.** "Claude Code v2.1.269", not "2.1.269".
- **Sources and links go in footnotes.** Documentation links, credits, and asides that would break the paragraph go there. No italic footer paragraph, no "References" heading. Inline links stay inline only when the link *is* the sentence's object ("the [`attribution` setting](…)"). Markdown syntax, definitions at the end of the file, labels free-form:

  ```markdown
  A commit is a promise.[^1] The `attribution` setting turns the line off,[^docs] but it checks nothing.

  Own it.

  [^1]: Regulated industries write this down; ALCOA+ calls it *attributable*.
  [^docs]: Claude Code documentation: [hooks](https://code.claude.com/docs/en/hooks).
  ```

  The publish script renders this as a superscript number in the text (`<sup><a href="#fn:1">1</a></sup>`) and, after the charge, a horizontal rule followed by a numbered list with ↩ back-links to each reference. Labels are renumbered in order of appearance, so `[^docs]` becomes 2. The theme's `.footnote` styling applies; no plugin needed. Preview with `uv run --script .claude/skills/wp-publish/wp_publish.py blog/POST.md --html`.

### Code blocks

- **A file block opens with its path as a comment.** Any block that shows a file the reader must reproduce — system settings, project settings, a script, a hook — starts with `// path/to/file` or `# path/to/file` in the file's own comment syntax. Use `jsonc` for JSON that carries the comment.
- **A snippet does not.** A multi-line example that is not a specific file (a command, a sample message, a fragment) carries no path.
- **Inline up to `MAX_INLINE_LINES = 50`.** Longer than that: show the essential part inline and link the whole file — in the project repo if it lives there, otherwise in a gist. Tune the number here.

## Tracks and numbering

Three series, and the prefix is part of the filename and of the draft subtitle.

| Prefix | Series | Numbering |
|---|---|---|
| none | The security-architecture thread — Posts 1–9, tied to the Acts | PLAN.md reserves the slot |
| `W#` | **Workbench** — the planned harness and tooling posts, published at Act checkpoints | PLAN.md reserves the slot |
| `L#` | **Learnings** — what a session turned up that was worth writing down, outside the plan | Publication order; no slot reserved |

A W post is scheduled: the plan names it before it is written, and it publishes when its Act closes. An L post is discovered: the work produced a finding that stands on its own, and it publishes when it is ready. If a draft is waiting on an Act, it is a W; if it is waiting on nothing, it is an L.

Filename is the prefix, lowercased, then the slug: `w1-blocking-ai-attribution-in-git-commits.md`, `l1-multi-repo-config.md`. The `slug:` frontmatter matches the filename stem, so the published URL carries the prefix too.

The draft subtitle names the track: `*Learnings track, L1 · Draft, 2026-10-08 · Claude Code v2.1.289*`. Delete the whole line when `status:` flips to `publish`.

A correction to a published post is an append under *Updates*, not a new number — unless the correction is large enough to carry its own position, in which case it becomes the next L and links back.

## Frontmatter contract

The Markdown file is the source of truth; WordPress renders it. The block at the top:

```yaml
---
status: draft        # draft | publish. Absent → nothing is sent. Peter flips this line, nobody else.
title:               # optional; defaults to the first "# " heading, which is then removed from the body
slug:                # optional; defaults to the filename stem
excerpt:             # REQUIRED. The decision, in one sentence. Same sentence as the post's first line.
categories: [Workbench]   # must already exist on the site
tags: [claude-code, hooks]
date:                # optional, site-local
wp_id:               # written back by the publish script after first create; commit it
---
```

- **The draft subtitle line** (`*Workbench track, W1 · Draft, 2026-09-12 · Claude Code 2.1.269*`) is draft-only. Delete it when `status:` flips to `publish`.
- **Until `status: publish`, edit freely.** After that, the body above the charge is frozen; see *Updates* under Structure.

## Editorial rules

These govern what gets published and are not negotiable per post.

1. **Agentic tooling is quarantined.** The security-architecture series contains no content about AI assistance, agents, or Claude Code. That material is the workbench track, a separate series with its own numbering. One non-exception: AI as a *regulated system* (Annex 22) is subject matter for the compliance thread, not tooling.
2. **No public URLs.** Deployed hostnames are never published. A walkthrough plus the public GitHub repos is enough context; if a post cannot work without a live URL, the post is wrong, not the rule.
3. **Redaction.** Hostnames blurred in screenshots. No tenant IDs, subscription IDs, or resource names that encode anything real.
4. **Named vendors get verified before publication.** Characterizing a real business in public is a higher bar than a plan entry. Drafts use categories; names go in after checking, with a source.
5. **Intentionally insecure code is labeled as such, prominently,** wherever it appears — in a post or in a repo README above the fold: teaching artifact, do not deploy, with the specific weaknesses named.

## Banned words

Never appears in a post, and never in this document either.

- **"honest", "honesty", "honestly".** Claiming the quality performs it instead of doing it, and it implies the rest of the writing was something else. The replacement is the specific quality meant: *precise*, *accurate*, *complete*, *unhedged*, or the fact itself. "One honest paragraph" → "One paragraph." "Keep the hook honest" → "Keep the hook precise."

## Do not

- Don't bring in the project's background at all unless a reason literally depends on it. The position is universal; the project is where the evidence happened, nothing more.
- Don't build toward an aphorism. If a line sounds like a pull-quote, check whether it says more than the plain version. Usually it says less.
- Don't use a table for what a sentence can say. Tables are for real comparisons with three or more columns of data.
- Don't announce sincerity or importance. Show the number instead.
- Don't reproduce typos or double spaces from older posts. Those are fingers, not voice.

## Never hard-wrap prose

One paragraph is one line. No inserted newlines at 80, 100, or any column — editors soft-wrap. Hard wraps make diffs noisy, break WordPress paragraphs at the wrong places, and turn one changed word into a rewrapped paragraph. Code blocks keep their own line breaks; everything else is one line per paragraph. Applies to every file under `blog/`; the same preference holds for prose Peter will publish anywhere.

## Open

Undecided. Each carries the current proposal so a draft has something to follow; Peter closes them.

- **Numbered reason headings** (`## 1.`, `## 2.`). No rule yet. Proposal: none until a post makes the case either way.
- **The agent-as-actor rule** (Pronouns) is untested on a post that is not about the agent. Revisit at the first such post.
