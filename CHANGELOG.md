# Changelog

Every push carries a new version. `python3 scripts/bump_version.py --body "..."` writes both
the sidebar label and the section below it; `scripts/push_staging.sh` refuses to push while the
sidebar still shows the version already deployed. Data changes are logged per field under
`documentation/`.

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
