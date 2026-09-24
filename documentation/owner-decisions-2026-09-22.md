# Decisions for the owner, 2026-09-22

Findings from the provenance runs that a script must not act on alone. Each line names
the evidence (findings files under `documentation/provenance-findings-*.json`, notes
field). Nothing below changes the database until you say so.

## Records that may not be real products

| Id | Name | Finding | Options |
|---|---|---|---|
| S047 | NU-LHT | Every document uses "NU-LHT" only as a series label ("NU-LHT series", "NU-LHT and its derivatives"); the members 1M, 1D, 2M, 2C, 2E are separate records already (2EG, 3M, 4M, NUW-LHT-5M too). Its stored "40 % glass" most plausibly comes from a category sentence about the series. | Retire as TUBS-H was, or keep as an explicit family record with no values of its own. |
| S085 | JSC-2 | The bare name appears twice: once citing a JSC-2A study, once in a 2005 abstract title "New lunar root simulants: JSC-2 (JSC-1 clone) and JSC-3" — the working name of what shipped as JSC-1A/2A. No document gives JSC-2 a property. | Retire, alias of S081 JSC-2A (and S028 JSC-1A). |
| S010 | CLRS-1 | Patzwald 2025, simulantdb, the Global Registry and Ruan 2024 all treat CLRS-1 as another name for CAS-1; its listed reference (R010) is the CAS-1 paper. But a dedicated 2014 publication on CLRS-1 particle size (ball-mill processing) exists on ResearchGate, and a Chinese patent calls CLRS-1 a "national standard sample". | Keep as a product with the alias noted, and acquire the 2014 paper; or merge into S007. |
| S029 | JSC-1AC | The only reference (R027) could not be located and appears not to exist as cited. JSC-1AC itself is real: the coarse (1–5 mm) fraction of the JSC-1A suite, but no document gives it a chemistry or geotechnical value of its own; the Orbitec MSDS values (SG 2.9, 45°, 1.0 kPa) are stated for the three-product family. | Replace R027 with the Orbitec MSDS; decide whether family-level values may be shown on a member. |

## Wrong or missing references

| Id | Name | Finding | Action |
|---|---|---|---|
| S083 | NAO-2 | R119 (Li et al. 2022) is the CUMT-1 paper and names NAO-2 once in a list. The primary paper is Li et al. 2011, "Two Lunar Mare Soil Simulants", Acta Geol. Sin. 85(5) 1016–1021 — not in the library. | Acquire Li 2011; retype R119 as `usage`. |
| S126 | HUST-1 | R152 (Chen 2025 review) supports none of the four stored scalars. Defining papers: Han et al. 2022 (CBM) and Han et al. 2024 (IJMST 34(9), doi 10.1016/j.ijmst.2024.06.004, open access) — captured as metadata only. | Open Han 2024 with ScienceDirect access and add to the library. |
| S075 | WHU-1 | R072 and R097 are the same paper (duplicate DOI), a loading-condition study readable only to the first page; the three geotechnical numbers (1.65, 9.9, 40.57) trace to nothing. Candidate development paper: Teng et al., Icarus 2025 (PII S0019103525003124). | Acquire; merge R072/R097. |
| S009 | CLDS-i | Only reference is a plant-growth review that lists it; composition read from simulantdb, which transcribes Tang et al. 2017. | Acquire Tang 2017. |
| S028 | JSC-1A | R026 (Taylor et al. 2005, MetSoc abstract 5180) is about JSC-1 and never uses the name JSC-1A; now marked as not naming S028. The same abstract is on JSC-1 as RN-S027-5. | Delete R026 from S028 (the design keeps it marked 0 until you say so). |
| — | duplicates | Same document under two ids for one simulant: R008 = R096 (S007), R013 = R108 (S013), R072 = R097 (S075), R078 = R103 (S120), R018 = R098 (S018); R067 (S050) and R122 (S086) are the same NASA guide on different simulants (fine). | Merge each pair; keep the lower id. |
| — | R080 | MDPI DOI still does not resolve (from the 2026-09-22 reference check). | Find the article's current DOI. |

## Stored values that are not what the paper says

The export already hides these (no source row). They stay in the database for your decision.

