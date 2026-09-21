# Composition audit, 21 September 2026

Result of applying the [data policy](data-policy.md) to every simulant that carried composition numbers. Machine-readable detail: `composition-audit-log-2026-09-21.json`, `physical-audit-log-2026-09-21.json`, and the findings file `composition-audit-findings-2026-09-21.json` with every quoted source passage.

## Outcome

| Status | Simulants | Meaning |
|---|---:|---|
| verified | 18 | read from an acceptable source and confirmed by an independent second read |
| withheld_unverified | 52 | numbers removed until a second read confirms a source |
| not_published | 1 | the defining source states the product has no controlled composition |
| not_extracted | 85 | never held composition numbers; not yet audited |

Rows removed from the public data: **430 oxide values and 223 mineral values**. Rows added or corrected for the verified set are in the composition log under `replace`.

## Verified simulants

| Simulant | Producer | Source | Oxides | Minerals | Note |
|---|---|---|---:|---:|---|
| TLH-0 (S065) | Hispansion | data sheet | 13 | 10 |  |
| TLM-0 (S066) | Hispansion | data sheet | 13 | 11 |  |
| OPRH2N (S057) | Off Planet Research | data sheet | 10 | 5 |  |
| OPRH3N (S058) | Off Planet Research | data sheet | 10 | 5 |  |
| OPRH4N (S059) | Off Planet Research | data sheet | 10 | 5 |  |
| OPRH4W30 (S100) | Off Planet Research | agency report | 8 | 0 | flagged for a second human check |
| OPRL2N (S060) | Off Planet Research | data sheet | 10 | 5 |  |
| LHS-1 (S036) | Space Resource Technologies | data sheet | 11 | 5 |  |
| LHS-1-25A (S093) | Space Resource Technologies | data sheet | 10 | 6 |  |
| LHS-1D (S091) | Space Resource Technologies | data sheet | 11 | 5 |  |
| LHS-1E (S092) | Space Resource Technologies | data sheet | 10 | 2 |  |
| LHS-2 (S077) | Space Resource Technologies | data sheet | 11 | 5 |  |
| LHS-2E (S078) | Space Resource Technologies | data sheet | 10 | 2 |  |
| LMS-1 (S037) | Space Resource Technologies | data sheet | 11 | 5 |  |
| LMS-1D (S094) | Space Resource Technologies | data sheet | 11 | 5 |  |
| LMS-1E (S095) | Space Resource Technologies | data sheet | 10 | 0 |  |
| LMS-2 (S076) | Space Resource Technologies | data sheet | 11 | 5 |  |
| LSP-2 (S079) | Space Resource Technologies | data sheet | 10 | 2 |  |

The second read for these came from the audit owner reading the same PDFs in session, because the workflow's verification agents hit the session limit. The sheets are on disk under `DIRT/Sources/datasheets/`.

## Why the 52 were withheld

| Reason | Simulants |
|---|---:|
| audit incomplete: extraction done, no second read (session limit) | 31 |
| audit incomplete: extraction not run (session limit) | 21 |

None of these 52 has been judged wrong. Extractions exist for 31 of them, several with a primary paper located and quoted, and they can be confirmed by re-running only the failed verification agents. Until then the policy withholds the numbers rather than show them unconfirmed.

### Withheld, by group

