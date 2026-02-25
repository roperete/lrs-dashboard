import React from 'react';
import { FilterSelect } from './FilterSelect';
import { X } from 'lucide-react';
import type { FilterState } from '../../types';
import { getCountryDisplay } from '../../utils/countryUtils';

interface FilterPanelProps {
  filters: FilterState;
  filterOptions: {
    types: string[];
    countries: string[];
    institutions: string[];
    detailedMinerals: string[];
    groupMinerals: string[];
    chemicals: string[];
  };
  setFilter: (key: keyof FilterState, values: string[]) => void;
  clearAllFilters: () => void;
}

export function FilterPanel({ filters, filterOptions, setFilter, clearAllFilters }: FilterPanelProps) {
  const hasActiveFilters = Object.values(filters).some(v => v.length > 0);

  return (
    <div className="space-y-2">
      <FilterSelect
        label="Type"
        selected={filters.type}
        options={filterOptions.types.map(t => ({ label: t, value: t }))}
        onChange={values => setFilter('type', values)}
      />

      <FilterSelect
        label="Country"
        selected={filters.country}
        options={[
          { label: 'European Union', value: 'EU' },
          ...filterOptions.countries.map(c => ({ label: getCountryDisplay(c), value: c })),
        ]}
        onChange={values => setFilter('country', values)}
      />

      <FilterSelect
        label="Mineral"
        selected={filters.mineral}
        groups={[
          {
            label: 'Detailed Minerals',
            options: filterOptions.detailedMinerals.map(m => ({ label: m, value: m })),
          },
          {
            label: 'NASA Mineral Groups',
            options: filterOptions.groupMinerals.map(m => ({ label: m, value: `group:${m}` })),
          },
        ]}
        onChange={values => setFilter('mineral', values)}
      />

      <FilterSelect
        label="Chemical"
        selected={filters.chemical}
        options={filterOptions.chemicals.map(c => ({ label: c, value: c }))}
        onChange={values => setFilter('chemical', values)}
      />

      <FilterSelect
        label="Institution"
        selected={filters.institution}
        options={filterOptions.institutions.map(i => ({ label: i, value: i }))}
        onChange={values => setFilter('institution', values)}
      />

      {hasActiveFilters && (
        <button
          onClick={clearAllFilters}
          className="w-full flex items-center justify-center gap-2 py-2 bg-orange-600/20 hover:bg-orange-600/30 border border-orange-500/30 text-orange-400 rounded-lg text-xs font-bold transition-all"
        >
          <X size={12} />
          Clear All Filters
        </button>
      )}
    </div>
  );
}
