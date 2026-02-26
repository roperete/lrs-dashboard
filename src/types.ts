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
  // Physical properties (sparse — not all simulants have these)
  bulk_density?: number | string | null;
  cohesion?: number | string | null;
  friction_angle?: number | string | null;
  density_g_cm3?: number | null;
  particle_size_d50?: number | null;
  particle_size_distribution?: string | null;
  particle_morphology?: string | null;
  particle_ruggedness?: string | null;
  glass_content_percent?: number | null;
  nasa_fom_score?: number | null;
  ti_content_percent?: number | null;
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
  mineral_name: string;
  chemistry?: string;
  source_mineral?: string;
  description?: string;
  description_simple?: string;
  mineral_locations?: string;
  mining_locations?: string;
  mining_company?: string;
  mine_active?: boolean;
  ethical_compliance?: string;
  available_france?: boolean;
  available_europe?: boolean;
  available_schengen?: boolean;
  supplier?: string;
  further_reading?: string;
  european_sources?: string;
}

export interface PurchaseInfo {
  simulant_id: string;
  vendor: string;
  url: string;
  price_note?: string;
}

export interface PhysicalProperties {
  bulk_density?: number;
  cohesion?: number;
  friction_angle?: number;
  specific_gravity?: number;
  particle_size_d50?: number;
  particle_size_distribution?: string;
  particle_morphology?: string;
  particle_ruggedness?: string;
  density_g_cm3?: number;
  glass_content_percent?: number;
  nasa_fom_score?: number;
  ti_content_percent?: number;
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
  availability: string[];
}

export interface PanelState {
  open: boolean;
  pinned: boolean;
  simulantId: string | null;
}
