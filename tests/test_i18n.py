"""The translation catalog and the QML must agree: every strings.t("key", "English")
has the same English in i18n/en.json, nothing in the catalog is unused, and every
plugin component that translates declares its Translations object. English output is
therefore identical to what the QML would show without a catalog."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CALL = re.compile(r'strings\.t\("([^"]+)",\s*"((?:[^"\\]|\\.)*)"\)')


def calls():
    found = {}
    for qml in sorted(ROOT.glob("*.qml")):
        for key, english in CALL.findall(qml.read_text()):
            found.setdefault(key, set()).add(json.loads('"' + english + '"'))
    return found


class I18nTest(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / "i18n" / "en.json").read_text())

    def test_catalog_is_flat_strings(self):
        for key, value in self.catalog.items():
            self.assertIsInstance(value, str, key)

    def test_each_key_has_one_english_text_equal_to_the_catalog(self):
        for key, texts in calls().items():
            self.assertEqual(len(texts), 1, f"{key} has different English fallbacks")
            self.assertEqual(self.catalog.get(key), next(iter(texts)), key)

    def test_no_unused_or_missing_keys(self):
        used = set(calls())
        self.assertEqual(sorted(set(self.catalog) - used), [], "unused catalog keys")
        self.assertEqual(sorted(used - set(self.catalog)), [], "keys missing from the catalog")

    def test_placeholders_are_numbered_and_whole(self):
        for key, value in self.catalog.items():
            for n in re.findall(r"%(\d)", value):
                self.assertIn(n, "123456789", key)

    def test_components_that_use_translations_import_the_commons(self):
        for qml in sorted(ROOT.glob("*.qml")):
            text = qml.read_text()
            if re.search(r"(?<![\w.])Translations\s*\{", text):
                self.assertRegex(text, r"(?m)^import qs\.Commons\s*$", f"{qml.name} uses Translations without importing qs.Commons")

    def test_every_component_that_translates_declares_translations(self):
        for qml in sorted(ROOT.glob("*.qml")):
            text = qml.read_text()
            if "strings.t(" in text:
                self.assertRegex(text, r'Translations\s*\{\s*id:\s*strings;\s*directory:\s*Qt\.resolvedUrl\("i18n"\)\s*\}', qml.name)


if __name__ == "__main__":
    unittest.main()
