"""Later runs must cover only what is still unverified.

Re-running the group builder after a batch has landed would otherwise send agents back to
simulants whose values are already sourced. A simulant is finished when all three of
Alvaro's tests pass for it: every reference has been checked against its document, every
composition row cites one, and every stored value has a source row. Simulants carrying no
data and no reference are not "finished" — there is simply nothing yet to check, and they
still need a reader to establish that the product exists.

Run:  python3 -m unittest scripts.tests.test_build_groups_skip
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402
from build_groups import unfinished_reason, SCALAR_FIELDS  # noqa: E402


def make_db(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())
    ensure_provenance_schema(con)
    return con


class SkipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.con = make_db(Path(self.tmp.name) / "lrs.sqlite")
        self.con.row_factory = sqlite3.Row

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def add(self, sid, **cols):
        keys = ", ".join(["simulant_id", "name", *cols])
        marks = ", ".join(["?"] * (2 + len(cols)))
        self.con.execute(f"INSERT INTO simulants ({keys}) VALUES ({marks})", (sid, sid, *cols.values()))

    def reason(self, sid):
        sim = dict(self.con.execute("SELECT * FROM simulants WHERE simulant_id=?", (sid,)).fetchone())
        refs = [dict(r) for r in self.con.execute("SELECT * FROM references_ WHERE simulant_id=?", (sid,))]
        chem = [dict(r) for r in self.con.execute("SELECT * FROM chemical_compositions WHERE simulant_id=?", (sid,))]
        mins = [dict(r) for r in self.con.execute("SELECT * FROM mineral_compositions WHERE simulant_id=?", (sid,))]
        sourced = {r[0] for r in self.con.execute("SELECT field FROM property_sources WHERE simulant_id=?", (sid,))}
        return unfinished_reason(sim, refs, chem, mins, sourced)

    def test_scalar_fields_are_the_ones_the_page_shows(self):
        for f in ("cohesion", "bulk_density", "ph"):
            self.assertIn(f, SCALAR_FIELDS)

    def test_fully_sourced_simulant_is_finished(self):
        self.add("S1", cohesion="1.2", composition_status="verified")
        self.con.execute("INSERT INTO references_ (reference_id, simulant_id, names_simulant) VALUES ('R1','S1',1)")
        self.con.execute("INSERT INTO chemical_compositions (composition_id, simulant_id, component_type, component_name, value_wt_pct, reference_id) VALUES ('CH1','S1','oxide','SiO2',47.0,'R1')")
        self.con.execute("INSERT INTO property_sources (simulant_id, field, reference_id) VALUES ('S1','cohesion','R1')")
        self.assertIsNone(self.reason("S1"))

    def test_unsourced_scalar_keeps_it_unfinished(self):
        self.add("S2", cohesion="1.2", bulk_density="1.5")
        self.con.execute("INSERT INTO references_ (reference_id, simulant_id, names_simulant) VALUES ('R2','S2',1)")
        self.con.execute("INSERT INTO property_sources (simulant_id, field, reference_id) VALUES ('S2','cohesion','R2')")
        self.assertEqual(self.reason("S2"), "1 value without a source")

    def test_unchecked_reference_keeps_it_unfinished(self):
        self.add("S3")
        self.con.execute("INSERT INTO references_ (reference_id, simulant_id) VALUES ('R3','S3')")
        self.assertEqual(self.reason("S3"), "1 reference unchecked")

    def test_reference_checked_and_found_absent_still_counts_as_checked(self):
        self.add("S4")
        self.con.execute("INSERT INTO references_ (reference_id, simulant_id, names_simulant) VALUES ('R4','S4',0)")
        self.assertIsNone(self.reason("S4"))

    def test_composition_row_without_a_citation_keeps_it_unfinished(self):
        self.add("S5")
        self.con.execute("INSERT INTO references_ (reference_id, simulant_id, names_simulant) VALUES ('R5','S5',1)")
        self.con.execute("INSERT INTO mineral_compositions (composition_id, simulant_id, component_type, component_name, value_pct) VALUES ('C5','S5','mineral','Olivine',10.0)")
        self.assertEqual(self.reason("S5"), "1 composition row without a citation")

    def test_a_simulant_with_nothing_at_all_still_needs_a_reader(self):
        self.add("S6")
        self.assertEqual(self.reason("S6"), "no reference on file")

    def test_release_date_and_institution_count_as_values(self):
        self.add("S7", institution="TU Braunschweig")
        self.con.execute("INSERT INTO references_ (reference_id, simulant_id, names_simulant) VALUES ('R7','S7',1)")
        self.assertEqual(self.reason("S7"), "1 value without a source")


if __name__ == "__main__":
    unittest.main()


class AlreadyReadTests(unittest.TestCase):
    """A simulant a reader-checker pair has already been through must not be sent again.

    Values the documents do not state never become sourced, so "every value sourced" would
    send agents back to JSC and NU-LHT for ever. What marks the work done is that a pair
    read it; what is left there is an owner decision, not another reading.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, ids):
        import json
        (self.dir / name).write_text(json.dumps(
            {"groups": [{"extraction": {"results": [{"simulant_id": i, "name": i} for i in ids]}}]}))

    def test_collects_ids_across_every_findings_file(self):
        from build_groups import already_read
        self.write("provenance-findings-batch2.json", ["S027", "S028"])
        self.write("provenance-findings-unit22-EAC-1A.json", ["S018"])
        self.assertEqual(already_read(self.dir), {"S027", "S028", "S018"})

    def test_other_json_in_the_directory_is_ignored(self):
        from build_groups import already_read
        self.write("provenance-findings-batch2.json", ["S027"])
        (self.dir / "library-simulant-index-2026-09-22.json").write_text('{"simulants": {}}')
        (self.dir / "provenance-apply-log-batch2.json").write_text('[{"simulant_id": "S999"}]')
        self.assertEqual(already_read(self.dir), {"S027"})

    def test_no_findings_yet_is_empty_not_an_error(self):
        from build_groups import already_read
        self.assertEqual(already_read(self.dir), set())

    def test_a_malformed_findings_file_does_not_hide_the_others(self):
        from build_groups import already_read
        self.write("provenance-findings-good.json", ["S027"])
        (self.dir / "provenance-findings-broken.json").write_text("{not json")
        self.assertEqual(already_read(self.dir), {"S027"})
