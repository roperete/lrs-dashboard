# Two reference sites: what we can take from them

2026-09-25. Research only; nothing in the database was changed.

Sites read with headless Chrome: page text, screenshots, the tables' own CSV exports, the
Streamlit app's user manual (PDF) and its dataset on Recherche Data Gouv. Our side was
compared against `public/data/data.json`, `export-suppression-2026-09-25.json` and the staging app.

## 1. What each site is

**Solar System Registry** (solarsystemregistry.org, v2.379, "in development").
- Author Adrien Normier, with the Cosmic Footprint Society.
- A 4D scene of human activity in space from 1940 to 2060: 192,480 objects on 46 layers,
  built from public catalogues (GCAT, JPL, Gaia, NASA and others).
- Pages: a database table, the scene, a legend, long documentation, a DOI-linked library and
  4,362 static "answer pages".
- Each value carries a provenance class (RAW measured, PROCESSED, MODELLED, SYNTHETIC,
  VISUAL). A 1σ is shown where a source gives one. Estimates are drawn in gold and never mixed
  with measurements.
- Licence SSR-GPL v2.0: free for public-interest use, anything else needs written
  permission. Bulk or API access needs an evaluation key, and the table shows at most 100
  rows per page. So "downloadable" is limited.
- Lunar content:
  - GCAT landers and the 12 lunar ascent sites.
  - NASA's "Catalogue of Manmade Material on the Moon" (694 items left at the Apollo sites).
  - 19 lunar impact sites, citing Wagner et al. 2017.
  - The IAU Gazetteer (9,086 lunar names).
  - LRO imagery and orbiter tracks.
- It holds no regolith properties.

**Lunar Regolith Database** (lunar-regolith-database.streamlit.app).
- Made by L. Gasteiner, N. Murdoch and O. D'Angelo at ISAE-SUPAERO, Toulouse. Funded by the ERC
  (1087060) and **CNES** (APR 10678, HERA): the same funder as ours.
- Paper: IJNAMG 2026, doi:10.1002/nag.70432 (arXiv 2602.03829). Dataset
  doi:10.57745/NTSZ8G, v2.0, 2026-06-11, licence Etalab 2.0. Code on GitHub, with a Hugging Face
  mirror. Last updated 27 Aug 2026.
- Five pages:
  - **Regolith**: 186 rows over 22 missions plus LRO: Surveyor I, III, V, VI, VII; Luna 9, 13, 16,
    17, 20, 21, 24; Apollo 11 to 17; Chang'e 3, 4, 5; Chandrayaan 3. There are 23 property
    columns: bulk density, friction angle, cohesion, bearing capacity, static bearing pressure,
    normal stress range, void ratio, grain density, compressibility, specific gravity, porosity,
    cone resistance, force, contact area, depth, sample ID and others. Each row also records the
    test, where it was done (122 in situ, 52 on Earth, 12 remote) and the atmosphere. 49 values
    are flagged `*` (estimated) or `**` (derived from estimates).
  - **Simulants**: 24 simulants, with bulk density, friction angle and cohesion only.
  - **Samples**: 2,038 Apollo sample records (type, mass, container). Also sieve data for 317
    subsamples, from Graf 1993.
  - **Mission pages**: a paragraph on how each mission measured the soil, plus its rows.
  - **Combined**: missions and simulants in one table.
- Each row names one source with a DOI or URL (29 distinct sources). The source is per row,
  not per value, and there is no page or quote.

## 2. Ideas worth adopting

Effort: S = up to a day, M = a few days, L = a week or more.

