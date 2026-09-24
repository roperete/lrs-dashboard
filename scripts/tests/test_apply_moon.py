"""Applying the Moon provenance run: a value of a landing site or lunar sample gets a source
only when the reader traced it and the checker confirmed that; it is corrected only to what a
confirmed document states. Anything else leaves it without a source, so the export hides it.

Run:  python3 -m unittest scripts.tests.test_apply_moon
"""

import json
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402
from apply_moon import apply_results  # noqa: E402


def ref(tid, title, path, quote="Apollo 11 landed", kind="paper"):
    return {"temp_id": tid, "title": title, "local_path": path, "kind": kind, "mention_quote": quote, "location": "p. 1"}


def val(field, stored, status, value, rid="R1", quote="q"):
    return {"field": field, "stored": stored, "status": status, "value_in_source": value, "reference_id": rid, "location": "Table 1", "quote": quote}


class ApplyMoonTests(unittest.TestCase):
    def setUp(self):
        con = sqlite3.connect(":memory:")
        con.executescript((ROOT / "scripts" / "schema.sql").read_text()); ensure_provenance_schema(con)
        con.execute("INSERT INTO lunar_sites (site_id, name, mission, programme, date, lat, lng, samples_returned, bulk_density, cohesion, friction_angle, bearing_capacity) "
                    "VALUES ('A11','Apollo 11','Apollo 11','Apollo','July 20, 1969',0.67409,23.47297,'21.5 kg',1.61,1.06,40.7,10.0)")
        con.execute("INSERT INTO lunar_references (sample_id, mission, landing_site, type, chemical_composition, mineral_composition) "
                    "VALUES ('10084','Apollo 11','Mare Tranquillitatis','Mare','{\"SiO2\": 42.2, \"TiO2\": 7.8}','{\"Ilmenite\": 15.0}')")
        self.con = con

    def run_one(self, entity, reading_values, checks, refs=None, ref_verdicts=None):
        refs = refs or [ref("R1", "Wagner et al. 2017", "papers/lunar/wagner.pdf")]
        ref_verdicts = ref_verdicts or {r["temp_id"]: "CONFIRMED" for r in refs}
        results = {"results": [{"group": "g", "ids": [entity],
            "reading": {"entities": [{"id": entity, "references": refs, "values": reading_values}]},
            "check": {"entities": [{"id": entity,
                "reference_checks": [{"temp_id": t, "verdict": v} for t, v in ref_verdicts.items()],
                "value_checks": [{"field": f, "verdict": v, "note": "", **extra} for f, (v, extra) in checks.items()]}]}}]}
        return apply_results(self.con, results, checked_on="2026-09-25")

    def sources(self, entity):
        return {r[0]: r[1:] for r in self.con.execute("SELECT field, document_id, quote, value_text FROM lunar_sources WHERE entity_id=?", (entity,))}

    def test_a_confirmed_supported_value_gets_its_source(self):
        self.run_one("A11", [val("lat", "0.67409", "supported", "0.67409", quote="0.67409 N")], {"lat": ("CONFIRMED", {})})
        self.assertIn("lat", self.sources("A11"))
        doc = self.con.execute("SELECT title, local_path, checked_on FROM lunar_documents").fetchone()
        self.assertEqual(doc, ("Wagner et al. 2017", "papers/lunar/wagner.pdf", "2026-09-25"))
        self.assertEqual(self.con.execute("SELECT count(*) FROM lunar_mentions WHERE entity_id='A11'").fetchone(), (1,))

    def test_a_confirmed_differing_value_is_corrected_to_the_source(self):
        log = self.run_one("A11", [val("samples_returned", "21.5 kg", "differs", "21.55 kg")], {"samples_returned": ("CONFIRMED", {})})
        self.assertEqual(self.con.execute("SELECT samples_returned FROM lunar_sites").fetchone(), ("21.55 kg",))
        self.assertIn("samples_returned", self.sources("A11"))
        self.assertIn("corrected to the source", [e["outcome"] for e in log])

    def test_units_are_converted_to_the_column_unit(self):
        self.run_one("A11", [val("cohesion", "1.06 kPa", "differs", "0.1 N/cm²"), val("bulk_density", "1.61 g/cm³", "differs", "1540 kg/m3")],
                     {"cohesion": ("CONFIRMED", {}), "bulk_density": ("CONFIRMED", {})})
        self.assertEqual(self.con.execute("SELECT cohesion, bulk_density FROM lunar_sites").fetchone(), (1.0, 1.54))

    def test_ranges_unfound_uncertain_and_refuted_values_get_no_source(self):
        log = self.run_one("A11", [val("friction_angle", "40.7 °", "range_only", "37-45°"), val("bearing_capacity", "10 kPa", "not_found", "", rid=""),
                                   val("date", "July 20, 1969", "supported", "July 20, 1969"), val("lng", "23.47297", "supported", "23.47297")],
                           {"friction_angle": ("CONFIRMED", {}), "bearing_capacity": ("CONFIRMED", {}), "date": ("UNCERTAIN", {}),
                            "lng": ("REFUTED", {"correct_value": "23.47314", "correct_reference": "R1"})})
        self.assertEqual(self.sources("A11"), {})
        self.assertEqual(self.con.execute("SELECT friction_angle, lng FROM lunar_sites").fetchone(), (40.7, 23.47297))   # kept in the database, hidden on export
        review = [e for e in log if e.get("needs_review")]
        self.assertEqual([e["field"] for e in review], ["lng"])

    def test_a_value_citing_an_unconfirmed_document_gets_no_source(self):
        self.run_one("A11", [val("lat", "0.67409", "supported", "0.67409")], {"lat": ("CONFIRMED", {})}, ref_verdicts={"R1": "REFUTED"})
        self.assertEqual(self.sources("A11"), {})
        self.assertEqual(self.con.execute("SELECT count(*) FROM lunar_documents").fetchone(), (0,))

    def test_one_document_is_stored_once_across_entities(self):
        r = [ref("R1", "Lunar Sourcebook", "papers/LRS/LunarSourceBook.pdf")]
        self.run_one("A11", [val("lat", "0.67409", "supported", "0.67409")], {"lat": ("CONFIRMED", {})}, refs=r)
        self.run_one("10084", [val("oxide:SiO2", "42.2 wt%", "supported", "42.2")], {"oxide:SiO2": ("CONFIRMED", {})}, refs=r)
        self.assertEqual(self.con.execute("SELECT count(*) FROM lunar_documents").fetchone(), (1,))

    def test_sample_composition_values_are_sourced_and_corrected(self):
        self.run_one("10084", [val("oxide:SiO2", "42.2 wt%", "supported", "42.2 wt%"), val("oxide:TiO2", "7.8 wt%", "differs", "7.5 wt%"),
                               val("mineral:Ilmenite", "15.0", "not_found", "", rid="")],
                     {"oxide:SiO2": ("CONFIRMED", {}), "oxide:TiO2": ("CONFIRMED", {}), "mineral:Ilmenite": ("CONFIRMED", {})})
        chem = json.loads(self.con.execute("SELECT chemical_composition FROM lunar_references").fetchone()[0])
        self.assertEqual(chem, {"SiO2": 42.2, "TiO2": 7.5})
        self.assertEqual(set(self.sources("10084")), {"oxide:SiO2", "oxide:TiO2"})

    def test_a_description_is_sourced_only_when_every_claim_is(self):
        vals = [val("description:first crewed landing", "First human landing on the Moon.", "supported", "the first crewed landing", quote="first crewed landing"),
                val("description:collected basalts", "Collected basaltic rocks", "supported", "basalts were collected", quote="basalts")]
        self.run_one("A11", vals, {v["field"]: ("CONFIRMED", {}) for v in vals})
        self.assertIn("description", self.sources("A11"))
        self.con.execute("DELETE FROM lunar_sources")
        vals[1]["status"] = "not_found"
        log = self.run_one("A11", vals, {v["field"]: ("CONFIRMED", {}) for v in vals})
        self.assertNotIn("description", self.sources("A11"))
        self.assertTrue(any(e["field"] == "description" and e.get("needs_review") for e in log))

    def test_applying_twice_changes_nothing_more(self):
        args = ("A11", [val("samples_returned", "21.5 kg", "differs", "21.55 kg")], {"samples_returned": ("CONFIRMED", {})})
        self.run_one(*args); self.run_one(*args)
        self.assertEqual(self.con.execute("SELECT count(*) FROM lunar_sources").fetchone(), (1,))
        self.assertEqual(self.con.execute("SELECT count(*) FROM lunar_documents").fetchone(), (1,))


if __name__ == "__main__":
    unittest.main()
