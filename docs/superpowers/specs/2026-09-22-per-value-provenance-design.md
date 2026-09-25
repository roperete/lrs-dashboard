# Per-value provenance for the Lunar Regolith Simulant Database

Status: approved in conversation 2026-09-22 ("You did good"). Supersedes the per-simulant
provenance model of 2026-09-21 by extending it; nothing in that model is removed.

## Goal

Three tests, set by the project owner:

1. Every simulant has at least one reference that names it. A simulant no document names
   has no evidence of existing.
2. Every reference attached to a simulant actually concerns it, and the simulant's
   composition and physical properties match what that reference states.
3. Provenance is recorded per value. When a simulant draws on several documents, each
   value shows a superscript pointing at the reference it came from.

A value with no recorded source is not displayed. This is the policy already in force
(documentation/data-policy.md), applied at the granularity of a single number.

## Data model

All changes are additive columns and one new table. `lrs.sqlite` stays the source of
truth; `scripts/export_json.py` picks up new columns and tables automatically where it
uses `SELECT *`, and is extended for the new table.

### `references_` becomes the registry of documents

| Column | Change |
|---|---|
| `reference_type` | new value `datasheet` for manufacturer data sheets |
| `names_simulant` | INTEGER, 1 when a reader confirmed the document names this exact simulant, 0 when it does not, NULL when unchecked |
| `mention_quote` | TEXT, the sentence that names it |
| `local_path` | TEXT, path of the copy under DIRT/Sources used for verification (never displayed) |
| `checked_on` | TEXT, ISO date of the last verification |

The 17 manufacturer sheets used in the 2026-09-21 audit are inserted as `datasheet`
references so that every sheet-derived value can cite a reference row like any paper.

### Composition rows cite a reference

`chemical_compositions.reference_id` and `mineral_compositions.reference_id`, TEXT,
nullable, pointing at `references_.reference_id`. Rows of the 18 verified simulants get
their sheet's reference id in a one-off backfill.

### Scalar properties cite a reference: `property_sources`

```
property_sources (
  simulant_id   TEXT REFERENCES simulants(simulant_id),
  field         TEXT,   -- column name on simulants, e.g. cohesion, ph, bulk_density
  reference_id  TEXT REFERENCES references_(reference_id),
  location      TEXT,   -- page, table or figure, as the reader found it
  quote         TEXT,   -- the line stating the value
  PRIMARY KEY (simulant_id, field)
)
```

One row per simulant and field. A scalar value on `simulants` with no `property_sources`
row is unsourced.

### Reference numbering

Per simulant, references are numbered in `reference_id` order; the number is derived at
render time, never stored. The same physical document has one `references_` row per
simulant it is attached to, as today, so numbering stays local to the simulant.

## Display

- **References section** becomes a numbered list, one number per reference, with type
  badges (datasheet, composition source, geotechnical, usage, review) and a mark for
  references confirmed to name the simulant.
- **Physical properties** show the value followed by a superscript with the reference
  number; hovering the superscript shows the quoted line and location.
- **Composition tables** show a superscript per row when the simulant's rows cite more
  than one reference; when all rows cite the same reference it is shown once in the
  table header.
- **Unsourced values are not rendered.** The export writes them as `null` so the UI
  needs no special case; the database keeps them, and `documentation/` logs what was
  suppressed and why.
- **Existence line.** The panel header states "named in N documents" from
  `names_simulant`; zero is shown in amber.

## Verification pipeline

### Deterministic (code, run first)

1. Repair truncated DOIs by re-extracting `10\.\d{4,9}/\S+` from `reference_text`, then
   re-resolve at Crossref (`scripts/check_references.py`).
2. Replace the truncated ISRU Gap Assessment URL (14 references) and the dead LPI
   presentation URL with live ones, or record them as unavailable.
3. Build the library index (`scripts/build_library_index.py`): for every PDF under
   DIRT/Sources, which simulant names occur in its text. Attach `local_path` to
   references whose DOI, title or filename matches a library document.
4. Backfill `property_sources` and composition `reference_id` for the 18 sheet-verified
   simulants from the datasheet reference rows. Values on those simulants that the sheet
   does not state (for example LHS-1 specific gravity 2.77) get no row and are withheld.

### Agent verification (the other 138 simulants)

Grouped by shared documents. Each group runs two stages:

**Extract.** Given the simulant records, their references with local paths, and their
stored values, the agent must open each referenced document (local copy first, then DOI
or URL) and return, per reference, whether it names the simulant with a verbatim quote;
per stored value, the reference, location and quoted line that supports it, or
`unsupported`; and any values the documents state that the database lacks, quoted. It
never reports a number it did not read.

**Verify.** An independent agent tries to refute each claim against the same documents:
quotes must be found, numbers must match, the document must be about that variant.
Default verdict when unable to confirm is refuted.

**Apply (code).** Confirmed claims write `property_sources`, `reference_id`,
`names_simulant` and `mention_quote`. Unsupported values are withheld. References that
name no simulant in the group are flagged `names_simulant = 0` for the owner's decision;
they are not deleted by code.

Batches of roughly 40 agents, each batch a resumable workflow run, because the
2026-09-18 run lost 35 agents to the session limit.

## Error handling

- A document that cannot be opened leaves its references NULL in `names_simulant` and
  every value depending on it withheld with reason `document unavailable`.
- A value the extractor and verifier disagree on is withheld and flagged for a human.
- Sum rules from the 2026-09-21 policy still apply to composition lists.
- The apply step is idempotent and logs every write with a reason.

## Testing

- Unit tests for the schema migration (idempotent), the DOI repair regex, the library
  name matcher (short names, separator variants), the backfill for sheet-verified
  simulants, and the apply step (confirmed writes a row, refuted withholds, disagreement
  flags).
- Export test: no scalar value appears in `data.json` without a `property_sources` row.
- Build and existing 68 tests stay green.

## Out of scope

Deleting simulants no document names; re-deriving NASA mineral groups; auditing map
coordinates, availability and release dates beyond what the referenced documents state.
