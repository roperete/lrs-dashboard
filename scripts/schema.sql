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
  ti_content_percent        REAL
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
  value_wt_pct   REAL
);

CREATE TABLE IF NOT EXISTS mineral_compositions (
  composition_id TEXT PRIMARY KEY,
  simulant_id    TEXT REFERENCES simulants(simulant_id),
  component_type TEXT,
  component_name TEXT,
  value_pct      REAL
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
  reference_type TEXT,
  title          TEXT,
  authors        TEXT,
  year           INTEGER,
  doi            TEXT,
  url            TEXT
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