| Id | Name | Stored | What the document states | Suggest |
|---|---|---|---|---|
| S013 | CUMT-1 | cohesion 15.79 kPa, friction 51.26° | Not in the paper; they are means of two of three Table 4 rows. The paper's own overall values: 16.93 kPa, 51.40° (peak state, Dr = 80 %, 106–197 kPa). | Replace with the paper's values and cite Table 4. |
| S120 | PolyU-1 | cohesion 6.75 kPa, friction 38.0° | Unstated midpoints of published ranges 0–13.5 kPa and 35.7–40.3° (direct shear, Dr = 75 %, ρ = 1.63 g/cm³). | Store the ranges as text, or the midpoints with "midpoint of" in the quote. |
| S045 | NAO-1 | cohesion 95.3 kPa (now sourced) | The paper states it but calls it an artefact of the dense 1.93 g/cm³ specimen and "assume[s] that the cohesion of NAO-1 is about 0". | Keep with the caveat, or clear. |
| S051 | NU-LHT-2M | bulk density 1.715, friction 39.54°, SG 2.9319 | In none of 13 documents. He 2010: SG 2.749, dry density 1.367–2.057 g/cm³, peak friction 36.0–40.7° (density-dependent), cohesion ≈ 0. | Replace with He 2010 values and cite. |
| S027 | JSC-1 | bulk density 1.065 | Not stated anywhere; literature 1.33–1.91 (He 2010 p.101), NASA ARES page 1.5–1.9. | Clear. |
| S081 | JSC-2A | PSD "2.3–102 µm"; availability "Production stopped" | The range splices two sieved study fractions of Zocca 2020, not the product; every source presents JSC-2A as the current JSC-1A replacement. | Clear the PSD; set availability to available. |
| S030 | JSC-1AF | median grain size | 23.72 µm (NASA 2006 summary, laser diffraction), 16 µm (He 2010, hydrometer), "average 27 µm" (Slabic 2024, source not given). | Pick the NASA summary and record the method. |
| S027 | JSC-1 | institution "NASA / Orbitec" | LEAG 2010 Appendix 4: JSC-1 = Johnson Space Center; JSC-1A/1AF = MSFC / Orbitec. | Set institution to NASA Johnson Space Center. |
| S026 | JLU-H | availability "Unavailable" | Patzwald 2025: "currently available". | Set available. |
| S084 | CLRS-2 | type "Highlands" (from R120) | Contradicted by every other source and by the basalt feedstock. | Clear the type until Song et al. 2020 (Icarus 347, 113810) is acquired. |
| S018 | EAC-1A | bulk density 1.95 | 1.95 g/cm³ is the specimen density of the cohesion test. The paper's bulk density (optimal packing) for EAC-1A is 1.45 g/cm³ (p.3); Ramos Somolinos 2024 measured 1.72 at atmospheric pressure. | Store 1.45 and cite p.3 "Density". |
| S018 | EAC-1A | PSD "d50=181" | Stated nowhere. Engelschiøn 2020: median 6.47 ϕ (~11 µm, laser diffraction); Ginés-Palomares 2023 as received: D(v,0.5) = 210 µm. Batch or method difference. | Clear; keep D50 = 11 µm as sourced, note the 210 µm as-received figure. |
| S018 | EAC-1A | composition (now shown, flagged) | The oxides are labelled "EAC-1" in the source, which the paper defines as the host material regardless of grain size. Kjøniksen et al. 2021 (ESA ACT report, in the library) gives a different 8-oxide EAC-1A composition, method unstated. | Accept the Engelschiøn chemistry as EAC-1A's, or hold until a batch analysis of the product itself is found. |

## Still open from earlier

- 19 simulants are named in no document in the library (`documentation/library-simulant-index-2026-09-22.json`): they need a document before their existence can be shown.
- TUBS-H (S068): retired 2026-09-22 at your decision; see `retired-simulants.md`.

## Wave 1, 2026-09-23 (45 simulants)

Evidence in `documentation/provenance-findings-lean-wave1.json` (notes fields) and
`documentation/value-repair-log-2026-09-23.json`.

### References attached to the wrong product

| Id | Name | Finding | Action |
|---|---|---|---|
| S004 | BH-1 | R004's title and abstract are about BH-2, not BH-1. | Move R004 to S121 (BH-2), where it is the primary source. |
| S015 | DNA-1A | R100 is about DNA-1 and is already listed there as R014. | Remove R100 from DNA-1A. |
| S111 | MLS-1A | Its only reference, R140, is the CUMT-1 paper and never discusses MLS-1A. | Replace with Hill et al. 2007. |
| S054 | OB-1A | One reference is about OB-1 and supports several OB-1 fields. | Move it to S053 (OB-1). |
| S059, S099 | OPRH4N, OPRH3W | One reference each is misattributed. | See the findings notes; remove. |

### Stored values the documents contradict

