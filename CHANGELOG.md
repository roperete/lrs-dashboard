# Changelog

Every push carries a new version. `python3 scripts/bump_version.py --body "..."` writes both
the sidebar label and the section below it; `scripts/push_staging.sh` refuses to push while the
sidebar still shows the version already deployed. Data changes are logged per field under
`documentation/`.

## v2.9.19 — 2026-09-25 (staging)

Two more crash fixes; the 2D Earth map in Equal Earth; drag to close the side panels; the document's name on every citation hover.

**Interface**
- Sorting the table by Country, or typing in the Reference filter, blanked the page, like the
  search did in v2.9.17: the three Lumina simulants have no country yet, and 61 references
  have a title but no citation text. Both now allow empty fields; the Reference filter also
  searches titles and authors, so those references can be found.
- The 2D Earth map uses the Equal Earth projection, endorsed by the UN General Assembly on
  4 September 2026 (resolution A/80/L.104) in place of Mercator, which enlarges land towards
  the poles. Map tiles exist only in Mercator, so the base map is now drawn: ocean, country
  outlines and a 30° graticule. Coordinates are unchanged; only how they are drawn.
- Hovering a citation mark [n] now shows first which document it is (author, year, title),
  then the page and the quote. Before, nothing on the hover said which reference [n] was.
- The right panel and the left panel each have a grip on their inner edge: drag it towards the
  panel's own edge to close it (down on phones). A short drag springs back.
- The lunar comparison table printed "+" for every difference; it now shows the sign.

**Process**
- `check:projection` tests the map projection against the published Equal Earth formulas, north-up
  and east-right, round trips and equal area, and that all 146 simulant sites stay in their
  country outline; `check:filters` now covers the Reference filter and the Country sort.

## v2.9.18 — 2026-09-25 (staging)

Hotfix: searching in the left panel no longer blanks the page.

**Interface**
- Typing in the left panel's search box crashed the whole page on the first letter. The three
  Lumina simulants added in v2.9.17 have no type or country yet, and the search read those
  fields without allowing them to be empty. An empty field now simply does not match.

**Process**
- `scripts/check_filters.tsx` runs the search and every filter over the real data file, so an
  empty field cannot break them unnoticed.

## v2.9.17 — 2026-09-25 (staging)

Figures of Merit, each traced to the table that prints it; three Lumina highland simulants.

**Data**
- 138 Figures of Merit for 23 simulants: Slabic et al. 2024 (*Lunar Regolith Simulant User's
  Guide, Revision A*, 83 scores on 0–100), Schrader et al. 2010 (39 scores on 0–1) and the
  Hispansion TLH-0 and TLM-0 data sheets (16). Each score is stored with what it measures
  (chemistry, mineralogy, particle size, shape…), the lunar reference it is compared with,
  its scale, and the table cell it was read from. Every score was confirmed by a second
  agent against the page.
- Not stored: two scores for "OB-1(A*)", which may be a variant of OB-1 (owner's decision
  pending); APL 2020's supplier colour ratings, which are not product scores.
- New simulants S159 Lunar90, S160 Lunar250 and S161 Lunar2000 (Lumina Sustainable Materials
  Ltd.), from Zémeny et al. 2024, *Front. Space Technol.*: supplier, highland label, size
  range, min–max dry density, sphericity and mineral table, each cited.
- Lunar2000's reported mean particle size (2.4 mm) is left out: the same paper gives the
  product as 0–2000 µm.

**Interface**
- The simulant panel has a Figures of Merit section: score, scale, property and lunar
  reference, each with its superscript.

**Process**
- The audit reads the quotes behind simulants added from a paper, and a re-run of the
  Figures of Merit step keeps a complete log. Final pass: 0 errors over 1337 values.

## v2.9.16 — 2026-09-24 (staging)

A third general check (reference hygiene); hover explanations and an honest source line in the Moon section.

**Data**
- Five simulants listed the same paper twice under two numbers (CAS-1, CUMT-1, EAC-1A,
  WHU-1, PolyU-1); each is now listed once, with every citation moved to the entry kept.
- 18 references a reader confirmed do not name the product are no longer listed under it
  (kept in the database as the record of that check).
