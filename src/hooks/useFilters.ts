import { useState, useMemo, useCallback } from 'react';
import type { Simulant, Composition, ChemicalComposition, MineralGroup, FilterState } from '../types';
import { filterSimulants } from '../utils/filterSimulants';

const emptyFilters: FilterState = {
  type: [], country: [], mineral: [], chemical: [], institution: [],
};

export function useFilters(
  simulants: Simulant[],
  compositions: Composition[],
  chemicalCompositions: ChemicalComposition[],
  mineralGroups: MineralGroup[],
) {
  const [filters, setFilters] = useState<FilterState>(emptyFilters);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSimulants = useMemo(
    () => filterSimulants(simulants, filters, searchQuery, compositions, chemicalCompositions, mineralGroups),
    [simulants, filters, searchQuery, compositions, chemicalCompositions, mineralGroups],
  );

  const setFilter = useCallback((key: keyof FilterState, values: string[]) => {
    setFilters(prev => ({ ...prev, [key]: values }));
  }, []);

  const toggleFilterValue = useCallback((key: keyof FilterState, value: string) => {
    setFilters(prev => {
      const current = prev[key];
      const next = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value];
      return { ...prev, [key]: next };
    });
  }, []);

  const clearAllFilters = useCallback(() => {
    setFilters(emptyFilters);
    setSearchQuery('');
  }, []);

  // Derive available filter options from data
  const filterOptions = useMemo(() => {
    const types = [...new Set(simulants.map(s => s.type))].sort();
    const countries = [...new Set(simulants.map(s => s.country_code))].filter(Boolean).sort();
    const institutions = [...new Set(simulants.map(s => s.institution).filter(Boolean))].sort();

    const detailedMinerals = [...new Set(compositions.map(c => c.component_name))].sort();
    const groupMinerals = [...new Set(mineralGroups.map(g => g.group_name))].sort();

    const chemicals = [...new Set(
      chemicalCompositions
        .filter(c => c.component_type === 'oxide' && c.component_name !== 'sum')
        .map(c => c.component_name)
    )].sort();

    return { types, countries, institutions, detailedMinerals, groupMinerals, chemicals };
  }, [simulants, compositions, mineralGroups, chemicalCompositions]);

  return {
    filters, filteredSimulants, searchQuery,
    setFilter, toggleFilterValue, clearAllFilters, setSearchQuery,
    filterOptions,
  };
}
