import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render.py"
EXAMPLES = ROOT / "examples"


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        shutil.copy2(EXAMPLES / "sample.json", self.work / "sample.json")
        shutil.copy2(EXAMPLES / "chart-zh.svg", self.work / "chart-zh.svg")

    def run_render(self, name="sample.json", extra=()):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.work / name),
             "--output", str(self.work / "article.html"), *extra],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )

    def test_renders_mobile_page_and_coverage(self):
        result = self.run_render()
        self.assertEqual(result.returncode, 0, result.stderr)
        page = (self.work / "article.html").read_text(encoding="utf-8")
        coverage = json.loads((self.work / "article.coverage.json").read_text(encoding="utf-8"))
        self.assertIn('class="reading-nav"', page)
        self.assertIn('href="#results"', page)
        self.assertIn('data-label="组别"', page)
        self.assertEqual(coverage["rendered_items"], 9)
        self.assertEqual(coverage["unmapped_items"], [])

    def test_rejects_unmapped_source_item(self):
        doc = json.loads((self.work / "sample.json").read_text(encoding="utf-8"))
        doc["sections"][1]["blocks"].pop()
        (self.work / "invalid.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        result = self.run_render("invalid.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unmapped source items: paragraph-3", result.stderr)
        self.assertFalse((self.work / "article.html").exists())

    def test_packages_media_when_inline_budget_is_zero(self):
        result = self.run_render(extra=("--max-inline-mb", "0"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.work / "article.zip").is_file())


if __name__ == "__main__":
    unittest.main()
