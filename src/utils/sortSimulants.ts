import type { Simulant, ChemicalComposition, Composition, Reference } from '../types';
import { getCountryDisplay } from './countryUtils';

export type SortDir = 'asc' | 'desc';
export type SortKey = 'name' | 'type' | 'country' | 'institution' | 'availability' | 'lunar_sample_reference' | 'year'
  | 'specific_gravity' | 'bulk_density' | 'd50' | 'friction_angle' | 'cohesion' | 'has_chemistry' | 'has_mineralogy' | 'references';

export const SORT_KEYS: SortKey[] = ['name', 'type', 'country', 'institution', 'availability', 'lunar_sample_reference', 'year',
  'specific_gravity', 'bulk_density', 'd50', 'friction_angle', 'cohesion', 'has_chemistry', 'has_mineralogy', 'references'];

export interface SortContext {
  chemicalBySimulant: Map<string, ChemicalComposition[]>;
  compositionBySimulant: Map<string, Composition[]>;
  referencesBySimulant: Map<string, Reference[]>;
}

/** A sparse numeric-ish field as a number, or null when absent or not a number. */
const num = (v: unknown): number | null => {
  if (v == null || v === '') return null;
  const n = Number(v);
  return Number.isNaN(n) ? null : n;
};
const text = (v: unknown): string | null => (v == null || v === '' ? null : String(v).toLowerCase());

function value(s: Simulant, key: SortKey, ctx: SortContext): string | number | null {
  switch (key) {
    case 'name': return text(s.name);
    case 'type': return text(s.type);
    case 'country': return text(getCountryDisplay(s.country_code));
    case 'institution': return text(s.institution);
    case 'availability': return text(s.availability);
    case 'lunar_sample_reference': return text(s.lunar_sample_reference);
    case 'year': return typeof s.release_date === 'number' ? s.release_date : num(s.release_date);
    case 'specific_gravity': return num(s.specific_gravity);
    case 'bulk_density': return num(s.bulk_density);
    case 'd50': return num(s.particle_size_d50);
    case 'friction_angle': return num(s.friction_angle);
    case 'cohesion': return num(s.cohesion);
    case 'has_chemistry': return ctx.chemicalBySimulant.has(s.simulant_id) ? 1 : 0;
    case 'has_mineralogy': return ctx.compositionBySimulant.has(s.simulant_id) ? 1 : 0;
    case 'references': return (ctx.referencesBySimulant.get(s.simulant_id) || []).length;
  }
}

/**
 * The table's order. Empty values always sort last, whichever the direction: a missing value is
 * not the smallest one. Every field may be empty on some record, so nothing here may assume a
 * string (v2.9.17-18: sorting by Country called toLowerCase() on null and blanked the page).
 */
export function sortSimulants(simulants: Simulant[], key: SortKey, dir: SortDir, ctx: SortContext): Simulant[] {
  const sign = dir === 'asc' ? 1 : -1;
  return [...simulants].sort((a, b) => {
    const va = value(a, key, ctx), vb = value(b, key, ctx);
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;
    if (typeof va === 'string' && typeof vb === 'string') return va.localeCompare(vb) * sign;
    return ((va as number) - (vb as number)) * sign;
  });
}
