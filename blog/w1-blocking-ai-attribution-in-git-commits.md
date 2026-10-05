---
wp_id: 8282469942
status: publish
categories: [Workbench]
tags: [claude-code, hooks, workbench]
excerpt: You own every commit your agent writes, and Claude Code's `Co-Authored-By` line says otherwise.
---
# Blocking AI Attribution in Git Commits

*Workbench track, W1 · Draft, 2026-09-22 · Claude Code v2.1.269*

---

You own every commit your agent writes, yet Claude Code's `Co-Authored-By` line says otherwise. Refuse it with a `PreToolUse` hook. 

## The Fix

A `PreToolUse` hook is a script that runs before Claude Code executes a shell command, receives the call as JSON on stdin, and can veto it. Exit code 2 blocks the call and feeds stderr back to the model, which tries again. Exit 0 lets it through.[^docs] The script lives in its own file, not inline in the JSON, so it can be run by hand and tested. The part that matters is two regular expressions and one function:

```python
# .claude/hooks/no_ai_attribution.py (excerpt; full file and tests in the gist)

# A commit or PR verb counts only in command position: the start of a line, or
# right after ; && || | ( $(. Prose that merely *mentions* "git commit" passes.
COMMAND_POSITION = r"(?:^|[;&|(]\s*|\$\(\s*)"
GIT_GLOBAL_OPTIONS = r"(?:\s+-\S+(?:\s+[^-\s]\S*)?)*"  # -C <path>, -c k=v, --no-pager
CHANGE_RECORD = re.compile(
    COMMAND_POSITION + r"(?:git" + GIT_GLOBAL_OPTIONS + r"\s+commit|gh\s+pr\s+(?:create|edit))(?:\s|$)",
    re.MULTILINE,
)

# Markers of AI authorship. A Co-Authored-By naming a human does not match.
AI_ATTRIBUTION = re.compile(
    r"co-authored-by:.*(?:claude|anthropic)|claude-session:|generated with.*claude|claude\.ai/code",
    re.IGNORECASE,
)

def should_block(command: str, cwd: str = ".") -> bool:
    """The whole rule: a change record that carries AI attribution."""
    return is_change_record(command) and AI_ATTRIBUTION.search(message_text(command, cwd)) is not None

def main() -> int:
    payload = json.load(sys.stdin)                                   # the pending tool call
    command = (payload.get("tool_input") or {}).get("command") or ""
    if should_block(command, payload.get("cwd") or "."):
        sys.stderr.write(BLOCKED)                                    # returned to the model
        return 2                                                     # blocks the call
    return 0
```

The full hook, its test suite, and a notebook that runs both are in a gist: https://gist.github.com/pjfitzgibbons/d391cbad417897d95afba7bae7cd906a. The suite is standard-library `unittest`, one command, no installs:

```
python3 .claude/hooks/test_no_ai_attribution.py
```

If that's all you wanted, stop here.

## 1. Ownership Is Accountability, and a Tool Can't Carry It

Attribution of written text predates software by thousands of years, and the record of why people signed their work reads like a list of what a commit message is for. The oldest text that names its own author, "I, Enheduana," is more than four thousand years old, and whether she really wrote it has been argued over for a century.[^enheduanna] A name was worth disputing from the very first one we have. Theognis of Megara set his "seal" on his verses so they would "never be filched from him, nor shall evil ever be changed with their good, but every man shall say 'These are the lines of Theognis of Megara, famous throughout the world'": ownership, integrity, and authority, in his own words.[^theognis] Foucault's history of the author lands somewhere harder. Texts acquired real authors "only when the author became subject to punishment," because a work was a risky act before it was property.[^foucault] The word itself is Latin *attribuere*, to assign, to entrust.

Authority, integrity, ownership, accountability. A name on a work is the person those four things attach to, and none of them associate to a machine, tool, or computation.

An AI agent is a *tool*, in the same class as a compiler. It takes intent in one form and produces the artifact in another, and the artifact is yours. No compiler has ever signed a commit. Nobody has written a git helper that appends `Co-Authored-By: Python 3.22` to every message. The hook doesn't alter a convention; it removes a default no other tool in the class has ever had.

## 2. Agent Context Might Be Ignored. Enforcement Is Guaranteed.

Every session, the Claude Code harness hands the model a context-prompt preceding any user-written input. That session-context includes instruction to add those attribution lines to git commits. My `CLAUDE.md` told the model to ignore it. For the first five commits of the project, this worked fine; only by random chance—because model output is probabilistic against the _entire_ input prompt—the session-context + user-input. In other sessions, the user-input "no attribution" prompt was probabilistically ignored on the first commit. The correct agent action several times in a row is only luck, not a guarantee at all.

Random is the only thing it can be. A model produces probabilistic output. We humans are easily tricked into believing in the consistency after we watch a model produce a fully-correct 5000-line website in one go. But `CLAUDE.md`, memory, and skills all work the same way: they add words to the user-context and raise the probability of the asked-for behaviour. This _raises_ probability, yet _cannot_ set P=1. Absence of a line is as probabilistic as its presence. This is not a defect in Claude Code; it is what a language model is. Any guarantee of output has to come from something that is not a model.

Claude Code does have a setting for commit attribution, in `settings.json`, which _adds_ to the user-input, alongside memory and skills.[^docs] `"attribution": { "commit": "", "pr": "" }` in `settings.json` removes the instruction at its source, and it works, the instruction the model receives flipped from "end commits with `Co-Authored-By`" to "do not add attribution lines". What this changes is the context. What the model does with the context is still a probability. The setting doesn't *check*.