- Readers' working notes removed from two reference titles; MLS-1's Batiste & Sture workshop
  presentation now links to NASA's copy, which is the same file the reader verified.

**Interface**
- The Moon table's columns and the landing-site panel's labels explain themselves on hover.
- The landing-site panel no longer says its soil values come from "Gasteiner et al. 2025": the
  values are compiled from that database, but only about half occur in its paper, and none has
  yet been checked against the mission reports. The panel now says so.

**Process**
- The audit also checks each simulant's reference list: duplicates, references confirmed not
  to name the product, empty entries, impossible years, working notes, and one label spelled
  several ways. Final pass: 0 errors over 1309 values.

## v2.9.15 — 2026-09-24 (staging)

Owner's decisions on the audit applied; a second, wider check fixed dead links and unsourced grain sizes.

**Data**
- At the owner's decision — "an empty value rather than a wrong one" — NAO-1's cohesion (which
  its own paper calls an artefact) and FEFU-1's 0.8 µm particle size (a sintering study's
  powder) are omitted, and NEU-1B is labelled High-Ti Mare, as its primary paper states.
- **30 dead links fixed.** Space Resource Technologies and Off Planet Research moved their
  product pages; the ESRIC knowledge base no longer exists and its catalogue is linked at an
  archived copy; a vendor site that no longer resolves is unlinked; TLS-01's reference cited
  a DOI that was never registered.
- **27 grain sizes no longer shown.** They came from the Gasteiner compilation without a
  source and bypassed the rule that hides an unsourced value.
- MLS-1's lunar analogue cited another simulant's reference row and showed no superscript;
  it now cites its own.

**Process**
- The audit now also checks lunar-analogue labels and institutions against their quotes,
  component names, citations belonging to another simulant, one figure copied onto many
  products, values shown with no source, the Apollo comparison data, map positions, and every
  link on the page. Final pass: 0 errors over 1309 values.
- The apply step refuses a citation of another simulant's reference.

## v2.9.14 — 2026-09-24 (staging)

Every value on the page audited against its own quote; composition tables that mixed analyses repaired.

**Data**
- `scripts/audit_values.py` tests all 1310 displayed values — 546 properties, 547 oxide rows,
  217 mineral rows across 145 simulants — against their own quote (allowing only the unit
  conversions the pipeline makes), physical plausibility, composition totals, the simulant's
  other values, and their citation. The first pass found 24 errors; three passes and the
  source documents resolved all but three judgement calls, listed for the owner.
- **Nine composition tables mixed analyses from different documents.** EAC-1's mineral table
  was two complete analyses stacked (194.5%); NU-LHT-1M, -2M and -4M carried Cr2O3, MnO, P2O5
  and total iron grafted on from another paper; GSC-1 added a review's pyroxene to the primary
  paper's full analysis. Grafts onto a complete analysis are removed and logged. One analysis
  cited piecemeal — EAC-1's XRF table reproduced across later papers, BH-1's paper and its
  corrigendum — is kept whole.
- PolyU-1's "Pyroxene 41.7" is removed: it is the sum of the hedenbergite and augite rows
  listed with it. TLS-01's 1.065 g/cm³ leaves the particle-density column, which no rock that
  light can belong in.
- JSC-1A (108.6%) and NU-LHT-1M (103.5%) reproduce sources that give iron twice; their rows say so.

