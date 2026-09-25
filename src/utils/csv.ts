import type { Simulant, Composition, ChemicalComposition, Reference, PropertySource, FigureOfMerit } from '../types';
import { orderReferences } from './references';
import { getCountryDisplay } from './countryUtils';

function escapeCSV(value: unknown): string {
  if (value === null || value === undefined) return '';
  let str = String(value).replace(/\r?\n/g, ' ').trim();
  if (/[",;]/.test(str) || str.startsWith('=') || str.startsWith('+') || str.startsWith('-') || str.startsWith('@')) {
    // quote anything a spreadsheet would split or read as a formula
    str = '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

/** Everything the export needs; each list may hold every simulant's rows, the export picks its own. */
export interface ExportData {
  compositions: Composition[];
  chemicalCompositions: ChemicalComposition[];
  references: Reference[];
  propertySources?: PropertySource[];
  figuresOfMerit?: FigureOfMerit[];
}

const IDENTITY: { key: keyof Simulant; label: string }[] = [
  { key: 'type', label: 'Type' },
  { key: 'country_code', label: 'Country' },
  { key: 'institution', label: 'Producer' },
  { key: 'availability', label: 'Availability' },
  { key: 'release_date', label: 'Released' },
  { key: 'lunar_sample_reference', label: 'Lunar sample it replicates' },
];
const PROPERTIES: { key: keyof Simulant; label: string; unit: string }[] = [
  { key: 'bulk_density', label: 'Bulk density', unit: 'g/cm³' },
  { key: 'bulk_density_range', label: 'Bulk density range', unit: '' },
  { key: 'density_g_cm3', label: 'Particle density', unit: 'g/cm³' },
  { key: 'specific_gravity', label: 'Specific gravity', unit: '' },
  { key: 'cohesion', label: 'Cohesion', unit: 'kPa' },
  { key: 'friction_angle', label: 'Friction angle', unit: '°' },
  { key: 'angle_of_repose', label: 'Angle of repose', unit: '' },
  { key: 'particle_size_d50', label: 'Particle size D50', unit: 'µm' },
  { key: 'particle_size_mean_um', label: 'Mean particle size', unit: 'µm' },
  { key: 'particle_size_distribution', label: 'Particle size distribution', unit: '' },
  { key: 'particle_morphology', label: 'Particle morphology', unit: '' },
  { key: 'ph', label: 'pH', unit: '' },
  { key: 'magnetic_susceptibility', label: 'Magnetic susceptibility', unit: '' },
  { key: 'glass_content_percent', label: 'Glass content', unit: '%' },
  { key: 'ti_content_percent', label: 'Ti content', unit: '%' },
];

const HEADERS = ['simulant_id', 'simulant', 'section', 'field', 'value', 'unit', 'value_as_stated',
  'ref_no', 'reference', 'doi_or_url', 'location', 'quote'];

/**
 * One row per value the page shows, each with the reference it is cited to (numbered as in the
 * pane), where in that document it was read, and the quoted line; then the simulant's full
 * reference list (review #17: the old export dropped every source and most references).
 */
export function buildCSV(simulants: Simulant[], data: ExportData): string {
  const rows: string[][] = [];
  for (const s of simulants) {
    const refs = orderReferences(data.references.filter(r => r.simulant_id === s.simulant_id));
    const number = new Map(refs.map((r, i) => [r.reference_id, i + 1] as const));
    const byId = new Map(refs.map(r => [r.reference_id, r] as const));
    const sources = new Map((data.propertySources ?? []).filter(p => p.simulant_id === s.simulant_id).map(p => [p.field, p] as const));
    const refCols = (rid: string | null | undefined, location?: string | null, quote?: string | null): string[] => {
      const r = rid ? byId.get(rid) : undefined;
      return [rid ? String(number.get(rid) ?? '') : '', r ? (r.title || r.reference_text || '') : '',
        r ? (r.doi ? `https://doi.org/${r.doi}` : r.url || '') : '', location ?? '', quote ?? ''];
    };
    const push = (section: string, field: string, value: unknown, unit: string, stated: unknown, ref: string[]) =>
      rows.push([s.simulant_id, s.name, section, field, value, unit, stated, ...ref].map(escapeCSV));

    for (const f of IDENTITY) {
      const v = f.key === 'country_code' ? getCountryDisplay(s.country_code) : s[f.key];
      if (v == null || v === '') continue;
      const src = sources.get(String(f.key));
      push('identity', f.label, v, '', '', refCols(src?.reference_id, src?.location, src?.quote));
    }
    for (const f of PROPERTIES) {
      const v = s[f.key];
      if (v == null || v === '') continue;
      const src = sources.get(String(f.key));
      push('property', f.label, v, f.unit, '', refCols(src?.reference_id, src?.location, src?.quote));
    }
    for (const c of data.chemicalCompositions.filter(c => c.simulant_id === s.simulant_id && c.component_type === 'oxide' && c.component_name !== 'sum')) {
      push('oxide', c.component_name, c.value_wt_pct, 'wt%', c.value_text ?? '', refCols(c.reference_id));
    }
    for (const c of data.compositions.filter(c => c.simulant_id === s.simulant_id)) {
      push('mineral', c.component_name, c.value_pct, '%', c.value_text ?? '', refCols(c.reference_id));
    }
    for (const f of (data.figuresOfMerit ?? []).filter(f => f.simulant_id === s.simulant_id)) {
      push('figure_of_merit', `${f.property_label} vs ${f.reference_sample ?? '—'}`, f.score, f.scale ?? '', f.score_text ?? '', refCols(f.reference_id, f.location, f.quote));
    }
    refs.forEach((r, i) => rows.push([s.simulant_id, s.name, 'reference', `[${i + 1}]`,
      r.title || r.reference_text || '', '', r.names_simulant === 1 ? 'names this simulant' : r.names_simulant === 0 ? 'does not name this simulant' : '',
      String(i + 1), r.reference_text || r.title || '', r.doi ? `https://doi.org/${r.doi}` : r.url || '', '', r.mention_quote || ''].map(escapeCSV)));
  }
  // a byte-order mark first, so spreadsheet programs read the file as UTF-8 (µ, °, ³)
  return '\uFEFF' + [HEADERS.join(','), ...rows.map(r => r.join(','))].join('\n');
}

export function exportToCSV(simulants: Simulant[], data: ExportData, filename: string) {
  downloadFile(buildCSV(simulants, data), filename, 'text/csv;charset=utf-8;');
}

export function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function downloadSimulantCSV(simulant: Simulant, data: ExportData) {
  const timestamp = new Date().toISOString().slice(0, 10);
  exportToCSV([simulant], data, `${simulant.name.replace(/[^a-z0-9]/gi, '_')}_${timestamp}.csv`);
}
