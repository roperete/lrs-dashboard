# Changelog

The version shown in the sidebar is set by hand in `src/components/sidebar/Sidebar.tsx`.
Data changes are logged per field under `documentation/`.

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
