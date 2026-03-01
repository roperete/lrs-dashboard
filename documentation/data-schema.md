# Data Schema Reference

Last verified: 2026-03-01 | Source: `public/data/*.json` | Types: `src/types.ts`

## Entity Relationship

```
simulant.json (156)  ──< site.json (157)              1:1 (mostly)
       │               ──< composition.json (210)       1:N  mineral %
       │               ──< chemical_composition.json (250)  1:N  oxide wt%
       │               ──< mineral_groups.json (145)    1:N  grouped minerals
       │               ──< references.json (190)        1:N  citations
       │               ──< simulant_extra.json (156)    1:1  extended metadata
       │               ──< purchase_info.json (156)     1:1  vendor info
       │
lunar_reference.json (7)       standalone — Apollo/Luna samples
mineral_sourcing.json (44)     standalone — mineral supply chain
```

All foreign keys use `simulant_id` (S001–S158, excluding S147/S148 martian).
All FK references verified consistent as of v2.8.3.

---

## simulant.json — Core simulant records
**PK:** `simulant_id` (S001–S158) | **Records:** 156

| Field | Type | Notes |
|-------|------|-------|
| simulant_id | string | Primary key, format `S###` |
| name | string | Display name (e.g. "JSC-1A") |
| type | string | "Mare", "Highland", "General" — used for marker colors and filtering |
| country_code | string | Full country name (not ISO code despite field name) |
| institution | string\|null | Producing organization |
| availability | string | "Available", "Limited Stock", "Production stopped", "Unknown" |
| release_date | number\|string\|null | Year as number, sometimes string |
| tons_produced_mt | number\|null | Metric tons produced |
| notes | string\|null | Free text |
| specific_gravity | number\|null | Sparse — many null |
| lunar_sample_reference | string | What lunar sample it replicates ("General", "Apollo 14", etc.) |
| bulk_density | number\|string | Sparse physical property |
| cohesion | number\|string | Sparse |
| friction_angle | number\|string | Sparse |
| density_g_cm3 | number | Sparse |
| particle_size_d50 | string | Sparse, sometimes with units |
| particle_size_distribution | string | Sparse |
| particle_morphology | string | Sparse |
| particle_ruggedness | string | Sparse |
| glass_content_percent | number | Sparse |
| nasa_fom_score | number | Sparse — NASA Figure of Merit |
| ti_content_percent | number | Sparse |

**Business rules:**
- `type` determines marker icon on map: "Highland" -> silver, "Mare" -> amber, else grey
- `availability` determines badge color in PurchaseSection
- Physical properties are very sparse — most simulants only have a few populated
- ComparisonPanel reads physical properties directly from Simulant objects via `Number(simulant[key]) || 0`

---

## simulant_extra.json — Extended metadata (Gasteiner DB)
**PK:** `simulant_id` | **Records:** 156 (1:1 with simulant.json)

| Field | Type | Notes |
|-------|------|-------|
| simulant_id | string | FK -> simulant.json |
| name | string | Redundant with simulant.json |
| classification | string\|null | "Geotechnical", "Chemical/Mineral", etc. |
| application | string\|null | Use case |
| replica_of | string\|null | What it replicates |
| feedstock | string\|null | Base material |
| petrographic_class | string\|null | Rock type classification |
| grain_size_mm | number\|string\|null | Sometimes has ranges as strings |
| specific_gravity | number\|null | May differ from simulant.json value |
| publicly_available_composition | boolean\|null | Whether composition data is published |
| reference | string\|null | Primary citation text |

**Business rules:**
- Displayed in SimulantPanel properties section
- `publicly_available_composition` renders as checkmark/X in table view
- `reference` field here is a display string, NOT linked to references.json

---

