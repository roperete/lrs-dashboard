# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Lunar Regolith Simulant (LRS) Database** - an interactive web dashboard for exploring and comparing lunar regolith simulants from around the world. It's a static frontend-only application (no build system) that uses Leaflet maps, Chart.js visualizations, and GeoJSON data.

## Development

### Running Locally

Open `index.html` directly in a browser, or serve with any static file server:
```bash
python3 -m http.server 8000
# Then visit http://localhost:8000
```

No build step, no dependencies to install.

### External Dependencies (CDN)

- Leaflet 1.9.4 (map rendering)
- Leaflet.MarkerCluster 1.5.3 (marker clustering)
- Chart.js 4.4.0 (composition charts)

## Architecture

### Single-Page Application Structure

The app loads all data at startup via `Promise.all()` in `app.js`, then uses client-side filtering:

```
index.html          - UI structure with sidebar, map container, info panels
app.js              - All application logic (~700 lines)
style.css           - CSS variables, panel animations, responsive layout
```

### Data Model

Five JSON files in `data/` form a relational structure linked by `simulant_id`:

| File | Purpose | Key Fields |
|------|---------|------------|
| `simulant.json` | Core simulant records (74 entries) | `simulant_id`, `name`, `type`, `country_code`, `availability` |
| `site.json` | Geographic locations | `simulant_id`, `lat`, `lon`, `site_name` |
| `composition.json` | Mineral composition (%) | `simulant_id`, `component_name`, `value_pct` |
| `chemical_composition.json` | Oxide composition (wt%) | `simulant_id`, `component_name`, `value_wt_pct` |
| `references.json` | Scientific references | `simulant_id`, `reference_text` |

### Key State Variables (app.js)

- `markerMap` - Maps `simulant_id` to Leaflet markers for programmatic popup control
- `panelStates` - Tracks open/pinned state for both info panels
- `compareMode` - Boolean for side-by-side simulant comparison
- `countryLayer` - Current GeoJSON highlight layer

### UI Components

1. **Sidebar** (left) - Multi-select filters for type, country, mineral, chemical composition
2. **Map** (center) - Leaflet with marker clustering, custom moon icons
3. **Country Panel** (right, slide-in) - Lists simulants when country filter is active
4. **Info Panels** (bottom, slide-up) - Two panels for comparing simulant compositions

### Filter Behavior

Filters use click-to-toggle selection (not standard multi-select). The `updateMap()` function applies all active filters with AND logic across categories, OR logic within each category.

### Country Code Handling

The `countryMap` object translates country names to ISO codes. Special handling for "EU" which highlights all 27 EU member states defined in `euCountries` array.
