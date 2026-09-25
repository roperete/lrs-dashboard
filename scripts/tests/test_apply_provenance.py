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


class StatedValueTests(unittest.TestCase):
    """What reaches a numeric column must be a number.

    Readers quote values as printed. Written verbatim into a REAL column, a string such as
    "22.4 (vol%)" stays text and the page drops the row without a word — 123 composition
    values and six physical values went missing that way on 2026-09-23. The number is now
    parsed at write time, the statement kept verbatim beside it, and anything that is not a
    single number goes to a human.
    """

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

    def run_new(self, field, value):
        e = extraction(values=[], new_values=[{"field": field, "value": value, "reference_id": "R010", "location": "Table 2", "quote": f"{field} {value}"}])
        v = verification(value_checks=[], new_value_checks=[{"field": field, "verdict": "CONFIRMED"}])
        return apply_group(self.db, [e], [v], checked_on="2026-09-23")

    def test_an_oxide_with_its_uncertainty_is_stored_as_a_number_and_the_statement_kept(self):
        self.run_new("oxide:TiO2", "2.33 ± 0.03 wt.-%")
        rows = self.q("SELECT value_wt_pct, typeof(value_wt_pct), value_text, reference_id FROM chemical_compositions WHERE component_name='TiO2'")
        self.assertEqual(rows, [(2.33, "real", "2.33 ± 0.03 wt.-%", "R010")])

    def test_a_mineral_in_volume_percent_keeps_its_basis(self):
        self.run_new("mineral:Plagioclase", "38.8 (vol%; An 80)")
        self.assertEqual(self.q("SELECT value_pct, value_text FROM mineral_compositions WHERE component_name='Plagioclase'"),
                         [(38.8, "38.8 (vol%; An 80)")])

    def test_a_plain_number_needs_no_statement(self):
        self.run_new("oxide:MgO", "8.18")
        self.assertEqual(self.q("SELECT value_wt_pct, value_text FROM chemical_compositions WHERE component_name='MgO'"), [(8.18, None)])

    def test_presence_without_a_quantity_is_not_a_composition_row(self):
        log = self.run_new("mineral:Plagioclase", "present (checkmark, no wt% reported)")
        self.assertEqual(self.q("SELECT count(*) FROM mineral_compositions WHERE component_name='Plagioclase'"), [(0,)])
        hit = [e for e in log if e.get("field") == "mineral:Plagioclase"]
        self.assertEqual(hit[0]["outcome"], "flagged: not a single number, kept out of the table")
        self.assertTrue(hit[0]["needs_review"])
        self.assertEqual(hit[0]["value"], "present (checkmark, no wt% reported)")

    def test_a_detection_limit_is_not_a_composition_row(self):
        self.run_new("oxide:P2O5", "<0.02")
        self.assertEqual(self.q("SELECT count(*) FROM chemical_compositions WHERE component_name='P2O5'"), [(0,)])

    def test_a_numeric_physical_property_is_parsed(self):
        self.run_new("particle_size_d50", "38.22 μm")
        self.assertEqual(self.q("SELECT particle_size_d50, typeof(particle_size_d50) FROM simulants WHERE simulant_id='S010'"), [(38.22, "real")])

    def test_a_range_for_a_numeric_property_is_refused(self):
        log = self.run_new("particle_size_d50", "41–61 µm (median; mean 53–81 µm)")
        self.assertEqual(self.q("SELECT particle_size_d50 FROM simulants WHERE simulant_id='S010'"), [(None,)])
        self.assertEqual(self.q("SELECT count(*) FROM property_sources WHERE field='particle_size_d50'"), [(0,)])
        self.assertTrue(any(e.get("field") == "particle_size_d50" and e["outcome"].startswith("flagged: not a single number") for e in log))

    def test_a_text_property_keeps_the_statement_as_it_is(self):
        self.run_new("particle_size_distribution", "41–61 µm (median; mean 53–81 µm)")
        self.assertEqual(self.q("SELECT particle_size_distribution FROM simulants WHERE simulant_id='S010'"),
                         [("41–61 µm (median; mean 53–81 µm)",)])


