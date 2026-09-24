"""Task 5 of docs/superpowers/plans/2026-09-22-per-value-provenance.md: export and suppression.

The database keeps every value. The export hides a scalar on `simulants` unless a
property_sources row names the document it came from, ships property_sources itself,
and carries reference_id on composition rows so the UI can number the citations.

Run:  python3 -m unittest scripts.tests.test_export_provenance
"""

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from export_json import SUPPRESSED_SCALAR_FIELDS, run  # noqa: E402
from verify_data import check_scalar_provenance  # noqa: E402

TODAY = "2026-09-22"


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())
    # S001: the sheet states cohesion and pH; bulk density and specific gravity have no source row.
    con.execute("""INSERT INTO simulants (simulant_id, name, bulk_density, specific_gravity, cohesion, ph, composition_status)
                   VALUES ('S001','LHS-1','1.40',2.77,'0.311',9.75,'verified')""")
    # S002: a value with no source at all.
    con.execute("INSERT INTO simulants (simulant_id, name, bulk_density) VALUES ('S002','WITHHELD-1','1.2')")
    con.execute("""INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type,
                                            names_simulant, mention_quote, local_path, checked_on)
                   VALUES ('DS-S001','S001','LHS-1 Fact Sheet','datasheet',1,'LHS-1 Lunar Highlands Simulant',
                           '/Users/owner/DIRT/Sources/LHS-1.pdf',?)""", (TODAY,))
    con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type) VALUES ('R001','S001','Long-Fox 2023','geotechnical')")
    con.executemany("INSERT INTO property_sources VALUES (?,?,?,?,?)", [
        ("S001", "cohesion", "DS-S001", "data sheet", "Cohesion: 0.311 kPa"),
        ("S001", "ph", "DS-S001", "data sheet", "pH: 9.75"),
    ])
    con.execute("""INSERT INTO chemical_compositions (composition_id, simulant_id, component_type, component_name, value_wt_pct, reference_id)
                   VALUES ('CH-S001-01','S001','oxide','SiO2',49.12,'DS-S001')""")
    con.execute("""INSERT INTO mineral_compositions (composition_id, simulant_id, component_type, component_name, value_pct, reference_id)
                   VALUES ('C-S001-01','S001','mineral','Anorthosite',74.4,'DS-S001')""")
    con.commit()
    con.close()


class ExportProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.db = root / "e.sqlite"
        make_db(self.db)
        self.out = root / "data.json"
        self.report_dir = root / "documentation"
        run(self.db, output=self.out, report_dir=self.report_dir, today=TODAY)
        with open(self.out) as f:
            self.bundle = json.load(f)
        self.sim = {s["simulant_id"]: s for s in self.bundle["simulants"]}

    def tearDown(self):
        self.tmp.cleanup()

    def test_scalar_with_a_source_row_is_exported(self):
        self.assertEqual(self.sim["S001"]["cohesion"], 0.311)
        self.assertEqual(self.sim["S001"]["ph"], 9.75)

    def test_scalar_without_a_source_row_exports_as_null(self):
        self.assertIsNone(self.sim["S001"]["bulk_density"])
        self.assertIsNone(self.sim["S001"]["specific_gravity"])
        self.assertIsNone(self.sim["S002"]["bulk_density"])

    def test_database_keeps_the_suppressed_value(self):
        con = sqlite3.connect(self.db)
        self.assertEqual(con.execute("SELECT bulk_density FROM simulants WHERE simulant_id='S001'").fetchone()[0], "1.40")
        con.close()

    def test_property_sources_present_in_bundle(self):
        rows = self.bundle["property_sources"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"simulant_id": "S001", "field": "cohesion", "reference_id": "DS-S001",
                                   "location": "data sheet", "quote": "Cohesion: 0.311 kPa"})

    def test_composition_rows_carry_reference_id(self):
        self.assertEqual(self.bundle["chemical_compositions"][0]["reference_id"], "DS-S001")
        self.assertEqual(self.bundle["compositions"][0]["reference_id"], "DS-S001")

    def test_references_carry_provenance_columns_but_not_local_path(self):
        ds = next(r for r in self.bundle["references"] if r["reference_id"] == "DS-S001")
        self.assertEqual(ds["names_simulant"], 1)
        self.assertEqual(ds["mention_quote"], "LHS-1 Lunar Highlands Simulant")
        self.assertEqual(ds["checked_on"], TODAY)
        self.assertNotIn("local_path", ds)

    def test_suppression_report_lists_every_hidden_value(self):
        report_path = self.report_dir / f"export-suppression-{TODAY}.json"
        self.assertTrue(report_path.exists())
        with open(report_path) as f:
            report = json.load(f)
        hidden = {(e["simulant_id"], e["field"], e["value"]) for e in report["suppressed"]}
        self.assertEqual(hidden, {("S001", "bulk_density", "1.40"), ("S001", "specific_gravity", 2.77), ("S002", "bulk_density", "1.2")})
        self.assertEqual(report["count"], 3)

    def test_field_list_matches_the_spec(self):
        self.assertEqual(set(SUPPRESSED_SCALAR_FIELDS), {
            "bulk_density", "cohesion", "friction_angle", "specific_gravity", "density_g_cm3",
            "particle_size_d50", "particle_size_distribution", "particle_morphology", "particle_ruggedness",
            "glass_content_percent", "nasa_fom_score", "ti_content_percent", "ph", "angle_of_repose",
            "particle_size_mean_um", "bulk_density_range", "magnetic_susceptibility"})


class VerifyScalarProvenanceTest(unittest.TestCase):
    def test_exported_bundle_passes(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        db = root / "e.sqlite"
        make_db(db)
        run(db, output=root / "data.json", report_dir=root, today=TODAY)
        with open(root / "data.json") as f:
            bundle = json.load(f)
        self.assertEqual(check_scalar_provenance(bundle["simulants"], bundle["property_sources"]), [])
        tmp.cleanup()

    def test_unsourced_scalar_in_bundle_is_an_error(self):
        simulants = [{"simulant_id": "S001", "name": "LHS-1", "cohesion": 0.311, "bulk_density": 1.4}]
        sources = [{"simulant_id": "S001", "field": "cohesion", "reference_id": "DS-S001"}]
        errors = check_scalar_provenance(simulants, sources)
        self.assertEqual(len(errors), 1)
        self.assertIn("S001", errors[0])
        self.assertIn("bulk_density", errors[0])


if __name__ == "__main__":
    unittest.main()


class GrainSizeGateTests(unittest.TestCase):
    """grain_size_mm, from the Gasteiner compilation, is shown among the physical properties;
    like every value there it needs a source row to be exported."""

    def test_grain_size_without_a_source_is_not_exported(self):
        import export_json
        self.assertIn("grain_size_mm", export_json.SUPPRESSED_EXTRA_FIELDS)
        extra = [{"simulant_id": "S1", "grain_size_mm": 0.088}, {"simulant_id": "S2", "grain_size_mm": 0.1}]
        out, n = export_json.suppress_unsourced_extra(extra, [{"simulant_id": "S2", "field": "grain_size_mm"}])
        self.assertEqual([e["grain_size_mm"] for e in out], [None, 0.1])
        self.assertEqual(n, 1)


class NotAboutItTests(unittest.TestCase):
    """A reference a reader confirmed does not name the product is not shown in its list."""

    def test_only_references_not_confirmed_absent_are_exported(self):
        import export_json
        refs = [{"reference_id": "R1", "names_simulant": 1}, {"reference_id": "R2", "names_simulant": 0}, {"reference_id": "R3", "names_simulant": None}]
        self.assertEqual([r["reference_id"] for r in export_json.shown_references(refs)], ["R1", "R3"])
