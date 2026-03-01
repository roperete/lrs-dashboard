# CLAUDE.md — Lunar Regolith Simulant Dashboard

## Project
React + TypeScript + Vite dashboard for 156 lunar regolith simulants.
3D globe (Three.js/react-globe.gl), 2D map (Leaflet), table view, comparison panels, filtering.
Data: JSON files in `public/data/`, types in `src/types.ts`.

## Documentation Lookup
Before modifying a feature, read its doc first.

| Working on... | Read first |
|---|---|
| Data files, JSON structure, adding/modifying simulant data | `documentation/data-schema.md` |
| Comparison panels (simulant vs simulant, or vs lunar ref) | `documentation/data-schema.md` (composition + lunar_reference sections) |
| Map markers, clustering, globe points | `src/components/map/` + `src/lunarData.ts` |
| Sidebar filters | `src/components/sidebar/DynamicFilterPanel.tsx` |
| Purchase info, availability badges | `documentation/data-schema.md` (purchase_info section) |
| References, citations, Scholar links | `documentation/data-schema.md` (references section) |

## Architecture
```
src/
  App.tsx              — Main orchestrator: state, data loading, routing
  types.ts             — All TypeScript interfaces
  lunarData.ts         — Hardcoded lunar landing sites (20 sites)
  components/
    map/               — GlobeView (3D), LeafletMap (2D)
    panels/            — SimulantPanel, ComparisonPanel, CrossComparisonPanel, LunarSitePanel
    sidebar/           — Sidebar, DynamicFilterPanel, SimulantList
    table/             — SimulantTable, LunarSampleTable
    controls/          — ExportMenu, LegendWidget, LoadingScreen
    layout/            — AppHeader, MapToolbar
    ui/                — PanelShell, ToggleButtonGroup
  utils/cn.ts          — Tailwind class merge utility
public/data/           — JSON datasets (see documentation/data-schema.md)
```

## Conventions
- Tailwind CSS, dark theme (slate-900 base)
- Lucide React icons
- Framer Motion (motion/react) for panel animations
- No tests, no API — static JSON loaded at startup via fetch
- Semver: PATCH for fixes, MINOR for features. Current: v2.8.3
- Version displayed in Sidebar.tsx — bump on every release
- Branching: dev -> staging -> main. GitHub Pages deploys staging and main automatically.
- Omit "Co-authored by Claude" in commits

## Data Integrity Rules
- `simulant_id` is the universal FK (S001-S158, no S147/S148 — those were martian, deleted)
- Every simulant must have entries in: simulant.json, simulant_extra.json, site.json, purchase_info.json, references.json
- composition.json and chemical_composition.json are sparse (only ~33-39 simulants have data)
- Physical properties on simulant.json are sparse — use `Number(val) || 0` and filter out zeros
- lunar_reference.json stores composition as `{ "SiO2": 42.2 }` objects, NOT arrays — different format from simulant composition data

## Common Pitfalls
- `country_code` field contains full country names, not ISO codes
- `release_date` can be number, string, or null
- Some chemical_composition records have legacy `oxide` field + nested object `value_wt_pct` (S040) — needs normalization
- PurchaseSection: vendor and url can be null — always check before rendering
- Marker type detection: `sim.type?.toLowerCase()` then check `.includes('highland')` / `.includes('mare')`