| Id | Name | Stored | What the documents state |
|---|---|---|---|
| S137 | TUBS-I | lunar_sample_reference "Ilmenite-rich" | Its defining reference (R161) describes a straight 50:50 mix of TUBS-M and TUBS-T, with no ilmenite enrichment. |
| S064 | TJ-1 | bulk density 1.55, cohesion 1.0, SG 2.9 | Literature: 1.08–1.78 g/cm³, 0.86 kPa, Gs 2.72. Right ballpark, wrong number — a pattern worth a wider check of pre-audit values. |
| S054 | OB-1A | specific gravity | Two sourced values disagree: 3.03 (APL 2022) and 3.22 (SDL/JSC-ARES 2023). Pick one and record the method. |
| S004, S020 | BH-1, FJS-1g | availability | Contradicted by the primary paper (BH-1) and by the one document that addresses it (FJS-1g). |
| S107 | Mooncastle | lunar_sample_reference "Mare", availability "Available" | Neither traceable; CSM's own site says it is still being worked on. |
| S149 | ES-1 | institution, lunar vs Mars category | Both look misattributed. |

### Contradictory sources

- **DNA-1 (S014)**: two full oxide tables disagree — Kjøniksen et al. 2021 and Zhou et al. 2021
  (SiO2 47.79, Al2O3 19.16) against Sandeep et al. 2019 quoting Cesaretti et al. 2014 (SiO2
  41.90, Al2O3 16.02). Its mineralogy is published only as presence ticks, so the composition
  reverted from verified.
- **BH-2 (S121)**: R147 gives BH-2 the same SiO2/Al2O3/CaO as BH-1's own paper (43.3/16.5/8.8).
  Plausible — same scoria source — but confirm against R004 once it is opened.
- **MLS-1 (S043)**: Schrader et al. 2010's modal mineralogy (36.6% glass) is for the
  glass-processed derivative, contradicting the well-corroborated "no glass" base product.
  The reader rightly did not attach it to MLS-1.

### Removed by the value repair (kept in the log)

- **Not a single number**: JSC-1 D50 "98 (UTD) / 117 (NASA) µm" — two measurements, pick one;
  NAO-1 D50 "41–61 µm" — a range; OPRH4W30 FoM, stated with a table of sub-scores; detection
  limits (NU-LHT-1M P2O5 <0.02, LX-T100 biotite <1 wt%); minerals marked only present or trace
  for DNA-1, BH-1, BH-2, CSM-CL, Mooncastle and EAC-1A.
- **Feedstock ratios recorded as minerals**: OPRH4W30 (anorthosite 90 / basalt 10 /
  agglutinates 30), CSM-LHT-1 (70% GreenSpar anorthosite, 30% Merriam Crater basalt),
  CSM-LMT-1 (100% basalt), CMU-1 (coal 63 / limestone 37). **CMU-1's recipe raises whether it
  is a lunar regolith simulant at all.**
- **Five citations of the Global Registry of Lunar Regolith Simulants** — this project's own
  spreadsheet — for CAS-1, CLDS-i, CLRS-1, CLRS-2 and IGG-01. They supported no values, but
  counted towards "named in a reference". Each of those simulants still has other confirmed
  references.

## Wave 2, 2026-09-24 (65 simulants)

Evidence in `documentation/provenance-findings-lean-wave2.json` (notes fields).

### Possibly not lunar simulants

| Id | Name | Finding | Options |
|---|---|---|---|
| S145 | OUHR-1 | Both documents naming it list it under **Mars**. None calls it lunar. | **Retired 2026-09-24** — Martian simulants are out of scope. |
| S146 | HR-2 | No document in the library calls it a lunar simulant. | **Retired 2026-09-24**, with OUSR-1, SR-2, OUEB-1, EB-2 and ES-1 to ES-4. |
| S119 | CMU-1 | Its "mineralogy" is coal 63% and limestone 37% (wave 1). | Same. |

### Probable duplicates

| Ids | Names | Finding |
|---|---|---|
| S023, S117 | GCA-1, GSC-1 | Both rest on Taylor et al. 2008, "Jurassic Diabase from Leesburg, VA" (NLSC abstract 2054), which never uses the name GCA-1. Likely one product entered twice. |
| S012, S125 | CUG-1A, CUG-1 | "CUG-1" appears only in secondary citations of the CUG-1A paper with the trailing "A" dropped. |
| S018, S017 | EAC-1A, EAC-1 | Engelschiøn 2020 labels host-rock chemistry "EAC-1" and processed-product physical properties "EAC-1A" by its own convention; values sit on the wrong record. |
| S096 | LHD-1D | Only the JHU-APL 2024 assessment uses the name; Space Resource Technologies' own catalogue does not. Possibly a misreading of LHS-1D. |

### References that do not name their product