## site.json — Geographic locations
**PK:** `site_id` (X###) | **FK:** `simulant_id` | **Records:** 157

| Field | Type | Notes |
|-------|------|-------|
| site_id | string | Primary key, format `X###` |
| simulant_id | string | FK -> simulant.json |
| site_name | string | Institution/lab name |
| site_type | string | "Lab", "University", etc. |
| country_code | string | Full country name |
| lat | number | Latitude (WGS84) |
| lon | number | Longitude (WGS84) |

**Business rules:**
- 157 sites for 156 simulants (one simulant has 2 sites)
- `lat`/`lon` used for both Leaflet 2D markers and Three.js 3D globe points
- Markers are clustered via react-leaflet-cluster (Earth 2D) and custom HTML badges (3D globe)
- `siteBySimulant` Map in App.tsx provides O(1) lookup: simulant_id -> Site

---

## composition.json — Mineral composition (%)
**PK:** `composition_id` (C###) | **FK:** `simulant_id` | **Records:** 210

| Field | Type | Notes |
|-------|------|-------|
| composition_id | string | Primary key |
| simulant_id | string | FK -> simulant.json |
| component_type | string | Always "mineral" |
| component_name | string | Mineral name (e.g. "Plagioclase", "Pyroxene") |
| value_pct | number | Volume/mass percentage |
| group | string | Mineral group name for grouped view |

**Business rules:**
- Only 39 simulants have mineral composition data
- Displayed in MineralChart (bar/pie) and CompositionTable
- Used in ComparisonPanel and CrossComparisonPanel for side-by-side comparison
- `group` field links conceptually to mineral_groups.json

---

## chemical_composition.json — Oxide chemistry (wt%)
**PK:** `composition_id` (CH###) | **FK:** `simulant_id` | **Records:** 250

| Field | Type | Notes |
|-------|------|-------|
| composition_id | string | Primary key |
| simulant_id | string | FK -> simulant.json |
| component_type | string | Always "oxide" |
| component_name | string | Oxide formula (e.g. "SiO2", "Al2O3") |
| value_wt_pct | number | Weight percentage |

**Known data quality issue:** Some records (e.g. S040) have an `oxide` field instead of
`component_type`/`component_name`, and `value_wt_pct` is an object instead of a number.
These are legacy records from bulk import and should be normalized.

**Business rules:**
- Only 33 simulants have chemical composition data
- Displayed in ChemicalChart and CompositionTable
- Used in ComparisonPanel and CrossComparisonPanel
- Common oxides: SiO2, TiO2, Al2O3, FeO, MgO, CaO, Na2O, K2O, MnO, Cr2O3, P2O5

---

## mineral_groups.json — Grouped mineral view
**PK:** `group_id` (MG###) | **FK:** `simulant_id` | **Records:** 145

| Field | Type | Notes |
|-------|------|-------|
| group_id | string | Primary key |
| simulant_id | string | FK -> simulant.json |
| group_name | string | Group (e.g. "Plagioclase Feldspar", "Pyroxene Group") |
| value_pct | number | Percentage |

**Business rules:**
- 29 simulants have grouped mineral data
- Provides a higher-level view than composition.json (aggregated mineral families)

---

## references.json — Scientific citations
**PK:** `reference_id` (R###) | **FK:** `simulant_id` | **Records:** 190

| Field | Type | Notes |
|-------|------|-------|
| reference_id | string | Primary key |
| simulant_id | string | FK -> simulant.json |
| reference_text | string | Full citation text |
| reference_type | string | "composition", "usage", "geotechnical" |

**Business rules:**
- All 156 simulants now have at least one reference (as of v2.8.3)
- R001-R111: curated references; R112-R190: from tentative_references.md (Gemini-generated, sample-verified)
- Displayed in ReferencesSection as numbered cards
- "Cited by" link extracts title and searches Google Scholar
- "Ask AI" button opens Google with `udm=50` param for AI Overview

---

## purchase_info.json — Commercial availability
**PK:** `simulant_id` | **Records:** 156 (1:1 with simulant.json)

| Field | Type | Notes |
|-------|------|-------|
| simulant_id | string | FK -> simulant.json |
| vendor | string\|null | Vendor name, null if not commercially available |
| url | string\|null | Purchase URL, null if no online store |
| price_note | string | Pricing/availability description |

**Business rules:**
- PurchaseSection conditionally renders vendor/url (null-safe since v2.8.3)
- ~14 simulants have direct purchase URLs (SRT, Hispansion, Specialist Aggregates)
- ~10 have "contact for quote" vendors
- Badge color driven by `simulant.availability`, not purchase_info

---

## lunar_reference.json — Real Apollo/Luna samples
**PK:** `sample_id` | **Records:** 7 | **No FK** — standalone

| Field | Type | Notes |
|-------|------|-------|
| mission | string | "Apollo 11", "Apollo 14", etc. |
| landing_site | string | Full site name |
| coordinates | object | `{ lat: number, lon: number }` |
| type | string | "Mare (High-Ti Basalt)", "Highland (Anorthosite)", etc. |
| sample_id | string | Apollo sample number (e.g. "10084") |
| sample_description | string | Description |
| chemical_composition | object | `{ "SiO2": 42.2, "TiO2": 7.8, ... }` — key:value pairs |
| mineral_composition | object | `{ "Plagioclase": 21.0, ... }` — key:value pairs |
| sources | string[] | Citation texts |

**Business rules:**
- Used in CrossComparisonPanel for simulant-vs-lunar-sample comparison
- Auto-inferred from `simulant.lunar_sample_reference` field
- Chemical/mineral composition stored as flat objects (not arrays like simulant data)
- This asymmetry means CrossComparisonPanel must transform the data format

---

## mineral_sourcing.json — Mineral supply chain (CNES/Spring)
**PK:** `mineral_name` (implicit) | **Records:** 44 | **No FK** — standalone

| Field | Type | Notes |
|-------|------|-------|
| mineral_name | string | Mineral identifier |
| chemistry | string | Chemical formula |
| source_mineral | string | Parent mineral description |
| description/description_simple | string | Detailed/simple descriptions |
| mineral_locations | string | Where found naturally |
| mining_locations | string | Active mining sites |
| mining_company | string | Companies |
| mine_active | boolean\|null | Active status |
| ethical_compliance | string | EU compliance note |
| available_france/europe/schengen | boolean\|null | Regional availability |
| supplier | string | Known suppliers |

**Business rules:**
- Displayed in MineralSourcingSection (currently hidden in UI)
- European mineral sourcing focus (CNES/Spring Institute research context)
- Not linked to simulant data — standalone reference table

---

## Lunar sites (hardcoded in lunarData.ts)
Not in JSON — lunar landing sites are defined in `src/lunarData.ts` as a TypeScript array.
20 sites from Apollo, Luna, and Chang'e missions with geotechnical data from Gasteiner et al.
Displayed on Moon 2D/3D views with mission-type-colored lander icons.
