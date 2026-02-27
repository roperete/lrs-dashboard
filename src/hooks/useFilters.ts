import { useState, useMemo, useCallback } from 'react';
import type { Simulant, Composition, ChemicalComposition, MineralGroup, Reference, DynamicFilter, FilterProperty, FilterPropertyMeta } from '../types';
import { filterSimulantsDynamic, type FilterContext } from '../utils/filterSimulants';

export const FILTER_PROPERTIES: FilterPropertyMeta[] = [
  { property: 'type', label: 'Type', type: 'categorical' },
  { property: 'country', label: 'Country', type: 'categorical' },
  { property: 'institution', label: 'Institution', type: 'categorical' },
  { property: 'availability', label: 'Availability', type: 'categorical' },
  { property: 'mineral', label: 'Mineral', type: 'categorical' },
  { property: 'chemical', label: 'Chemical Oxide', type: 'categorical' },
  { property: 'has_chemistry', label: 'Has Chemistry Data', type: 'boolean' },
  { property: 'has_mineralogy', label: 'Has Mineralogy Data', type: 'boolean' },
  { property: 'year', label: 'Year', type: 'range' },
  { property: 'reference', label: 'Reference', type: 'text' },
  { property: 'lunar_ref', label: 'Lunar Sample Ref', type: 'text' },
];

let nextId = 1;

export function useFilters(
  simulants: Simulant[],
  compositions: Composition[],
  chemicalCompositions: ChemicalComposition[],
  mineralGroups: MineralGroup[],
  chemicalBySimulant: Map<string, ChemicalComposition[]>,
  compositionBySimulant: Map<string, Composition[]>,
  referencesBySimulant: Map<string, Reference[]>,
) {
  const [filters, setFilters] = useState<DynamicFilter[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  const filterCtx = useMemo<FilterContext>(() => ({
    compositions, chemicalCompositions, mineralGroups,
    chemicalBySimulant, compositionBySimulant, referencesBySimulant,
  }), [compositions, chemicalCompositions, mineralGroups, chemicalBySimulant, compositionBySimulant, referencesBySimulant]);

  const filteredSimulants = useMemo(
    () => filterSimulantsDynamic(simulants, filters, searchQuery, filterCtx),
    [simulants, filters, searchQuery, filterCtx],
  );

  const addFilter = useCallback((property: FilterProperty) => {
    setFilters(prev => [...prev, { id: String(nextId++), property, values: [] }]);
  }, []);

  const updateFilter = useCallback((id: string, values: string[]) => {
    setFilters(prev => prev.map(f => f.id === id ? { ...f, values } : f));
  }, []);

  const removeFilter = useCallback((id: string) => {
    setFilters(prev => prev.filter(f => f.id !== id));
  }, []);

  const clearAllFilters = useCallback(() => {
    setFilters([]);
    setSearchQuery('');
  }, []);

  // Derive available options for categorical filters
  const filterOptions = useMemo(() => {
    const types = [...new Set(simulants.map(s => s.type))].sort();
    const countries = [...new Set(simulants.map(s => s.country_code))].filter(Boolean).sort();
    const rawInstitutions = [...new Set(simulants.map(s => s.institution).filter(Boolean))].sort();
    const hasNASA = rawInstitutions.some(i => i.toLowerCase().includes('nasa'));
    const institutions = hasNASA ? ['NASA (all)', ...rawInstitutions] : rawInstitutions;

    const detailedMinerals = [...new Set(compositions.map(c => c.component_name))].sort();
    const groupMinerals = [...new Set(mineralGroups.map(g => g.group_name))].sort();

    const chemicals = [...new Set(
      chemicalCompositions
        .filter(c => c.component_type === 'oxide' && c.component_name !== 'sum')
        .map(c => c.component_name)
    )].sort();

    const availabilities = [...new Set(simulants.map(s => s.availability).filter(Boolean))].sort();

    return { types, countries, institutions, detailedMinerals, groupMinerals, chemicals, availabilities };
  }, [simulants, compositions, mineralGroups, chemicalCompositions]);

  return {
    filters, filteredSimulants, searchQuery,
    addFilter, updateFilter, removeFilter, clearAllFilters, setSearchQuery,
    filterOptions,
  };
}
