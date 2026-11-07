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