class RegistryIsNotEvidenceTests(unittest.TestCase):
    """The Global Registry of Lunar Regolith Simulants is this project's own spreadsheet —
    the unverified data the audit exists to check. A reader found a copy in the NotebookLM
    export folder and cited it for five simulants on 2026-09-23. Citing it proves nothing."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "a.sqlite"
        make_db(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_new_reference_to_the_registry_is_refused(self):
        e = extraction(values=[], new_values=[{"field": "bulk_density", "value": "1.45", "reference_id": "NEW1", "location": "row 12", "quote": "CAS-1,1.45"}],
                       new_references=[{"temp_id": "NEW1", "title": "Global Registry of Lunar Regolith Simulants (CSV compilation)",
                                        "kind": "general", "local_path": "papers/LRS/Sources/Global Registry of Lunar Regolith Simulants.html",
                                        "mention_quote": "CAS-1", "location": "row 12"}])
        v = verification(reference_checks=[{"reference_id": "NEW1", "verdict": "CONFIRMED"}], value_checks=[],
                         new_value_checks=[{"field": "bulk_density", "verdict": "CONFIRMED"}])
        log = apply_group(self.db, [e], [v], checked_on="2026-09-23")
        con = sqlite3.connect(self.db)
        self.assertEqual(con.execute("SELECT count(*) FROM references_ WHERE title LIKE 'Global Registry%'").fetchone(), (0,))
        self.assertEqual(con.execute("SELECT bulk_density FROM simulants WHERE simulant_id='S010'").fetchone(), (None,))
        con.close()
        self.assertTrue(any(e["outcome"] == "refused: the project's own registry is not evidence" for e in log))


class TemporaryIdTests(unittest.TestCase):
    """A reader may name its new documents in any form, not only NEW1, NEW2.

    On 2026-09-24 two readers named theirs "S117-N1" and "S023-N4". The references were
    created, but values citing them were translated only when the id began with "NEW", so
    eleven values were written citing ids that exist nowhere. The integrity check caught it.
    """

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

    def new_ref_extraction(self, temp_id, cite):
        return extraction(
            values=[],
            new_references=[{"temp_id": temp_id, "title": "Characterisation of CAS-1", "kind": "composition",
                             "local_path": "papers/LRS/cas1.pdf", "mention_quote": "CAS-1", "location": "p.1"}],
            new_values=[{"field": "mineral:Olivine", "value": "12.5", "reference_id": cite, "location": "Table 3", "quote": "olivine 12.5"},
                        {"field": "bulk_density", "value": "1.45", "reference_id": cite, "location": "Table 4", "quote": "1.45"}])

    def checks(self, temp_id):
        return verification(reference_checks=[{"reference_id": temp_id, "verdict": "CONFIRMED"}], value_checks=[],
                            new_value_checks=[{"field": "mineral:Olivine", "verdict": "CONFIRMED"}, {"field": "bulk_density", "verdict": "CONFIRMED"}])

    def test_a_temporary_id_in_any_form_is_translated(self):
        apply_group(self.db, [self.new_ref_extraction("S010-N1", "S010-N1")], [self.checks("S010-N1")], checked_on="2026-09-24")
        rid = self.q("SELECT reference_id FROM references_ WHERE title='Characterisation of CAS-1'")[0][0]
        self.assertTrue(rid.startswith("RN-S010-"))
        self.assertEqual(self.q("SELECT reference_id FROM mineral_compositions WHERE component_name='Olivine'"), [(rid,)])
        self.assertEqual(self.q("SELECT reference_id FROM property_sources WHERE field='bulk_density'"), [(rid,)])

    def test_a_value_citing_an_id_that_exists_nowhere_writes_nothing(self):
        e = extraction(values=[], new_values=[{"field": "mineral:Olivine", "value": "12.5", "reference_id": "R999", "location": "T3", "quote": "12.5"}])
        v = verification(value_checks=[], new_value_checks=[{"field": "mineral:Olivine", "verdict": "CONFIRMED"}])
        log = apply_group(self.db, [e], [v], checked_on="2026-09-24")
        self.assertEqual(self.q("SELECT count(*) FROM mineral_compositions WHERE component_name='Olivine'"), [(0,)])
        self.assertTrue(any(x["outcome"] == "flagged: cites a reference that does not exist" for x in log))

    def test_reapplying_a_value_already_stored_restores_a_missing_source_row(self):
        """Repairing a run means deleting its bad rows and applying it again; a value
        already in the column must regain its source row rather than be skipped."""
        apply_group(self.db, [self.new_ref_extraction("NEW1", "NEW1")], [self.checks("NEW1")], checked_on="2026-09-24")
        con = sqlite3.connect(self.db); con.execute("DELETE FROM property_sources WHERE field='bulk_density'"); con.commit(); con.close()
        apply_group(self.db, [self.new_ref_extraction("NEW1", "NEW1")], [self.checks("NEW1")], checked_on="2026-09-24")
        self.assertEqual(len(self.q("SELECT reference_id FROM property_sources WHERE field='bulk_density'")), 1)


class ColumnUnitApplyTests(unittest.TestCase):
    """A new cohesion stated in pascals is stored in kilopascals, the unit the page prints."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "a.sqlite"
        make_db(self.db)
        con = sqlite3.connect(self.db); con.execute("UPDATE simulants SET cohesion=NULL, friction_angle=NULL WHERE simulant_id='S010'"); con.commit(); con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def run_new(self, field, value):
        e = extraction(values=[], new_values=[{"field": field, "value": value, "reference_id": "R010", "location": "T5", "quote": value}])
        v = verification(value_checks=[], new_value_checks=[{"field": field, "verdict": "CONFIRMED"}])
        return apply_group(self.db, [e], [v], checked_on="2026-09-24")

    def value(self, field):
        con = sqlite3.connect(self.db); r = con.execute(f"SELECT {field} FROM simulants WHERE simulant_id='S010'").fetchone()[0]; con.close()
        return r

    def test_pascals_become_kilopascals(self):
        self.run_new("cohesion", "185.2 Pa (AP-cohesive strength, ambient pressure, rheometer)")
        self.assertAlmostEqual(float(self.value("cohesion")), 0.1852)

    def test_a_degree_written_as_the_ordinal_sign_is_stored_bare(self):
        self.run_new("friction_angle", "46.12 º")
        self.assertAlmostEqual(float(self.value("friction_angle")), 46.12)

    def test_two_values_for_two_conditions_are_refused(self):
        log = self.run_new("cohesion", "3.1 kPa (low stress level); 18.80 kPa (conventional stress level)")
        self.assertIsNone(self.value("cohesion"))
        self.assertTrue(any(e.get("field") == "cohesion" and e["outcome"].startswith("flagged: not a single number") for e in log))


