# Plan: per-value provenance

Spec: docs/superpowers/specs/2026-09-22-per-value-provenance-design.md
Branch: `staging` (deploys to /lrs-dashboard/staging/). Each task ends green and committed.
Tests run with `python3 -m unittest scripts.tests.<module>`; frontend with `npm run build`.

## Task 1: schema migration

Files: scripts/provenance.py (new), scripts/schema.sql, scripts/tests/test_provenance.py (new)

1. Test: `ensure_provenance_schema(con)` adds `names_simulant`, `mention_quote`,
   `local_path`, `checked_on` to references_, `reference_id` to both composition tables,
   and creates `property_sources`; a second call adds nothing. Run, watch fail.
2. Implement `ensure_provenance_schema`, reusing `datasheet_fill.ensure_columns`.
3. Mirror the columns and table in schema.sql. Tests green. Commit.

## Task 2: repair identifiers

Files: scripts/repair_references.py (new), scripts/tests/test_repair_references.py (new)

1. Test: `doi_from_text("... https://doi.org/10.1061/(ASCE)AS.1943-5525.000042 ...")`
   returns the full DOI; text with no DOI returns None. Run, watch fail.
2. Implement; script repairs the six truncated ASCE DOIs and the MDPI one from
   `reference_text`, replaces the truncated ISRU report URL with the live one and the LPI
   URL with its NTRS equivalent (find both by hand first, HEAD-check), logs each change.
3. Re-run scripts/check_references.py; unresolved should drop to zero or be explained.
   Commit script, log and report.

## Task 3: datasheet reference rows and backfill for the 18

Files: scripts/backfill_sheet_sources.py (new), scripts/tests/test_backfill_sheet_sources.py (new)

1. Test on a fixture DB: for a verified simulant with a datasheet source, the script
   inserts one `datasheet` reference row (title, url, local_path, year), sets
   `reference_id` on all its composition rows, writes a `property_sources` row for each
   scalar field that `datasheet_fill.FILL` or the audit findings attribute to the sheet,
   and leaves a field with no sheet statement without a row. Run, watch fail.
2. Implement. Source of truth for "which fields the sheet states": the findings file's
   `physical` block per simulant plus `datasheet_fill.FILL`.
3. Run against lrs.sqlite; log; check LHS-1 specific_gravity has no source row. Commit.

## Task 4: attach library documents to references

Files: scripts/attach_library.py (new), scripts/tests/test_attach_library.py (new)

1. Test: matching a reference to a library document by DOI in the PDF text, by
   normalised title in the first page, or by Zotero export filename; ambiguous matches
   are not attached. Run, watch fail.
2. Implement using documentation/library-simulant-index-<date>.json and the text cache;
   set `local_path` on matched references. Report how many of 184 have a local copy.
3. Commit script and report.

## Task 5: export and suppression

Files: scripts/export_json.py, scripts/tests/test_export_provenance.py (new)

1. Test: `data.json` contains `property_sources`; a scalar field on a simulant with no
   source row exports as null; composition rows carry `reference_id`; references carry
   `names_simulant`. Run, watch fail.
2. Implement in export_json.py. Keep the DB values; only the export suppresses.
3. verify_data.py: new check that no exported scalar lacks a source row. Commit.

## Task 6: display

Files: src/types.ts, src/hooks/useData.ts, src/context/DataContext.tsx,
src/components/panels/ReferencesSection.tsx, PhysicalPropertiesSection.tsx,
CompositionTable.tsx, MineralChart.tsx, ChemicalChart.tsx, SimulantPanel.tsx,
src/components/ui/RefSup.tsx (new)

1. Types for property_sources and the new reference fields; a `refNumber(simulantId,
   referenceId)` helper deriving the per-simulant number.
2. `RefSup` component: superscript with tooltip showing quote and location.
3. ReferencesSection numbered, badges for type and for names_simulant.
4. PhysicalPropertiesSection renders `RefSup` after each value; CompositionTable takes an
   optional per-row reference number and shows a header note when all rows share one.
5. Existence line in the panel header. Build passes; commit.

## Task 7: agent verification, batched

Files: workflow script (inline), scripts/apply_provenance.py (new),
scripts/tests/test_apply_provenance.py (new)

1. Test the apply step on fixtures: confirmed claim writes property_sources and
   names_simulant; refuted claim withholds and logs; extractor/verifier disagreement
   flags for review; a reference naming no simulant gets names_simulant 0, not deleted.
   Run, watch fail. Implement. Commit.
2. Build groups from the library index and references: simulants sharing documents go
   together; cap ~8 simulants per group; ~35 to 40 groups.
3. Workflow batch 1 (first half of groups): extract then verify, schemas as in the spec,
   local copies first. Save the run id. Apply. Export. Commit.
4. Workflow batch 2. Same. Re-run failed agents with resumeFromRunId as needed.
5. Summary document: documentation/provenance-audit-<date>.md with per-simulant
   outcome, unsourced values withheld, references flagged as naming no simulant.

## Task 8: release

1. CHANGELOG v2.9.5; bump the sidebar label.
2. Update data-policy.md (per-value rule) and data-schema.md (new columns and table).
3. Push staging on the owner's word; verify /staging/ shows superscripts and numbered
   references; root still on maintenance.
