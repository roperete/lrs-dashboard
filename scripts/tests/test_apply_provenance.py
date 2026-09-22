"""Task 7.1 of the per-value provenance plan: applying agent findings.

Agents return, per simulant, (a) for each reference whether the document names the
simulant with a quote, (b) for each stored value the reference, location and quote that
supports it or `unsupported`, (c) values the documents state that the database lacks.
An independent verifier confirms or refutes each claim.

Rules under test:
  * a claim confirmed by both writes a property_sources row (scalar) or reference_id
    (composition row) and sets names_simulant on the reference;
  * a claim the verifier refutes, or that the extractor marked unsupported, writes no row;
    the value stays in the database but is logged as withheld (the export hides it);
  * extractor and verifier disagreement writes no row and flags the value for a human;
  * a reference confirmed to name no simulant gets names_simulant = 0 and is never deleted;
  * a new value the documents state is inserted only when both agents agree, with its
    source row, and never overwrites an existing value.

Run:  python3 -m unittest scripts.tests.test_apply_provenance
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provenance import apply_group  # noqa: E402
from provenance import ensure_provenance_schema  # noqa: E402


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())
    ensure_provenance_schema(con)
    con.execute("INSERT INTO simulants (simulant_id, name, cohesion, friction_angle, bulk_density, composition_status) VALUES ('S010','CAS-1','1.2','35.0',NULL,'withheld_unverified')")
    con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type) VALUES ('R010','S010','Zheng et al. 2009 CAS-1 lunar soil simulant','composition')")
    con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type) VALUES ('R011','S010','Duri et al. 2022 review','review')")
    con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type) VALUES ('R012','S010','Patzwald et al. 2025 LX simulants','usage')")
    con.execute("INSERT INTO chemical_compositions (composition_id, simulant_id, component_type, component_name, value_wt_pct) VALUES ('CH-S010-01','S010','oxide','SiO2',49.24)")
    con.commit()
    con.close()


def extraction(**kw):
    base = {
        "simulant_id": "S010",
        "references": [
            {"reference_id": "R010", "names_simulant": True, "mention_quote": "CAS-1 lunar soil simulant was developed", "opened": True},
            {"reference_id": "R011", "names_simulant": True, "mention_quote": "CAS-1 (China)", "opened": True},
            {"reference_id": "R012", "names_simulant": False, "mention_quote": "", "opened": True},
        ],
        "values": [
            {"field": "cohesion", "stored": "1.2", "status": "supported", "reference_id": "R010", "location": "Table 4", "quote": "cohesion 1.2 kPa"},
            {"field": "friction_angle", "stored": "35.0", "status": "unsupported", "reference_id": "", "location": "", "quote": ""},
            {"field": "oxide:SiO2", "stored": "49.24", "status": "supported", "reference_id": "R010", "location": "Table 2", "quote": "SiO2 49.24"},
        ],
        "new_values": [
            {"field": "bulk_density", "value": "1.45", "reference_id": "R010", "location": "Table 4", "quote": "bulk density 1.45 g/cm3"},
        ],
    }
    base.update(kw)
    return base


def verification(**kw):
    base = {
        "simulant_id": "S010",
        "reference_checks": [{"reference_id": "R010", "verdict": "CONFIRMED"}, {"reference_id": "R011", "verdict": "CONFIRMED"}, {"reference_id": "R012", "verdict": "CONFIRMED"}],
        "value_checks": [
            {"field": "cohesion", "verdict": "CONFIRMED"},
            {"field": "friction_angle", "verdict": "CONFIRMED"},   # confirms it is unsupported
            {"field": "oxide:SiO2", "verdict": "CONFIRMED"},
        ],
        "new_value_checks": [{"field": "bulk_density", "verdict": "CONFIRMED"}],
    }
    base.update(kw)
    return base


class ApplyGroupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "a.sqlite"
        make_db(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def q(self, sql, *args):
        con = sqlite3.connect(self.db)
        r = con.execute(sql, args).fetchall()
        con.close()
        return r

    def test_confirmed_scalar_gets_a_source_row(self):
        apply_group(self.db, [extraction()], [verification()], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT reference_id, location, quote FROM property_sources WHERE simulant_id='S010' AND field='cohesion'"),
                         [("R010", "Table 4", "cohesion 1.2 kPa")])

    def test_confirmed_composition_row_cites_its_reference(self):
        apply_group(self.db, [extraction()], [verification()], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT reference_id FROM chemical_compositions WHERE composition_id='CH-S010-01'"), [("R010",)])

    def test_unsupported_value_gets_no_row_but_stays_in_db_and_is_logged(self):
        log = apply_group(self.db, [extraction()], [verification()], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT count(*) FROM property_sources WHERE field='friction_angle'"), [(0,)])
        self.assertEqual(self.q("SELECT friction_angle FROM simulants WHERE simulant_id='S010'"), [("35.0",)])
        self.assertTrue(any(e["field"] == "friction_angle" and e["outcome"] == "withheld: unsupported by any cited document" for e in log))

    def test_refuted_claim_writes_nothing_and_logs(self):
        v = verification(value_checks=[{"field": "cohesion", "verdict": "REFUTED", "problems": ["quote not in Table 4"]},
                                       {"field": "friction_angle", "verdict": "CONFIRMED"},
                                       {"field": "oxide:SiO2", "verdict": "CONFIRMED"}])
        log = apply_group(self.db, [extraction()], [v], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT count(*) FROM property_sources WHERE field='cohesion'"), [(0,)])
        self.assertTrue(any(e["field"] == "cohesion" and e["outcome"].startswith("withheld: refuted") for e in log))

    def test_disagreement_flags_for_review(self):
        # extractor says supported, verifier cannot decide
        v = verification(value_checks=[{"field": "cohesion", "verdict": "UNCERTAIN"},
                                       {"field": "friction_angle", "verdict": "CONFIRMED"},
                                       {"field": "oxide:SiO2", "verdict": "CONFIRMED"}])
        log = apply_group(self.db, [extraction()], [v], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT count(*) FROM property_sources WHERE field='cohesion'"), [(0,)])
        self.assertTrue(any(e["field"] == "cohesion" and e["needs_review"] for e in log))

    def test_reference_naming_the_simulant_is_marked_with_quote(self):
        apply_group(self.db, [extraction()], [verification()], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT names_simulant, mention_quote, checked_on FROM references_ WHERE reference_id='R010'"),
                         [(1, "CAS-1 lunar soil simulant was developed", "2026-09-22")])

    def test_reference_naming_no_simulant_is_marked_zero_not_deleted(self):
        apply_group(self.db, [extraction()], [verification()], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT names_simulant FROM references_ WHERE reference_id='R012'"), [(0,)])
        self.assertEqual(self.q("SELECT count(*) FROM references_ WHERE simulant_id='S010'"), [(3,)])

    def test_confirmed_new_value_is_inserted_with_its_source(self):
        apply_group(self.db, [extraction()], [verification()], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT bulk_density FROM simulants WHERE simulant_id='S010'"), [("1.45",)])
        self.assertEqual(self.q("SELECT reference_id FROM property_sources WHERE field='bulk_density'"), [("R010",)])

    def test_new_value_never_overwrites_an_existing_one(self):
        e = extraction(new_values=[{"field": "cohesion", "value": "9.9", "reference_id": "R011", "location": "p.3", "quote": "cohesion 9.9"}])
        v = verification(new_value_checks=[{"field": "cohesion", "verdict": "CONFIRMED"}])
        log = apply_group(self.db, [e], [v], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT cohesion FROM simulants WHERE simulant_id='S010'"), [("1.2",)])
        self.assertTrue(any(e2["field"] == "cohesion" and "conflict" in e2["outcome"] for e2 in log))

    def test_missing_verification_writes_nothing(self):
        log = apply_group(self.db, [extraction()], [], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT count(*) FROM property_sources"), [(0,)])
        self.assertTrue(all(e["needs_review"] for e in log if "field" in e))

    def test_confirmed_new_reference_becomes_a_row_and_values_can_cite_it(self):
        e = extraction(
            new_references=[{"temp_id": "NEW1", "local_path": "papers/LRS/Zheng_2009_CAS-1.pdf", "url": "", "doi": "10.1016/j.asr.2008.07.006",
                             "title": "CAS-1 lunar soil simulant", "authors": "Zheng, Wang, Ouyang", "year": 2009, "kind": "composition",
                             "mention_quote": "CAS-1 lunar soil simulant", "location": "title"}],
            values=[{"field": "friction_angle", "stored": "35.0", "status": "supported", "reference_id": "NEW1", "location": "Table 5", "quote": "friction angle 35.0"}],
            new_values=[],
        )
        v = verification(reference_checks=[{"reference_id": "R010", "verdict": "CONFIRMED"}, {"reference_id": "R011", "verdict": "CONFIRMED"},
                                           {"reference_id": "R012", "verdict": "CONFIRMED"}, {"reference_id": "NEW1", "verdict": "CONFIRMED"}],
                         value_checks=[{"field": "friction_angle", "verdict": "CONFIRMED"}], new_value_checks=[])
        apply_group(self.db, [e], [v], checked_on="2026-09-22")
        rows = self.q("SELECT reference_id, reference_type, title, doi, local_path, names_simulant, mention_quote FROM references_ WHERE simulant_id='S010' AND reference_id NOT IN ('R010','R011','R012')")
        self.assertEqual(len(rows), 1)
        rid, rtype, title, doi, local_path, names, quote = rows[0]
        self.assertEqual((rtype, title, doi, local_path, names, quote),
                         ("composition", "CAS-1 lunar soil simulant", "10.1016/j.asr.2008.07.006", "papers/LRS/Zheng_2009_CAS-1.pdf", 1, "CAS-1 lunar soil simulant"))
        self.assertEqual(self.q("SELECT reference_id FROM property_sources WHERE field='friction_angle'"), [(rid,)])

    def test_unconfirmed_new_reference_creates_nothing_and_flags_its_values(self):
        e = extraction(
            new_references=[{"temp_id": "NEW1", "title": "Some paper", "kind": "usage", "mention_quote": "CAS-1", "location": "p.1"}],
            values=[{"field": "friction_angle", "stored": "35.0", "status": "supported", "reference_id": "NEW1", "location": "p.2", "quote": "35.0"}],
            new_values=[],
        )
        v = verification(reference_checks=[{"reference_id": "NEW1", "verdict": "REFUTED", "problems": ["document does not name CAS-1"]}],
                         value_checks=[{"field": "friction_angle", "verdict": "CONFIRMED"}], new_value_checks=[])
        log = apply_group(self.db, [e], [v], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT count(*) FROM references_ WHERE simulant_id='S010'"), [(3,)])
        self.assertEqual(self.q("SELECT count(*) FROM property_sources WHERE field='friction_angle'"), [(0,)])
        self.assertTrue(any(x["field"] == "friction_angle" and x["needs_review"] for x in log))

    def test_new_reference_is_not_duplicated_on_rerun(self):
        e = extraction(
            new_references=[{"temp_id": "NEW1", "title": "CAS-1 lunar soil simulant", "kind": "composition", "doi": "10.1016/j.asr.2008.07.006",
                             "mention_quote": "CAS-1", "location": "title"}],
            values=[], new_values=[])
        v = verification(reference_checks=[{"reference_id": "NEW1", "verdict": "CONFIRMED"}], value_checks=[], new_value_checks=[])
        apply_group(self.db, [e], [v], checked_on="2026-09-22")
        apply_group(self.db, [e], [v], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT count(*) FROM references_ WHERE simulant_id='S010' AND doi='10.1016/j.asr.2008.07.006'"), [(1,)])

    def test_apply_is_idempotent(self):
        apply_group(self.db, [extraction()], [verification()], checked_on="2026-09-22")
        again = apply_group(self.db, [extraction()], [verification()], checked_on="2026-09-22")
        self.assertEqual(self.q("SELECT count(*) FROM property_sources WHERE simulant_id='S010'"), [(2,)])
        self.assertEqual([e for e in again if e["outcome"].startswith("source row written")], [])


if __name__ == "__main__":
    unittest.main()