Three layers ended up in the repo. The `attribution` setting removes the instruction. Telling Claude in `CLAUDE.md` to eliminate the attribution raises the probability of removal. A `PreToolUse` hook refuses any commit with the attribution. This third step is the enforcement, and the only layer that is not probabilistic.

From here on, the next time Claude reaches for a `Co-Authored-By`, with no instruction in user-input telling it not to, `PreToolUse` refuses the commit, Claude sees the `PreToolUse` error message and retries without the attribution. Linked above is the finished hook; the first version was three lines shorter, and the difference is the next reason.

## 3. All Code Is Tested, and Failing Tests Are Education

I expected to restart Claude Code for the hook to load. I didn't have to. Claude Code v2.1.269 picked the hook up immediately, and I know because the very next _tool-use-command_ was blocked.

That command was a `sed` with a heredoc updating the project plan with a paragraph describing the hook. The paragraph contained the words "git commit" and "Co-Authored-By … Claude". The first version of the hook checked whether the command *text* contained those things. It did. The hook blocked its own documentation.

In any other case, the first instinct would be to reword the paragraph. Knowing that we're in the middle of _building_ this hook, though, this blocked command required a dance—fix the code and tests *without triggering the hook*. Claude gladly did the dance: the `Write` tool puts content straight into a file, and the hook's matcher is `Bash`, so `Write` never reaches it.

So the fix, the verb now has to sit in command position. Start of a line, or after `;`, `&&`, `||`, `|`, `(`, `$(`. Prose that mentions `git commit` offhandedly passes the hook.

After this fix, the hook blocked only twice more, correctly. One of those was while running the updated test-suite, which runs a test matrix, a dozen sample commands piped through the hook to check the exit codes. The matrix included:

```
x=$(git commit -m "claude.ai/code/session_1")
```

From stdin that is a commit in command position carrying an AI marker. The hook cannot tell a fixture from a commit. "Looks like a test" isn't any part of the hook's filter.

So the tests moved into a file, `test_no_ai_attribution.py`. The suite passes whole or fails.

- Seven cases check that the hook **allows** a command, including a `Co-Authored-By` naming a human, because a real co-author is a legitimate record.
- Eight check that the hook **blocks** one:
    - `-m`
    - a heredoc message
    - `-F file`
    - chained after `&&`
    - `git -C path commit`
    - a commit on the second line of a multi-line command
    - inside `$( )`
    - `gh pr create --body`
- Three run the script the way Claude Code does: JSON in, exit code out.

Claude's first attempt to write that test file was a `Bash` heredoc, and the hook blocked it, because the fixtures look like commits. Claude then wrote the file through the `Write` tool, which the hook doesn't watch and doesn't need to: nothing but `Bash` can run `git`, and the test file doesn't commit anything.

Working TDD (Test-Driven Development) is great, yet sometimes it can leave gaps due to confirmation-bias. You'd have to think-up the edge case to know to test for it. In this case, writing a comprehensive test-suite, matrix-style, gave us an edge-case: `git -C /tmp/x commit`. The hook pattern allowed git's global options but didn't check the arguments, nor possible file-references for content. This is the kind of gap you only find with a test. 

## Where This Doesn't Hold

The hook watches one tool, `Bash`, because that is the only tool that can run `git`; a message hidden in a `-F` or `--body-file` target is still read. A git hook would be weird in some cases, as we're only intending to limit Claude. If a human types `Co-Authored-By: Claude` into a commit outside Claude Code, we don't mean to stop that. (Though, WHY?). The settings alone (`settings.json`, `CLAUDE.md`) might be enough if you are the only person who will ever read the git log. Most repos outlive that assumption. 

[^docs]: Claude Code documentation: [hooks](https://code.claude.com/docs/en/hooks) and the [`attribution` setting](https://code.claude.com/docs/en/settings-reference), where the older `includeCoAuthoredBy` key is listed as deprecated. The hook, its test, and the settings file are in the project repo.
[^enheduanna]: Enheduana, high priestess of Ur, c. 2300 BCE; she names herself at line 67 of *The Exaltation of Inana*: "I am the high priestess, I am Enheduana." The poems survive only in copies made some five centuries later, and Sophus Helle's summary of the debate is that "we cannot say for sure whether the poems were written by Enheduana or in her name (as the ancient equivalent of historical fiction)": [enheduana.org/authorship](https://enheduana.org/authorship/). His annotated translation is free at [enheduana.org/exaltation](https://enheduana.org/exaltation/); the book is *Enheduana: The Complete Poems of the World's First Author* (Yale University Press, 2023).
[^theognis]: Theognis, *Elegies*, lines 19ff., trans. J. M. Edmonds, *Elegy and Iambus*, vol. 1 (Loeb Classical Library, 1931), [the poems at the Perseus Digital Library](https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:2008.01.0479:volume%3D1:text%3D11:section%3D2). The passage is the earliest known *sphragis*, the Greek poets' "seal" of authorship, and its purpose is stated in the text: that the lines not be stolen or altered.
[^foucault]: Michel Foucault, "What Is an Author?" (1969), in *Language, Counter-Memory, Practice*, trans. Bouchard and Simon (Cornell University Press, 1977); [excerpt at foucault.info](https://foucault.info/documents/foucault.authorFunction.en/), [full text as PDF from the Open University](https://www.open.edu/openlearn/ocw/pluginfile.php/624849/mod_resource/content/1/a840_1_michel_foucault.pdf): "Speeches and books were assigned real authors, other than mythical or important religious figures, only when the author became subject to punishment and to the extent that his discourse was considered transgressive." Discourse "was a gesture charged with risks before it became a possession caught in a circuit of property values."
