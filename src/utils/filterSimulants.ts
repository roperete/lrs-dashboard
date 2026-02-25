import type { Simulant, Composition, ChemicalComposition, MineralGroup, FilterState } from '../types';
import { isEUMember } from './countryUtils';

export function filterSimulants(
  simulants: Simulant[],
  filters: FilterState,
  searchQuery: string,
  compositions: Composition[],
  chemicalCompositions: ChemicalComposition[],
  mineralGroups: MineralGroup[],
): Simulant[] {
  return simulants.filter(s => {
    // Search query
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const match = s.name.toLowerCase().includes(q) ||
        s.country_code.toLowerCase().includes(q) ||
        s.type.toLowerCase().includes(q) ||
        (s.institution || '').toLowerCase().includes(q);
      if (!match) return false;
    }

    // Type filter
    if (filters.type.length > 0 && !filters.type.includes(s.type)) return false;

    // Country filter (with EU expansion)
    if (filters.country.length > 0) {
      const hasEU = filters.country.includes('EU');
      const match = filters.country.includes(s.country_code) ||
        (hasEU && isEUMember(s.country_code));
      if (!match) return false;
    }

    // Mineral filter (detailed + group: prefixed)
    if (filters.mineral.length > 0) {
      const detailedMinerals = filters.mineral.filter(m => !m.startsWith('group:'));
      const groupMinerals = filters.mineral.filter(m => m.startsWith('group:')).map(m => m.slice(6));

      const hasDetailedMatch = detailedMinerals.length === 0 ||
        compositions.some(c =>
          c.simulant_id === s.simulant_id &&
          detailedMinerals.includes(c.component_name) &&
          c.value_pct > 0
        );

      const hasGroupMatch = groupMinerals.length === 0 ||
        mineralGroups.some(g =>
          g.simulant_id === s.simulant_id &&
          groupMinerals.includes(g.group_name) &&
          g.value_pct > 0
        );

      if (!hasDetailedMatch && !hasGroupMatch) return false;
    }

    // Chemical filter
    if (filters.chemical.length > 0) {
      const hasMatch = chemicalCompositions.some(c =>
        c.simulant_id === s.simulant_id &&
        filters.chemical.includes(c.component_name) &&
        c.value_wt_pct > 0
      );
      if (!hasMatch) return false;
    }

    // Institution filter
    if (filters.institution.length > 0) {
      if (!filters.institution.includes(s.institution || '')) return false;
    }

    return true;
  });
}
