import type { DynamicFilter, FilterProperty } from '../types';

/**
 * The page's state in the query string (review #13), so a view can be shared and cited:
 *   ?planet=earth&view=table&sim=S028&cmp=S028,S051&f=type:Mare|Highlands;bulk_density:1.2..1.6&q=jsc&site=A11
 * Filters: property:values, values joined with "|", a range as "min..max".
 */
export interface UrlState {
  planet?: 'earth' | 'moon';
  view?: 'globe' | 'map' | 'table';
  sim?: string;
  cmp?: string[];
  filters?: { property: FilterProperty; values: string[] }[];
  q?: string;
  site?: string;
}

const RANGE_PROPERTIES = new Set(['year', 'bulk_density', 'd50', 'friction_angle', 'cohesion']);

export function readUrlState(search: string = window.location.search): UrlState {
  const p = new URLSearchParams(search);
  const out: UrlState = {};
  const planet = p.get('planet'); if (planet === 'earth' || planet === 'moon') out.planet = planet;
  const view = p.get('view'); if (view === 'globe' || view === 'map' || view === 'table') out.view = view;
  if (p.get('sim')) out.sim = p.get('sim')!;
  if (p.get('cmp')) out.cmp = p.get('cmp')!.split(',').filter(Boolean).slice(0, 4);
  if (p.get('q')) out.q = p.get('q')!;
  if (p.get('site')) out.site = p.get('site')!;
  const f = p.get('f');
  if (f) {
    out.filters = f.split(';').map(part => {
      const i = part.indexOf(':');
      if (i < 0) return null;
      const property = part.slice(0, i) as FilterProperty;
      const raw = part.slice(i + 1);
      const values = RANGE_PROPERTIES.has(property) ? raw.split('..') : raw.split('|');
      return { property, values };
    }).filter((x): x is { property: FilterProperty; values: string[] } => !!x && x.values.some(v => v !== ''));
  }
  return out;
}

export function writeUrlState(s: UrlState): string {
  const p = new URLSearchParams();
  if (s.planet && s.planet !== 'earth') p.set('planet', s.planet);
  if (s.view && s.view !== 'globe') p.set('view', s.view);
  if (s.sim) p.set('sim', s.sim);
  if (s.cmp && s.cmp.length) p.set('cmp', s.cmp.join(','));
  if (s.filters && s.filters.length) {
    p.set('f', s.filters.map(f => `${f.property}:${RANGE_PROPERTIES.has(f.property) ? f.values.join('..') : f.values.join('|')}`).join(';'));
  }
  if (s.q) p.set('q', s.q);
  if (s.site) p.set('site', s.site);
  const qs = p.toString();
  return qs ? `?${qs}` : window.location.pathname;
}

export function filtersForUrl(filters: DynamicFilter[]): { property: FilterProperty; values: string[] }[] {
  return filters.filter(f => f.values.some(v => v !== '')).map(f => ({ property: f.property, values: f.values }));
}
