"""Wrap rendered HTML in Gutenberg block delimiters.

WordPress stores blocks as ordinary HTML fenced by HTML comments:

    <!-- wp:paragraph -->
    <p>Welcome to the world of blocks.</p>
    <!-- /wp:paragraph -->

Content with no delimiters still renders on the front end, but the block
editor treats the whole post as one Classic block, and block-aware plugins
never fire.

This module takes the HTML that python-markdown produces and adds the
delimiters, top level only. core/list wraps every item in its own
core/list-item block (WordPress 6.0+); anything with no core equivalent --
the footnotes div -- goes inside core/html, which the editor leaves alone.
Code is the one site-specific choice: peter.fitzgibbons.info runs
SyntaxHighlighter Evolved, so code goes to `syntaxhighlighter/code` rather
than core/code. See `_code` for why, and for where each claim was checked.

Everything here was verified against the WordPress block parser through the
wp-blockmarkup MCP server, and against the site's own /wp-json/wp/v2
/block-types, not from recollection of the handbook.
"""

import re
from html import unescape
from html.parser import HTMLParser

try:
    from pygments import highlight as _pyg
    from pygments.formatters import HtmlFormatter
    from pygments.filter import Filter
    from pygments.lexers import get_lexer_by_name
    from pygments.token import Name, Operator, Punctuation
    from pygments.util import ClassNotFound
    PYGMENTS = True
except ImportError:                      # the SyntaxHighlighter path still works
    PYGMENTS = False

# Top-level tag -> block name. Tags absent here fall through to core/html.
SIMPLE_BLOCKS = {
    "p": "paragraph",
    "h1": "heading",
    "h2": "heading",
    "h3": "heading",
    "h4": "heading",
    "h5": "heading",
    "h6": "heading",
    "blockquote": "quote",
    "hr": "separator",
    "table": "table",
    "figure": "table",
}

LANGUAGE = re.compile(r'<code[^>]*class="[^"]*language-([A-Za-z0-9_+-]+)')
OPEN_LIST = re.compile(r"<(ul|ol)\b[^>]*>")

# WordPress generates this from the block name and appends it to save() output
# for any block that does not set `supports.className: false`.
CODE_CLASS = "wp-block-syntaxhighlighter-code"

# The block declares `supports.align`, so a code block can break out of the
# prose column. Twenty Twenty-Three sets contentSize 650px and wideSize
# 1200px, which is ~140 monospace columns -- enough for any line in a post,
# while prose keeps a readable measure. Set to "" for themes without
# align-wide support (Twenty Fourteen reported align-wide: false, where the
# class would be inert).
CODE_ALIGN = "wide"

# Markdown fence name -> SyntaxHighlighter's *canonical* brush name.
#
# The plugin keeps a 64-entry alias table, and its brush loader asks
# `in_array($language, $this->brushes, true)` -- which tests the table's
# VALUES (canonical names) and not its keys (aliases). So a block tagged
# `js` or `py` renders with the right brush class and the brush script is
# never enqueued, leaving the code unhighlighted with no error anywhere.
# Sending the canonical name sidesteps it: every canonical name is also a
# valid key, so the lookup that follows still succeeds.
#
# Derived from syntaxhighlighter.php's table; only the entries where the
# alias differs from the brush are listed, everything else passes through.
BRUSH_ALIASES = {
    "actionscript3": "as3", "c": "cpp", "c-sharp": "csharp", "cf": "coldfusion",
    "clj": "clojure", "erl": "erlang", "golang": "go", "html": "xml",
    "javascript": "jscript", "jfx": "javafx", "js": "jscript",
    "matlab": "matlabkey", "obj-c": "objc", "pas": "delphi", "pascal": "delphi",
    "patch": "diff", "pl": "perl", "ps": "powershell", "py": "python",
    "rails": "ruby", "rb": "ruby", "ror": "ruby", "shell": "bash",
    "splus": "r", "tex": "latex", "text": "plain", "vbnet": "vb",
    "xhtml": "xml", "xslt": "xml", "yml": "yaml",
}


def _fence(name: str, html: str, attrs: str = "") -> str:
    return f"<!-- wp:{name}{attrs} -->\n{html}\n<!-- /wp:{name} -->"


