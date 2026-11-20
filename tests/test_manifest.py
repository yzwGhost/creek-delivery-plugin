import json
from pathlib import Path
import unittest


class PluginManifestTest(unittest.TestCase):
    def test_entry_is_discoverable(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / ".codex-plugin/plugin.json").read_text("utf-8"))
        self.assertEqual(manifest["name"], "creek-delivery")
        entry = root / manifest["skills"] / manifest["name"] / "SKILL.md"
        frontmatter = entry.read_text("utf-8").split("---", 2)[1]
        self.assertIn("name: creek-delivery", frontmatter.splitlines())
        self.assertRegex(frontmatter, r"(?m)^description: .+")