**Interface**
- A partial oxide analysis — only the components a source states — shows "Partial analysis"
  instead of a total (NEU-1B's single TiO2 row had "totalled" 6.50%).

**Process**
- A row from a second document is never merged into a table another document already fills.
- The audit runs after every apply.

## v2.9.13 — 2026-09-24 (staging)

Hispansion data sheets restored, on their current versions; physical values stored with their unit repaired.

**Data**
- TLH-0 and TLM-0 link to Hispansion's public data sheets again. The link had been empty since
  v2.9.4: the sheets used then were supplied privately, so only a local copy existed and no
  public address. The manufacturer has since published newer sheets, TDS-TLH-0-v1.4 and
  TDS-TLM-0-v2.2, with different chemistry — iron as FeO, and sodium measured where v1.1 gave it
  as below detection. A reader and an independent checker confirmed all 72 values; the page now
  shows those and cites the new sheets. The v1.1 sheets remain as superseded references.
- **Units inside stored values.** Bulk density, cohesion and friction angle are text columns
  that the page reads as numbers in g/cm³, kPa and °. Sixteen values carried their unit,
  so they were hidden — TLH-0 and TLM-0's new bulk density among them — or read in the wrong
  unit: the LX simulants' cohesion, stated in pascals, was shown in kilopascals, a thousand
  times too large. 18 values are converted; 4 that state two values at once are cleared and
  listed for a human.

**Process**
- Values in these three columns are converted into the column's unit wherever they are written,
  and `verify_data.py` fails if one reaches the page as anything but a bare number.
- The page reads cohesion and friction angle with `Number()`, as it already read bulk density,
  so a unit slip hides a value instead of showing it in the wrong unit.
- `scripts/supersede_sheet.py` moves a simulant to a newer version of its data sheet: whole
  composition tables are replaced, never merged, and only values two readers agreed on are taken.

## v2.9.12 — 2026-09-24 (staging)

Wave 3, the last of the provenance run: every simulant has now been read.

**Data**
- The remaining 20 simulants read by a reader and an independent checker. With wave 3,
  **all 145 simulants are named in a reference confirmed to name them** — the first test
  passes in full. References checked against their document: 679 of 708. Verified
  compositions 60 → 64; physical values with a source 505 → 549; every one of the 801
  composition rows cites its document.
- The readers confirmed all twenty are lunar products; none needed the new scope rule.
- GRC-1 and GRC-3's crystalline-silica rows renamed from `crystalline_silica` for display.

**Open**
- Descriptive fields — availability, release year, lunar analogue, institution, type — are
  shown whether or not a document states them. See the owner-decisions file for the counts
  and the options.

## v2.9.11 — 2026-09-24 (staging)

Martian simulants retired at the owner's decision: the database covers lunar simulants only.

**Data**
- Ten records retired: the Open University's OUSR-1, SR-2 (sulfur-rich), OUEB-1, EB-2 (early
  basaltic), OUHR-1 and HR-2, and ESA's engineering soils ES-1 to ES-4. Each was placed under
  Mars by both its reader and an independent checker, on the same two sources: the "Mars"
  sub-header of ISECG Table 9, and the "Mars Regolith Simulants" section of the ESRIC
  knowledge base. They had entered from listings that mix lunar and Martian products.
- 145 simulants remain. The deleted rows are archived under `documentation/retired/` and each
  decision is in `documentation/retired-simulants.md`; TUBS-H, retired on 2026-09-22, is
  confirmed gone from the page.
- `documentation/data-policy.md` records the scope rule. A paper studying lunar and Martian
  simulants together is not evidence that a lunar product is Martian.

## v2.9.10 — 2026-09-24 (staging)

Wave 2 of the provenance run (65 simulants).

**Data**
- 65 simulants read by a reader and an independent checker; written only where both agreed.
  Verified compositions 49 → 60; physical values with a source 392 → 515; simulants named in a
  confirmed reference 84 → 137 of 155, none failing; references checked against their
  document 402 → 614 of 661.
- The integrity check caught eleven values citing references that did not exist: two readers
  named their new documents "S117-N1" rather than "NEW1", and only the latter form was
  translated. The rows were re-linked to the right references.
- CUG-1A's mineralogy, printed as "9% wt", now parses; ranges such as TLS-01A's "60–75" are
  kept out of the table and listed for a human.

**Process**
- A reader's temporary id is translated in whatever form it takes; a value citing an id that
  names no reference is refused.
- Re-applying a run restores a missing source row for a value already stored, so a run can be
  repaired by deleting its bad rows and applying it again.

Decisions for the owner — three records that may not be lunar simulants, four probable
duplicates, and a rule for rock components in the mineral table: `documentation/owner-decisions-2026-09-22.md`, wave 2.

## v2.9.9 — 2026-09-23 (staging)

Wave 1 of the provenance run (45 simulants), and a repair of values that never reached the page.

