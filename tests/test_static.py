"""A cheap undefined-name check (no pyflakes needed): every name that is read
must be defined, imported, assigned or a parameter somewhere in the file, or be
a builtin. Catches 'deleted a helper another function still calls'."""
import ast
import builtins
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"


def undefined_names(path):
    tree = ast.parse(path.read_text())
    known = set(dir(builtins)) | {"__file__", "__name__", "__doc__"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            known.add(node.name)
            if not isinstance(node, ast.ClassDef):
                a = node.args
                for arg in a.posonlyargs + a.args + a.kwonlyargs + [x for x in (a.vararg, a.kwarg) if x]:
                    known.add(arg.arg)
        elif isinstance(node, ast.Lambda):
            for arg in node.args.args + node.args.kwonlyargs + [x for x in (node.args.vararg, node.args.kwarg) if x]:
                known.add(arg.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                known.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            known.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            known.add(node.id)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            known.update(node.names)
    return sorted({n.id for n in ast.walk(tree)
                   if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in known})


ROOT = Path(__file__).resolve().parent.parent


def blank_comments_and_strings(source):
    """Replace comments and the inside of string literals with spaces, so braces or
    property names inside them cannot fool the checks (line layout is kept)."""
    out, i, n = [], 0, len(source)
    while i < n:
        c, nxt = source[i], source[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            while i < n and source[i] != "\n":
                out.append(" "); i += 1
        elif c == "/" and nxt == "*":
            while i < n and not (source[i] == "*" and i + 1 < n and source[i + 1] == "/"):
                out.append("\n" if source[i] == "\n" else " "); i += 1
            out.append("  "); i += 2
        elif c in "\"'`":
            quote = c
            out.append(quote); i += 1
            while i < n and source[i] != quote:
                if source[i] == "\\": out.append("  "); i += 2; continue
                out.append("\n" if source[i] == "\n" else " "); i += 1
            out.append(quote); i += 1
        else:
            out.append(c); i += 1
    return "".join(out)


def text_blocks(source):
    """Yield the body of every QML `Text { ... }` element (balanced braces, comments and
    strings ignored)."""
    import re
    clean = blank_comments_and_strings(source)
    for m in re.finditer(r'(?<![\w.])Text\s*\{', clean):
        depth, j = 1, m.end()
        while depth and j < len(clean):
            depth += {'{': 1, '}': -1}.get(clean[j], 0)
            j += 1
        yield source[m.end():j - 1], clean[m.end():j - 1]


def direct_part(block):
    """The block without nested {...} bodies, so only the element's own properties remain."""
    import re
    flat = block
    while True:
        smaller = re.sub(r'\{[^{}]*\}', '{}', flat)
        if smaller == flat:
            return flat
        flat = smaller


class QmlPlainTextTest(unittest.TestCase):
    """Omarchy's plugin guide: text from outside the plugin must never be rich text.
    Menu labels, titles and app names come from other applications, so every Text
    in the plugin is plain text."""

    def test_every_text_element_is_plain_text(self):
        found = 0
        for qml in sorted(ROOT.glob("*.qml")):
            for original, clean in text_blocks(qml.read_text()):
                found += 1
                # the property must be a real line of the element, not text in a comment or string
                self.assertRegex(direct_part(clean), r"(?m)^\s*textFormat:\s*Text\.PlainText\s*$",
                                 f"{qml.name}: a Text without plain text format")
        self.assertGreater(found, 5)

    def test_tooltips_are_literals(self):
        import re
        for qml in sorted(ROOT.glob("*.qml")):
            for m in re.finditer(r'(?m)^\s*tooltipText:\s*(.*)$', qml.read_text()):
                # a literal, or a string from the plugin's own catalog (strings.t("key", "literal")); never app data
                self.assertRegex(m.group(1), r'^("[^"\n]*"|strings\.t\("[^"\n]+", "[^"\n]*"\))\s*$', f"{qml.name}: a tooltip that is not a literal or a catalog string")

    def test_no_shell_in_the_widgets(self):
        for qml in sorted(ROOT.glob("*.qml")):
            self.assertNotIn('"sh", "-c"', qml.read_text(), f"{qml.name} runs a shell")

    def test_the_check_catches_a_text_without_plain_text(self):
        blocks = list(text_blocks('Item {\n Text { text: "x" }\n Text {\n  textFormat: Text.PlainText\n  text: "y"\n }\n}'))
        self.assertEqual(len(blocks), 2)
        pattern = r"(?m)^\s*textFormat:\s*Text\.PlainText\s*$"
        self.assertNotRegex(direct_part(blocks[0][1]), pattern)
        self.assertRegex(direct_part(blocks[1][1]), pattern)

    def test_the_check_is_not_fooled_by_comments_strings_or_braces(self):
        tricky = 'Item {\n Text {\n  // textFormat: Text.PlainText\n  text: "} textFormat: Text.PlainText {"\n }\n}'
        (original, clean), = list(text_blocks(tricky))
        self.assertNotRegex(direct_part(clean), r"(?m)^\s*textFormat:\s*Text\.PlainText\s*$")


class StaticTest(unittest.TestCase):
    def test_scripts_have_no_undefined_names(self):
        for name in ("omarchy-global-menu-bridge", "oma-top-menu-hypr-input", "oma-top-menu-uninstall"):
            self.assertEqual(undefined_names(BIN / name), [], name)

    def test_the_check_catches_a_missing_helper(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.py"
            p.write_text("def f():\n    return missing_helper()\n")
            self.assertEqual(undefined_names(p), ["missing_helper"])


if __name__ == "__main__":
    unittest.main()
