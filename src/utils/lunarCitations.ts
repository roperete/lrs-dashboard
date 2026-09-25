import type { LunarDocument, LunarSource } from '../types';

export interface LunarCite {
  n: number;
  location: string | null;
  quote: string;
  document: LunarDocument;
}

export interface LunarCitations {
  /** The entity's documents, in citation-number order (index 0 is [1]). */
  documents: LunarDocument[];
  /** The citations of one field: a column name, "oxide:SiO2", "mineral:Plagioclase" or "description". */
  cite: (field: string) => LunarCite[];
}

/** Display order of a site's values, so its sources are numbered as they appear on the page. */
export const SITE_FIELD_ORDER = ['date', 'samples_returned', 'description', 'bulk_density', 'friction_angle', 'cohesion', 'bearing_capacity', 'lat', 'lng'];
/** Display order of a sample's values; a trailing ':' matches every component of that kind. */
export const SAMPLE_FIELD_ORDER = ['landing_site', 'type', 'oxide:', 'mineral:'];

export const EMPTY_CITATIONS: LunarCitations = { documents: [], cite: () => [] };

/**
 * The numbered sources of one lunar site or sample. Documents are numbered in the order their
 * first value appears on the page (fieldOrder), then any remaining ones by field name.
 */
export function lunarCitations(
  entityId: string,
  sources: LunarSource[],
  documents: LunarDocument[],
  fieldOrder: string[] = [],
): LunarCitations {
  const docs = new Map(documents.map(d => [d.document_id, d] as const));
  const rank = (field: string) => {
    const i = fieldOrder.findIndex(p => (p.endsWith(':') ? field.startsWith(p) : field === p));
    return i < 0 ? fieldOrder.length : i;
  };
  const mine = sources
    .filter(s => s.entity_id === entityId && docs.has(s.document_id))
    .sort((a, b) => rank(a.field) - rank(b.field) || a.field.localeCompare(b.field));
  const number = new Map<string, number>();
  for (const s of mine) if (!number.has(s.document_id)) number.set(s.document_id, number.size + 1);
  const byField = new Map<string, LunarCite[]>();
  for (const s of mine) {
    const list = byField.get(s.field) ?? [];
    list.push({ n: number.get(s.document_id)!, location: s.location, quote: s.quote, document: docs.get(s.document_id)! });
    byField.set(s.field, list);
  }
  return {
    documents: [...number.keys()].map(id => docs.get(id)!),
    cite: field => byField.get(field) ?? [],
  };
}

/** "Wagner et al. (2017)" style label for a hover or a list entry. */
export function lunarDocumentLabel(d: LunarDocument): string {
  const who = (d.authors || '').split(/[;,]| and /)[0]?.trim();
  const year = d.year ? ` (${d.year})` : '';
  return who ? `${who}${/[;,]| and /.test(d.authors || '') ? ' et al.' : ''}${year}` : d.title;
}