**Data**
- 45 simulants read by a reader and an independent checker. Written only where both agreed:
  162 source rows for stored values, 242 values the documents state that the database lacked,
  144 documents confirmed to name their product. Verified compositions 31 → 49; sourced
  physical values 227 → 392; simulants named in a confirmed reference 43 → 84.
- **Values stored as text are repaired.** Readers quote values as printed, and a string such
  as "22.4 (vol%)" in a numeric column stayed text — the page dropped the row without a word,
  so LX-M100, DNA-1A and others showed as verified above empty tables, some since v2.9.5. 107
  such values are now numbers, the statement kept verbatim; 22 that are not single numbers
  (ranges, detection limits, "present") are removed and logged.
- Eight mineral rows that were feedstock mixing ratios, and five citations of the project's
  own registry spreadsheet, are removed. DNA-1, Mooncastle and CMU-1 revert from verified:
  their sources give only qualitative mineralogy or a recipe.

**Interface**
- Hovering a composition row's citation shows the value as the document states it — its
  basis (vol% or wt%), uncertainty or "ca." — ahead of the source.

**Process**
- Values are parsed at write time; a non-number is kept out of the table and shown to a human.
- `verify_data.py` now fails if any number reaches the bundle as text, or if a reference
  cites the project's own registry. It found 134 such errors in the previous bundle.
- Reader rules: never cite the registry; cite NotebookLM captures by their original; feedstock
  ratios are not mineral composition.

Decisions for the owner: `documentation/owner-decisions-2026-09-22.md`, wave 1 section.

## v2.9.8 — 2026-09-23 (staging)

Runs sized to fit the weekly budget, and a guard that stops at 80%.

**Process**
- A full pass at 12 documents per group on Opus would need roughly 62 weekly points against
  the 22 left before the 80% stop. Reading is what costs — 120M cache-read tokens in one
  afternoon — so `build_groups.py --max-docs 6` halves the documents offered (225 slots,
  down from 360) and the extraction pass runs on Sonnet. The adversarial check stays on
  Opus: deciding whether a quote really supports a value for this exact product is what the
  audit rests on.
- `scripts/usage_guard.py` reads the weekly figure the `/usage` panel shows and answers in
  two modes — a pre-flight gate that refuses what it cannot confirm, and a monitor that
  reports "cannot tell" rather than killing a run in flight over a stale cache.
- `already_read()` now requires both stages of a run. Only claims two readers agreed on are
  written, so an extraction whose checker died wrote nothing; counting it as read had
  silently dropped AGK-2010 and the four ES products from the queue.

Queue: 44 groups, 130 simulants. No change to what the page displays.

## v2.9.7 — 2026-09-23 (staging)

The library index was hiding documents from the readers.

**Data**
- A product name of four characters or fewer mentioned once in a document was discarded,
  to suppress false positives such as "ALS" or "OB-1" occurring as ordinary abbreviations.
  That silently threw away 75 document-simulant pairs, among them the only sentence in the
  library naming TJ-2 ("In addition, a variant TJ-2 exists in which silicon..."), and left
  six products recorded as named in no document at all.
- Single mentions of short names are now kept separately as weak matches and offered to a
  reader after the confident ones, with the instruction to read the sentence and decide
  whether it is really about that product. Judging a mention is a reader's job, not a
  threshold's.
- Rebuilt with the 28 documents agents fetched since: simulants named in no library
  document fall from 19 to 9 (OPRH2W, OPRH3W, OPRL2W, OPRFLCROSS1, LSS-2, LSS-3, TYII-1,
  TYII-2, SCC-2). Every group now has at least one document to open.

**Process**
- `build_groups.py --skip-read` leaves out simulants a reader-checker pair has already been
  through, and groups are ranked by what they still have to establish rather than how much
  data they already hold.

No change to what the page displays.

## v2.9.6 — 2026-09-23 (staging)

Housekeeping: the version now changes on every push.

**Process**
- `scripts/bump_version.py` writes the sidebar label and opens this section in one step;
  `scripts/push_staging.sh` refuses to push while the sidebar still shows the version that
  is already on origin/staging, or while a version has no section here.
