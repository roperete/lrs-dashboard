# Data-quality scorecard

Generated from `lrs.sqlite` — 156 simulants.

## Summary

| Priority | Meaning | Simulants |
|---|---|---|
| P1 | composition numbers with only review/no sources (likely unsourced) | 27 |
| P2 | integrity problem (sums out of range or null values) | 11 |
| P3 | composition numbers with a spec sheet or primary paper — verify against it | 31 |
| P4 | no composition numbers — nothing to verify | 87 |

| Source tier | Simulants |
|---|---|
| A — spec sheet / datasheet | 7 |
| B — primary paper | 38 |
| C — other paper | 41 |
| D — review-type only | 70 |
| E — none | 0 |

## Per simulant

| Pri | ID | Name | Institution | Tier | Oxides (sum) | Minerals (sum) | Refs (comp) | Issues |
|---|---|---|---|---|---|---|---|---|
| P1 | S005 | BHLD20 |  | D | — | 2 (45) | 1 (0) | mineral sum 45.0% outside 90-101%; composition numbers without a primary source |
| P1 | S009 | CLDS-i | Chinese Academy of Sciences | D | — | 3 (100) | 1 (0) | composition numbers without a primary source |
| P1 | S016 | DUST-Y | Space Resource Technologies | D | — | 4 (9.7) | 1 (0) | mineral sum 9.7% outside 90-101%; composition numbers without a primary source |
| P1 | S025 | GreenSpar | Hudson Resources | D | 8 (99.6) | — | 1 (0) | composition numbers without a primary source |
| P1 | S029 | JSC-1AC | NASA / Orbitec | D | — | 13 (100.2) | 1 (0) | composition numbers without a primary source |
| P1 | S030 | JSC-1AF | NASA / Orbitec | D | 6 (98.07) | 13 (100.2) | 1 (0) | composition numbers without a primary source |
| P1 | S047 | NU-LHT | NASA-MSFC and USGS | D | — | 2 (20.4) | 1 (0) | mineral sum 20.4% outside 90-101%; composition numbers without a primary source |
| P1 | S052 | NUW-LHT-5M | NASA / Washington Mills | D | — | 2 (100) | 1 (0) | composition numbers without a primary source |
| P1 | S058 | OPRH3N | Off Planet Research | D | 8 (100) | — | 2 (1) | composition numbers without a primary source |
| P1 | S060 | OPRL2N | Off Planet Research | D | 8 (100) | — | 2 (1) | composition numbers without a primary source |
| P1 | S076 | LMS-2 | Space Resource Technologies | D | 10 (98.17) | 5 (100) | 1 (0) | composition numbers without a primary source |
| P1 | S089 | NU-LHT-4M | NASA / USGS | D | 8 (98.6) | — | 1 (1) | composition numbers without a primary source |
| P1 | S100 | OPRH4W30 | Off Planet Research | D | 8 (99) | — | 1 (0) | composition numbers without a primary source |
| P1 | S103 | CSM-LHT-1 | Colorado School of Mines | D | 8 (99.9) | 1 (100) | 1 (1) | composition numbers without a primary source |
| P1 | S105 | CSM-LMT-1 | Colorado School of Mines | D | 8 (100.1) | — | 1 (1) | composition numbers without a primary source |
| P1 | S108 | LMA-1 | Outward Technologies | D | — | 2 (100) | 1 (0) | composition numbers without a primary source |
| P1 | S109 | LHA-1 | Outward Technologies | D | — | 1 (100) | 1 (0) | composition numbers without a primary source |
| P1 | S117 | GSC-1 | Goddard Space Center | D | 10 (99.8) | — | 1 (0) | composition numbers without a primary source |
| P1 | S121 | BH-2 | Beihang University | D | 7 (97.89) | — | 1 (0) | composition numbers without a primary source |
| P1 | S131 | LBD |  | D | 13 (99.68) | 10 (97.6) | 1 (0) | 1 composition rows with null value; composition numbers without a primary source |
| P1 | S132 | TYII-0 |  | D | 13 (98.61) | 11 (100) | 1 (0) | 1 composition rows with null value; composition numbers without a primary source |
| P1 | S144 | EB-2 | Open University | D | 10 (98.74) | — | 1 (0) | composition numbers without a primary source |
| P1 | S145 | OUHR-1 | Open University | D | 10 (99.98) | — | 1 (0) | composition numbers without a primary source |
| P1 | S146 | HR-2 | Open University | D | 10 (98.74) | — | 1 (0) | composition numbers without a primary source |
| P1 | S149 | ES-1 | Open University | D | 10 (98.77) | — | 1 (0) | composition numbers without a primary source |
| P1 | S150 | ES-2 | Open University | D | 10 (98.17) | — | 1 (0) | composition numbers without a primary source |
| P1 | S151 | ES-3 | Open University | D | 10 (99.99) | — | 1 (0) | composition numbers without a primary source |
| P2 | S006 | BP-1 | NASA KSC | B | 10 (93.13) | 7 (100) | 2 (2) | oxide sum 93.13% outside 95-102% |
| P2 | S017 | EAC-1 | European Astronaut Centre | C | 11 (108.56) | 3 (100) | 1 (0) | oxide sum 108.56% outside 95-102% |
| P2 | S018 | EAC-1A | European Astronaut Centre | B | 8 (95.76) | 7 (100) | 2 (1) | 4 composition rows with null value |
| P2 | S027 | JSC-1 | NASA / Orbitec | B | 3 (70.1) | 13 (100.2) | 2 (1) | oxide sum 70.1% outside 95-102% |
| P2 | S037 | LMS-1 | Space Resource Technologies | B | 11 (100.34) | 9 (184.6) | 2 (1) | mineral sum 184.6% outside 90-101% |
| P2 | S049 | NU-LHT-1M | NASA / USGS | C | 9 (98.76) | 14 (111) | 1 (0) | mineral sum 111.0% outside 90-101%; 9 composition rows with null value |
| P2 | S051 | NU-LHT-2M | NASA / USGS | C | 9 (97.39) | 16 (105) | 1 (0) | mineral sum 105.0% outside 90-101%; 10 composition rows with null value |
| P2 | S053 | OB-1 | Deltion / EVC / NORCAT | B | 8 (98.5) | 10 (102.04) | 2 (1) | mineral sum 102.04% outside 90-101% |
| P2 | S067 | TLS-01 | Space Zab Company | B | 7 (106.28) | 4 (93.4) | 2 (2) | oxide sum 106.28% outside 95-102% |
| P2 | S120 | PolyU-1 | Hong Kong Polytechnic University | B | 10 (99.22) | 8 (99.9) | 2 (1) | 1 composition rows with null value |
| P2 | S122 | TJ-2 | Tongji University | B | 11 (106.14) | — | 1 (1) | oxide sum 106.14% outside 95-102% |
| P3 | S004 | BH-1 | Beihang University | B | 10 (99.3) | — | 2 (1) |  |
| P3 | S007 | CAS-1 | Chinese Academy of Sciences | B | 10 (98.81) | 6 (100) | 3 (1) |  |
| P3 | S012 | CUG-1A | China University of Geosciences | B | — | 4 (100) | 2 (1) |  |
| P3 | S013 | CUMT-1 | China Univ. of Mining and Tech | B | 10 (98.76) | 8 (100) | 2 (1) |  |
| P3 | S014 | DNA-1 | Monolite / ESA | C | 10 (98.81) | 1 (100) | 1 (0) |  |
| P3 | S015 | DNA-1A | Monolite / ESA | B | 10 (100.02) | 1 (100) | 3 (1) |  |
| P3 | S019 | FJS-1 | JAXA / Shimizu Corporation | B | 10 (97.95) | 7 (100) | 2 (1) |  |
| P3 | S028 | JSC-1A | NASA / Orbitec | B | 11 (98.9) | 13 (100.2) | 2 (1) |  |
| P3 | S032 | KLS-1 | Korea Institute of Civil Engineering and Building Technology | B | 11 (99.84) | 10 (93.33) | 2 (2) |  |
| P3 | S036 | LHS-1 | Space Resource Technologies | B | 10 (98.74) | 5 (100) | 2 (1) |  |
| P3 | S040 | LX-M100 | TU Berlin | C | 11 (98.62) | 7 (96) | 2 (0) |  |
| P3 | S041 | LX-T100 | TU Berlin | C | 11 (99.76) | 5 (100) | 2 (0) |  |
| P3 | S043 | MLS-1 | Univ. of Minnesota | C | 8 (99.9) | 3 (93) | 2 (1) |  |
| P3 | S045 | NAO-1 | National Astronomical Observatories | B | 11 (98.63) | 3 (100) | 2 (1) |  |
| P3 | S054 | OB-1A | Deltion | B | 8 (97.9) | 3 (97.3) | 2 (1) |  |
| P3 | S063 | TBG-1 | Turkish Space Agency | C | 12 (99.71) | — | 1 (0) |  |
| P3 | S064 | TJ-1 | Tongji University | B | 10 (97.84) | — | 1 (1) |  |
| P3 | S065 | TLH-0 | Hispansion | A | 13 (99.68) | 10 (97.6) | 1 (0) |  |
| P3 | S066 | TLM-0 | Hispansion | A | 13 (98.61) | 11 (100) | 1 (0) |  |
| P3 | S069 | TUBS-M | TU Braunschweig | B | 10 (96.96) | — | 1 (1) |  |
| P3 | S070 | TUBS-T | TU Braunschweig | B | 9 (98.63) | — | 1 (1) |  |
| P3 | S077 | LHS-2 | Space Resource Technologies | C | 10 (98.74) | 5 (100) | 1 (0) |  |
| P3 | S078 | LHS-2E | Space Resource Technologies | A | 10 (99.98) | 2 (100) | 1 (0) |  |
| P3 | S079 | LSP-2 | Space Resource Technologies | C | 10 (99.99) | 2 (100) | 1 (0) |  |
| P3 | S081 | JSC-2A | NASA / Zybek | C | 10 (99.34) | 2 (100) | 1 (0) |  |
| P3 | S091 | LHS-1D | Space Resource Technologies | C | 10 (98.74) | 5 (100) | 1 (0) |  |
| P3 | S092 | LHS-1E | Space Resource Technologies | A | 10 (99.98) | 2 (100) | 1 (0) |  |
| P3 | S093 | LHS-1-25A | Space Resource Technologies | C | 10 (99.54) | 6 (99.98) | 1 (0) |  |
| P3 | S094 | LMS-1D | Space Resource Technologies | C | 10 (98.52) | 5 (100) | 1 (0) |  |
| P3 | S095 | LMS-1E | Space Resource Technologies | A | 10 (98.77) | — | 1 (0) |  |
| P3 | S153 | LZS-1 | Instituto de Geociencias (IGEO, CSIC-UCM) | B | 10 (99.8) | — | 1 (1) |  |
| P4 | S001 | AGK-2010 | AGH University of Technology | C | — | — | 1 (0) |  |
| P4 | S002 | ALRS-1 | Australian Space Agency | D | — | — | 1 (1) |  |
| P4 | S003 | ALS | Univ. of Arizona | B | — | — | 1 (1) |  |
| P4 | S008 | CHENOBI | Deltion / NORCAT | C | — | — | 1 (0) |  |
| P4 | S010 | CLRS-1 | Chinese Academy of Sciences | B | — | — | 1 (1) |  |
| P4 | S011 | CSM-CL | Colorado School of Mines | C | — | — | 1 (0) |  |
| P4 | S020 | FJS-1g | JAXA / Shimizu Corporation | D | — | — | 1 (0) |  |
| P4 | S021 | FJS-2 | JAXA / Shimizu Corporation | D | — | — | 1 (0) |  |
| P4 | S022 | FJS-3 | JAXA / Shimizu Corporation | D | — | — | 1 (0) |  |
| P4 | S023 | GCA-1 | Goddard Space Center | C | — | — | 1 (0) |  |
| P4 | S024 | GRC-1 | NASA Glenn Research Center | C | — | — | 1 (0) |  |
| P4 | S026 | JLU-H | Jilin University | B | — | — | 1 (1) |  |
| P4 | S031 | KIGAM-L1 | Korea Institute of Geoscience and Mineral Resources | D | — | — | 1 (0) |  |
| P4 | S033 | KOHLS-1 |  | C | — | — | 1 (0) |  |
| P4 | S034 | Kohyama Simulant | Shimizu Corporation | D | — | — | 1 (0) |  |
| P4 | S035 | LCATS-1 | Astroport Space Technologies | B | — | — | 1 (1) |  |
| P4 | S038 | LSS-ISAC-1 | ISRO | B | — | — | 2 (2) |  |
| P4 | S039 | LuNOR | SolSys Mining | C | — | — | 1 (0) |  |
| P4 | S042 | MKS-1 | Shimizu Corporation | C | — | — | 1 (0) |  |
| P4 | S044 | MLS-2 | Univ. of Minnesota | C | — | — | 1 (0) |  |
| P4 | S046 | NEU-1 | Northeastern University | B | — | — | 1 (1) |  |
| P4 | S048 | NU-LHT-1D | NASA / USGS | C | — | — | 1 (0) |  |
| P4 | S050 | NU-LHT-2C | NASA / USGS | D | — | — | 1 (0) |  |
| P4 | S055 | OPR Agglutinate | Off Planet Research | D | — | — | 1 (0) |  |
| P4 | S056 | OPRFLCROSS2 | Off Planet Research | D | — | — | 1 (0) |  |
| P4 | S057 | OPRH2N | Off Planet Research | D | — | — | 1 (0) |  |
| P4 | S059 | OPRH4N | Off Planet Research | D | — | — | 1 (0) |  |
| P4 | S061 | OPRL2NT | Off Planet Research | D | — | — | 1 (0) |  |
| P4 | S062 | Oshima Simulant | Shimizu Corporation | C | — | — | 1 (0) |  |
| P4 | S068 | TUBS-H | ESA | C | — | — | 1 (0) |  |
| P4 | S071 | UoM-B | Univ. of Manchester | C | — | — | 1 (0) |  |
| P4 | S072 | UoM-W | Univ. of Manchester | C | — | — | 1 (0) |  |
| P4 | S073 | UW-1H | University of Winnipeg | D | — | — | 1 (0) |  |
| P4 | S074 | UW-1M | University of Winnipeg | D | — | — | 1 (0) |  |
| P4 | S075 | WHU-1 | Wuhan University | C | — | — | 2 (0) |  |
| P4 | S080 | IGG-01 | Chinese Academy of Sciences | B | — | — | 1 (1) |  |
| P4 | S082 | GRC-3 | NASA Glenn Research Center | B | — | — | 1 (1) |  |
| P4 | S083 | NAO-2 | Chinese Academy of Sciences | B | — | — | 1 (1) |  |
| P4 | S084 | CLRS-2 | Chinese Academy of Sciences | D | — | — | 1 (0) |  |
| P4 | S085 | JSC-2 | NASA / Zybek | D | — | — | 1 (0) |  |
| P4 | S086 | NU-LHT-2E | NASA / USGS | D | — | — | 1 (0) |  |
| P4 | S087 | NU-LHT-2EG | NASA / USGS | D | — | — | 1 (0) |  |
| P4 | S088 | NU-LHT-3M | NASA / USGS | C | — | — | 1 (0) |  |
| P4 | S090 | NU-LHT-5M | NASA / USGS | D | — | — | 1 (0) |  |
| P4 | S096 | LHD-1D | Space Resource Technologies | D | — | — | 1 (0) |  |
| P4 | S097 | FROST-Y | Space Resource Technologies | C | — | — | 1 (0) |  |
| P4 | S098 | OPRH2W | Off Planet Research | D | — | — | 1 (0) |  |
| P4 | S099 | OPRH3W | Off Planet Research | D | — | — | 1 (0) |  |
| P4 | S101 | OPRL2W | Off Planet Research | D | — | — | 1 (0) |  |
| P4 | S102 | OPRFLCROSS1 | Off Planet Research | A | — | — | 1 (0) |  |
| P4 | S104 | CSM-LHT-1G | Colorado School of Mines | D | — | — | 1 (0) |  |
| P4 | S106 | CSM-CL-S | Colorado School of Mines | C | — | — | 1 (0) |  |
| P4 | S107 | Mooncastle | Colorado School of Mines | D | — | — | 1 (0) |  |
| P4 | S110 | MLS-1P | Univ. of Minnesota | C | — | — | 1 (0) |  |
| P4 | S111 | MLS-1A | Univ. of Minnesota | B | — | — | 1 (1) |  |
| P4 | S112 | LSS-1 | NASA | C | — | — | 1 (0) |  |
| P4 | S113 | LSS-2 | NASA | C | — | — | 1 (0) |  |
| P4 | S114 | LSS-3 | NASA | C | — | — | 1 (0) |  |
| P4 | S115 | LSS-4 | NASA | C | — | — | 1 (0) |  |
| P4 | S116 | LSS-5 | NASA | C | — | — | 1 (0) |  |
| P4 | S118 | Maryland-Sanders |  | A | — | — | 1 (0) |  |
| P4 | S119 | CMU-1 | Carnegie Mellon University | D | — | — | 1 (0) |  |
| P4 | S123 | NEU-1A | Northeastern University | B | — | — | 1 (1) |  |
| P4 | S124 | NEU-1B | Northeastern University | B | — | — | 1 (1) |  |
| P4 | S125 | CUG-1 | China University of Geosciences | B | — | — | 1 (1) |  |
| P4 | S126 | HUST-1 | HUST | D | — | — | 1 (0) |  |
| P4 | S127 | HIT-LRS-1 |  | D | — | — | 1 (0) |  |
| P4 | S128 | CQU-1 |  | D | — | — | 1 (0) |  |
| P4 | S129 | NJU-1 |  | D | — | — | 1 (0) |  |
| P4 | S130 | IRSM-1 |  | C | — | — | 1 (0) |  |
| P4 | S133 | TYII-1 |  | D | — | — | 1 (0) |  |
| P4 | S134 | TYII-2 |  | D | — | — | 1 (0) |  |
| P4 | S135 | ZJM-01 |  | D | — | — | 1 (0) |  |
| P4 | S136 | QH-E |  | D | — | — | 1 (0) |  |
| P4 | S137 | TUBS-I | TU Braunschweig | C | — | — | 1 (0) |  |
| P4 | S138 | LX-I50 | TU Berlin | C | — | — | 1 (0) |  |
| P4 | S139 | SCC-1 | Open University | D | — | — | 1 (0) |  |
| P4 | S140 | SCC-2 | Open University | D | — | — | 1 (0) |  |
| P4 | S141 | OUSR-1 | Open University | D | — | — | 1 (0) |  |
| P4 | S142 | SR-2 | Open University | D | — | — | 1 (0) |  |
| P4 | S143 | OUEB-1 | Open University | D | — | — | 1 (0) |  |
| P4 | S152 | ES-4 | Open University | D | — | — | 1 (0) |  |
| P4 | S154 | KAUMLS | Korea Aerospace University | D | — | — | 1 (0) |  |
| P4 | S155 | TRI-1 |  | D | — | — | 1 (0) |  |
| P4 | S156 | TLS-01A |  | B | — | — | 1 (1) |  |
| P4 | S157 | FEFU-1 |  | D | — | — | 1 (0) |  |
| P4 | S158 | LuSIC-1 | IBeA Research Group, UPV/EHU | B | — | — | 2 (1) |  |
