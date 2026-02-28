# UX DataViz Reviewer — Project Memory

## Stack
- React 19 + TypeScript + Vite + Tailwind v4
- Chart library: Recharts (in package.json; usage in panels not yet audited)
- Globe: react-globe.gl v2.37 (Three.js wrapper by vasturiano)
- 2D map: react-leaflet v5 + react-leaflet-cluster v4 (spiderfication works well)
- Animation: motion/react (Framer Motion)
- Geospatial: @turf/turf for proximity calculations

## Key Files
- `/src/App.tsx` — main orchestrator, globe data prep, all event handlers
- `/src/components/map/GlobeView.tsx` — thin react-globe.gl wrapper (forwardRef)
- `/src/components/map/LeafletMap.tsx` — Leaflet map with MarkerClusterGroup
- `/src/types.ts` — Simulant, Site, Composition, ChemicalComposition, etc.
- `/src/hooks/useMapState.ts` — all map/globe view state
- `/src/hooks/usePanelState.ts` — panel open/pinned/selected state
- `/src/hooks/useFilters.ts` — filter logic
- `/public/data/site.json` — one site per simulant, lat/lon per institution

## Data Reality: Co-location is Severe
Co-located groups confirmed in site.json (exact same lat/lon):
- JAXA Tsukuba: S019, S020, S021, S022 (4 simulants)
- Orbitec Madison WI: S027, S028, S029, S030 (4 simulants)
- NASA MSFC Huntsville: S048, S049, S050+ (3+ simulants)
- CAS Beijing: S007, S009, S010 (3 simulants, exact match)
- Shimizu Tokyo: S034, S042 (2 simulants)
- TU Berlin: S040, S041 (2 simulants)
- EAC Cologne: S017, S018 (2 simulants)
- Space Resource Technologies Orlando: S016, S036, S037 (3 simulants)
- Monolite/Bari: S014, S015 (2 simulants)
- U of Minnesota: S043, S044 (2 simulants)
This is a structural data problem — institutions produce multiple simulants.

## Current Co-location Hack (App.tsx lines 87–112)
Groups by 0.1-degree rounding, then spiral-offsets by OFFSET=0.8 degrees.
Problems: 0.8 deg ~89 km at equator — points land in ocean/wrong country.
The grouping threshold is also wrong: CAS (116.33) and NAO Beijing (116.39)
would land in the same 0.1-deg bucket even though they are different institutions.

## Color Scheme
- Earth simulant (mare): #10b981 (emerald-500)
- Earth simulant (highland): #06b6d4 (cyan-500)
- Moon sites (Apollo): #f59e0b (amber-500)
- Moon sites (Luna): #ef4444 (red-500)
- Moon sites (Other): #3b82f6 (blue-500)
- Background/UI: slate-900/slate-950 dark theme
- NOTE: Red (#ef4444) + Green (#10b981) co-exist — colorblind issue for Luna vs mare simulants in legend. Flag when reviewing legend.

## Terminology
- "Simulant" (not "analog") — used throughout codebase
- "Site" = production/research institution location (one per simulant)
- "Lunar reference" = actual Apollo/Luna sample data for comparison
- oxide composition uses wt% (weight percent), labeled value_wt_pct

## Data Coverage (158 simulants total)
- Core metadata (name, type, country, institution, availability, lunar_sample_reference): ~158/158
- Chemical composition (any oxide): 30/158 (19%). Top oxides: SiO2 30, Al2O3 30, CaO 27, TiO2 21, MgO 20
- Physical properties: bulk_density 26/158, cohesion 25/158, specific_gravity 23/158, particle_size_d50 7/158, nasa_fom_score 3/158
- Availability breakdown: Available 74, Unknown 49, Production stopped 21, Limited Stock 13, Research Only 1
- Type breakdown: Mare 72, Highlands 47, General 23, Engineering 4, Specialty 4, Dust Simulant 3, Lunar Icy 3
- Top countries: USA 70, China 32, UK 16, Japan 7, Germany 7
- IMPORTANT: Sparse columns (oxide wt%, physical props) will be ~80% empty in a table — must use '—' not blank/0

## Table View Analysis (evaluated 2026-02-27)
- Gap identified: no "ranking/scanning" view — sidebar list is not sortable, shows only name/country/type
- Recommended table columns (always-present): Name, Type, Country, Institution, Availability, Lunar Reference, Release Date
- Recommended sparse columns (toggle-able, default hidden or clearly marked): SiO2 wt%, Al2O3 wt%, TiO2 wt%, Bulk Density, Specific Gravity
- Integration: add 'table' to viewMode union in useMapState.ts; add Table button to AppHeader.tsx view toggle
- Row click → onSelectSimulant (reuses existing handler); compare button per row → onSelectCompare
- Sort must be numeric (not lexicographic) — release_date is typed number|string, needs parseFloat()
- Export from table view must use current sorted array, not raw filteredSimulants

## Globe API Constraints (react-globe.gl v2.37)
- pointsData: flat colored spheres, pointAltitude scales height above surface
- htmlElementsData: arbitrary DOM — rendered as CSS-transformed divs, can cause perf issues at 157 points if complex
- labelsData: text labels, always face camera
- onPointClick/onPointHover: work per-point, no built-in cluster support
- No native clustering support — must be implemented manually
- Globe altitude (zoom) is accessible via globeRef.current.pointOfView()
- See: globe-design-decision.md for the co-location solution analysis
