#!/usr/bin/env python3
"""Tests for blocks.py.

Run:  python3 .claude/skills/wp-publish/test_blocks.py

Every expected string here comes from the block editor handbook, not from
memory. The suite passes whole or fails.
"""

import sys
import unittest
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blocks  # noqa: E402
from blocks import to_blocks  # noqa: E402

OPEN = '<pre class="wp-block-syntaxhighlighter-code">'


class HighlightTests(unittest.TestCase):
    """Publish-time highlighting: the default path."""

    def test_python_is_lexed_not_pattern_matched(self):
        """The distinctions SyntaxHighlighter's regex brushes cannot draw."""
        src = ('@lru_cache\ndef should_block(c: str) -&gt; bool:\n'
               '    """Doc."""\n    return c is None\n')
        out = to_blocks(f'<pre><code class="language-python">{src}</code></pre>')
        for cls, what in [("nd", "@lru_cache is a decorator"),
                          ("nf", "should_block is a definition, not a builtin"),
                          ("nb", "str/bool are builtins"),
                          ("sd", "the docstring is its own class, not a comment"),
                          ("kc", "None is a keyword constant"),
                          ("ow", "`is` is a word operator, not a keyword")]:
            with self.subTest(what):
                self.assertIn(f'class="{cls}"', out, what)

    def test_highlighted_code_goes_in_an_html_block(self):
        """core/code's content is rich-text and would strip the spans."""
        out = to_blocks('<pre><code class="language-python">x = 1</code></pre>')
        self.assertTrue(out.startswith("<!-- wp:html -->"))
        self.assertIn('<pre class="wp-block-code pyg"><code>', out)

    def test_bicep_falls_back_to_a_lexer_that_reads_it(self):
        out = to_blocks("<pre><code class=\"language-bicep\">param x string = 'a'</code></pre>")
        self.assertIn("<span", out)

    def test_unknown_language_keeps_the_same_wrapper(self):
        out = to_blocks('<pre><code class="language-klingon">nuqneH</code></pre>')
        self.assertIn('<pre class="wp-block-code pyg"><code>nuqneH</code></pre>', out)
        self.assertNotIn("<span", out)

    def test_unknown_language_still_escapes(self):
        out = to_blocks('<pre><code class="language-klingon">a &amp;&amp; b &lt;c&gt;</code></pre>')
        self.assertIn("a &amp;&amp; b &lt;c>", out)


