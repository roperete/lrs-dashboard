# Data policy

Why the site went into maintenance, what rule now governs every published number,
and how to run the audit yourself.

## What went wrong

Between February and March 2026 the database grew from 74 to 156 simulants, largely
through automated extraction. Two failure modes reached users.

**Invented references.** Commit `8e94185` removed 79 fabricated references in one
go. The replacement pass (`502e356`) backfilled citations for all 156 simulants from
a source index, which restored coverage but not provenance: a citation now existed
for every simulant, whether or not it was the source of that simulant's numbers.

**Citations that point at the wrong document.** TJ-2 cited the LX simulant papers, a
different simulant family entirely. Six Open University simulants cited an ISRU gap
assessment, a strategy document with no composition tables. LHS-2 and LSP-2 cited an
unrelated physicochemical-properties paper rather than their own manufacturer fact
sheets. The numbers may or may not be right; nothing in the record said where they
came from.

The result was a database that looked fully cited and was not. Users reported
inaccuracies and the site was taken down.

## The rule

A composition is published only when both hold:

1. It was read from an **acceptable source**, and
2. an **independent second read** of that same source confirmed it.

Acceptable sources, best first:

| Kind | What it is |
|---|---|
| `manufacturer_datasheet` | the producer's spec or technical data sheet for that exact product |
| `primary_paper` | the paper that introduced and characterised the simulant |
| `agency_report` | an agency report tabulating measured data |

A review paper that reprints someone else's table is **not** an acceptable source.
Reviews are where most of the unsourced numbers came from. The same table quoted at
third hand acquires no authority, and the reader cannot tell which measurement it
came from.

Numbers are never transferred between product variants. A dust grade, an engineering
grade, a sieve fraction and an agglutinate-bearing version are different products,
even when a producer derives one from another.

### Sum rules

A composition list must sum like a real analysis, or it is incomplete and is dropped:

| List | Must sum to |
|---|---|
| Mineral modal analysis | 90–101 % |
| Bulk oxide analysis | 95–102 % |

Aggregate rows (`Sum`, `Total`, `LOI`) are excluded from the oxide sum, as are
duplicated totals such as `FeOT` when `FeO` is also present.

The two lists are judged separately. A mineral list that double-counts no longer
discards a sound oxide list alongside it.

## The four states

Every simulant carries a `composition_status`. The distinction between the last two
matters and is the reason there are four states rather than two.

| Status | Shown to the reader as | Meaning |
|---|---|---|
| `verified` | the data, plus a source line | traced to an acceptable source and re-checked |
| `withheld_unverified` | "Composition withheld" | values existed but could not be traced; removed |
| `not_published` | "Composition not published" | the producer and defining paper disclose none |
| `not_extracted` | "Composition not yet verified" | not yet audited; makes no claim either way |

`not_published` is a claim about the world and is only ever set when an audit reached
the defining source and found no composition in it. Applying it to simulants nobody
has checked would be a new false statement of exactly the kind that took the site
down.

The pre-existing `simulant_extra.publicly_available_composition` flag cannot carry
this distinction: it is `1` for precisely the simulants that have data in our
database and `0` for every other, so it records what we hold, not what was published.

## Physical properties

The same rule applies, with two defects cleared everywhere because they are provable
without consulting any source:

- `specific_gravity` equal to `bulk_density` — the bulk density was copied into the
  wrong column.
- `specific_gravity` below 2.0 — lighter than any silicate mineral, so it is not a
  specific gravity.

Other physical values are corrected only where an audited source states them.

## Running the audit

```bash
python3 scripts/scorecard.py                          # grade every simulant, writes documentation/data-quality-scorecard.{md,csv}
python3 scripts/reconcile.py --findings audit.json    # dry run: print the plan
python3 scripts/reconcile.py --findings audit.json --write
python3 scripts/export_json.py                        # regenerate public/data/data.json
python3 scripts/verify_data.py                        # referential integrity
python3 -m unittest scripts.tests.test_scorecard scripts.tests.test_reconcile scripts.tests.test_physical
```

`lrs.sqlite` is the source of truth. Edit it, then export. Never hand-edit
`public/data/data.json`.

Every change reconcile makes is written to `documentation/composition-audit-log.json`
with the reason, so any removal can be explained to a user who asks where a number
went.

## If you are adding data

Attach the source before the number. A row whose provenance you cannot state in one
line does not belong in the database, however plausible it looks. When in doubt,
leave `not_extracted` — an honest gap costs a user nothing, and a wrong number costs
them an experiment.
