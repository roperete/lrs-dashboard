-- LRS Database Schema
-- Source of truth for all simulant data. Edit this DB, run export_json.py to regenerate public/data/data.json.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS simulants (
  simulant_id               TEXT PRIMARY KEY,
  name                      TEXT NOT NULL,
  type                      TEXT,
  country_code              TEXT,
  institution               TEXT,
  availability              TEXT,
  release_date              TEXT,
  tons_produced_mt          REAL,
  notes                     TEXT,
  specific_gravity          REAL,
  lunar_sample_reference    TEXT,
  bulk_density              TEXT,
  cohesion                  TEXT,
  friction_angle            TEXT,
  density_g_cm3             REAL,
  particle_size_d50         REAL,
  particle_size_distribution TEXT,
  particle_morphology       TEXT,
  particle_ruggedness       TEXT,
  glass_content_percent     REAL,
  nasa_fom_score            REAL,
  ti_content_percent        REAL,
  datasheet_url             TEXT, -- manufacturer/spec datasheet, distinct from academic references
  -- Provenance of the composition data (see scripts/reconcile.py):
  --   verified | withheld_unverified | not_published | not_extracted
  composition_status        TEXT,
  composition_source_title  TEXT,
  composition_source_url    TEXT,
  composition_source_kind   TEXT,  -- manufacturer_datasheet | primary_paper | agency_report
  composition_needs_review  INTEGER,
  -- Stated on the manufacturer data sheet (scripts/datasheet_fill.py, 2026-09-22)
  ph                        REAL,
  angle_of_repose           TEXT,  -- as stated, with the sample mass used
  particle_size_mean_um     REAL,
  bulk_density_range        TEXT,  -- min-max or loose-settled, as stated
  magnetic_susceptibility   TEXT,  -- mass susceptibility, as stated
  product_grade             TEXT,  -- the sheet's own "Simulant Type" / series wording
  datasheet_document_id     TEXT,  -- document / batch code printed on the sheet
  datasheet_date            TEXT,  -- revision date of the sheet used
  datasheet_notes           TEXT   -- methods, labs and caveats printed on the sheet
);

CREATE TABLE IF NOT EXISTS simulant_extra (
  simulant_id                    TEXT PRIMARY KEY REFERENCES simulants(simulant_id),
  name                           TEXT,
  classification                 TEXT,
  application                    TEXT,
  replica_of                     TEXT,
  feedstock                      TEXT,
  petrographic_class             TEXT,
  grain_size_mm                  REAL,
  specific_gravity               REAL,
  publicly_available_composition INTEGER,  -- boolean: 0/1
  reference                      TEXT
);

CREATE TABLE IF NOT EXISTS sites (
  site_id      TEXT PRIMARY KEY,
  simulant_id  TEXT REFERENCES simulants(simulant_id),
  site_name    TEXT,
  site_type    TEXT,
  country_code TEXT,
  lat          REAL,
  lon          REAL
);

CREATE TABLE IF NOT EXISTS chemical_compositions (
  composition_id TEXT PRIMARY KEY,
  simulant_id    TEXT REFERENCES simulants(simulant_id),
  component_type TEXT,
  component_name TEXT,
  value_wt_pct   REAL,
  reference_id   TEXT REFERENCES references_(reference_id), -- the document this row was read from
  value_text     TEXT            -- the value as stated, when it says more than the number
);

CREATE TABLE IF NOT EXISTS mineral_compositions (
  composition_id TEXT PRIMARY KEY,
  simulant_id    TEXT REFERENCES simulants(simulant_id),
  component_type TEXT,
  component_name TEXT,
  value_pct      REAL,
  reference_id   TEXT REFERENCES references_(reference_id), -- the document this row was read from
  value_text     TEXT            -- the value as stated, when it says more than the number
);