- **IRSM-1** (S130): R156 is the CUMT-1 paper.
- **Maryland-Sanders** (S118): R145, Off Planet Research's product listing, does not mention it; it is a 1995 academic simulant.
- **OPRL2NT** (S061): R071, Slabic et al. 2024, does not contain the name anywhere.
- **SCC-1, SCC-2** (S139, S140): the only trace in the library is one table cell ("SCC-1/2", UK) in a
  solidification review; the institution "Open University" is stated nowhere.

### Stored values the documents contradict

| Id | Name | Stored | What the documents state |
|---|---|---|---|
| S141, S142 | OUSR-1, SR-2 | lunar_sample_reference "General"; availability "Unavailable" | Both sources: "Sulfur rich"; ESRIC: "Currently available". |
| S005 | BHLD20 | availability "Unavailable" | Its own reference R005: "May Be Available". |
| S132 | TYII-0 | D50 48.4 µm | Its paper's Table 4: 116 µm. |
| S060 | OPRL2N | release_date 2010 | Unsupported; the producer was founded in 2015. |
| S153 | LZS-1 | density and porosity | Measured on intact basalt cores, not the loose simulant. |
| S036 | LHS-1 | feedstock | The 2022 assessment tested batches of Stillwater anorthite + SF volcanic-field basalt; the current fact sheet says GreenSpar anorthosite + Merriam Crater basalt. A batch change worth noting on the page. |

### One rule needed: rock components in the mineral table

Exolith's fact sheets publish LHS, LMS and LSP "mineralogy" as rock components — LHS-1:
anorthosite 74.4, glass-rich basalt 24.7 — and those rows were verified against the sheets on
2026-09-21 and are shown. The wave-1 repair removed CSM-LHT-1's equivalent (70% anorthosite,
30% basalt) and CSM-LMT-1's (100% basalt) as feedstock ratios. The two treatments are
inconsistent. Either rock-component breakdowns belong in the mineral table — then CSM-LHT-1 and
CSM-LMT-1 can be restored from `documentation/value-repair-log-2026-09-23.json` — or they do
not, and the Exolith rows move out too. OPRH4W30's 90/10/+30 and CMU-1's coal/limestone are
recipes under either rule.

## Wave 3, 2026-09-24 (20 simulants)

With wave 3 every simulant in the database has been read by a reader and an independent
checker, and all 145 are named in a confirmed reference. Evidence in
`documentation/provenance-findings-lean-wave3.json`.

| Id | Name | Finding | Suggest |
|---|---|---|---|
| S124 | NEU-1B | Stored lunar_sample_reference "Low-Ti Mare"; every document calls it the **high-Ti** variant (TiO2 6.5%, against NEU-1A's 2.87%). | Set "High-Ti Mare". |
| S046 | NEU-1 | The series name; Li et al. 2019 introduced two products, NEU-1a and NEU-1b, which are S123 and S124. No document gives values for plain NEU-1. | Keep as a family record with no values, or retire as a series name (same question as NU-LHT). |
| S102, S056 | OPRFLCROSS1, OPRFLCROSS2 | OPRFLCROSS1 (LPSC 2019) looks like the predecessor name of OPRFLCROSS2, which appears from 2020 and is still sold. | Probable duplicate; confirm with Off Planet Research. |
| S055 | OPR Agglutinate | Availability contradicted: ESRIC and ISECG both list it as currently available. | Correct. |
| S039 | LuNOR | SolSys Mining's 2025 ESA workshop abstract describes its availability differently from the stored value. | Check the abstract (NEW1 in the findings) and correct. |
| S065, S066 | TLH-0, TLM-0 | The data sheets' §1 composition (anorthosite, basalt, altered peridotite) is the feedstock blend; the readers rightly did not record it as mineralogy. | Relevant to the rock-component rule above. |

## Across all waves: descriptive fields are shown without a source

The per-value rule hides a physical property that has no source row. It does not cover the
descriptive fields, which the page shows regardless. On 2026-09-24:

| Field | Shown | With a source row | Without |
|---|---:|---:|---:|
| availability | 145 | 47 | 98 |
| release_date | 109 | 40 | 69 |
| lunar_sample_reference | 142 | 80 | 62 |
| institution | 129 | 106 | 23 |
| type (highland / mare / general) | 145 | 0 | 145 |

The readers found many of these stated nowhere, and several contradicted — availability most
often (BHLD20, OUSR-1, OPR Agglutinate, JLU-H, BH-1, FJS-1g…). `type` was never in the readers'
brief at all. Options: hide the unsourced ones as physical properties are hidden (availability
would disappear for two thirds of the simulants, and `type` drives the map colours and filters);
mark them visibly as unverified; or accept them as editorial fields. Your call — this decides
whether the third test covers the whole page or only its numbers.