class OneAnalysisPerTableTests(unittest.TestCase):
    """A composition table is one analysis of one sample, from one document.

    On 2026-09-24 the audit found nine tables assembled from several documents: EAC-1's
    mineral table was two complete analyses stacked (194.5%), NU-LHT-2M's oxides carried
    Cr2O3, MnO, P2O5 and a total iron grafted on from another paper. A row from a second
    document is not merged into a table another document already fills.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "a.sqlite"
        make_db(self.db)            # S010 has SiO2 49.24, cited to R010 once applied

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_row_from_a_second_document_is_not_merged(self):
        apply_group(self.db, [extraction()], [verification()], checked_on="2026-09-24")   # SiO2 cites R010
        e = extraction(values=[], new_values=[{"field": "oxide:Cr2O3", "value": "0.12", "reference_id": "R011", "location": "T4", "quote": "Cr2O3 0.12"}])
        v = verification(value_checks=[], new_value_checks=[{"field": "oxide:Cr2O3", "verdict": "CONFIRMED"}])
        log = apply_group(self.db, [e], [v], checked_on="2026-09-24")
        con = sqlite3.connect(self.db)
        self.assertEqual(con.execute("SELECT count(*) FROM chemical_compositions WHERE component_name='Cr2O3'").fetchone(), (0,))
        con.close()
        self.assertTrue(any(x["outcome"] == "not merged: the table already holds another document's analysis" for x in log))

    def test_rows_from_the_same_document_still_complete_its_table(self):
        apply_group(self.db, [extraction()], [verification()], checked_on="2026-09-24")
        e = extraction(values=[], new_values=[{"field": "oxide:TiO2", "value": "1.9", "reference_id": "R010", "location": "T2", "quote": "TiO2 1.9"}])
        v = verification(value_checks=[], new_value_checks=[{"field": "oxide:TiO2", "verdict": "CONFIRMED"}])
        apply_group(self.db, [e], [v], checked_on="2026-09-24")
        con = sqlite3.connect(self.db)
        self.assertEqual(con.execute("SELECT reference_id FROM chemical_compositions WHERE component_name='TiO2'").fetchone(), ("R010",))
        con.close()


class ReferenceOwnershipTests(unittest.TestCase):
    """A value cites a reference in its own simulant's list.

    The page numbers references within each simulant's list, so a value citing another
    simulant's reference row gets no superscript. On 2026-09-24 the audit found MLS-1's
    lunar analogue citing R066, MLS-2's row for the paper both share.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "a.sqlite"
        make_db(self.db)
        con = sqlite3.connect(self.db)
        con.execute("INSERT INTO simulants (simulant_id, name) VALUES ('S099','Other')")
        con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, title, doi, names_simulant) "
                    "VALUES ('R099','S099','Taylor 2016','Evaluations of lunar regolith simulants','10.1016/j.pss.2016.04.005',1)")
        con.commit(); con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_value_citing_another_simulants_reference_writes_nothing(self):
        e = extraction(values=[{"field": "cohesion", "stored": "1.2", "status": "supported", "reference_id": "R099", "location": "T2", "quote": "cohesion 1.2"}], new_values=[])
        v = verification(value_checks=[{"field": "cohesion", "verdict": "CONFIRMED"}], new_value_checks=[])
        log = apply_group(self.db, [e], [v], checked_on="2026-09-24")
        con = sqlite3.connect(self.db)
        self.assertEqual(con.execute("SELECT count(*) FROM property_sources WHERE simulant_id='S010' AND field='cohesion'").fetchone(), (0,))
        con.close()
        self.assertTrue(any(x["outcome"] == "flagged: cites a reference from another simulant's list" for x in log))