| # | Idea | Why it helps a researcher | Effort | From |
|---|---|---|---|---|
| 1 | **Several values per property.** Each value keeps its own test method, conditions (test density, normal stress range) and source. Keep ranges as min–max, never midpoints. | Friction angle and cohesion depend on density and test. LHS-1 is 31.5° in its fact sheet and 40.3° in Yin et al. 2023; both are true under their own conditions, but today one must win. Many values we hold but hide are midpoints of published ranges (section 4). | L | LRD rows; SSR keeps rival values ("erase none") |
| 2 | **Citable releases.** A DOI per data version (Zenodo or Recherche Data Gouv), an explicit data licence, a CITATION.cff and a "cite this version" line in the app. | Users can cite the exact version they used, and reviewers can reproduce it. Our README only says "open source". | S | LRD (paper plus dataset DOI); SSR (licence per source, attribution form) |
| 3 | **Lunar ground truth beside simulants.** Plot a simulant's value against each landing site's range, per test. Plot simulant grain-size curves against Apollo soil sieve curves. | The question users ask is "which simulant matches site X?". LRD's range chart shows why one number per site misleads: Apollo 11 bulk density runs from 0.75 to 1.93 g/cm³. | M, after the lunar values are verified | LRD range plot, combined table, grain-size curves |
| 4 | **Say what is not known.** Per simulant, mark each property as stated (with source), held but not yet verified, no source found, or omitted because the source disowns it. Print "no uncertainty stated" rather than a bare number, and show ± where the source gives it (e.g. AGK-2010, s = 0.0097 kg/l). | A reader learns whether to look elsewhere or wait for us. The states already exist in the suppression logs. | S–M | SSR ("the gaps are part of the record"; "a blank cell reads as exact") |
| 5 | **A static page per simulant**, with schema.org `Dataset` metadata, a sitemap and `llms.txt`. | Google Dataset Search, search engines and AI assistants could find values and quote their sources. Today crawlers get an empty app shell. | M | SSR answer pages |
| 6 | Per-producer report: what we hold from each producer or paper, and where two sources disagree. | Something to send to Exolith, Off Planet Research or ESA to get corrections. | S–M | SSR contributor report |
| 7 | Test details on Moon values (in situ, returned sample or remote; vacuum, N₂ or air; depth; sample ID) and a short "how it was measured" note per mission. | Values from footpad models, drive tubes and lab shear tests are not comparable without these details. | M | LRD mission pages |
| 8 | One timeline of simulant release years and lunar landings. | Shows which simulants followed which samples (e.g. PolyU-1 and WHU-1 after Chang'e-5). | S–M | SSR time scrubbing |
| 9 | Moon view: IAU feature names (USGS Gazetteer, public domain) and LROC landing-site mosaics from NASA Trek. | Places a site against named craters and maria. | M | SSR |
| 10 | "Raw record" view: a simulant's stored record with its sources, as JSON. | Power users can check exactly what we hold. | S | SSR "consolidated record (as baked)" |
| 11 | Free plot builder: any property against any other, grouped by type, producer or country, with range bars. | Quick comparisons without exporting. | M | LRD |

**Also:** both projects are CNES-funded and in Toulouse or Paris. A contact with the ISAE-SUPAERO
team could avoid duplicated work on the lunar side, where they are ahead.

## 3. What we already do better

**Against the Lunar Regolith Database**
- **Scope.** We have 148 simulants against 24. They have only density, friction and cohesion.
  We also have oxides, minerals, grain size, morphology, availability, buying links, figures of
  merit and a map of origins. All 24 of their simulants are already in ours.
- **Provenance.**
  - Theirs: one source string per row.
  - Ours, per value: the reference, the page or table, the quoted line and a second read.
  - We also check that each reference names the product.
- **Hygiene.** Their sources have errors we would catch:
  - The Lunar Sourcebook's DOI (42 rows) resolves to a 1992 book review by Collinson in
    *Phys. Earth Planet. Int.*, not to the book. Two Gromov rows carry the same wrong DOI, and one
    row has a broken DOI (`0.1016/…`).
  - TLS-01's DOI `10.3390/IAAI-2021-10583` is not registered. We found and fixed the same DOI on
    24 Sep.
  - The Apollo 15 catalogue citation has no authors in any of its 449 sample rows, and is cut
    short in 67 of them. Some rows have stray quote marks.
  - Three coordinates are wrong. Luna 16 is given as 47.24N 68.36E; it landed near 0.5°S
    56.4°E. Chang'e 4 is given as 45.44N; it is at 45.44°S. Apollo 14 is given as 19.67W; LROC
    puts it at 17.47°W.
- **Test conditions taken as product properties.**
  - Their EAC-1A "bulk density 1.95" is the density of the shear specimen. Our quote: "The
    cohesion of EAC-1A at a density of 1.95 g/cm3 was estimated to be 0.38 kPa".
  - They still show NAO-1's cohesion of 95.3 kPa, which its own paper calls an artefact; we omit
    it.
- **Links and speed.** Our views have shareable URLs (`?sim=…&f=…`); their app state never
  reaches the URL. Ours is static and instant; theirs sleeps and must be woken.
- **Export.** Our CSV carries source, location and quote for each value. Theirs carries one
  source per row.

**Against the Solar System Registry**
- **Downloads.** Our whole dataset downloads in one click. SSR needs an API key, pages its
  table at 100 rows and forbids non-public-interest use.
- **Quotes.** Our values carry a quoted line. SSR attributes values to a whole catalogue.
- **Its lunar data is compiled and has errors.**
  - GCAT gives Apollo 12's longitude as +23.38 (east); the site is at 23.4°W.
  - Apollo 14 is given at 19.27°W instead of 17.47°W.
  - SSR's object tree lists the Luna-16 ascent site under Earth.

## 4. Data leads

Our rule: a value counts only when a document names the product and states the value. Everything
below is a lead to read, not evidence.

### From the Lunar Regolith Database

**Simulant names:** none new. All 24 are in ours.

**Simulant values** we lack or hold but hide. Each is listed with the source their row cites.
In most cases the value we hold but hide is the **midpoint of their range**. It came from an
earlier import of this compilation, so the document will state a range, not our number.

| Simulant | Their value | Their cited source | Ours now |
|---|---|---|---|
| LSS-ISAC-1 | ρ 1.52, φ 36.34°, c 0.343 kPa | Anbazhagan et al. 2021, *Icarus*, 10.1016/j.icarus.2021.114511 | φ, c held and hidden (same numbers); ρ held as 1.065, which conflicts |
| CUG-1A | ρ 1.45, φ 21°, c 5 kPa | He & Xiao 2010, LPSC 41, abstract 1183 (2010LPI....41.1183H) | same numbers, hidden |
| WHU-1 | ρ 1.31–1.99, φ 40.57°, c 9.9 kPa | Teng et al. 2025, *Acta Geotechnica*, 10.1007/s11440-025-02553-7 | ρ 1.65 (midpoint), φ, c hidden |
| TLS-01 | φ 39.4–45°, c 1.65–8.14 kPa | Chancharoen et al. 2021; cited DOI not registered | midpoints hidden |
| GRC-3 | ρ 1.52–1.94, φ 37.8–47.8° | He, Zeng et al. 2013, *J. Aerosp. Eng.*, 10.1061/(ASCE)AS.1943-5525.0000162 | midpoints hidden |
| JSC-1A | ρ 1.63, φ 42.9–48.8°, c 1.4–2.4 kPa | Alshibli & Hasan 2009, *J. Geotech. Geoenv. Eng.*, 10.1061/(ASCE)GT.1943-5606.0000068 | 1.63 and midpoints, hidden |
| BP-1 | ρ 1.43–1.86 | Stoeser & Rickman 2010, NTRS 20100036344 | ρ 1.65 (midpoint) hidden; φ, c shown |
| MLS-1 | ρ 1.59–2.09, φ 41.4–62.3° | Slabic & Gruener 2024, *User's Guide Rev. A*, NTRS 20240011783 (Table 19 also gives nominal φ 51.7°) | ρ 1.84 and φ 51.85 (midpoints) hidden; c 0.8 shown |
| CSM-LHT-1 / CSM-LMT-1 / NU-LHT-4M | ρ 1.5–1.9 / 1.5–1.76 / 1.5–1.63 | same User's Guide | midpoints hidden |
| OB-1A | ρ 1.51–1.63 | NASA ARES OB-1 web page, 2010 | midpoint hidden |
| OPRH3N | φ 36°, c 12 kPa (ρ 1.32–1.5) | same User's Guide | φ, c hidden; ρ 1.2 shown (OPR data sheet) |
| JSC-1 | ρ 1.5 | McKay et al. 1994, LPI | 1.065 hidden (the same 1.065 also appears on LSS-ISAC-1 and FJS-1) |
| PolyU-1 | φ 40.3°, c 13.5 kPa | Zou et al. 2024, *IJMST*, 10.1016/j.ijmst.2024.08.006 | φ 38.0, c 6.75 hidden (different numbers); ρ 1.22 shown from the same paper (its loose state) |
| LHS-1 / LMS-1 | φ 40.3° / 40.5°, c 1.7 / 3.9 kPa, ρ 1.6 / 1.54 | Yin et al. 2023, *PSS*, 10.1016/j.pss.2022.105630 | fact-sheet values shown (31.49°, 0.311 kPa / 34.84°, 0.393 kPa). A candidate second value (idea 1), not a correction. |
| EAC-1A | ρ 1.95 | Engelschion et al. 2020 | not a lead: this is the test density (section 3) |

**Moon sites.**
- **Four missions missing from our Moon table.** LRD reads the first three from footpad and
  trench models:
  - Surveyor V: ρ 1.1, φ 35°, c 0.143 kPa. JPL TR 32-1246 (NTRS 19680003577).
  - Surveyor VI: ρ 0.7–1.6, φ 30–35°, c 0.07–1.7 kPa. JPL TR 32-1262 (NTRS 19680011500).
  - Surveyor VII: ρ 1.5, φ 37–39°, c 0.35–0.7 kPa. JPL TR 32-1264 (NTRS 19680028774).
  - Luna 9: no values, only a 1966 CIA intelligence digest.
- **LRO boulder tracks** give remote estimates (12 rows): Bickel et al. 2019, *JGR Planets*,
  10.1029/2018JE005876.
- **Current Moon-table values that match one of their rows**, with the source to check:

  | Value | Source their row cites |
  |---|---|
  | Apollo 16, ρ 1.68 | footprint analysis, Apollo 16 PSR, NASA SP-315 |
  | Chang'e 3, ρ 1.63 | Dong et al. 2016, *Icarus*, 10.1016/j.icarus.2016.09.010 |
  | Chandrayaan 3, ρ 1.3 | Mathew et al. 2025, *ASR*, 10.1016/j.asr.2025.01.022 |
  | Luna 13, 0.8 g/cm³, 32°, 0.49 kPa | Cherkasov & Shvarev 1973, 10.1007/BF01704945 |
  | Luna 21, 22.5°, 5 kPa | Cherkasov & Shvarev 1977, 10.1007/BF02093004 |
  | Surveyor I and III, ρ 1.5 | the JPL mission reports (flagged as estimates in LRD) |

- **Warning: many other Moon-table values are averages.** They equal the mean of the midpoints of
  all LRD rows for that mission, mixing methods and sources:
  - Luna 16: 1.44 g/cm³, 26.7°
  - Luna 20: 1.31 g/cm³, 24.4°, 4.66 kPa
  - Apollo 15: 48.1°
  - Surveyor I: 4.52 kPa
  - Luna 24: 1.85 g/cm³, the midpoint of 1.6–2.1

  No document states these values. Under "empty over wrong" they should be emptied until each is
  replaced by a stated value with its test.
- LRD's Chang'e 4 and 5 rows hold no strength values, so there is nothing to take there.

**Lunar samples.**
- Graf 1993, *Lunar Soils Grain Size Catalog*, NASA RP-1265, has sieve data for 3 of our 7
  reference samples: 10084 (subsample 10084,79), 12070 (two subsamples) and 14163 (two
  subsamples). LRD lists no subsamples for 15271, 60501, 71501 or the Chang'e-5 sample. Its D50
  may be its own calculation, so check it against Graf.
- The Apollo sample catalogues give sample type and mass for 2,038 samples: JSC 12522, NASA TR
  R-353, JSC 14240, MSC 03209, MSC 03210 and MSC 03211.

### From the Solar System Registry

- **Wagner et al. 2017**, "Coordinates of anthropogenic features on the Moon", *Icarus* 283,
  doi:10.1016/j.icarus.2016.05.011. SSR cites it for lunar impact sites. It is a peer-reviewed
  LROC source to check our withdrawn landing-site coordinates against (`lunar_sites` is empty
  pending verification).
- **GCAT sites table** (J. McDowell, planet4589.org, CC BY 4.0, updated 2026-09-24). It gives
  coordinates and dates for the 12 lunar ascent sites: Apollo 11, 12, 14, 15, 16, 17; Luna 16,
  20, 23, 24; Chang'e-5 and Chang'e-6 (41.6384°S, 153.9855°W). It is a compilation with the
  errors listed in section 3, so it is a lead only.
- NASA History Program Office, *Catalogue of Manmade Material on the Moon* (2012): hardware left
  at the Apollo sites. It has no regolith data and is low priority.

## Working files

The CSVs, manual text and screenshots are in the session scratchpad (`refsites/`) and are not
kept in the repository. Their dataset can be downloaded again from doi:10.57745/NTSZ8G.