def _editable(text: str) -> str:
    """The plugin's escapeEditableHTML: & and <, and deliberately nothing else.

    Verified against wp-includes/js/dist/escape-html.min.js on the site:
    `b(e) = n(e.replace(/&/g, "&amp;"))` where `n` escapes `<`. Escaping `>`
    or `"` as well would not match what the block's save() regenerates, and
    the editor would offer to "recover" the block every time it opened.
    """
    return text.replace("&", "&amp;").replace("<", "&lt;")


# Pygments runs at publish time, so the page ships finished HTML: no runtime
# JS, no plugin, nothing to override. It also reads Python properly, which
# SyntaxHighlighter's regex brushes do not -- they class every operator as a
# keyword, every docstring as a comment, and cannot see a function
# definition at all. Set to False to go back to the plugin's block.
HIGHLIGHT_AT_PUBLISH = True

# Scoped to .pyg so these short class names cannot collide with anything the
# theme or a plugin ships. No !important needed anywhere.
CODE_WRAP = "wp-block-code pyg"

# Markdown fence names Pygments does not know, mapped to the lexer that
# reads them best. Scored on real samples, not guessed: on a Bicep resource
# block the TypeScript lexer leaves nothing unclassified and picks up the
# single-quoted strings, while Terraform -- the intuitive choice, since both
# are HCL-shaped -- fails on 25 tokens. Razor has no lexer in Pygments at
# all; its markup outweighs its C#, so HTML is the least-wrong reading.
FENCE_ALIASES = {"bicep": "typescript", "razor": "html", "cshtml": "html",
                 "arm": "json", "sql": "psql", "postgres": "psql", "dotenv": "bash", "env": "bash", "jsonc": "json"}


if PYGMENTS:

    class _Members(Filter):
        r"""Tag `x.member` so attribute and method usage carries colour.

        Pygments matches builtins with a `(?<!\.)` lookbehind, so anything
        after a dot is deliberately left a bare Name: `json.load`,
        `payload.get` and `sys.stderr` all arrive unclassified. The lexer is
        right to be careful -- it cannot know what an attribute resolves to --
        but the result is that method-heavy code reads flat.

        Retagging happens on the token stream rather than in a lexer, so one
        rule covers every language. A dot reaches us as Operator in Python
        and as Punctuation in TypeScript and C#; both are handled. Only a
        bare `Name` is retagged, so anything the lexer already classified --
        a builtin, a keyword, a definition -- is left exactly as it was.
        Python emits a member as bare `Name`; TypeScript and JavaScript use
        `Name.Other`, so both are accepted.
        """

        def filter(self, lexer, stream):
            after_dot = False
            for ttype, value in stream:
                if after_dot and ttype in (Name, Name.Other):
                    ttype = Name.Attribute
                if not value.isspace():
                    after_dot = value == "." and ttype in (Operator, Punctuation)
                yield ttype, value


def _pygmentise(source: str, fence: str) -> str | None:
    """Finished HTML for `source`, or None if we cannot highlight it."""
    if not (PYGMENTS and HIGHLIGHT_AT_PUBLISH and fence):
        return None
    try:
        lexer = get_lexer_by_name(FENCE_ALIASES.get(fence, fence), stripnl=False)
    except ClassNotFound:
        return None
    lexer.add_filter(_Members())
    body = _pyg(source, lexer, HtmlFormatter(nowrap=True)).rstrip("\n")
    return f'<pre class="{CODE_WRAP}"><code>{body}</code></pre>'


def _code(fragment: str) -> str:
    """A fenced code block, highlighted at publish time where we can.

    Pygments output goes inside core/html: its <span> classes would not
    survive core/code, whose content attribute is rich-text and strips
    markup it does not recognise. core/html is stored verbatim and the
    editor never tries to parse it.

    Without Pygments, or for a language it does not know, this falls back to
    the SyntaxHighlighter block -- see the git history for why its markup
    has to match save() byte for byte.
    """
    match = LANGUAGE.search(fragment)
    fence = match.group(1).lower() if match else ""
    inner = re.sub(r'^<pre[^>]*>\s*<code[^>]*>', "", fragment, count=1)
    inner = re.sub(r"</code>\s*</pre>$", "", inner, count=1)
    source = unescape(inner).rstrip("\n")

    lit = _pygmentise(source, fence)
    if lit is not None:
        return _fence("html", lit)
    if PYGMENTS and HIGHLIGHT_AT_PUBLISH:
        # No lexer for this fence. Same wrapper, same styling, no spans --
        # unhighlighted, never inconsistent.
        esc = source.replace("&", "&amp;").replace("<", "&lt;")
        return _fence("html", f'<pre class="{CODE_WRAP}"><code>{esc}</code></pre>')

    parts = []
    if fence:
        parts.append(f'"language":"{BRUSH_ALIASES.get(fence, fence)}"')
    if CODE_ALIGN:
        parts.append(f'"align":"{CODE_ALIGN}"')
    attrs = f' {{{",".join(parts)}}}' if parts else ""
    return _fence("syntaxhighlighter/code", f'<pre class="{CODE_CLASS}">{_editable(source)}</pre>', attrs)


