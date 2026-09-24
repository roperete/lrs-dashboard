# Value audit, 2026-09-24

Every value the page shows — 1310 across 145 simulants — tested against its own quote,
physical plausibility, composition totals, the simulant's other values, and its citation.
Nothing was changed. Errors go to an agent to re-read; warnings are for a human.

| Severity | Check | Count |
|---|---|---:|
| error | plausibility | 2 |
| error | quote | 1 |
| warn | consistency | 2 |
| warn | stated in words | 3 |
| warn | total | 6 |

## Errors

- **FEFU-1** (S157) `particle_size_mean_um` — plausibility: 0.8 µm is outside the plausible range 1–5000 µm
- **NAO-1** (S045) `cohesion` — plausibility: 95.3 kPa is outside the plausible range 0–30 kPa
- **OPRL2N** (S060) `particle_size_distribution` — quote: 2000, 4.19, 850, 9.09, 425, 15.43, 250, 20.32, 150, 26.81, 75, 37.99, 32, 61.31, 22, 71.04, 13, 80.38, 9, 85.42, 7, 91.36, 3.2, 96.51, 1.3, 98.25 not in its quote

## Warns

- **BH-2** (S121) `oxide table` — total: oxide total 68.6% (expected 90–103%)
- **EAC-1A** (S018) `glass_content_percent` — stated in words: 0.0 rests on wording, not a number: 'EAC-1A is fully crystallized and contains plagioclase, which our XRD characterization indi'
- **GreenSpar** (S025) `mineral table` — total: mineral total 106.0% exceeds 100%
- **IGG-01** (S080) `oxide table` — total: oxide total 22.4% (expected 90–103%)
- **JSC-1** (S027) `glass_content_percent` — stated in words: 50.0 rests on wording, not a number: 'Approximately half of the volume of a typical particle is glass of basaltic composition.'
- **JSC-1A** (S028) `oxide table` — total: oxide total 108.6% (expected 90–103%)
- **NEU-1B** (S124) `cross-field` — consistency: labelled 'Low-Ti Mare' but TiO2 is 6.5%
- **NEU-1B** (S124) `oxide table` — total: oxide total 6.5% (expected 90–103%)
- **NU-LHT-1M** (S049) `oxide table` — total: oxide total 103.5% (expected 90–103%)
- **NU-LHT-2M** (S051) `cohesion` — stated in words: 0.0 rests on wording, not a number: 'The measured cohesion was too low to make any meaningful conclusion and is considered to b'
- **OB-1** (S053) `cross-field` — consistency: glass content 42% but the glass row is 52.6%

## Resolved by checking the source

- **OPRL2N** particle_size_distribution: the reader shortened the quote with "…"; all 30 numbers
  of the stored distribution occur in the OPR General Lunar Simulants data sheet. Correct.
- **OB-1** oxides: the rows quoted "(same row as above)" point to the first quote, which carries
  the whole row; all 12 values occur in the cited document. Correct. (The audit now reads
  back-references against the table's other quotes.)
- **JSC-1A** oxide total 108.6%: the NASA characterisation summary prints its own total of
  108.64%, giving iron both as Fe2O3 (total) and FeO. Faithful; the row is annotated.
- **NU-LHT-1M** oxide total 103.5%: the source gives FeO and total iron (Fe2O3T); annotated.
- **GreenSpar** mineral total 106%: the source's own approximate figures (~5, ~7).
- **IGG-01, BH-2, NEU-1B**: partial analyses; the page now says "Partial analysis" instead of a total.
