"""The version shown in the sidebar must change on every push.

Alvaro reads `v2.9.x` in the sidebar to tell whether the staging page in front of him
already contains the change he asked about, so a push that leaves the number alone makes
the page unverifiable for him. This step does both edits at once — the sidebar label and a
dated CHANGELOG section — so the bump travels in the same commit as the change.

Rules under test:
  * the current version is read from the sidebar, which is the number the reader sees;
  * bumping increments the patch by default, or sets an explicit version;
  * the CHANGELOG gains a section at the top, under the preamble, never above the title;
  * a version already in the CHANGELOG is refused, so two pushes cannot share a number;
  * a body is inserted verbatim under the heading; without one a placeholder line marks it.

Run:  python3 -m unittest scripts.tests.test_bump_version
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from bump_version import bump, current_version, next_patch  # noqa: E402

SIDEBAR = """      <div className="p-4">
        <p className="text-[10px]">
          Interactive Database <span className="text-emerald-400 font-semibold">v2.9.5</span>
        </p>
      </div>
"""

CHANGELOG = """# Changelog

The version shown in the sidebar is set by hand in `src/components/sidebar/Sidebar.tsx`.
Data changes are logged per field under `documentation/`.

## v2.9.5 — 2026-09-22 (staging)

Per-value provenance.

## v2.9.4 — 2026-09-22 (staging)

The composition audit.
"""


class BumpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.sidebar = root / "src" / "components" / "sidebar" / "Sidebar.tsx"
        self.sidebar.parent.mkdir(parents=True)
        self.sidebar.write_text(SIDEBAR)
        self.changelog = root / "CHANGELOG.md"
        self.changelog.write_text(CHANGELOG)

    def tearDown(self):
        self.tmp.cleanup()

    def test_current_version_is_read_from_the_sidebar(self):
        self.assertEqual(current_version(self.sidebar), "2.9.5")

    def test_next_patch(self):
        self.assertEqual(next_patch("2.9.5"), "2.9.6")
        self.assertEqual(next_patch("2.9.9"), "2.9.10")
        self.assertEqual(next_patch("2.10.0"), "2.10.1")

    def test_bump_updates_both_files(self):
        v = bump(self.sidebar, self.changelog, today="2026-09-23", body="MLS-1 applied.")
        self.assertEqual(v, "2.9.6")
        self.assertIn("v2.9.6", self.sidebar.read_text())
        self.assertNotIn("v2.9.5", self.sidebar.read_text())
        text = self.changelog.read_text()
        self.assertIn("## v2.9.6 — 2026-09-23 (staging)", text)
        self.assertIn("MLS-1 applied.", text)

    def test_new_section_sits_under_the_preamble_and_above_the_previous_one(self):
        bump(self.sidebar, self.changelog, today="2026-09-23", body="Body.")
        lines = self.changelog.read_text().splitlines()
        self.assertEqual(lines[0], "# Changelog")
        self.assertLess(lines.index("## v2.9.6 — 2026-09-23 (staging)"), lines.index("## v2.9.5 — 2026-09-22 (staging)"))
        # The preamble survives.
        self.assertIn("set by hand", self.changelog.read_text())

    def test_explicit_version(self):
        v = bump(self.sidebar, self.changelog, today="2026-09-23", body="x", version="2.9.9")
        self.assertEqual(v, "2.9.9")
        self.assertIn("v2.9.9", self.sidebar.read_text())

    def test_a_version_already_in_the_changelog_is_refused(self):
        with self.assertRaises(ValueError):
            bump(self.sidebar, self.changelog, today="2026-09-23", body="x", version="2.9.4")

    def test_without_a_body_a_placeholder_marks_the_section(self):
        bump(self.sidebar, self.changelog, today="2026-09-23")
        self.assertIn("_No summary written._", self.changelog.read_text())

    def test_two_bumps_in_a_row_give_two_sections(self):
        bump(self.sidebar, self.changelog, today="2026-09-23", body="First.")
        bump(self.sidebar, self.changelog, today="2026-09-23", body="Second.")
        text = self.changelog.read_text()
        self.assertIn("## v2.9.7 — 2026-09-23 (staging)", text)
        self.assertLess(text.index("v2.9.7"), text.index("v2.9.6"))
        self.assertEqual(current_version(self.sidebar), "2.9.7")


if __name__ == "__main__":
    unittest.main()