-- Provenance of scalar values on simulants: one row per (simulant, field).
-- A scalar with no row here is unsourced and is not exported for display.
CREATE TABLE IF NOT EXISTS property_sources (
  simulant_id   TEXT NOT NULL REFERENCES simulants(simulant_id),
  field         TEXT NOT NULL,   -- column name on simulants, e.g. cohesion, ph, bulk_density
  reference_id  TEXT NOT NULL REFERENCES references_(reference_id),
  location      TEXT,            -- page, table or figure as the reader found it
  quote         TEXT,            -- the line stating the value
  PRIMARY KEY (simulant_id, field)
);

CREATE TABLE IF NOT EXISTS mineral_groups (
  group_id    TEXT PRIMARY KEY,
  simulant_id TEXT REFERENCES simulants(simulant_id),
  group_name  TEXT,
  value_pct   REAL
);

CREATE TABLE IF NOT EXISTS references_ (
  reference_id   TEXT PRIMARY KEY,
  simulant_id    TEXT REFERENCES simulants(simulant_id),
  reference_text TEXT,
  reference_type TEXT,           -- datasheet | composition | geotechnical | usage | review | report | general
  title          TEXT,
  authors        TEXT,
  year           INTEGER,
  doi            TEXT,
  url            TEXT,
  -- Per-value provenance (2026-09-22): the reference list is the registry of documents
  names_simulant INTEGER,        -- 1 confirmed to name this exact simulant, 0 checked and absent, NULL unchecked
  mention_quote  TEXT,           -- the sentence naming the simulant
  local_path     TEXT,           -- copy under DIRT/Sources used for verification; never displayed
  checked_on     TEXT            -- ISO date of last verification
);

CREATE TABLE IF NOT EXISTS purchase_info (
  simulant_id TEXT PRIMARY KEY REFERENCES simulants(simulant_id),
  vendor      TEXT,
  url         TEXT,
  price_note  TEXT
);

-- Nested JSON stored as TEXT (coordinates, chemical_composition, mineral_composition, sources)
CREATE TABLE IF NOT EXISTS lunar_references (
  sample_id           TEXT PRIMARY KEY,
  mission             TEXT,
  landing_site        TEXT,
  coordinates         TEXT,  -- JSON: {"lat": ..., "lon": ...}
  type                TEXT,
  sample_description  TEXT,
  chemical_composition TEXT, -- JSON: {"SiO2": 42.2, ...}
  mineral_composition  TEXT, -- JSON or NULL
  sources             TEXT   -- JSON array of strings
);

CREATE TABLE IF NOT EXISTS mineral_sourcing (
  mineral_name             TEXT PRIMARY KEY,
  chemistry                TEXT,
  source_mineral           TEXT,
  description              TEXT,
  description_simple       TEXT,
  comments                 TEXT,
  mineral_locations        TEXT,
  mining_locations         TEXT,
  mining_company           TEXT,
  mine_active              INTEGER,  -- boolean: 0/1
  ethical_compliance       TEXT,
  available_france         INTEGER,  -- boolean: 0/1
  available_europe         INTEGER,
  available_schengen       INTEGER,
  supplier                 TEXT,
  further_reading          TEXT,
  european_sources         TEXT,
  european_locations_detail TEXT
);

-- Figures of Merit: one score per (simulant, property, lunar reference), each cited (2026-09-25).
-- An FoM compares a simulant with a lunar reference material property by property; a single
-- column would lose what it measures and against what.
CREATE TABLE IF NOT EXISTS figures_of_merit (
  fom_id           TEXT PRIMARY KEY,
  simulant_id      TEXT NOT NULL REFERENCES simulants(simulant_id),
  property         TEXT NOT NULL,   -- composition | mineralogy | particle_size | shape | density | overall | other
  property_label   TEXT NOT NULL,   -- as the document names it
  reference_sample TEXT,            -- the lunar material it is scored against, as stated
  score            REAL NOT NULL,
  scale            TEXT,            -- 0-1, 0-100, % ... as the document uses
  score_text       TEXT,            -- the score as printed
  reference_id     TEXT NOT NULL REFERENCES references_(reference_id),
  location         TEXT,
  quote            TEXT
);
