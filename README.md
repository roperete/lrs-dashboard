# Lunar Regolith Simulant Database

An interactive web dashboard for exploring and comparing lunar regolith simulants used in space research and ISRU (In-Situ Resource Utilization) development.

## Overview

Lunar regolith simulants are Earth-based materials designed to replicate the physical, chemical, and mineralogical properties of lunar soil. This dashboard provides researchers, engineers, and educators with a comprehensive database of 75+ simulants from institutions worldwide.

## Features

### Interactive Map
- View simulant origins on a global map
- Click markers to see simulant details
- Filter by country to highlight regions
- Cluster view for areas with multiple simulants

### Filtering & Search
- **Quick Select**: Search simulants by name
- **Type**: Filter by simulant type (Mare, Highland, Geotechnical, etc.)
- **Country**: Filter by country of origin
- **Mineral**: Filter by mineral composition
- **Chemical**: Filter by chemical composition (oxides)
- **Institution**: Filter by producing institution

### Simulant Details Panel
- **Properties**: Type, institution, availability, release date, lunar sample reference
- **Physical Properties**: Density, particle size, morphology, glass content
- **Mineral Composition**: Bar chart of mineral percentages
- **Chemical Composition**: Doughnut chart of oxide composition
- **References**: Academic citations and source papers

### Comparison Mode
- Compare two simulants side-by-side
- View composition differences
- Useful for selecting appropriate simulants for specific research needs

## How to Use

1. **Browse**: Pan and zoom the map to explore simulant locations
2. **Filter**: Use the sidebar filters to narrow down simulants by criteria
3. **Select**: Click a map marker or use the dropdown to select a simulant
4. **View Details**: The bottom panel shows properties, composition charts, and references
5. **Compare**: Click the compare button to select a second simulant for side-by-side comparison
6. **Search Sources**: Click "Sources" to search Google Scholar for related papers

## Data Fields

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

## Data Sources

Simulant data is compiled from:
- NASA Technical Reports
- Lunar Regolith Simulant User's Guide (Slabic et al., 2024)
- Peer-reviewed journal articles
- Institutional documentation

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

## Data Extraction Pipeline

The repository includes an AI-powered data extraction pipeline for populating simulant properties from literature:

```bash
cd scripts
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build document index
python build_pdf_index.py

# Run extraction (requires Anthropic API key)
python batch_extract.py

# Update database
python update_database.py --auto-only
```

## File Structure

```
lrs-dashboard/
├── index.html          # Main application
├── app.js              # Application logic
├── style.css           # Space-tech theme styling
├── data/
│   ├── simulant.json           # Simulant properties
│   ├── composition.json        # Mineral compositions
│   ├── chemical_composition.json # Chemical compositions
│   ├── references.json         # Academic references
│   ├── site.json              # Location coordinates
│   └── countries.geojson      # Country boundaries
├── img/
│   └── moon.png               # Map marker icon
└── scripts/
    ├── config.py              # Extraction configuration
    ├── batch_extract.py       # Batch extraction script
    ├── build_pdf_index.py     # Document indexer
    └── update_database.py     # Database updater
```

## Contributing

Contributions are welcome! If you have:
- Corrections to simulant data
- New simulants to add
- Feature suggestions

Please open an issue or submit a pull request.

## License

This project is open source. Simulant data is compiled from publicly available sources.

## Acknowledgments

- NASA Astromaterials Research and Exploration Science (ARES)
- European Space Agency (ESA)
- All institutions producing lunar regolith simulants
- Researchers who published characterization data

---

*Developed for the Spring Institute for Forest on the Moon*