- v2.9.5 covered four separate pushes (the citation superscripts and the render check,
  TUBS-H's retirement, the batch-2 provenance run, and EAC-1A), which is what this is
  meant to prevent; they are described in that section and in the commit history.

## v2.9.5 — 2026-09-22 (staging)

Per-value provenance. Every value on the page now cites the document it was read from,
and a value with no such document is not shown. See
[documentation/data-policy.md](documentation/data-policy.md) and the status report
`documentation/provenance-status-<date>.md`.

**Data**
- New `property_sources` table: one row per (simulant, field) giving the reference,
  the page or table, and the line that states the value. `reference_id` on every
  composition row. References carry `names_simulant`, `mention_quote`, `checked_on`.
- The export nulls any physical property without a source row: 181 values across 54
  simulants are hidden (kept in the database) until a reader locates them in a document.
  The 118 values on the 18 sheet-verified simulants are cited to their data sheets.
- Manufacturer sheets are reference rows (`DS-<id>`), so a sheet-stated value is numbered
  like any other citation.
- Reference repairs: 88 of 89 DOIs resolve (R001, R081 corrected; R112 retitled).
- TUBS-H (S068) retired: not a distinct product; the cited paper describes TUBS-M and
  TUBS-T. Rows archived under `documentation/retired/`; see `documentation/retired-simulants.md`.

**Interface**
- References are numbered per simulant; a `[n]` superscript after every physical value,
  every composition row, and every scalar in the main table, with the location and the
  quoted line on hover. References confirmed to name the simulant are marked; the panel
  header says in how many documents on file the simulant is named.
- `scripts/render_smoke.tsx` (`npm run check:render`) renders the real components with the
  real bundle and fails if any displayed value lacks its mark.

**Verification**
- Agent pipeline: one reader per simulant opens every cited document and quotes what
  supports each value; an independent checker tries to refute each claim; only agreed
  claims are written (`scripts/apply_provenance.py`). Runs are one simulant at a time so a
  session limit loses at most the unit in progress.

## v2.9.4 — 2026-09-22 (staging)

The composition audit. See [documentation/data-policy.md](documentation/data-policy.md)
for the rule and [documentation/composition-audit-2026-09-21.md](documentation/composition-audit-2026-09-21.md)
for the result.

**Data**
- Every simulant carries a `composition_status`: `verified` (18), `withheld_unverified` (52),
  `not_published` (1), `not_extracted` (85). Composition rows exist only for verified simulants.
- 430 oxide values and 223 mineral values removed as unconfirmed. The 18 verified simulants
  were read from manufacturer sheets or the NASA simulant guide and confirmed by a second read.
- LHS-1 no longer carries LHS-1D's physical properties; LMS-1 matches its own fact sheet;
  OPRL2N and OPRH3N use the manufacturer's data sheet rather than the 2021 assessment chemistry;
  OPRH2N and OPRH4N gained compositions; 16 specific gravities that were bulk densities cleared.
- New sheet-stated fields: pH, angle of repose, mean particle size, bulk-density range,
  magnetic susceptibility, product grade, document number, revision date, methods and caveats.
- Composition source links point at the original public documents; the per-table JSON files
  that were serving pre-audit data are removed (the app loads `data.json` only).

**Interface**
- Each simulant shows its provenance: a source line with the document, revision and methods
  for verified ones, and an honest notice for the other three states.
- Composition tables show two decimals, as the sheets do.
- The mineral Groups view is disabled where no grouped breakdown is published.
- Datasheet links appear only on verified simulants.

**Deploy**
- The maintenance step now lives in both `main` and `staging` workflows. Deploys triggered
  from `staging` had been rebuilding the public root without it since 2026-06-25.

**Tooling**
- `scripts/scorecard.py`, `scripts/reconcile.py`, `scripts/datasheet_fill.py`, with 68 unit
  tests; `scripts/verify_data.py` reads the same bundle the app does.

## v2.9.3 — 2026-06-25 (staging)
- Physical properties, composition detail and datasheet column in the Table view; physical
  properties in CSV export.

## v2.9.1 — 2026-05-25
- Globe auto-rotates on load; sidebar closed by default; simulant list expanded by default.

## v2.9.0 — 2026-03-25
- SQLite becomes the source of truth; `data.json` exported from it.
