# lrs-dashboard

Lunar Regolith Simulant dashboard — interactive data visualization for LRS research.

## Stack

- **Frontend:** Vanilla JS + CSS, no build step, no framework
- **Data pipeline:** Python 3.11, scripts in `scripts/`
- **Dev server:** `python -m http.server 8000` from project root

## Key Files

| File | Size | Purpose |
|------|------|---------|
| `app.js` | 84KB | Main application logic (all JS in one file) |
| `style.css` | 30KB | All styles |
| `index.html` | Entry point | HTML structure |
| `data/*.json` | Datasets | lunar_reference, chemical_composition, simulant, mineral_groups, etc. |
| `scripts/` | Python | Data extraction, PDF parsing, DB updates, AI pipeline |

## Data Files (data/)

- `lunar_reference.json` — Reference lunar soil compositions
- `chemical_composition.json` — Simulant chemical data
- `simulant.json` / `simulant_extra.json` — Simulant metadata
- `mineral_groups.json` — Mineral classification
- `mineral_sourcing.json` — Sourcing information
- `references.json` — Literature references
- `site.json` — Lunar landing site data
- `countries.geojson` — Map data
- `LMNotebook_list.json` — Notebook listing

## Model Routing

Use subagents (Task tool) to keep main Opus context lean:

| Task | Model | Why |
|------|-------|-----|
| Exploring/searching codebase | Haiku | Fast, cheap, read-only |
| Reading/summarizing data files | Haiku | No reasoning needed |
| Data validation/diffing | Sonnet | Moderate reasoning |
| Planning implementation | Sonnet | Good reasoning, cheaper than Opus |
| Writing/editing JS/Python code | Opus (main) | Needs full capability |
| Git operations, commits | Haiku | Mechanical tasks |

**Rules:**
- Never read large data files (>100 lines) directly into main context. Delegate to Haiku subagent with a specific question.
- For codebase exploration, use `subagent_type=Explore` with Haiku model.
- For data summarization, use `subagent_type=general-purpose` with Haiku model and a focused prompt.
- Keep app.js reads targeted — use line offsets, never read the full 84KB file.

## Common Tasks

### Add/update a data visualization
1. Explore current implementation in app.js (Haiku subagent)
2. Plan changes (Sonnet subagent if complex)
3. Edit app.js and style.css (main context)

### Update data pipeline
1. Read relevant script in scripts/ (direct Read with offset if large)
2. Edit Python script (main context)
3. Test: `cd scripts && python -m pytest` or run specific script

### Process bulk data files
Use `scripts/batch_claude.sh` for parallel processing of JSON files.

## Versioning

**CRITICAL:** Every commit must bump the version in `index.html:33`:
```html
<span class="version-tag">vX.Y.Z</span>
```
- **Major (X):** Breaking changes, full redesign
- **Minor (Y):** New features, data expansions, new visualizations
- **Patch (Z):** Bug fixes, small corrections, styling tweaks
