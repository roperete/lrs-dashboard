# Lunar Regolith Simulant Database

An interactive web dashboard for exploring and comparing lunar regolith simulants used in space research and ISRU (In-Situ Resource Utilization) development.

Developed by **Spring Institute for Forest on the Moon** | Sponsored by **CNES**

## Overview

Lunar regolith simulants are Earth-based materials designed to replicate the physical, chemical, and mineralogical properties of lunar soil. This dashboard provides researchers, engineers, and educators with a comprehensive database of 80+ simulants from institutions worldwide.

## Features

### Interactive Map
- View simulant origins on a global map
- Click markers to see simulant details
- Filter by country to highlight regions (EU filter highlights all member states)
- Cluster view for areas with multiple simulants

### Filtering & Search
- **Quick Select**: Search simulants by name
- **Type**: Filter by simulant type (Mare, Highland, Geotechnical, etc.)
- **Country**: Filter by country of origin
- **Mineral**: Filter by detailed mineral or NASA mineral group
- **Chemical**: Filter by chemical composition (oxides)
- **Institution**: Filter by producing institution

### Simulant Details Panel
- **Properties**: Type, institution, availability, release date, lunar sample reference
- **Physical Properties**: Density, particle size, morphology, glass content
- **Mineral Composition**: Detailed minerals and NASA mineral group views with toggle
- **Chemical Composition**: Doughnut chart of oxide composition
- **References**: Separated into composition source papers and usage studies

### Comparison Mode
- Compare two simulants side-by-side
- View composition differences
- Useful for selecting appropriate simulants for specific research needs

### Data Export
- Export filtered simulants to CSV
- Download individual simulant data
- Composition and reference data included in exports

## How to Use

1. **Browse**: Pan and zoom the map to explore simulant locations
2. **Filter**: Use the sidebar filters to narrow down simulants by criteria
3. **Select**: Click a map marker or use the dropdown to select a simulant
4. **View Details**: The bottom panel shows properties, composition charts, and references
5. **Compare**: Click the compare button to select a second simulant for side-by-side comparison
6. **Toggle View**: Switch between detailed minerals and NASA mineral groups
7. **Search Sources**: Click "Sources" to search Google Scholar for related papers

## Data

### Fields

| Field | Description |
|-------|-------------|
| Type | Simulant category (Mare, Highland, Dust, Geotechnical) |
| Lunar Sample | Apollo/Luna mission sample being replicated |
| Institution | Organization that developed the simulant |
| Availability | Current availability status |
| Release Date | Year the simulant was first produced |
| Density | Bulk density in g/cm³ |
| Glass Content | Percentage of glass/agglutinates |
| Particle Size | Size distribution or median particle size |
| Particle Morphology | Shape description (angular, sub-angular, etc.) |
| NASA FoM Score | NASA Figures of Merit score when available |

### NASA Mineral Groups

The dashboard supports both detailed mineral composition and aggregated NASA mineral groups:

| Group | Includes |
|-------|----------|
| Plagioclase Feldspar | Plagioclase, Anorthite, Labradorite, Bytownite, Albite, Anorthosite |
| Pyroxene | Augite, Clinopyroxene, Orthopyroxene, Bronzite |
| Olivine | Olivine, Forsterite, Fayalite |
| Ilmenite | Ilmenite |
| Glass | Glass, Volcanic Glass, Agglutinate, Glass-rich Basalt |

Hovering over a NASA group in the chart shows the detailed minerals that contribute to it.

### Sources

Simulant data is compiled from:
- Spec sheets and technical data sheets (primary source)
- Peer-reviewed characterization papers
- NASA Technical Reports and Lunar Simulant Assessment Reports
- Institutional documentation

### Composition Data Policy

- Composition data is sourced from a single authoritative reference per simulant
- Spec sheets take priority over research papers
- All mineral compositions are validated to sum to ≤100%
- Manually curated data is preserved and never overwritten by automated extraction

## Technical Stack

- **Frontend**: HTML, CSS, JavaScript
- **Mapping**: Leaflet.js with marker clustering
- **Charts**: Chart.js
- **Data**: JSON files
- **Hosting**: GitHub Pages

## Local Development

```bash
# Clone the repository
git clone https://github.com/roperete/lrs-dashboard.git
cd lrs-dashboard

# Serve locally (Python 3)
python -m http.server 8000

# Open in browser
open http://localhost:8000
```

## File Structure

```
lrs-dashboard/
├── index.html                  # Main application
├── app.js                      # Application logic
├── style.css                   # Space-tech theme styling
├── data/
│   ├── simulant.json           # Simulant properties
│   ├── composition.json        # Mineral compositions
│   ├── chemical_composition.json # Chemical compositions (oxides)
│   ├── mineral_groups.json     # NASA mineral group classifications
│   ├── references.json         # Academic references (composition + usage)
│   ├── site.json               # Location coordinates
│   └── countries.geojson       # Country boundaries
├── img/
│   └── moon.png                # Map marker icon
└── scripts/
    ├── import_curated_data.py  # Import verified composition data
    ├── specsheet_data.json     # Curated composition from spec sheets
    ├── populate_mineral_groups.py # Generate NASA groups from minerals
    ├── classify_references.py  # Classify references by type
    └── extractors/             # Document extraction tools
```

## Contributing

Contributions are welcome. If you have:
- Corrections to simulant data
- New simulants to add
- Feature suggestions

Please open an issue or submit a pull request.

## License

This project is open source. Simulant data is compiled from publicly available sources.

## Acknowledgments

- CNES (Centre National d'Etudes Spatiales)
- NASA Astromaterials Research and Exploration Science (ARES)
- European Space Agency (ESA)
- All institutions producing lunar regolith simulants
- Researchers who published characterization data

---

*Developed by Spring Institute for Forest on the Moon, sponsored by CNES*
