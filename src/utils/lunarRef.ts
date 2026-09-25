/**
 * The Apollo or Chang'e reference sample a simulant's producer says it replicates, read from
 * the simulant's lunar_sample_reference ("Apollo 14 soils", "60501", "CE-5"). Used only to
 * suggest a comparison; the panel labels it as a suggestion.
 */
export function suggestedLunarMission(ref: string | null | undefined): string | null {
  if (!ref) return null;
  const lower = ref.toLowerCase();
  if (lower.includes('apollo 11') || lower === '10084') return 'Apollo 11';
  if (lower.includes('apollo 12') || lower === '12070') return 'Apollo 12';
  if (lower.includes('apollo 14') || lower === '14163') return 'Apollo 14';
  if (lower.includes('apollo 15') || lower === '15271') return 'Apollo 15';
  if (lower.includes('apollo 16') || lower === '60501') return 'Apollo 16';
  if (lower.includes('apollo 17') || lower === '71501') return 'Apollo 17';
  if (lower.includes("chang'e") || lower.includes('change') || lower.includes('ce5') || lower.includes('ce-5')) return "Chang'e-5";
  return null;
}

/** A lunar sample can be compared only when it shows at least one cited oxide or mineral: one
 *  whose values are all hidden (not traced to a source) would give a column of dashes. */
export function hasLunarValues(r: { chemical_composition?: Record<string, number> | null; mineral_composition?: Record<string, number> | null }): boolean {
  return Object.keys(r.chemical_composition ?? {}).length > 0 || Object.keys(r.mineral_composition ?? {}).length > 0;
}
