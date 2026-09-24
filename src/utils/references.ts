import type { Reference } from '../types';

/**
 * Per-simulant reference numbering. A simulant's references are numbered 1..n in
 * reference_id order; the number is derived wherever it is rendered and never stored,
 * so the References section and every superscript agree by construction.
 */

/** Code-point order, the order SQL gives for ORDER BY reference_id. Ids are zero-padded
 *  (R033, DS-S036), so this is also the order a reader expects. */
export function compareReferenceIds(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

/** A simulant's references in numbering order. Returns a sorted copy. */
export function orderReferences(references: Reference[]): Reference[] {
  return [...references].sort((a, b) => compareReferenceIds(a.reference_id, b.reference_id));
}

/** reference_id to its 1-based number within the simulant's list. */
export function referenceNumbers(references: Reference[]): Map<string, number> {
  const numbers = new Map<string, number>();
  orderReferences(references).forEach((r, i) => numbers.set(r.reference_id, i + 1));
  return numbers;
}

/** The number of one reference, or undefined when the id is not in the list. */
export function referenceNumber(references: Reference[], referenceId: string | null | undefined): number | undefined {
  return referenceId ? referenceNumbers(references).get(referenceId) : undefined;
}

/** Hover text for a composition row: the value as the document states it, when that says
 *  more than the number the table shows (the basis, the uncertainty, "ca."), then the source. */
export function rowCitationTooltip(stated: string | null | undefined, sourceLabel: string | undefined): string | undefined {
  const parts = [stated?.trim() ? `Stated as: ${stated.trim()}` : undefined, sourceLabel].filter((p): p is string => !!p);
  return parts.length ? parts.join(' — ') : undefined;
}

/** First line of a citation hover: "First author et al. (year). Title", else the citation text. */
export function referenceHoverLabel(reference: Reference | undefined): string | undefined {
  if (!reference) return undefined;
  const authors = (reference.authors || '').trim();
  const first = authors.split(/;| and /)[0].trim().replace(/,?\s*et al\.?$/, '');
  const who = authors ? `${first}${first.length < authors.length || /et al/.test(authors) ? ' et al.' : ''}` : '';
  const head = [who, reference.year ? `(${reference.year})` : ''].filter(Boolean).join(' ');
  const title = (reference.title || '').trim();
  const text = title ? (head ? `${head}. ${title}` : title) : (reference.reference_text || '').trim();
  if (!text) return undefined;
  return text.length > 180 ? text.slice(0, 177) + '...' : text;
}

/** Short hover label for a citation: the title, else authors and year, else the citation text. */
export function referenceShortLabel(reference: Reference | undefined): string | undefined {
  if (!reference) return undefined;
  if (reference.title) return reference.title;
  if (reference.authors) return reference.year ? `${reference.authors} (${reference.year})` : reference.authors;
  const text = reference.reference_text?.trim();
  if (!text) return undefined;
  return text.length > 140 ? text.slice(0, 137) + '...' : text;
}