- **Open University**: EB-2 (S144), OUHR-1 (S145), HR-2 (S146), ES-1 (S149), ES-2 (S150), ES-3 (S151)
- **NASA / Orbitec**: JSC-1 (S027), JSC-1A (S028), JSC-1AC (S029), JSC-1AF (S030)
- **(no institution recorded)**: BHLD20 (S005), LBD (S131), TYII-0 (S132)
- **NASA / USGS**: NU-LHT-1M (S049), NU-LHT-2M (S051), NU-LHT-4M (S089)
- **Beihang University**: BH-1 (S004), BH-2 (S121)
- **Chinese Academy of Sciences**: CAS-1 (S007), CLDS-i (S009)
- **Monolite / ESA**: DNA-1 (S014), DNA-1A (S015)
- **European Astronaut Centre**: EAC-1 (S017), EAC-1A (S018)
- **TU Berlin**: LX-M100 (S040), LX-T100 (S041)
- **Tongji University**: TJ-1 (S064), TJ-2 (S122)
- **TU Braunschweig**: TUBS-M (S069), TUBS-T (S070)
- **Colorado School of Mines**: CSM-LHT-1 (S103), CSM-LMT-1 (S105)
- **Outward Technologies**: LMA-1 (S108), LHA-1 (S109)
- **NASA KSC**: BP-1 (S006)
- **China University of Geosciences**: CUG-1A (S012)
- **China Univ. of Mining and Tech**: CUMT-1 (S013)
- **JAXA / Shimizu Corporation**: FJS-1 (S019)
- **Hudson Resources**: GreenSpar (S025)
- **Korea Institute of Civil Engineering and Building Technology**: KLS-1 (S032)
- **Univ. of Minnesota**: MLS-1 (S043)
- **National Astronomical Observatories**: NAO-1 (S045)
- **NASA-MSFC and USGS**: NU-LHT (S047)
- **NASA / Washington Mills**: NUW-LHT-5M (S052)
- **Deltion / EVC / NORCAT**: OB-1 (S053)
- **Deltion**: OB-1A (S054)
- **Turkish Space Agency**: TBG-1 (S063)
- **Space Zab Company**: TLS-01 (S067)
- **NASA / Zybek**: JSC-2A (S081)
- **Goddard Space Center**: GSC-1 (S117)
- **Hong Kong Polytechnic University**: PolyU-1 (S120)
- **Instituto de Geociencias (IGEO, CSIC-UCM)**: LZS-1 (S153)

## Headline corrections

- **LHS-1** carried LHS-1D's bulk density (0.81), median particle size (10.22 µm), cohesion (0.205 kPa) and friction angle (28.62°). The fact sheet gives 1.40 g/cm³, 81.62 µm, 0.311 kPa and 31.49°. Numbers had been transferred from the dust grade to the general-purpose product.
- **LMS-1** disagreed with its December 2025 fact sheet on 11 of 12 oxides and carried two overlapping mineral lists summing to 184.6 %. Replaced with the sheet's values.
- **OPRL2N and OPRH3N** carried oxide rows from the NASA simulant guide's 2021 APL assessment. The manufacturer's own 2024 data sheet disagrees on every value (OPRL2N TiO₂ 1.47 wt%, not 5.5) and now takes precedence. OPRL2N's reference material was also 'High-Ti Mare', which describes the OPRL2NT variant.
- **OPRH2N and OPRH4N** had no composition at all; both are on the same data sheet and are now published.
- **Specific gravity** was cleared on 16 simulants where it equalled the bulk density or fell below 2.0, lighter than any silicate mineral.
- **TLM-0** carried TLH-0's TiO₂ value in its Ti-content field; cleared.
- **Reference material** strings that named a mission the source never names ('Apollo 16' on the SRT highlands simulants, 'Apollo 12/15' on TLM-0) were replaced with the sources' own wording.

## Not published

- **DUST-Y** (Space Resource Technologies): the JHU APL / LSIC Lunar Simulant Assessment (30 Jan 2020) states it is grinding fines produced as a by-product 'with limited control on composition'. The four partial mineral rows it carried (summing to 9.7 %) were removed.

## What is still open

1. Re-run the 35 failed audit agents (23 verifications, 12 extractions) so the 52 withheld simulants get their second read. Cached extractions replay instantly.
2. Decide the reference-list UI: references typed `report`, `review` or `general` are currently shown in neither the composition nor the usage bucket (pre-existing).
3. The 85 `not_extracted` simulants make no claim either way. Each needs a source hunt before it can be called `not_published`.
4. Physical properties outside the verified set were not audited beyond the two specific-gravity rules.
