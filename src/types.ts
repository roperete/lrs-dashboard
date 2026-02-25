export interface Simulant {
  simulant_id: string;
  name: string;
  type: string;
  country_code: string;
  institution: string;
  availability: string;
  release_date: number | string;
  tons_produced_mt: number | null;
  notes: string;
  specific_gravity: number | null;
  lunar_sample_reference: string;
}

export interface Site {
  site_id: string;
  simulant_id: string;
  site_name: string;
  site_type: string;
  country_code: string;
  lat: number | null;
  lon: number | null;
}

export interface Composition {
  composition_id: string;
  simulant_id: string;
  component_type: string;
  component_name: string;
  value_pct: number;
}

export interface ChemicalComposition {
  composition_id: string;
  simulant_id: string;
  component_type: string;
  component_name: string;
  value_wt_pct: number;
}

export interface Reference {
  reference_id: string;
  simulant_id: string;
  reference_text: string;
  reference_type: string;
}

export interface MineralGroup {
  group_id: string;
  simulant_id: string;
  group_name: string;
  value_pct: number;
}

export interface SimulantExtra {
  simulant_id: string;
  name: string;
  classification: string | null;
  application: string | null;
  replica_of: string | null;
  feedstock: string | null;
  petrographic_class: string | null;
  grain_size_mm: number | null;
  specific_gravity: number | null;
  publicly_available_composition: boolean;
  reference: string | null;
}

export interface LunarReference {
  mission: string;
  landing_site: string;
  coordinates: { lat: number; lon: number };
  type: string;
  sample_id: string;
  sample_description: string;
  chemical_composition: Record<string, number>;
  mineral_composition?: Record<string, number>;
  sources: string[];
}

export interface MineralSourcing {
  simulant_id: string;
  [key: string]: unknown;
}

export interface LunarSite {
  id: string;
  name: string;
  mission: string;
  date: string;
  lat: number;
  lng: number;
  samples_returned?: string;
  description: string;
  type: 'Apollo' | 'Luna' | 'Chang-e' | 'Other';
}

export interface CustomMarker {
  id: string;
  lat: number;
  lng: number;
  label: string;
}

export interface CustomPolygon {
  id: string;
  positions: [number, number][];
  color: string;
}

export interface FilterState {
  type: string[];
  country: string[];
  mineral: string[];
  chemical: string[];
  institution: string[];
}

export interface PanelState {
  open: boolean;
  pinned: boolean;
  simulantId: string | null;
}
