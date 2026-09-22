"""Task 1 of docs/superpowers/plans/2026-09-22-per-value-provenance.md: schema migration.

Run:  python3 -m unittest scripts.tests.test_provenance
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402


def cols(con, table):
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})")}


def tables(con):
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


class EnsureProvenanceSchemaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "p.sqlite"
        con = sqlite3.connect(self.db)
        # an OLD schema: the pre-provenance table shapes, so the migration has work to do
        con.executescript("""
            CREATE TABLE simulants (simulant_id TEXT PRIMARY KEY, name TEXT, cohesion TEXT);
            CREATE TABLE references_ (reference_id TEXT PRIMARY KEY, simulant_id TEXT, reference_text TEXT, reference_type TEXT);
            CREATE TABLE chemical_compositions (composition_id TEXT PRIMARY KEY, simulant_id TEXT, component_type TEXT, component_name TEXT, value_wt_pct REAL);
            CREATE TABLE mineral_compositions (composition_id TEXT PRIMARY KEY, simulant_id TEXT, component_type TEXT, component_name TEXT, value_pct REAL);
        """)
        con.commit()
        con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_adds_reference_columns(self):
        con = sqlite3.connect(self.db)
        ensure_provenance_schema(con)
        self.assertTrue({"names_simulant", "mention_quote", "local_path", "checked_on"} <= cols(con, "references_"))
        con.close()

    def test_adds_reference_id_to_both_composition_tables(self):
        con = sqlite3.connect(self.db)
        ensure_provenance_schema(con)
        self.assertIn("reference_id", cols(con, "chemical_compositions"))
        self.assertIn("reference_id", cols(con, "mineral_compositions"))
        con.close()

    def test_creates_property_sources_with_one_row_per_simulant_and_field(self):
        con = sqlite3.connect(self.db)
        ensure_provenance_schema(con)
        self.assertIn("property_sources", tables(con))
        con.execute("INSERT INTO property_sources VALUES ('S001','cohesion','R001','Table 2','Cohesion: 0.311 kPa')")
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute("INSERT INTO property_sources VALUES ('S001','cohesion','R002','p.3','other')")
        con.close()

    def test_second_run_changes_nothing(self):
        con = sqlite3.connect(self.db)
        first = ensure_provenance_schema(con)
        second = ensure_provenance_schema(con)
        self.assertTrue(first)          # something was added the first time
        self.assertEqual(second, [])    # nothing the second time
        con.close()

    def test_real_schema_file_already_carries_the_model(self):
        con = sqlite3.connect(":memory:")
        con.executescript((ROOT / "scripts" / "schema.sql").read_text())
        self.assertEqual(ensure_provenance_schema(con), [])
        con.close()


if __name__ == "__main__":
    unittest.main()
