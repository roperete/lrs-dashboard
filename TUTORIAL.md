# Lunar Regolith Simulant Dashboard — User Guide (v2.8.0)

A comprehensive guide to using the Lunar Regolith Simulant Database, an interactive web application for exploring, comparing, and exporting data on Earth-made lunar soil simulants and actual lunar landing sites.

**Live:** [https://roperete.github.io/lrs-dashboard/](https://roperete.github.io/lrs-dashboard/)

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Navigation & Layout](#navigation--layout)
3. [View Modes](#view-modes)
4. [Planet Toggle: Earth & Moon](#planet-toggle-earth--moon)
5. [Sidebar: Search, Filter & Browse](#sidebar-search-filter--browse)
6. [Simulant Detail Panel](#simulant-detail-panel)
7. [Lunar Reference Comparison](#lunar-reference-comparison)
8. [Cross-Comparison Panel](#cross-comparison-panel)
9. [Two-Simulant Comparison](#two-simulant-comparison)
10. [Table View Features](#table-view-features)
11. [Map Controls & Toolbar](#map-controls--toolbar)
12. [Exporting Data](#exporting-data)
13. [Legend](#legend)
14. [Mobile & Responsive Behavior](#mobile--responsive-behavior)
15. [Feature Summary](#feature-summary)

---

## Getting Started

When the dashboard loads, you'll see a 3D interactive globe showing Earth with colored dots representing lunar regolith simulants developed by institutions worldwide. The left sidebar lists all simulants and provides search and filtering tools. Click any dot on the globe or any item in the sidebar to explore its data.

---

## Navigation & Layout

The interface has four main areas:

| Area | Location | Purpose |
|------|----------|---------|
| **Header** | Top bar | Planet toggle (Earth/Moon), view mode (3D/2D/Table), geocoding search |
| **Sidebar** | Left panel (320px) | Search bar, dynamic filters, simulant/mission list |
| **Main View** | Center | Globe, map, or table visualization |
| **Detail Panel** | Right side | Selected simulant or lunar site details, charts, comparisons |

---

## View Modes

Switch between three visualization modes using the buttons in the header:

### 3D Globe

The default view. An interactive WebGL globe you can rotate by clicking and dragging, and zoom with the scroll wheel.

- **Data points** appear as colored dots on the globe surface.
- **Clusters**: When zoomed out, nearby simulants merge into numbered cluster badges. Click a cluster once to see a popover listing the simulants at that location. Double-click a cluster to auto-zoom into it.
- **Day/Night toggle**: Switch the Earth texture between daytime and nighttime views using the sun/moon button on the right toolbar.

### 2D Map

A flat OpenStreetMap-based view with the same data points as markers.

- Supports standard pan and zoom controls.
- Marker clustering behaves the same as the globe — zoom in to see individual markers.
- Markers are color-coded by type (green for Mare simulants, cyan for Highlands).

### Table

A sortable, full-featured data table replacing the map entirely.

- Click any column header to sort ascending/descending.
- Click a row to select a simulant and open its detail panel.
- Use checkboxes for multi-select operations (comparison, export).

See [Table View Features](#table-view-features) for full details.

---

## Planet Toggle: Earth & Moon

The header contains an **Earth / Moon** toggle that switches between two datasets:

### Earth Mode
- Shows **lunar regolith simulants** — synthetic materials made by institutions to replicate lunar soil.
- Dots are placed at the institution's geographic location.
- Color coding: **Green** = Mare type, **Cyan** = Highlands type.
- Full filtering, comparison, and export features available.

### Moon Mode
- Shows **actual lunar landing sites** — Apollo, Luna, Chang'e, and other missions.
- Dots are placed at the landing coordinates on the Moon's surface.
- Color coding: **Orange** = Apollo, **Red** = Luna, **Blue** = Chang'e, **Purple** = Other.
- Clicking a site opens a panel with mission metadata, description, and geotechnical properties.
- No filters available in Moon mode (only search).

---

## Sidebar: Search, Filter & Browse

### Opening & Closing
- Click the **hamburger icon** (top-left) to open the sidebar.
- Click the **chevron** or area outside the sidebar to close it.
- On mobile, the sidebar appears as a full-width overlay and closes automatically when you select an item.

### Search Bar
Type in the search field to instantly filter the list. Matching is case-insensitive and works on partial strings.
- **Earth mode**: Searches simulant names.
- **Moon mode**: Searches mission names.

### Dynamic Filters (Earth Mode Only)

Click **"Add filter"** to add one or more filter criteria. Filters apply with AND logic between different properties and OR logic within the same property.

| Filter | Type | Description |
|--------|------|-------------|
| **Type** | Categorical | Mare, Highland, etc. |
| **Country** | Categorical | Country of origin (includes "European Union") |
| **Institution** | Categorical | Producing institution. "NASA (all)" groups all NASA centers. |
| **Availability** | Categorical | Available, Pending, etc. |
| **Mineral** | Grouped dropdown | Detailed minerals or NASA Mineral Groups (prefixed with `group:`) |
| **Chemical Oxide** | Categorical | Filter by presence of specific oxides |
| **Has Chemistry Data** | Boolean | Yes / No |
| **Has Mineralogy Data** | Boolean | Yes / No |
| **Year** | Range slider | Release year range (min–max) |
| **Lunar Sample Reference** | Categorical | Apollo, Luna, or Chang'e reference samples |
| **Reference** | Text search | Free-text search within bibliography |

Each active filter appears as a card with an **X** button to remove it. Use **"Clear All"** to reset all filters and search at once.

### Simulant / Mission List
Below the filters, a collapsible list shows all items matching the current search and filter criteria. The count is displayed at the bottom of the sidebar (e.g., "42 / 66 simulants").

- Click any item to select it and open its detail panel.
- The selected item is highlighted with an emerald green border (simulants) or amber border (lunar sites).

---

## Simulant Detail Panel

When you select a simulant, a panel slides in from the right showing:

### Header
- Simulant name, classification, and type.
- **Pin button**: Keeps the panel open while you navigate.
- **Download button**: Exports this simulant's data as CSV.
- **Compare button**: Enables comparison mode (see [Two-Simulant Comparison](#two-simulant-comparison)).
- **Close button**: Dismisses the panel.

### Properties Table
Key metadata displayed as a two-column grid:
- Type, Origin (country), Institution, Availability, Release Date
- Specific Gravity, Lunar Sample Reference, Production (metric tons)
- Classification, Application, Feedstock, Grain Size (mm)
- Petrographic Class (rock composition breakdown)

### Physical Properties
If available, a grid of cards showing measured physical properties.

### Purchase Information
Availability status and any known purchase links.

### Mineral Composition
- **Detailed / Groups toggle**: Switch between individual minerals and NASA mineral group classification.
- **Chart / Table toggle**: View as horizontal bar chart or tabular data.
- Bars are sorted by percentage, highest first.
- If a lunar reference is selected, its values appear as an amber overlay.

### Chemical Composition
- **Chart / Table toggle**: Same as mineral composition.
- Shows oxide weight percentages (wt%), excludes "sum" entries.
- Lunar reference overlay in amber/gold when active.

### References
Numbered list of citations with:
- Clickable **"Source"** or **"DOI"** links when available.
- **"Google Scholar"** search link for each reference.

---

## Lunar Reference Comparison

When viewing a simulant that has chemistry or mineralogy data, you'll see a **Lunar Reference** selector in the detail panel.

### How It Works
1. The dashboard **auto-infers** the most relevant lunar reference from the simulant's `lunar_sample_reference` field. For example, a simulant referencing Apollo 11 soil 10084 automatically selects the Apollo 11 reference.
2. You can also manually select a different reference from the dropdown.
3. Once selected, the **mineral and chemical charts** show the lunar reference values as amber-colored bars alongside the simulant's green/blue bars.

### Dropdown Options
- **"No reference comparison"** — Hides reference overlay.
- **Mission entries** — e.g., "Apollo 11 — Mare Tranquillitatis (Mare)" with landing site and type.

---

## Cross-Comparison Panel

For a dedicated full-screen comparison between a simulant and a lunar reference sample:

1. Select a lunar reference in the dropdown (see above).
2. Click **"Full comparison view"**.
3. A panel slides up showing side-by-side data.

### Layout
- **Header**: Simulant name (blue) vs. Lunar mission/sample (amber).
- **Metadata row**: Landing site, mission type, and simulant reference number.
- **Chart / Table toggle**.

### Chart View
Two vertical bar charts:
- **Chemical Composition (wt%)**: Simulant bars (blue) next to reference bars (amber).
- **Mineral Composition (%)**: Same layout.

### Table View
Two delta tables with columns:
- **Component** | **Simulant value** | **Reference value** | **Delta (difference)**
- Delta is color-coded: blue when simulant is higher, amber when reference is higher.
- Missing data shown as em-dash (—).

---

## Two-Simulant Comparison

Compare any two simulants side by side:

### From the Table View
1. Check the boxes next to exactly **2 simulants**.
2. A toolbar appears at the top with a blue **"Compare"** button.
3. Click it to open the comparison panel.

### From the Sidebar
1. Select a simulant to open its detail panel.
2. Click the **Compare** button in the panel header.
3. Click a second simulant — it opens in comparison mode.

### Comparison Panel
- **Header**: Both simulant names color-coded (emerald vs. blue).
- **Chart / Table toggle**.
- **Chart view**: Two side-by-side bar charts (mineral and chemical compositions).
- **Table view**: Merged component list with columns for both simulants and a delta column showing the difference. Delta values are color-coded (green if simulant 1 is higher, blue if simulant 2 is higher).

---

## Table View Features

### Simulant Table (Earth Mode)

| Column | Description |
|--------|-------------|
| Checkbox | Select for multi-operations |
| Name | Simulant name |
| Type | Mare, Highland, etc. |
| Country | Country code |
| Institution | Producing organization |
| Availability | Current availability status |
| Lunar Ref | Referenced lunar sample |
| Year | Release year (numeric sort) |
| Chem | Checkmark if chemistry data exists |
| Miner | Checkmark if mineralogy data exists |
| Reference | Primary citation (click to expand full text) |

### Sorting
Click any column header to sort. An arrow icon indicates the current sort direction. Click again to reverse.

### Multi-Select Toolbar
When one or more checkboxes are active, a sticky toolbar appears:
- **"X selected"** — Count of checked items.
- **"Compare"** — Opens comparison panel (enabled when exactly 2 selected).
- **"Export Selected"** — Downloads CSV of checked simulants.
- **"Clear"** — Unchecks all.

### Lunar Sample Table (Moon Mode)
Columns: Name, Mission, Date, Type, Samples Returned. Click a row to view mission details.

---

## Map Controls & Toolbar

A vertical toolbar on the right side provides quick actions:

| Button | Function |
|--------|----------|
| **Fullscreen** | Toggle browser fullscreen mode |
| **Day/Night** | Switch Earth globe texture (3D only) |
| **My Location** | Center the view on your GPS location (requires browser permission) |
| **Home** | Reset to default view (Europe centered) |

The toolbar is hidden in Table view.

---

## Exporting Data

An **Export** button in the bottom-right corner offers three options:

| Option | Description |
|--------|-------------|
| **Export Current Simulant** | CSV of the currently selected simulant (if any) |
| **Export Filtered** | CSV of all simulants matching current search/filters |
| **Export All** | CSV of the entire dataset |

Files are named with a timestamp (e.g., `simulant_data_2026-02-28.csv`).

You can also export individual simulants using the **download button** in the detail panel header.

---

## Legend

A small legend widget in the bottom-left corner shows the current color coding:

- **Earth mode**: Green = Mare Simulant, Cyan = Highlands Simulant.
- **Moon mode**: Orange = Apollo, Red = Luna, Blue = Chang'e, Purple = Other.

---

## Mobile & Responsive Behavior

The dashboard adapts to different screen sizes:

| Feature | Desktop | Mobile/Tablet |
|---------|---------|---------------|
| Sidebar | Fixed 320px panel | Full-width overlay, auto-closes on selection |
| Detail panel | Fixed 450px right panel | Full-width bottom sheet |
| Header | Full layout with all controls | Compact with abbreviated labels (3D/2D) |
| Geocoding search | Visible | Hidden |
| Comparison panel | Full height | 80% viewport height |

---

## Feature Summary

| Feature | Description |
|---------|-------------|
| 3D Globe | Interactive WebGL Earth/Moon with rotation, zoom, clustering |
| 2D Map | OpenStreetMap with markers and clustering |
| Table View | Sortable, filterable data table with multi-select |
| Planet Toggle | Switch between Earth simulants and Moon landing sites |
| Search | Real-time name filtering |
| Dynamic Filters | 11 filter types with AND/OR logic |
| Simulant Panel | Full metadata, properties, charts, references |
| Chemical Chart | Oxide composition bar chart with table toggle |
| Mineral Chart | Mineral composition with Detailed/Groups and Chart/Table toggles |
| Lunar Reference | Compare simulant to actual lunar sample data |
| Cross-Comparison | Full-screen simulant vs. lunar reference comparison |
| Two-Simulant Compare | Side-by-side comparison of any two simulants |
| CSV Export | Export single, filtered, or all simulants |
| Responsive Design | Desktop, tablet, and mobile layouts |
| Code-Split Bundles | Lazy-loaded components for fast initial load |

---

*Lunar Regolith Simulant Database v2.8.0 — Sponsored by CNES*