def _balanced_end(html: str, start: int, tag: str) -> int:
    """Index just past the </tag> that closes the <tag> opening at `start`."""
    pattern = re.compile(rf"</?{tag}\b[^>]*>", re.IGNORECASE)
    depth = 0
    for match in pattern.finditer(html, start):
        depth += -1 if match.group().startswith("</") else 1
        if depth == 0:
            return match.end()
    return len(html)


def _convert_nested(content: str) -> str:
    """Replace any list nested inside a list item with its block markup."""
    out, i = [], 0
    while True:
        match = OPEN_LIST.search(content, i)
        if not match:
            out.append(content[i:])
            return "".join(out)
        end = _balanced_end(content, match.start(), match.group(1))
        out.append(content[i:match.start()])
        out.append("\n" + _list(content[match.start():end], match.group(1) == "ol") + "\n")
        i = end


def _split_items(html: str) -> list[str]:
    """Inner HTML of each top-level <li>, nested lists left intact."""
    inner = re.sub(r"^<(ul|ol)\b[^>]*>", "", html.strip(), count=1)
    inner = re.sub(r"</(ul|ol)>$", "", inner.strip(), count=1)
    items, i = [], 0
    while True:
        match = re.compile(r"<li\b[^>]*>").search(inner, i)
        if not match:
            return items
        end = _balanced_end(inner, match.start(), "li")
        body = inner[match.end():end]
        items.append(re.sub(r"</li>$", "", body.strip(), count=1).strip())
        i = end


def _list(html: str, ordered: bool) -> str:
    """Every <li> becomes its own core/list-item block (WordPress 6.0+)."""
    tag = "ol" if ordered else "ul"
    attrs = ' {"ordered":true}' if ordered else ""
    items = "".join(
        _fence("list-item", f"<li>{_convert_nested(item)}</li>") + "\n"
        for item in _split_items(html)
    )
    return _fence("list", f"<{tag}>\n{items}</{tag}>", attrs)


class _TopLevel(HTMLParser):
    """Split a fragment into top-level elements, keeping their raw HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.chunks: list[tuple[str, str]] = []
        self._tag = None
        self._depth = 0
        self._start = 0

    def handle_starttag(self, tag, attrs):
        if self._tag is None:
            self._tag, self._depth, self._start = tag, 1, self.getpos_offset()
        elif tag == self._tag:
            self._depth += 1

    def handle_startendtag(self, tag, attrs):
        if self._tag is None:
            self.chunks.append((tag, self.get_starttag_text()))

    def handle_endtag(self, tag):
        if self._tag is None or tag != self._tag:
            return
        self._depth -= 1
        if self._depth == 0:
            end = self.getpos_offset() + len(f"</{tag}>")
            self.chunks.append((self._tag, self.rawdata[self._start:end]))
            self._tag = None

    def getpos_offset(self) -> int:
        line, col = self.getpos()
        return sum(len(l) + 1 for l in self.rawdata.split("\n")[: line - 1]) + col


def to_blocks(html: str) -> str:
    """Wrap each top-level element of `html` in its block delimiters."""
    parser = _TopLevel()
    parser.feed(html)
    parser.close()

    out = []
    for tag, raw in parser.chunks:
        if tag == "pre":
            out.append(_code(raw))
        elif tag in ("ul", "ol"):
            out.append(_list(raw, ordered=(tag == "ol")))
        elif tag == "hr":
            out.append(_fence("separator", '<hr class="wp-block-separator"/>'))
        elif tag in SIMPLE_BLOCKS:
            out.append(_fence(SIMPLE_BLOCKS[tag], raw))
        else:
            # No core equivalent (the footnotes <div>, raw embeds). core/html
            # is stored verbatim and the editor does not try to parse it.
            out.append(_fence("html", raw))
    return "\n\n".join(out)
