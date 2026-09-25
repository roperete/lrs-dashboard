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
  { property: 'has_geotechnical', label: 'Has Geotechnical Data', type: 'boolean' },
  { property: 'year', label: 'Year', type: 'range' },
  { property: 'bulk_density', label: 'Bulk density (g/cm³)', type: 'range' },
  { property: 'd50', label: 'D50 (µm)', type: 'range' },
  { property: 'friction_angle', label: 'Friction angle (°)', type: 'range' },
  { property: 'cohesion', label: 'Cohesion (kPa)', type: 'range' },
  { property: 'reference', label: 'Reference', type: 'text' },
  { property: 'lunar_ref', label: 'Lunar Sample Ref', type: 'categorical' },
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

  /** Set one property's values in a click (the Find pane's chips and ranges): creates, updates
   *  or, with no values, removes that property's filter. */
  const setFacet = useCallback((property: FilterProperty, values: string[]) => {
    setFilters(prev => {
      const rest = prev.filter(f => f.property !== property);
      if (values.length === 0 || values.every(v => v === '')) return rest;
      const existing = prev.find(f => f.property === property);
      return [...rest, { id: existing?.id ?? String(nextId++), property, values }];
    });
  }, []);

  /** How many simulants each value of a property would give, counting under every other active
   *  filter but not that property's own, so a chip's number is what clicking it adds. */
  const facetCounts = useCallback((property: FilterProperty, valueOf: (s: Simulant) => string[]) => {
    const others = filters.filter(f => f.property !== property);
    const base = filterSimulantsDynamic(simulants, others, searchQuery, filterCtx);
    const counts = new Map<string, number>();
    for (const s of base) for (const v of valueOf(s)) counts.set(v, (counts.get(v) ?? 0) + 1);
    return counts;
  }, [filters, simulants, searchQuery, filterCtx]);

  /** How many simulants a chip would leave: the other filters plus this property set to values. */
  const countWith = useCallback((property: FilterProperty, values: string[]) => {
    const others = filters.filter(f => f.property !== property);
    return filterSimulantsDynamic(simulants, [...others, { id: 'probe', property, values }], searchQuery, filterCtx).length;
  }, [filters, simulants, searchQuery, filterCtx]);

  const clearAllFilters = useCallback(() => {
    setFilters([]);
    setSearchQuery('');
  }, []);

  // Derive available options for categorical filters
  const filterOptions = useMemo(() => {
    // Empty values are left out of the options: "" is not a type a user can pick.
    const types = [...new Set(simulants.map(s => s.type).filter(Boolean))].sort();
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

    const lunarRefs = [...new Set(simulants.map(s => s.lunar_sample_reference).filter(Boolean))].sort() as string[];

    return { types, countries, institutions, detailedMinerals, groupMinerals, chemicals, availabilities, lunarRefs };
  }, [simulants, compositions, mineralGroups, chemicalCompositions]);

  return {
    filters, filteredSimulants, searchQuery, setFacet, facetCounts, countWith,
    addFilter, updateFilter, removeFilter, clearAllFilters, setSearchQuery,
    filterOptions,
  };
}
