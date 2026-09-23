# Changelog

Every push carries a new version. `python3 scripts/bump_version.py --body "..."` writes both
the sidebar label and the section below it; `scripts/push_staging.sh` refuses to push while the
sidebar still shows the version already deployed. Data changes are logged per field under
`documentation/`.

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
