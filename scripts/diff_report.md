# Diff Report: JSON vs Google Spreadsheet

**Date:** 2026-02-24


## Summary

| Source | Simulants | With Mineral Comp | With Chemical Comp |
|--------|-----------|-------------------|-------------------|
| Spreadsheet | 75 | 0 | 15 |
| JSON | 84 | 30 | 20 |

## Simulant Name Differences

### In JSON only (9):
- CLRS-2
- GRC-3
- IGG-01
- JSC-2A
- LHS-2
- LHS-2E
- LMS-2
- LSP-2
- NAO-2

### In Spreadsheet only (0):

## Mineral Composition

### Has mineral data in JSON but NOT in spreadsheet (30):
- BHLD20
- BP-1
- CAS-1
- CLDS-1
- CUG-1A
- CUMT-1
- DNA-1
- DNA-1A
- DUST-Y
- EAC-1
- EAC-1A
- FJS-1
- JSC-1
- JSC-1A
- JSC-1AC
- JSC-1AF
- KLS-1
- LHS-1
- LHS-2
- LHS-2E
- LMS-1
- LMS-2
- LSP-2
- LX-T100
- NAO-1
- NU-LHT
- OB-1
- TLH-0
- TLM-0
- TLS-01

### Has mineral data in spreadsheet but NOT in JSON (0):

## Chemical Composition

### Has chemical data in JSON but NOT in spreadsheet (6):
- LHS-2
- LHS-2E
- LMS-2
- LSP-2
- TLH-0
- TLM-0

### Has chemical data in spreadsheet but NOT in JSON (1):
- LX-M100

## Field Differences (JSON vs Spreadsheet)

Comparing: type, country, institution, availability

Found 55 differences:

- **AGK-2010** `institution`: JSON=`Polish Academy of Sciences` vs Sheet=`Faculty of Drilling, Oil and Gas, AGH University of Science and Technology in Kraków`
- **ALRS-1** `institution`: JSON=`Australian Space Agency` vs Sheet=``
- **BH-1/2** `institution`: JSON=`Chinese Academy of Sciences` vs Sheet=``
- **BHLD20** `type`: JSON=`Lunar Dust Simulant` vs Sheet=``
- **BHLD20** `availability`: JSON=`MayBeAvailable` vs Sheet=``
- **CAS-1** `institution`: JSON=`Institute of
Geochemistry,
Chinese Academy of Sciences` vs Sheet=`Institute of
Geochemistry,
Chinese Academy of Sciences`
- **CSM-CL** `availability`: JSON=`MayBeAvailable` vs Sheet=``
- **CUMT-1** `institution`: JSON=`China University of Mining and Technology` vs Sheet=``
- **DNA-1** `institution`: JSON=`ESA` vs Sheet=`ESA / Technical University of Bari`
- **DNA-1A** `institution`: JSON=`ESA` vs Sheet=`ESA / Technical University of Bari`
- **DUST-Y** `institution`: JSON=`UCF` vs Sheet=``
- **DUST-Y** `availability`: JSON=`No` vs Sheet=``
- **EAC-1** `institution`: JSON=`ESA` vs Sheet=`European Astronaut Centre (EAC`
- **EAC-1A** `institution`: JSON=`ESA` vs Sheet=`European Astronaut Centre (EAC`
- **FJS-1g** `institution`: JSON=`Shimizu Corporation` vs Sheet=``
- **FJS-2** `institution`: JSON=`Shimizu Corporation` vs Sheet=``
- **FJS-3** `institution`: JSON=`Shimizu Corporation` vs Sheet=``
- **GCA-1** `institution`: JSON=`NASA` vs Sheet=``
- **JLU-H** `institution`: JSON=`Jilin University Changchun` vs Sheet=``
- **JSC-1AC** `type`: JSON=`Mare` vs Sheet=``
- **JSC-1AF** `type`: JSON=`Mare` vs Sheet=``
- **KIGAM-L1** `institution`: JSON=`KIGAM` vs Sheet=``
- **KLS-1** `institution`: JSON=`KIGAM` vs Sheet=``
- **Kohyama** `institution`: JSON=`Shimizu Corporation` vs Sheet=``
- **LCATS-1** `institution`: JSON=`Astroport Space Technologies, Inc.` vs Sheet=``
- **LSS-ISAC-1** `institution`: JSON=`ISAC` vs Sheet=``
- **LX-M100** `institution`: JSON=`Technische Universität Berlin` vs Sheet=``
- **LX-T100** `institution`: JSON=`Technische Universität Berlin` vs Sheet=``
- **MKS-1** `institution`: JSON=`NASA` vs Sheet=``
- **MLS-2** `institution`: JSON=`University of Minnesota` vs Sheet=``
- **MLS-2** `availability`: JSON=`no longer produced` vs Sheet=``
- **NAO-1** `institution`: JSON=`National
Astronomical
Observatories,
Chinese Academy of
Sciences` vs Sheet=`National
Astronomical
Observatories,
Chinese Academy of
Sciences`
- **NAO-1** `availability`: JSON=`MayBeAvailable` vs Sheet=`NA`
- **NU-LHT-1D** `availability`: JSON=`Production stopped` vs Sheet=``
- **NU-LHT-1M** `institution`: JSON=`NASA` vs Sheet=``
- **NU-LHT-1M** `availability`: JSON=`Production stopped` vs Sheet=``
- **NU-LHT-2C** `institution`: JSON=`NASA` vs Sheet=``
- **NU-LHT-2C** `availability`: JSON=`Production stopped` vs Sheet=``
- **NU-LHT-2M** `institution`: JSON=`NASA` vs Sheet=``
- **NU-LHT-2M** `availability`: JSON=`out of production and largely out of stock` vs Sheet=``
- **NUW-LHT-5M** `institution`: JSON=`NASA` vs Sheet=``
- **OB-1A** `institution`: JSON=`Deltion Innovations Ltd` vs Sheet=``
- **OPRFLCROSS2** `type`: JSON=`Polar Volatile Ice simulant` vs Sheet=``
- **OPRH4N** `availability`: JSON=`commercially available` vs Sheet=``
- **Oshima** `institution`: JSON=`Shimizu Corporation` vs Sheet=``
- **TBG-1** `institution`: JSON=`Turkish Space Agency` vs Sheet=``
- **TLM-0** `type`: JSON=`Mare` vs Sheet=``
- **TUBS-H** `institution`: JSON=`ESA` vs Sheet=`ESA/Technical University Braunschweig`
- **TUBS-H** `availability`: JSON=`Currently available` vs Sheet=``
- **TUBS-M** `institution`: JSON=`German Aerospace Center (DLR)` vs Sheet=``

... and 5 more

## References

- JSON has 72 reference entries across 69 simulants