class BlockTests(unittest.TestCase):
    def setUp(self):
        """The SyntaxHighlighter block is now the opt-out path."""
        blocks.HIGHLIGHT_AT_PUBLISH = False
        self.addCleanup(setattr, blocks, "HIGHLIGHT_AT_PUBLISH", True)

    def no_align(self):
        """Compare the block's own shape, without our alignment attribute."""
        blocks.CODE_ALIGN = ""
        self.addCleanup(setattr, blocks, "CODE_ALIGN", "wide")

    def test_paragraph(self):
        self.assertEqual(
            to_blocks("<p>Hello</p>"),
            "<!-- wp:paragraph -->\n<p>Hello</p>\n<!-- /wp:paragraph -->",
        )

    def test_heading(self):
        self.assertIn("<!-- wp:heading -->\n<h2>The Fix</h2>", to_blocks("<h2>The Fix</h2>"))

    def test_code_matches_a_block_the_editor_itself_wrote(self):
        """Byte-for-byte against post 8282469903, read back via context=edit.

        This is the only assertion in the suite taken from WordPress rather
        than from a source tree. An earlier version omitted the generated
        class and every code block opened with a recovery banner.
        """
        self.no_align()
        self.assertEqual(
            to_blocks('<pre><code class="language-xml">&lt;svelte here&gt;</code></pre>'),
            '<!-- wp:syntaxhighlighter/code {"language":"xml"} -->\n'
            '<pre class="wp-block-syntaxhighlighter-code">&lt;svelte here></pre>\n'
            "<!-- /wp:syntaxhighlighter/code -->",
        )

    def test_code_sends_canonical_brush_not_fence_alias(self):
        """`js` and `py` are aliases the plugin's brush loader silently drops.

        It tests `in_array($language, $this->brushes)` against the table's
        values, so only a canonical brush name enqueues its script. The block
        still renders with the right class, so the failure looks like "no
        highlighting" and reports nothing.
        """
        for fence, brush in (("py", "python"), ("js", "jscript"),
                             ("shell", "bash"), ("yml", "yaml"), ("html", "xml")):
            with self.subTest(fence):
                out = to_blocks(f'<pre><code class="language-{fence}">x</code></pre>')
                self.assertIn(f'"language":"{brush}"', out)

    def test_code_keeps_language(self):
        """`python` is a real SyntaxHighlighter brush alias (shBrushPython.js)."""
        out = to_blocks('<pre><code class="language-python">x = 1</code></pre>')
        self.assertIn('"language":"python"', out)
        self.assertIn('<pre class="wp-block-syntaxhighlighter-code">x = 1</pre>', out)
        self.assertNotIn("language-python", out.split("-->")[1])

    def test_code_without_language(self):
        """No fence language: the block falls back to the site default."""
        out = to_blocks("<pre><code>plain</code></pre>")
        self.assertIn('<!-- wp:syntaxhighlighter/code {"align":"wide"} -->', out)
        self.assertIn('<pre class="wp-block-syntaxhighlighter-code">plain</pre>', out)

    def test_code_drops_the_trailing_newline(self):
        """Markdown ends a fenced block with \n; the editor stores none."""
        out = to_blocks("<pre><code>one\ntwo\n</code></pre>")
        self.assertIn("two</pre>", out)
        self.assertNotIn("two\n</pre>", out)

    def test_code_escapes_only_ampersand_and_lt(self):
        """Must match what save() regenerates, or the block will not validate.

        Escaping `>` or `"` as well, or leaving Markdown's entities in place,
        makes the stored markup differ from the regenerated markup and the
        editor offers to recover the block on open. The editor's own output
        in test_code_matches_a_block_the_editor_itself_wrote shows the same
        rule: `&lt;svelte here>`, with the `>` left raw.
        """
        out = to_blocks("<pre><code>a &amp;&amp; b &lt;c&gt; d &quot;e&quot;</code></pre>")
        self.assertIn(OPEN + 'a &amp;&amp; b &lt;c> d "e"</pre>', out)

    def test_code_round_trips_through_the_block(self):
        """Stored text -> textContent -> save() must return the stored text."""
        source = "if x &lt; 1 and y &gt; 2: p(&quot;a &amp;&amp; b&quot;)"
        stored = to_blocks(f"<pre><code>{source}</code></pre>")
        inner = stored.split(OPEN, 1)[1].split("</pre>", 1)[0]
        text_content = unescape(inner)                     # what the parser reads
        regenerated = text_content.replace("&", "&amp;").replace("<", "&lt;")
        self.assertEqual(inner, regenerated)

    def test_list_items_are_blocks(self):
        """WordPress 6.0+: each <li> is its own core/list-item block."""
        out = to_blocks("<ul><li>one</li><li>two</li></ul>")
        self.assertEqual(out.count("<!-- wp:list-item -->"), 2)
        self.assertEqual(out.count("<!-- /wp:list-item -->"), 2)
        self.assertIn("<!-- wp:list -->", out)
        self.assertIn("<li>one</li>", out)

    def test_ordered_list(self):
        out = to_blocks("<ol><li>one</li></ol>")
        self.assertIn('<!-- wp:list {"ordered":true} -->', out)
        self.assertIn("<ol>", out)

    def test_separator(self):
        self.assertIn('<hr class="wp-block-separator"/>', to_blocks("<hr />"))

    def test_unknown_element_becomes_html_block(self):
        """The footnotes div has no core equivalent; core/html preserves it."""
        out = to_blocks('<div class="footnote"><ol><li>note</li></ol></div>')
        self.assertTrue(out.startswith("<!-- wp:html -->"))
        self.assertIn('<div class="footnote">', out)
        self.assertNotIn("wp:list-item", out)

    def test_multiple_top_level_elements(self):
        out = to_blocks("<p>a</p>\n<h2>b</h2>\n<p>c</p>")
        self.assertEqual(out.count("<!-- wp:paragraph -->"), 2)
        self.assertEqual(out.count("<!-- wp:heading -->"), 1)

    def test_nested_same_tag_not_split(self):
        """A <p> inside a blockquote must not end the outer element early."""
        out = to_blocks("<blockquote><p>inner</p></blockquote>")
        self.assertEqual(out.count("<!-- wp:quote -->"), 1)
        self.assertIn("<p>inner</p>", out)
        self.assertNotIn("<!-- wp:paragraph -->", out)

    def test_nested_list_recurses(self):
        """A list inside a list item gets its own block markup, not raw HTML."""
        out = to_blocks("<ul><li>parent<ul><li>child</li></ul></li></ul>")
        self.assertEqual(out.count("<!-- wp:list -->"), 2)
        self.assertEqual(out.count("<!-- wp:list-item -->"), 2)
        self.assertEqual(out.count("<!-- wp:"), out.count("<!-- /wp:"))
        self.assertIn("<li>child</li>", out)

    def test_nested_list_item_text_preserved(self):
        out = to_blocks("<ul><li>Eight check:<ul><li>-m</li><li>heredoc</li></ul></li></ul>")
        self.assertIn("Eight check:", out)
        self.assertEqual(out.count("<!-- wp:list-item -->"), 3)

    def test_delimiters_balance(self):
        out = to_blocks("<p>a</p><ul><li>x</li></ul><pre><code>y</code></pre>")
        self.assertEqual(out.count("<!-- wp:"), out.count("<!-- /wp:"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
