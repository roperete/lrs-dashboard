"""A wiki page is never a source (owner, 2026-09-25): the apply steps refuse it and the export
never publishes it, even if one is on record. A value it gives is shown only when another
document states it.

Run:  python3 -m unittest scripts.tests.test_source_policy
"""

import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402
from source_policy import is_wiki, is_wiki_document, strip_wiki_links  # noqa: E402
from moon import export_moon  # noqa: E402
from export_json import shown_references, drop_wiki_citations  # noqa: E402
from apply_moon import apply_results  # noqa: E402


class WikiIsNotASource(unittest.TestCase):
    def test_wiki_pages_are_recognised(self):
        for t in ("https://en.wikipedia.org/wiki/Luna_16", "https://the-moon.us/wiki/Apollo_11_Site",
                  "papers/lunar/Wikipedia_Luna16_wikitext.txt", "Lunar regolith simulant - Wikipedia",
                  "Apollo 12 Site (wiki page, coordinates per Davies and Colvin, 2000)", "https://www.wikiwand.com/en/Luna_16"):
            self.assertTrue(is_wiki(t), t)

    def test_papers_and_files_on_wiki_hosts_are_not_wikis(self):
        for t in ("https://doi.org/10.1029/1999JE001165", "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1969-059C",
                  "https://static.igem.wiki/teams/5108/pdf/lsp-2-spec-sheet-dec2023-pptx.pdf", "papers/lunar/Wagner_2017_Icarus.pdf",
                  "Lunar coordinates in the regions of the Apollo landers"):
            self.assertFalse(is_wiki(t), t)

    def test_the_export_never_lists_a_wiki_reference(self):
        refs = [{"reference_id": "R1", "url": "https://en.wikipedia.org/wiki/Lunar_regolith_simulant", "names_simulant": 1},
                {"reference_id": "R2", "doi": "10.1016/j.icarus.2021.114511", "names_simulant": 1}]
        self.assertEqual([r["reference_id"] for r in shown_references(refs)], ["R2"])
        self.assertEqual(drop_wiki_citations([{"reference_id": "R1"}, {"reference_id": "R2"}, {"reference_id": None}], {"R1"}),
                         [{"reference_id": "R2"}, {"reference_id": None}])


    def test_wiki_links_are_taken_out_of_a_link_list_and_nothing_else_changes(self):
        self.assertEqual(strip_wiki_links("https://en.wikipedia.org/wiki/Kiruna_mine; https://www.mindat.org/loc-1"), "https://www.mindat.org/loc-1")
        self.assertIsNone(strip_wiki_links("https://en.wikipedia.org/wiki/Tellnes_mine"))
        self.assertEqual(strip_wiki_links("Norway;Italy"), "Norway;Italy")     # no wiki: left exactly as it was


class MoonWithoutWikis(unittest.TestCase):
    def setUp(self):
        con = sqlite3.connect(":memory:")
        con.executescript((ROOT / "scripts" / "schema.sql").read_text()); ensure_provenance_schema(con)
        con.execute("INSERT INTO lunar_sites (site_id, name, mission, programme, date, lat, lng) VALUES "
                    "('S1','Surveyor 1','Surveyor 1','Other','June 2, 1966',-2.474,-43.339),"
                    "('L16','Luna 16','Luna 16','Luna','September 20, 1970',-0.5137,56.3638)")
        con.execute("INSERT INTO lunar_documents (document_id, title, url, local_path, kind) VALUES "
                    "('LD-045','Surveyor 1','https://en.wikipedia.org/wiki/Surveyor_1','papers/lunar/Wikipedia_Surveyor1.html','web'),"
                    "('LD-035','NASA NSSDCA Master Catalog - Luna 16','https://nssdc.gsfc.nasa.gov/x','papers/lunar/n.html','catalogue'),"
                    "('LD-015','Celebrated Moon Rocks (PSRD)','http://www.psrd.hawaii.edu/x','papers/lunar/p.html','web'),"
                    "('LD-013','Open Database of Lunar Regolith - Dataset_Regolith.csv','https://github.com/x','papers/lunar/g.csv','compilation')")
        con.executemany("INSERT INTO lunar_sources (entity_id, field, document_id, location, quote) VALUES (?,?,?,?,?)",
                        [("S1", "lat", "LD-045", "infobox", "2.474 S"), ("S1", "lng", "LD-045", "infobox", "43.339 W"),
                         ("S1", "date", "LD-045", "infobox", "June 2, 1966"),
                         ("L16", "lat", "LD-035", "p", "0.5137 S"), ("L16", "lng", "LD-035", "p", "56.3638 E"),
                         ("L16", "date", "LD-045", "p", "wrongly cited"),
                         ("L16", "samples_returned", "LD-015", "table", "0.101 kg"), ("L16", "friction_angle", "LD-013", "row", "20")])
        self.con = con

    def test_a_site_placed_only_by_a_wiki_leaves_the_map(self):
        out = export_moon(self.con)
        self.assertEqual([s["id"] for s in out["lunar_sites"]], ["L16"])
        self.assertIsNone(out["lunar_sites"][0]["date"])            # its only source was the wiki
        self.assertNotIn("LD-045", [d["document_id"] for d in out["lunar_documents"]])
        self.assertTrue(all(s["document_id"] != "LD-045" for s in out["lunar_sources"]))

    def test_web_articles_and_compilations_are_not_moon_sources(self):
        self.con.execute("UPDATE lunar_sites SET samples_returned='0.101 kg', friction_angle=20 WHERE site_id='L16'")
        l16 = export_moon(self.con)["lunar_sites"][0]
        self.assertIsNone(l16["samples_returned"])
        self.assertEqual(l16["geotechnical"], {})
        self.assertEqual(sorted(d["document_id"] for d in export_moon(self.con)["lunar_documents"]), ["LD-035"])

    def test_the_moon_apply_refuses_a_wiki_document(self):
        ref = {"temp_id": "R1", "title": "Luna 21 - Wikipedia", "url": "https://en.wikipedia.org/wiki/Luna_21",
               "local_path": "papers/lunar/Wikipedia_Luna21.txt", "kind": "web", "mention_quote": "Luna 21", "location": "lead"}
        results = {"results": [{"group": "g", "ids": ["L16"],
            "reading": {"entities": [{"id": "L16", "references": [ref],
                "values": [{"field": "date", "stored": "x", "status": "supported", "value_in_source": "x", "reference_id": "R1", "location": "l", "quote": "q"}]}]},
            "check": {"entities": [{"id": "L16", "reference_checks": [{"temp_id": "R1", "verdict": "CONFIRMED"}],
                "value_checks": [{"field": "date", "verdict": "CONFIRMED", "note": ""}]}]}}]}
        log = apply_results(self.con, results, checked_on="2026-09-25")
        self.assertTrue(any("wiki page is not a source" in e["outcome"] for e in log))
        self.assertIsNone(self.con.execute("SELECT 1 FROM lunar_documents WHERE url LIKE '%Luna_21%'").fetchone())
        self.assertIsNone(self.con.execute("SELECT 1 FROM lunar_sources WHERE entity_id='L16' AND field='date' AND quote='q'").fetchone())


if __name__ == "__main__":
    unittest.main()
